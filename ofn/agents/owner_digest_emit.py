#!/usr/bin/env python3
"""owner_digest_emit — weekday morning/evening owner Telegram digests (138).
Additive under SEC-TG-RICH-DIGEST. RO SoT reads only. No secrets in body.
Usage: owner_digest_emit.py --card-type digest_morning|digest_evening
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/home/ari/ofn")

from ofn.agents.owner_notify import send  # noqa: E402

TZ = ZoneInfo("Australia/Sydney")
STATE = Path("/home/ari/ofn/state/owner_dialogue")
CAP_FILE = STATE / "digest_daily_cap.json"
DEDUP_FILE = STATE / "digest_dedup.json"
QUEUE_JSONL = STATE / "owner_queue.jsonl"
MAX_CHARS = 800
DAILY_CAP = 6
DEDUP_MIN = 60

FORBIDDEN = re.compile(
    r"(bot\d+:|cookie|password|tfn|api[_-]?key|Bearer\s|[A-Za-z0-9_-]{40,})",
    re.I,
)


def now_sydney() -> datetime:
    return datetime.now(TZ)


def load_json(path: Path, default):
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

POLICY_FILE = STATE / "notify_cap_policy.json"


def daily_cap_limit() -> int | None:
    """None = no ceiling (unstable). int = hard daily cap."""
    pol = load_json(POLICY_FILE, {})
    if pol.get("daily_send_cap") is None and pol.get("mode") == "no_cap_until_stable":
        return None
    if "daily_send_cap" in pol and pol["daily_send_cap"] is None:
        return None
    try:
        return int(pol.get("daily_send_cap", DAILY_CAP))
    except Exception:
        return DAILY_CAP


def day_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def cap_ok(dt: datetime) -> tuple[bool, int]:
    data = load_json(CAP_FILE, {})
    k = day_key(dt)
    spent = int(data.get(k, 0) or 0)
    limit = daily_cap_limit()
    if limit is None:
        return True, spent
    return spent < limit, spent


def cap_spend(dt: datetime) -> int:
    data = load_json(CAP_FILE, {})
    k = day_key(dt)
    data[k] = int(data.get(k, 0) or 0) + 1
    # prune old days
    data = {kk: vv for kk, vv in data.items() if kk >= (dt - timedelta(days=14)).strftime("%Y-%m-%d")}
    save_json(CAP_FILE, data)
    return data[k]


def dedup_skip(card_type: str, fingerprint: str, dt: datetime) -> bool:
    data = load_json(DEDUP_FILE, {})
    key = f"{card_type}|{fingerprint}"
    prev = data.get(key)
    if not prev:
        return False
    try:
        prev_dt = datetime.fromisoformat(prev)
        if prev_dt.tzinfo is None:
            prev_dt = prev_dt.replace(tzinfo=TZ)
        if (dt - prev_dt).total_seconds() < DEDUP_MIN * 60:
            return True
    except Exception:
        return False
    return False


def dedup_mark(card_type: str, fingerprint: str, dt: datetime) -> None:
    data = load_json(DEDUP_FILE, {})
    data[f"{card_type}|{fingerprint}"] = dt.isoformat()
    # keep small
    if len(data) > 200:
        items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:100]
        data = dict(items)
    save_json(DEDUP_FILE, data)


def count_open_queue() -> int | None:
    if not QUEUE_JSONL.is_file():
        return None
    n = 0
    try:
        for line in QUEUE_JSONL.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if str(row.get("state", "OPEN")).upper() in {"OPEN", "NOTIFIED", "WAITING_DECISION"}:
                n += 1
        return n
    except Exception:
        return None


def hold_flags() -> dict:
    # RO presence checks — never invent cash
    out = {"hold_customer_send": True, "hold_publish": None}
    candidates = [
        Path("/home/ari/ofn/state/hold_external"),
        Path("/home/ari/ofn/state/HOLD_EXTERNAL"),
        Path("/home/ari/.config/ofn/hold_external"),
    ]
    for p in candidates:
        if p.exists():
            out["hold_publish"] = True
            break
    return out


def build_body(card_type: str, dt: datetime) -> tuple[str, str]:
    q = count_open_queue()
    holds = hold_flags()
    lines = []
    title = (
        f"OCTOPUS DIGEST MORNING {dt.strftime('%Y-%m-%d')}"
        if card_type == "digest_morning"
        else f"OCTOPUS DIGEST EVENING {dt.strftime('%Y-%m-%d')}"
    )
    if card_type == "digest_morning":
        lines.append("صبح‌بخیر — پالس مالک روی درب تلگرام ۱۳۸.")
        lines.append("وضعیت: درب owner_telegram فعال · digests زمان‌بندی‌شده.")
    else:
        lines.append("عصرانه — خلاصه روز روی درب تلگرام ۱۳۸.")
        lines.append("یادآوری: ارسال مشتری / publish فقط با EXECUTE نام‌دار.")
    if q is None:
        lines.append("OWNER_QUEUE: UNKNOWN (فایل صف هنوز نیست)")
    else:
        lines.append(f"OWNER_QUEUE open={q}")
    lines.append(
        f"hold_customer_send=true · hold_publish={'true' if holds.get('hold_publish') else 'UNKNOWN'}"
    )
    lines.append("l1_shadow=false · customer_send=false · secrets_in_card=false")
    lines.append("اگر BLOCKED_ON_OWNER باز است → decision_request یا این digest (cap≤6/روز).")
    body = title + "\n" + "\n".join(lines)
    if len(body) > MAX_CHARS:
        body = body[: MAX_CHARS - 1] + "…"
    if FORBIDDEN.search(body):
        # strip long tokens if any slipped
        body = FORBIDDEN.sub("REDACTED", body)
    fp = hashlib.sha256(f"{card_type}|{day_key(dt)}|{q}".encode()).hexdigest()[:16]
    return body, fp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card-type", required=True, choices=["digest_morning", "digest_evening"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dt = now_sydney()
    # weekdays only (Mon=0..Fri=4)
    if dt.weekday() > 4:
        print("skip_weekend")
        return 0
    ok_cap, spent = cap_ok(dt)
    if not ok_cap:
        print(f"skip_cap spent={spent}")
        return 0
    body, fp = build_body(args.card_type, dt)
    if dedup_skip(args.card_type, fp, dt):
        print("skip_dedup")
        return 0
    print("chars", len(body))
    print("fingerprint", fp)
    if args.dry_run:
        print(body)
        return 0
    r = send(body)
    print("ok", bool(r.get("ok")))
    print("errs_len", len(r.get("errs") or []))
    if r.get("ok"):
        new_spent = cap_spend(dt)
        dedup_mark(args.card_type, fp, dt)
        print("daily_cap_spent", new_spent)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
