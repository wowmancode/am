#!/usr/bin/env python3
"""Add custom effects to an Alight Motion APK and patch the integrity signature.

This script performs two tasks in a single ZIP repack:

  1. Injects (or replaces) effect XML files from a local directory into
     assets/effects/ inside the APK.

  2. Recomputes the SHA-256 effect-integrity digest that Alight Motion
     checks on startup, and patches the hardcoded expected value in
     classes.dex so the check passes with the new effect set.

The DEX-internal Adler32 checksum and SHA-1 signature are recomputed
after patching so Android accepts the modified DEX.

Usage:
    python3 add-effects.py <source.apk> <output.apk> <effects-dir>
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

# ── Alight Motion effect-integrity constants ────────────────────────
# Reverse-engineered from VisualEffectKt.loadVisualEffects and
# MainActivity$f0.invoke in Alight Motion 3.10.0.

SEED = b"AMVESIG"
STRIP_RE = re.compile(r"[^A-Za-z,0-9(){}\_.+\]\[\-*@#$=]")
OLD_SIG = b"F14CEE321924058BE7D1730D5B696A8DEA1E7462695B6E7E03C6C79054C6453B"

EFFECTS_PREFIX = "assets/effects/"

# Only the old JAR-signature entries are dropped (they are re-created
# by apksigner later).  Other META-INF entries stay.
SIGNATURE_RE = re.compile(
    r"^META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))$"
)


def fix_dex_checksums(data: bytearray) -> bytes:
    """Recompute the SHA-1 signature and Adler32 checksum in a DEX header.

    DEX header layout:
      0- 7  magic
      8-11  Adler32 checksum  (over bytes 12 .. EOF)
     12-31  SHA-1 signature   (over bytes 32 .. EOF)
     32-35  file_size
    """
    sha1 = hashlib.sha1(data[32:]).digest()
    data[12:32] = sha1

    checksum = zlib.adler32(bytes(data[12:])) & 0xFFFFFFFF
    struct.pack_into("<I", data, 8, checksum)

    return bytes(data)


def compute_effect_sig(effect_contents: dict[str, bytes]) -> str:
    """Reproduce the digest that VisualEffectKt.loadVisualEffects computes.

    effect_contents maps "assets/effects/<name>.xml" → file bytes for
    every effect XML that will be in the final APK.
    """
    digest = hashlib.sha256()
    digest.update(SEED)

    for name in sorted(effect_contents):
        raw = effect_contents[name].decode("utf-8")
        stripped = STRIP_RE.sub("", raw)
        digest.update(stripped.encode("utf-8"))

    return digest.hexdigest().upper()


def main() -> None:
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <source.apk> <output.apk> <effects-dir>",
            file=sys.stderr,
        )
        raise SystemExit(1)

    source_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    effects_dir = Path(sys.argv[3])

    custom_effects = sorted(effects_dir.glob("*.xml"))
    if not custom_effects:
        raise SystemExit(f"ERROR: no .xml files found in {effects_dir}")

    custom_data = {
        EFFECTS_PREFIX + p.name: p.read_bytes() for p in custom_effects
    }
    custom_names = set(custom_data)

    # ── Pass 1: collect the full effect set for digest computation ───

    all_effects: dict[str, bytes] = {}

    with ZipFile(source_path) as src:
        for name in src.namelist():
            if (
                name.startswith(EFFECTS_PREFIX)
                and name.endswith(".xml")
                and "/" not in name[len(EFFECTS_PREFIX):]
            ):
                all_effects[name] = src.read(name)

    # Override / add custom effects.
    all_effects.update(custom_data)

    new_sig = compute_effect_sig(all_effects).encode("utf-8")
    assert len(new_sig) == len(OLD_SIG) == 64

    print(f"Old effect signature: {OLD_SIG.decode()}")
    print(f"New effect signature: {new_sig.decode()}")

    need_dex_patch = new_sig != OLD_SIG

    # ── Pass 2: build the output APK in one repack ───────────────────

    kept = 0
    replaced = 0
    dropped_sig = 0
    patched_dex = 0

    with ZipFile(source_path) as src, ZipFile(output_path, "w") as dst:
        for info in src.infolist():
            if SIGNATURE_RE.match(info.filename):
                dropped_sig += 1
                continue

            if info.filename in custom_names:
                replaced += 1
                continue

            data = src.read(info.filename)

            # Patch the hardcoded effect digest in DEX files.
            if need_dex_patch and info.filename.endswith(".dex") and OLD_SIG in data:
                count = data.count(OLD_SIG)
                data = data.replace(OLD_SIG, new_sig)
                data = fix_dex_checksums(bytearray(data))
                print(f"  Patched {info.filename}: {count} sig occurrence(s), checksums updated")
                patched_dex += 1

            # Preserve the original entry's metadata exactly so the
            # repack is as close to a byte-for-byte copy as possible.
            copy = ZipInfo(info.filename, date_time=info.date_time)
            copy.compress_type = info.compress_type
            copy.external_attr = info.external_attr
            copy.create_system = info.create_system
            dst.writestr(copy, data)
            kept += 1

        # Add custom effect files.
        for path in custom_effects:
            entry = ZipInfo(
                EFFECTS_PREFIX + path.name,
                date_time=(1981, 1, 1, 1, 1, 1),
            )
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            dst.writestr(entry, path.read_bytes())
            print(f"  Added: {entry.filename}")

    print(f"Entries kept: {kept}")
    print(f"Effect entries replaced: {replaced}")
    print(f"Signature entries dropped: {dropped_sig}")
    print(f"DEX files patched: {patched_dex}")

    if need_dex_patch and patched_dex == 0:
        raise SystemExit(
            f"ERROR: needed to patch effect sig but {OLD_SIG.decode()} "
            "was not found in any .dex file"
        )

    # ── Pass 3: verify ───────────────────────────────────────────────

    with ZipFile(source_path) as before, ZipFile(output_path) as after:
        after_entries = {e.filename: e for e in after.infolist()}

        for entry in before.infolist():
            name = entry.filename
            if SIGNATURE_RE.match(name) or name in custom_names:
                continue

            rebuilt = after_entries.get(name)
            if rebuilt is None:
                raise SystemExit(f"ERROR: lost {name}")

            # DEX files will differ (patched sig + checksums).
            if name.endswith(".dex") and need_dex_patch:
                if rebuilt.file_size != entry.file_size:
                    raise SystemExit(f"ERROR: {name} size changed")
                continue

            if (rebuilt.CRC, rebuilt.file_size, rebuilt.compress_type) != (
                entry.CRC,
                entry.file_size,
                entry.compress_type,
            ):
                raise SystemExit(f"ERROR: changed {name}")

        for path in custom_effects:
            rebuilt = after_entries.get(EFFECTS_PREFIX + path.name)
            if rebuilt is None or after.read(rebuilt) != path.read_bytes():
                raise SystemExit(f"ERROR: {path.name} not added correctly")

        resources = after_entries.get("resources.arsc")
        if resources is None or resources.compress_type != ZIP_STORED:
            raise SystemExit("ERROR: resources.arsc must stay stored")

        # Verify the new effect sig is in the DEX.
        if need_dex_patch:
            for info in after.infolist():
                if info.filename.endswith(".dex"):
                    dex_data = after.read(info.filename)
                    if OLD_SIG in dex_data:
                        raise SystemExit(
                            f"ERROR: {info.filename} still contains old signature"
                        )

    print("Verified: all original entries preserved, custom effects added, signature patched.")


if __name__ == "__main__":
    main()
