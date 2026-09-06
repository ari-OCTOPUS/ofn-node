"""glass_runner — اجراکنندهٔ شیشهٔ تلگرام (ماده-۱۰ لین ۴، PR #114→main).

حلقهٔ گمشدهٔ شیشه بود: telegram_glass کاملاً خالص است (route + render +
snapshot builderها) ولی هیچ چیز آپدیت‌های بات را نمی‌خواند و جواب نمی‌داد.
این runner: getUpdates با offset پایدار → فرمان‌های / شیشه → snapshot درست
→ route → render_text → sendMessage به همان چت فرستنده.

قواعد:
  · فقط توکن OWNER (همان مجازِ رأی Q7) — پاسخ فقط به چت‌های مجاز
  · فقط-خواندنی برای دیتا؛ هرگز route خارج از شیشه، هرگز اجرا
  · offset در state/pulse/glass-offset.txt ماندگار تا پیام تکرار نشود
  · بدون توکن/چت = خروج صادقانه با رسید jsonl، نه کرش
  · خیلی-کوش: هر خطا = ردِ آن آپدیت + ادامه؛ سیکل هرگز worker را نمی‌کشد
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parents[1]))
import opslib  # noqa: E402
import owner_notify  # noqa: E402  (secrets loader الگو می‌گیرد)

SCHEMA = "octopus.glass-runner.v1"
OFFSET_FILE = "glass-offset.txt"

# مسیرهای snapshot — فقط از درخت/state مجاز
_DOCTOR_REPORT = Path.home() / "ofn/data/state/doctor/report.json"
_OWNER_QUEUE = opslib.STATE_DIR / "OWNER-QUEUE.md"


def _tg(token: str, method: str, params: dict | None = None,
        timeout: int = 20) -> dict | None:
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _owner_token() -> str:
    for line in (Path.home() / ".config/ofn/secrets.env") \
            .read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        if k.strip() == "OFN_BOT_TOKEN_OWNER":
            return v.strip()
    return ""


def _allowed_chats() -> set[str]:
    env = dict(os.environ)
    for line in (Path.home() / ".config/ofn/secrets.env") \
            .read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return {c.strip() for c in (env.get("OFN_OWNER_USER_IDS") or
                                "").split(",") if c.strip()}


def build_snapshot(command: str) -> dict:
    """snapshot درست برای هر فرمان — از منابع مجاز فقط-خواندن."""
    from ofn.adapters import telegram_glass as tg
    if command == "/status":
        return tg.build_status_snapshot()
    if command == "/money":
        return tg.build_learning_snapshot(
            Path.home() / "ofn/09-LANES/ECONOMIC-LEARNING/runs")
    if command == "/self":
        return tg.build_self_snapshot()
    if command == "/doctor":
        try:
            r = json.loads(_DOCTOR_REPORT.read_text(encoding="utf-8"))
            return {"doctor_snapshot": r, "failed_units":
                    r.get("counts", {}).get("failed", 0)}
        except (OSError, ValueError):
            return {}
    if command == "/queue":
        try:
            return {"owner_queue": _OWNER_QUEUE.read_text(
                encoding="utf-8")[:1500]}
        except OSError:
            return {}
    return {}  # /receipts — receipt های خود شیشه داخل پاسخ‌اند


def process_updates(updates: list[dict], token: str) -> dict:
    allowed = _allowed_chats()
    stats = {"answered": 0, "ignored": 0, "failed": 0}
    from ofn.adapters import telegram_glass as tg
    for u in updates:
        msg = u.get("message") or {}
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        if chat_id not in allowed or not text.startswith(tuple(tg.COMMANDS)):
            stats["ignored"] += 1
            continue
        snap = build_snapshot(text.split()[0].lower())
        try:
            resp = tg.route(text.split()[0].lower(), snap)
            out = tg.render_text(resp)
            ok = _tg(token, "sendMessage",
                     {"chat_id": chat_id, "text": out[:3800]}).get("ok")
            stats["answered" if ok else "failed"] += \
                1 if ok else 1
        except Exception as e:  # noqa: BLE001 — خیلی‌کوش
            stats["failed"] += 1
            opslib.append_jsonl(
                opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                {"event_type": "glass.error",
                 "occurred_at": opslib.now_iso(),
                 "payload": {"command": text[:30],
                             "error": type(e).__name__}})
    return stats


def cycle(state_dir: Path | None = None) -> dict:
    token = _owner_token()
    sd = state_dir or opslib.STATE_DIR
    if not token:
        return {"schema": SCHEMA, "ok": False, "reason": "not-armed"}
    off_path = sd / OFFSET_FILE
    try:
        offset = int(off_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        offset = 0
    res = _tg(token, "getUpdates",
              {"offset": offset + 1, "timeout": 0, "limit": 20})
    updates = (res or {}).get("result", [])
    stats = process_updates(updates, token)
    for u in updates:
        offset = max(offset, int(u.get("update_id", offset)))
    if updates:
        off_path.parent.mkdir(parents=True, exist_ok=True)
        off_path.write_text(str(offset), encoding="utf-8")
    return {"schema": SCHEMA, "ok": True, "offset": offset, **stats}


def main() -> int:
    print(json.dumps(cycle(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
