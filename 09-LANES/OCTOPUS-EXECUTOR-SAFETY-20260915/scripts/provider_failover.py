#!/usr/bin/env python3
"""provider_failover.py — health-probing failover for the OCTOPUS paid rung.

Owner directive 2026-09-17: the keys for deepseek / anthropic / openai / gemini
carry credit and fugu's limit reopens later; the system must CHECK and must
never sit idle because ONE provider is limited.

Zero-spend by design: probing uses each provider's FREE models/discovery
endpoint (never a chat completion, never a billed call).

Contract
--------
* No credential value is ever read into a variable that leaves this module:
  probing delegates to providers.list_models(), which already guarantees that.
* `refresh_all()` measures every paid provider and records status, http code,
  checked_at, consecutive_failures and cooldown_until (no secrets).
* `pick(need)` returns the first provider that is enabled, keyed, measured
  LIVE, and NOT cooling down; `ensure_fresh()` re-probes only when the record
  is older than max_age_s (default 1h) so callers can invoke it per-call.
* Everything degrades gracefully: if providers.py cannot be imported the
  module reports unavailable and callers keep their previous behaviour.
"""
from __future__ import annotations

import json
import pathlib
import time

try:
    import providers  # same directory on node 138
except Exception:  # pragma: no cover - import-time environment guard
    providers = None

HEALTH_FILE = pathlib.Path(
    "/home/ari/ofn/state/api-budget/config/provider-health.json"
)
HISTORY_FILE = pathlib.Path(
    "/home/ari/ofn/state/api-budget/config/provider-health.jsonl"
)

# failure class -> base cooldown seconds
COOLDOWN = {
    "RATE_LIMITED": 6 * 3600,
    "CREDIT_EXHAUSTED": 24 * 3600,
    "KEY_REJECTED": 24 * 3600,
    "TRANSIENT": 15 * 60,
    "UNREACHABLE": 15 * 60,
}
FAIL_ESCALATION = (15 * 60, 3600, 6 * 3600, 24 * 3600)  # by consecutive count
NEED_PREFERENCE = {
    "patch": ("deepseek", "openai", "anthropic", "gemini"),
    "quick": ("gemini", "deepseek", "openai", "anthropic"),
    "strong": ("openai", "anthropic", "deepseek", "gemini"),
    "review": ("anthropic", "openai", "deepseek", "gemini"),
}


def _now() -> float:
    return time.time()


def _iso(ts: float | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts or _now()))


def load() -> dict:
    try:
        return json.loads(HEALTH_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return {}


def save(rec: dict) -> None:
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_FILE.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n",
                           encoding="utf-8")


def _classify(http_status: int | None, ok: bool, err: str = "") -> str:
    if ok:
        return "LIVE"
    if http_status == 429:
        return "RATE_LIMITED"
    if http_status == 402:
        return "CREDIT_EXHAUSTED"
    if http_status in (401, 403):
        return "KEY_REJECTED"
    if http_status is None:
        return "UNREACHABLE"
    return "TRANSIENT"


def probe(pid: str, timeout_s: int = 20) -> dict:
    """Free probe of one provider. Returns a status dict, never a secret."""
    if providers is None:
        return {"status": "UNPROBED", "reason": "providers_module_unavailable"}
    try:
        res = providers.list_models(pid, timeout_s=timeout_s)
    except Exception as e:  # network/DNS/etc. — never crash the caller
        return {"status": "UNREACHABLE", "http_status": None,
                "reason": type(e).__name__, "checked_at": _iso()}
    ok = bool(res.get("ok"))
    st = _classify(res.get("http_status"), ok, str(res.get("error") or ""))
    out = {"status": st, "http_status": res.get("http_status"),
           "checked_at": _iso()}
    if ok:
        out["models_count"] = res.get("count")
    else:
        out["reason"] = str(res.get("error") or "")[:80]
    return out


def refresh_all(timeout_s: int = 20) -> dict:
    """Probe every PAID provider; update status/cooldown/failure counters."""
    if providers is None:
        return {"ok": False, "reason": "providers_module_unavailable"}
    rec = load()
    for pid in providers.provider_ids():
        d = providers.REGISTRY.get(pid) or {}
        if not d.get("paid"):
            continue
        entry = rec.get(pid) or {}
        if not (providers.enabled(pid) and providers.key_present(pid)):
            entry.update({"status": "NOT_CONFIGURED", "checked_at": _iso()})
            rec[pid] = entry
            continue
        got = probe(pid, timeout_s)
        prev_fail = int(entry.get("consecutive_failures") or 0)
        if got["status"] == "LIVE":
            got["consecutive_failures"] = 0
            got["cooldown_until"] = None
        else:
            n = prev_fail + 1
            got["consecutive_failures"] = n
            base = COOLDOWN.get(got["status"], 900)
            esc = FAIL_ESCALATION[min(n - 1, len(FAIL_ESCALATION) - 1)]
            secs = max(base, esc)
            got["cooldown_until"] = _iso(_now() + secs)
            got["cooldown_s"] = secs
        # preserve human-curated metadata fields
        for k in ("tier_source", "evidence", "unblocked_by", "paid",
                  "credential_from_chat_transcript"):
            if k in entry and k not in got:
                got[k] = entry[k]
        got["paid"] = bool(d.get("paid"))
        rec[pid] = got
    rec.setdefault("_meta", {})["last_refresh_utc"] = _iso()
    rec["_meta"]["probe_method"] = "free models/discovery endpoint (zero spend)"
    save(rec)
    try:
        with HISTORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": _iso(), "record": rec},
                               sort_keys=True) + "\n")
    except OSError:
        pass
    return {"ok": True, "record": rec}


def _fresh(entry: dict, max_age_s: int) -> bool:
    try:
        t = time.mktime(time.strptime(entry.get("checked_at", ""),
                                      "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    except (ValueError, TypeError):
        return False
    return (_now() - t) <= max_age_s


def cooling(entry: dict) -> bool:
    cu = entry.get("cooldown_until")
    if not cu:
        return False
    try:
        t = time.mktime(time.strptime(cu, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    except (ValueError, TypeError):
        return False
    return _now() < t


def ensure_fresh(max_age_s: int = 3600) -> dict:
    """Re-probe only when the record is stale; cheap and idempotent."""
    rec = load()
    last = (rec.get("_meta") or {}).get("last_refresh_utc")
    if last:
        try:
            t = time.mktime(time.strptime(last, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
            if (_now() - t) <= max_age_s:
                return rec
        except (ValueError, TypeError):
            pass
    out = refresh_all()
    return out.get("record", rec) if out.get("ok") else rec


def live_providers(max_age_s: int = 3600) -> list:
    """Enabled+keyed providers measured LIVE and not cooling, in route rank."""
    rec = ensure_fresh(max_age_s)
    out = []
    order = getattr(providers, "ROUTE_RANK", None) or providers.provider_ids()
    for pid in order:
        d = (providers.REGISTRY.get(pid) or {})
        if not d.get("paid"):
            continue
        if not (providers.enabled(pid) and providers.key_present(pid)):
            continue
        e = rec.get(pid) or {}
        if e.get("status") == "LIVE" and not cooling(e):
            out.append(pid)
    return out


def pick(need: str = "standard", max_age_s: int = 3600) -> str:
    """First healthy provider for this need; '' when none is available."""
    if providers is None:
        return ""
    c = live_providers(max_age_s)
    for pid in NEED_PREFERENCE.get(need, ()):
        if pid in c:
            return pid
    return c[0] if c else ""


def status_line() -> str:
    rec = load()
    parts = []
    for pid, e in sorted(rec.items()):
        if pid.startswith("_"):
            continue
        cd = " COOLING" if cooling(e) else ""
        parts.append(f"{pid}:{e.get('status')}{cd}")
    return " ".join(parts)


if __name__ == "__main__":
    import sys
    if "--refresh" in sys.argv:
        r = refresh_all()
        print("refresh ok:", r.get("ok"))
    elif "--pick" in sys.argv:
        need = sys.argv[sys.argv.index("--pick") + 1] if \
            len(sys.argv) > sys.argv.index("--pick") + 1 else "standard"
        print(pick(need))
    print(status_line())
