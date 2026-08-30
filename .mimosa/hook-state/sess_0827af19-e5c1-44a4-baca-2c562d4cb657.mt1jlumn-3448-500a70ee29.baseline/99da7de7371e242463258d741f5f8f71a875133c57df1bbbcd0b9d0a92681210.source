#!/usr/bin/env python3
"""تست Phase 5 · S-1..S-6 — ۲۴/۷ survival + convergence ($0 آفلاین).

S-1 watchdog: kill→restart؛ STOP→بدونِ restart (yield بی‌قید).
S-2 germline retry: خطای اجباری لاگ+retry، بی‌صدا گم نشود.
S-3 unified bus: یک event مسیرِ ledger→checkpoint را طی کند؛ non-destructive.
S-4 checkpoint/replay: بازسازیِ state در بیتِ گذشته <۵s.
S-5 MAX_LAG alarm: وقتی بکاپ skip شد شلیک شود.
S-6 smoke 24h: چک‌لیست.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("phase5")
_REAL_OPS = (harness.SELF_OPS)
if str(_REAL_OPS) not in sys.path:
    sys.path.insert(0, str(_REAL_OPS))


# ════════════════════════════════════════════════════════════════════════════════
# S-1 · watchdog
# ════════════════════════════════════════════════════════════════════════════════

def t_watchdog_revive_when_dead():
    """port مرده + no STOP + prior run → revive."""
    import watchdog
    d = Path(tempfile.mkdtemp(prefix="wd-"))
    fake_stop = d / "STOP-ORGANISM"
    should, reason = watchdog.should_revive(
        port_alive=False, stop_flags=[fake_stop], state_exists=True)
    assert should is True, reason
    assert "revive" in reason


def t_watchdog_yield_to_stop():
    """STOP flag → yield (هیچ revive). kill-switch مطلق."""
    import watchdog
    d = Path(tempfile.mkdtemp(prefix="wd-"))
    stop = d / "STOP-ORGANISM"
    stop.write_text("kill", encoding="utf-8")
    should, reason = watchdog.should_revive(
        port_alive=False, stop_flags=[stop], state_exists=True)
    assert should is False, f"نباید revive وقتی STOP هست: {reason}"
    assert "yield" in reason or "STOP" in reason


def t_watchdog_no_revive_if_alive():
    """port زنده → no revive."""
    import watchdog
    should, reason = watchdog.should_revive(port_alive=True, state_exists=True)
    assert should is False
    assert "alive" in reason


def t_watchdog_no_first_birth():
    """state غایب = اولین بار → no revive (owner-launched، INC-1)."""
    import watchdog
    should, reason = watchdog.should_revive(
        port_alive=False, state_exists=False)
    assert should is False, f"اولین تولد نباید با watchdog: {reason}"
    assert "first-birth" in reason or "owner" in reason


def t_watchdog_revive_action_noop_when_stop():
    """revive_action وقتی STOP هست → NO-OP."""
    import watchdog
    d = Path(tempfile.mkdtemp(prefix="wd-"))
    stop = d / "STOP-ORGANISM"
    stop.write_text("kill", encoding="utf-8")
    watchdog.STOP_FLAGS = [stop]
    result = watchdog.revive_action()
    assert "NO-OP" in result


# ════════════════════════════════════════════════════════════════════════════════
# S-2/S-5 · germline lag + MAX_LAG alarm + retry
# ════════════════════════════════════════════════════════════════════════════════

def t_lag_zero_when_recent():
    """بکاپِ تازه → lag ≈ 0 → ok."""
    import germline
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    lag = germline.compute_lag_hours(now, now, now_ts=now)
    assert lag < 0.1, f"lag باید ≈0 باشد: {lag}"
    assert germline.lag_severity(lag) == "ok"


def t_lag_warn_over_2h():
    """lag > 2h → warn."""
    import germline
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    old = (now - timedelta(hours=3)).isoformat()
    lag = germline.compute_lag_hours(old, old, now_ts=now.isoformat())
    assert lag > 2.0
    assert germline.lag_severity(lag) == "warn"


def t_lag_error_over_26h():
    """lag > 26h → ERROR."""
    import germline
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    old = (now - timedelta(hours=27)).isoformat()
    lag = germline.compute_lag_hours(old, None, now_ts=now.isoformat())
    assert germline.lag_severity(lag) == "ERROR"


def t_lag_crit_over_72h():
    """lag > 72h → CRIT (نبودِ بکاپ = مرگِ قریب‌الوقوع)."""
    import germline
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    old = (now - timedelta(hours=73)).isoformat()
    lag = germline.compute_lag_hours(old, old, now_ts=now.isoformat())
    assert germline.lag_severity(lag) == "CRIT"


def t_lag_crit_when_no_backup():
    """هیچ بکاپی → lag=inf → CRIT."""
    import germline
    lag = germline.compute_lag_hours(None, None)
    assert lag == float("inf")
    assert germline.lag_severity(lag) == "CRIT"


def t_retry_logs_and_retries():
    """خطای اجباری → retry + لاگ، نه بی‌صدا گم."""
    import germline
    logs = []
    attempts = [0]
    def failing_fn():
        attempts[0] += 1
        raise RuntimeError("simulated push failure")
    result = germline.run_with_retry(failing_fn, max_retries=3, base_backoff=0.01,
                                      logger=logs.append)
    assert result["ok"] is False
    assert result["attempts"] == 3
    assert "simulated push failure" in result["last_error"]
    assert len(logs) >= 2, f"باید لاگ شده باشد: {logs}"   # retry لاگ‌ها


def t_retry_succeeds_on_second():
    """اگر fn در attempt دوم موفق شود → ok."""
    import germline
    state = [0]
    def flaky_fn():
        state[0] += 1
        if state[0] == 1:
            return False   # اولین شکست
        return True
    result = germline.run_with_retry(flaky_fn, max_retries=3, base_backoff=0.01)
    assert result["ok"] is True
    assert result["attempts"] == 2


def t_lag_alarm_from_paths():
    """lag_alarm_from_paths با مسیرهای موقت."""
    import germline
    d = Path(tempfile.mkdtemp(prefix="germ-"))
    logf = d / "hourly.log"
    logf.write_text("test", encoding="utf-8")
    result = germline.lag_alarm_from_paths(logf, d)
    assert result["germline_alert"] in ("ok", "warn", "ERROR", "CRIT")
    assert "germline_lag_h" in result


# ════════════════════════════════════════════════════════════════════════════════
# S-3 · unified bus
# ════════════════════════════════════════════════════════════════════════════════

def _fresh_ledger():
    """یک Ledger واقعی در vault موقت. هر بار یک فایلِ یکتا."""
    import uuid as _uuid
    sys.path.insert(0, str(ENV["genome"] / "ledger"))
    from ledger import Ledger
    return Ledger(ENV["genome"] / "ledger" / f"p5-{_uuid.uuid4().hex[:8]}.jsonl")


def t_unified_publish_to_ledger():
    """publish → genome ledger. entry حاوی hash/age_tick."""
    from unified_bus import UnifiedBus
    lg = _fresh_ledger()
    bus = UnifiedBus(ledger=lg)
    entry = bus.publish("NOTE", {"x": 1}, actor="test")
    assert isinstance(entry, dict)
    assert entry.get("hash"), "entry باید hash داشته باشد"
    assert entry.get("type") == "NOTE"


def t_unified_publish_human_advances_age():
    """is_human=True → age_tick +۱ (human-append)."""
    from unified_bus import UnifiedBus
    lg = _fresh_ledger()
    bus = UnifiedBus(ledger=lg)
    before = lg.last_age_tick()
    bus.publish("APPROVAL", {"v": "yes"}, actor="human", is_human=True)
    after = lg.last_age_tick()
    assert after == before + 1, f"age_tick باید +۱: {before}→{after}"


def t_unified_publish_non_human_no_age():
    """is_human=False → age_tick ثابت (non-human فلش را نمی‌برد)."""
    from unified_bus import UnifiedBus
    lg = _fresh_ledger()
    bus = UnifiedBus(ledger=lg)
    before = lg.last_age_tick()
    bus.publish("NOTE", {"x": 1}, actor="agent", is_human=False)
    after = lg.last_age_tick()
    assert after == before, f"age_tick نباید حرکت کند: {before}→{after}"


def t_unified_replay_from_ledger():
    """replay از ledger برمی‌گردد. eventهای publishشده دیده می‌شوند."""
    from unified_bus import UnifiedBus
    lg = _fresh_ledger()
    bus = UnifiedBus(ledger=lg)
    bus.publish("NOTE", {"n": 1}, actor="test")
    bus.publish("NOTE", {"n": 2}, actor="test")
    events = bus.replay(event_type="NOTE")
    assert len(events) == 2, f"باید ۲ event باشد: {len(events)}"


def t_unified_non_destructive_old_path_works():
    """NON-DESTRUCTIVE: ledger.append مستقیم (مسیرِ قدیمی) هنوز کار می‌کند.
    publish = مسیرِ جدیدِ توصیه‌شده، نه جایگزین."""
    from unified_bus import UnifiedBus
    lg = _fresh_ledger()
    # مسیرِ قدیمی: مستقیم ledger.append
    lg.append("NOTE", {"via": "direct"}, actor="legacy")
    # مسیرِ جدید: unified bus
    bus = UnifiedBus(ledger=lg)
    bus.publish("OBSERVE", {"via": "bus"}, actor="bus")
    # هر دو دیده می‌شوند — هیچ delete
    legacy = [e for e in lg.filter(event_type="NOTE")]
    new = [e for e in lg.filter(event_type="OBSERVE")]
    assert len(legacy) == 1 and len(new) == 1


# ════════════════════════════════════════════════════════════════════════════════
# S-4 · checkpoint / replay
# ════════════════════════════════════════════════════════════════════════════════

def t_checkpoint_writes_to_chrono():
    """checkpoint در chrono.db می‌نویسد (اگر db باشد)."""
    import chrono
    sys.path.insert(0, str(ENV["genome"] / "ledger"))
    from ledger import Ledger
    import checkpoint as ckpt
    lg = Ledger(ENV["genome"] / "ledger" / f"ckpt-{os.getpid()}.jsonl")
    db = chrono.ChronoDB(ENV["ops"] / "state" / f"ckpt-{os.getpid()}.db")
    try:
        ok = ckpt.checkpoint(beat=1, hlc=(100, 0), ledger_hash="abc123", db=db,
                             snapshot={"legs": {}})
        assert ok is True
        row = db.q("SELECT ledger_hash FROM checkpoint WHERE beat_id=1")
        assert row and row[0][0] == "abc123"
    finally:
        db.close()


def t_checkpoint_no_db_returns_false():
    """db=None → False (fail-soft، ولی ledger source of truth است)."""
    import checkpoint as ckpt
    ok = ckpt.checkpoint(beat=1, hlc=(1, 0), ledger_hash="x", db=None)
    assert ok is False


def t_replay_returns_events():
    """replay از ledger events برمی‌گرداند."""
    from unified_bus import UnifiedBus
    lg = _fresh_ledger()
    bus = UnifiedBus(ledger=lg)
    bus.publish("NOTE", {"i": 1}, actor="t")
    bus.publish("NOTE", {"i": 2}, actor="t")
    import checkpoint as ckpt
    events = ckpt.replay(ledger=lg, event_type="NOTE")
    assert len(events) == 2


def t_replay_state_within_5s():
    """بازسازیِ state <۵s (DoD S-4)."""
    from unified_bus import UnifiedBus
    lg = _fresh_ledger()
    bus = UnifiedBus(ledger=lg)
    for i in range(100):
        bus.publish("NOTE", {"i": i}, actor="t")
    import checkpoint as ckpt
    result = ckpt.replay_state_at(ledger=lg)
    assert result["within_5s"] is True, f"replay باید <5s: {result['replay_seconds']}"
    assert result["events_count"] == 100


# ════════════════════════════════════════════════════════════════════════════════
# S-6 · smoke 24h
# ════════════════════════════════════════════════════════════════════════════════

def t_smoke_returns_checks():
    """smoke_24h.run_checks لیستِ چک‌ها برمی‌گرداند."""
    import smoke_24h
    result = smoke_24h.run_checks(state_dir=ENV["ops"] / "state")
    assert "checks" in result and "pass" in result
    assert len(result["checks"]) >= 5   # حداقل ۶ چک
    names = [c["name"] for c in result["checks"]]
    assert "state-fresh" in names and "ledger-verify" in names


def t_smoke_each_check_has_verdict():
    """هر چک ok/detail دارد."""
    import smoke_24h
    result = smoke_24h.run_checks(state_dir=ENV["ops"] / "state")
    for c in result["checks"]:
        assert "ok" in c and "name" in c and "detail" in c, c


if __name__ == "__main__":
    failed = harness.run([
        # S-1 watchdog
        ("[S-1] port مرده + no STOP + prior → revive", t_watchdog_revive_when_dead),
        ("[S-1] STOP → yield (kill-switch مطلق)", t_watchdog_yield_to_stop),
        ("[S-1] port زنده → no revive", t_watchdog_no_revive_if_alive),
        ("[S-1] اولین تولد → no revive (owner-launched)", t_watchdog_no_first_birth),
        ("[S-1] revive_action با STOP → NO-OP", t_watchdog_revive_action_noop_when_stop),
        # S-2/S-5 germline
        ("[S-5] بکاپِ تازه → lag≈0 → ok", t_lag_zero_when_recent),
        ("[S-5] lag>2h → warn", t_lag_warn_over_2h),
        ("[S-5] lag>26h → ERROR", t_lag_error_over_26h),
        ("[S-5] lag>72h → CRIT", t_lag_crit_over_72h),
        ("[S-5] هیچ بکاپی → CRIT", t_lag_crit_when_no_backup),
        ("[S-2] خطا → retry + لاگ (نه بی‌صدا)", t_retry_logs_and_retries),
        ("[S-2] موفقیت در attempt دوم", t_retry_succeeds_on_second),
        ("[S-5] lag_alarm از مسیرها", t_lag_alarm_from_paths),
        # S-3 unified bus
        ("[S-3] publish → ledger + hash", t_unified_publish_to_ledger),
        ("[S-3] is_human → age_tick +۱", t_unified_publish_human_advances_age),
        ("[S-3] non-human → age ثابت", t_unified_publish_non_human_no_age),
        ("[S-3] replay از ledger", t_unified_replay_from_ledger),
        ("[S-3] non-destructive: مسیرِ قدیمی هنوز کار می‌کند", t_unified_non_destructive_old_path_works),
        # S-4 checkpoint/replay
        ("[S-4] checkpoint در chrono", t_checkpoint_writes_to_chrono),
        ("[S-4] db=None → False (fail-soft)", t_checkpoint_no_db_returns_false),
        ("[S-4] replay events", t_replay_returns_events),
        ("[S-4] replay_state <۵s (DoD)", t_replay_state_within_5s),
        # S-6 smoke
        ("[S-6] smoke چک‌ها برمی‌گرداند", t_smoke_returns_checks),
        ("[S-6] هر چک verdict دارد", t_smoke_each_check_has_verdict),
    ])
    sys.exit(1 if failed else 0)
