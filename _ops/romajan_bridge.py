#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""romajan_bridge.py — پلِ آزمایشگاهِ romajan ←→ C6 hypothesis pipeline.

فقط‌خواندنی نسبت به F:\romajan. صفر اجرای موتور (engine_a/SINDy هرگز از اینجا
اجرا نمی‌شود — فقط مالک در آزمایشگاه خودش). صفر شبکه. صفر پول.

وظیفه:
  1) خواندن claims_ledger.json(های) romajan
  2) فیلتر: status ∈ {verified, executed, fact} AND claim_id ∉ seen-set
  3) برای هر ادعای جدید → ردیف mechanism_count/romajan_claim در hypothesis-queue.jsonl
  4) نوشتن claim_id در state/c6/romajan-seen.json (append-only، هرگز remove)
  5) در thesis_queue هم register شود (EXPERIMENT_REGISTRY enrichment)

گیت:
  - OCTOPUS_WIRE_ROMAJAN_PROBES (env flag)
  - ACTIVATION-C6-RESEARCH.flag (مالک)
  - go.romajan_root = env ROMAJAN_LAB_PATH یا F:\romajan
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_ROMAJAN_PROBES"
QUEUE = opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl"
SEEN = opslib.STATE_DIR / "c6" / "romajan-seen.json"


def enabled() -> bool:
    if str(os.environ.get(FLAG, "")).strip().lower() not in ("1", "true", "yes", "on"):
        return False
    if not (opslib.OPS / "ACTIVATION-C6-RESEARCH.flag").exists():
        return False
    return True


def romajan_root() -> Path:
    return Path(os.environ.get("ROMAJAN_LAB_PATH", r"F:\romajan"))


def _read_ledgers(root: Path) -> list[dict]:
    """همهٔ claims_ledger*.json را می‌خواند. fail-soft: نبود = خالی."""
    candidates = [
        root / "propagation" / "claims_ledger.json",
        root / "propagation-lab" / "data" / "claims_ledger.json",
        root / "evaluation-lab" / "results" / "claims_ledger.json",
    ]
    claims: list[dict] = []
    for lp in candidates:
        if not lp.exists():
            continue
        try:
            data = json.loads(lp.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        items = data if isinstance(data, list) else (
            data.get("claims", data.get("results", [])) if isinstance(data, dict) else [])
        if not isinstance(items, list):
            continue
        for c in items:
            if isinstance(c, dict):
                c["_source_file"] = str(lp)
                claims.append(c)
    return claims


def _load_seen() -> set:
    if not SEEN.exists():
        return set()
    try:
        data = json.loads(SEEN.read_text("utf-8"))
        if isinstance(data, list):
            return {str(x) for x in data}
        if isinstance(data, dict):
            return {str(x) for x in (data.get("ids") or [])}
    except (OSError, ValueError):
        pass
    return set()


def _append_seen(ids: list[str]) -> None:
    existing = _load_seen()
    existing.update(str(i) for i in ids)
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    tmp = SEEN.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps({"ids": sorted(existing), "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                   ensure_ascii=False, indent=2),
        "utf-8",
    )
    tmp.replace(SEEN)


def _queue_append(row: dict) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _already_in_queue(cid: str) -> bool:
    if not QUEUE.exists():
        return False
    try:
        for ln in QUEUE.read_text("utf-8").splitlines():
            if cid in ln:
                return True
    except OSError:
        pass
    return False


def _mk_row(claim: dict) -> dict:
    cid = str(claim.get("id") or claim.get("claim_id") or "")
    return {
        "id": f"rc-{cid[:40]}",
        "kind": "romajan_claim",
        "probe": "romajan_new_claims",
        "subject": f"romajan:{cid[:80]}",
        "question": str(claim.get("claim") or claim.get("question") or "")[:500],
        "hypothesis": f"romajan verified claim: {str(claim.get('claim') or '')[:300]}",
        "stop_condition": "one offline re-verification on the same evidence",
        "verifier": "compare_frozen_baselines",
        "expected_artifact": f"romajan claim {cid[:60]} with status={claim.get('status')}",
        "falsification_criteria": [
            "claim status changes from verified/executed/fact in source ledger",
            "re-measurement produces conflicting result",
        ],
        "tools": ["test_in_sandbox"],
        "unit": "claim",
        "floor": 0,
        "baseline_count": 1,
        "baseline_detail": str(claim.get("evidence") or claim.get("status") or "")[:300],
        "measured": {
            "count": 1,
            "detail": f"romajan:{cid[:80]} status={claim.get('status')}",
            "source": claim.get("_source_file", "romajan"),
        },
        "fix_hint": "verify romajan claim; if still valid, admit to memory",
        "source": "romajan_bridge",
        "producer_version": "romajan-bridge.v1",
        "honesty": "claim from external lab; C6 only verifies, never re-executes engine",
        "status": "PENDING",
        "romajan_claim_id": cid,
        "romajan_status": claim.get("status"),
        "romajan_file": claim.get("_source_file"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def sync() -> dict:
    """یک راند: ادعاهای جدید romajan → صف C6. fail-soft."""
    if not enabled():
        return {"ok": False, "reason": "flag-off-or-activation-missing"}
    try:
        root = romajan_root()
        claims = _read_ledgers(root)
        if not claims:
            return {"ok": False, "reason": f"no-claims-under:{root}"}
        seen = _load_seen()
        new_ids = []
        added = 0
        for c in claims:
            cid = str(c.get("id") or c.get("claim_id") or "").strip()
            if not cid:
                continue
            status = str(c.get("status") or "").strip().lower()
            if status not in ("verified", "executed", "fact"):
                continue
            if cid in seen:
                continue
            if _already_in_queue(cid):
                new_ids.append(cid)
                continue
            row = _mk_row(c)
            _queue_append(row)
            new_ids.append(cid)
            added += 1
        if new_ids:
            _append_seen(new_ids)
        return {
            "ok": True,
            "added": added,
            "already_known": len(new_ids) - added,
            "new_ids": new_ids[:20],
            "total_scanned": len(claims),
            "seen_before": len(seen),
            "root": str(root),
        }
    except Exception as e:  # noqa: BLE001
        try:
            opslib.alert([f"romajan_bridge.sync failed: {type(e).__name__}: {e}"])
        except Exception:
            pass
        return {"ok": False, "reason": f"fail:{type(e).__name__}"}


# ─── C6 _derive_fns integration ─────────────────────────────────────────────────
# c6_trigger._derive_fns: kind → (derive_fn, accept_fn). این ماژول فقط derive
# می‌کند؛ accept از مسیر research_loop می‌گذرد.

_KNOWN_KIND = "romajan_claim"


def derive_fn(row: dict, result: dict) -> dict:
    """derive fn برای romajan_claim — فقط شاهدِ باز، هیچ auto-accept."""
    verdict = str((result or {}).get("verdict") or "")
    return {
        "row_id": row.get("id"),
        "kind": _KNOWN_KIND,
        "romajan_claim_id": row.get("romajan_claim_id"),
        "verdict": verdict,
        "measured": result.get("measured"),
        "note": "romajan claim verification — C6 does NOT re-execute engine_a/SINDy",
    }


def register_derive_fns() -> None:
    """c6_trigger._derive_fns enrichment با fail-soft. از c6_trigger صدا زده شود."""
    try:
        import c6_trigger as _ct  # noqa: WPS433
        existing = getattr(_ct, "_derive_fns", {}) or {}
        existing[_KNOWN_KIND] = (derive_fn, None)  # None = accept از مسیر اصلی
        setattr(_ct, "_derive_fns", existing) if hasattr(_ct, "_derive_fns") else None
    except Exception:
        pass


if __name__ == "__main__":
    print(json.dumps(sync(), ensure_ascii=False, indent=2))
