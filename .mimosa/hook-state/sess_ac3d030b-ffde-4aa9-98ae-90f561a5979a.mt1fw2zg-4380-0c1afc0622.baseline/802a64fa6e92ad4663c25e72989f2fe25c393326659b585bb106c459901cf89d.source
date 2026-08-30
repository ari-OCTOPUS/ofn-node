#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tool_request_sees_its_answers.py — مغز باید پاسخِ خودش را ببیند.

VQ-UNJOINABLE-CONTEXT-001 (۲۰۲۶-۰۸-۰۴). شکایتِ مالک: «حس می‌کنم هنوز کور است».

`_context()` دو فهرستِ **ساختاراً غیرقابلِ‌پیوند** می‌داد:

    «قبلاً_خواسته‌ام»     = [متنِ نیاز]      ← بدونِ شناسه
    «رأی‌های_قبلیِ_مالک» = [(شناسه, رأی)]   ← بدونِ متن

مغز می‌شنید «این هشت چیز را خواسته‌ای» و «این چند شناسه granted شده‌اند» و هیچ
راهی نداشت بفهمد کدام کدام است.

اندازه‌گیریِ زندهٔ ۰۸-۰۴ روی دفترِ واقعی: **۷۲ درخواست، همه `pending`؛ ۸ پاسخ،
همه `granted`**. مالک هشت بار «بله» گفته بود و اختاپوس پاسخِ خودش را نمی‌دید —
پس همان نیاز را شش بار در یک روز تکرار کرد.

⚠️ و رفع عمداً **سرکوب نمی‌کند**: تصمیمِ «دوباره نپرس» مالِ خودِ مغز است. تا
وقتی هیچ کدی یک `granted` را مصرف نمی‌کند، کارتِ تکراری تنها شاهدی است که ✅ ِ
مالک هیچ کاری نکرد — و ساکت‌کردنش آن حقیقت را پنهان می‌کند، نه رفع.
خودِ کد این را صادقانه می‌گوید: «تا وقتی ابزار واقعاً وصل نشود، این فقط یک رأی
است نه یک قابلیت.»
"""
import ast
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("tool-request-context")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops"))
import tool_request as tr  # noqa: E402

HIST = "تاریخچهٔ_درخواست‌ها"
GRANTED = "اینها_را_مالک_قبلاً_تأیید_کرده"


def _seed(rows):
    """دفتر را از خودِ ماژول بگیر، نه دست‌ساز.

    ⚠️ نسخهٔ اول `tr._ledger()` را صدا زد به گمانِ اینکه مسیر برمی‌گرداند —
    ولی آن تابعِ **نوشتن** است و آرگومان می‌خواهد. چهار تست با
    `TypeError` قرمز شدند. ثابتِ درست `tr.LEDGER` است."""
    path = Path(tr.LEDGER)
    assert str(harness.REAL_VAULT).lower() not in str(path).lower(), (
        "دفترِ تست داخلِ درختِ زنده افتاد — harness ایزوله نکرده", str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path.write_text(body, encoding="utf-8")
    return path


def t_a_the_history_joins_need_to_verdict():
    """قلبِ گارد: نیاز و رأی باید در **یک** عنصر باشند، نه دو فهرست."""
    _seed([
        {"schema": tr.SCHEMA, "request_id": "r1", "need": "دسترسی به شل", "ts": 1},
        {"schema": tr.SCHEMA, "request_id": "r2", "need": "دسترسی به دیسک", "ts": 2},
        {"schema": tr.SCHEMA + ".answer", "request_id": "r1", "verdict": "granted", "ts": 3},
    ])
    ctx = tr._context()
    h = ctx.get(HIST)
    assert h, ("تاریخچهٔ پیوسته وجود ندارد — مغز نمی‌تواند نیاز را به رأی وصل کند", list(ctx))
    by_need = {x["نیاز"]: x["رأیِ مالک"] for x in h}
    assert by_need.get("دسترسی به شل") == "granted", by_need
    assert by_need.get("دسترسی به دیسک") == "بی‌پاسخ", by_need


def t_b_granted_needs_are_surfaced_explicitly():
    """بندِ صریح، چون همین گم‌شدنش باعثِ تکرار می‌شد."""
    _seed([
        {"schema": tr.SCHEMA, "request_id": "r1", "need": "ابزارِ الف", "ts": 1},
        {"schema": tr.SCHEMA + ".answer", "request_id": "r1", "verdict": "granted", "ts": 2},
    ])
    ctx = tr._context()
    g = ctx.get(GRANTED)
    assert g and "ابزارِ الف" in g[0], (
        "نیازِ تأییدشده صریح به مغز گفته نمی‌شود", ctx.get(GRANTED))


def t_c_a_denied_need_is_not_reported_as_granted():
    _seed([
        {"schema": tr.SCHEMA, "request_id": "r1", "need": "ابزارِ ب", "ts": 1},
        {"schema": tr.SCHEMA + ".answer", "request_id": "r1", "verdict": "denied", "ts": 2},
    ])
    ctx = tr._context()
    assert not ctx.get(GRANTED), ("رأیِ منفی به‌عنوان تأیید گزارش شد", ctx.get(GRANTED))
    assert ctx[HIST][0]["رأیِ مالک"] == "denied"


def t_d_the_context_never_suppresses_a_request():
    """⚠️ ناوردیِ ضدِ «رفعی که سکوت بسازد». این تابع فقط **اطلاعات** می‌دهد؛
    اگر روزی خودش تصمیم بگیرد چیزی را حذف کند، تنها شاهدِ اینکه ✅ ِ مالک هیچ
    کاری نکرد از بین می‌رود."""
    src = Path(tr.__file__).read_text("utf-8", errors="replace")
    fn = next((n for n in ast.walk(ast.parse(src))
               if isinstance(n, ast.FunctionDef) and n.name == "_context"), None)
    assert fn is not None
    seg = ast.get_source_segment(src, fn) or ""
    for banned in ("return None", "raise ", "skip", "suppress"):
        assert banned not in seg, (
            f"«{banned}» در _context — این تابع نباید تصمیم بگیرد، فقط اطلاع بدهد")


def t_e_it_still_works_on_an_empty_ledger():
    _seed([])
    ctx = tr._context()
    assert HIST not in ctx and GRANTED not in ctx, ctx


def t_f_this_test_only_reads_the_live_tree():
    src = Path(__file__).read_text("utf-8")
    assert "REAL_VAULT" in src
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in ("unlink", "rmtree"):
            raise AssertionError("این تست چیزی حذف نمی‌کند")


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t(); passed += 1; print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__); print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_tool_request_sees_its_answers: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
