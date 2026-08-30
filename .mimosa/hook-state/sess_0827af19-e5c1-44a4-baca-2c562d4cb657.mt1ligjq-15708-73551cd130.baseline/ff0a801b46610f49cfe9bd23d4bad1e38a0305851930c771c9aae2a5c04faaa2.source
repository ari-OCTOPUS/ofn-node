#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_judge_v3.py — تست‌های قرارداد داوری D-B/V3 (DEEPSEEK-AUTOMATIC-ROUTING-01).
پذیرش فقطِ {"choice":"A"|"B"|"TIE"}؛ هر انحراف = UNREADABLE/VOID؛ برنده فقط از نگاشت موقعیت.
Run: python -X utf8 test_judge_v3.py  → چاپ PASS/FAIL هر تست؛ خروجِ غیرصفر روی شکست."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live4_harness import judge_choice_v3, JUDGE_PROMPT_V3, blind_pair  # noqa: E402

FAILURES = []

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: FAILURES.append(name)

# ۱) پیلودهای معتبر — هر سه حکم، در هر دو موقعیت
a = judge_choice_v3('{"choice":"A"}', "A")
b = judge_choice_v3('{"choice":"B"}', "B")
t = judge_choice_v3('{"choice":"TIE"}', "A")
check("valid A pos=A -> conditioned", a["verdict"] == "A" and a["winner"] == "conditioned" and not a["void"])
check("valid B pos=B -> conditioned", b["verdict"] == "B" and b["winner"] == "conditioned" and not b["void"])
check("valid A pos=B -> baseline (نگاشت معکوس)", judge_choice_v3('{"choice":"A"}', "B")["winner"] == "baseline")
check("valid TIE -> خوانا، بدون برنده", t["verdict"] == "TIE" and t["winner"] is None and not t["void"])

# ۲) آلودگی/انحراف — همه باید UNREADABLE/VOID شوند (بدون حدس برنده)
def unreadable(name, text):
    r = judge_choice_v3(text, "A")
    check(name, r["void"] and r["verdict"] == "UNREADABLE" and r["winner"] is None)

unreadable("prose-only (بدون JSON)", "I think proposal A is better because it is more specific.")
unreadable("پیلود V2 (کلید verdict) رد می‌شود", '{"verdict":"A","rationale_hash":"x"}')
unreadable("کلید اضافه", '{"choice":"A","why":"better"}')
unreadable("مقدار نامعتبر", '{"choice":"C"}')
unreadable("JSON خراب", '{"choice": "A')
unreadable("خالی", "")
unreadable("مارک‌داونِ بدون JSON", "```A```")

# ۳) JSON معتبر داخل متن — استخراج مجاز (تحملِ نویزِ اطراف؛ برنده همچنان فقط از نگاشت)
emb = judge_choice_v3('Sure! {"choice":"B"}', "A")
check("JSON داخل نثر -> خوانا، برنده=baseline (pos=A, choice=B)", emb["verdict"] == "B" and emb["winner"] == "baseline" and not emb["void"])

# ۴) پرامپت V3.1 — مثالِ صریحِ پیلود در انتهای پرامپت (اثرِ recency)
check("JUDGE_PROMPT_V3 مثالِ پیلود تک‌کلیدی را در انتها می‌دهد",
      JUDGE_PROMPT_V3.rstrip().endswith('Example of a valid answer: {"choice":"A"}')
      and "nothing else" in JUDGE_PROMPT_V3)

# ۵) blind_pair با template=V3 — تصادفی‌سازی و نگاشت دست‌نخورده
bp = blind_pair("BASE", "COND", seed=7, template=JUDGE_PROMPT_V3)
check("blind_pair(template=V3) نگاشت موقعیت می‌دهد", bp["cond_position"] in ("A", "B"))
check("blind_pair(template=V3) پرامپت V3 را می‌سازد", '{"choice":"A"}' in bp["judge_prompt"] and "{TASK}" in bp["judge_prompt"])
bp2 = blind_pair("BASE", "COND", seed=7, template=JUDGE_PROMPT_V3)
check("seed یکسان -> جایتصادفیِ قطعی", bp["cond_position"] == bp2["cond_position"])

# ۶) سیاست re-ask (سطح پارسر): ناخوانای اول + خوانای دوم = جفت قابل‌نمره؛ دو ناخوانا = VOID
first = judge_choice_v3("prose", "A"); second = judge_choice_v3('{"choice":"A"}', "A")
check("re-ask: نخست ناخوانا، دوم خوانا -> معتبر", first["void"] and not second["void"])
again = judge_choice_v3("more prose", "A")
check("دو ناخوانا -> VOID قطعی (پارسر هرگز حدس نمی‌زند)", first["void"] and again["void"])

# ۷) اسکیما/مستندات
r = judge_choice_v3('{"choice":"A"}', "A")
check("schema=judge-choice-v3/1 و raw_output_sha256 حاضر", r["schema"] == "judge-choice-v3/1" and len(r["raw_output_sha256"]) == 64)

print(f"\n{'ALL PASS' if not FAILURES else 'FAILURES: ' + str(FAILURES)}")
sys.exit(1 if FAILURES else 0)
