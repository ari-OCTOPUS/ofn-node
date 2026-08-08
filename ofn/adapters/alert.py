"""Owner alert notifier: Telegram (opt-in) + durable local log.

This is the *one* outbound path the node opens on its own — and only for a
service that has crashed, which is the one event the owner cannot see by
looking at the panel (the panel is served by the service that just died).

Two layers, deliberately separate:

  1. A local log line, always. Survives power cuts, needs no network, and is
     the fallback when (2) is off or fails. This is the same posture as the
     backup-alert unit: a durable local mark, not a notification channel.

  2. A Telegram message, only when OFN_ALERT_TELEGRAM=1 is set explicitly.
     The bot token and chat IDs come from the secrets env at call time and
     are never stored here. Default off because every other outbound path
     on this node is gated behind the owner's finger, and an unsolicited
     message is the one path that must not become ambient.

Both layers are best-effort: a notifier that raises masks the alert it was
supposed to deliver. Failures are swallowed and returned, not raised.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Iterable

# Where the local alert log lives. Same directory the backup-alert unit
# writes to, so there is one place to look.
DEFAULT_LOG_PATH = os.path.expanduser("~/.local/share/ofn/service-alerts.log")

# Hard cap on message size; Telegram's limit is 4096 but an alert should be
# short enough to read on a phone notification without opening the chat.
MAX_TEXT_LEN = 800

_TELEGRAM_API = "https://api.telegram.org"


def _append_local_log(path: str, text: str) -> None:
    """Write one line to the alert log. Best-effort: never raises."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            from datetime import datetime
            ts = datetime.now().astimezone().isoformat(timespec="seconds")
            # Collapse newlines so one alert = one line in the log; without
            # this a forged alert body could forge an extra log line.
            safe = " ".join(text.split())
            f.write(f"{ts} {safe}\n")
    except OSError:
        pass


def _send_telegram(token: str, chat_ids: Iterable[str], text: str) -> list[str]:
    """Send to every chat id. Returns the list of ids that succeeded.

    Uses urllib, not requests, because this node has no third-party HTTP
    library by policy (http_api.py enforces the same for its server side).
    Timeout is short: if Telegram is unreachable, holding the alert path
    open for 30s means systemd may kill the unit before the local log write.
    """
    sent: list[str] = []
    body = text[:MAX_TEXT_LEN]
    for chat_id in chat_ids:
        chat_id = str(chat_id).strip()
        if not chat_id or not token:
            continue
        url = f"{_TELEGRAM_API}/bot{token}/sendMessage"
        payload = urllib.parse.urlencode({
            "chat_id": chat_id, "text": body,
        }).encode()
        try:
            req = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    sent.append(chat_id)
        except Exception:
            # One failed chat must not abort the others or the local log.
            continue
    return sent


def notify(text: str, *,
           log_path: str = DEFAULT_LOG_PATH,
           env: dict[str, str] | None = None) -> dict:
    """Deliver an alert through both layers.

    Always writes the local log. Sends Telegram only when
    OFN_ALERT_TELEGRAM is exactly "1". Returns a dict describing what
    happened, so a caller (or test) can assert both layers without parsing
    log files.

    The env is taken from os.environ by default but is a parameter so tests
    can drive it without polluting the real environment.
    """
    env = env if env is not None else dict(os.environ)
    _append_local_log(log_path, text)

    telegram_enabled = env.get("OFN_ALERT_TELEGRAM", "") == "1"
    if not telegram_enabled:
        return {"ok": True, "logged": True, "telegram": "disabled"}

    token = env.get("OFN_BOT_TOKEN_OWNER", "")
    raw_ids = env.get("OFN_OWNER_USER_IDS", "")
    chat_ids = [c.strip() for c in raw_ids.split(",") if c.strip()]
    if not token or not chat_ids:
        # Flag is on but credentials missing — that is a configuration error
        # worth surfacing in the local log, not silently swallowing.
        _append_local_log(log_path,
                          "ALERT TELEGRAM enabled but token/chat_ids missing")
        return {"ok": True, "logged": True,
                "telegram": "misconfigured"}

    sent = _send_telegram(token, chat_ids, text)
    return {"ok": True, "logged": True,
            "telegram": "sent" if sent else "failed",
            "sent_to": sent}


# ── CLI entry point ──────────────────────────────────────────────────────
# Called by the systemd alert unit. Reads the service name and result from
# argv so the unit file does not need a format string that systemd might
# expand with %. Usage: python3 -m ofn.adapters.alert "ofn" "crashed"
def main(argv: list[str] | None = None) -> int:
    import sys
    args = argv if argv is not None else sys.argv[1:]
    service = args[0] if len(args) > 0 else "unknown-service"
    reason = args[1] if len(args) > 1 else "failed"
    text = f"⚠️ OFN alert: service '{service}' {reason}. " \
           f"Check the board: ssh in and run 'systemctl status {service}'."
    out = notify(text)
    # Print JSON so the journal has a structured record of what was attempted.
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
