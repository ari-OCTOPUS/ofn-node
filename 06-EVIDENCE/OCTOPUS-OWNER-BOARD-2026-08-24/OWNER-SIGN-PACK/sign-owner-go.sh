#!/usr/bin/env bash
# OWNER-SIGN-PACK — OWNER RUNS THIS HIMSELF (never an agent).
# Signs owner-go packet files with the owner's Ed25519 key so boards can
# verify authenticity by signature (fixes S13 name-match class + T-04/T-11).
#
# Usage (from PowerShell):
#   & "C:\Program Files\Git\bin\bash.exe" "./sign-owner-go.sh"            # signs all queue/*.md queue/*.json
#   & "C:\Program Files\Git\bin\bash.exe" "./sign-owner-go.sh" queue/FILE.json
# Output: PACKET.sig (base64) + OWNER-SIGN-MANIFEST.jsonl next to the packets.
# The private key is NEVER printed, copied, or moved. No network. No send.
set -euo pipefail

KEYDIR="$HOME/.octopus-signing"
PRIV="$KEYDIR/octopus-owner-ed25519-private.pem"
PUB="$KEYDIR/octopus-owner-ed25519-public.pem"
[ -f "$PRIV" ] || { echo "ERROR: $PRIV not found" >&2; exit 1; }
[ -f "$PUB" ] || { echo "ERROR: $PUB not found" >&2; exit 1; }

files=()
if [ "$#" -eq 0 ]; then
  for g in queue/*.md queue/*.json; do [ -f "$g" ] && files+=("$g"); done
else
  for a in "$@"; do
    if [ -f "$a" ]; then files+=("$a")
    elif [[ "$a" == *[*]* ]]; then
      for g in $a; do [ -f "$g" ] && files+=("$g"); done
    else
      echo "skip (not a file): $a" >&2
    fi
  done
fi
[ ${#files[@]} -ge 1 ] || { echo "ERROR: no packets found (run from the OWNER-SIGN-PACK folder)" >&2; exit 1; }

FP=$(openssl pkey -pubin -in "$PUB" -outform DER 2>/dev/null | sha256sum | cut -c1-16)
NOW=$(date -u +%FT%TZ)
MANIFEST="$(dirname "${files[0]}")/OWNER-SIGN-MANIFEST.jsonl"

echo "key_fingerprint_sha256_16=$FP  (identity only — no key material leaves this machine)"
: > "$MANIFEST"
for f in "${files[@]}"; do
  SHA=$(sha256sum "$f" | cut -d' ' -f1)
  SIG=$(openssl pkeyutl -sign -inkey "$PRIV" -rawin -in "$f" 2>/dev/null | base64 -w0)
  SIGFILE="$f.sig"
  printf '%s' "$SIG" > "$SIGFILE"
  printf '{"file":"%s","sha256":"%s","sig_b64":"%s","key_fp16":"%s","signed_at_utc":"%s","scheme":"ed25519-pure"}\n' \
    "$(basename "$f")" "$SHA" "$SIG" "$FP" "$NOW" >> "$MANIFEST"
  echo "SIGNED $(basename "$f") sha=${SHA:0:12}... -> $(basename "$SIGFILE")"
done
echo "manifest: $MANIFEST"
echo "done. now tell the agent 'امضا شد' — it transports sigs+manifest to board138 WITH receipt (transport only, after your word)."
