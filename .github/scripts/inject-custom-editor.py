#!/usr/bin/env python3
"""Wire the in-app Custom Effects editor into the disassembled app code.

Run by rebuild-dex.sh as a --hook, after apktool has disassembled the APK
(resources left compiled, so only smali is edited here) and before the code
is reassembled. It:

1. Copies the customfx smali classes into the smallest DEX, so the nearly
   full main DEX doesn't hit the 64K method limit.

2. Hooks the effect loader thread so saved custom effects are registered
   just before the app signals that effects have finished loading.

3. Hooks EffectBrowserActivity.onCreate to add a floating "+ Custom" button
   that opens the editor dialog.

4. Adds a home-screen Project XML picker which forwards files to the app's
   existing native ImportActivity.

5. Lets effect value labels open a numeric keyboard for slider and spinner
   controls, using their existing change handlers to persist the value.

6. Uses the empty scene overlay for preview and export, removing the watermark.

7. Removes diagnostic work from the live preview loop and adds an optional
   per-player Preview FPS button in the editor.

The editor is a dialog over the effect browser rather than its own activity,
so the manifest does not change. Its HTML page is added to the APK's assets
by add-effects.py.

Usage:
    inject-custom-editor.py <patch-dir> <decoded-dir>
"""

import re
import shutil
import sys
from pathlib import Path

LOADER_CLASS = "VisualEffectKt$initVisualEffects$1.smali"
BROWSER_CLASS = "EffectBrowserActivity.smali"
EFFECT_PARAMETER_ROW = "smali/i1/k$a$a.smali"
MAIN_ACTIVITY = "smali_classes4/com/alightcreative/app/motion/activities/main/MainActivity.smali"
MARKER = "Lcom/wowmancode/customfx/"


def find_one(decoded: Path, name: str) -> Path:
    found = sorted(decoded.glob(f"smali*/**/{name}"))
    if len(found) != 1:
        raise SystemExit(f"ERROR: expected one {name}, found {[str(p) for p in found]}")
    return found[0]


def copy_smali(decoded: Path, patch: Path) -> None:
    src = patch / "smali" / "com" / "wowmancode" / "customfx"
    files = sorted(src.glob("*.smali"))
    if not files:
        raise SystemExit(f"ERROR: no smali classes in {src}")

    # Put the classes in the DEX with the fewest classes.
    dirs = [d for d in decoded.glob("smali*") if d.is_dir()]
    target = min(dirs, key=lambda d: sum(1 for _ in d.rglob("*.smali")))
    dst = target / "com" / "wowmancode" / "customfx"
    dst.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy2(f, dst / f.name)
    print(f"  Copied {len(files)} classes into {target.name}/", file=sys.stderr)


def patch_effect_loader(decoded: Path) -> None:
    path = find_one(decoded, LOADER_CLASS)
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    # In invoke(), right after the built-in effects are put in the map:
    #   :cond_1
    #   invoke-static {}, ...->access$getVisualEffectsLoaded$p()...
    #   move-result-object v0
    #   invoke-virtual {v0}, ...CountDownLatch;->countDown()V
    # v0 is overwritten there, so it is free to use first.
    latch = (
        "invoke-static {}, Lcom/alightcreative/app/motion/scene/visualeffect/"
        "VisualEffectKt;->access$getVisualEffectsLoaded$p()"
        "Ljava/util/concurrent/CountDownLatch;\n"
    )
    count = text.count(latch)
    if count != 1:
        raise SystemExit(f"ERROR: expected one countDown site in {path.name}, found {count}")
    if not re.search(re.escape(latch) + r"(?:\s*\.line \d+)*\s*move-result-object v0\n", text):
        raise SystemExit(f"ERROR: latch result in {path.name} is not v0; v0 may be live")

    hook = (
        "iget-object v0, p0, Lcom/alightcreative/app/motion/scene/visualeffect/"
        "VisualEffectKt$initVisualEffects$1;->$appContext:Landroid/content/Context;\n"
        "    invoke-static {v0}, Lcom/wowmancode/customfx/CustomEffectsLoader;"
        "->loadAll(Landroid/content/Context;)V\n\n    "
    )
    path.write_text(text.replace(latch, hook + latch), encoding="utf-8")
    print(f"  Hooked custom effect loading into {path.name}", file=sys.stderr)


def patch_effect_browser(decoded: Path) -> None:
    path = find_one(decoded, BROWSER_CLASS)
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    m = re.search(r"\.method protected onCreate\(Landroid/os/Bundle;\)V\n.*?\.end method",
                  text, re.S)
    if not m:
        raise SystemExit(f"ERROR: no onCreate in {path.name}")
    method = m.group(0)

    # Add the button once the layout exists. p0 is still `this` there.
    content = re.search(r"invoke-virtual \{p0, \w+\}, L[\w/$]+;->setContentView\(I\)V\n", method)
    if not content:
        raise SystemExit(f"ERROR: no setContentView in {path.name} onCreate")

    hook = (
        "\n    invoke-static {p0}, Lcom/wowmancode/customfx/CustomEffectsUi;"
        "->attachButton(Landroid/app/Activity;)V\n"
    )
    method = method[:content.end()] + hook + method[content.end():]
    path.write_text(text[:m.start()] + method + text[m.end():], encoding="utf-8")
    print(f"  Added the Custom button to {path.name}", file=sys.stderr)


def patch_project_import(decoded: Path) -> None:
    path = decoded / MAIN_ACTIVITY
    if not path.is_file():
        raise SystemExit("ERROR: MainActivity is missing")
    text = path.read_text(encoding="utf-8")
    if "ProjectImportUi;->attachButton" not in text:
        method = re.search(r"\.method protected onCreate\(Landroid/os/Bundle;\)V\n.*?\.end method", text, re.S)
        if not method:
            raise SystemExit("ERROR: MainActivity onCreate is missing")
        anchor = "invoke-virtual {v0, v1}, Landroidx/appcompat/app/c;->setContentView(I)V"
        if method.group(0).count(anchor) != 1:
            raise SystemExit("ERROR: MainActivity layout hook changed")
        patched = method.group(0).replace(anchor, anchor +
            "\n    invoke-static/range {p0 .. p0}, Lcom/wowmancode/customfx/ProjectImportUi;->attachButton(Landroid/app/Activity;)V")
        text = text[:method.start()] + patched + text[method.end():]

    if "ProjectImportUi;->onActivityResult" not in text:
        anchor = ".method protected onActivityResult(IILandroid/content/Intent;)V\n    .locals 3"
        if text.count(anchor) != 1:
            raise SystemExit("ERROR: MainActivity result hook changed")
        hook = ("\n    invoke-static {p0, p1, p2, p3}, Lcom/wowmancode/customfx/ProjectImportUi;"
                "->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)Z\n"
                "    move-result v0\n"
                "    if-eqz v0, :project_import_other\n"
                "    return-void\n"
                "    :project_import_other")
        text = text.replace(anchor, anchor + hook)
    path.write_text(text, encoding="utf-8")
    print("  Added native Project XML import to MainActivity", file=sys.stderr)


def patch_effect_number_edit(decoded: Path) -> None:
    path = decoded / EFFECT_PARAMETER_ROW
    if not path.is_file():
        raise SystemExit("ERROR: Effects parameter row is missing")
    text = path.read_text(encoding="utf-8")
    if "EffectNumberEdit;->bind" in text:
        return
    value_view = (
        "iget-object v0, v11, Landroidx/recyclerview/widget/RecyclerView$d0;->a:Landroid/view/View;\n"
        "    sget v1, Lf1/e;->Ma:I\n"
        "    invoke-virtual {v0, v1}, Landroid/view/View;->findViewById(I)Landroid/view/View;\n"
        "    move-result-object v0\n"
        "    check-cast v0, Landroid/widget/TextView;\n"
        "    move-object/from16 v1, p1\n"
    )
    spinner = "invoke-virtual {v13, v7}, Lcom/alightcreative/widget/ValueSpinner;->setOnSpinAbs(Lkotlin/jvm/functions/Function1;)V"
    slider = "invoke-virtual {v10, v12}, Lcom/alightcreative/widget/AlightSlider;->setOnSeekBarChangeListener(Landroid/widget/SeekBar$OnSeekBarChangeListener;)V"
    if text.count(spinner) != 1 or text.count(slider) != 1:
        raise SystemExit("ERROR: Effects parameter controls changed")
    text = text.replace(spinner, spinner + "\n    " + value_view +
        "    invoke-static {v1, v0, v13}, Lcom/wowmancode/customfx/EffectNumberEdit;"
        "->bind(Lcom/alightcreative/app/motion/scene/userparam/UserParameter;Landroid/widget/TextView;Landroid/view/View;)V")
    text = text.replace(slider, slider + "\n    " + value_view +
        "    invoke-static {v1, v0, v10}, Lcom/wowmancode/customfx/EffectNumberEdit;"
        "->bind(Lcom/alightcreative/app/motion/scene/userparam/UserParameter;Landroid/widget/TextView;Landroid/view/View;)V")
    path.write_text(text, encoding="utf-8")
    print("  Added tap-to-edit numeric effect values", file=sys.stderr)


def patch_scene_overlay(decoded: Path) -> None:
    path = find_one(decoded, "SceneOverlayKt.smali")
    find_one(decoded, "SceneOverlay_None.smali")
    text = path.read_text(encoding="utf-8")
    signature = (
        ".method public static final getCurrentSceneOverlay("
        "Lcom/alightcreative/app/motion/scene/Scene;"
        "Lcom/alightcreative/app/motion/scene/ExportParams;)"
        "Lcom/alightcreative/app/motion/scene/SceneOverlay;\n"
    )
    methods = list(re.finditer(re.escape(signature) + r".*?^\.end method", text, re.S | re.M))
    if len(methods) != 1:
        raise SystemExit("ERROR: scene overlay selector changed")
    method = methods[0]
    body = method.group(0)
    old = (
        "sget-object p0, Lcom/alightcreative/app/motion/scene/SceneOverlay_StandardWM;"
        "->INSTANCE:Lcom/alightcreative/app/motion/scene/SceneOverlay_StandardWM;"
    )
    new = (
        "# Use the empty overlay for personal builds.\n    "
        "sget-object p0, Lcom/alightcreative/app/motion/scene/SceneOverlay_None;"
        "->INSTANCE:Lcom/alightcreative/app/motion/scene/SceneOverlay_None;"
    )
    if old not in body and body.count(new) == 1:
        return
    if body.count(old) != 1:
        raise SystemExit("ERROR: expected one standard watermark overlay fallback")
    body = body.replace(old, new)
    path.write_text(text[:method.start()] + body + text[method.end():], encoding="utf-8")
    print("  Disabled the watermark in scene preview and export", file=sys.stderr)


def patch_native_preview(decoded: Path) -> None:
    player = find_one(decoded, "ScenePlayer.smali")
    worker = find_one(decoded, "ScenePlayer$2.smali")
    request = find_one(decoded, "ScenePlayer$renderFrame$2.smali")
    editor = find_one(decoded, "EditActivity.smali")
    gl_context = find_one(decoded, "GLContext.smali")
    text = gl_context.read_text(encoding="utf-8")
    method = re.search(r"^\.method public final l0\(\)I\n.*?^\.end method", text, re.M | re.S)
    if not method:
        raise SystemExit("ERROR: preview surface swap method changed")
    if "Avoid formatting a diagnostic for every surface swap" not in method.group():
        log = re.compile(r"    new-instance v1, Ljava/lang/StringBuilder;.*?"
                         r"invoke-static \{v2, v1\}, Landroid/util/Log;->d\(Ljava/lang/String;Ljava/lang/String;\)I", re.S)
        body, count = log.subn("    # Avoid formatting a diagnostic for every surface swap.", method.group())
        if count != 1:
            raise SystemExit("ERROR: preview surface swap diagnostic changed")
        gl_context.write_text(text[:method.start()] + body + text[method.end():], encoding="utf-8")
    text = player.read_text(encoding="utf-8")
    if "previewFrameCount:J" not in text:
        anchor = ".field private didRender:Z"
        if text.count(anchor) != 1:
            raise SystemExit("ERROR: preview player fields changed")
        text = text.replace(anchor, anchor + "\n\n.field public volatile previewFrameCount:J")
        # This lambda only formats a debug log on each frame request.
        log = re.compile(
            r"    new-instance v0, Lcom/alightcreative/app/motion/scene/ScenePlayer\$renderFrame\$1;"
            r".*?invoke-static \{p0, v0\}, Lt2/b;->c\(Ljava/lang/Object;Lkotlin/jvm/functions/Function0;\)V", re.S)
        text, count = log.subn("    # Avoid a per-request diagnostic allocation.", text)
        if count != 1:
            raise SystemExit("ERROR: preview frame request log changed")
        player.write_text(text, encoding="utf-8")

    text = worker.read_text(encoding="utf-8")
    if "previewFrameCount:J" not in text:
        trace = ("invoke-virtual {v0}, Lcom/alightcreative/app/motion/persist/a;"
                 "->getDisableRenderPerformanceTrace()Z\n\n    move-result v6")
        stats = ("invoke-static {v0, v3}, Lcom/alightcreative/app/motion/scene/SceneKt;"
                 "->statsForFrame(Lcom/alightcreative/app/motion/scene/Scene;I)"
                 "Lcom/alightcreative/app/motion/scene/FrameStats;\n\n    move-result-object v0")
        swap = "invoke-virtual {v0}, Lcom/alightcreative/gl/GLContext;->l0()I"
        if any(text.count(anchor) != 1 for anchor in (trace, stats, swap)):
            raise SystemExit("ERROR: live preview render loop changed")
        text = text.replace(trace, "const/4 v6, 0x1    # Disable per-frame profiling traces.")
        text = text.replace(stats, "const/4 v0, 0x0    # Statistics were only consumed by profiling.")
        log = re.compile(
            r"    iget-object v3, v1, Lcom/alightcreative/app/motion/scene/ScenePlayer\$2;->this\$0:Lcom/alightcreative/app/motion/scene/ScenePlayer;\n\n"
            r"    new-instance v4, Lcom/alightcreative/app/motion/scene/ScenePlayer\$2\$4;"
            r".*?invoke-static \{v3, v4\}, Lt2/b;->c\(Ljava/lang/Object;Lkotlin/jvm/functions/Function0;\)V", re.S)
        text, count = log.subn("    # No debug lambda allocation while polling the preview queue.", text)
        if count != 1:
            raise SystemExit("ERROR: preview queue diagnostic changed")
        hook = ("\n    move-result v3\n    const/16 v4, 0x3000\n"
                "    if-ne v3, v4, :customfps_swap_done\n\n"
                "    iget-object v0, v1, Lcom/alightcreative/app/motion/scene/ScenePlayer$2;"
                "->this$0:Lcom/alightcreative/app/motion/scene/ScenePlayer;\n"
                "    iget-wide v3, v0, Lcom/alightcreative/app/motion/scene/ScenePlayer;->previewFrameCount:J\n"
                "    const-wide/16 v10, 0x1\n    add-long/2addr v3, v10\n"
                "    iput-wide v3, v0, Lcom/alightcreative/app/motion/scene/ScenePlayer;->previewFrameCount:J\n"
                "    :customfps_swap_done")
        text = text.replace(swap, swap + hook)
        worker.write_text(text, encoding="utf-8")

    text = request.read_text(encoding="utf-8")
    log = re.compile(
        r"    new-instance v1, Lcom/alightcreative/app/motion/scene/ScenePlayer\$renderFrame\$2\$1;"
        r".*?invoke-static \{v0, v1\}, Lt2/b;->c\(Ljava/lang/Object;Lkotlin/jvm/functions/Function0;\)V", re.S)
    text, count = log.subn("    # Pending-frame updates do not need a diagnostic lambda.", text)
    if count:
        request.write_text(text, encoding="utf-8")
    elif "Pending-frame updates do not need" not in text:
        raise SystemExit("ERROR: pending preview frame diagnostic changed")

    text = editor.read_text(encoding="utf-8")
    hooks = {
        "onCreate": ("invoke-virtual {p0, p1}, Landroidx/appcompat/app/c;->setContentView(I)V", "attach"),
        "onResume": ("invoke-super {p0}, Landroidx/fragment/app/e;->onResume()V", "resume"),
        "onPause": (".locals 4", "pause"),
    }
    for name, (anchor, action) in hooks.items():
        marker = f"PreviewFpsUi;->{action}"
        if marker in text:
            continue
        method = re.search(r"^\.method protected " + name + r"\([^\n]*\n.*?^\.end method", text, re.M | re.S)
        if not method or method.group().count(anchor) != 1:
            raise SystemExit(f"ERROR: editor {name} FPS hook changed")
        body = method.group().replace(anchor, anchor + "\n    invoke-static {p0}, "
            f"Lcom/wowmancode/customfx/PreviewFpsUi;->{action}(Landroid/app/Activity;)V")
        text = text[:method.start()] + body + text[method.end():]
    editor.write_text(text, encoding="utf-8")
    print("  Optimized the live preview loop and added optional Preview FPS", file=sys.stderr)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"Usage: {sys.argv[0]} <patch-dir> <decoded-dir>")

    patch = Path(sys.argv[1])
    decoded = Path(sys.argv[2])
    if not decoded.is_dir():
        raise SystemExit(f"ERROR: {decoded} is not a directory")

    print("Injecting the Custom Effects editor...", file=sys.stderr)
    copy_smali(decoded, patch)
    patch_effect_loader(decoded)
    patch_effect_browser(decoded)
    patch_project_import(decoded)
    patch_effect_number_edit(decoded)
    patch_scene_overlay(decoded)
    patch_native_preview(decoded)


if __name__ == "__main__":
    main()
