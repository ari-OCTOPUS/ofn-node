#!/usr/bin/env python3
"""imap_idle.py — IMAP IDLE push for the inbound edge (EVENT-DRIVEN-OCTOPUS 2026-09-18).

Replaces the 15-min `octopus-imap.timer` and the 2-min `octopus-reply-alert.timer`
as the *trigger*: this daemon holds an IMAP IDLE connection on the funnel Gmail
INBOX and, on server push (new mail), emits ONE `mail_seen` event. The existing
runners (reply_alert.py, imap_listener.py) keep ALL their logic, cursors and
guards; they are simply triggered by the event instead of a clock.

  - emits on startup (catch-up for mail that arrived while down) and on push;
  - re-issues IDLE every IDLE_MAX_S (default 1200s) to stay under Gmail's ~29min limit;
  - reconnect with backoff on any error; never raises out of the loop;
  - rate-limits emits to >= MIN_GAP_S (default 10s) to absorb server bursts;
  - credentials come from the environment (systemd EnvironmentFile), never argv.
"""
from __future__ import annotations

import imaplib
import os
import socket
import sys
import time

sys.path.insert(0, "/home/ari/ofn/tools")
import octopus_events as oe  # noqa: E402

HOST = os.environ.get("OCTOPUS_IMAP_HOST", "imap.gmail.com")
IDLE_MAX_S = float(os.environ.get("OCTOPUS_IDLE_MAX_S", "1200"))
MIN_GAP_S = float(os.environ.get("OCTOPUS_MAIL_MIN_GAP_S", "10"))
BACKOFF_S = float(os.environ.get("OCTOPUS_IMAP_BACKOFF_S", "30"))

_last_emit = [0.0]


def log(msg: str) -> None:
    print("%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), msg), flush=True)


def emit_mail(reason: str, detail: str = "") -> None:
    now = time.time()
    if now - _last_emit[0] < MIN_GAP_S:
        log("emit suppressed (gap) reason=%s" % reason)
        return
    _last_emit[0] = now
    try:
        ev = oe.emit("mail_seen", "mail-%d" % int(now), {"reason": reason, "detail": detail[:80]})
        log("emitted mail_seen %s reason=%s" % (ev["event_id"], reason))
    except Exception as exc:  # noqa: BLE001
        log("emit failed: %s: %s" % (type(exc).__name__, exc))


def idle_once(user: str, pw: str) -> str:
    """One IDLE session. Returns the reason it ended."""
    m = imaplib.IMAP4_SSL(HOST, 993)
    try:
        m.login(user, pw)
        m.select("INBOX", readonly=True)
        log("IDLE session open (user=%s***)" % user[:3])
        emit_mail("connected", "idle session started")
        tag = m._new_tag().decode()
        m.send(("%s IDLE\r\n" % tag).encode())
        while True:
            line = m.readline()
            if not line:
                return "connection-closed"
            if line.startswith(b"+"):
                break
        m.sock.settimeout(IDLE_MAX_S)
        reason = "idle-timeout-refresh"
        try:
            while True:
                line = m.readline()
                if not line:
                    reason = "connection-closed"
                    break
                if b"EXISTS" in line or b"RECENT" in line:
                    reason = "new-mail"
                    break
        except socket.timeout:
            reason = "idle-timeout-refresh"
        finally:
            try:
                m.sock.settimeout(30)
                m.send(b"DONE\r\n")
                m.readline()
            except Exception:  # noqa: BLE001
                pass
        return reason
    finally:
        try:
            m.logout()
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    user = os.environ.get("GMAIL_ADDRESS", "")
    pw = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not (user and pw):
        log("NO_CREDS — exiting (systemd will retry)")
        return 2
    while True:
        try:
            reason = idle_once(user, pw)
            log("idle ended: %s" % reason)
            if reason == "new-mail":
                emit_mail("new-mail", "server push")
            if not oe.beat_fresh():
                log("beat stale — still emitting; the gate is what refuses to run runners")
        except Exception as exc:  # noqa: BLE001 — daemon must survive everything
            log("error: %s: %s — backoff %ss" % (type(exc).__name__, exc, BACKOFF_S))
            time.sleep(BACKOFF_S)
        else:
            time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
