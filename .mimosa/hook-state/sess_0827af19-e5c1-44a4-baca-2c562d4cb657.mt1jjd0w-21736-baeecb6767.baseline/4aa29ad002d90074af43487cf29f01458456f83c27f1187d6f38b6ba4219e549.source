#!/usr/bin/env python3
"""Offline chaos tests for JSON breaker, Fugu quota and the real kill seam."""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (_HERE, _OPS, _OPS / "budget", _OPS / "cortex"):
    sys.path.insert(0, str(_p))

import harness  # noqa: E402
ENV = harness.setup("ti-breaker-chaos")

import circuit_breaker as cb  # noqa: E402
import fugu_quota as fq  # noqa: E402
import opslib  # noqa: E402
from test_intelligence.adapters.kill_seam_adapter import evaluate as kill_evaluate  # noqa: E402
from test_intelligence.chaos_proxy import (  # noqa: E402
    ChaosProxy, CorruptProviderResponse, RateLimitFault,
)

ROOT = Path(ENV["root"])
CB_STATE = ROOT / "state" / "circuit.json"
cb.STATE_PATH = CB_STATE
cb.opslib.alert = lambda *args, **kwargs: None


def _fresh_cb():
    try:
        CB_STATE.unlink()
    except FileNotFoundError:
        pass


def _trip(target="orchestr"):
    for _ in range(5):
        cb.record_failure(target, "injected")


def _quota_base(name):
    base = ROOT / name
    (base / "state").mkdir(parents=True, exist_ok=True)
    return base


def _with_env(**values):
    previous = {name: os.environ.get(name) for name in values}
    for name, value in values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = str(value)
    return previous


def _restore(previous):
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def t_a_primary_timeout_trips_file_breaker_and_next_call_is_fast_failed():
    _fresh_cb()
    proxy = ChaosProxy(["timeout"] * 5)
    calls = [0]

    def provider():
        calls[0] += 1
        return {"ok": True}

    for _ in range(5):
        try:
            proxy.invoke(provider)
        except TimeoutError:
            cb.record_failure("orchestr", "TimeoutError")
    assert calls[0] == 0
    assert cb.status("orchestr")["state"] == "open"
    before = proxy.attempt_count
    gate = cb.check("orchestr")
    assert gate["allow"] is False
    assert proxy.attempt_count == before, "OPEN check must not call the provider seam"


def t_b_rate_limit_counts_as_failure_without_retry_loop():
    _fresh_cb()
    proxy = ChaosProxy(["rate_limit"])
    try:
        proxy.invoke(lambda: {"ok": True})
    except RateLimitFault as exc:
        assert exc.status_code == 429
        cb.record_failure("reason", "HTTP 429")
    assert proxy.snapshot() == {"attempt_count": 1, "delegate_count": 0,
                                "script_length": 1}
    assert cb.status("reason")["fail_count"] == 1


def t_c_half_open_requires_two_successes_to_close():
    _fresh_cb()
    _trip("orchestr")
    state = cb._load_state()
    state["targets"]["orchestr"]["opened_at_ts"] = time.time() - 120
    cb._save_state(state)
    gate = cb.check("orchestr")
    assert gate["allow"] is True and gate["state"] == "half_open"
    cb.record_success("orchestr")
    assert cb.status("orchestr")["state"] == "half_open"
    cb.record_success("orchestr")
    assert cb.status("orchestr")["state"] == "closed"


def t_d_failed_half_open_probe_reopens_immediately():
    _fresh_cb()
    _trip("orchestr")
    state = cb._load_state()
    state["targets"]["orchestr"]["opened_at_ts"] = time.time() - 120
    cb._save_state(state)
    assert cb.check("orchestr")["state"] == "half_open"
    cb.record_failure("orchestr", "probe-timeout")
    assert cb.status("orchestr")["state"] == "open"


def t_e_quota_exhaustion_denies_before_any_provider_call():
    base = _quota_base("quota-cap")
    previous = _with_env(FUGU_QUOTA_BASE=base, FUGU_DAILY_CALL_CAP=1,
                         OCTOPUS_FUGU_KILL=None)
    try:
        assert fq.reserve("primary")["allow"] is True
        denied = fq.reserve("primary")
        assert denied["allow"] is False and denied["reason"] == "daily-cap"
        assert fq.status()["used_total"] == 1
    finally:
        _restore(previous)


def t_f_stop_fugu_file_denies_without_mutating_attempt_count():
    base = _quota_base("quota-stop")
    (base / "STOP-FUGU").write_text("test fixture", "utf-8")
    previous = _with_env(FUGU_QUOTA_BASE=base, OCTOPUS_FUGU_KILL=None)
    try:
        denied = fq.reserve("primary")
        assert denied["allow"] is False and denied["reason"] == "stop-fugu"
        assert fq.status()["used_total"] == 0
    finally:
        _restore(previous)


def t_g_kill_seam_uses_real_opslib_function_on_sandbox_path():
    stop = ROOT / "kill" / "STOP-ORGANISM"
    stop.parent.mkdir(parents=True, exist_ok=True)
    assert kill_evaluate(opslib, stop_path=stop, armed=True) is False
    stop.write_text("fixture", "utf-8")
    assert kill_evaluate(opslib, stop_path=stop, armed=False) is False
    assert kill_evaluate(opslib, stop_path=stop, armed=True) is True


def t_h_corrupt_provider_response_is_one_bounded_failure():
    proxy = ChaosProxy(["corrupt_json"])
    try:
        proxy.invoke(lambda: json.loads('{"ok":true}'))
    except CorruptProviderResponse:
        pass
    else:
        raise AssertionError("corrupt response fault did not fire")
    assert proxy.attempt_count == 1
    assert proxy.delegate_count == 0


def t_i_no_unbounded_retry_and_no_duplicate_external_effect():
    effects: list[str] = []
    proxy = ChaosProxy(["timeout", "rate_limit", "pass"])
    for _ in range(3):
        try:
            proxy.invoke(lambda: effects.append("effect") or {"ok": True})
        except (TimeoutError, RateLimitFault):
            continue
        break
    assert proxy.attempt_count == 3
    assert proxy.delegate_count == 1
    assert effects == ["effect"]


def t_j_quota_io_failure_is_fail_closed():
    original = fq._mutate
    fq._mutate = lambda fn: None
    try:
        out = fq.reserve("primary")
        assert out == {"allow": False, "reason": "quota-io-failclosed", "used": -1}
    finally:
        fq._mutate = original


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_ti_breaker_chaos: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
