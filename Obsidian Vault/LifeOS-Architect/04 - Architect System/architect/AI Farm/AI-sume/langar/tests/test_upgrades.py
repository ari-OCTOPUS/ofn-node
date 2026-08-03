"""
test_upgrades.py — تستِ ماژول‌های جدید (retrieval, brain_router, ace).

بدونِ pytest اجرا می‌شود:  python3 tests/test_upgrades.py
هر تست یک assert ساده است؛ خروجی شمارشِ pass/fail می‌دهد و در صورتِ شکست exit=1.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.retrieval import HybridRetriever, tokenize, normalize  # noqa: E402
from core.ace import ACELoop, Outcome  # noqa: E402
from brain.brain_router import BrainRouter, classify_depth  # noqa: E402

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ✅ {name}")
    else:
        _failed += 1
        print(f"  ❌ {name}")


# ───────────────────── retrieval ─────────────────────
print("== HybridRetriever ==")

r = HybridRetriever()
r.add(1, "کافئینِ دیروقت کیفیتِ خواب را پایین می‌آورد و RMSSD کم می‌شود", {"domain": "body_hrv"})
r.add(2, "تمرینِ تنفسی صبحگاهی به آرامشِ ذهن کمک می‌کند", {"domain": "mind_emotion"})
r.add(3, "گفتگوی صادقانه با شریک، رابطه را تقویت می‌کند", {"domain": "relationships"})
r.add(4, "caffeine late at night lowers sleep quality", {"domain": "body_hrv"})
r.build()

hits = r.search("کافئین و خواب", k=2)
check("retrieval: نتیجه برمی‌گرداند", len(hits) >= 1)
check("retrieval: مرتبط‌ترین سند اول است (کافئین/خواب)", hits[0].id in (1, 4))
check("retrieval: امتیاز نزولی مرتب است",
      all(hits[i].score >= hits[i + 1].score for i in range(len(hits) - 1)))

hits_en = r.search("caffeine sleep", k=1)
check("retrieval: انگلیسی هم کار می‌کند", hits_en and hits_en[0].id == 4)

check("retrieval: کوئریِ بی‌ربط نتیجه‌ی ضعیف/خالی", len(r.search("کوانتوم فیزیک نسبیت", k=3)) <= 2)
check("normalize: ي/ك عربی نرمال می‌شود", normalize("كيف") == "کیف")
check("tokenize: توقف‌واژه حذف می‌شود", "در" not in tokenize("او در خانه است"))

# corpus خالی نباید crash کند
empty = HybridRetriever().build()
check("retrieval: corpus خالی → []", empty.search("هرچیز") == [])


# ───────────────────── brain_router ─────────────────────
print("== BrainRouter ==")

check("router: سلام ساده → simple", classify_depth("سلام خوبی؟") == "simple")
check("router: جستجو → react", classify_depth("قیمت بیت‌کوین را سرچ کن") == "react")
check("router: بساز/پیاده → plan", classify_depth("یک اسکریپت بساز و پیاده کن") == "plan")
check("router: سرمایه/ریسک → deliberate",
      classify_depth("روی این سهم سرمایه‌گذاری کنم؟ ریسکش چیست") == "deliberate")
check("router: risk=True → deliberate", classify_depth("یک کارِ ساده", risk=True) == "deliberate")

br = BrainRouter(budget=None)
rt = br.route("روی این ترید سرمایه بگذارم؟")
check("router: deliberate → strong + loop", rt.model_tier == "strong" and rt.use_loop)

rt2 = br.route("سلام")
check("router: simple → cheap + بدون loop", rt2.model_tier == "cheap" and not rt2.use_loop)


class _NoBudget:
    def can_spend(self):
        return False


br_poor = BrainRouter(budget=_NoBudget())
rt3 = br_poor.route("روی این ترید سرمایه بگذارم؟")
check("router: بودجه تمام → downgrade", rt3.downgraded and rt3.model_tier == "cheap")

br_offline = BrainRouter(budget=None, allow_strong=False)
rt4 = br_offline.route("یک پروژه‌ی بزرگ طراحی و پیاده کن")
check("router: آفلاین → هرگز strong نیست", rt4.model_tier == "cheap")


# ───────────────────── ACE loop ─────────────────────
print("== ACE loop ==")


class _FakeDB:
    def __init__(self):
        self.saved = []

    def save_improvement_report(self, metrics, suggestions, status="pending"):
        self.saved.append((metrics, suggestions, status))
        return len(self.saved)


# نمونه‌ی کم → reflect نمی‌کند
loop = ACELoop(db=_FakeDB())
res_small = loop.run([Outcome("t", True, "research")], persist=True)
check("ace: نمونه کم → reflect نمی‌کند", res_small["reflection"]["ok"] is False)

# الگوی پرشکست → proposal تولید و pending ذخیره می‌شود
db = _FakeDB()
loop2 = ACELoop(db=db)
outcomes = [
    Outcome("q1", False, "research", error="no_source"),
    Outcome("q2", False, "research", error="no_source"),
    Outcome("q3", False, "research", error="timeout"),
    Outcome("q4", True, "research"),
    Outcome("q5", True, "coach"),
    Outcome("q6", True, "coach"),
]
res = loop2.run(outcomes, persist=True)
check("ace: proposal تولید می‌شود", len(res["proposals"]) >= 1)
check("ace: research به‌خاطرِ نرخِ شکستِ بالا پیشنهاد دارد",
      any(p.label == "research" for p in res["proposals"]))
check("ace: pending در db ذخیره شد", res["saved"] >= 1 and db.saved[0][2] == "pending")
check("ace: هرگز خودکار اعمال نمی‌شود (گاردریل)", res["applied_automatically"] is False)


# ───────────────────── جمع‌بندی ─────────────────────
print(f"\nنتیجه: {_passed} pass / {_failed} fail")
sys.exit(1 if _failed else 0)
