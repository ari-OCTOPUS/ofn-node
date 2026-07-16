"""test_autonomy_matrix.py — ماتریسِ ردهٔ خودمختاری (رأی مالک 2026-07-16 19:30).

اثبات: ردهٔ مهم (پول/کد/secret/حذف/ارسال/kill/PII) هرگز آزاد نمی‌شود حتی با فلگ؛
غیرمهم با فلگِ روشن خودتصمیم (self) می‌شود نه سوال از مالک؛ فلگِ خاموش = رفتارِ
قبلی بایت‌به‌بایت (escalate)؛ هر خودتصمیم در ledger و لاگ ثبت می‌شود.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("autonomy-matrix")

import autonomy_matrix as am   # noqa: E402
import auto_approve as aa      # noqa: E402
import improve                 # noqa: E402
import opslib                  # noqa: E402

FLAG = am.FLAG


def _p(title, action, level="tune"):
    return {"title": title, "action": action, "change_level": level, "auto_ok": True}


def _flag(on):
    if on:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


def t_a_important_never_freed():
    """پول/کد/secret/حذف/ارسال/kill/پارتنر → مهم؛ و با فلگِ روشن هم escalate."""
    _flag(True)
    try:
        for kw in ("پولِ بیشتری خرج کن", "این فایل را حذف کن", "delete stale rows",
                   "ایمیل به مشتری بفرست", "publish the report", "kill the daemon",
                   "api_key را عوض کن", "دادهٔ پارتنر را بخوان", "restart organism"):
            imp, why = am.is_important(_p(kw, kw))
            assert imp, f"باید مهم باشد: {kw}"
            d = aa.decide(_p(kw, kw))
            assert d["action"] == "escalate", f"مهم باید escalate بماند: {kw} → {d}"
        assert am.is_important(_p("x", "y", "code"))[0]      # هر code = مهم
    finally:
        _flag(False)


def t_b_benign_not_important():
    for kw in ("کادنسِ نمونه‌برداری را نرم کن", "گزارشِ داخلیِ سلامت بساز",
               "دسته‌بندیِ تراکنش‌های صفِ مرور را مرتب کن", "cache برای extractorها"):
        imp, _ = am.is_important(_p(kw, kw))
        assert not imp, f"نباید مهم باشد: {kw}"


def t_c_flag_off_regression_escalate():
    """فلگ خاموش → دقیقاً رفتارِ قبلی: غیرknob به مالک escalate."""
    _flag(False)
    d = aa.decide(_p("گزارشِ داخلیِ سلامت بساز", "یک نوتِ داخلی"))
    assert d["action"] == "escalate" and "مالک" in d["reason"]


def t_d_flag_on_self_approve_and_logged():
    """فلگ روشن → غیرمهمِ هم‌راستا = self/approve؛ ثبت در ledger و لاگ؛ صفِ مالک خالی."""
    _flag(True)
    try:
        d = aa.decide(_p("گزارشِ داخلیِ سلامت بساز", "یک نوتِ داخلی"))
        assert d["action"] == "self" and d["verdict"] == "approve", d
        res = aa.run([_p("گزارشِ داخلیِ سلامت بساز", "یک نوتِ داخلی")])
        assert res["self_decided"] and not res["escalated"], res
        assert res["permission"] is True                      # فلگ = مجوز
        log = aa.LOG_PATH.read_text("utf-8")
        assert "self-approve" in log
    finally:
        _flag(False)


def t_e_flag_on_misaligned_defers_not_asks():
    """فلگ روشن + ناهم‌راستا با اهداف → self/defer (نه سوال از مالک)."""
    _flag(True)
    try:
        aa.GOALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        aa.GOALS_PATH.write_text("- درآمدِ نقاشی را بالا ببر\n", "utf-8")
        d = aa.decide(_p("بازچینشِ رنگِ داشبورد", "قالبِ ظاهری", "reconfig"))
        assert d["action"] == "self" and d["verdict"] == "defer", d
    finally:
        aa.GOALS_PATH.unlink(missing_ok=True)
        _flag(False)


def t_f_important_keyword_in_action_field():
    """کلیدواژهٔ مهم در فیلدِ action (نه فقط title) هم می‌گیرد."""
    _flag(True)
    try:
        d = aa.decide(_p("بهینه‌سازیِ کوچک", "send invoice to client", "tune"))
        assert d["action"] == "escalate", d
    finally:
        _flag(False)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"PASS test_autonomy_matrix ({len(fns)} tests)")
