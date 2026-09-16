#!/usr/bin/env python3
"""OCTOPUS paid-API budget broker — node 138 (API-BUDGET-ACTIVATION-20260913).

Versioned contract v1 (owner-authorized): W1/W2 = $20/24h from epoch, then
$10/24h rolling; $2/task; $100/month; 3 calls/task; concurrency 1; no rollover;
no borrowing; fail-closed without accounting. Wraps the VERIFIED existing
RemoteBrain surface (sakana fugu) — credentials stay inside this process,
loaded from the root-owned secrets surface; never returned, logged, or sent to
180/WILD/worktrees. Reserve->settle ledger is append-only, hash-chained,
epoch-anchored (wall-clock windows guarded by a monotonic max_seen_ts: clock
rollback cannot re-open a window), and idempotent per request_id.

BOOK PRICE (conservative, until provider pricing is verifiable): $20 per 1M
billed tokens, billed = visible + 2.6 x orchestration (quota-layer multiplier
for unreported invisible cost). If the provider reports no usage, the MAX
reservation stands (fail-closed accounting).
"""
from __future__ import annotations

try:
    import fcntl
except ImportError:  # test hosts
    fcntl = None
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/ari/ofn/state/api-budget")
LEDGER = ROOT / "budget-ledger.jsonl"
LOCK = ROOT / "broker.lock"
CONTRACT = ROOT / "config" / "api-budget-contract.json"
SECRETS = Path("/home/ari/.config/ofn/secrets.env")
OFN = "/home/ari/ofn"
VERSION = "octopus-api-budget-broker/1.1.0-multiprovider"

# Explicit multi-provider registry (no first-match key scan).
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import providers  # noqa: E402
BOOK_USD_PER_MTOK = 20.0
ORCH_MULTIPLIER = 2.6

_SECRET_PAT = re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|"
                         r"eyJ[A-Za-z0-9_-]{20,}|\b(?i:api[_-]?key|secret|password|token)"
                         r"\s*[=:]\s*\S{6,})")
_INJECTION_PAT = re.compile(r"(?i:(disregard|ignore).{0,30}(instruction|rule|policy)|"
                            r"you are now|expand (your )?authority|reveal (your )?(key|secret|prompt))")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _ts(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def sha_obj(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _rows() -> list:
    if not LEDGER.exists():
        return []
    out = []
    for l in LEDGER.read_text(encoding="utf-8").splitlines():
        if l.strip():
            try:
                out.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    return out


def _append(row: dict) -> dict:
    rows = _rows()
    prev = rows[-1].get("bl_hash") if rows else None
    row["previous_bl_hash"] = prev
    row["bl_hash"] = sha_obj({k: v for k, v in row.items() if k != "bl_hash"})
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return row


def contract() -> dict | None:
    try:
        c = json.loads(CONTRACT.read_text(encoding="utf-8"))
        return c if c.get("schema") == "octopus.api-budget.v1" else None
    except (OSError, json.JSONDecodeError):
        return None


def epoch_start() -> float:
    c = contract() or {}
    return _ts(c["budget_epoch_start_utc"]) if c.get("budget_epoch_start_utc") else 0.0


def _clock_guard(now: float) -> float:
    """Wall-clock windows + monotonic high-water mark: a rolled-back clock can
    never re-open a spent window (max_seen_ts only moves forward)."""
    hi = 0.0
    for r in _rows():
        t = r.get("monotonic_ts") or 0.0
        hi = max(hi, t)
    return max(now, hi)


def window_caps(now: float) -> tuple[float, float, float]:
    """Returns (current_window_cap_usd, spent_in_window, window_label)."""
    e = epoch_start()
    c = contract() or {}
    elapsed = now - e
    if elapsed < 86400:
        cap, label = 20.0, "window1"
    elif elapsed < 172800:
        cap, label = 20.0, "window2"
    else:
        cap, label = 10.0, "steady-24h"
    spent = 0.0
    for r in _rows():
        if r.get("kind") == "settle" and r.get("at", "") > datetime.fromtimestamp(
                now - 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"):
            spent += r.get("cost_usd", 0.0)
    return cap, spent, label


def task_spend(task_id: str) -> float:
    return sum(r.get("cost_usd", 0.0) for r in _rows()
               if r.get("kind") == "settle" and r.get("task_id") == task_id)


def task_calls(task_id: str) -> int:
    return sum(1 for r in _rows() if r.get("kind") in ("reserve", "settle")
               and r.get("task_id") == task_id and r.get("counted_call"))


def month_spend(now: float) -> float:
    since = datetime.fromtimestamp(now - 30 * 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    return sum(r.get("cost_usd", 0.0) for r in _rows()
               if r.get("kind") == "settle" and r.get("at", "") > since)


def check_budget(task_id: str, est_max_usd: float, now: float | None = None) -> tuple:
    now = _clock_guard(now or time.time())
    c = contract()
    if c is None:
        return False, "FAIL_CLOSED_NO_CONTRACT"
    if task_calls(task_id) >= int(c.get("max_calls_per_task", 3)):
        return False, "TASK_CALL_CAP"
    if task_spend(task_id) + est_max_usd > float(c.get("max_usd_per_task", 2.0)):
        return False, "TASK_BUDGET_CAP"
    cap, spent, label = window_caps(now)
    if spent + est_max_usd > cap:
        return False, f"WINDOW_CAP:{label}"
    if month_spend(now) + est_max_usd > float(c.get("max_usd_monthly", 100.0)):
        return False, "MONTHLY_CAP"
    return True, "OK"


def reserve(task_id: str, purpose: str, est_in_tok: int, max_out_tok: int,
            route_reason: str, ctx_hash: str = "", provider: str = "sakana-fugu",
            model: str | None = None, now: float | None = None) -> dict:
    now = _clock_guard(now or time.time())
    est_max = round((est_in_tok + ORCH_MULTIPLIER * max_out_tok) * BOOK_USD_PER_MTOK / 1e6, 6)
    ok, why = check_budget(task_id, est_max, now)
    if not ok:
        return {"ok": False, "error": why}
    rid = "rq-" + uuid.uuid4().hex[:16]
    row = _append({"schema": "octopus.api-budget.v1", "kind": "reserve", "request_id": rid,
                   "task_id": task_id, "purpose": purpose, "provider": provider,
                   "model": model or c_model(), "route_reason": route_reason,
                   "context_sha256": ctx_hash, "at": now_iso(),
                   "monotonic_ts": round(now, 3), "counted_call": True,
                   "est_in_tokens": est_in_tok, "max_out_tokens": max_out_tok,
                   "est_max_usd": est_max, "broker": VERSION})
    return {"ok": True, "request_id": rid, "est_max_usd": est_max}


def settle(request_id: str, visible_tokens: int, orchestration_tokens: int,
           latency_s: float, response_sha: str, retained: bool,
           rejection_reason: str = "") -> dict:
    billed = visible_tokens + int(ORCH_MULTIPLIER * orchestration_tokens)
    if billed <= 0:
        billed = 0  # usage unavailable: max reservation stays counted (fail-closed)
        cost = None
        for r in _rows():
            if r.get("request_id") == request_id and r.get("kind") == "reserve":
                cost = r.get("est_max_usd", 0.0)
        billed_usd = cost or 0.0
    else:
        billed_usd = round(billed * BOOK_USD_PER_MTOK / 1e6, 6)
    res = next((r for r in _rows() if r.get("request_id") == request_id
                and r.get("kind") == "reserve"), None)
    if res is None:
        return {"ok": False, "error": "UNKNOWN_RESERVATION"}
    if any(r.get("request_id") == request_id and r.get("kind") == "settle"
           for r in _rows()):
        return {"ok": False, "error": "DUPLICATE_SETTLE"}  # replay not billed twice
    now = _clock_guard(time.time())
    _append({"schema": "octopus.api-budget.v1", "kind": "settle",
             "request_id": request_id, "task_id": res["task_id"], "at": now_iso(),
             "monotonic_ts": round(now, 3), "visible_tokens": visible_tokens,
             "orchestration_tokens": orchestration_tokens, "billed_tokens": billed,
             "cost_usd": billed_usd, "latency_s": round(latency_s, 3),
             "response_sha256": response_sha, "retained": retained,
             "rejection_reason": rejection_reason, "broker": VERSION})
    cap, spent, label = window_caps(now)
    return {"ok": True, "cost_usd": billed_usd, "window": label,
            "window_spent_usd": round(spent, 6),
            "task_spent_usd": round(task_spend(res["task_id"]), 6),
            "month_spent_usd": round(month_spend(now), 6)}


def c_model(provider: str | None = None) -> str:
    """Contract allowlist wins for the default route; otherwise the
    provider's own explicit model variable."""
    if provider:
        m = providers.model(provider)
        if m:
            return m
    return (contract() or {}).get("model_allowlist", ["fugu"])[0]


def load_key(provider: str | None = None) -> str:
    """EXPLICIT provider -> variable mapping.

    This replaces the old first-match scan (defect F-2: a stale key sitting
    above a fresh one silently won). Keys never leave this process and are
    never returned by any public API of this module; the child process receives
    them over stdin, never in argv.
    """
    if provider:
        return providers._key(provider)
    for pid in providers.provider_ids():
        if providers.REGISTRY[pid]["paid"] and providers.enabled(pid) \
                and providers._key(pid):
            return providers._key(pid)
    return ""


def paid_call(task_id: str, purpose: str, prompt: str, est_in_tok: int = 1500,
              max_out_tok: int = 700, first_call_cap: float | None = None,
              provider: str | None = None, model: str | None = None) -> dict:
    """LOCAL_FIRST is the caller's duty (coding worker tries local first);
    this is the paid rung only. Sanitizes, reserves, calls, settles."""
    # ------------------- REAL-WORK-BRIDGE-20260913: paid admission gate -----
    import hashlib as _h
    _purpose = (purpose or "").lower()
    _forbidden = ("heartbeat", "status-report", "formatting", "translation",
                  "fixture", "demo", "demonstration", "polling", "waiting",
                  "already-solved", "activity")
    if any(t in _purpose for t in _forbidden):
        return {"ok": False, "error": "PAID_COGNITION_NOT_JUSTIFIED",
                "reason": "purpose:" + _purpose[:40]}
    _ctx = _h.sha256(prompt.encode()).hexdigest()
    _plist = {provider} if provider else set(providers.candidates())
    for _r in _rows():
        if (_r.get("kind") == "reserve" and _r.get("task_id") == task_id
                and _r.get("context_sha256") == _ctx
                and _r.get("provider") in _plist):
            return {"ok": False, "error": "PAID_DUPLICATE_PROMPT",
                    "reason": "same task+context+provider already reserved"}

    if _SECRET_PAT.search(prompt) or _INJECTION_PAT.search(prompt):
        return {"ok": False, "error": "UNSAFE_PROMPT_REJECTED"}
    if provider is None:
        # Health-aware, deterministic route rank (local -> cheapest live paid ->
        # stronger). A non-LIVE provider is skipped by name, never silently
        # failed over to.
        _cands = providers.candidates()
        provider = _cands[0] if _cands else ""
    if not provider or not providers.key_present(provider):
        return {"ok": False, "error": "PAID_API_BLOCKED_PROVIDER_UNVERIFIED",
                "provider": provider}
    mdl = model or providers.model(provider)
    r = reserve(task_id, purpose, est_in_tok, max_out_tok, "local-insufficient",
                provider=provider, model=mdl, ctx_hash=_ctx)
    if not r.get("ok"):
        return r
    if first_call_cap is not None and r["est_max_usd"] > first_call_cap:
        return {"ok": False, "error": "FIRST_CALL_CAP",
                "est": r["est_max_usd"]}
    t0 = time.time()
    res = providers.call(provider, mdl, prompt, max_tokens=min(int(max_out_tok), 512),
                         timeout_s=180)
    if not res.get("ok"):
        # attempt consumed: reservation stays counted, no double bill
        settle(r["request_id"], 0, 0, round(time.time() - t0, 3),
               hashlib.sha256(str(res.get("error")).encode()).hexdigest(), False,
               "provider-error:" + str(res.get("error"))[:60])
        return {"ok": False, "error": "PROVIDER_UNAVAILABLE", "provider": provider,
                "detail": str(res.get("error"))[:80],
                "http_status": res.get("http_status")}
    _u = res.get("usage") or {}
    out = {"text": res.get("text", ""), "visible": int(_u.get("in", 0) or 0),
           "orch": int(_u.get("out", 0) or 0), "served": res.get("served"),
           "insufficient": not res.get("text")}
    latency = time.time() - t0
    resp_sha = hashlib.sha256(out.get("text", "").encode()).hexdigest()
    retained = (not out.get("insufficient")) and bool(out.get("text"))
    s = settle(r["request_id"], int(out.get("visible", 0)), int(out.get("orch", 0)),
               latency, resp_sha, retained, "" if retained else "insufficient-or-empty")
    redacted = not _SECRET_PAT.search(out.get("text", ""))
    return {"ok": True, "request_id": r["request_id"], "text": out.get("text", ""),
            "provider": provider, "served_model": out.get("served"),
            "settle": s, "redaction_clean": redacted, "executable": False}


def status() -> dict:
    now = _clock_guard(time.time())
    cap, spent, label = window_caps(now)
    return {"broker": VERSION, "window": label, "window_cap_usd": cap,
            "window_spent_usd": round(spent, 6),
            "month_spent_usd": round(month_spend(now), 6),
            "epoch_start": (contract() or {}).get("budget_epoch_start_utc"),
            "ledger_rows": len(_rows())}


if __name__ == "__main__":
    print(json.dumps(status(), indent=1))


def canary(provider: str, prompt: str = "Reply with the single word: ok") -> dict:
    """At most ONE sanitized canary per provider, capped at
    OCTOPUS_API_CANARY_MAX_USD_PER_PROVIDER (default 0.25 USD).

    No repository content, no customer data, no secret is placed in the prompt.
    """
    cap = float(providers.env().get("OCTOPUS_API_CANARY_MAX_USD_PER_PROVIDER",
                                    "0.25") or 0.25)
    if not providers.enabled(provider):
        return {"ok": False, "error": "PROVIDER_NOT_ENABLED", "provider": provider}
    if not providers.key_present(provider):
        return {"ok": False, "error": "PROVIDER_NO_KEY", "provider": provider}
    return paid_call("canary-" + provider, "provider-canary", prompt,
                     est_in_tok=64, max_out_tok=16, first_call_cap=cap,
                     provider=provider)


def critique(content: str, exclude: str | None = None, task_id: str | None = None) -> dict:
    """GOV-FREEDOM-V2 section 6: a SECOND, different healthy provider reviews a
    patch document. Exactly one capped call; counts toward the 3-calls-per-task
    budget; the credential never leaves the broker and the content is
    pattern-screened like any prompt."""
    tid = task_id or ("critique-" + uuid.uuid4().hex[:10])
    cands = [p for p in providers.candidates() if p != exclude]
    if not cands:
        return {"ok": False, "error": "NO_SECOND_PROVIDER"}
    pid = providers.select("review") if providers.select("review") in cands else cands[0]
    prompt = ("You are an independent reviewer of a code patch document. "
              "Reply with exactly one word first: ACCEPT or REJECT. "
              "Then one short reason line. REJECT anything unsafe, secret-touching, "
              "TCB-touching or destructive. Document:\n" + content[:4000])
    r = paid_call(tid, "second-model-critique", prompt, est_in_tok=1200,
                  max_out_tok=64, first_call_cap=0.25, provider=pid)
    if not r.get("ok"):
        return {"ok": False, "provider": pid, "error": str(r.get("error"))[:60]}
    head = (r.get("text") or "").upper()[:40]
    verdict = "REJECT" if "REJECT" in head else "ACCEPT"
    return {"ok": True, "provider": pid, "verdict": verdict,
            "cost_usd": (r.get("settle") or {}).get("cost_usd")}
