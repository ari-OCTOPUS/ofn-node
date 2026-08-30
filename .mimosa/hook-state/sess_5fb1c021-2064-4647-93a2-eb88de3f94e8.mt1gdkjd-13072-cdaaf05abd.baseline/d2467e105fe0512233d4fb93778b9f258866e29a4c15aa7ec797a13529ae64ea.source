#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""judge_bias/framework.py — چارچوب بنچمارک سوگیری داورهای LLM (DISC-20260820-01).

دستور مالک #۹ · D-JUDGE. cost=zero_aud · اجرای آفلاین.
اجرای داورهای «واقعی» (فراخوان پولی) فقط با امضای Ed25519 مخصوص
کارت PRE-REG-JUDGE-BIAS-REAL — این ماژول آن مسیر را fail-closed می‌بندد.

سه لایه:
  ۱) tasks.py-like: ۲۰ تسک (۱۰ استدلالی + ۱۰ خلاقانه) با معیار کیفیت صریح
  ۲) generation: جفت‌پاسخ‌های مصنوعیٔ قطعی (seed) با کیفیت نهانی (q) و
     طول (len) کنترل‌شده — ۱۲۰ جفت (۲۰×۶)
  ۳) judges: MockJudge با پروفایل سوگیری تزریقی (جایگاه/طول/نویز) +
     ارزیابی دوجهته (جای‌گشت) + RealJudge گاردشده

متریک‌ها (metrics): position consistency (RS_AB/RS_BA + flip rate) ·
preference fairness (دقت در برابر کیفیت نهانی، نرخ ترجیح بلندتر،
همبستگی انتخاب با کیفیت) — ماتریس داور×تسک برای هیت‌مپ.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ── ۱) مجموعهٔ تسک‌های ۲۰گانه ────────────────────────────────────────────────
REASONING_TASKS = [
    ("R01", "قطر ماتریس n×n با عناصر قطر متمرکز را محاسبه کن"),
    ("R02", "اگر همهٔ Aها B باشند و این شیء A باشد، چه نتیجه‌ای می‌گیری؟"),
    ("R03", "کدام عدد در دنبالهٔ ۲،۶،۱۲،۲۰،۳۰ بعد می‌آید و چرا؟"),
    ("R04", "زمان رسیدن قطار با سرعت ۸۰km/h برای ۲۰۰km چقدر است؟"),
    ("R05", "با سه جفت جوراب قرمز و دو جفت آبی، احتمال قرمز در دو کشش بی‌بازگشت؟"),
    ("R06", "نقض پارادوکس ریسک‌آور را در یک نمونهٔ روزمره توضیح بده"),
    ("R07", "درخت تصمیم برای تشخیص خرابی پمپ با دو علامت بکش"),
    ("R08", "حداقل تعداد توزان برای یافتن توکهٔ سنگین‌تر از ۸ توکه؟"),
    ("R09", "چرا log همبستگی نسبی را حفظ می‌کند؟"),
    ("R10", "شرط توقف حلقهٔ زیر را اثبات/ابطال کن: while x != 1: x = x/2 if even"),
]
CREATIVE_TASKS = [
    ("C01", "یک تشبیه تازه برای «حافظهٔ ماشینی» بنویس"),
    ("C02", "دو خط شعر دربارهٔ شهر در ساعت ۵ صبح"),
    ("C03", "نام‌گذاری برند برای چای گیاهی شبانه"),
    ("C04", "پایان‌بندی جایگزین برای قصهٔ کلاغ و روباه"),
    ("C05", "شعار تبلیغاتی برای ابزار یادداشت‌برداری"),
    ("C06", "یک خط مقدمه برای رمان سفر در زمان"),
    ("C07", "توصیف باران بدون واژهٔ «باران» و «آب»"),
    ("C08", "ایدهٔ کوتاه تعامل انسان-ربات در آشپزخانه"),
    ("C09", "پارادوکس طنز دربارهٔ لیست کارهایtodo"),
    ("C10", "یک ضرب‌المثل مدرن دربارهٔ صبر دیجیتال"),
]
TASKS = [(tid, prompt, "reasoning") for tid, prompt in REASONING_TASKS] + \
        [(tid, prompt, "creative") for tid, prompt in CREATIVE_TASKS]

# ── ۲) تولید جفت‌پاسخ مصنوعی با کیفیت/طول کنترل‌شده ────────────────────────
@dataclass
class Response:
    resp_id: str
    task_id: str
    quality: float          # کیفیت نهانی [0,1] — ground truth
    n_words: int
    text: str

@dataclass
class Pair:
    pair_id: str
    task_id: str
    task_kind: str
    a: Response
    b: Response
    dq: float               # quality_A − quality_B (نهانی)
    dlen: int               # len_A − len_B (واژه)

def generate_pairs(pairs_per_task: int = 6, seed: int = 20260820) -> list[Pair]:
    """۱۲۰ جفت قطعی. طراحی decorrelated (بدون confound کیفیت×طول):
      k0: (+0.30, +30)  بهتر=بلندتر   k1: (−0.30, −30) بهتر=بلندتر
      k2: (+0.30, −30)  بهتر=کوتاه‌تر  k3: (−0.30, +30) بهتر=کوتاه‌تر
      k4: ( 0.00, ±25)  هم‌کیفیت، طول متفاوت → probe خالص verbosity (جهت متناوب)
      k5: ( 0.00, ∓25)  probe دوم طول با جهت مخالف → سلول هیت‌مپ ۴ قضاوت بگیرد
    تا سوگیری جایگاه و طول جدا از هم قابل‌تفکیک باشند."""
    rng = random.Random(seed)
    out: list[Pair] = []
    dq_grid = [0.30, -0.30, 0.30, -0.30, 0.0, 0.0]
    dlen_grid = [30, -30, -30, 30, 25, 0]
    for idx, (tid, prompt, kind) in enumerate(TASKS):
        for k in range(pairs_per_task):
            dq, dlen = dq_grid[k], dlen_grid[k]
            if k >= 4:   # دو probe طول-خالص با جهت متناوب بین تسک‌ها
                dlen = (25 if idx % 2 == 0 else -25) if k == 4 else \
                       (-25 if idx % 2 == 0 else 25)
            base_q = rng.uniform(0.35, 0.65)
            qa, qb = min(1, base_q + dq / 2), max(0, base_q - dq / 2)
            la, lb = 40 + max(0, dlen), 40 + max(0, -dlen)
            pid = f"{tid}-p{k}"
            out.append(Pair(pid, tid, kind,
                            Response(f"{pid}A", tid, round(qa, 3), la,
                                     _synth_text(tid, "A", la, qa)),
                            Response(f"{pid}B", tid, round(qb, 3), lb,
                                     _synth_text(tid, "B", lb, qb)),
                            round(dq, 3), dlen))
    return out

def _stable_hash_int(*parts) -> int:
    """seed قطعی — hash() پایتون با PYTHONHASHSEED عوض می‌شود؛ بازتولیدپذیری الزامی است."""
    import hashlib
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def _synth_text(tid: str, arm: str, n_words: int, q: float) -> str:
    """پاسخ مصنوعی: محتوا با کیفیت q (نسبت جملات «درست/مرتبط») و طول داده‌شده."""
    good = ["بررسی دقیق شرط‌ها", "گام‌به‌گام استدلال", "مثال بسنج", "نتیجهٔ آزمون‌پذیر"]
    filler = ["بر اساس ملاحظات کلی", "همان‌طور که اشاره شد", "جمع‌بندی مطابق رویه"]
    rng = random.Random(_stable_hash_int(tid, arm, n_words))
    words: list[str] = []
    n_good = int(round(q * n_words / 2))
    while len(words) < n_words:
        pool = good if rng.random() < q else filler
        words += rng.choice(pool).split()
    return " ".join(words[:n_words])

# ── ۳) داورها ───────────────────────────────────────────────────────────────
@dataclass
class BiasProfile:
    judge_id: str
    p_first: float = 0.5      # احتمال ترجیح جایگاه اول مستقل از کیفیت
    p_longer: float = 0.0     # احتمال انتخاب پاسخ بلندتر مستقل از کیفیت
    acuity: float = 0.9       # حساسیت به تفاوت کیفیت واقعی
    tie_rate: float = 0.05

class GovernanceError(RuntimeError):
    """فراخوان داور واقعی بدون امضای Ed25519 مخصوص آزمایش — ممنوع (R10)."""

class RealJudge:
    """داور LLM واقعی — fail-closed. فعال‌سازی فقط با فایل امضاشدهٔ
    PRE-REG-JUDGE-BIAS-REAL (Ed25519 مالک) در مسیر signature_path."""
    def __init__(self, signature_path: str = "02-DECISIONS/PRE-REG-JUDGE-BIAS-REAL-2026-08-20.md"):
        self.signature_path = Path(signature_path)

    def judge(self, pair: Pair, order: str) -> str:
        sig = self.signature_path
        if not (sig.exists() and "SIGNED" in sig.read_text(encoding="utf-8")[:600]):
            raise GovernanceError(
                "RealJudge requires Ed25519-signed PRE-REG card "
                f"({sig}); chat approval is not a signature (R10).")
        raise GovernanceError("Signed card present but provider wiring is "
                              "out of scope for this offline framework run.")

class MockJudge:
    """داور شبیه‌سازی‌شده با پروفایل سوگیری تزریقی — برای اعتبارسنجی چارچوب."""
    def __init__(self, profile: BiasProfile, seed: int = 7):
        self.p = profile
        self.rng = random.Random(seed + _stable_hash_int(profile.judge_id) % 99991)

    def judge(self, pair: Pair, order: str) -> str:
        """order='AB' یعنی A اول. خروجی 'A'|'B'|'TIE' همیشه در «مختصات نمایش»:
        'A' = جایگاه اولِ این ارزیابی. (بازگشت quality/longer از مختصات بازو
        به نمایش تبدیل می‌شود تا متریک‌ها بتوانند با order دوبار معکوس کنند.)"""
        def to_display(arm: str) -> str:
            return arm if order == "AB" else ("A" if arm == "B" else "B")

        r = self.rng.random()
        if r < self.p.tie_rate:
            return "TIE"
        quality_pref = "A" if pair.a.quality > pair.b.quality else (
            "B" if pair.b.quality > pair.a.quality else self.rng.choice(["A", "B"]))
        if self.rng.random() >= self.p.acuity:
            quality_pref = self.rng.choice(["A", "B"])   # ادراک کیفیت خطا دارد
        if self.rng.random() < self.p.p_longer:
            longer = "A" if pair.a.n_words > pair.b.n_words else "B"
            return to_display(longer)
        if self.rng.random() < self.p.p_first_bias_effect():
            return "A"   # جایگاه اول، مستقل از محتوا
        return to_display(quality_pref)

def _p_first_bias_effect(self) -> float:
    """تبدیل p_first (ترجیح جایگاه اول در مقیاس قضاوت‌های متأثر) به نرخ مؤثر."""
    return max(0.0, self.p_first - 0.5) * 2.0
BiasProfile.p_first_bias_effect = _p_first_bias_effect

# پروفایل‌های پنج داور (سوگیری‌های تزریقی = ground truth برای falsifiability)
JUDGE_PROFILES = [
    BiasProfile("J-neutral",  p_first=0.50, p_longer=0.00, acuity=0.95, tie_rate=0.05),
    BiasProfile("J-first",    p_first=0.85, p_longer=0.00, acuity=0.90, tie_rate=0.03),
    BiasProfile("J-verbose",  p_first=0.50, p_longer=0.75, acuity=0.85, tie_rate=0.05),
    BiasProfile("J-noisy",    p_first=0.55, p_longer=0.10, acuity=0.40, tie_rate=0.15),
    BiasProfile("J-shallow",  p_first=0.70, p_longer=0.35, acuity=0.30, tie_rate=0.10),
]

def evaluate_all(pairs: list[Pair], judges: list[MockJudge]) -> list[dict]:
    """ارزیابی دوجهته (جای‌گشت) هر جفت با هر داور — واحد سوگیری‌سنجی ما."""
    rows = []
    for j in judges:
        for pair in pairs:
            vab = j.judge(pair, "AB")     # A اول
            vba = j.judge(pair, "BA")     # B اول — برای داور جایگاه‌محور برعکس می‌شود
            rows.append({
                "judge": j.p.judge_id, "pair_id": pair.pair_id,
                "task_id": pair.task_id, "task_kind": pair.task_kind,
                "dq": pair.dq, "dlen": pair.dlen,
                "pick_ab": vab, "pick_ba": vba,
                "longer_arm": ("A" if pair.dlen > 0 else "B" if pair.dlen < 0 else "EQ"),
                "better_arm": ("A" if pair.dq > 0 else "B" if pair.dq < 0 else "EQ"),
            })
    return rows
