#!/usr/bin/env bash
# Run once with a GitHub account that can manage Actions secrets for this repo.
# Keep the keystore and password file: losing them breaks update compatibility.
set -euo pipefail
umask 077

REPO=wowmancode/am
KEY_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/alight-motion-plus"
KEY_FILE="$KEY_DIR/update.keystore"
PASSWORD_FILE="$KEY_DIR/update-password"
ALIAS=alightmotionplus

for tool in gh keytool openssl base64 tr; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done

mkdir -p "$KEY_DIR"
if [[ -e "$KEY_FILE" && ! -e "$PASSWORD_FILE" ]] ||
   [[ ! -e "$KEY_FILE" && -e "$PASSWORD_FILE" ]]; then
  echo "Signing key or password is missing. Restore both from backup before continuing." >&2
  exit 1
fi

if [[ ! -e "$KEY_FILE" ]]; then
  openssl rand -hex 32 > "$PASSWORD_FILE"
  PASSWORD="$(cat "$PASSWORD_FILE")"
  keytool -genkeypair -noprompt -keystore "$KEY_FILE" \
    -storetype PKCS12 -storepass "$PASSWORD" -keypass "$PASSWORD" \
    -alias "$ALIAS" -keyalg RSA -keysize 3072 -validity 10000 \
    -dname 'CN=Alight Motion Plus Update Key' >/dev/null
fi

PASSWORD="$(cat "$PASSWORD_FILE")"
keytool -list -keystore "$KEY_FILE" -storepass "$PASSWORD" -alias "$ALIAS" >/dev/null

# gh encrypts each secret locally before sending it to GitHub.
base64 < "$KEY_FILE" | tr -d '\n' | gh secret set PATCH_KEYSTORE_B64 --repo "$REPO"
printf '%s' "$PASSWORD" | gh secret set PATCH_KEYSTORE_PASSWORD --repo "$REPO"
printf '%s' "$PASSWORD" | gh secret set PATCH_KEY_PASSWORD --repo "$REPO"
printf '%s' "$ALIAS" | gh secret set PATCH_KEY_ALIAS --repo "$REPO"

echo "Persistent signing secrets uploaded to $REPO."
echo "Back up $KEY_FILE and $PASSWORD_FILE in a secure location."
gh workflow run build-patched-apk.yml --repo "$REPO"
echo "Build started. This first persistently signed APK needs one final reinstall."
