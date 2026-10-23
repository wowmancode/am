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

8. Drains available video encoder output without stalling each frame, while
   preserving the blocking end-of-stream drain, and removes export profiling.

9. Adds project-backed XYZ controls and perspective projection to the native
   Move & Transform panel, including its dial, trackpad, and keyframe bindings.

10. Enables all native easing graphs through the AdvancedEasing benefit shared
    by graph selection, editing, clipboard actions, and preview/export checks.

The editor is a dialog over the effect browser rather than its own activity,
so the manifest does not change. Its HTML page is added to the APK's assets
by add-effects.py.

Usage:
    inject-custom-editor.py <patch-dir> <decoded-dir>
"""

import re
import shutil
import subprocess
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


def patch_export_rendering(decoded: Path) -> None:
    codec = find_one(decoded, "MediaCodecExportContext.smali")
    exporter = find_one(decoded, "SceneExporter.smali")
    text = codec.read_text(encoding="utf-8")
    if "export_drain_timeout_ready" not in text:
        method = re.search(r"^\.method private final drainEncoder\(Z\)V\n.*?^\.end method", text, re.M | re.S)
        anchor = ("const-wide/16 v4, 0x2710\n\n"
                  "    invoke-virtual {v2, v3, v4, v5}, Landroid/media/MediaCodec;"
                  "->dequeueOutputBuffer(Landroid/media/MediaCodec$BufferInfo;J)I")
        if not method or method.group().count(anchor) != 1:
            raise SystemExit("ERROR: video encoder drain timeout changed")
        # Drain every ready buffer before submitting another frame. Waiting
        # for future output here serializes GPU rendering and encoding. EOS
        # still waits/retries until the encoder emits its final flagged buffer.
        body = method.group().replace(anchor,
            "const-wide/16 v4, 0x0\n"
            "    if-eqz p1, :export_drain_timeout_ready\n"
            "    const-wide/16 v4, 0x2710\n"
            "    :export_drain_timeout_ready\n\n" + anchor.split("\n\n", 1)[1])
        text = text[:method.start()] + body + text[method.end():]
        # These callbacks only format diagnostic strings. Leave format-change,
        # warning, failure, end-of-stream, and buffer/muxer handling untouched.
        for suffix, register, level in (("beginFrame$1", "v0", "c"),
                                        ("drainEncoder$1", "v0", "h"),
                                        ("drainEncoder$3", "v3", "h"),
                                        ("drainEncoder$8", "v3", "h")):
            cls = "Lcom/alightcreative/app/motion/scene/MediaCodecExportContext$" + suffix + ";"
            pattern = re.compile(r"    new-instance " + register + ", " + re.escape(cls) +
                r".*?invoke-static \{p0, " + register + r"\}, Lt2/b;->" + level +
                r"\(Ljava/lang/Object;Lkotlin/jvm/functions/Function0;\)V", re.S)
            text, count = pattern.subn("    # Avoid a per-frame encoder diagnostic allocation.", text)
            if count != 1:
                raise SystemExit(f"ERROR: encoder diagnostic changed: {suffix}")
        codec.write_text(text, encoding="utf-8")

    text = exporter.read_text(encoding="utf-8")
    if "Export frames do not need a profiling trace" not in text:
        method = re.search(r"^\.method private final renderFrame\([^\n]*\n.*?^\.end method", text, re.M | re.S)
        if not method:
            raise SystemExit("ERROR: export renderFrame changed")
        pattern = re.compile(r"    invoke-static \{\}, Lcom/google/firebase/perf/c;->c\(\)Lcom/google/firebase/perf/c;"
            r".*?invoke-virtual \{v1\}, Lcom/google/firebase/perf/metrics/Trace;->start\(\)V", re.S)
        body, count = pattern.subn("    # Export frames do not need a profiling trace.", method.group())
        stop = "invoke-virtual {v1}, Lcom/google/firebase/perf/metrics/Trace;->stop()V"
        if count != 1 or body.count(stop) != 1:
            raise SystemExit("ERROR: per-frame export profiling changed")
        body = body.replace(stop, "# No per-frame export profiling to stop.")
        exporter.write_text(text[:method.start()] + body + text[method.end():], encoding="utf-8")
    # These diagnostics run in the shared renderer, including nested scenes,
    # in both preview and export. Their constructors only capture arguments.
    scene = find_one(decoded, "SceneKt.smali")
    text = scene.read_text(encoding="utf-8")
    for suffix, register, level in (("4", "v3", "c"), ("7", "v9", "h"), ("8", "v4", "h")):
        marker = f"# Shared renderer diagnostic {suffix} omitted."
        if marker in text:
            continue
        cls = "Lcom/alightcreative/app/motion/scene/SceneKt$renderWithGpu$1$" + suffix + ";"
        pattern = re.compile(r"    new-instance " + register + ", " + re.escape(cls) + r"\s+"
            r"invoke-direct \{[^\n]+\}, " + re.escape(cls) + r"-><init>\([^\n]+\)V\s+"
            r"invoke-static \{v0, " + register + r"\}, Lt2/b;->" + level +
            r"\(Ljava/lang/Object;Lkotlin/jvm/functions/Function0;\)V")
        text, count = pattern.subn("    " + marker, text)
        if count != 1:
            raise SystemExit(f"ERROR: shared renderer diagnostic changed: {suffix}")
    scene.write_text(text, encoding="utf-8")
    print("  Optimized encoder scheduling and removed per-frame export profiling", file=sys.stderr)


def patch_graph_access(decoded: Path) -> None:
    paths = list(decoded.glob("smali*/d1/g.smali"))
    if len(paths) != 1:
        raise SystemExit("ERROR: graph purchase state changed")
    path = paths[0]
    text = path.read_text(encoding="utf-8")
    marker = "# Enable all native easing graphs in every local purchase snapshot."
    if marker in text:
        return
    constructor = ("<init>(Ljava/util/Set;Ljava/util/List;Ljava/util/List;"
                   "Lcom/alightcreative/account/f;ZLcom/alightcreative/account/c;"
                   "Ljava/lang/Long;Ljava/util/List;Ljava/util/List;)V")
    method = re.search(r"^\.method public constructor " + re.escape(constructor) +
                       r"\n.*?^\.end method", text, re.M | re.S)
    anchor = "    iput-object p1, p0, Ld1/g;->a:Ljava/util/Set;"
    if not method or method.group().count(anchor) != 1 or ".locals 1" not in method.group():
        raise SystemExit("ERROR: native graph benefit constructor changed")
    sets = find_one(decoded, "SetsKt.smali").read_text(encoding="utf-8")
    if ".method public static bridge synthetic plus(Ljava/util/Set;Ljava/lang/Object;)Ljava/util/Set;" not in sets:
        raise SystemExit("ERROR: native immutable set union API changed")
    body = method.group().replace(anchor,
        "    " + marker + "\n"
        "    sget-object v0, Lcom/alightcreative/account/LicenseBenefit;->AdvancedEasing:Lcom/alightcreative/account/LicenseBenefit;\n"
        "    invoke-static {p1, v0}, Lkotlin/collections/SetsKt;->plus(Ljava/util/Set;Ljava/lang/Object;)Ljava/util/Set;\n"
        "    move-result-object p1\n\n" + anchor)
    path.write_text(text[:method.start()] + body + text[method.end():], encoding="utf-8")
    print("  Unlocked every native easing graph for selection, editing, and export", file=sys.stderr)


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
    patch_export_rendering(decoded)
    patch_graph_access(decoded)
    subprocess.run([sys.executable, str(Path(__file__).with_name("inject-transform3d.py")),
                    str(decoded)], check=True, stdout=sys.stderr)
    subprocess.run([sys.executable, str(Path(__file__).with_name("check-export-drain.py")),
                    str(decoded)], check=True, stdout=sys.stderr)


if __name__ == "__main__":
    main()
