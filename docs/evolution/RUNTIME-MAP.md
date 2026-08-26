# RUNTIME-MAP — BOARD 180

scope: this_host_only | vantage: loopback + local-disk | method: systemd/proc read-only

## سرویس‌های systemd (octopus-*)
| unit | state | ExecStart | User | bind |
|---|---|---|---|---|
| octopus-gateway | active/running | uvicorn app:app --host 0.0.0.0 --port 8780 --no-server-header | root | 0.0.0.0:8780 |
| octopus-organism-lab | active/running | /opt/octopus/lab/bin/start-organism.sh | root | 127.0.0.1:8090 + 192.168.0.180:8090 |
| octopus-llama-lab | active/running | (llama.cpp server) | root | 127.0.0.1:8081 |
| octopus-afferent-lab | active/running | LAN watch + owner letters | root | — |
| octopus-soak-lab | active/running | soak observer | root | — |
| octopus-heartbeat | activating(start) | ICMP heartbeat | root | — |
| octopus-first-stage-proof | active/exited | one-shot post-reboot proof | root | — |
| octopus-mirror | inactive/dead | one-way pull | root | — |

## organism runtime (PID 42687)
- cmdline: `python3 -m ofn.organism.runtime.app --db /opt/octopus/lab/lab-data/organism.db --host 127.0.0.1 --port 8090 --heartbeat-interval 180 --pid-file /opt/octopus/lab/receipts/organism.pid`
- cwd → /opt/octopus/lab ; exe → /usr/bin/python3.13 ; PYTHONPATH=/opt/octopus/lab
- env (redacted): OCTOPUS_GET_PURE=1, OCTOPUS_REQUIRE_LAN_TOKEN=<redacted>, OCTOPUS_LEARN_EXTERNAL=0, OCTOPUS_LAN_TOKEN=<redacted>
- runtime↔code: app.py sha256 0e881b7fa7025269 (31235 bytes), mtime 2026-08-25T13:09Z < proc start 13:17Z → NOT diverged (REPO_VERIFIED).

## نکتهٔ bind (مهم)
cmdline می‌گوید `--host 127.0.0.1` ولی listenerها هم `127.0.0.1:8090` و هم `192.168.0.180:8090` را نشان می‌دهند (هر دو PID 42687). یعنی app یک socket دوم روی LAN باز می‌کند که با LAN token محافظت می‌شود (app.py: LAN_BIND_HOST="192.168.0.180"). این یک سطح دسترسی LAN است، نه صرفاً loopback → در SECURITY-BOUNDARIES ثبت شد.

## گذرگاه‌های دیگر
- containerd loopback: 127.0.0.1:40105 ; node dev ports 41829/44981 (cursor server).
- gateway 8780 روی 0.0.0.0 اما per app.py فقط read endpoints (`/status`,`/health`,`/openapi.json`)، بدون command surface.
