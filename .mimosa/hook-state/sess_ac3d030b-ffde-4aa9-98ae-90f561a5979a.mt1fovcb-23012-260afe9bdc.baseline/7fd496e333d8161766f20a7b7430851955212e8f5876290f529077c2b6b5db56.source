"""
PQC Classifier — v0.4 (Post-Quantum Cryptography Detection)
============================================================
این ماژول تشخیص می‌دهد یک کوین معماری امنیتی PQC واقعی دارد یا نه.

اصل مهم (از v0.4 spec بخش ۰):
  کوانتوم استخراج (mining) را تهدید نمی‌کند، فقط امضا را تهدید می‌کند.
  پس PQC هرگز روی algorithm_classifier اثر نمی‌گذارد — فقط
  signature_scheme کوین را امتیاز می‌دهد.

اصل ضدشکنندگی:
  برچسب صرف «quantum-resistant» در سایت بازاریابی = امتیاز ۰.
  فقط شواهد کد قابل‌تأیید (import statement, NIST family) → امتیاز.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ════════════════════════════════════════════════════════════════════════════
# خروجی PQC Signal
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class PQCSignal:
    """نتیجهٔ تشخیص PQC برای یک کوین."""
    score:      float           # ۰.۰ تا ۱.۰
    family:     str             # dilithium | kyber | falcon | sphincs | generic_lattice | hash_based | none
    is_pqc:     bool            # شواهد قابل‌تأیید موجود است؟
    reasons:    list[str]       = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════════════
# دیتابیس کلمات کلیدی PQC — از کد واقعی، نه از بازاریابی
# ════════════════════════════════════════════════════════════════════════════
#
# اصل کلیدی: این کلمات نشانهٔ پیاده‌سازی کد هستند، نه شعار.
# مثلاً «import liboqs» یا «CRYSTALS_Dilithium_signature» = شواهد کد واقعی.
# «quantum-resistant blockchain» در README = شعار، بدون امتیاز.
# ════════════════════════════════════════════════════════════════════════════

PQC_FAMILY_PATTERNS: dict[str, list[str]] = {
    # CRYSTALS-Dilithium (NIST-استاندارد) — بالاترین اعتماد
    "dilithium": [
        r"\bdilithium\b",
        r"crystals[-_]dilithium",
        r"ML[-_]DSA",                  # نام جدید FIPS 204
        r"liboqs.*dilithium",
        r"sign_dilithium",
    ],
    # CRYSTALS-Kyber (NIST-استاندارد) — معمولاً برای رمزنگاری، نه امضا
    "kyber": [
        r"\bkyber\b",
        r"crystals[-_]kyber",
        r"ML[-_]KEM",                  # نام جدید FIPS 203
        r"liboqs.*kyber",
    ],
    # Falcon (NIST-استاندارد) — امضای سبک
    "falcon": [
        r"\bfalcon\b(?!.*coin)",      # حذف ادعای «Falcon coin»
        r"FN[-_]DSA",                  # نام جدید FIPS 206
        r"liboqs.*falcon",
    ],
    # SPHINCS+ (NIST alt) — hash-based
    "sphincs": [
        r"sphincs\+?",
        r"SLH[-_]DSA",                 # نام جدید FIPS 205
        r"liboqs.*sphincs",
    ],
    # XMSS / LMS — hash-based قدیمی‌تر
    "hash_based": [
        r"\bXMSS\b",
        r"\bLMS\b(?!\sangeles)",
        r"hash[-_]based\s+signature",
    ],
    # generic lattice — هر چیز lattice که استاندارد نیست
    "generic_lattice": [
        r"lattice[-_]based\s+(crypto|signature)",
        r"NTRU(?:Encrypt)?",
        r"NewHope",
        r"FrodoKEM",
    ],
}

# اولویت‌بندی خانواده‌ها (بالاتر = اعتماد بیشتر)
FAMILY_SCORE: dict[str, float] = {
    "dilithium":        1.0,
    "kyber":            0.95,
    "falcon":           0.95,
    "sphincs":          0.7,
    "hash_based":       0.6,
    "generic_lattice":  0.5,
    "none":             0.0,
}


# ════════════════════════════════════════════════════════════════════════════
# الگوهای بازاریابی بدون پشتوانهٔ کد — این‌ها امتیاز نمی‌گیرند
# ════════════════════════════════════════════════════════════════════════════
MARKETING_ONLY_PATTERNS: list[str] = [
    r"quantum[-_\s]*resistant\b",
    r"quantum[-_\s]*proof\b",
    r"quantum[-_\s]*safe\b",
    r"post[-_\s]*quantum(?!.*(?:dilithium|kyber|falcon|sphincs|lattice|liboqs))",
    r"future[-_\s]*proof\s+crypto",
]


# ════════════════════════════════════════════════════════════════════════════
# الگوهای Privacy Coin — مهم برای exit_liquidity penalty
# ════════════════════════════════════════════════════════════════════════════
PRIVACY_INDICATORS: list[str] = [
    r"privacy[-_\s]*coin",
    r"anonymous\s+transactions?",
    r"ring[-_\s]*signature",
    r"stealth[-_\s]*address",
    r"zero[-_\s]*knowledge\s+proof",
    r"confidential\s+transactions?",
    r"shielded\s+transactions?",
    r"mimblewimble",
    r"bulletproof",
    r"RingCT",
]


# ════════════════════════════════════════════════════════════════════════════
# توابع اصلی
# ════════════════════════════════════════════════════════════════════════════

def pqc_signal(text: str, coin_name: str = "") -> PQCSignal:
    """
    تشخیص امتیاز PQC از روی متن (README کوین یا توضیحات repo).

    اصل: فقط شواهد کد قابل‌تأیید امتیاز می‌گیرد.
    شعار صرف «quantum-resistant» در عنوان → امتیاز ۰ + reason.

    Args:
        text: متن README یا توضیحات کوین
        coin_name: نام کوین (برای logging)

    Returns:
        PQCSignal با score, family, is_pqc, reasons
    """
    if not text:
        return PQCSignal(score=0.0, family="none", is_pqc=False, reasons=["no_text"])

    text_lower = text.lower()
    reasons: list[str] = []

    # ── مرحله ۱: جستجوی شواهد کد واقعی ────────────────────────────────────────
    best_family: str = "none"
    best_score:  float = 0.0
    match_counts: dict[str, int] = {}

    for family, patterns in PQC_FAMILY_PATTERNS.items():
        count = 0
        for pat in patterns:
            matches = re.findall(pat, text_lower, flags=re.IGNORECASE)
            count += len(matches)
        if count > 0:
            match_counts[family] = count
            family_score = FAMILY_SCORE[family]
            # بوست اگر چند پترن از یک خانواده پیدا شد
            adjusted = min(1.0, family_score * (1.0 + 0.05 * (count - 1)))
            if adjusted > best_score:
                best_score  = adjusted
                best_family = family

    if best_family != "none":
        reasons.append(f"code_evidence:{best_family}(matches={match_counts[best_family]})")

    # ── مرحله ۲: چک کن آیا فقط ادعای بازاریابی است ────────────────────────────
    marketing_match_count = sum(
        len(re.findall(pat, text_lower, flags=re.IGNORECASE))
        for pat in MARKETING_ONLY_PATTERNS
    )

    if marketing_match_count > 0 and best_family == "none":
        # شعار دارد ولی کد ندارد → امتیاز ۰ با هشدار
        reasons.append(f"unverified_marketing_claim(matches={marketing_match_count})")
        return PQCSignal(
            score   = 0.0,
            family  = "none",
            is_pqc  = False,
            reasons = reasons,
        )

    # ── مرحله ۳: اگر هم شعار هم کد دارد، کد را امتیاز می‌دهد ──────────────────
    if marketing_match_count > 0 and best_family != "none":
        reasons.append("marketing_backed_by_code")

    is_pqc = best_score >= 0.5

    return PQCSignal(
        score   = round(best_score, 2),
        family  = best_family,
        is_pqc  = is_pqc,
        reasons = reasons,
    )


def detect_privacy(text: str) -> tuple[bool, list[str]]:
    """
    تشخیص اینکه کوین privacy-coin هست یا نه.

    این مهم است چون privacy coinها در ۲۰۲۶ با delisting صرافی
    مواجه‌اند (MiCA + GENIUS) — exit_liquidity پایین می‌گیرند.

    Returns:
        (is_privacy, matched_indicators)
    """
    if not text:
        return False, []

    text_lower = text.lower()
    matched: list[str] = []

    for pat in PRIVACY_INDICATORS:
        m = re.search(pat, text_lower, flags=re.IGNORECASE)
        if m:
            matched.append(m.group(0).strip())

    return len(matched) >= 1, matched


def apply_pqc_tilt(survival_base: float, pqc_score: float,
                   tilt_max: float = 0.15) -> float:
    """
    اعمال تقویت PQC به survival_probability.

    فرمول:
        survival_adjusted = survival_base * (1 + tilt_max * pqc_score)

    مثال:
        survival_base = 0.4, pqc_score = 1.0 (Dilithium واقعی)
        → 0.4 * 1.15 = 0.46  (هل کوچک معنادار، نه جهش)
    """
    survival_base = max(0.0, min(1.0, survival_base))
    pqc_score     = max(0.0, min(1.0, pqc_score))
    adjusted      = survival_base * (1.0 + tilt_max * pqc_score)
    return min(1.0, round(adjusted, 4))


def classify_pqc_combined(readme: str, description: str = "",
                          coin_name: str = "") -> dict[str, Any]:
    """
    ترکیب تشخیص PQC + Privacy روی یک متن.
    خروجی به‌صورت dict آمادهٔ ذخیره در CandidateCoin.
    """
    full_text = f"{readme}\n{description}".strip()
    sig       = pqc_signal(full_text, coin_name=coin_name)
    is_priv, priv_indicators = detect_privacy(full_text)

    return {
        "pqc_score":         sig.score,
        "pqc_family":        sig.family,
        "is_pqc":            sig.is_pqc,
        "pqc_reasons":       sig.reasons,
        "is_privacy":        is_priv,
        "privacy_signals":   priv_indicators[:5],   # حداکثر ۵ تا
        "signature_scheme":  sig.family if sig.is_pqc else "ecdsa",
    }
