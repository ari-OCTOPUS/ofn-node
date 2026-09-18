#!/usr/bin/env python3
"""Fixture-driven tests for provider_failover — no network, no secrets."""
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "provider_failover.py"
if not SRC.exists():
    SRC = HERE.parent / "provider_failover.py"
spec = importlib.util.spec_from_file_location("pf", SRC)
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name, detail if not ok else "")
    (PASS if ok else FAIL).append(name)


class FakeProviders:
    """Minimal stand-in for providers.py with scripted HTTP outcomes."""
    ROUTE_RANK = ("sakana-fugu", "deepseek", "openai", "anthropic", "gemini")
    REGISTRY = {p: {"paid": True} for p in ROUTE_RANK}
    script = {}

    @classmethod
    def provider_ids(cls):
        return list(cls.ROUTE_RANK)

    @classmethod
    def enabled(cls, pid):
        return True

    @classmethod
    def key_present(cls, pid):
        return True

    @classmethod
    def list_models(cls, pid, timeout_s=20):
        return cls.script.get(pid, {"ok": True, "http_status": 200, "count": 3})


def iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def setup():
    fx = Path(tempfile.mkdtemp(prefix="pf-fx-"))
    pf.HEALTH_FILE = fx / "provider-health.json"
    pf.HISTORY_FILE = fx / "provider-health.jsonl"
    pf.providers = FakeProviders
    FakeProviders.script = {}
    return fx


def main():
    setup()
    # T1: 200 -> LIVE, cooldown cleared
    FakeProviders.script = {"sakana-fugu": {"ok": True, "http_status": 200, "count": 2}}
    pf.refresh_all()
    rec = pf.load()
    check("T1 live_200", rec["sakana-fugu"]["status"] == "LIVE"
          and not rec["sakana-fugu"].get("cooldown_until"))

    # T2: 429 -> RATE_LIMITED + cooldown >= 6h
    FakeProviders.script = {"sakana-fugu": {"ok": False, "http_status": 429,
                                            "error": "rate_limit"}}
    pf.refresh_all()
    rec = pf.load()
    e = rec["sakana-fugu"]
    cd_s = (time.mktime(time.strptime(e["cooldown_until"], "%Y-%m-%dT%H:%M:%SZ"))
            - time.timezone) - time.time()
    check("T2 rate_limited_cooldown", e["status"] == "RATE_LIMITED" and cd_s > 5 * 3600,
          f"cd_s={cd_s/3600:.1f}h")

    # T3: pick() skips cooling provider, returns next healthy
    got = pf.pick("standard")
    check("T3 pick_skips_cooling", got == "deepseek", got)

    # T4: live_providers excludes the cooling one
    live = pf.live_providers()
    check("T4 live_excludes_cooling", "sakana-fugu" not in live and live, live)

    # T5: cooldown expiry re-includes (simulate past cooldown)
    rec = pf.load()
    rec["sakana-fugu"]["cooldown_until"] = iso(time.time() - 60)
    rec["sakana-fugu"]["status"] = "LIVE"
    pf.save(rec)
    check("T5 expired_cooling_readmitted", "sakana-fugu" in pf.live_providers())

    # T6: escalation — repeated TRANSIENT failures grow the cooldown
    FakeProviders.script = {}
    rec = pf.load()
    rec["deepseek"]["consecutive_failures"] = 0
    pf.save(rec)
    pf.HEALTH_FILE.unlink()
    FakeProviders.script = {"deepseek": {"ok": False, "http_status": 503, "error": "x"}}
    pf.refresh_all()
    first = pf.load()["deepseek"].get("cooldown_s")
    pf.refresh_all()
    second = pf.load()["deepseek"].get("cooldown_s")
    check("T6 escalation", first and second and second >= first, (first, second))

    # T7: key rejected -> status + no live pick
    FakeProviders.script = {p: {"ok": False, "http_status": 401, "error": "bad"}
                            for p in FakeProviders.ROUTE_RANK}
    pf.refresh_all()
    check("T7 key_rejected_blocks", pf.pick("standard") == "",
          pf.status_line())

    # T8: ensure_fresh probes when stale, then no-ops while fresh
    calls = {"n": 0}
    orig = FakeProviders.list_models.__func__

    def counting(cls, pid, timeout_s=20):
        calls["n"] += 1
        return {"ok": True, "http_status": 200, "count": 1}

    FakeProviders.list_models = classmethod(counting)
    rec = pf.load()
    rec["_meta"]["last_refresh_utc"] = iso(time.time() - 7200)  # stale
    pf.save(rec)
    pf.ensure_fresh(3600)
    first_calls = calls["n"]
    pf.ensure_fresh(3600)
    check("T8 fresh_noop", first_calls > 0 and calls["n"] == first_calls, calls)

    # T9: stale record triggers re-probe
    rec = pf.load()
    rec["_meta"]["last_refresh_utc"] = iso(time.time() - 7200)
    pf.save(rec)
    before = calls["n"]
    pf.ensure_fresh(3600)
    check("T9 stale_reprobes", calls["n"] > before, (before, calls["n"]))
    FakeProviders.list_models = orig

    # T10: record never contains key-like values
    SetupSecrets = ["sk-test", "xoxb-123"]
    blob = pf.HEALTH_FILE.read_text(encoding="utf-8")
    check("T10 no_secret_values", all(s not in blob for s in SetupSecrets)
          and "api_key" not in blob and "key_value" not in blob)

    print(f"-- {len(PASS)+len(FAIL)} checks, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
