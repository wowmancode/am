#!/usr/bin/env bash
# Rebuild the DEX that holds Alight Motion's effect-integrity constant,
# with the constant changed from OLD_SIG to NEW_SIG.
#
# The DEX is disassembled and reassembled with smali (via apktool) rather
# than byte-patched: DEX string tables must stay sorted, and swapping the
# hash in place breaks that order, so Android refuses to load the file.
#
# Usage: rebuild-sig-dex.sh <source.apk> <OLD_SIG> <NEW_SIG> <out-dir>
# Prints DEX_NAME=classesN.dex and writes <out-dir>/<DEX_NAME>.

set -euo pipefail

SOURCE="$1"
OLD_SIG="$2"
NEW_SIG="$3"
OUT_DIR="$4"

APKTOOL_VERSION="2.10.0"
APKTOOL_SHA256="c0350abbab5314248dfe2ee0c907def4edd14f6faef1f5d372d3d4abd28f0431"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

curl -sSLf -o "$WORK/apktool.jar" \
  "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar"
echo "$APKTOOL_SHA256  $WORK/apktool.jar" | sha256sum -c - >&2

# -r: leave resources alone; only the code is disassembled.
java -jar "$WORK/apktool.jar" d -r -f -o "$WORK/dec" "$SOURCE" >&2

mapfile -t MATCHES < <(grep -rlF "$OLD_SIG" "$WORK/dec"/smali* || true)

if [ "${#MATCHES[@]}" -ne 1 ]; then
  echo "::error::expected the effect signature in exactly one smali file, found ${#MATCHES[@]}" >&2
  printf '  %s\n' "${MATCHES[@]}" >&2
  exit 1
fi

FILE="${MATCHES[0]}"
REL="${FILE#"$WORK/dec/"}"
echo "Effect signature found in $REL" >&2

sed -i "s/$OLD_SIG/$NEW_SIG/g" "$FILE"
grep -qF "$NEW_SIG" "$FILE"

# smali/ -> classes.dex, smali_classes2/ -> classes2.dex, ...
SMALI_DIR="${REL%%/*}"
if [ "$SMALI_DIR" = "smali" ]; then
  DEX_NAME="classes.dex"
else
  DEX_NAME="${SMALI_DIR#smali_}.dex"
fi

java -jar "$WORK/apktool.jar" b -o "$WORK/rebuilt.apk" "$WORK/dec" >&2

mkdir -p "$OUT_DIR"
unzip -o -q "$WORK/rebuilt.apk" "$DEX_NAME" -d "$OUT_DIR"

if grep -qaF "$OLD_SIG" "$OUT_DIR/$DEX_NAME" || ! grep -qaF "$NEW_SIG" "$OUT_DIR/$DEX_NAME"; then
  echo "::error::rebuilt $DEX_NAME does not carry the new effect signature" >&2
  exit 1
fi

echo "DEX_NAME=$DEX_NAME"
