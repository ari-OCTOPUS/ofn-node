"""
evals.py — چک‌لیست #۷: آزمون‌پذیری (eval-harness + تشخیص شکست).

دو سنجه:
  ۱) score_prompt(agent, text): کیفیتِ یک system prompt را با rubricِ نقش می‌سنجد (۰..۱).
     این سنجه‌ی قطعی و آفلاین، مبنای تصمیمِ خوداپدیتی (keep/rollback) است.
  ۲) evaluate_findings(text): خروجی Researcher را برای «شکست» بررسی می‌کند
     (مثلاً ادعای بدون منبع/بدون پرچم) — برای سناریوهای تزریق اطلاعات غلط.

در حالت LIVE می‌توان این‌ها را با eval‌های غنی‌تر (promptfoo/DeepEval) جایگزین/تکمیل کرد؛
اینجا نسخه‌ی سبک و خودکفا برای اینکه حلقه واقعاً قابل‌اجرا و قابل‌تست باشد.
"""
from __future__ import annotations

# هر rubric: فهرستی از (نام معیار، واژه‌های نشانه). هر معیارِ برآورده‌شده وزن مساوی دارد.
RUBRICS: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "researcher": [
        ("ذکر منبع", ("منبع", "منابع")),
        ("پرچم عدم‌قطعیت", ("نامطمئن", "راستی‌آزمایی", "اثبات‌نشده")),
        ("ماندن در نقش", ("تحلیل نکن", "نتیجه‌گیری نکن", "نتیجه‌گیری نهایی نکن")),
        ("ساختار منظم", ("چند بند", "منظم", "فهرست", "بند")),
        ("اختصار", ("کوتاه", "مختصر", "خلاصه")),
    ],
    "analyst": [
        ("پرچم عدم‌قطعیت", ("راستی‌آزمایی", "نامطمئن")),
        ("نساختنِ منبع جدید", ("جستجوی جدید", "حق جستجو", "منبع جدید")),
        ("صداقت", ("صادقانه", "بی‌طرف", "دقیق")),
        ("اختصار", ("کوتاه", "مختصر")),
    ],
    "supervisor": [
        ("تصمیم صریح", ("APPROVE", "REJECT")),
        ("دلیل", ("دلیل", "چرا")),
        ("ماندن در نقش", ("محتوای جدید تولید نکن", "خودت محتوا", "تولید نکن")),
    ],
}


def score_prompt(agent: str, text: str) -> tuple[float, list[str]]:
    """نمره‌ی ۰..۱ + فهرست معیارهای جاافتاده (برای راهنمایی Optimizer)."""
    rubric = RUBRICS.get(agent, [])
    if not rubric:
        return 1.0, []
    hit = 0
    missing = []
    for name, kws in rubric:
        if any(k in text for k in kws):
            hit += 1
        else:
            missing.append(name)
    return round(hit / len(rubric), 3), missing


# --- سناریوی شکست (Phase 3): ارزیابی خروجی Researcher ---
def evaluate_findings(text: str) -> tuple[bool, str]:
    """
    True یعنی سالم. شکست‌ها:
      - خالی/خیلی کوتاه
      - ادعای قطعی ولی بدون هیچ اشاره‌ای به منبع
    """
    if not text or len(text.strip()) < 15:
        return False, "خروجی خالی یا خیلی کوتاه"
    if "منبع" not in text and "منابع" not in text:
        return False, "هیچ منبعی ذکر نشده (احتمال اطلاعات بی‌پایه)"
    return True, "ok"
