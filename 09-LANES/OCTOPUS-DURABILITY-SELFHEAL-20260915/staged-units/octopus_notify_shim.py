#!/usr/bin/env python3
"""octopus_notify_shim — systemd Type=notify watchdog shim, zero dependencies.

Runs the real worker as a child; announces READY once, pings WATCHDOG every
10s while the child lives (WatchdogSec=30 in the units), propagates the exit
code. Notify is spoken directly to $NOTIFY_SOCKET (unix datagram) so
python3-systemd is NOT required on the target node.

Deploy path (staged): /opt/octopus-worker/octopus_notify_shim.py
"""
import os
import socket
import subprocess
import sys
import time

PING_INTERVAL_S = 10.0


def notify(msg: str) -> None:
    sock_path = os.environ.get("NOTIFY_SOCKET")
    if not sock_path:
        return
    if sock_path.startswith("@"):
        sock_path = "\0" + sock_path[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
            s.connect(sock_path)
            s.sendall(msg.encode("utf-8"))
    except OSError:
        pass  # journald absence must not kill the worker


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: octopus_notify_shim.py <real-command> [args...]", file=sys.stderr)
        return 2
    proc = subprocess.Popen(sys.argv[1:])
    notify("READY=1\n")
    while True:
        rc = proc.poll()
        if rc is not None:
            notify(f"STOPPING=1\nSTATUS=exited {rc}\n")
            return rc
        notify("WATCHDOG=1\n")
        time.sleep(PING_INTERVAL_S)


if __name__ == "__main__":
    raise SystemExit(main())
