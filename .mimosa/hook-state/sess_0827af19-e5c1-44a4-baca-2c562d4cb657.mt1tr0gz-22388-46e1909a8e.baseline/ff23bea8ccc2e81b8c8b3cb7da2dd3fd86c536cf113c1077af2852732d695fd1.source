"""
Phase 8 -- external-I/O resilience (retry/backoff + idempotency). OFFLINE.

  - retryable failures (429/5xx) are retried with backoff, then succeed
  - before_attempt (check_and_enforce) exceptions are NOT retried -> propagate
  - non-retryable errors propagate on the first failure
  - all-fail -> raises after exactly max_attempts
  - Retry-After header overrides the computed backoff
  - through Worker C: a retried Haiku call logs cost ONCE (no double-charge) and
    reuses ONE idempotency key across attempts
"""
import os
import sys
import tempfile

_TMP_DB = tempfile.mkstemp(suffix="_brushline_p8.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = ""
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"
os.environ["RETRY_BASE_DELAY_SEC"] = "0"          # fast test (no real sleeping)
os.environ["SPEND_CAP_PER_ACTION_AUD"] = "5.00"
os.environ["SPEND_CAP_PER_DAY_AUD"] = "20.00"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_connection
from src.resilience import call_with_retry, new_idempotency_key
from src.governance import SpendCapExceeded
from src.agents.content import ContentAgent


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


class FakeHTTPErr(Exception):
    def __init__(self, status=429, retry_after=None):
        super().__init__(f"HTTP {status}")
        self.status_code = status
        if retry_after is not None:
            self.response = type("R", (), {
                "status_code": status,
                "headers": {"retry-after": str(retry_after)},
            })()


def main():
    init_db()

    # 1) retry then succeed
    calls = {"n": 0}
    sleeps = []
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise FakeHTTPErr(429)
        return "ok"
    res = call_with_retry(flaky, agent_id="t", max_attempts=3, base_delay=0.0,
                          sleep=lambda d: sleeps.append(d))
    _check("retryable -> eventual success", res == "ok")
    _check("retried until 3rd attempt", calls["n"] == 3)
    _check("slept between attempts (2 backoffs)", len(sleeps) == 2)

    # 2) before_attempt (governance) exception is NOT retried
    op_calls = {"n": 0}
    def op(): op_calls["n"] += 1; return "x"
    def gate(): raise SpendCapExceeded("daily cap")
    raised = False
    try:
        call_with_retry(op, before_attempt=gate, sleep=lambda d: None)
    except SpendCapExceeded:
        raised = True
    _check("spend-cap in before_attempt propagates", raised)
    _check("op never ran when governance blocked", op_calls["n"] == 0)

    # 3) non-retryable error propagates on first failure
    vc = {"n": 0}
    def boom(): vc["n"] += 1; raise ValueError("nope")
    raised = False
    try:
        call_with_retry(boom, max_attempts=3, sleep=lambda d: None)
    except ValueError:
        raised = True
    _check("non-retryable raises", raised)
    _check("non-retryable NOT retried (1 call)", vc["n"] == 1)

    # 4) all attempts fail -> raise after exactly max_attempts
    fc = {"n": 0}
    def always(): fc["n"] += 1; raise FakeHTTPErr(503)
    raised = False
    try:
        call_with_retry(always, max_attempts=3, base_delay=0.0, sleep=lambda d: None)
    except FakeHTTPErr:
        raised = True
    _check("exhausts and raises", raised)
    _check("exactly max_attempts tried", fc["n"] == 3)

    # 5) Retry-After header overrides computed backoff
    ra = {"n": 0}
    ra_sleeps = []
    def ra_op():
        ra["n"] += 1
        if ra["n"] < 2:
            raise FakeHTTPErr(429, retry_after=0)
        return "ok"
    call_with_retry(ra_op, max_attempts=2, base_delay=5.0,
                    sleep=lambda d: ra_sleeps.append(d))
    _check("Retry-After honoured (delay=0, not base 5)", ra_sleeps == [0.0])

    # 6) through Worker C: retried Haiku logs cost ONCE + one idempotency key
    class FlakyAnthropic:
        def __init__(self, fail_times):
            self.calls = 0
            self.keys = []
            self.fail_times = fail_times
            self.messages = self
        def create(self, **kw):
            self.calls += 1
            self.keys.append((kw.get("extra_headers") or {}).get("Idempotency-Key"))
            if self.calls <= self.fail_times:
                raise FakeHTTPErr(429)
            return type("M", (), {
                "content": [type("C", (), {"text": "Hi Sam, happy to help."})()],
                "usage": type("U", (), {"input_tokens": 50, "output_tokens": 20})(),
            })()

    c = ContentAgent()
    fake = FlakyAnthropic(fail_times=1)   # fail once, then succeed
    c._llm = fake
    d = c.draft_speed_to_lead({"id": None, "name": "Sam", "suburb": "Glebe",
                               "service_type": "interior"})
    _check("Worker C draft produced after retry", len(d.content) > 20)
    _check("Haiku retried once (2 create calls)", fake.calls == 2)
    _check("real Haiku cost computed (>0)", d.cost_usd > 0.0)
    _check("idempotency key stable across retries",
           len(set(fake.keys)) == 1 and fake.keys[0] is not None)

    conn = get_connection()
    try:
        n_cost = conn.execute("SELECT COUNT(*) AS c FROM cost_events").fetchone()["c"]
        n_retry = conn.execute(
            "SELECT COUNT(*) AS c FROM audit_entries WHERE event_type='IO_RETRY'"
        ).fetchone()["c"]
    finally:
        conn.close()
    _check("cost logged exactly once (no double-charge)", n_cost == 1)
    _check("retry recorded in audit (IO_RETRY)", n_retry >= 1)

    print("\nALL RESILIENCE (P8) CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
