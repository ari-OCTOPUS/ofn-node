"""mining_switch_receipt.py — رسیدِ سوییچِ کوین/الگوریتم (D-015).

رأیِ مالک: سوییچ روی نودهای مالک **خودکار + رسید**، بدونِ اجازهٔ موردی.
هیچ پولی جابه‌جا نمی‌شود؛ فقط ثبت.

append-only JSONL. صفر SSH، صفر شبکه، صفر side-effect روی نود.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_VAULT = _HERE.parents[1]
_DEFAULT_PATH = _VAULT / "_ops" / "state" / "mining-switch-receipts.jsonl"


def _path() -> Path:
    """مسیرِ فایلِ رسید؛ قابل‌تغییر با env var برای تست."""
    return Path(os.environ.get("OCTOPUS_MINING_SWITCH_RECEIPT_FILE", str(_DEFAULT_PATH)))


def _iso(ts: float | None = None) -> str:
    """timestamp به ISO 8601."""
    dt = datetime.fromtimestamp(ts or time.time(), tz=timezone.utc)
    return dt.isoformat(timespec="seconds")


def record_switch(*, node_id: str, from_coin: str, to_coin: str,
                  algo: str = "", now: float | None = None) -> dict:
    """یک ردیفِ رسید به JSONL اضافه می‌کند (append مستقیم، اتمیک).

    خروجی: ردیفِ نوشته‌شده (dict).
    """
    ts = now or time.time()
    row = {"ts": _iso(ts), "node": node_id, "from": from_coin,
           "to": to_coin, "algo": algo}
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def recent_switches(n: int = 10) -> list:
    """آخرین n رسید (برعکسِ زمانی). fail-soft."""
    try:
        lines = _path().read_text("utf-8").strip().splitlines()
    except (OSError, ValueError):
        return []
    rows = []
    for line in reversed(lines):
        try:
            rows.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
    return rows[:n]


def receipt_text(node_id: str, from_coin: str, to_coin: str,
                 *, now: float | None = None) -> str:
    """متنِ رسید برای تلگرام (HTML امن).

    صادقانه: فقط «ثبت شد»، نه «اجرا شد» — چون مسیرِ زنده اثبات‌نشده (D-20).
    """
    return (f"\U0001f501 سوییچِ کوین · نود {node_id} · "
            f"{from_coin} → {to_coin} · ثبت شد "
            f"(خودکار، D-015)")


if __name__ == "__main__":
    r = record_switch(node_id="TEST", from_coin="VRSC", to_coin="SAL")
    print(json.dumps(r, ensure_ascii=False, indent=2))
