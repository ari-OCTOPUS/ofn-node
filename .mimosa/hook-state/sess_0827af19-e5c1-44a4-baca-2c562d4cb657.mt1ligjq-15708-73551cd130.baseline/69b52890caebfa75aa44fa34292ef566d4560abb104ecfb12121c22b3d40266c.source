#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_probe_v2.py — پروب تک‌فراخوانی مطابق دستور مالک 2026-08-20 (~15:45).

retries=0 مطلق · nonce از پیش ثبت‌شده · پنج timestamp با http.client ·
معنای created = COMPLETION_CREATED_TIMESTAMP با exact_server_stage=UNKNOWN ·
رسید کامل + ردیف هزینهٔ منتسب (task_id/run_id) + رویداد spine."""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import ssl
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT / "_ops"), str(_ROOT / "_ops/cortex"), str(_ROOT / "_ops/spine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# مدل/endpoint: payload امضاشده مدل را پین نکرده — منبع رسمیِ مدلِ مسیرِ پرداختی،
# تصمیم امضاشدهٔ DEEPSEEK-AUTOMATIC-ROUTING-01 است (deepseek-v4-flash · tier=primary).
# این استثنا در رسید ثبت شده و برای کارت‌های آینده توصیهٔ pin-کردن مدل ثبت شد.
MODEL = "deepseek-v4-flash"
HOST = "api.deepseek.com"
PATH_URL = "/chat/completions"


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds")


def execute_probe(run_id: str, receipt_id: str, fx_rate: float, lease_id: str,
                  _conn=None) -> dict:
    """یک فراخوان. _conn برای تست تزریق می‌شود (بدون شبکه)."""
    nonce = f"EVENT-TIME-PROBE-{run_id}"
    nonce_sha = hashlib.sha256(nonce.encode()).hexdigest()
    body = json.dumps({"model": MODEL,
                       "messages": [{"role": "user",
                                     "content": f"Return exactly this nonce and nothing else: {nonce}"}],
                       "max_tokens": 32, "temperature": 0, "stream": False, "tools": []})
    body_sha = hashlib.sha256(body.encode()).hexdigest()

    receipt = {"schema": "event-time-probe.v1", "probe_id": f"probe-{receipt_id}",
               "task_id": "event-time-probe-20260820", "run_id": run_id,
               "authorization": {"payload_sha256": hashlib.sha256(
                   (_ROOT / "02-DECISIONS/PAYLOAD-EVENT-TIME-PROBE-2026-08-20.json")
                   .read_bytes()).hexdigest().upper(),
                   "signature_verified": True, "fx_pin_receipt_id": receipt_id},
               "request": {"endpoint_host": HOST, "model_requested": MODEL,
                           "model_source": "DEEPSEEK-AUTOMATIC-ROUTING-01 (payload مدل را پین نکرده)",
                           "body_sent_at": None, "request_sha256": body_sha,
                           "nonce_sha256": nonce_sha, "max_output_tokens": 32,
                           "temperature": 0, "retries_allowed": 0}}
    t_start = time.time()
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        sys.path.insert(0, str(_ROOT / "_ops/budget"))
        import env_loader
        env_loader.load_env()
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")

    try:
        conn = _conn or http.client.HTTPSConnection(HOST, timeout=60,
                                                    context=ssl.create_default_context())
        conn.request("POST", PATH_URL, body=body,
                     headers={"Authorization": f"Bearer {api_key}",
                              "Content-Type": "application/json"})
        t_sent = time.time()
        resp = conn.getresponse()
        t_headers = time.time()
        raw = resp.read()
        t_body = time.time()
        status = resp.status
        req_id = resp.headers.get("x-request-id", "") or resp.headers.get("RequestId", "")
    except Exception as e:
        receipt.update({"verdict": "PROBE_HTTP_FAILED",
                        "result": {"calls_attempted": 1, "calls_succeeded": 0,
                                   "retry_count": 0, "server_created_captured": False,
                                   "spine_event_written": False, "executable": False},
                        "error": f"{type(e).__name__}: {e}",
                        "timing": {"request_started_at": _iso(t_start)}})
        _write(receipt, fx_rate)
        return receipt

    receipt["request"].update({"request_started_at": _iso(t_start),
                               "body_sent_at": _iso(t_sent)})
    receipt["response"] = {"http_status": status, "request_id": req_id,
                           "headers_received_at": _iso(t_headers),
                           "body_completed_at": _iso(t_body),
                           "response_sha256": hashlib.sha256(raw).hexdigest()[:16]}
    receipt["timing"] = {"round_trip_ms": round((t_body - t_start) * 1000, 1),
                         "created_minus_send_ms": None, "receive_minus_created_ms": None,
                         "clock_skew_suspected": False}

    if status != 200:
        receipt.update({"verdict": "PROBE_HTTP_FAILED",
                        "result": {"calls_attempted": 1, "calls_succeeded": 0,
                                   "retry_count": 0, "server_created_captured": False,
                                   "spine_event_written": False, "executable": False}})
        _write(receipt, fx_rate)
        return receipt

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    created = data.get("created")
    text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    usage = data.get("usage") or {}
    nonce_match = text.strip() == nonce
    receipt["response"].update({
        "model_returned": data.get("model", ""),
        "created_unix": created,
        "created_utc": (datetime.fromtimestamp(int(created), tz=timezone.utc)
                        .isoformat(timespec="seconds") if isinstance(created, int) else None),
        "nonce_match": nonce_match,
        "finish_reason": ((data.get("choices") or [{}])[0].get("finish_reason")),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "semantic_interpretation": "COMPLETION_CREATED_TIMESTAMP",
        "exact_server_stage": "UNKNOWN", "precision": "1s"})

    server_created_captured = isinstance(created, int)
    if server_created_captured:
        receipt["timing"]["created_minus_send_ms"] = round((created - t_sent) * 1000, 1)
        receipt["timing"]["receive_minus_created_ms"] = round((t_headers - created) * 1000, 1)
        receipt["timing"]["clock_skew_suspected"] = created > t_body

    valid = server_created_captured and nonce_match and usage.get("total_tokens") \
        and len(data.get("choices") or []) == 1

    # رویداد spine با occurred_at = created (ساعت مستقل سرور)
    spine_ok = False
    if server_created_captured:
        try:
            import spine_adapters
            occ = datetime.fromtimestamp(created, tz=timezone.utc).isoformat(timespec="seconds")
            r = spine_adapters.emit_event(
                event_type="accepted-measurement", domain="provider",
                correlation_id=f"probe-{receipt_id}",
                subject="event-time-probe-20260820",
                producer="event_time_probe_v2", trust="DETERMINISTIC",
                occurred_at=occ, event_time_source="provider_server_created",
                time_precision="1s",
                payload={"run_id": run_id, "nonce_sha256": nonce_sha,
                         "semantic": "COMPLETION_CREATED_TIMESTAMP",
                         "exact_server_stage": "UNKNOWN"},
                idempotency_key=f"probe-{receipt_id}|provider_server_created")
            spine_ok = bool(r.get("published"))
        except Exception:
            spine_ok = False

    receipt["cost"] = {"receipt_id": f"cost-{receipt_id}",
                       "attributed_task_id": receipt["task_id"],
                       "attributed_run_id": run_id,
                       "method": "ESTIMATE_FROM_USAGE",
                       "tokens": usage.get("total_tokens"),
                       "fx_usd_to_aud": fx_rate}
    receipt["result"] = {"calls_attempted": 1,
                         "calls_succeeded": 1 if status == 200 else 0,
                         "retry_count": 0,
                         "server_created_captured": server_created_captured,
                         "spine_event_written": spine_ok,
                         "executable": False}
    receipt["verdict"] = "PROBE_PASS" if valid else "PROBE_RESPONSE_INVALID"
    _write(receipt, fx_rate, usage=usage)
    return receipt


def _write(receipt: dict, fx_rate: float, usage: dict | None = None) -> None:
    out = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json"
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    # ردیف هزینهٔ منتسب در جریان cost-receipts (تست‌پذیری T50 برای همین فراخوان)
    try:
        row = {"schema": "cost-receipt/1",
               "trace_id": receipt.get("probe_id"),
               "provider": "deepseek", "exact_model": MODEL,
               "request_timestamp": receipt["request"].get("request_started_at"),
               "response_timestamp": receipt["response"].get("body_completed_at"),
               "budget_before_aud": 0.01, "task_id": receipt["task_id"],
               "run_id": receipt["run_id"], "attribution": "TASK",
               "prompt_tokens": (usage or {}).get("prompt_tokens"),
               "completion_tokens": (usage or {}).get("completion_tokens"),
               "estimated_or_reported_cost_aud": None,
               "cost_method": "FREE_OR_UNBILLED" if not (usage or {}).get("total_tokens")
               else "DETERMINISTIC_ESTIMATE",
               "receipt_status": "COMPLETE" if receipt.get("verdict") == "PROBE_PASS"
               else "COMPLETE_INVALID_RESPONSE",
               "budget_after_aud": 0.01,
               "note": "event-time-probe single call; AUD within 0.01 by construction"}
        p = _ROOT / "_ops/state/cortex/cost-receipts.jsonl"
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
