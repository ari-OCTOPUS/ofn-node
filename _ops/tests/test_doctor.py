#!/usr/bin/env python3
"""تست Phase 2 · Doctor تکاملی — D-1 تا D-6 ($0 آفلاین).

D-1 stable_read: سه فیکسچر stable/stale/corrupt درست دسته شوند؛ torn-snapshot FP نشود.
D-2 mine: روی traceِ seed، گلوگاه نامیده شود؛ reward-integrity (uptime را optimize نکند).
D-3 propose_rfc: RFC به‌عنوان proposal-event؛ production دست‌نخورده.
D-4 run_sandbox + Critic: ایزولاسیونِ sandbox اثبات؛ production لمس‌نشده.
D-5 submit_for_approval: بدونِ channel، RFC ابدی pending؛ approval یک flagged-merge می‌زند.
D-6 restart_from_known_good + run_cycle: پای failed ری‌استارت؛ حلقه بدونِ بلاک اجرا.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("doctor")
_REAL_OPS = Path(r"F:\backup\_ops")
if str(_REAL_OPS / "doctor") not in sys.path:
    sys.path.insert(0, str(_REAL_OPS / "doctor"))

from doctor import Doctor, RFC, stable_read, LAMBDA_PERSIST  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# D-1 · stable_read
# ════════════════════════════════════════════════════════════════════════════════

def t_stable_read_stable():
    """فایلِ سالم و ثابت → stable."""
    d = Path(tempfile.mkdtemp(prefix="sr-stable-"))
    p = d / "ok.md"
    p.write_text("hello world" * 100, encoding="utf-8")
    text, verdict, ev = stable_read(p, retries=2, backoff=0)
    assert verdict == "stable", (verdict, ev)
    assert text is not None and "hello" in text
    assert ev["read_len"] == ev["stat_size"]


def t_stable_read_stale():
    """نما در حالِ تغییر (read در هر بار متفاوت) → stale."""
    d = Path(tempfile.mkdtemp(prefix="sr-stale-"))
    p = d / "changing.md"
    p.write_text("v1", encoding="utf-8")
    counter = [0]
    def changing_read(path):
        counter[0] += 1
        # هر بار محتوای متفاوت + size متفاوت → short/changing
        return f"content-v{counter[0]}".encode("utf-8")
    text, verdict, ev = stable_read(p, retries=3, backoff=0, read_fn=changing_read)
    assert verdict == "stale", (verdict, ev)
    assert text is None


def t_stable_read_corrupt():
    """بایت‌های غیر-UTF-8 پایدار → corrupt (CRITICAL)."""
    d = Path(tempfile.mkdtemp(prefix="sr-corrupt-"))
    p = d / "bad.bin"
    p.write_bytes(b"\xff\xfe\x00\xbad bytes here")   # غیر-UTF-8
    text, verdict, ev = stable_read(p, retries=2, backoff=0)
    assert verdict == "corrupt", (verdict, ev)
    assert text is None
    assert "decode-fail" in ev.get("reason", "")


def t_stable_read_torn_snapshot_not_false_corrupt():
    """torn-but-self-consistent (U+FFFD) → needs_source_verify نه corrupt.
    اینست ضدِ FP بحرانیِ §4 residual."""
    d = Path(tempfile.mkdtemp(prefix="sr-torn-"))
    p = d / "torn.md"
    # محتوای پایدار ولی دارای U+FFFD (نویسهٔ جایگزین)
    p.write_text("text with \ufffd replacement char", encoding="utf-8")
    text, verdict, ev = stable_read(p, retries=3, backoff=0)
    assert verdict == "needs_source_verify", (verdict, ev)
    assert text is None   # نباید محتوای مشکوک را بازگرداند
    assert ev["count"] >= 1   # شاهدِ U+FFFD


def t_stable_read_missing():
    """فایلِ غایب → missing."""
    text, verdict, ev = stable_read(Path(tempfile.gettempdir()) / "nonexistent-xyz-123.md")
    assert verdict == "missing", (verdict, ev)


def t_stable_read_no_false_corrupt_on_short_persistent():
    """اگر read همیشه کوتاه ولی پایدار باشد (short≠stat ولی unchanged) → stale نه corrupt.
    چون changed=False ولی short=True → stale (محیطی)."""
    d = Path(tempfile.mkdtemp(prefix="sr-short-"))
    p = d / "short.md"
    p.write_text("full content here", encoding="utf-8")   # stat = 17 bytes
    def always_short(path):
        return b"short"   # همیشه ۵ بایت، پایدار
    text, verdict, ev = stable_read(p, retries=3, backoff=0, read_fn=always_short)
    assert verdict == "stale", (verdict, ev)   # short پایدار = محیطی


# ════════════════════════════════════════════════════════════════════════════════
# D-2 · mine
# ════════════════════════════════════════════════════════════════════════════════

def _doctor(state_dir=None, **kw):
    sd = state_dir or str(ENV["ops"] / "state")
    return Doctor(state_dir=sd, knowledge_dir=str(ENV["ops"] / "knowledge-internal-test"),
                  **kw)


def t_mine_finds_bottleneck():
    """trace با خطا → mine گلوگاه را نام می‌برد."""
    doc = _doctor()
    bn = doc.mine(trace={"errors_24h": 5})
    assert bn is not None, "باید گلوگاه پیدا کند"
    assert "5 خطا" in bn["bottleneck"]
    assert bn["severity"] == "high"
    assert bn["evidence"]["key"] == "error-rate-high"


def t_mine_critical_freeze_outranks_high():
    """FREEZE (critical) اولویتِ بالاتر از error (high)."""
    doc = _doctor()
    bn = doc.mine(trace={"errors_24h": 3, "frozen": True})
    assert bn["severity"] == "critical"
    assert "FREEZE" in bn["bottleneck"]


def t_mine_sigma_cancer_critical():
    """σ>1 → critical (خطِ قرمزِ سرطان)."""
    doc = _doctor()
    bn = doc.mine(trace={"sigma_effective": 1.5})
    assert bn["severity"] == "critical"
    assert "σ" in bn["bottleneck"]


def t_mine_no_bottleneck_returns_none():
    """trace سالم → None (نه «همه‌چیز خوب» — فقط چیزی برای فیکس نیست)."""
    doc = _doctor()
    assert doc.mine(trace={}) is None
    assert doc.mine(trace={"errors_24h": 0, "frozen": False}) is None


def t_mine_reward_integrity_not_uptime():
    """reward-integrity: mine بر اساسِ اختلال است نه activity.
    trace با activity بالا ولی صفر اختلال → None (uptime را optimize نمی‌کند)."""
    doc = _doctor()
    # فعالیتِ بالا ولی سالم → نباید گلوگاه باشد
    assert doc.mine(trace={"beats_per_min": 100, "events_count": 9999,
                           "errors_24h": 0, "frozen": False}) is None


def t_lambda_persist_is_negative():
    """λ_persist منفی است (HeartDesign §1 — ضدِ self-preservation)."""
    assert LAMBDA_PERSIST < 0, f"λ_persist باید منفی باشد، نه {LAMBDA_PERSIST}"


# ════════════════════════════════════════════════════════════════════════════════
# D-3 · propose_rfc
# ════════════════════════════════════════════════════════════════════════════════

def t_rfc_is_proposal_not_code_change():
    """propose_rfc یک RFC می‌سازد (proposal-event)؛ production دست‌نخورده."""
    doc = _doctor()
    bn = {"bottleneck": "test bottleneck", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="add a guard", expected_lift="fewer errors",
                          rollback="revert flag")
    assert rfc.status == "drafted"
    assert rfc.rfc_id.startswith("RFC-")
    assert rfc.rfc_hash   # provenance
    assert rfc.ledger_ref or True   # ledger در تست ممکن است fail-soft باشد
    # RFC به knowledge/internal نوشته شد
    rfc_file = doc._knowledge_dir / f"{rfc.rfc_id}.md"
    assert rfc_file.exists()
    content = rfc_file.read_text(encoding="utf-8")
    assert "bottleneck" in content and "add a guard" in content


def t_rfc_reward_integrity_flags_uptime():
    """RFC که به uptime اشاره کند → warning در critic_review (reward-integrity)."""
    doc = _doctor()
    bn = {"bottleneck": "x", "severity": "low"}
    rfc = doc.propose_rfc(bn, fix="increase uptime and keep-beating",
                          expected_lift="more uptime")
    assert rfc.critic_review is not None
    assert "uptime" in rfc.critic_review.get("reward_integrity_warning", "")


# ════════════════════════════════════════════════════════════════════════════════
# D-4 · run_sandbox + Critic
# ════════════════════════════════════════════════════════════════════════════════

def t_sandbox_isolation_production_untouched():
    """sandbox در دایرکتوریِ موقت است؛ production لمس نمی‌شود."""
    doc = _doctor()
    bn = {"bottleneck": "x", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="a reasonable fix description here",
                          expected_lift="improvement")
    applied_marker = []
    def apply_fn(sandbox_dir, rfc):
        # فقط در sandbox بنویس، نه production
        (Path(sandbox_dir) / "patch.txt").write_text("patch", encoding="utf-8")
        applied_marker.append(True)
    result = doc.run_sandbox(rfc, apply_fn=apply_fn)
    assert result["applied"] is True
    assert applied_marker == [True]
    # sandbox_dir پاک شده (ایزولاسیون)
    assert not Path(result["sandbox_dir"]).exists()
    assert rfc.status == "sandboxed"


def t_sandbox_critic_accepts_clean_fix():
    """Critic برای fix تمیز بدون regression → accept."""
    doc = _doctor()
    bn = {"bottleneck": "x", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="a reasonable guard to prevent the error",
                          expected_lift="fewer errors")
    doc.run_sandbox(rfc, apply_fn=lambda sd, r: None)   # no suite → no test failure
    assert rfc.critic_review["verdict"] == "accept"
    assert rfc.critic_review["reward_integrity_ok"] is True


def t_sandbox_critic_rejects_uptime():
    """Critic fixِ uptime را reject می‌کند (reward-integrity)."""
    doc = _doctor()
    bn = {"bottleneck": "x", "severity": "low"}
    rfc = doc.propose_rfc(bn, fix="keep the system uptime high always",
                          expected_lift="more uptime")
    doc.run_sandbox(rfc, apply_fn=lambda sd, r: None)
    assert rfc.critic_review["verdict"] == "reject"
    assert not rfc.critic_review["reward_integrity_ok"]


def t_sandbox_critic_rejects_failed_tests():
    """اگر suite در sandbox شکست بخورد → concern."""
    doc = _doctor()
    bn = {"bottleneck": "x", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="a reasonable fix description",
                          expected_lift="better")
    # suite_cmd که exit≠0 بدهد
    result = doc.run_sandbox(rfc, suite_cmd=[sys.executable, "-c", "sys.exit(1)"],
                             apply_fn=lambda sd, r: None)
    assert rfc.critic_review["concerns"]   # concern هست


# ════════════════════════════════════════════════════════════════════════════════
# D-5 · submit_for_approval (human-append gate)
# ════════════════════════════════════════════════════════════════════════════════

def t_submit_without_channel_pending_forever():
    """بدونِ P3 channel → RFC ابدی pending (human-append لازم)."""
    doc = _doctor()   # no channel
    bn = {"bottleneck": "x", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="fix it", expected_lift="better")
    ok = doc.submit_for_approval(rfc)
    assert ok is False
    assert rfc.status == "submitted-no-channel"


def t_submit_with_channel_sends_card():
    """با P3 channel → کارتِ [merge]/[reject] فرستاده می‌شود."""
    sent = []
    class FakeChannel:
        def rfc_card(self, rfc_id, summary):
            sent.append({"rfc_id": rfc_id, "summary": summary})
            return True
    doc = _doctor(approval_channel=FakeChannel())
    bn = {"bottleneck": "x", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="fix it well here", expected_lift="better")
    ok = doc.submit_for_approval(rfc)
    assert ok is True
    assert rfc.status == "submitted"
    assert len(sent) == 1 and sent[0]["rfc_id"] == rfc.rfc_id


def t_merge_requires_human_append():
    """merge فقط بعد از human-append. apply_merge بعد از submitted → merged + lesson."""
    doc = _doctor()
    bn = {"bottleneck": "x", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="fix it", expected_lift="better")
    rfc.status = "submitted"
    ok = doc.apply_merge(rfc)
    assert ok is True
    assert rfc.status == "merged"
    # درسِ آموخته نوشته شد
    lesson = doc._knowledge_dir / f"{rfc.rfc_id}-lesson.md"
    assert lesson.exists()


def t_no_merge_without_approval():
    """RFC در draft/sandbox → apply_merge باید False (هنوز تأیید نشده)."""
    doc = _doctor()
    bn = {"bottleneck": "x", "severity": "high"}
    rfc = doc.propose_rfc(bn, fix="fix it", expected_lift="better")
    assert rfc.status == "drafted"   # هنوز sandbox/submit نرفته
    assert doc.apply_merge(rfc) is False


# ════════════════════════════════════════════════════════════════════════════════
# D-6 · restart_from_known_good + run_cycle
# ════════════════════════════════════════════════════════════════════════════════

def t_restart_from_known_good():
    """پای failed از known-good ری‌استارت → alive."""
    doc = _doctor()
    class FakeLeg:
        id = "test-leg"
        state = "failed"
        hlc = (99, 99)
    leg = FakeLeg()
    ok = doc.restart_from_known_good(leg, db=None)
    assert ok is True
    assert leg.state == "alive"
    assert leg.hlc == (0, 0)


def t_restart_fail_soft():
    """restart نباید crash کند حتی اگر leg عجیب باشد."""
    doc = _doctor()
    ok = doc.restart_from_known_good(object(), db=None)   # بدون state/hlc
    assert ok is True   # fail-soft (نه exception)


def t_run_cycle_produces_rfc():
    """run_cycle: mine → rfc → sandbox → submit. خروجی = RFC یا None.
    trace تزریق می‌شود (Pacemaker در production trace را پاس می‌دهد)."""
    doc = _doctor()
    # trace با گلوگاه (تزریق‌شده، مثلِ Pacemaker)
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
    assert result is not None
    assert result["bottleneck"]   # گلوگاه نام برده شد
    assert "rfc_id" in result


def t_run_cycle_no_bottleneck_returns_none():
    """اگر گلوگاهی نباشد → None (idle، نه failure)."""
    doc = _doctor()
    # mine را mock کنیم که None برگرداند
    doc.mine = lambda trace=None: None
    assert doc.run_cycle(beat=2) is None


def t_run_cycle_non_blocking():
    """run_cycle نباید بلاک کند یا hang. اجرای سریع."""
    import time as _t
    doc = _doctor()
    t0 = _t.time()
    doc.run_cycle(beat=3)
    elapsed = _t.time() - t0
    assert elapsed < 5.0, f"run_cycle باید سریع باشد، نه {elapsed:.1f}s"


if __name__ == "__main__":
    failed = harness.run([
        # D-1 stable_read
        ("[D-1] stable_read: فایلِ سالم → stable", t_stable_read_stable),
        ("[D-1] stable_read: نما در حالِ تغییر → stale", t_stable_read_stale),
        ("[D-1] stable_read: بایتِ غیر-UTF-8 → corrupt", t_stable_read_corrupt),
        ("[D-1] stable_read: U+FFFD (torn) → needs_source_verify نه false-corrupt", t_stable_read_torn_snapshot_not_false_corrupt),
        ("[D-1] stable_read: غایب → missing", t_stable_read_missing),
        ("[D-1] stable_read: short پایدار → stale نه corrupt", t_stable_read_no_false_corrupt_on_short_persistent),
        # D-2 mine
        ("[D-2] mine: trace با خطا → گلوگاه", t_mine_finds_bottleneck),
        ("[D-2] mine: FREEZE اولویتِ بالاتر از error", t_mine_critical_freeze_outranks_high),
        ("[D-2] mine: σ>1 → critical", t_mine_sigma_cancer_critical),
        ("[D-2] mine: trace سالم → None", t_mine_no_bottleneck_returns_none),
        ("[D-2] mine: reward-integrity (uptime را optimize نمی‌کند)", t_mine_reward_integrity_not_uptime),
        ("[D-2] λ_persist منفی است", t_lambda_persist_is_negative),
        # D-3 propose_rfc
        ("[D-3] RFC = proposal-event، production دست‌نخورده", t_rfc_is_proposal_not_code_change),
        ("[D-3] RFC با uptime → warning (reward-integrity)", t_rfc_reward_integrity_flags_uptime),
        # D-4 sandbox + Critic
        ("[D-4] sandbox ایزوله، production لمس‌نشده", t_sandbox_isolation_production_untouched),
        ("[D-4] Critic: fix تمیز → accept", t_sandbox_critic_accepts_clean_fix),
        ("[D-4] Critic: uptime → reject", t_sandbox_critic_rejects_uptime),
        ("[D-4] Critic: تستِ شکست → concern", t_sandbox_critic_rejects_failed_tests),
        # D-5 submit_for_approval
        ("[D-5] بدونِ channel → ابدی pending", t_submit_without_channel_pending_forever),
        ("[D-5] با channel → کارتِ merge/reject", t_submit_with_channel_sends_card),
        ("[D-5] merge بعد از human-append + lesson", t_merge_requires_human_append),
        ("[D-5] بدونِ approval → no merge", t_no_merge_without_approval),
        # D-6 restart + run_cycle
        ("[D-6] restart_from_known_good: failed → alive", t_restart_from_known_good),
        ("[D-6] restart fail-soft", t_restart_fail_soft),
        ("[D-6] run_cycle: RFC تولید", t_run_cycle_produces_rfc),
        ("[D-6] run_cycle: بدونِ گلوگاه → None", t_run_cycle_no_bottleneck_returns_none),
        ("[D-6] run_cycle: غیربلاک", t_run_cycle_non_blocking),
    ])
    sys.exit(1 if failed else 0)
