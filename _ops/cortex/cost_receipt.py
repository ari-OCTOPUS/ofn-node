#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cost_receipt.py — آداپتور رسیدِ هزینهٔ provider (CL01 / COST-OBS-1، حکم مالک 2026-08-19).

قرارداد ۱۲فیلدی مالک را می‌سازد؛ فقط از شواهد واقعی:
  REPORTED               وقتی provider خودش usage/cost می‌دهد.
  DETERMINISTIC_ESTIMATE فقط با جدولِ قیمتِ pinned+hash و شمار توکن و نرخِ تبدیلِ pinned.
  UNOBSERVABLE           هر کمبود ⇒ همان توقفِ سابق.
  FREE_OR_UNBILLED       برای fugu/free — هرگز «0 AUD» بی‌شاهد.
هیچ توکن/قیمت/هویتی ساخته نمی‌شود؛ راز هرگز وارد رسید نمی‌شود."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA = "cost-receipt/1"
_HERE = Path(__file__).resolve().parent


def _sha(b) -> str:
    return hashlib.sha256(b if isinstance(b, bytes) else str(b).encode("utf-8", "replace")).hexdigest()


class PricingTable:
    """جدول قیمتِ محلیِ نسخه‌دار. مقادیرِ production فقط با دست مالک پر می‌شود —
    مقادیر تست باید کلید TEST_ONLY داشته باشند و هرگز در production استفاده نشوند."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.sha256 = _sha(self.path.read_bytes()) if self.path.exists() else ""
        self.entries: dict = {}
        self.fx_usd_to_aud: float | None = None
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = data.get("models", {})
            fx = data.get("fx_usd_to_aud")
            self.fx_usd_to_aud = float(fx) if fx else None
        self.source_id = str(self.path)

    def price_for(self, model: str):
        e = self.entries.get(str(model or ""))
        if not e or e.get("TEST_ONLY"):
            return None
        return e

    def test_price_for(self, model: str):
        """فقط برای تست‌ها — ورودی TEST_ONLY مجاز است."""
        return self.entries.get(str(model or ""))


DEFAULT_PRICING = PricingTable(_HERE / "pricing_pinned.json")


class CostReceiptAdapter:
    def __init__(self, pricing: PricingTable | None = None, *,
                 per_call_cap_aud: float = 0.50, hard_stop_aud: float = 12.0):
        self.pricing = pricing or DEFAULT_PRICING
        self.per_call_cap_aud = per_call_cap_aud
        self.hard_stop_aud = hard_stop_aud
        self._seen: dict[str, dict] = {}          # trace_id+input_sha → رسید (idempotency)
        self.paid_blocked: bool = False           # COST_UNOBSERVABLE ⇒ true

    # ── helpers ────────────────────────────────────────────────────────────
    def _base(self, trace_id, provider, model, ts_req, ts_resp, budget_before,
              task_id=None, run_id=None):
        # T50 (OWNER-DIRECTIVE-08 §۵): تفکیک انتساب — افزودنی؛ رسید بدون
        # task_id صریحاً UNATTRIBUTED برچسب می‌خورد تا حسابرسی‌ها بدون
        # بدترین‌حالت‌سازی باشند.
        import os as _os
        import time as _t
        rid = str(trace_id or "")
        rec = {"schema": SCHEMA, "trace_id": trace_id, "provider": provider,
                "exact_model": model, "request_timestamp": ts_req,
                "response_timestamp": ts_resp, "budget_before_aud": round(float(budget_before), 6),
                "task_id": str(task_id or ""),
                "run_id": str(run_id or ""),
                "attribution": "TASK" if task_id else "UNATTRIBUTED",
                # A3 additive fields (old rows on disk are not rewritten)
                "receipt_id": "rcp-" + rid[:16],
                "turn_id": str(task_id or ""),
                "request_id": rid,
                "model": model,
                "status": "PENDING",
                "process_id": _os.getpid(),
                "code_version": str(_os.environ.get("OCTOPUS_CODE_VERSION") or "cost-receipt/1"),
                "created_at": ts_resp or _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
                "cognitive_quota_eligible": bool(task_id) and bool(run_id)}
        return rec

    def _finish(self, rec, *, tokens_in, tokens_out, usage_hash, pricing_src, pricing_ver,
                cost, method, status, budget_after, extra=None):
        rec.update({"prompt_tokens": tokens_in if tokens_in is not None else "TOKEN_COUNT_UNKNOWN",
                    "completion_tokens": tokens_out if tokens_out is not None else "TOKEN_COUNT_UNKNOWN",
                    "provider_usage_payload_hash": usage_hash,
                    "pricing_source_id": pricing_src, "pricing_version": pricing_ver,
                    "estimated_or_reported_cost_aud": cost, "cost_method": method,
                    "receipt_status": status, "budget_after_aud": round(float(budget_after), 6),
                    "status": status,
                    "tokens": (
                        (tokens_in if isinstance(tokens_in, int) else 0)
                        + (tokens_out if isinstance(tokens_out, int) else 0)
                    ) if isinstance(tokens_in, int) or isinstance(tokens_out, int) else rec.get("tokens"),
                    "cost_aud": cost if cost is not None else rec.get("cost_aud")})
        if extra:
            rec.update(extra)
        if status == "COST_UNOBSERVABLE":
            self.paid_blocked = True
        return rec

    # ── سازندهٔ اصلی ────────────────────────────────────────────────────────
    def build(self, *, trace_id: str, provider: str, model: str, ts_req: str, ts_resp: str,
              budget_before_aud: float, usage_payload: dict | None = None,
              tokens_in: int | None = None, tokens_out: int | None = None,
              input_sha256: str = "", free_tier: bool = False,
              fallback_of: dict | None = None, test_mode: bool = False,
              task_id: str | None = None, run_id: str | None = None) -> dict:
        key = f"{trace_id}:{input_sha256}"
        if key in self._seen:                      # idempotency — بدون شارژ دوباره
            return dict(self._seen[key])
        rec = self._base(trace_id, provider, model, ts_req, ts_resp, budget_before_aud,
                         task_id=task_id, run_id=run_id)
        if fallback_of:
            rec["fallback"] = {"primary_status": fallback_of.get("receipt_status"),
                               "primary_provider": fallback_of.get("provider"),
                               "primary_trace": fallback_of.get("trace_id")}
        usage_hash = _sha(json.dumps(usage_payload, sort_keys=True)) if usage_payload else ""

        if free_tier:
            out = self._finish(rec, tokens_in=tokens_in, tokens_out=tokens_out, usage_hash=usage_hash,
                               pricing_src="provider-contract", pricing_ver="free-tier",
                               cost=None, method="FREE_OR_UNBILLED", status="COMPLETE",
                               budget_after=budget_before_aud,
                               extra={"note": "free/quota tier — no billable evidence, not claimed as 0 AUD cost"})
            self._seen[key] = out
            return out

        # ۱) REPORTED — خود provider هزینه گزارش کرده باشد
        if usage_payload:
            cost_usd = usage_payload.get("cost_usd")
            if cost_usd is None and usage_payload.get("total_cost"):
                cost_usd = usage_payload.get("total_cost")
            if cost_usd is not None:
                fx = self.pricing.fx_usd_to_aud
                if fx is None:
                    out = self._finish(rec, tokens_in=tokens_in, tokens_out=tokens_out,
                                       usage_hash=usage_hash, pricing_src="provider-usage",
                                       pricing_ver="reported", cost=None, method="UNOBSERVABLE",
                                       status="COST_UNOBSERVABLE", budget_after=budget_before_aud,
                                       extra={"note": "reported cost_usd present but fx_usd_to_aud unpinned"})
                else:
                    cost_aud = float(cost_usd) * fx
                    out = self._finish(rec, tokens_in=tokens_in, tokens_out=tokens_out,
                                       usage_hash=usage_hash, pricing_src="provider-usage",
                                       pricing_ver="reported", cost=round(cost_aud, 6),
                                       method="REPORTED", status="COMPLETE",
                                       budget_after=budget_before_aud - cost_aud)
                    if cost_aud > self.per_call_cap_aud:
                        out["cap_violation"] = "PER_CALL_CAP_EXCEEDED"
                        self.paid_blocked = True
                self._seen[key] = out
                return out

        # ۲) DETERMINISTIC_ESTIMATE — توکن + قیمتِ pinned + fxِ pinned
        if tokens_in is not None and tokens_out is not None:
            entry = (self.pricing.test_price_for(model) if test_mode else self.pricing.price_for(model))
            fx = self.pricing.fx_usd_to_aud
            if entry and fx:
                cost_usd = (tokens_in * float(entry["in_per_1m"]) +
                            tokens_out * float(entry["out_per_1m"])) / 1_000_000
                cost_aud = cost_usd * fx
                out = self._finish(rec, tokens_in=tokens_in, tokens_out=tokens_out,
                                   usage_hash=usage_hash, pricing_src=self.pricing.source_id,
                                   pricing_ver=self.pricing.sha256[:12],
                                   cost=round(cost_aud, 6), method="DETERMINISTIC_ESTIMATE",
                                   status="COMPLETE", budget_after=budget_before_aud - cost_aud,
                                   extra={"fx_usd_to_aud": fx})
                if cost_aud > self.per_call_cap_aud:
                    out["cap_violation"] = "PER_CALL_CAP_EXCEEDED"
                    self.paid_blocked = True
                self._seen[key] = out
                return out

        # ۳) هیچ‌چیز کافی نیست
        out = self._finish(rec, tokens_in=tokens_in, tokens_out=tokens_out, usage_hash=usage_hash,
                           pricing_src="", pricing_ver="", cost=None, method="UNOBSERVABLE",
                           status="COST_UNOBSERVABLE", budget_after=budget_before_aud)
        self._seen[key] = out
        return out

    # ── گارد بودجه ────────────────────────────────────────────────────────
    def budget_ok(self, spent_aud: float, next_cost_aud: float) -> bool:
        return (spent_aud + next_cost_aud) <= self.hard_stop_aud and next_cost_aud <= self.per_call_cap_aud


# ── RCPT-1/RCPT-2 (2026-08-19, CORE-AUTO-DEBUG per audit AUDIT-191 §F) ──────────
# RCPT-1: مبنای budget_before = بودجهٔ باقی‌ماندهٔ روز (نه هزینهٔ خودِ فراخوانی —
#         باگِ قبلی همهٔ رسیدها را budget_afterِ منفی می‌کرد).
# RCPT-2: COST_UNOBSERVABLE روز → مسیرِ پولیِ عمومی بسته می‌ماند (fail-closedِ
#         وعده‌داده‌شده در کامنتِ COST-OBS-1 که تا امروز خوانده نمی‌شد).
from datetime import datetime as _dtm, timezone as _tzm

RECEIPTS_PATH = _HERE.parent / "state" / "cortex" / "cost-receipts.jsonl"
DAILY_CAP_AUD = 30.0  # LEARNING-FIRST-BUDGET-EXPANSION-01


def _today_receipts(path=None) -> list:
    p = Path(path or RECEIPTS_PATH)
    if not p.exists():
        return []
    today = _dtm.now(_tzm.utc).date().isoformat()
    out = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if str(r.get("request_timestamp", "")).startswith(today):
            out.append(r)
    return out


def remaining_budget_aud(path=None, *, daily_cap_aud: float = DAILY_CAP_AUD) -> float:
    """بودجهٔ باقی‌ماندهٔ روز از خودِ جریانِ رسیدها — self-contained و قابل‌تست."""
    spent = sum(float(r.get("estimated_or_reported_cost_aud") or 0.0)
                for r in _today_receipts(path)
                if r.get("receipt_status") == "COMPLETE"
                and r.get("cost_method") in ("REPORTED", "DETERMINISTIC_ESTIMATE"))
    return round(float(daily_cap_aud) - spent, 6)


def fx_pinned_fresh(*, max_age_h: float = 24.0, path=None):
    """F18: مسیرِ پرداختیِ عمومی هم مثل Live-4 به FXِ تازه نیاز دارد.
    (ok, reason) — stale/missing ⇒ بسته (fail-closed). منبع: pricing_pinned.json::fx_record."""
    pp = Path(path or (_HERE / "pricing_pinned.json"))
    try:
        rec = json.loads(pp.read_text(encoding="utf-8")).get("fx_record") or {}
        ts = _dtm.fromisoformat(str(rec.get("fx_timestamp_utc", "")).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return False, "missing-or-malformed"
    if (_dtm.now(_tzm.utc) - ts).total_seconds() > max_age_h * 3600:
        return False, "expired(>24h)"
    return True, "ok"


def paid_blocked_today(path=None) -> bool:
    """RCPT-2: اگر امروز رسیدِ COST_UNOBSERVABLE یا نقضِ سقفِ فراخوانی هست، بسته."""
    return any(r.get("receipt_status") == "COST_UNOBSERVABLE" or r.get("cap_violation")
               for r in _today_receipts(path))
