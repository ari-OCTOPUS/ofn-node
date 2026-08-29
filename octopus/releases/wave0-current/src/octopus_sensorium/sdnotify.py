"""systemd Type=notify / watchdog helpers. Does not open /dev/watchdog*."""

from __future__ import annotations

import os
import socket


def _socket_path() -> str | None:
    return os.environ.get("NOTIFY_SOCKET")


def notify(message: str) -> bool:
    path = _socket_path()
    if not path:
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        addr: str | bytes
        if path.startswith("@"):
            addr = "\0" + path[1:]
        else:
            addr = path
        sock.connect(addr)
        sock.sendall(message.encode("utf-8"))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def ready() -> bool:
    return notify("READY=1")


def watchdog() -> bool:
    return notify("WATCHDOG=1")


def stopping() -> bool:
    return notify("STOPPING=1")


def status(text: str) -> bool:
    return notify("STATUS=" + text.replace("\n", " "))
