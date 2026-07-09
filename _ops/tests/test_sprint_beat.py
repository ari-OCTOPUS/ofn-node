#!/usr/bin/env python3
"""تستِ رفتاریِ P-A5: رفعِ نشتیِ TINV-5 در sprint.py (wall-clock → beat_seq).

گپِ recon: SprintContract بودجهٔ beat را به‌صورتِ deadlineِ ساعتِ دیواری بیان می‌کرد
(`deadline_ts = time.time() + budget_beats*60`) که خلافِ TINV-5 است (هیچ ماژولی
wall-clock مستقیم نمی‌خواند؛ زمان از beat/broadcast می‌آید؛ لازم برای determinism/replay).

این تست اثبات می‌کند:
  (۱) sprint.py دیگر time.time() نمی‌خواند (grep structural).
  (۲) expiry با beat تزریقی کار می‌کند: sprint با deadline_beat=50 → در now_beat=50
      منقضی می‌شود (نه با انتظارِ زمانِ واقعی).
  (۳) fail-soft: اگر now_beat تزریق نشود (0)، sprint فقط با budget شمارشی کار می‌کند.
  (۴) deadline_ts فیلد حذف‌شده است (migration کامل).
$0 آفلاین، stdlib-only.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("sprint-beat")

_NEURAL = Path(r"F:\backup\_ops\neural")
if str(_NEURAL) not in sys.path:
    sys.path.insert(0, str(_NEURAL))

from sprint import SprintContract, SprintRunner, SprintResult  # noqa: E402

SPRINT_SRC = Path(SprintContract.__module__).absolute()
SPRINT_PATH = _NEURAL / "sprint.py"
SPRINT_CODE = SPRINT_PATH.read_text("utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# (۱) TINV-5: sprint.py دیگر time.time() در کد نمی‌خواند
# ════════════════════════════════════════════════════════════════════════════════

def t_no_time_time_call():
    """هیچ فراخوانیِ time.time() در کدِ sprint نباشد (کامنت/docstring مجاز است)."""
    # با tokenize فقط کدِ واقعی (نه string/comment) را بررسی کن
    import tokenize, io
    code_only = []
    with io.BytesIO(SPRINT_CODE.encode("utf-8")) as fb:
        try:
            for tok in tokenize.tokenize(fb.readline):
                if tok.type in (tokenize.STRING, tokenize.COMMENT, tokenize.NL):
                    continue
                code_only.append(tok.string)
        except tokenize.TokenizeError:
            pass
    code = " ".join(code_only)
    # نباید time.time() در کدِ واقعی باشد
    assert not re.search(r"\btime\.time\s*\(", code), \
        "TINV-5 نشتی: sprint.py نباید time.time() صدا بزند"
    # نباید import time هم باشد (در کدِ واقعی)
    assert not re.search(r"import\s+time\b", code), \
        "TINV-5 نشتی: sprint.py نباید `import time` داشته باشد"


def t_no_wall_clock_fields():
    """فیلدهای wall-clock نباید وجود داشته باشند."""
    # deadline_ts حذف شده
    assert "deadline_ts" not in SPRINT_CODE, \
        "deadline_ts (wall-clock field) باید حذف شده باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (۲) expiry با beat تزریقی (نه زمانِ واقعی)
# ════════════════════════════════════════════════════════════════════════════════

def t_expiry_by_injected_beat():
    """sprint با deadline_beat=50 → در now_beat=50 منقضی (False) — بدونِ انتظار."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t1", scope="beat-expiry",
                       budget_beats=100, budget_tokens=1000,
                       start_beat=40, deadline_beat=50)
    runner.start(c)
    # هنوز قبل از deadline → ادامه
    assert runner.tick(now_beat=45) is True, "قبل از deadline باید ادامه دهد"
    # به deadline رسید → منقضی
    assert runner.tick(now_beat=50) is False, "در deadline باید False (منقضی)"
    assert runner.tick(now_beat=51) is False


def t_finish_reports_timeout_by_beat():
    """finish باید timed_out=True را وقتی now_beat از deadline گذشته گزارش کند."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t2", scope="timeout-report",
                       budget_beats=100, budget_tokens=1000,
                       start_beat=10, deadline_beat=20)
    runner.start(c)
    runner.tick(now_beat=15)
    result = runner.finish(now_beat=25)  # بعد از deadline
    assert result.timed_out is True, "timed_out باید True باشد (now_beat > deadline)"
    assert result.completed is False


def t_no_timeout_before_deadline_beat():
    """قبل از deadline_beat → timed_out=False."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t3", scope="no-timeout",
                       budget_beats=100, budget_tokens=1000,
                       start_beat=10, deadline_beat=20)
    runner.start(c)
    runner.tick(now_beat=12)
    result = runner.finish(now_beat=15)  # قبل از deadline
    assert result.timed_out is False
    assert result.completed is True


def t_start_beat_sets_deadline_automatically():
    """اگر فقط start_beat تزریق شود، deadline_beat = start + budget خودکار محاسبه شود."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t4", scope="auto-deadline",
                       budget_beats=10, budget_tokens=1000, start_beat=100)
    assert c.deadline_beat == 110, f"deadline_beat باید 110 باشد، نه {c.deadline_beat}"


def t_start_accepts_injected_beat():
    """start() می‌تواند start_beat را تزریق کند (اگر contract.start_beat صفر باشد)."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t5", scope="inject-start",
                       budget_beats=5, budget_tokens=100)  # start_beat=0
    runner.start(c, start_beat=200)
    assert c.start_beat == 200
    assert c.deadline_beat == 205


# ════════════════════════════════════════════════════════════════════════════════
# (۳) fail-soft: بدونِ تزریقِ beat هم sprint کار می‌کند (فقط شمارشی)
# ════════════════════════════════════════════════════════════════════════════════

def t_fail_soft_no_beat_injected():
    """اگر now_beat تزریق نشود، sprint فقط با budget شمارشی کار می‌کند (fail-soft)."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t6", scope="no-beat",
                       budget_beats=3, budget_tokens=100)
    runner.start(c)
    assert runner.tick() is True   # beat 1
    assert runner.tick() is True   # beat 2
    assert runner.tick() is False  # beat 3 = budget پر شد
    result = runner.finish()  # now_beat تزریق نشد
    # timed_out بر اساسِ شمارشِ داخلی = budget پر شد
    assert result.timed_out is True
    assert result.completed is False


def t_fail_soft_deadline_zero():
    """deadline_beat=0 و start_beat=0 → فقط شمارشِ budget."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t7", scope="zero-deadline",
                       budget_beats=2, budget_tokens=100,
                       start_beat=0, deadline_beat=0)
    runner.start(c)
    assert runner.tick(now_beat=999) is True   # even large now_beat — deadline=0 = غیرفعال
    assert runner.tick(now_beat=9999) is False  # budget پر شد


# ════════════════════════════════════════════════════════════════════════════════
# (۴) رفتارِ منطقیِ موجود حفظ شده: budget_tokens همچنان کار می‌کند
# ════════════════════════════════════════════════════════════════════════════════

def t_token_budget_still_enforced():
    """budget_tokens همچنان sprint را متوقف می‌کند."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t8", scope="token-budget",
                       budget_beats=100, budget_tokens=20)
    runner.start(c)
    runner.tick(tokens=15, now_beat=1)
    cont = runner.tick(tokens=10, now_beat=2)  # 25 > 20
    assert cont is False
    result = runner.finish(now_beat=2)
    assert result.budget_exhausted is True


def t_context_reset_preserved():
    """context_reset بعد از finish همچنان پاک می‌کند."""
    runner = SprintRunner()
    c = SprintContract(sprint_id="t9", scope="reset", context_reset=True)
    runner.start(c)
    runner.tick(insight="x")
    runner.finish()
    assert not runner.is_active  # context پاک شد


if __name__ == "__main__":
    failed = harness.run([
        # (۱) TINV-5 structural
        ("TINV-5: no time.time() call in code", t_no_time_time_call),
        ("TINV-5: no wall-clock fields (deadline_ts gone)", t_no_wall_clock_fields),
        # (۲) expiry by beat
        ("expiry با beat تزریقی (نه زمان واقعی)", t_expiry_by_injected_beat),
        ("finish timed_out بر اساسِ beat", t_finish_reports_timeout_by_beat),
        ("قبل از deadline → no timeout", t_no_timeout_before_deadline_beat),
        ("start_beat → deadline خودکار", t_start_beat_sets_deadline_automatically),
        ("start() تزریقِ start_beat", t_start_accepts_injected_beat),
        # (۳) fail-soft
        ("fail-soft: بدونِ beat، شمارشی کار می‌کند", t_fail_soft_no_beat_injected),
        ("fail-soft: deadline=0 فقط شمارشِ budget", t_fail_soft_deadline_zero),
        # (۴) behavior preserved
        ("budget_tokens همچنان enforced", t_token_budget_still_enforced),
        ("context_reset حفظ شده", t_context_reset_preserved),
    ])
    sys.exit(1 if failed else 0)
