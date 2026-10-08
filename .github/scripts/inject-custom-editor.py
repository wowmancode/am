#!/usr/bin/env python3
"""Inject the Custom Effects editor into a disassembled Alight Motion APK.

This script is run after apktool decodes the APK and before it rebuilds.
It does four things:

1. Copies the smali classes for CustomEffectsActivity, CustomEffectsBridge,
   and CustomEffectsLoader into the decoded smali tree.

2. Copies the HTML editor into assets/.

3. Patches AndroidManifest.xml to register CustomEffectsActivity.

4. Patches the effect loader to call CustomEffectsLoader.loadAll() at boot,
   and patches EffectBrowserActivity to add a "Custom Effects" entry that
   launches CustomEffectsActivity.

Usage:
    inject-custom-editor.py <patch-dir> <decoded-dir>

    patch-dir:   repo's patch/ directory (contains smali/ and custom-editor/)
    decoded-dir: apktool output (contains smali/, AndroidManifest.xml, etc.)
"""

import os
import re
import shutil
import sys
from pathlib import Path


def copy_smali(decoded: Path, patch: Path) -> None:
    """Copy custom smali classes into the decoded tree."""
    src = patch / "smali" / "com" / "wowmancode" / "customfx"
    # Put our classes in smali/ (the main DEX).
    dst = decoded / "smali" / "com" / "wowmancode" / "customfx"
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob("*.smali"):
        shutil.copy2(f, dst / f.name)
        print(f"  Copied {f.name} -> smali/com/wowmancode/customfx/")


def copy_editor_html(decoded: Path, patch: Path) -> None:
    """Copy the HTML editor into the assets directory."""
    src = patch / "custom-editor" / "custom_effects_editor.html"
    dst = decoded / "assets" / "custom_effects_editor.html"
    shutil.copy2(src, dst)
    print(f"  Copied custom_effects_editor.html -> assets/")


def patch_manifest(decoded: Path) -> None:
    """Add CustomEffectsActivity to AndroidManifest.xml."""
    manifest = decoded / "AndroidManifest.xml"
    text = manifest.read_text(encoding="utf-8")

    activity_decl = (
        '        <activity '
        'android:name="com.wowmancode.customfx.CustomEffectsActivity" '
        'android:theme="@android:style/Theme.NoTitleBar.Fullscreen" '
        'android:exported="false" />\n'
    )

    if "CustomEffectsActivity" in text:
        print("  Manifest already patched, skipping")
        return

    # Insert before the closing </application> tag
    text = text.replace("</application>", activity_decl + "    </application>")
    manifest.write_text(text, encoding="utf-8")
    print("  Patched AndroidManifest.xml with CustomEffectsActivity")


def patch_effect_loader(decoded: Path) -> None:
    """Patch VisualEffectKt$initVisualEffects$1 to call CustomEffectsLoader.loadAll()
    right before countDown(), so custom effects are loaded at boot."""

    # Find the loader thread smali file
    loader = None
    for p in decoded.rglob("VisualEffectKt$initVisualEffects$1.smali"):
        loader = p
        break

    if loader is None:
        print("  WARNING: Could not find VisualEffectKt$initVisualEffects$1.smali")
        return

    text = loader.read_text(encoding="utf-8")

    if "CustomEffectsLoader" in text:
        print("  Effect loader already patched, skipping")
        return

    # The pattern: right before the countDown() call, insert our loader.
    # We look for:
    #   invoke-static {}, Lcom/.../VisualEffectKt;->access$getVisualEffectsLoaded$p()...CountDownLatch;
    #   move-result-object vN
    #   invoke-virtual {vN}, ...CountDownLatch;->countDown()V

    # We'll insert before the access$getVisualEffectsLoaded call.
    pattern = (
        r'(invoke-static \{[^}]*\}, '
        r'Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectKt;->'
        r'access\$getVisualEffectsLoaded\$p\(\)'
        r'Ljava/util/concurrent/CountDownLatch;)'
    )

    match = re.search(pattern, text)
    if not match:
        print("  WARNING: Could not find countDown insertion point in effect loader")
        return

    # We need the appContext field and the map accessor.
    # From the UI map: iget-object v0, p0, ...;->$appContext:Landroid/content/Context;
    # The map: invoke-static {}, ...VisualEffectKt;->access$getLoadedVisualEffects$p()Ljava/util/Map;

    injection = """
    # --- Custom Effects: load saved effects at boot ---
    iget-object v8, p0, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectKt$initVisualEffects$1;->$appContext:Landroid/content/Context;
    invoke-static {}, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectKt;->access$getLoadedVisualEffects$p()Ljava/util/Map;
    move-result-object v9
    invoke-static {v8, v9}, Lcom/wowmancode/customfx/CustomEffectsLoader;->loadAll(Landroid/content/Context;Ljava/util/Map;)V
    # --- End Custom Effects ---

    """

    text = text[:match.start()] + injection + text[match.start():]

    # We may need to bump the register count. Find the .registers or .locals directive
    # for the method containing the countDown call and bump it.
    # The method is invoke()V. Find the nearest .registers before our insertion point.
    # Increase by 2 (we use v8 and v9).
    reg_pattern = r'(\.registers\s+)(\d+)'
    # Find all .registers directives and bump the one for the right method
    def bump_registers(m):
        count = int(m.group(2))
        if count < 10:
            return m.group(1) + str(max(count, 12))
        return m.group(1) + str(max(count, count + 2))

    # We need to be careful to only bump the right method's registers.
    # Let's find the method that contains "countDown" and bump its registers.
    methods = list(re.finditer(r'\.method[^\n]*\n', text))
    countdown_pos = text.find('countDown()V')

    for i, meth in enumerate(methods):
        end = methods[i+1].start() if i+1 < len(methods) else len(text)
        if meth.start() < countdown_pos < end:
            method_text = text[meth.start():end]
            new_method = re.sub(reg_pattern, bump_registers, method_text, count=1)
            text = text[:meth.start()] + new_method + text[end:]
            break

    loader.write_text(text, encoding="utf-8")
    print(f"  Patched {loader.name} with CustomEffectsLoader.loadAll() hook")


def patch_effect_browser(decoded: Path) -> None:
    """Patch EffectBrowserActivity to add a 'Custom Effects' entry.

    Adds a launchCustomEffects() helper, menu items to reach it, and
    result forwarding so applying an effect from the custom editor works
    the same as picking a built-in effect.
    """

    # Find EffectBrowserActivity
    browser = None
    for p in decoded.rglob("EffectBrowserActivity.smali"):
        browser = p
        break

    if browser is None:
        print("  WARNING: Could not find EffectBrowserActivity.smali")
        return

    text = browser.read_text(encoding="utf-8")

    if "CustomEffectsActivity" in text:
        print("  Effect browser already patched, skipping")
        return

    has_on_activity_result = "onActivityResult" in text

    new_methods = "\n# --- Custom Effects ---\n"

    # 1) Launch helper
    new_methods += """
.method private launchCustomEffects()V
    .registers 4
    new-instance v0, Landroid/content/Intent;
    const-class v1, Lcom/wowmancode/customfx/CustomEffectsActivity;
    invoke-direct {v0, p0, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const/16 v1, 0x3e9
    invoke-virtual {p0, v0, v1}, Landroid/app/Activity;->startActivityForResult(Landroid/content/Intent;I)V
    return-void
.end method
"""

    # 2) Menu methods
    if "onCreateOptionsMenu" not in text:
        new_methods += """
.method public onCreateOptionsMenu(Landroid/view/Menu;)Z
    .registers 5
    invoke-super {p0, p1}, Landroidx/fragment/app/e;->onCreateOptionsMenu(Landroid/view/Menu;)Z
    const/4 v0, 0x0
    const v1, 0x7fff01
    const/4 v2, 0x0
    const-string v3, "Custom Effects"
    invoke-interface {p1, v0, v1, v2, v3}, Landroid/view/Menu;->add(IIILjava/lang/CharSequence;)Landroid/view/MenuItem;
    const/4 v0, 0x1
    return v0
.end method
"""

    if "onOptionsItemSelected" not in text:
        new_methods += """
.method public onOptionsItemSelected(Landroid/view/MenuItem;)Z
    .registers 4
    invoke-interface {p1}, Landroid/view/MenuItem;->getItemId()I
    move-result v0
    const v1, 0x7fff01
    if-ne v0, v1, :cond_super
    invoke-direct {p0}, Lcom/alightcreative/app/motion/activities/effectbrowser/EffectBrowserActivity;->launchCustomEffects()V
    const/4 v0, 0x1
    return v0
    :cond_super
    invoke-super {p0, p1}, Landroidx/fragment/app/e;->onOptionsItemSelected(Landroid/view/MenuItem;)Z
    move-result v0
    return v0
.end method
"""

    # 3) onActivityResult — patch existing or add new
    if has_on_activity_result:
        # Inject a check at the top of the existing method body.
        pattern = (
            r'(\.method[^\n]*onActivityResult\(IILandroid/content/Intent;\)V'
            r'\s*\n(?:\s*\.(?:registers|locals)\s+\d+\s*\n))'
        )
        match = re.search(pattern, text)
        if match:
            injection = (
                "\n"
                "    # --- Custom Effects result forwarding ---\n"
                "    const/16 v0, 0x3e9\n"
                "    if-ne p1, v0, :customfx_skip\n"
                "    const/4 v0, -0x1\n"
                "    if-ne p2, v0, :customfx_skip\n"
                "    if-eqz p3, :customfx_skip\n"
                "    invoke-virtual {p0, p2, p3}, Landroid/app/Activity;"
                "->setResult(ILandroid/content/Intent;)V\n"
                "    invoke-virtual {p0}, Landroid/app/Activity;->finish()V\n"
                "    return-void\n"
                "    :customfx_skip\n"
                "    # --- End Custom Effects result forwarding ---\n"
            )
            text = text[:match.end()] + injection + text[match.end():]
            # Bump registers for this method if needed
            reg_m = re.search(
                r'(\.method[^\n]*onActivityResult[^\n]*\n\s*\.registers\s+)(\d+)',
                text,
            )
            if reg_m:
                old_count = int(reg_m.group(2))
                if old_count < 5:
                    text = (
                        text[: reg_m.start(2)]
                        + "5"
                        + text[reg_m.end(2) :]
                    )
            print("  Patched existing onActivityResult in EffectBrowserActivity")
        else:
            print("  WARNING: Could not find onActivityResult pattern to patch")
    else:
        new_methods += """
.method protected onActivityResult(IILandroid/content/Intent;)V
    .registers 5
    const/16 v0, 0x3e9
    if-ne p1, v0, :cond_super
    const/4 v0, -0x1
    if-ne p2, v0, :cond_super
    if-eqz p3, :cond_super
    invoke-virtual {p0, p2, p3}, Landroid/app/Activity;->setResult(ILandroid/content/Intent;)V
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V
    return-void
    :cond_super
    invoke-super {p0, p1, p2, p3}, Landroidx/fragment/app/e;->onActivityResult(IILandroid/content/Intent;)V
    return-void
.end method
"""

    new_methods += "# --- End Custom Effects ---\n"

    text += new_methods
    browser.write_text(text, encoding="utf-8")
    print("  Patched EffectBrowserActivity with Custom Effects menu + result forwarding")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <patch-dir> <decoded-dir>", file=sys.stderr)
        sys.exit(1)

    patch = Path(sys.argv[1])
    decoded = Path(sys.argv[2])

    if not decoded.is_dir():
        print(f"ERROR: {decoded} is not a directory", file=sys.stderr)
        sys.exit(1)

    print("Injecting Custom Effects editor...")
    copy_smali(decoded, patch)
    copy_editor_html(decoded, patch)
    patch_manifest(decoded)
    patch_effect_loader(decoded)
    patch_effect_browser(decoded)
    print("Custom Effects injection complete.")


if __name__ == "__main__":
    main()
