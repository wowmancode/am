#!/usr/bin/env python3
"""Change the default compiled app_name in resources.arsc without rebuilding resources.

The APK is decoded with apktool -r for DEX patching. Rebuilding its entire
resource table would change unrelated resources, so edit one value in the
table's global UTF-8 string pool and preserve every resource identifier.
"""

import argparse
import struct
from pathlib import Path


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def put32(data, offset, value):
    struct.pack_into("<I", data, offset, value)


def length8(data, offset):
    first = data[offset]
    if first & 0x80:
        return ((first & 0x7f) << 8) | data[offset + 1], offset + 2
    return first, offset + 1


def encode8(value):
    if value < 0x80:
        return bytes([value])
    if value < 0x8000:
        return bytes([0x80 | (value >> 8), value & 0xff])
    raise ValueError("string too long")


def rename(data, old="Alight Motion", new="Alight Motion+"):
    if u16(data, 0) != 0x0002 or u16(data, 2) != 12 or u32(data, 4) != len(data):
        raise ValueError("unsupported Android resource table")
    pool = 12
    if u16(data, pool) != 0x0001 or u16(data, pool + 2) != 28:
        raise ValueError("expected global string pool")
    size = u32(data, pool + 4)
    count = u32(data, pool + 8)
    styles = u32(data, pool + 12)
    flags = u32(data, pool + 16)
    strings_start = u32(data, pool + 20)
    styles_start = u32(data, pool + 24)
    if not flags & 0x100:
        raise ValueError("expected UTF-8 global string pool")
    offsets = [u32(data, pool + 28 + i * 4) for i in range(count)]
    starts = pool + strings_start
    replacement = encode8(len(new)) + encode8(len(new.encode())) + new.encode() + b"\0"
    matches = []
    for index, offset in enumerate(offsets):
        pos = starts + offset
        _, pos = length8(data, pos)
        byte_count, pos = length8(data, pos)
        if data[pos:pos + byte_count] == old.encode() and data[pos + byte_count] == 0:
            matches.append((index, starts + offset, pos + byte_count + 1))
    if len(matches) != 1:
        raise ValueError(f"expected one exact {old!r} value, found {len(matches)}")
    index, begin, end = matches[0]
    change = len(replacement) - (end - begin)
    old_pool = data[pool:pool + size]
    edited = bytearray(old_pool[:begin - pool] + replacement + old_pool[end - pool:])
    for i, offset in enumerate(offsets):
        if offset > offsets[index]:
            put32(edited, 28 + i * 4, offset + change)
    if styles and styles_start:
        put32(edited, 24, styles_start + change)
    padding = (-len(edited)) % 4
    edited.extend(b"\0" * padding)
    put32(edited, 4, len(edited))
    result = bytearray(data[:pool] + edited + data[pool + size:])
    put32(result, 4, len(result))
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_bytes(rename(args.source.read_bytes()))
    print("Updated compiled app label to Alight Motion+")


if __name__ == "__main__":
    main()
