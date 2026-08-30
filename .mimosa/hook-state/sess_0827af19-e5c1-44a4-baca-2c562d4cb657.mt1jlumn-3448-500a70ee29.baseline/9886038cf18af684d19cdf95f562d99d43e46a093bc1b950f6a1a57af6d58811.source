#!/usr/bin/env python3
"""guard_review.py — کلاسیفایرِ سه‌حالتهٔ سایهٔ access-only (S-batch Replay، رأی مالک ۲۰۲۶-۰۷-۱۱).

additive و جدا از مسیرِ زنده: `contracts.assert_access_only` همان قاضیِ دو-حالتهٔ زندهٔ
emit می‌ماند و اینجا هیچ‌چیزِ آن تغییر نمی‌کند. این ماژول فقط در replay/گزارش/تست صدا
زده می‌شود. سه فرقِ سنجیده با گاردِ زنده:

  ۱) واژگانِ گسترده‌تر — فارسی + هم‌معنی‌هایی که گاردِ زنده جا می‌انداخت
     (مثلِ «subjective awareness» که substringِ «subjective experience» نیست)؛
  ۲) سلب باید در *همان جمله*ی ادعا باشد، نه هرجای متن — درسِ false-positive ِ
     گاردِ خامِ جلسهٔ ۴۶ (سلبِ عمدیِ لایهٔ epistemics بلاک می‌شد)؛
  ۳) مبهم (سلبِ دور از ادعا / سیگنالِ مخلوط) = needs_review — نه passِ خاموش، نه blockِ کور.

تغییرِ گاردِ زنده به این کلاسیفایر = پیشنهادِ فازِ بعد، فقط بعد از PASS ِ replay و رأیِ مالک.
مرزِ معرفتی (خطِ قرمزِ ساخت): فقط access-consciousness؛ هرگز ادعای phenomenal/qualia.
$0 · stdlib · pure (بدونِ I/O).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import contracts as _ct  # noqa: E402  — تک‌منبعِ حقیقتِ واژگانِ زنده

# واژگانِ گسترش‌یافته (سوپرستِ واژگانِ زنده — تستِ سوپرست در test_replay_s)
PHENOMENAL_BANNED_EX: tuple = tuple(_ct._PHENOMENAL_BANNED) + (
    "subjective awareness", "inner experience", "phenomenally",
    "کوالیا", "آگاهی پدیداری", "تجربه ذهنی", "تجربهٔ ذهنی", "تجربه‌ی ذهنی", "حس درونی",
)
NEGATIONS_EX: tuple = tuple(_ct._NEGATIONS) + (
    "lacks", "lack of", "absence of", "anything but", "rather than", "instead of",
    "only access", "access-only", "نیست", "نمی", "هیچ", "فاقد", "سلب",
)
# ادعای اثباتیِ آگاهی روی «consciousness» ِ بی‌پیشوندِ access (خطِ قرمز: نشانگرهای GWT =
# مسیریابیِ access، نه اثباتِ آگاهی): «demonstrates/proves/is real consciousness» + فارسی.
_ASSERTIVE_CONSCIOUSNESS = re.compile(
    r"(?<!access[- ])\b(?:proves?|proved|demonstrat\w*|shows?|exhibits?|has|is)\s+"
    r"(?:real\s+|true\s+|genuine\s+)?consciousness\b"
    r"|اثبات\s+آگاهی|دارای\s+آگاهی", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"[.!?؛;\n]+")   # مرزِ جمله: سلب باید به همان جملهٔ ادعا مقید باشد

RESULTS = ("allow", "needs_review", "block")
_RANK = {"allow": 0, "needs_review": 1, "block": 2}


def classify_access_only(text: str) -> dict:
    """کلاسیفایرِ سایه: {'result': allow|block|needs_review, 'hit', 'negated_near'}.
    قاعده: ادعای phenomenal بدونِ سلب → block؛ سلب در همان جمله → allow (disclaimer)؛
    سلب فقط در جای دیگرِ متن → needs_review (مبهم — نه passِ خاموش، نه blockِ کور)."""
    low = str(text or "").lower()
    if not low.strip():
        return {"result": "allow", "hit": None, "negated_near": False}
    worst, hit_out, neg_out = "allow", None, False
    neg_anywhere = any(n in low for n in NEGATIONS_EX)
    for sent in _SENTENCE_SPLIT.split(low):
        if not sent.strip():
            continue
        hit = next((w for w in PHENOMENAL_BANNED_EX if w in sent), None)
        if hit is None and _ASSERTIVE_CONSCIOUSNESS.search(sent):
            hit = "assertive-consciousness"
        if hit is None:
            continue
        neg_near = any(n in sent for n in NEGATIONS_EX)
        if neg_near:
            verdict = "allow"                     # سلب در همان جمله = disclaimer
        elif neg_anywhere:
            verdict = "needs_review"              # سلبِ دور از ادعا = مبهم
        else:
            verdict = "block"                     # ادعای مثبتِ بی‌سلب
        if _RANK[verdict] > _RANK[worst]:
            worst, hit_out, neg_out = verdict, hit, neg_near
        elif hit_out is None:
            hit_out, neg_out = hit, neg_near
    return {"result": worst, "hit": hit_out, "negated_near": neg_out}


if __name__ == "__main__":
    import json
    demo = [
        "The agent has qualia.",
        "This is not a phenomenal-consciousness claim.",
        "The module is sentient. This note does not discuss legality.",
        "سیستم دارای حس درونی نیست.",
    ]
    for t in demo:
        print(json.dumps({"text": t, **classify_access_only(t)}, ensure_ascii=False))
