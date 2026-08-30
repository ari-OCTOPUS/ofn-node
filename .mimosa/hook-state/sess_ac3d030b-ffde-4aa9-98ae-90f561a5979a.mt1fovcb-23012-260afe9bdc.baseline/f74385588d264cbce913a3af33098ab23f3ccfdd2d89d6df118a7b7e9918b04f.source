"""
TESSERACT-Miner v0.4 — Scout + PQC + Dual-Track
==================================================
نسخهٔ کامل بسته‌بندی‌شدهٔ آپدیت v0.4. این فایل ۳ کار می‌کند:

  1. کشف کوین — همان pipeline اسکات از v0.3 (۵ منبع)
  2. PQC-Aware — تشخیص امضای پساکوانتومی روی هر کوین
                 + تقویت survival تا حداکثر ۱۵٪ + watchlist
  3. Dual-Track — تقسیم کاندیداها به Track A (عمومی ۷۵٪)
                  و Track B (PQC ≤۹۰ روزه ۲۵٪) — Kelly مستقل

اصل ضدشکنندگی:
  - قانون ۹۰ روز در هر دو track غیرقابل‌مذاکره
  - مرز بودجه Track A/B سفت (بدون نشت پیش‌فرض)
  - شعار «quantum-resistant» بدون کد = امتیاز ۰

اجرا:
    1. کپی فایل .env.example به .env
    2. پر کردن کلیدهای API در .env
    3. python tesseract_v04.py
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

# Windows UTF-8 fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup

# ── ماژول‌های پروژه ─────────────────────────────────────────────────────────
from config import (
    GITHUB_TOKEN, COINGECKO_API_KEY, SOCHAIN_API_KEY,
    REQUEST_TIMEOUT, MAX_README_FETCH, TOP_N_RESULTS,
    OUTPUT_FILE, WATCHLIST_FILE, DATA_DIR,
    MAX_COIN_AGE_DAYS,
    PQC_TILT_MAX, PQC_WATCHLIST_THRESHOLD, PQC_TRACK_THRESHOLD,
    PQC_TRACK_BUDGET, PQC_BUDGET_REALLOCATE,
    FRACTIONAL_KELLY, MAX_COIN_HASHRATE,
)
from pqc_classifier import (
    pqc_signal, detect_privacy, apply_pqc_tilt, classify_pqc_combined,
)


# ════════════════════════════════════════════════════════════════════════════
# Logging
# ════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("TESSERACT")


# ════════════════════════════════════════════════════════════════════════════
# Schema — کاندید v0.4 با فیلدهای PQC و Track
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class CandidateCoin:
    """ساختار v0.4 با فیلدهای PQC و Track افزوده."""
    coin_name:               str
    algorithm:               str
    launch_date:             str           # ISO 8601
    ann_url:                 str
    regulatory_score:        float          # ۰ تا ۱
    mineable_on_orangepi:    bool
    source:                  str
    scraped_at:              str
    # متادیتای پایه
    volume_usd:              float = 0.0
    market_cap_usd:          float = 0.0
    classifier_confidence:   float = 0.0
    rank_score:              float = 0.0
    age_days:                int   = 0
    # محاسبهٔ survival
    survival_base:           float = 0.5
    survival_adjusted:       float = 0.5
    # v0.4 — فیلدهای PQC
    signature_scheme:        str   = "ecdsa"   # ecdsa | dilithium | kyber | ...
    pqc_score:               float = 0.0
    pqc_family:              str   = "none"
    is_pqc:                  bool  = False
    pqc_reasons:             list[str] = field(default_factory=list)
    is_privacy:              bool  = False
    privacy_signals:         list[str] = field(default_factory=list)
    # v0.4 — Track assignment
    track:                   str   = "A"      # "A" general | "B" PQC | "" rejected
    in_watchlist:            bool  = False
    track_reason:            str   = ""
    # extra
    extra:                   dict[str, Any] = field(default_factory=dict)


# ════════════════════════════════════════════════════════════════════════════
# Sanitize
# ════════════════════════════════════════════════════════════════════════════
FORBIDDEN_PATTERNS: list[str] = [
    r"ignore\s+(previous|prior|all)\s+instructions?",
    r"system\s+prompt", r"override", r"jailbreak",
    r"clear\s+history", r"forget\s+everything",
    r"new\s+instructions?", r"act\s+as\s+", r"role[-_]?play",
    r"disregard",
]
HTML_TAG_RE      = re.compile(r"<[^>]+>")
MARKDOWN_CODE_RE = re.compile(r"```[\s\S]*?```")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_input(value: Any, max_length: int = 500) -> str:
    if value is None: return ""
    try:    text = str(value)
    except: return ""
    text = CONTROL_CHARS_RE.sub("", text)
    text = MARKDOWN_CODE_RE.sub("[CODE_REMOVED]", text)
    text = HTML_TAG_RE.sub("", text)
    for pat in FORBIDDEN_PATTERNS:
        text = re.sub(pat, "[REDACTED]", text, flags=re.IGNORECASE)
    return text.strip()[:max_length]


def sanitize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None: return default
        r = float(value)
        if r != r or r in (float("inf"), float("-inf")): return default
        return r
    except (ValueError, TypeError):
        return default


# ════════════════════════════════════════════════════════════════════════════
# Algorithm Database (همانند v0.3)
# ════════════════════════════════════════════════════════════════════════════
ALGORITHM_DATABASE: dict[str, dict[str, Any]] = {
    "randomx":    {"mineable_on_orangepi": True,  "asic_resistance": "strong"},
    "yespower":   {"mineable_on_orangepi": True,  "asic_resistance": "strong"},
    "cryptonight":{"mineable_on_orangepi": True,  "asic_resistance": "weak"},
    "argon2":     {"mineable_on_orangepi": True,  "asic_resistance": "strong"},
    "ghostrider": {"mineable_on_orangepi": True,  "asic_resistance": "strong"},
    "verushash":  {"mineable_on_orangepi": True,  "asic_resistance": "strong"},
    "minotaurx":  {"mineable_on_orangepi": True,  "asic_resistance": "strong"},
    "kheavyhash": {"mineable_on_orangepi": False, "asic_resistance": "weak"},
    "ethash":     {"mineable_on_orangepi": False, "asic_resistance": "weak"},
    "blake3":     {"mineable_on_orangepi": False, "asic_resistance": "weak"},
    "sha256":     {"mineable_on_orangepi": False, "asic_resistance": "none"},
    "scrypt":     {"mineable_on_orangepi": False, "asic_resistance": "none"},
}

BLOCKLIST_KEYWORDS: set[str] = {
    "sha256", "scrypt", "ethash", "kheavyhash", "etchash", "blake3", "kawpow",
}

TOOL_NAME_KEYWORDS: set[str] = {
    "xmrig", "cpuminer", "cgminer", "bfgminer", "ccminer", "sgminer",
    "miner", "mining-software", "miningcore", "proxy", "stratum-proxy",
    "pool-proxy", "benchmark", "hashbench", "farm", "farmmanager",
    "rig-manager", "rigmanager", "monitor", "watchdog", "dashboard",
}

TOOL_DESC_INDICATORS: list[str] = [
    "unified cpu/gpu miner", "silent crypto miner", "mining software",
    "stratum proxy", "pool proxy", "farm management", "ansible playbook",
    "monitoring dashboard", "wallet software", "block explorer",
    "node software", "benchmark tool",
]


def is_blocklisted(algorithm: str) -> bool:
    if not algorithm: return False
    a = algorithm.lower().strip()
    return any(bad in a for bad in BLOCKLIST_KEYWORDS)


def is_tool_not_coin(coin: CandidateCoin) -> bool:
    desc = (coin.extra.get("description") or "").lower()
    name = coin.coin_name.lower()
    if any(kw in name for kw in TOOL_NAME_KEYWORDS):  return True
    if any(ind in desc for ind in TOOL_DESC_INDICATORS): return True
    return False


# ════════════════════════════════════════════════════════════════════════════
# Algorithm Classifier (همانند v0.3)
# ════════════════════════════════════════════════════════════════════════════
def detect_algorithm_in_text(text: str) -> tuple[str, float]:
    if not text: return "unknown", 0.0
    t = text.lower()
    priority = ["randomx", "yespower", "ghostrider", "verushash", "minotaurx",
                "argon2", "cryptonight", "kheavyhash", "ethash", "blake3",
                "sha256", "scrypt"]
    matches: list[tuple[str, int]] = []
    for algo in priority:
        c = len(re.findall(r"\b" + re.escape(algo) + r"\b", t))
        if c > 0: matches.append((algo, c))
    if not matches: return "unknown", 0.0
    matches.sort(key=lambda x: x[1], reverse=True)
    a, c = matches[0]
    conf = 0.9 if c >= 3 else (0.75 if c == 2 else 0.6)
    return a, conf


def classify_coin_algorithm(hint: str) -> dict[str, Any]:
    if not hint or hint == "unknown":
        return {"matched": False, "algorithm": "unknown"}
    a = hint.lower().strip()
    if a in ALGORITHM_DATABASE:
        r = ALGORITHM_DATABASE[a].copy()
        r["matched"] = True
        r["algorithm"] = a
        return r
    for known in ALGORITHM_DATABASE:
        if known in a or a in known:
            r = ALGORITHM_DATABASE[known].copy()
            r["matched"] = True
            r["algorithm"] = known
            return r
    return {"matched": False, "algorithm": hint}


def fetch_github_readme(repo_full_name: str) -> Optional[str]:
    if not GITHUB_TOKEN: return None
    url = f"https://api.github.com/repos/{repo_full_name}/readme"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}",
               "Accept": "application/vnd.github+json"}
    try:
        r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code == 404: return None
        r.raise_for_status()
        b64 = r.json().get("content", "")
        if not b64: return None
        return base64.b64decode(b64).decode("utf-8", errors="ignore")[:15000]
    except Exception as e:
        logger.debug(f"README fetch {repo_full_name}: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# v0.4 — Age computation
# ════════════════════════════════════════════════════════════════════════════
def compute_age_days(launch_date: str) -> int:
    """محاسبهٔ سن کوین — برای قانون ۹۰ روز."""
    if not launch_date: return 0
    try:
        dt = datetime.fromisoformat(launch_date.replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0, delta.days)
    except Exception:
        return 0


# ════════════════════════════════════════════════════════════════════════════
# v0.4 — Enrichment with PQC
# ════════════════════════════════════════════════════════════════════════════
def enrich_with_classifier_and_pqc(
    coin: CandidateCoin,
    readme_budget: list[int],
) -> CandidateCoin:
    """
    Enrich یکپارچه:
      1. classify algorithm (mining)
      2. اگر unknown و github source، README بخوان
      3. هم algorithm را تشخیص بده هم PQC
      4. age_days محاسبه کن
      5. survival adjusted با PQC tilt
    """
    # ── ۱. Algorithm classifier (mining) ──────────────────────────────────────
    classification = classify_coin_algorithm(coin.algorithm)
    if classification["matched"]:
        coin.algorithm            = classification["algorithm"]
        coin.mineable_on_orangepi = bool(classification.get("mineable_on_orangepi", False))
        coin.classifier_confidence = 1.0
        coin.extra["asic_resistance"] = classification.get("asic_resistance", "unknown")

    # ── ۲. README fetch (هم برای algorithm، هم PQC) ──────────────────────────
    readme_text: str = ""
    description: str = str(coin.extra.get("description", ""))

    needs_readme = (
        coin.algorithm == "unknown" or coin.pqc_score == 0.0
    ) and coin.source == "github" and readme_budget[0] > 0

    if needs_readme:
        m = re.match(r"https?://github\.com/([^/]+/[^/]+)", coin.ann_url)
        if m:
            repo_name = m.group(1)
            readme_budget[0] -= 1
            time.sleep(0.5)
            readme_text = fetch_github_readme(repo_name) or ""

    # ── ۳. Algorithm detection از README (اگر هنوز unknown) ──────────────────
    if coin.algorithm == "unknown" and readme_text:
        search_text = readme_text + "\n" + description
        algo, conf  = detect_algorithm_in_text(search_text)
        if algo != "unknown":
            classification = classify_coin_algorithm(algo)
            if classification["matched"]:
                coin.algorithm            = classification["algorithm"]
                coin.mineable_on_orangepi = bool(classification.get("mineable_on_orangepi", False))
                coin.classifier_confidence = conf
                coin.extra["asic_resistance"] = classification.get("asic_resistance", "unknown")

    # ── ۴. PQC detection ─────────────────────────────────────────────────────
    pqc_text = readme_text + "\n" + description + "\n" + coin.coin_name
    pqc_info = classify_pqc_combined(readme_text, description, coin.coin_name)

    coin.signature_scheme = pqc_info["signature_scheme"]
    coin.pqc_score        = pqc_info["pqc_score"]
    coin.pqc_family       = pqc_info["pqc_family"]
    coin.is_pqc           = pqc_info["is_pqc"]
    coin.pqc_reasons      = pqc_info["pqc_reasons"]
    coin.is_privacy       = pqc_info["is_privacy"]
    coin.privacy_signals  = pqc_info["privacy_signals"]

    # ── ۵. Age + Survival adjustment ─────────────────────────────────────────
    coin.age_days = compute_age_days(coin.launch_date)

    # survival_base = اولیه از regulatory_score و mineable
    base = coin.regulatory_score * 0.5
    if coin.mineable_on_orangepi: base += 0.3
    if coin.algorithm != "unknown": base += 0.2
    coin.survival_base = round(min(1.0, base), 3)

    # تقویت PQC (حداکثر ۱۵٪)
    coin.survival_adjusted = apply_pqc_tilt(
        coin.survival_base, coin.pqc_score, tilt_max=PQC_TILT_MAX,
    )

    # ── ۶. Privacy penalty (تنش با exit_liquidity) ───────────────────────────
    # طبق spec بخش ۴: privacy منفی روی exit، نه روی survival
    # ذخیره می‌کنیم تا Exit Manager از آن استفاده کند
    if coin.is_privacy:
        coin.extra["exit_liquidity_penalty"] = 0.30  # ۳۰٪ کسر از exit confidence

    return coin


# ════════════════════════════════════════════════════════════════════════════
# v0.4 — Track Assignment (هستهٔ Dual-Track)
# ════════════════════════════════════════════════════════════════════════════
def assign_track(coin: CandidateCoin) -> tuple[str, bool, str]:
    """
    تخصیص track طبق قواعد v0.4:
      - اگر سن > ۹۰ روز → رد (قانون ۱)
        * ولی اگر pqc_score >= PQC_WATCHLIST_THRESHOLD → به watchlist اضافه
      - اگر mineable_on_orangepi نیست → رد
      - اگر pqc_score >= PQC_TRACK_THRESHOLD → Track B
      - وگرنه → Track A

    Returns: (track, in_watchlist, reason)
        track ∈ {"A", "B", ""}  ("" = رد)
    """
    # قانون ۱: سن
    if coin.age_days > MAX_COIN_AGE_DAYS:
        if coin.pqc_score >= PQC_WATCHLIST_THRESHOLD:
            return "", True, f"age>{MAX_COIN_AGE_DAYS}d but PQC>{PQC_WATCHLIST_THRESHOLD} → watchlist"
        return "", False, f"age={coin.age_days}d > {MAX_COIN_AGE_DAYS}d"

    # قانون ۲: قابل ماین
    if not coin.mineable_on_orangepi:
        return "", False, "not mineable on OrangePi"

    # قانون ۳: blocklist
    if is_blocklisted(coin.algorithm):
        return "", False, f"blocklisted algo: {coin.algorithm}"

    # Track B یا A؟
    if coin.pqc_score >= PQC_TRACK_THRESHOLD:
        return "B", False, f"PQC {coin.pqc_family} (score={coin.pqc_score})"

    return "A", False, "general frontier"


# ════════════════════════════════════════════════════════════════════════════
# Survival Filter (v0.3 + age check)
# ════════════════════════════════════════════════════════════════════════════
def survival_filter(coin: CandidateCoin) -> tuple[bool, str]:
    if not coin.coin_name or not coin.coin_name.strip():
        return False, "missing coin_name"
    if not coin.ann_url or not coin.ann_url.startswith(("http://", "https://")):
        return False, "invalid ann_url"
    if is_blocklisted(coin.algorithm):
        return False, f"blocklisted: {coin.algorithm}"
    if coin.volume_usd < 0:
        return False, "corrupted volume"
    if coin.source == "github" and is_tool_not_coin(coin):
        return False, "tool/infra repo"
    return True, "ok"


# ════════════════════════════════════════════════════════════════════════════
# Source Fetchers (مختصرشده — منطق همانند v0.3)
# ════════════════════════════════════════════════════════════════════════════
def fetch_from_github() -> list[CandidateCoin]:
    results: list[CandidateCoin] = []
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN missing — skip GitHub")
        return results

    since = (datetime.now(timezone.utc) - timedelta(days=21)).strftime("%Y-%m-%d")
    queries = [
        f"randomx cryptocurrency pushed:>{since} -miner -proxy -stratum -pool",
        f"topic:randomx topic:cryptocurrency pushed:>{since}",
        f"yespower cryptocurrency pushed:>{since} -miner -proxy",
        f"genesis block randomx pushed:>{since} -miner",
        f"quantum-resistant mining randomx pushed:>{since}",
        f"ghostrider cryptocurrency blockchain pushed:>{since} -miner",
        f'"fair launch" OR "no premine" randomx pushed:>{since}',
        # v0.4: جستجوی PQC-aware
        f"dilithium blockchain pushed:>{since} -miner",
        f"liboqs cryptocurrency pushed:>{since}",
        f"lattice cryptocurrency pushed:>{since} -miner -proxy",
    ]
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    for q in queries:
        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                headers=headers,
                params={"q": q, "sort": "updated", "order": "desc", "per_page": 15},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            for item in r.json().get("items", []):
                name = sanitize_input(item.get("name"))
                if not name: continue
                # حدس الگوریتم از topic
                algo = "unknown"
                for t in (item.get("topics") or []):
                    tl = str(t).lower()
                    for known in ALGORITHM_DATABASE:
                        if known in tl:
                            algo = known
                            break
                    if algo != "unknown": break

                coin = CandidateCoin(
                    coin_name=name, algorithm=algo,
                    launch_date=sanitize_input(item.get("created_at")),
                    ann_url=sanitize_input(item.get("html_url")),
                    regulatory_score=0.5, mineable_on_orangepi=False,
                    source="github",
                    scraped_at=datetime.now(timezone.utc).isoformat(),
                    extra={
                        "stars": int(item.get("stargazers_count", 0) or 0),
                        "description": sanitize_input(item.get("description"), 300),
                        "full_name": sanitize_input(item.get("full_name")),
                        "pushed_at":  sanitize_input(item.get("pushed_at")),
                    },
                )
                results.append(coin)
            time.sleep(1)
        except requests.RequestException as e:
            logger.error(f"GitHub '{q[:40]}...': {e}")

    logger.info(f"GitHub: {len(results)} raw")
    return results


def fetch_from_coingecko() -> list[CandidateCoin]:
    results: list[CandidateCoin] = []
    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    for page in (8, 9, 10, 11, 12):
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                headers=headers,
                params={"vs_currency": "usd", "order": "market_cap_asc",
                        "per_page": 50, "page": page, "sparkline": "false",
                        "price_change_percentage": "7d"},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            for item in r.json():
                coin_id = sanitize_input(item.get("id"))
                name    = sanitize_input(item.get("name"))
                if not coin_id or not name: continue
                mcap = sanitize_float(item.get("market_cap"))
                if mcap > 50_000_000 or (0 < mcap < 1_000): continue

                coin = CandidateCoin(
                    coin_name=name, algorithm="unknown",
                    launch_date=datetime.now(timezone.utc).date().isoformat(),
                    ann_url=f"https://www.coingecko.com/en/coins/{coin_id}",
                    regulatory_score=0.55, mineable_on_orangepi=False,
                    source="coingecko_smallcap",
                    scraped_at=datetime.now(timezone.utc).isoformat(),
                    market_cap_usd=mcap,
                    extra={"symbol": sanitize_input(item.get("symbol")).upper(),
                           "market_cap_usd": mcap},
                )
                results.append(coin)
            time.sleep(1.5)
        except requests.RequestException as e:
            logger.error(f"CoinGecko p{page}: {e}")
            break
    logger.info(f"CoinGecko: {len(results)} raw")
    return results


def fetch_from_bitcointalk() -> list[CandidateCoin]:
    results: list[CandidateCoin] = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}
    try:
        r = requests.get("https://bitcointalk.org/index.php?board=159.0",
                         headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        anchors = soup.select("td.subject a[href*='topic']") or \
                  [a for a in soup.find_all("a", href=True) if "topic=" in a.get("href", "")]
        keywords = ["cpu", "randomx", "yespower", "argon2", "cryptonight",
                    "mineable", "launch", "mainnet", "[ann]", " ann ",
                    "pow", "ghostrider", "minotaurx", "verus",
                    "dilithium", "kyber", "post-quantum", "lattice"]
        seen: set[str] = set()
        for a in anchors[:100]:
            title = sanitize_input(a.get_text(strip=True), 200)
            href  = sanitize_input(a.get("href", ""))
            if not title or len(title) < 5 or not href.startswith("http"):
                continue
            if href in seen: continue
            seen.add(href)
            if not any(k in title.lower() for k in keywords): continue
            algo, _ = detect_algorithm_in_text(title)
            coin = CandidateCoin(
                coin_name=title, algorithm=algo,
                launch_date=datetime.now(timezone.utc).date().isoformat(),
                ann_url=href, regulatory_score=0.4,
                mineable_on_orangepi=False, source="bitcointalk_ann",
                scraped_at=datetime.now(timezone.utc).isoformat(),
            )
            results.append(coin)
    except Exception as e:
        logger.error(f"Bitcointalk: {e}")
    logger.info(f"Bitcointalk: {len(results)} raw")
    return results


# ════════════════════════════════════════════════════════════════════════════
# v0.4 — Watchlist Management
# ════════════════════════════════════════════════════════════════════════════
def save_watchlist(watchlist_coins: list[CandidateCoin]) -> None:
    """ذخیرهٔ کوین‌های PQC>90d در watchlist (برای ردیابی fork های آینده)."""
    path = os.path.join(DATA_DIR, WATCHLIST_FILE)
    existing: list[dict] = []
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    seen_urls = {c.get("ann_url", "") for c in existing}

    added = 0
    for c in watchlist_coins:
        if c.ann_url and c.ann_url not in seen_urls:
            existing.append({
                "coin_name":   c.coin_name,
                "ann_url":     c.ann_url,
                "pqc_family":  c.pqc_family,
                "pqc_score":   c.pqc_score,
                "age_days":    c.age_days,
                "added_at":    datetime.now(timezone.utc).isoformat(),
                "reason":      c.track_reason,
            })
            added += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing[-200:], f, indent=2, ensure_ascii=False)  # ۲۰۰ تای آخر
    if added > 0:
        logger.info(f"📋 PQC Watchlist: +{added} (total={len(existing[-200:])})")


# ════════════════════════════════════════════════════════════════════════════
# Ranking
# ════════════════════════════════════════════════════════════════════════════
def compute_rank_score(c: CandidateCoin) -> float:
    score = 0.0
    if c.mineable_on_orangepi:        score += 50
    score += c.classifier_confidence  * 20
    score += c.regulatory_score       * 10
    weights = {"github": 15, "bitcointalk_ann": 18,
               "coingecko_smallcap": 8, "coingecko_trending": 8,
               "dexscreener": 5, "sochain_baseline": 0}
    score += weights.get(c.source, 0)

    stars = c.extra.get("stars", 0)
    if isinstance(stars, (int, float)):
        if 0 < stars < 1000: score += min(stars / 20, 5)
        elif stars >= 1000:  score -= 5

    if c.extra.get("asic_resistance") == "strong": score += 5
    elif c.extra.get("asic_resistance") == "weak": score -= 5

    # v0.4: بوست از survival_adjusted (شامل PQC tilt)
    score += (c.survival_adjusted - c.survival_base) * 100  # کوچک ولی معنادار

    # v0.4: penalty برای privacy (روی rank، نه روی survival)
    if c.is_privacy: score -= 3

    return round(score, 2)


# ════════════════════════════════════════════════════════════════════════════
# Dual-Track Hashrate Allocation (stub — برای orchestrator واقعی)
# ════════════════════════════════════════════════════════════════════════════
def allocate_dual_track(
    candidates: list[CandidateCoin],
    h_total_khs: float = 100.0,
) -> dict[str, Any]:
    """
    تخصیص هش‌ریت با Dual-Track barbell:
      Track A = (1 - PQC_TRACK_BUDGET) × H_total
      Track B = PQC_TRACK_BUDGET × H_total

    این یک stub ساده است. در orchestrator واقعی، هر track باید
    Kelly مستقل اجرا کند (با fractional_kelly=0.25 و سقف ۲۰٪ per coin).

    Args:
        candidates: کوین‌های تأییدشده (track ∈ {A,B})
        h_total_khs: کل هش‌ریت ناوگان (kH/s)
    Returns:
        dict با تخصیص هر کوین در هر track
    """
    track_a = [c for c in candidates if c.track == "A"]
    track_b = [c for c in candidates if c.track == "B"]

    h_track_a = h_total_khs * (1 - PQC_TRACK_BUDGET)
    h_track_b = h_total_khs * PQC_TRACK_BUDGET

    def _kelly_allocate(coins: list[CandidateCoin], budget: float) -> dict[str, float]:
        """تخصیص ساده با وزن survival_adjusted (تقریب Kelly)."""
        if not coins or budget <= 0: return {}
        weights = [c.survival_adjusted for c in coins]
        total = sum(weights)
        if total <= 0: return {}
        # سقف ۲۰٪ per coin
        cap = budget * MAX_COIN_HASHRATE
        alloc: dict[str, float] = {}
        for c, w in zip(coins, weights):
            raw = budget * (w / total) * FRACTIONAL_KELLY * 4  # نرمال
            alloc[c.coin_name] = round(min(raw, cap), 2)
        return alloc

    return {
        "h_total_khs":     h_total_khs,
        "h_track_a_khs":   round(h_track_a, 2),
        "h_track_b_khs":   round(h_track_b, 2),
        "track_a_count":   len(track_a),
        "track_b_count":   len(track_b),
        "track_a_alloc":   _kelly_allocate(track_a, h_track_a),
        "track_b_alloc":   _kelly_allocate(track_b, h_track_b),
        "track_b_idle":    len(track_b) == 0,
        "reallocate":      PQC_BUDGET_REALLOCATE,
    }


# ════════════════════════════════════════════════════════════════════════════
# Main Pipeline
# ════════════════════════════════════════════════════════════════════════════
def deduplicate(coins: list[CandidateCoin]) -> list[CandidateCoin]:
    seen: set[str] = set()
    unique: list[CandidateCoin] = []
    for c in coins:
        key = c.ann_url.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def run_pipeline() -> dict[str, Any]:
    logger.info("=" * 70)
    logger.info("🚀 TESSERACT-Miner v0.4 — Dual-Track + PQC Pipeline")
    logger.info("=" * 70)

    # ── ۱. جمع‌آوری ──────────────────────────────────────────────────────────
    raw: list[CandidateCoin] = []
    for fetcher in (fetch_from_github, fetch_from_coingecko, fetch_from_bitcointalk):
        try: raw.extend(fetcher())
        except Exception as e: logger.error(f"{fetcher.__name__}: {e}")

    logger.info(f"📦 Total raw: {len(raw)}")

    # ── ۲. Survival ──────────────────────────────────────────────────────────
    survivors = [c for c in raw if survival_filter(c)[0]]
    logger.info(f"🛡️  Post-Survival: {len(survivors)}")

    # ── ۳. Deduplicate ───────────────────────────────────────────────────────
    unique = deduplicate(survivors)
    logger.info(f"🔁 Unique: {len(unique)}")

    # ── ۴. Enrichment (algorithm + PQC) ──────────────────────────────────────
    logger.info(f"🧠 Enrichment (budget={MAX_README_FETCH} README)...")
    budget = [MAX_README_FETCH]
    enriched = [enrich_with_classifier_and_pqc(c, budget) for c in unique]

    # ── ۵. Track Assignment ──────────────────────────────────────────────────
    track_a, track_b, rejected, watchlist = [], [], [], []
    for c in enriched:
        track, in_wl, reason = assign_track(c)
        c.track          = track
        c.in_watchlist   = in_wl
        c.track_reason   = reason
        if   track == "A": track_a.append(c)
        elif track == "B": track_b.append(c)
        else:
            if in_wl: watchlist.append(c)
            else:     rejected.append(c)

    logger.info(f"🎯 Track A (general): {len(track_a)}")
    logger.info(f"🔐 Track B (PQC):     {len(track_b)}")
    logger.info(f"📋 PQC Watchlist (>90d): {len(watchlist)}")
    logger.info(f"❌ Rejected:          {len(rejected)}")

    # ── ۶. Ranking ───────────────────────────────────────────────────────────
    for c in track_a + track_b:
        c.rank_score = compute_rank_score(c)
    track_a.sort(key=lambda x: x.rank_score, reverse=True)
    track_b.sort(key=lambda x: x.rank_score, reverse=True)

    # ── ۷. Watchlist save ────────────────────────────────────────────────────
    save_watchlist(watchlist)

    # ── ۸. Dual-Track Allocation (stub) ──────────────────────────────────────
    h_total_khs = 100.0   # مقدار نمونه — جایگزین کن با hashrate واقعی ناوگان
    accepted = (track_a + track_b)[:TOP_N_RESULTS]
    allocation = allocate_dual_track(accepted, h_total_khs=h_total_khs)

    # ── ۹. خروجی ────────────────────────────────────────────────────────────
    result = {
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "summary": {
            "raw":            len(raw),
            "post_survival":  len(survivors),
            "track_a_count":  len(track_a),
            "track_b_count":  len(track_b),
            "watchlist_new":  len(watchlist),
            "rejected":       len(rejected),
        },
        "track_a":    [asdict(c) for c in track_a[:TOP_N_RESULTS]],
        "track_b":    [asdict(c) for c in track_b[:TOP_N_RESULTS]],
        "allocation": allocation,
    }

    # ذخیره JSON
    path = os.path.join(DATA_DIR, OUTPUT_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info(f"💾 Saved: {path}")

    return result


# ════════════════════════════════════════════════════════════════════════════
# Printing
# ════════════════════════════════════════════════════════════════════════════
def print_summary(result: dict[str, Any]) -> None:
    sep = "=" * 80
    print("\n" + sep)
    print(" TESSERACT v0.4 — DUAL-TRACK SCOUT RESULTS")
    print(sep)
    s = result["summary"]
    print(f"\nRaw: {s['raw']}  |  Survived: {s['post_survival']}  "
          f"|  Track A: {s['track_a_count']}  |  Track B: {s['track_b_count']}  "
          f"|  Watchlist: {s['watchlist_new']}")

    # Track A
    print("\n" + "─" * 80)
    print(" 🎯 TRACK A — General Frontier (≤90d, mineable, non-PQC)")
    print("─" * 80)
    if result["track_a"]:
        print(f"{'#':<3}{'NAME':<32}{'ALGO':<12}{'AGE':<6}{'SCORE':<7}{'SOURCE'}")
        for i, c in enumerate(result["track_a"][:15], 1):
            print(f"{i:<3}{c['coin_name'][:30]:<32}{c['algorithm'][:10]:<12}"
                  f"{c['age_days']:<6}{c['rank_score']:<7}{c['source'][:15]}")
    else:
        print("  (هیچ کاندیدی فعلاً)")

    # Track B
    print("\n" + "─" * 80)
    print(" 🔐 TRACK B — PQC Frontier (≤90d + PQC≥0.5)")
    print("─" * 80)
    if result["track_b"]:
        print(f"{'#':<3}{'NAME':<25}{'ALGO':<10}{'FAMILY':<12}{'PQC':<6}{'AGE':<6}{'SCORE'}")
        for i, c in enumerate(result["track_b"][:15], 1):
            priv = "🔒" if c["is_privacy"] else ""
            print(f"{i:<3}{c['coin_name'][:23]:<25}{c['algorithm'][:8]:<10}"
                  f"{c['pqc_family'][:10]:<12}{c['pqc_score']:<6}"
                  f"{c['age_days']:<6}{c['rank_score']} {priv}")
    else:
        print("  (هیچ کوین PQC جوانی فعلاً پیدا نشد)")
        print(f"  → Track B بودجه‌اش بیکار می‌ماند ({PQC_TRACK_BUDGET*100:.0f}% از H_total)")
        print(f"  → reallocate به Track A: {PQC_BUDGET_REALLOCATE}")

    # Allocation
    a = result["allocation"]
    print("\n" + "─" * 80)
    print(" ⚡ HASHRATE ALLOCATION (Dual-Track Barbell)")
    print("─" * 80)
    print(f"  H_total: {a['h_total_khs']} kH/s")
    print(f"  ├─ Track A: {a['h_track_a_khs']} kH/s ({(1-PQC_TRACK_BUDGET)*100:.0f}%)")
    print(f"  └─ Track B: {a['h_track_b_khs']} kH/s ({PQC_TRACK_BUDGET*100:.0f}%)")
    if a["track_a_alloc"]:
        print(f"\n  Track A allocation:")
        for coin, khs in list(a["track_a_alloc"].items())[:5]:
            print(f"    • {coin[:30]:<30} {khs:>8} kH/s")
    if a["track_b_alloc"]:
        print(f"\n  Track B allocation:")
        for coin, khs in list(a["track_b_alloc"].items())[:5]:
            print(f"    • {coin[:30]:<30} {khs:>8} kH/s")

    print("\n" + sep)
    print(f" 💾 خروجی کامل در: {os.path.join(DATA_DIR, OUTPUT_FILE)}")
    print(f" 📋 Watchlist در:  {os.path.join(DATA_DIR, WATCHLIST_FILE)}")
    print(sep + "\n")


# ════════════════════════════════════════════════════════════════════════════
# Entry Point
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    result = run_pipeline()
    print_summary(result)
