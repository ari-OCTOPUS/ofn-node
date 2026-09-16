# OWNER-SIGN — Checkpoint 348 / امضای مالک — چک‌پوینت ۳۴۸

**EN:** Owner (ari) signs. Agent does NOT touch any private key.
**FA:** مالک (اری) امضا می‌کند. عامل به کلید خصوصی دست نمی‌زند.

## File / فایل
- Path: `F:\backup\06-EVIDENCE\OCTOPUS-CKPT348-OWNER-SIGN-2026-08-22\payload\checkpoint.unsigned.json`
- sequence: **348**
- file SHA256: `sha256:30c2d77123516caef620228b0809127a16759749f30729b44d8d13ef41b8a086`
- expected head_hash (Pi hunt): `sha256:be872007d0383c748cae080e94fc39ae773042acba673402b3e8b0f05873040e`
- re-verified after copy: **MATCH** / تطابق

## Before sign / قبل از امضا
1. Confirm head_hash matches above.
2. Confirm sequence is 348.
3. Only then sign.

## How to sign / نحوه امضا

### A) Preferred — same folder bat
From Explorer or cmd, run:
`
F:\backup\06-EVIDENCE\OCTOPUS-CKPT348-OWNER-SIGN-2026-08-22\payload\sign-checkpoint.bat
`
Requires Owner's root-v2 private key in one of the paths the script looks for (Owner only). Outputs under `payload\SIGNED-CHECKPOINT-BUNDLE\`.

### B) Fallback — openssl (owner-runbook pattern) AFTER hash match
Only if bat/PyNaCl path unavailable. After SHA256/head_hash match:
`
openssl pkeyutl -sign -inkey "<OWNER_PRIVATE_PEM>" -rawin -in checkpoint.unsigned.json -out checkpoint.unsigned.json.sig
`
(Use Owner key path from your runbook; never paste key contents into chat.)

## Rules / قوانین
- No agent signing. No reading private key into chat.
- Stop if head_hash ≠ expected.
