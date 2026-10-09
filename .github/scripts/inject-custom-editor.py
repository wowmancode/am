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

4. Adds a Transitions row under Add Effect in the Effects list.

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
EFFECTS_FRAGMENT = "smali/i1/k.smali"
EFFECTS_ADAPTER = "smali/i1/i.smali"
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


def patch_transitions_row(decoded: Path) -> None:
    fragment = decoded / EFFECTS_FRAGMENT
    adapter = decoded / EFFECTS_ADAPTER
    if not fragment.is_file() or not adapter.is_file():
        raise SystemExit("ERROR: Effects list classes are missing")

    text = fragment.read_text(encoding="utf-8")
    if "TransitionUi;->bind" not in text:
        anchor = "invoke-super {p0, p1, p2}, Landroidx/fragment/app/Fragment;->onViewCreated(Landroid/view/View;Landroid/os/Bundle;)V"
        if text.count(anchor) != 1:
            raise SystemExit("ERROR: Effects fragment onViewCreated hook site changed")
        text = text.replace(anchor, anchor + "\n    invoke-static {p0}, Lcom/wowmancode/customfx/TransitionUi;->bind(Li1/k;)V")
        fragment.write_text(text, encoding="utf-8")

    text = adapter.read_text(encoding="utf-8")
    if "TransitionUi;->wrapAddRow" not in text:
        anchor = "invoke-direct {v0, p2, p1}, Li1/i$a;-><init>(ILandroid/view/View;)V"
        if text.count(anchor) != 1:
            raise SystemExit("ERROR: Effects adapter row creation hook site changed")
        text = text.replace(anchor,
            "invoke-static {p1, p2}, Lcom/wowmancode/customfx/TransitionUi;->wrapAddRow(Landroid/view/View;I)Landroid/view/View;\n"
            "    move-result-object p1\n    " + anchor)
        adapter.write_text(text, encoding="utf-8")
    print("  Added the Transitions row to Effects", file=sys.stderr)


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
    patch_transitions_row(decoded)


if __name__ == "__main__":
    main()
