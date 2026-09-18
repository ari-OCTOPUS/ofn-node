#!/bin/bash
# OCTOPUS board 138 -> laptop hub telemetry pulse.
# Emits ONE fixed 140-byte JSON heartbeat on octopus.telemetry.138.heartbeat to the local
# NATS leaf client port (127.0.0.1:4223). Stateless: writes nothing to disk.
set -euo pipefail
exec /usr/bin/python3 - <<'PY'
import socket, json, datetime, sys

SUBJ = "octopus.telemetry.138.heartbeat"
# 160B frame: the hub consumer reads `nats_leaf_active` (the same key every
# other node publishes); the old key `leaf` made the row render leaf=None.
SIZE = 160
try:
    _s = socket.create_connection(("127.0.0.1", 4223), timeout=2)
    _s.close()
    _leaf = True
except OSError:
    _leaf = False
now = datetime.datetime.now(datetime.timezone.utc)
base = {"node": "138", "host": "DietPi", "utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "svc": "nats-leaf", "event": "pulse",
        "load1": round(float(open("/proc/loadavg").read().split()[0]), 2),
        "nats_leaf_active": _leaf}
payload = None
for n in range(0, 200):
    rec = dict(base)
    if n:
        rec["pad"] = " " * n
    p = json.dumps(rec, separators=(",", ":")).encode()
    if len(p) == SIZE:
        payload = p
        break
    if len(p) > SIZE:
        break
if payload is None:
    print("PULSE_FAIL could_not_build_%dB_frame" % SIZE)
    sys.exit(1)
try:
    s = socket.create_connection(("127.0.0.1", 4223), timeout=5)
    s.recv(4096)
    s.sendall(b'CONNECT {"verbose":false,"pedantic":false,"name":"pulse-138","lang":"py","version":"1.0"}\r\n')
    s.sendall(b"PUB " + SUBJ.encode() + b" " + str(len(payload)).encode() + b"\r\n" + payload + b"\r\n")
    s.sendall(b"PING\r\n")
    r = s.recv(64)
    s.close()
    ok = r.startswith(b"PONG")
except Exception as e:
    print("PULSE_FAIL", type(e).__name__, e)
    sys.exit(1)
print("PULSE_SENT bytes=%d subject=%s ok=%s" % (len(payload), SUBJ, ok))
sys.exit(0 if ok else 1)
PY
