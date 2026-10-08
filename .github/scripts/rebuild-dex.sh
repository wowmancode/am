#!/usr/bin/env bash
# Rebuild the app's DEX files with exact string-constant replacements.
#
# The code is disassembled and reassembled with smali (via apktool) rather
# than byte-patched: DEX string tables must stay sorted, and changing a
# string in place can break that order, so Android refuses to load the file.
#
# Usage: rebuild-dex.sh <source.apk> <out-dir> OLD=NEW [OLD=NEW ...]
#
# Each OLD must appear as a complete smali string constant ("OLD") at least
# once, or the script fails. Only DEX files whose code changed are written
# to <out-dir>; their names are printed as DEX_NAMES=classes.dex ....

set -euo pipefail

SOURCE="$1"
OUT_DIR="$2"
shift 2

APKTOOL_VERSION="2.10.0"
APKTOOL_SHA256="c0350abbab5314248dfe2ee0c907def4edd14f6faef1f5d372d3d4abd28f0431"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

curl -sSLf -o "$WORK/apktool.jar" \
  "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar"
echo "$APKTOOL_SHA256  $WORK/apktool.jar" | sha256sum -c - >&2

# -r: leave resources alone; only the code is disassembled.
java -jar "$WORK/apktool.jar" d -r -f -o "$WORK/dec" "$SOURCE" >&2

CHANGED_DIRS="$WORK/changed-dirs"
: > "$CHANGED_DIRS"

for PAIR in "$@"; do
  OLD="${PAIR%%=*}"
  NEW="${PAIR#*=}"

  # Match the whole quoted constant so substrings of longer strings are
  # left alone.
  mapfile -t FILES < <(grep -rlF "\"$OLD\"" "$WORK/dec"/smali* || true)
  if [ "${#FILES[@]}" -eq 0 ]; then
    echo "::error::string constant \"$OLD\" not found in the app code" >&2
    exit 1
  fi

  for FILE in "${FILES[@]}"; do
    OLD="$OLD" NEW="$NEW" python3 -I -c '
import os, sys
path = sys.argv[1]
old = "\"" + os.environ["OLD"] + "\""
new = "\"" + os.environ["NEW"] + "\""
text = open(path, encoding="utf-8").read()
open(path, "w", encoding="utf-8").write(text.replace(old, new))
' "$FILE"
    REL="${FILE#"$WORK/dec/"}"
    echo "${REL%%/*}" >> "$CHANGED_DIRS"
  done

  echo "Replaced \"$OLD\" in ${#FILES[@]} file(s)" >&2
done

java -jar "$WORK/apktool.jar" b -o "$WORK/rebuilt.apk" "$WORK/dec" >&2

# smali/ -> classes.dex, smali_classes2/ -> classes2.dex, ...
DEX_NAMES=()
for DIR in $(sort -u "$CHANGED_DIRS"); do
  if [ "$DIR" = "smali" ]; then
    DEX_NAMES+=("classes.dex")
  else
    DEX_NAMES+=("${DIR#smali_}.dex")
  fi
done

mkdir -p "$OUT_DIR"
for DEX in "${DEX_NAMES[@]}"; do
  unzip -o -q "$WORK/rebuilt.apk" "$DEX" -d "$OUT_DIR"
done

# Every replacement must be visible in the rebuilt code.
for PAIR in "$@"; do
  OLD="${PAIR%%=*}"
  NEW="${PAIR#*=}"
  if ! grep -qaF "$NEW" "${DEX_NAMES[@]/#/$OUT_DIR/}"; then
    echo "::error::rebuilt DEX files do not contain \"$NEW\"" >&2
    exit 1
  fi
done

echo "DEX_NAMES=${DEX_NAMES[*]}"
