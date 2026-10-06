#!/usr/bin/env python3
"""Copy an APK and add effect XML files to assets/effects/.

    add-effects.py source.apk output.apk [effects_dir]

Without effects_dir the APK is only repacked, which gives a control build for
telling "the repack broke it" apart from "the effects broke it".

Only the old signature is dropped. Every other entry is copied with its
original compression method, so resources.arsc and the native libraries stay
stored. The script then re-reads both archives and fails if any entry differs.
"""

import re
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

TARGET_DIR = "assets/effects/"

# Other META-INF entries (service files, version markers) are part of the app.
SIGNATURE = re.compile(r"^META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))$")


def main() -> None:
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)

    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    effects = []

    if len(sys.argv) == 4:
        effects_dir = Path(sys.argv[3])
        effects = sorted(effects_dir.glob("*.xml"))
        if not effects:
            raise SystemExit(f"ERROR: no effect files found in {effects_dir}")

    new_names = {TARGET_DIR + path.name for path in effects}
    kept = replaced = dropped_signature = 0

    with ZipFile(source) as src, ZipFile(output, "w") as dst:
        for info in src.infolist():
            if SIGNATURE.match(info.filename):
                dropped_signature += 1
                continue

            if info.filename in new_names:
                replaced += 1
                continue

            copy = ZipInfo(info.filename, date_time=info.date_time)
            copy.compress_type = info.compress_type
            copy.external_attr = info.external_attr
            copy.create_system = info.create_system
            dst.writestr(copy, src.read(info.filename))
            kept += 1

        for path in effects:
            entry = ZipInfo(TARGET_DIR + path.name, date_time=(1981, 1, 1, 1, 1, 1))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            dst.writestr(entry, path.read_bytes())
            print("Added:", entry.filename)

    print("Entries copied unchanged:", kept)
    print("Existing effect entries replaced:", replaced)
    print("Old signature entries dropped:", dropped_signature)

    with ZipFile(source) as before, ZipFile(output) as after:
        after_entries = {entry.filename: entry for entry in after.infolist()}

        for entry in before.infolist():
            name = entry.filename
            if SIGNATURE.match(name) or name in new_names:
                continue

            rebuilt = after_entries.get(name)
            if rebuilt is None:
                raise SystemExit(f"ERROR: lost {name}")

            if (rebuilt.CRC, rebuilt.file_size, rebuilt.compress_type) != (
                entry.CRC,
                entry.file_size,
                entry.compress_type,
            ):
                raise SystemExit(f"ERROR: changed {name}")

        for path in effects:
            rebuilt = after_entries.get(TARGET_DIR + path.name)
            if rebuilt is None or after.read(rebuilt) != path.read_bytes():
                raise SystemExit(f"ERROR: {path.name} was not added correctly")

        resources = after_entries.get("resources.arsc")
        if resources is None or resources.compress_type != ZIP_STORED:
            raise SystemExit("ERROR: resources.arsc must stay stored")

    print("Verified every original entry is unchanged.")


main()
