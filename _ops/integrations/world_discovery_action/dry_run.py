#!/usr/bin/env python3
"""dry_run — زنجیرهٔ کامل روی artifact، بدونِ هیچ اثری.

    artifact → اعتبار → ترجمه → (اگر عملی بود) طبقه‌بندی و نقشهٔ پل → draft
             → رسیدِ ترجمه روی دیسکِ namespace خودمان

سه ناوردی که در **هر** مسیر برقرارند و تست می‌شوند:
    external_effects == []      · spend == 0      · runtime_state_writes == 0

این ماژول تنها جایی است که `action_bridge` را import می‌کند — و فقط سطحِ
عمومی‌اش (`planner`, `classifier`). هرگز `executor` را صدا نمی‌زند: اجرای
واقعی، حتی sandbox، کارِ این دور نیست.

$0 · stdlib · صفر ارسال · صفر خرج.
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import contracts
from . import integration_receipt
from . import policy
from . import telegram_draft
from . import translator
from . import validator

# سطحِ عمومیِ پلِ اقدام — مسیرش را صداکننده ست می‌کند تا وابستگی سخت نشود.
_BRIDGE = Path(__file__).resolve().parents[2] / "action_bridge"


def _load_bridge():
    if str(_BRIDGE) not in sys.path:
        sys.path.insert(0, str(_BRIDGE))
    import classifier as bridge_classifier
    import planner as bridge_planner
    return bridge_classifier, bridge_planner


def run(artifact: dict, *, sandbox_dir, now=None, prereg_lookup=None) -> dict:
    """bundle ِ کاملِ dry-run. همیشه dict برمی‌گرداند — هرگز استثنا."""
    out = {
        "schema": "world-discovery-action.dry-run.v1",
        "created_at": str(now or ""),
        "external_effects": [], "spend": 0, "runtime_state_writes": 0,
        "telegram_send_attempted": False,
    }
    v = validator.validate_artifact(artifact)
    result = v.get("result") or {}
    out["artifact_valid"] = v["ok"]
    out["source_status"] = v.get("status")
    out["discovery_count"] = 1 if isinstance(result.get("discovery"), dict) and result.get("discovery") else 0
    cands = result.get("candidates")
    out["candidate_count"] = len(cands) if isinstance(cands, list) else 0

    rec = translator.translate_discovery_artifact(artifact, now=now)
    out["translation"] = rec
    out["decision"] = rec["decision"]
    out["action_class"] = rec["action_class"]

    # نقشهٔ پل فقط وقتی ساخته می‌شود که ترجمه عملی تولید کرده باشد.
    out["bridge_plan"] = None
    if rec["decision"] in ("DRY_RUN", "OWNER_GATE") and rec.get("action_id"):
        try:
            _, bridge_planner = _load_bridge()
            exp = validator.experiment_of(result) or {}
            req = translator.build_action_request(
                result.get("discovery") or {}, exp, now=now,
                prereg_id=str(rec.get("source_artifact", {}).get("content_hash") or ""))
            pl = bridge_planner.plan(req, sandbox_root=sandbox_dir,
                                     prereg_lookup=prereg_lookup, ledger={},
                                     now=float(now or 0))
            out["bridge_plan"] = {k: pl.get(k) for k in
                                  ("classification", "decision", "reason",
                                   "idempotency_key")}
        except Exception as e:  # noqa: BLE001 — نقشه هرگز dry-run را نمی‌کشد
            out["bridge_plan"] = {"error": f"{type(e).__name__}: {e}"[:200]}

    out["draft"] = telegram_draft.from_translation(rec, result, now=now)
    out["telegram_send_attempted"] = bool(out["draft"].get("send_attempted"))

    w = integration_receipt.write(rec, out_dir=Path(sandbox_dir) / "receipts")
    out["receipt_written"] = w["ok"]
    out["receipt_path"] = w.get("path")
    if not w["ok"]:
        # همان قاعدهٔ پل: رسیدِ ننشسته ⇒ ادعای موفقیت نه
        out["errors"] = [f"receipt-write-failed:{w.get('error')}"]
        out["ok"] = False
    else:
        out["ok"] = True

    rv = contracts.validate_translation_receipt(rec)
    out["receipt_valid"] = rv["ok"]
    if not rv["ok"]:
        out["ok"] = False
        out.setdefault("errors", []).extend(rv["errors"])
    return out
