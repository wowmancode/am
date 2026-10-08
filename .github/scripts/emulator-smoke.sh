#!/usr/bin/env bash
# Install the custom APK on a running emulator, launch it, and record what
# happens: periodic screenshots, the crash buffer and app logs.
# Exits non-zero if the app process dies.
#
# Usage: emulator-smoke.sh <apk> <out-dir> [steps-script]
# The optional steps script is sourced after launch with PKG and OUT set,
# for driving the UI (adb shell input ...) and taking extra screenshots.

set -uo pipefail

APK="$1"
OUT="$2"
STEPS="${3:-}"
mkdir -p "$OUT"

shot() { adb exec-out screencap -p > "$OUT/$1.png" 2>/dev/null || true; }

adb wait-for-device
adb shell 'while [ "$(getprop sys.boot_completed)" != "1" ]; do sleep 2; done'
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

adb install -r -g "$APK" | tee "$OUT/install.txt"

PKG="$(adb shell pm list packages | tr -d '\r' | sed -n 's/^package://p' | grep -m1 '^com\.alightcreative\.motion\.')"
if [ -z "$PKG" ]; then
  echo "::error::custom package not installed"
  exit 1
fi
echo "Package: $PKG"
export PKG OUT

adb logcat -c
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null

alive() { [ -n "$(adb shell pidof "$PKG" | tr -d '\r')" ]; }

STATUS=0
# The effect-integrity check fires on a background thread up to ~15 s after
# start, so watch for longer than that.
for t in 3 8 15 25 40; do
  sleep $(( t - ${prev:-0} )); prev=$t
  shot "launch-${t}s"
  if ! alive; then
    echo "::error::app process died within ${t}s of launch"
    STATUS=1
    break
  fi
done

if [ "$STATUS" -eq 0 ] && [ -n "$STEPS" ]; then
  # shellcheck disable=SC1090
  . "$STEPS" || STATUS=1
  if ! alive; then
    echo "::error::app process died while running $STEPS"
    STATUS=1
  fi
fi

adb logcat -d -b crash > "$OUT/crash.txt" 2>&1 || true
adb logcat -d -v time > "$OUT/logcat.txt" 2>&1 || true
grep -E "FATAL EXCEPTION|AndroidRuntime|EffectIntegrity|ShaderCompile|CustomFx|GradientEdit" "$OUT/logcat.txt" | head -80 || true

if [ -s "$OUT/crash.txt" ]; then
  echo "=== crash buffer ==="
  head -60 "$OUT/crash.txt"
  STATUS=1
fi

exit "$STATUS"
