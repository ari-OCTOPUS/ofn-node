"""Gateway facade: flash budget → circuit snapshot → DeepSeekClient → lab receipt.

Does NOT call cortex.model_router.ask (that appends _ops/state/paid-calls.jsonl).
Does NOT call circuit_breaker.check/record (those persist circuit-state.json).
Reuses debate.client.DeepSeekClient as the existing spender.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import budget as flash_budget

_OPS = Path(__file__).resolve().parents[2]
_SECRET_RE = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9_\-\.]+|api[_-]?key\s*[:=]\s*\S+|sk-[A-Za-z0-9]+)"
)
ENDPOINT = "https://api.deepseek.com/chat/completions"
FLASH_TARGET = "deepseek"
_LAST_HTTP: dict[str, Any] = {}


def redact(text: str) -> str:
    return _SECRET_RE.sub("<REDACTED>", text or "")


def key_status() -> dict[str, Any]:
    present = bool((os.environ.get("DEEPSEEK_API_KEY") or "").strip())
    return {
        "env_var": "DEEPSEEK_API_KEY",
        "present": present,
        "status": "PRESENT" if present else "UNLOCATED",
        "value_logged": False,
    }


def circuit_snapshot(ops: Path | None = None) -> dict[str, Any]:
    """Read-only JSON snapshot. Does not call circuit_breaker.check (would persist)."""
    path = (ops or _OPS) / "state" / "circuit-state.json"
    if not path.exists():
        return {"status": "UNLOCATED", "allow_assumed": True, "reason": "circuit-state.json missing", "wrote": False}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        targets = raw.get("targets") or {}
        ds = targets.get(FLASH_TARGET) or targets.get("reason") or {}
        st = str(ds.get("state") or "closed")
        allow = st != "open"
        return {
            "status": "OK",
            "allow": allow,
            "state": st,
            "target_keys": sorted(targets.keys())[:12],
            "wrote": False,
            "path": str(path).replace("\\", "/"),
            "source_hash": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    except (OSError, json.JSONDecodeError) as e:
        return {"status": "UNLOCATED", "allow_assumed": False, "reason": type(e).__name__, "wrote": False}


def render_chat_completions(
    *,
    task: dict[str, Any],
    pipeline: dict[str, Any],
    memory: dict[str, Any],
    reservation: dict[str, Any],
    handshake: bool = False,
) -> dict[str, Any]:
    ha = pipeline.get("homeostatic_assessment") or {}
    gates = pipeline.get("gate_decisions") or []
    skills = {
        g.get("domain"): {
            "score": ((g.get("skill_score") or {}).get("final_score")),
            "mode": g.get("mode"),
        }
        for g in gates
    }
    evidence_ids = list(memory.get("evidence_ids") or [])
    evidence_ids += [o.get("observation_id") for o in (pipeline.get("observations") or []) if o.get("observation_id")]
    status_line = (
        f"HC={ha.get('global_state')} beat={pipeline.get('observations', [{}])[0].get('beat') if pipeline.get('observations') else None} "
        f"D6=BETWEEN_RUN_VARIANCE GAP-001=OPEN executable=false"
    )
    if handshake:
        user = (
            f"وضعیت داده‌شده: {status_line}\n"
            "این request_id را برگردان و در یک جمله وضعیت داده‌شده را خلاصه کن."
        )
    else:
        user = (
            f"کار مالک: {task.get('summary')}\n"
            f"وضعیت: {status_line}\n"
            f"evidence_ids: {', '.join(str(x) for x in evidence_ids[:24])}\n"
            f"memory: {'; '.join(memory.get('snippets') or [])[:400]}\n"
            "فقط یک پیشنهاد متنی بده. executable=false. هیچ اقدام خارجی نکن."
        )
    system = (
        "You are an advisory sidecar for OCTOPUS. executable=false. "
        "external_action=false. Do not claim full-octopus. Judge is advisory (D6)."
    )
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 128,
        "temperature": 0,
    }
    return {
        "schema": "full-loop-rendered-request.v1",
        "network": False,
        "authorization_header": "ABSENT",
        "endpoint": ENDPOINT,
        "method": "POST",
        "body": body,
        "evidence_ids": evidence_ids,
        "skill_scores": skills,
        "homeostatic_state": ha.get("global_state"),
        "budget_reservation": {
            "est_aud": reservation.get("est_aud"),
            "remaining_aud": (reservation.get("budget") or {}).get("remaining_aud"),
            "remaining_calls": (reservation.get("budget") or {}).get("remaining_calls"),
            "k9_mixed": False,
        },
        "executable": False,
        "external_action": False,
        "prompt_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest(),
    }


def _http_transport(client: Any, timeout_s: int) -> Callable[[dict], dict]:
    """Official OpenAI-compatible POST using the existing client's key/url/model."""

    def send(body: dict) -> dict:
        payload = dict(body)
        payload["model"] = client.model or payload.get("model")
        _LAST_HTTP.clear()
        req = urllib.request.Request(
            client.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {client.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw_bytes = resp.read()
                status = int(getattr(resp, "status", 200) or 200)
                headers = {k.lower(): v for k, v in resp.headers.items()}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "replace")[:400]
            e.octopus_http_status = int(e.code or 0)
            e.octopus_err_body = redact(err_body)
            raise
        data = json.loads(raw_bytes.decode("utf-8"))
        rid = data.get("id") or headers.get("x-request-id") or headers.get("x-ds-request-id")
        data["octopus_http_status"] = status
        data["octopus_request_id"] = rid
        data["octopus_model"] = data.get("model") or client.model
        data["octopus_tier"] = "paid"
        data["octopus_response_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
        _LAST_HTTP.update({
            "http_status": status,
            "request_id": rid,
            "response_sha256": data["octopus_response_sha256"],
            "returned_model": data["octopus_model"],
        })
        return data

    return send


def call_deepseek_once(
    rendered: dict[str, Any],
    *,
    store: Path,
    timeout_s: int = flash_budget.TIMEOUT_SECONDS,
    max_retries: int = flash_budget.MAX_RETRIES,
) -> dict[str, Any]:
    """Stage B only. One tiny call. Never logs the key. Isolated flash budget."""
    ks = key_status()
    if not ks["present"]:
        return {
            "ok": False,
            "status": "UNLOCATED",
            "reason": "DEEPSEEK_API_KEY UNLOCATED",
            "http_status": None,
            "network": False,
            "key_logged": False,
        }
    try:
        flash_budget.reserve(store, est_aud=0.01, stage="B")
    except flash_budget.BudgetError as e:
        return {
            "ok": False,
            "status": "BLOCKED_BUDGET",
            "reason": str(e),
            "network": False,
            "key_logged": False,
        }
    circ = circuit_snapshot()
    if circ.get("allow") is False:
        return {
            "ok": False,
            "status": "BLOCKED_CIRCUIT_OPEN",
            "circuit": circ,
            "network": False,
            "key_logged": False,
        }
    debate_dir = str(_OPS / "debate")
    if debate_dir not in sys.path:
        sys.path.insert(0, debate_dir)
    import client as ds_client  # type: ignore  # existing spender

    retries = 0
    t0 = time.perf_counter()
    http_status = None
    last_err = None
    out = None
    cli = ds_client.DeepSeekClient(role="reason")
    cli.transport = _http_transport(cli, timeout_s)
    body = rendered["body"]
    while True:
        try:
            out = cli.complete(
                system=body["messages"][0]["content"],
                user=body["messages"][1]["content"],
                max_tokens=int(body.get("max_tokens") or 128),
                temperature=float(body.get("temperature") or 0),
            )
            http_status = 200
            last_err = None
            break
        except urllib.error.HTTPError as e:
            http_status = int(getattr(e, "octopus_http_status", None) or e.code or 0)
            last_err = {"type": "HTTPError", "http_status": http_status, "body": getattr(e, "octopus_err_body", "")}
            break
        except TimeoutError as e:
            last_err = {"type": "TimeoutError", "msg": type(e).__name__}
            if retries < max_retries:
                retries += 1
                continue
            break
        except Exception as e:  # noqa: BLE001
            name = type(e).__name__
            if "timeout" in name.lower() or "timed out" in str(e).lower():
                last_err = {"type": "timeout", "cls": name}
                if retries < max_retries:
                    retries += 1
                    continue
            last_err = {"type": name}
            break
    latency_ms = int((time.perf_counter() - t0) * 1000)
    if http_status in (401, 429) or (last_err and last_err.get("type") in ("timeout", "TimeoutError")):
        rec = {
            "ok": False,
            "status": "FAIL",
            "http_status": http_status,
            "error": last_err,
            "latency_ms": latency_ms,
            "retries": retries,
            "endpoint": ENDPOINT,
            "key_logged": False,
            "abort_main_loop": True,
        }
        _write_receipt(store, rec)
        return rec
    if out is None:
        rec = {
            "ok": False,
            "status": "FAIL",
            "http_status": http_status,
            "error": last_err,
            "latency_ms": latency_ms,
            "retries": retries,
            "endpoint": ENDPOINT,
            "key_logged": False,
            "abort_main_loop": True,
        }
        _write_receipt(store, rec)
        return rec

    usage = {"prompt_tokens": out.get("tokens_in"), "completion_tokens": out.get("tokens_out"), "cost_usd": out.get("cost_usd")}
    text = redact(str(out.get("text") or ""))
    rec = {
        "ok": True,
        "status": "PASS",
        "schema": "full-loop-gateway-receipt.v1",
        "endpoint": ENDPOINT,
        "returned_model": out.get("model"),
        "request_id": None,  # filled from transport extras if complete() kept them — see below
        "latency_ms": latency_ms,
        "token_usage": usage,
        "http_status": http_status,
        "timeout_retry_count": retries,
        "response_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text_redacted": text[:800],
        "cost_usd": out.get("cost_usd"),
        "cost_aud": None,
        "cost_method": "provider_tokens_x_budgets_yaml_usd",
        "key_logged": False,
        "wrote_paid_calls_jsonl": False,
        "k9_mixed": False,
        "executable": False,
        "external_action": False,
    "spend_path": "DeepSeekClient.complete via lab facade (not the cortex paid-calls writer)",
    }
    # DeepSeekClient.complete does not forward octopus_request_id; hash text is the receipt id stand-in
    rec["request_id"] = _LAST_HTTP.get("request_id") or rec["response_hash"][:24]
    rec["response_hash"] = _LAST_HTTP.get("response_sha256") or rec["response_hash"]
    if _LAST_HTTP.get("returned_model"):
        rec["returned_model"] = _LAST_HTTP["returned_model"]
    spent_usd = float(out.get("cost_usd") or 0.0)
    rec["cost_aud_note"] = "USD from locked budgets.yaml prices; FX pin not applied; life_credit conversion never called"
    rec["spent_usd"] = spent_usd
    flash_budget.settle(store, spent_aud=0.0, calls=1)  # USD tracked separately; AUD pin UNLOCATED
    rec["flash_budget"] = flash_budget.load(store).to_dict()
    _write_receipt(store, rec)
    return rec


def _write_receipt(store: Path, rec: dict[str, Any]) -> None:
    store = Path(store)
    store.mkdir(parents=True, exist_ok=True)
    p = store / "gateway-receipts.jsonl"
    safe = json.loads(redact(json.dumps(rec, default=str)))
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(safe, ensure_ascii=True) + "\n")
