# LAN token implementation

- Token length: at least 32 bytes. Generated with `head -c 32 /dev/urandom | base64 -w0` into `/etc/octopus/lan-token`.
- Storage: file mode `0600`. Path `OCTOPUS_LAN_TOKEN_FILE` (default `/etc/octopus/lan-token`).
- Not in Git, reports, process argv, or systemd `Environment=` value.
- `OCTOPUS_LAN_TOKEN` is test-only, never a live unit environment.
- Compare: SHA-256 of offered and expected, then `hmac.compare_digest`.
- Missing/invalid token on data paths: `401 {"error":"unauthorized"}` with no token echo.
- Unauthenticated LAN data request is rejected when `OCTOPUS_REQUIRE_LAN_TOKEN=1`.
- Authenticated request with matching header `X-Octopus-Token` is accepted.
- Request body limit: `MAX_REQUEST_BYTES` (16 KiB).
- Failure cooldown: 2s after a failure; 429 after 8 failures in 60s.
- Rotation: write a new 0600 file in place (mtime reload). Restart organism and token-using clients. Keep the previous file copy offline for rollback.
- Loopback policy: `GET /health` on the 127.0.0.1 listener does not require a token. LAN listener `/health` and all `/api/v1/*` require a token.
- No executable endpoint is added. POST `/api/v1/eval` and `/api/v1/ask` stay `executable=false`, WAVE0, `PROPOSE_ONLY`.
