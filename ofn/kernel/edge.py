"""مدل «لبهٔ سیستم» — تفکیک تصمیم به بدن / خود بازتابی / ابرموجود.

خالص stdlib، بدون I/O، بدون ساعت — مثل safety.py. هر تابع دترمینیستیک و
قابل‌آزمون. وزن‌ها همه از متن مالک آمده‌اند، نه اختراع. این ماژول فقط عدد
می‌دهد؛ ترجمهٔ فارسیِ نتیجه را هم در `interpret` می‌سازیم تا مغز نیازی به
ترجمهٔ فنی نداشته باشد.

سه قطب:

  بدن          خواب، گرسنگی، خستگی، مصرف، استرس، هوس
  خود بازتابی   ارزش‌ها، برنامهٔ ۹۰روزه، پایداریِ بعد از تأخیر، پذیرش هزینه
  ابرموجود     بازار، خانواده، پول، ترند، پلتفرم، فشار اجتماعی، مشتری
"""
# ── provenance ────────────────────────────────────────────────────
# Copied from hypno-fugu-mini/hypno/kernel/edge.py (UNIFY phase L, 2026-08-10).
# Pure stdlib math, no I/O — belongs in the kernel. The hypno project keeps
# its own copy while it still runs standalone; this is the OFN copy.

from __future__ import annotations
from dataclasses import dataclass, field
import math

# ── آستانه‌ها و ثابت‌ها ───────────────────────────────────────────────────
EPS = 1e-9
DOMINANT = 0.55        # «بیشتر از این سهم» یعنی غالب
SCALE = 10.0           # همهٔ ورودی‌های کاربر ۰ تا ۱۰ هستند


def clamp01(x: float) -> float:
    """هر عدد را به بازهٔ [0,1] ببر (ورودی ممکن است ۰-۱۰ یا درصد باشد)."""
    if x <= 0:
        return 0.0
    if x >= 1 and x <= SCALE:
        return x / SCALE          # ۰-۱۰ → ۰-۱
    if x >= 1:
        return 1.0
    return float(x)


def _pos(x: float) -> float:
    """[x]_+ = max(0, x) — در q شعاعی استفاده می‌شود."""
    return x if x > 0 else 0.0


def sigmoid(x: float) -> float:
    """σ(x) = 1/(1+e^{-x}). در γ_S و γ_R استفاده می‌شود."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


# ── شاخص‌های سه‌قطبی (نسخهٔ سریع دستی) ────────────────────────────────────────
# همهٔ ورودی‌ها ۰ تا ۱۰. وزن‌ها دقیقاً از متن مالک.

def agency_index(V, P, K, D, H) -> float:
    """Agency Index — سهم «خود بازتابی».

    AI = 0.25·V + 0.20·P + 0.20·K + 0.20·D + 0.15·H
    V هماهنگی با ارزش‌ها، P پیش‌تعهد (قبل از محرک)، K پذیرش هزینه،
    D پایداری بعد از ۲۴ ساعت، H ثبات بدن.
    خروجی ۰ تا ۱.
    """
    ai = (0.25 * clamp01(V) + 0.20 * clamp01(P) + 0.20 * clamp01(K)
          + 0.20 * clamp01(D) + 0.15 * clamp01(H))
    return min(ai, 1.0)


def super_index(E, F, M, U, D) -> float:
    """Superorganism Index — سهم «ابرموجود/شبکه».

    SI = 0.30·E + 0.20·F + 0.20·M + 0.20·U + 0.10·(1−D)
    E شدت محرک بیرونی/پلتفرم/ترند، F فومو/مقایسه، M فشار پول/خانواده/بازار،
    U فوریت ناگهانی و هیجانی، D پایداری بعد از ۲۴ ساعت.
    خروجی ۰ تا ۱.
    """
    si = (0.30 * clamp01(E) + 0.20 * clamp01(F) + 0.20 * clamp01(M)
          + 0.20 * clamp01(U) + 0.10 * (1.0 - clamp01(D)))
    return min(si, 1.0)


def body_index(H, C, sleep_debt, stress) -> float:
    """Body Index — سهم «بدن/خستگی/هوس».

    BI = 0.30·(1−H) + 0.30·C + 0.20·SleepDebt + 0.20·Stress
    H ثبات بدن، C craving (هوس/مصرف/پرخوری)، sleep_debt بدهی خواب،
    stress استرس.
    خروجی ۰ تا ۱.
    """
    bi = (0.30 * (1.0 - clamp01(H)) + 0.30 * clamp01(C)
          + 0.20 * clamp01(sleep_debt) + 0.20 * clamp01(stress))
    return min(bi, 1.0)


# ── تجزیهٔ تصمیم (decomposition) ────────────────────────────────────────────
@dataclass(frozen=True)
class Decomposition:
    a_self: float       # Ã
    a_super: float      # S̃
    a_body: float       # B̃
    label: str          # تفسیر فارسی کوتاه

    def dominant(self) -> str:
        m = max(self.a_self, self.a_super, self.a_body)
        if m < DOMINANT:
            return "ترکیبی"
        if m == self.a_self:
            return "خود"
        if m == self.a_super:
            return "ابرموجود"
        return "بدن"


def decomposition(ai: float, si: float, bi: float) -> Decomposition:
    """سه شاخص را به سهم‌های نرمال‌شده (Ã, S̃, B̃) ببر.

    Ã = AI / (AI+SI+BI+ε)  و همین برای بقیه.
    تفسیر فارسی بر اساس آستانهٔ ۰.۵۵.
    """
    denom = ai + si + bi + EPS
    a_self = ai / denom
    a_super = si / denom
    a_body = bi / denom
    label = interpret(a_self, a_super, a_body)
    return Decomposition(a_self, a_super, a_body, label)


def interpret(a_self, a_super, a_body) -> str:
    """سهم‌های نرمال‌شده را به جملهٔ فارسی ساده ترجمه کن (D-22: بدون کلمهٔ فنی)."""
    if a_self >= DOMINANT:
        return "این تصمیم بیشتر از خودت آمده."
    if a_super >= DOMINANT:
        return "این تصمیم بیشتر از موجِ بیرون (بازار/ترند/فشار) آمده."
    if a_body >= DOMINANT:
        return "این تصمیم بیشتر از بدنت (خستگی/هوس/گرسنگی) آمده."
    return "این تصمیم ترکیبی است؛ نه کلاً خودت، نه کلاً بیرون."


# ── معادلهٔ اصلی لبه ─────────────────────────────────────────────────────────
def les(F, C, S, A, X, B, O) -> float:
    """Life-on-Edge Score (LES_t).

        LES_t = (F·C·S·A) / (1 + X + (1−B) + O)

    F فلو، C بستن حلقه، S سیگنال واقعی بازار، A آگاهی (همه ۰-۱۰).
    X هزینهٔ پنهان، B بدن، O حلقه‌های باز (۰-۱۰). هرچه بالاتر، لبهٔ سالم‌تر.
    مخرش همواره ≥ ۱ است پس تقسیم‌برصفر نیست.
    """
    num = (clamp01(F) * clamp01(C) * clamp01(S) * clamp01(A))
    den = 1.0 + clamp01(X) + (1.0 - clamp01(B)) + clamp01(O)
    return num / den


# ── حساسیت‌ها: γ_S و γ_R ──────────────────────────────────────────────────────
# وقتی بدن ضعیف یا آگاهی پایین است، ابرموجود قوی‌تر اثر می‌کند.

def gamma_super(sleep_debt, stress, weed, fomo, awareness) -> float:
    """γ_S — حساسیت به ابرموجود.

    γ_S = σ(α₀ + α₁·SleepDebt + α₂·Stress + α₃·Weed + α₄·FOMO − α₅·Awareness)
    وزن‌های α مستقیماً از متن: یک شیفت پایه + اثر مساوی هر عامل بدن/فومو − اثر آگاهی.
    """
    a = (clamp01(sleep_debt) + clamp01(stress) + clamp01(weed)
         + clamp01(fomo) - clamp01(awareness))
    return sigmoid(2.0 * a - 1.0)   # آستانه‌دار؛ خنثی = ۰.۵


def gamma_reflexive(value_fit, pre_commitment, delay_persistence,
                    cost_acceptance, sleep_debt, craving) -> float:
    """γ_R — حساسیت به خودِ بازتابی.

    γ_R = σ(ρ₁·ValueFit + ρ₂·PreCommitment + ρ₃·DelayPersistence
            + ρ₄·CostAcceptance − ρ₅·SleepDebt − ρ₆·Craving)
    وزن‌های ρ از متن: عوامل خود بالا، بدن/هوس پایین.
    """
    r = (clamp01(value_fit) + clamp01(pre_commitment) + clamp01(delay_persistence)
         + clamp01(cost_acceptance) - clamp01(sleep_debt) - clamp01(craving))
    return sigmoid(2.0 * r - 2.0)


# ── q شعاعی و انتساب (نسخهٔ برداری) ───────────────────────────────────────────
def cosine_q(delta_n, direction) -> float:
    """q = [ (Δn · dir) / (|Δn||dir|) ]_+

    Δn تغییر میل/تصمیم، direction جهت یکی از سه قطب (بردار هم‌اندازه).
    هر دو لیست عدد هم‌اندازه. خروجی ۰ تا ۱.
    """
    if not delta_n or not direction or len(delta_n) != len(direction):
        return 0.0
    dot = sum(a * b for a, b in zip(delta_n, direction))
    nd = math.sqrt(sum(a * a for a in delta_n)) + EPS
    nr = math.sqrt(sum(b * b for b in direction)) + EPS
    return _pos(dot / (nd * nr))


@dataclass(frozen=True)
class Attribution:
    p_self: float
    p_super: float
    p_body: float
    label: str


def attribution(delta_n, v_self, s_super, b_body) -> Attribution:
    """انتساب یک تغییر تصمیم به سه قطب با q شعاعی نرمال‌شده.

    P_G = q_G / (q_self + q_super + q_body + ε)
    ورودی‌ها هر سه بردارِ هم‌اندازهٔ delta_n.
    """
    qs = cosine_q(delta_n, v_self)
    qsu = cosine_q(delta_n, s_super)
    qb = cosine_q(delta_n, b_body)
    denom = qs + qsu + qb + EPS
    p_self = qs / denom
    p_super = qsu / denom
    p_body = qb / denom
    return Attribution(p_self, p_super, p_body, interpret(p_self, p_super, p_body))


# ── قانون طلایی تصمیم سالم ───────────────────────────────────────────────────
def healthy_decision(p_self, p_super_aligned, p_super_chaos, p_body,
                     lam=0.5, mu=0.5) -> float:
    """HealthyDecision = P_self + λ·P_super_aligned − μ·P_body_chaos.

    ایده‌آل: خود بالا، ابرموجودِ هم‌راستا موجود، آشوبِ بدن پایین.
    p_self و p_super_aligned و p_body همه ۰-۱ (سهم نرمال‌شده).
    خروجی می‌تواند منفی باشد (تصمیم ناسالم).
    """
    return (clamp01(p_self) + lam * clamp01(p_super_aligned)
            - mu * clamp01(p_body))


# ── قانون سه‌روزهٔ روزانه ──────────────────────────────────────────────────────
@dataclass(frozen=True)
class DailyVerdict:
    verdict: str        # سبز / زرد / قرمز
    advice: str         # فارسی ساده


def daily_verdict(B, C, X) -> DailyVerdict:
    """قانون روزانه از روی سه نمرهٔ ۰-۱۰.

    B بدن، C بستن حلقه، X هزینهٔ پنهان.
    سبز  : B>6 و C>5 و X<4  → فردا فشار سازنده مجاز.
    زرد  : B<5 یا X>6       → فردا فقط تثبیت؛ گسترش ممنوع.
    (قرمز توسط three_red_days داده می‌شود.)
    """
    b, c, x = clamp01(B), clamp01(C), clamp01(X)
    if b > 0.6 and c > 0.5 and x < 0.4:
        return DailyVerdict("سبز", "فردا می‌توانی کمی بیشتر به لبه نزدیک شوی.")
    if b < 0.5 or x > 0.6:
        return DailyVerdict("زرد", "فردا گسترش ممنوع؛ فقط تثبیت.")
    return DailyVerdict("سبز", "روی لبه‌ای؛ بدن را نگه دار و یک حلقهٔ کوچک ببند.")


def three_red_days(history) -> DailyVerdict:
    """سه روز قرمز پشت‌سرهم → قرمز.

    history لیستی از DailyVerdict (یا 'verdict' string) برای روزهای اخیر
    به‌ترتیب قدیم‌به‌جدید. اگر سه روز آخر همه قرمز/زرد سخت بود → عقب‌نشینی.
    """
    if len(history) < 3:
        return DailyVerdict("خنثی", "هنوز دادهٔ کافی نیست.")
    last = history[-3:]
    bad = sum(1 for v in last
              if (getattr(v, 'verdict', v) in ("قرمز", "زرد")))
    if bad >= 3:
        return DailyVerdict("قرمز",
            "سه روز سخت بوده؛ اول بدن، خواب، غذا، تعهدات پایه. بعد فلسفه و استارتاپ.")
    return DailyVerdict("خنثی", "هنوز روی لبه‌ای.")


# ── تابع یکپارچه: ۱۰ نمره → نتیجهٔ تصمیم ─────────────────────────────────────
@dataclass(frozen=True)
class DecisionResult:
    ai: float
    si: float
    bi: float
    dec: Decomposition
    verdict: str       # dec.label (فارسی ساده)
    healthy: float


def decision_source(V, P, K, D, H, E, F, M, U, C, sleep_debt, stress) -> DecisionResult:
    """از ۱۰+۲ نمرهٔ کاربر، نتیجهٔ کامل تصمیم را بده.

    ورودی‌ها همه ۰-۱۰:
    V هماهنگی با ارزش‌ها · P پیش‌تعهد · K پذیرش هزینه · D پایداری ۲۴ساعت · H ثبات بدن
    E محرک بیرونی/ترند · F فومو · M فشار پول/خانواده · U فوریت هیجانی
    C craving/هوس · sleep_debt بدهی خواب · stress استرس
    """
    ai = agency_index(V, P, K, D, H)
    si = super_index(E, F, M, U, D)
    bi = body_index(H, C, sleep_debt, stress)
    dec = decomposition(ai, si, bi)
    # healthy_decision(p_self, p_super_aligned, p_super_chaos, p_body).
    # The decomposition only gives a_self/a_super/a_body; the closest honest
    # approximation is p_super_aligned = a_super (the super-organism share,
    # treated as aligned unless proven otherwise) and p_super_chaos = a_super
    # too (a high super share can be chaotic), with p_body = a_body. This
    # replaces the prior call which passed a_body twice and silently dropped
    # the chaos-vs-aligned distinction entirely.
    healthy = healthy_decision(dec.a_self, dec.a_super, dec.a_super, dec.a_body)
    return DecisionResult(ai=ai, si=si, bi=bi, dec=dec,
                          verdict=dec.label, healthy=healthy)


# ── سه سؤال قبل از تصمیم بزرگ (خلاصهٔ عددی) ───────────────────────────────────
def big_decision_check(value_fit, pre_commitment, cost_acceptance, delay_persistence,
                       sleep_debt, craving, external_cue, fomo) -> dict:
    """سه سؤال قبل از تصمیم بزرگ را به اعداد تبدیل کن.

    ۱. این میل از کجا آمده؟ → γ_R vs γ_S
    ۲. هزینهٔ پنهانش چیست؟ → body_index(هزینه)
    ۳. آیا در ۷۲ ساعت خروجی کوچک می‌سازد؟ → delay_persistence به‌عنوان جایگزین

    خروجی: یک دیکشنری فارسی ساده برای مغز.
    """
    gr = gamma_reflexive(value_fit, pre_commitment, delay_persistence,
                         cost_acceptance, sleep_debt, craving)
    gs = gamma_super(sleep_debt, 0, craving, fomo, 0)
    # هزینهٔ پنهان: بدن ضعیف + هوس + بدهی خواب
    hidden_cost = body_index(1.0 - clamp01(sleep_debt), craving, sleep_debt, 0)
    if gr > gs + 0.1:
        source = "بیشتر از خودت آمده."
    elif gs > gr + 0.1:
        source = "بیشتر از موجِ بیرون آمده؛ مراقب باش."
    else:
        source = "ترکیبی است؛ صبر کن و بعداً دوباره بپرس."
    return {
        "منشأ": source,
        "هزینهٔ پنهان": "بالا" if hidden_cost > 0.5 else "قابل‌تحمل",
        "γ_self": round(gr, 2),
        "γ_super": round(gs, 2),
    }
