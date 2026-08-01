"""mining_swap_card.py — کارتِ پیشنهادِ swapِ یک‌ضربه‌ای (D-016).

رأیِ مالک: کارتِ پیشنهادِ swap = یک تپ (بدونِ تأییدِ دوم، بدونِ مهلت).
ولی طبقِ D-11: ایجنت به کیف پول دسترسی ندارد. تپ فقط «تأیید ثبت شد» است.
idempotency روی تصمیم لازم است تا کارتِ کهنه دوباره اجرا نشود.

هیچ SSH، هیچ کیف پولی، هیچ شبکه‌ای. فقط فایلِ حالت + متن.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_VAULT = _HERE.parents[1]
_DEFAULT_PATH = _VAULT / "_ops" / "state" / "mining-swap-decisions.json"


def _path() -> Path:
    """مسیرِ فایلِ تصمیم‌ها؛ قابل‌تغییر با env var برای تست."""
    return Path(os.environ.get("OCTOPUS_MINING_SWAP_DECISION_FILE", str(_DEFAULT_PATH)))


def _iso(ts: float | None = None) -> str:
    dt = datetime.fromtimestamp(ts or time.time(), tz=timezone.utc)
    return dt.isoformat(timespec="seconds")


def _load() -> list[dict]:
    """خواندنِ لیستِ تصمیم‌ها. fail-soft → []."""
    try:
        text = _path().read_text("utf-8").strip()
        if not text:
            return []
        return json.loads(text)
    except (OSError, ValueError, json.JSONDecodeError):
        return []


def _save(decisions: list[dict]) -> None:
    """نوشتنِ اتمیک: .tmp + os.replace."""
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), "utf-8")
        os.replace(str(tmp), str(p))
    except OSError:
        pass


def _make_id(from_coin: str, to_coin: str, ts: float) -> str:
    """هشِ کوتاه از from+to+ts (زمانی ثانیه‌ای)."""
    blob = f"{from_coin}:{to_coin}:{ts:.0f}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def _find_pending(from_coin: str, to_coin: str, decisions: list[dict]) -> dict | None:
    """اگر پیشنهادِ pending با همان from/to هست، همان را برگردان (idempotency)."""
    for d in decisions:
        if (d.get("status") == "pending"
                and d.get("from") == from_coin
                and d.get("to") == to_coin):
            return d
    return None


def propose_swap(*, from_coin: str, to_coin: str, reason: str = "",
                 now: float | None = None) -> dict:
    """یک پیشنهادِ تازه می‌سازد (یا existing pending را برمی‌گرداند).

    idempotency روی تصمیم: اگر از قبل pending با همان from/to هست، تازه نمی‌سازد.
    """
    decisions = _load()
    existing = _find_pending(from_coin, to_coin, decisions)
    if existing:
        return existing

    ts = now or time.time()
    entry = {
        "id": _make_id(from_coin, to_coin, ts),
        "from": from_coin,
        "to": to_coin,
        "reason": reason,
        "status": "pending",
        "proposed_ts": _iso(ts),
    }
    decisions.append(entry)
    _save(decisions)
    return entry


def owner_approved(swap_id: str, *, now: float | None = None) -> dict:
    """تپِ مالک: status → owner_approved."""
    decisions = _load()
    for d in decisions:
        if d.get("id") == swap_id and d.get("status") == "pending":
            d["status"] = "owner_approved"
            d["approved_ts"] = _iso(now or time.time())
            _save(decisions)
            return d
    return {"error": "swap not found or not pending", "id": swap_id}


def owner_approval_text(swap_id: str) -> str:
    """متنِ تأییدِ مالک — صادقانه: اجرا با خودت (D-11)."""
    return (f"\u2705 تأییدِ مالک ثبت شد · "
            f"اجرا با خودت (D-11: ایجنت به کیف پول دسترسی ندارد)")


def card_text() -> str:
    """متنِ کارتِ swap برای تلگرام.

    هر پیشنهادِ pending را نشان می‌دهد. دکمه‌ها را center.py می‌سازد؛ این فقط متن.
    """
    decisions = _load()
    pending = [d for d in decisions if d.get("status") == "pending"]
    if not pending:
        return ""
    lines = ["\U0001f4b0 پیشنهادِ swap"]
    for d in pending:
        sid = d.get("id", "?")
        fr = d.get("from", "?")
        to = d.get("to", "?")
        reason = d.get("reason", "")
        line = f"  {fr} \u2192 {to}"
        if reason:
            line += f" ({reason})"
        line += f" · یک تپ = تأییدِ تو (اجرای swap با خودت)"
        lines.append(line)
        lines.append(f"  callback_data: mo:swap:{sid}")
    return "\n".join(lines)


if __name__ == "__main__":
    r = propose_swap(from_coin="VRSC", to_coin="SAL", reason="test")
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("---")
    print(card_text())
