# -*- coding: utf-8 -*-
"""حافظهٔ chord — JSONLِ append-only با hash-chain (الگوی epistemics/epi-ledger).

- مسیرِ پیش‌فرض نسبت به خودِ پکیج resolve می‌شود (نه CWD/env — تلهٔ ORG_ROOT).
- override فقط برای تست: env CHORD_STATE_DIR.
- idempotency: dedup_key تکراریِ آخرین رکورد → skip.
- هرگز روی ledgerِ مالی/state ارگانیسم نمی‌نویسد.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .schemas import sha256_of

_LEDGER_NAME = "chord-ledger.jsonl"


def state_dir() -> Path:
    env = os.environ.get("CHORD_STATE_DIR", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "state"


def ledger_path() -> Path:
    return state_dir() / _LEDGER_NAME


def _last_line(p: Path) -> dict | None:
    try:
        if not p.exists() or p.stat().st_size == 0:
            return None
        with p.open("rb") as f:
            tail = f.read()[-8192:]
        lines = [ln for ln in tail.decode("utf-8", "replace").splitlines() if ln.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception:  # noqa: BLE001 — ledger خواندنی نبود → مثلِ خالی، ولی صادقانه
        return None


def append(record: dict, dedup_key: str = "") -> dict:
    """رکورد را زنجیره‌ای می‌نویسد. خروجی: {ok, skipped?, sha256?, path}."""
    p = ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    last = _last_line(p)
    if dedup_key and last and last.get("dedup_key") == dedup_key:
        return {"ok": True, "skipped": "dedup", "path": str(p)}
    body = dict(record)
    body["prev_sha256"] = (last or {}).get("sha256", "")
    body["dedup_key"] = dedup_key
    body["sha256"] = sha256_of({k: v for k, v in body.items() if k != "sha256"})
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(body, ensure_ascii=False, sort_keys=True) + "\n")
    return {"ok": True, "sha256": body["sha256"], "path": str(p)}


def verify_chain(limit: int = 200) -> dict:
    """راستی‌آزماییِ زنجیره روی nتای آخر — برای /health و تست."""
    p = ledger_path()
    if not p.exists():
        return {"ok": True, "checked": 0, "note": "empty"}
    bad = 0
    prev = None
    lines = [ln for ln in p.read_text("utf-8").splitlines() if ln.strip()][-limit:]
    for ln in lines:
        try:
            rec = json.loads(ln)
            expect = sha256_of({k: v for k, v in rec.items() if k != "sha256"})
            if rec.get("sha256") != expect:
                bad += 1
            elif prev is not None and rec.get("prev_sha256") != prev:
                bad += 1
            prev = rec.get("sha256")
        except Exception:  # noqa: BLE001
            bad += 1
    return {"ok": bad == 0, "checked": len(lines), "bad": bad}
