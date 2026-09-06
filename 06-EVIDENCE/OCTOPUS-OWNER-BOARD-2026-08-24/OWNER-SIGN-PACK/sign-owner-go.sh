#!/usr/bin/env bash
# OWNER-SIGN-PACK — OWNER RUNS THIS HIMSELF (never an agent).
# Signs owner-go packet files with the owner's Ed25519 key so boards can
# verify authenticity by signature (fixes S13 name-match class + T-04/T-11).
# Usage:  bash sign-owner-go.sh PACKET1.json PACKET2.json ...
# Output: PACKET.sig (base64) + OWNER-SIGN-MANIFEST.jsonl next to the packets.
# The private key is NEVER printed, copied, or moved. No network. No send.
set -euo pipefail

KEYDIR="$HOME/.octopus-signing"
PRIV="$KEYDIR/octopus-owner-ed25519-private.pem"
PUB="$KEYDIR/octopus-owner-ed25519-public.pem"
[ -f "$PRIV" ] || { echo "ERROR: $PRIV not found" >&2; exit 1; }
[ -f "$PUB" ] || { echo "ERROR: $PUB not found" >&2; exit 1; }
[ "$#" -ge 1 ] || { echo "usage: $0 packet.json [more.json ...]" >&2; exit 1; }

FP=$(openssl pkey -pubin -in "$PUB" -outform DER 2>/dev/null | sha256sum | cut -c1-16)
NOW=$(date -u +%FT%TZ)
MANIFEST="$(dirname "$1")/OWNER-SIGN-MANIFEST.jsonl"

echo "key_fingerprint_sha256_16=$FP  (identity only — no key material leaves this machine)"
: > "$MANIFEST"
for f in "$@"; do
  [ -f "$f" ] || { echo "skip (not a file): $f" >&2; continue; }
  SHA=$(sha256sum "$f" | cut -d' ' -f1)
  SIG=$(openssl pkeyutl -sign -inkey "$PRIV" -rawin -in "$f" 2>/dev/null | base64 -w0)
  SIGFILE="$f.sig"
  printf '%s' "$SIG" > "$SIGFILE"
  printf '{"file":"%s","sha256":"%s","sig_b64":"%s","key_fp16":"%s","signed_at_utc":"%s","scheme":"ed25519-pure"}\n' \
    "$(basename "$f")" "$SHA" "$SIG" "$FP" "$NOW" >> "$MANIFEST"
  echo "SIGNED $(basename "$f") sha=${SHA:0:12}… -> $(basename "$SIGFILE")"
done
echo "manifest: $MANIFEST"
echo "next: transfer the .sig files + manifest to board138 state/owner-go/ and run the verifier (agent does transport WITH receipt, only after you say go)."
