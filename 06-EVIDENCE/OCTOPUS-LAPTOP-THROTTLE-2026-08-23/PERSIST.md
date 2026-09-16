# Persist throttle

- Runtime: `_ops/scripts/octopus_throttle_now.py` (re-run anytime)
- organism.py: applies BelowNormal at process start on Windows
- cloudflared tunnels (cp + miniapp) kept; set Idle via throttle script
- TICK_SECONDS already 300 — hitch-every-few-seconds is NOT organism tick
