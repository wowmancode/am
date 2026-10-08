#!/usr/bin/env python3
"""Patch the effect-integrity signature inside an APK.

Alight Motion computes a SHA-256 digest over every XML file in
assets/effects/ (sorted alphabetically, with non-allowed characters
stripped) and compares it against a value hardcoded in the DEX.  When
custom effects are added the digest changes and the app crashes.

This script:
  1. Reads assets/effects/*.xml from the APK (after custom effects
     have been injected).
  2. Recomputes the digest using the same algorithm as the app.
  3. Finds the old digest string in every classes*.dex and replaces it
     with the new one.
  4. Writes a new APK with the patched DEX files.

Usage:
    python3 patch-effect-sig.py <input.apk> <output.apk>
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
import zlib
from pathlib import Path
from zipfile import ZipFile, ZipInfo

# ── constants matching the decompiled app code ──────────────────────

SEED = b"AMVESIG"
STRIP_RE = re.compile(r"[^A-Za-z,0-9(){}\_.+\]\[\-*@#$=]")
EFFECTS_DIR = "assets/effects/"

# The known digest the unmodified APK checks against.
OLD_SIG = "F14CEE321924058BE7D1730D5B696A8DEA1E7462695B6E7E03C6C79054C6453B"

# Only the old JAR-signature entries are dropped (they'll be
# re-created by apksigner later).
SIGNATURE_RE = re.compile(
    r"^META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))$"
)


def fix_dex_checksums(data: bytearray) -> bytearray:
    """Recompute the SHA-1 signature and Adler32 checksum in a DEX header.

    DEX header layout (first 36 bytes):
      0- 7: magic (e.g. "dex\\n039\\0")
      8-11: Adler32 checksum  (over bytes 12..EOF)
     12-31: SHA-1 signature   (over bytes 32..EOF)
     32-35: file_size
    """
    # 1. SHA-1 signature over bytes 32..end → written at offset 12.
    sha1 = hashlib.sha1(data[32:]).digest()          # 20 bytes
    data[12:32] = sha1

    # 2. Adler32 checksum over bytes 12..end → written at offset 8.
    checksum = zlib.adler32(bytes(data[12:])) & 0xFFFFFFFF
    struct.pack_into("<I", data, 8, checksum)

    return data


def compute_effect_sig(apk: ZipFile) -> str:
    """Reproduce VisualEffectKt.loadVisualEffects digest computation."""

    digest = hashlib.sha256()
    digest.update(SEED)

    # The app calls assets.list("effects") which returns sorted names.
    effect_names = sorted(
        name
        for name in apk.namelist()
        if name.startswith(EFFECTS_DIR)
        and name.endswith(".xml")
        and "/" not in name[len(EFFECTS_DIR):]  # no sub-directories
    )

    for name in effect_names:
        raw = apk.read(name).decode("utf-8")
        stripped = STRIP_RE.sub("", raw)
        digest.update(stripped.encode("utf-8"))

    return digest.hexdigest().upper()


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.apk> <output.apk>", file=sys.stderr)
        raise SystemExit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    with ZipFile(input_path) as apk:
        new_sig = compute_effect_sig(apk)

    print(f"Old effect signature: {OLD_SIG}")
    print(f"New effect signature: {new_sig}")

    if new_sig == OLD_SIG:
        print("Signatures match — no patching needed.")
        if input_path != output_path:
            import shutil
            shutil.copy2(input_path, output_path)
        return

    old_bytes = OLD_SIG.encode("utf-8")
    new_bytes = new_sig.encode("utf-8")
    assert len(old_bytes) == len(new_bytes) == 64

    patched_dex = 0

    with ZipFile(input_path) as src, ZipFile(output_path, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)

            # Patch DEX files that contain the hardcoded signature,
            # then recompute the DEX-internal checksums so Android
            # accepts the modified file.
            if info.filename.endswith(".dex") and old_bytes in data:
                count = data.count(old_bytes)
                data = data.replace(old_bytes, new_bytes)
                data = bytes(fix_dex_checksums(bytearray(data)))
                print(f"  Patched {info.filename}: {count} occurrence(s), checksums updated")
                patched_dex += 1

            copy = ZipInfo(info.filename, date_time=info.date_time)
            copy.compress_type = info.compress_type
            copy.external_attr = info.external_attr
            copy.create_system = info.create_system
            dst.writestr(copy, data)

    if patched_dex == 0:
        print(
            f"WARNING: old signature {OLD_SIG} was not found in any .dex file.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    # Verify the patch took effect.
    with ZipFile(output_path) as patched:
        verify_sig = compute_effect_sig(patched)
        if verify_sig != new_sig:
            raise SystemExit(
                f"ERROR: verification failed — expected {new_sig}, got {verify_sig}"
            )

        # Make sure the new sig is in the DEX now.
        for info in patched.infolist():
            if info.filename.endswith(".dex"):
                dex_data = patched.read(info.filename)
                if new_bytes in dex_data:
                    print(f"  Verified {info.filename} contains new signature")
                if old_bytes in dex_data:
                    raise SystemExit(
                        f"ERROR: {info.filename} still contains old signature"
                    )

    print(f"Patched {patched_dex} DEX file(s). Effect signature updated.")


if __name__ == "__main__":
    main()
