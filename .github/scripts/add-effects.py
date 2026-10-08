#!/usr/bin/env python3
"""Add custom effects to an Alight Motion APK.

Alight Motion hashes every assets/effects/*.xml on startup and compares
the result with a constant in MainActivity$f0. Adding effects changes
that hash, so the constant has to be updated too. That can't be done by
swapping bytes inside classes.dex: DEX string tables must stay sorted,
and a different hash usually sorts elsewhere, so Android refuses to load
the DEX and the app dies instantly. Instead the workflow rebuilds the
DEX with smali, and this script handles the two ends of that:

  sig    Print the effect hash the APK will have once the custom
         effects are added (and the hash it expects today).

           add-effects.py sig <source.apk> <effects-dir>

  build  Copy the APK, add the effects, and swap in rebuilt DEX files,
         all in a single repack.

           add-effects.py build <source.apk> <output.apk> <effects-dir>
                          [--dex classes.dex=path/to/classes.dex ...]
"""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

# From VisualEffectKt.loadVisualEffects / MainActivity$f0 (AM 3.10.0).
SEED = b"AMVESIG"
STRIP_RE = re.compile(r"[^A-Za-z,0-9(){}_.+\]\[\-*@#$=]")
STOCK_SIG = "F14CEE321924058BE7D1730D5B696A8DEA1E7462695B6E7E03C6C79054C6453B"

EFFECTS_PREFIX = "assets/effects/"

# Only the old signature is dropped; apksigner writes a new one.
SIGNATURE_RE = re.compile(r"^META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))$")


def effect_sig(effects: dict[str, bytes]) -> str:
    """Same digest the app computes: seed, then each XML in sorted order
    with every character outside the allowed set removed."""
    digest = hashlib.sha256(SEED)
    for name in sorted(effects):
        text = effects[name].decode("utf-8")
        digest.update(STRIP_RE.sub("", text).encode("utf-8"))
    return digest.hexdigest().upper()


def check_dex(name: str, data: bytes) -> None:
    """Fail on the DEX problems that make Android refuse to load a file:
    bad header checksums or an unsorted string table."""
    if data[12:32] != hashlib.sha1(data[32:]).digest():
        raise SystemExit(f"ERROR: {name} has a bad SHA-1 signature")
    if struct.unpack_from("<I", data, 8)[0] != zlib.adler32(data[12:]) & 0xFFFFFFFF:
        raise SystemExit(f"ERROR: {name} has a bad Adler-32 checksum")

    def utf16_units(raw: bytes) -> list[int]:
        units, i = [], 0
        while i < len(raw):
            c = raw[i]
            if c < 0x80:
                units.append(c); i += 1
            elif c & 0xE0 == 0xC0:
                units.append(((c & 0x1F) << 6) | (raw[i + 1] & 0x3F)); i += 2
            else:
                units.append(((c & 0x0F) << 12) | ((raw[i + 1] & 0x3F) << 6)
                             | (raw[i + 2] & 0x3F)); i += 3
        return units

    count, table = struct.unpack_from("<II", data, 56)
    previous = None
    for index in range(count):
        offset = struct.unpack_from("<I", data, table + 4 * index)[0]
        while data[offset] & 0x80:  # skip the ULEB128 length
            offset += 1
        offset += 1
        current = utf16_units(data[offset:data.index(b"\0", offset)])
        if previous is not None and current <= previous:
            raise SystemExit(f"ERROR: {name} string table is out of order at {index}")
        previous = current


def is_top_level_effect(name: str) -> bool:
    rest = name[len(EFFECTS_PREFIX):]
    return name.startswith(EFFECTS_PREFIX) and rest.endswith(".xml") and "/" not in rest


def load_custom(effects_dir: Path) -> dict[str, bytes]:
    files = sorted(effects_dir.glob("*.xml"))
    if not files:
        raise SystemExit(f"ERROR: no .xml files in {effects_dir}")
    return {EFFECTS_PREFIX + p.name: p.read_bytes() for p in files}


def cmd_sig(args: argparse.Namespace) -> None:
    custom = load_custom(Path(args.effects_dir))

    with ZipFile(args.source) as apk:
        stock = {n: apk.read(n) for n in apk.namelist() if is_top_level_effect(n)}

    current = effect_sig(stock)
    if current != STOCK_SIG:
        # The source APK's own effects no longer hash to the value we know
        # the app checks, so this script is out of date for this version.
        raise SystemExit(
            f"ERROR: source effects hash to {current}, expected {STOCK_SIG}. "
            "The app version changed; re-check the integrity constant."
        )

    combined = dict(stock)
    combined.update(custom)

    print(f"OLD_EFFECT_SIG={current}")
    print(f"NEW_EFFECT_SIG={effect_sig(combined)}")


def cmd_build(args: argparse.Namespace) -> None:
    custom = load_custom(Path(args.effects_dir))

    dex_replacements: dict[str, bytes] = {}
    for spec in args.dex or []:
        name, _, path = spec.partition("=")
        if not name.endswith(".dex") or not path:
            raise SystemExit(f"ERROR: bad --dex value {spec!r}")
        dex_replacements[name] = Path(path).read_bytes()
        check_dex(name, dex_replacements[name])

    kept = replaced_effects = dropped = 0
    seen_dex: set[str] = set()

    with ZipFile(args.source) as src, ZipFile(args.output, "w") as dst:
        for info in src.infolist():
            name = info.filename

            if SIGNATURE_RE.match(name):
                dropped += 1
                continue
            if name in custom:
                replaced_effects += 1
                continue

            if name in dex_replacements:
                data = dex_replacements[name]
                seen_dex.add(name)
                print(f"Replaced {name} with rebuilt DEX")
            else:
                data = src.read(name)

            # Keep each entry's compression method so resources.arsc and
            # native libraries stay stored.
            copy = ZipInfo(name, date_time=info.date_time)
            copy.compress_type = info.compress_type
            copy.external_attr = info.external_attr
            copy.create_system = info.create_system
            dst.writestr(copy, data)
            kept += 1

        for name, data in custom.items():
            entry = ZipInfo(name, date_time=(1981, 1, 1, 1, 1, 1))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            dst.writestr(entry, data)
            print(f"Added {name}")

    missing = set(dex_replacements) - seen_dex
    if missing:
        raise SystemExit(f"ERROR: source APK has no {', '.join(sorted(missing))}")

    print(f"Entries copied: {kept}, effects replaced: {replaced_effects}, "
          f"old signature entries dropped: {dropped}")

    # Everything other than the signature, the effects and the swapped DEX
    # files must be unchanged.
    with ZipFile(args.source) as before, ZipFile(args.output) as after:
        after_entries = {e.filename: e for e in after.infolist()}

        for entry in before.infolist():
            name = entry.filename
            if SIGNATURE_RE.match(name) or name in custom or name in dex_replacements:
                continue
            rebuilt = after_entries.get(name)
            if rebuilt is None:
                raise SystemExit(f"ERROR: lost {name}")
            if (rebuilt.CRC, rebuilt.file_size, rebuilt.compress_type) != (
                entry.CRC, entry.file_size, entry.compress_type
            ):
                raise SystemExit(f"ERROR: changed {name}")

        for name, data in custom.items():
            if after.read(name) != data:
                raise SystemExit(f"ERROR: {name} not added correctly")

        resources = after_entries.get("resources.arsc")
        if resources is None or resources.compress_type != ZIP_STORED:
            raise SystemExit("ERROR: resources.arsc must stay stored")

        final = {n: after.read(n) for n in after.namelist() if is_top_level_effect(n)}
        print(f"Effect hash of output: {effect_sig(final)}")

    print("Verified output.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_sig = sub.add_parser("sig")
    p_sig.add_argument("source")
    p_sig.add_argument("effects_dir")
    p_sig.set_defaults(func=cmd_sig)

    p_build = sub.add_parser("build")
    p_build.add_argument("source")
    p_build.add_argument("output")
    p_build.add_argument("effects_dir")
    p_build.add_argument("--dex", action="append",
                         help="NAME=PATH: replace dex entry NAME with the file at PATH")
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
