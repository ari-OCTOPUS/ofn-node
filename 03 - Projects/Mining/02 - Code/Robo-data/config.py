"""
TESSERACT-Miner v0.4 — Configuration
=====================================
تمام ثابت‌های پروژه — قواعد ۱۲گانهٔ غیرقابل‌مذاکره + پارامترهای v0.4 (PQC + Dual-Track).

تغییر این فایل = تغییر رفتار ربات.
هر تغییر باید با کامنت توضیح داده شود.
"""

import os
from dotenv import load_dotenv

# بارگذاری .env با override=True (لازم برای Windows)
load_dotenv(override=True)


# ════════════════════════════════════════════════════════════════════════════
# قواعد ۱۲گانهٔ غیرقابل‌مذاکره
# ════════════════════════════════════════════════════════════════════════════
# ۱. فقط کوین‌های ≤۹۰ روز (Frontier rule)
# ۲. ASIC/GPU-only = blocklist
# ۳. Fractional Kelly = 0.25 (محافظه‌کارانه)
# ۴. سقف ۲۰٪ هش‌ریت روی هر کوین
# ۵. لبهٔ منفی → idle (نه force-allocate)
# ۶. Survival Filter قبل از هر سرمایه‌گذاری
# ۷. Sanitize input برای جلوگیری از Prompt Injection
# ۸. Cross-Source Triangulation برای validation
# ۹. Hybrid Exit ۲۰/۸۰
# ۱۰. Stablecoin خروج فقط USDC/PYUSD (MiCA/GENIUS-compliant)
# ۱۱. PQC نمی‌تواند گیت ۹۰ روز را دور بزند (فقط watchlist)
# ۱۲. مرز بودجهٔ Track A/B سفت — بدون نشت
# ════════════════════════════════════════════════════════════════════════════


# ── کلیدهای API ───────────────────────────────────────────────────────────────
GITHUB_TOKEN:      str = os.getenv("GITHUB_TOKEN", "")
COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
SOCHAIN_API_KEY:   str = os.getenv("SOCHAIN_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")


# ── قانون ۱: سن کوین (Frontier rule) ──────────────────────────────────────────
MAX_COIN_AGE_DAYS: int = 90       # هیچ استثنایی ندارد


# ── قانون ۲–۳: Kelly + هش‌ریت ─────────────────────────────────────────────────
FRACTIONAL_KELLY:     float = 0.25
MAX_COIN_HASHRATE:    float = 0.20   # ۲۰٪ سقف per coin
MIN_EDGE_TO_ALLOCATE: float = 0.0    # لبهٔ منفی → idle


# ── قانون ۹: Hybrid Exit ──────────────────────────────────────────────────────
EXIT_LOCKIN_PCT: float = 0.20   # ۲۰٪ فروری در کوین stable
EXIT_LET_RIDE_PCT: float = 0.80


# ════════════════════════════════════════════════════════════════════════════
# v0.4 — لایهٔ PQC (post-quantum cryptography awareness)
# ════════════════════════════════════════════════════════════════════════════

# سقف تقویت survival توسط سیگنال PQC — وزن متوسط (نه محور درجه‌یک)
PQC_TILT_MAX:            float = 0.15
PQC_WATCHLIST_THRESHOLD: float = 0.7    # کف امتیاز برای ورود به watchlist
PQC_TRACK_THRESHOLD:     float = 0.5    # کف امتیاز برای ورود به Track B
PQC_REQUIRE_CODE_PROOF:  bool  = True   # «quantum-resistant» بدون کد = ۰
PQC_NIST_FAMILIES        = ("dilithium", "kyber", "falcon")


# ════════════════════════════════════════════════════════════════════════════
# v0.4 — معماری Dual-Track (barbell در سطح استخراج)
# ════════════════════════════════════════════════════════════════════════════

# سهم هش‌ریت Track B (PQC frontier)
PQC_TRACK_BUDGET: float = 0.25         # ۲۵٪ → ۷۵٪ Track A / ۲۵٪ Track B

# آیا بودجهٔ بلااستفادهٔ Track B به Track A منتقل شود؟
# پیش‌فرض False (barbell سفت می‌ماند)
PQC_BUDGET_REALLOCATE: bool = False


# ════════════════════════════════════════════════════════════════════════════
# تنظیمات اجرا
# ════════════════════════════════════════════════════════════════════════════

REQUEST_TIMEOUT:    int = 15           # ثانیه
MAX_README_FETCH:   int = 30           # سقف خوانش README (rate-limit)
TOP_N_RESULTS:      int = 50           # کاندیدهای نهایی
OUTPUT_FILE:        str = "candidates_v04.json"
WATCHLIST_FILE:     str = "pqc_watchlist.json"


# ── خروجی فایل‌ها ─────────────────────────────────────────────────────────────
DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
