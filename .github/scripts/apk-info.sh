#!/usr/bin/env bash
# Print an APK's package name, version and min SDK as KEY=value lines.
#
#   apk-info.sh app.apk [PREFIX]
#
# With PREFIX=SOURCE_ the output is SOURCE_PACKAGE=..., SOURCE_VERSION_CODE=...,
# SOURCE_VERSION_NAME=..., SOURCE_MIN_SDK=...
#
# apkanalyzer reads only the binary manifest, so it works even when the
# resource table is unusual (as it can be in a patched APK). aapt2 is the
# fallback. When a required field is still missing the script exits 1 and puts
# the tool errors in a GitHub annotation, so the cause is visible without
# opening the raw job log.

set -u

APK="${1:?usage: apk-info.sh app.apk [PREFIX]}"
PREFIX="${2:-}"

ERR="$(mktemp)"
trap 'rm -f "$ERR"' EXIT

ANALYZER="$(
  find "${ANDROID_HOME:-/nonexistent}/cmdline-tools" -type f -name apkanalyzer 2>/dev/null |
  sort -V |
  tail -n 1
)"

AAPT2="${BUILD_TOOLS:+$BUILD_TOOLS/aapt2}"

PACKAGE=""
VERSION_CODE=""
VERSION_NAME=""
MIN_SDK=""

analyzer_get() {
  "$ANALYZER" manifest "$1" "$APK" 2>>"$ERR" | tr -d '\r' | sed -n '1p'
}

if [ -n "$ANALYZER" ]; then
  PACKAGE="$(analyzer_get application-id)"
  VERSION_CODE="$(analyzer_get version-code)"
  VERSION_NAME="$(analyzer_get version-name)"
  MIN_SDK="$(analyzer_get min-sdk)"
else
  echo "apkanalyzer not found under ANDROID_HOME=${ANDROID_HOME:-<unset>}" >>"$ERR"
fi

if { [ -z "$PACKAGE" ] || [ -z "$VERSION_CODE" ] || [ -z "$MIN_SDK" ]; } &&
   [ -n "$AAPT2" ] && [ -x "$AAPT2" ]; then
  BADGING="$("$AAPT2" dump badging "$APK" 2>>"$ERR")"

  [ -n "$PACKAGE" ] || PACKAGE="$(
    printf '%s\n' "$BADGING" |
    sed -n "s/^package: name='\([^']*\)'.*/\1/p" | sed -n '1p'
  )"
  [ -n "$VERSION_CODE" ] || VERSION_CODE="$(
    printf '%s\n' "$BADGING" |
    sed -n "s/^package:.*versionCode='\([^']*\)'.*/\1/p" | sed -n '1p'
  )"
  [ -n "$VERSION_NAME" ] || VERSION_NAME="$(
    printf '%s\n' "$BADGING" |
    sed -n "s/^package:.*versionName='\([^']*\)'.*/\1/p" | sed -n '1p'
  )"
  [ -n "$MIN_SDK" ] || MIN_SDK="$(
    printf '%s\n' "$BADGING" |
    sed -n "s/^sdkVersion:'\([^']*\)'.*/\1/p" | sed -n '1p'
  )"
fi

# apkanalyzer prints "(unknown)" style placeholders for absent values.
case "$VERSION_NAME" in
  "(unknown)"|null) VERSION_NAME="" ;;
esac

if [ -z "$PACKAGE" ] || [ -z "$VERSION_CODE" ] || [ -z "$MIN_SDK" ]; then
  DETAILS="$(tr '\n' ' ' <"$ERR" | head -c 900)"
  echo "::error title=Could not read $APK::package='${PACKAGE}' versionCode='${VERSION_CODE}' minSdk='${MIN_SDK}'. ${DETAILS}"
  exit 1
fi

echo "${PREFIX}PACKAGE=$PACKAGE"
echo "${PREFIX}VERSION_CODE=$VERSION_CODE"
echo "${PREFIX}VERSION_NAME=$VERSION_NAME"
echo "${PREFIX}MIN_SDK=$MIN_SDK"
