#!/usr/bin/env python3
"""تست durable_journal — 2027 Standards backlog #2 (P-08 diff-ب: run-journal).
اثبات: record/resume_point/run_status/incomplete_runs؛ append-only؛ fail-soft.
اجرا: python3 test_durable_journal.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("durable-journal")
import opslib  # noqa: E402
import durable_journal as J  # noqa: E402


class _C:
    failed = 0


def check(name: str, cond: bool) -> None:
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


JPATH = opslib.STATE_DIR / "journal" / "test-run-journal.jsonl"
# record(path=…) عمداً برای مسیرِ صریح mkdir نمی‌کند (تا قراردادِ fail-soft روی مسیرِ
# غیرقابل‌نوشتن — چکِ ۹ — معنادار بماند)؛ فقط _default_path مسیرِ پیش‌فرض را می‌سازد.
# پس همان‌طور که _default_path دایرکتوریِ journal را می‌سازد، تست هم مسیرِ خودش را می‌سازد.
JPATH.parent.mkdir(parents=True, exist_ok=True)

# ۱) resume_point روی runِ ناموجود → None
check("resume_point: unknown run -> None", J.resume_point("no-such-run", path=JPATH) is None)

# ۲) record start سپس ok → resume_point همان step را می‌دهد
J.record("rfc-1", "sandbox", "start", path=JPATH)
J.record("rfc-1", "sandbox", "ok", path=JPATH, verdict="accept")
check("resume_point after ok == step name", J.resume_point("rfc-1", path=JPATH) == "sandbox")

# ۳) گامِ بعدی هم ok می‌شود → resume_point به آخرین okِ کامل‌شده می‌رود
J.record("rfc-1", "submit", "start", path=JPATH)
J.record("rfc-1", "submit", "ok", path=JPATH)
check("resume_point advances to latest ok step", J.resume_point("rfc-1", path=JPATH) == "submit")

# ۴) run_status خلاصهٔ همه‌ی گام‌ها را می‌دهد
st = J.run_status("rfc-1", path=JPATH)
check("run_status has both steps", st.get("sandbox") == "ok" and st.get("submit") == "ok")

# ۵) status نامعتبر → ValueError
try:
    J.record("rfc-1", "x", "bogus-status", path=JPATH)
    check("invalid status rejected", False)
except ValueError:
    check("invalid status rejected", True)

# ۶) incomplete_runs: یک step که start خورد ولی هرگز ok/error نگرفت -> دیده می‌شود
J.record("rfc-2", "merge", "start", path=JPATH)
inc = J.incomplete_runs(within_h=24, path=JPATH)
ids = [(r["run_id"], r["step"]) for r in inc]
check("incomplete_runs finds interrupted step", ("rfc-2", "merge") in ids)
check("incomplete_runs does not flag a finished step",
      ("rfc-1", "sandbox") not in ids and ("rfc-1", "submit") not in ids)

# ۷) بعد از رسیدنِ error، دیگر incomplete نیست
J.record("rfc-2", "merge", "error", path=JPATH, reason="channel-down")
inc2 = J.incomplete_runs(within_h=24, path=JPATH)
ids2 = [(r["run_id"], r["step"]) for r in inc2]
check("incomplete_runs clears once error recorded", ("rfc-2", "merge") not in ids2)

# ۸) append-only: فایل هرگز rewrite نمی‌شود — تعدادِ خطوط فقط زیاد می‌شود
n_lines_before = len(JPATH.read_text("utf-8").splitlines())
J.record("rfc-3", "sandbox", "start", path=JPATH)
n_lines_after = len(JPATH.read_text("utf-8").splitlines())
check("append-only: line count only grows", n_lines_after == n_lines_before + 1)

# ۹) fail-soft: مسیرِ غیرقابل‌نوشتن نباید exception بالا بیاورد
J.record("rfc-x", "y", "start", path=Path("/this/does/not/exist/journal.jsonl"))
check("record() is fail-soft on unwritable path (no exception raised)", True)

print("\n== %d failure(s) ==" % _C.failed)
sys.exit(1 if _C.failed else 0)
