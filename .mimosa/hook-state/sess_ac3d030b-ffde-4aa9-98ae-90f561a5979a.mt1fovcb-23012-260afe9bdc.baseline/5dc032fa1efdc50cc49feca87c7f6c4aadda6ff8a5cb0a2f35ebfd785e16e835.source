"""
SENTINEL — portfolio_advisor.py
گزارش دوهفتگی کوین‌های پیشنهادی (از QuantumAlphaBot)

هر ۱۴ روز یک بار:
  ۱. paper_ledger.jsonl از QuantumAlphaBot می‌خواند
  ۲. کوین‌هایی که ACCUMULATE گرفته‌اند جمع‌آوری می‌کند
  ۳. فیلتر: survival ≥ 40، final_score ≥ 35، سن < 365 روز
  ۴. تفکیک: veto فقط ماکرو (خریدنی) یا veto واقعی (مشکل‌دار)
  ۵. Claude API برای thesis یک تا دو ساله فراخوانی می‌شود
  ۶. گزارش به تلگرام ارسال می‌شود

اجرا:
  python3 portfolio_advisor.py            # بدون force — اگه ۱۴ روز نگذشته skip
  python3 portfolio_advisor.py --force    # اجرا بدون چک بازه زمانی

cron (۱ام و ۱۵ام هر ماه — ساعت ۸ صبح):
  0 8 1,15 * * cd /path/to/sentinel && python3 portfolio_advisor.py >> logs/advisor.log 2>&1
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# ─── مسیر و لاگ ──────────────────────────────────────────────
_BASE = Path(__file__).parent
load_dotenv(_BASE / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ADVISOR] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel.portfolio_advisor")

# ─── مسیر paper_ledger ────────────────────────────────────────
LEDGER_PATH   = _BASE.parent / "QuantumAlphaBot" / "data" / "paper_ledger.jsonl"
TIMESTAMP_FILE = _BASE / "data" / "advisor_last_run.txt"
MIN_INTERVAL_DAYS = 14

# ─── آستانه‌های فیلتر ─────────────────────────────────────────
MIN_SURVIVAL    = 40      # survival_score حداقل
MIN_FINAL       = 35      # final_score حداقل
MAX_AGE_DAYS    = 365     # سن حداکثر (یک سال)
MIN_APPEARANCES = 2       # حداقل دفعات ظاهر شدن در ledger

# veto دلایلی که ماکرو هستند (موقتی، نه ساختاری)
MACRO_VETO_PREFIXES = ("MACRO_CYCLE",)

# veto دلایلی که واقعاً نگران‌کننده‌اند
STRUCTURAL_VETO_PREFIXES = (
    "HOLDER_DANGER",
    "HOLDER_RED",
    "STRUCTURAL_DECLINE",
    "DRAWDOWN",
    "LLM_VERDICT",
    "LLM_CONFIDENCE_LOW",
)

# ─── تعداد کوین‌های برتر برای thesis ─────────────────────────
TOP_N_THESIS = 5

# ──────────────────────────────────────────────────────────────
# خواندن ledger
# ──────────────────────────────────────────────────────────────

def load_ledger(path: Path) -> list[dict]:
    """همه سیکل‌های paper_ledger.jsonl را می‌خواند."""
    if not path.exists():
        logger.error(f"paper_ledger.jsonl پیدا نشد: {path}")
        return []
    cycles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cycles.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"خط بد در ledger: {e}")
    logger.info(f"ledger: {len(cycles)} سیکل لود شد")
    return cycles


# ──────────────────────────────────────────────────────────────
# تجمیع ACCUMULATE سیگنال‌ها
# ──────────────────────────────────────────────────────────────

def _is_macro_only_veto(veto_reasons: list[str]) -> bool:
    """آیا تنها دلیل veto، ماکرو است (یعنی با بهتر شدن ماکرو خریدنی است)؟"""
    if not veto_reasons:
        return False
    structural = [
        r for r in veto_reasons
        if any(r.startswith(p) for p in STRUCTURAL_VETO_PREFIXES)
    ]
    return len(structural) == 0


def aggregate_candidates(cycles: list[dict]) -> dict[str, dict]:
    """
    از همه سیکل‌ها، کوین‌هایی که llm_decision == ACCUMULATE گرفته‌اند جمع می‌کند.
    حتی اگر سیکل cycle_nulled=True باشد — LLM تشخیص داده بود.

    برمی‌گرداند: dict[symbol → aggregate_info]
    """
    agg: dict[str, dict] = defaultdict(lambda: {
        "appearances": 0,
        "accumulate_count": 0,
        "best_final_score": 0,
        "best_survival_score": 0,
        "best_antifragile": 0,
        "best_derivs_score": 0,
        "min_age_days": 9999,
        "llm_confidences": [],
        "veto_layers_seen": set(),
        "veto_reasons_latest": [],
        "macro_only_veto_count": 0,
        "structural_veto_count": 0,
        "name": "",
        "holder_max_single": None,
        "holder_count": None,
        "social_score": None,
        "latest_cycle_ts": "",
        "llm_decision_latest": "",
    })

    for cycle in cycles:
        cycle_ts = cycle.get("cycle_ts", "")
        for coin in cycle.get("coins", []):
            sym = coin.get("symbol", "").upper()
            if not sym:
                continue

            decision = (coin.get("llm_decision") or "").upper()
            if decision != "ACCUMULATE":
                continue

            d = agg[sym]
            d["appearances"] += 1
            d["accumulate_count"] += 1
            d["name"] = coin.get("name", sym)
            d["latest_cycle_ts"] = cycle_ts

            fs = coin.get("final_score") or 0
            sv = coin.get("survival_score") or 0
            af = coin.get("antifragile") or 0
            dr = coin.get("derivs_score") or 0
            age = coin.get("age_days") or 9999

            if fs > d["best_final_score"]:       d["best_final_score"] = fs
            if sv > d["best_survival_score"]:     d["best_survival_score"] = sv
            if af > d["best_antifragile"]:        d["best_antifragile"] = af
            if dr > d["best_derivs_score"]:       d["best_derivs_score"] = dr
            if age < d["min_age_days"]:           d["min_age_days"] = age

            conf = (coin.get("llm_confidence") or "").upper()
            if conf:
                d["llm_confidences"].append(conf)

            veto_reasons = coin.get("veto_reasons") or []
            veto_layers  = coin.get("veto_layers") or []
            d["veto_layers_seen"].update(veto_layers)
            d["veto_reasons_latest"] = veto_reasons

            if coin.get("vetoed"):
                if _is_macro_only_veto(veto_reasons):
                    d["macro_only_veto_count"] += 1
                else:
                    d["structural_veto_count"] += 1

            # آخرین اطلاعات holder و social
            h = coin.get("holder") or {}
            if h:
                d["holder_max_single"] = h.get("max_single_pct")
                d["holder_count"]      = h.get("holder_count")

            s = coin.get("social") or {}
            if s:
                d["social_score"] = s.get("score") or s.get("galaxy_7d")

    # تبدیل set به list برای JSON-serializability
    for sym in agg:
        agg[sym]["veto_layers_seen"] = list(agg[sym]["veto_layers_seen"])

    return dict(agg)


# ──────────────────────────────────────────────────────────────
# فیلتر و رنک‌بندی
# ──────────────────────────────────────────────────────────────

def _long_term_score(d: dict) -> float:
    """
    امتیاز ترکیبی برای چشم‌انداز ۱-۲ ساله و پتانسیل ۵۰x:
      - appearances (تکرار): نشانه‌ی consistency
      - survival_score: استحکام پروژه
      - final_score: امتیاز کل
      - عدم veto ساختاری: کیفیت
      - سن کم: فرصت رشد
      - llm HIGH confidence: قوت سیگنال
    """
    appearances     = d["appearances"]
    survival        = d["best_survival_score"]
    final           = d["best_final_score"]
    struct_veto     = d["structural_veto_count"]
    macro_veto      = d["macro_only_veto_count"]
    age             = d["min_age_days"]
    high_conf_count = d["llm_confidences"].count("HIGH")

    # عامل سن — کوین‌های جدیدتر پتانسیل بیشتری دارند
    age_factor = max(0.3, 1.0 - (age / 365) * 0.5) if age < 9999 else 0.3

    score = (
        appearances     * 10.0 +   # هر بار ظهور = ۱۰ امتیاز
        survival        *  0.8 +   # survival_score وزن بالا
        final           *  0.5 +   # final_score
        high_conf_count * 15.0 +   # HIGH confidence بسیار مهم
        macro_veto      *  5.0 -   # veto فقط ماکرو = امتیاز مثبت (صبر کن)
        struct_veto     * 25.0     # veto ساختاری = کسر جدی
    ) * age_factor

    return round(score, 2)


def filter_and_rank(agg: dict) -> list[dict]:
    """
    فیلتر اولیه + رنک‌بندی با _long_term_score.
    برمی‌گرداند: لیست مرتب از بهترین به بدترین.
    """
    candidates = []
    for sym, d in agg.items():
        # فیلترهای سخت
        if d["appearances"] < MIN_APPEARANCES:
            continue
        if d["best_survival_score"] < MIN_SURVIVAL:
            continue
        if d["best_final_score"] < MIN_FINAL:
            continue
        if d["min_age_days"] > MAX_AGE_DAYS:
            continue

        lt_score = _long_term_score(d)
        candidates.append({
            "symbol": sym,
            **d,
            "lt_score": lt_score,
            "macro_only": d["structural_veto_count"] == 0,
        })

    candidates.sort(key=lambda x: x["lt_score"], reverse=True)
    logger.info(f"فیلتر: {len(candidates)} کاندید از {len(agg)} کوین ACCUMULATE")
    return candidates


# ──────────────────────────────────────────────────────────────
# Claude API — thesis نویسی
# ──────────────────────────────────────────────────────────────

def _call_claude(prompt: str) -> Optional[str]:
    """
    یک فراخوانی ساده به Anthropic API.
    از ANTHROPIC_API_KEY در محیط استفاده می‌کند.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY تنظیم نشده — thesis خودکار تولید می‌شود")
        return None

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Claude API خطا: {e}")
        return None


def generate_thesis(coin: dict) -> str:
    """
    thesis یک تا دو ساله برای یک کوین — کوتاه و کاربردی.
    اگر API در دسترس نبود، thesis ساده‌ای از داده‌ها می‌سازد.
    """
    prompt = (
        f"You are a crypto researcher focused on 1-2 year high-conviction picks.\n"
        f"Coin: {coin['name']} ({coin['symbol']})\n"
        f"Age: {coin['min_age_days']} days old\n"
        f"Survival score: {coin['best_survival_score']}/100\n"
        f"Final score: {coin['best_final_score']}/100\n"
        f"Appeared in {coin['appearances']} scan cycles, all rated ACCUMULATE\n"
        f"LLM confidences: {', '.join(coin['llm_confidences'])}\n"
        f"Structural vetos: {coin['structural_veto_count']} (lower is better)\n"
        f"Holder max single wallet: {coin.get('holder_max_single', 'unknown')}%\n\n"
        f"Write a 2-3 sentence investment thesis for a 1-2 year horizon targeting 50x potential. "
        f"Be specific about catalysts, risks, and why NOW (early stage) matters. "
        f"Reply ONLY with the thesis, no headers. Keep it under 80 words."
    )

    thesis = _call_claude(prompt)
    if thesis:
        return thesis

    # fallback: thesis دستی از داده‌ها
    macro_note = "macro veto only — investable when BTC trend turns bullish" if coin["macro_only"] else "has structural concerns"
    return (
        f"{coin['name']} is {coin['min_age_days']} days old with survival={coin['best_survival_score']}/100. "
        f"Appeared {coin['appearances']}x as ACCUMULATE — {macro_note}. "
        f"Early-stage project; full position after macro confirmation."
    )


# ──────────────────────────────────────────────────────────────
# قالب‌بندی پیام تلگرام
# ──────────────────────────────────────────────────────────────

def format_telegram_report(candidates: list[dict], theses: dict[str, str],
                            ledger_cycles: int, run_date: str) -> str:
    """
    پیام HTML تلگرام برای گزارش دوهفتگی.
    """
    investable = [c for c in candidates if c["macro_only"]]
    watchlist  = [c for c in candidates if not c["macro_only"]]

    lines = [
        "📊 <b>گزارش دوهفتگی SENTINEL</b>",
        f"🗓 {run_date}",
        f"📂 تحلیل {ledger_cycles} سیکل از QuantumAlphaBot",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "🟢 <b>کوین‌های آماده (با تأیید ماکرو بخر)</b>",
        "<i>veto فقط ماکرو — با بازگشت BTC به روند صعودی فعال می‌شوند</i>",
        "",
    ]

    if investable:
        for i, c in enumerate(investable[:TOP_N_THESIS], 1):
            conf_str = _confidence_label(c["llm_confidences"])
            holder_warn = ""
            if c.get("holder_max_single") and c["holder_max_single"] > 30:
                holder_warn = f" ⚠️ top holder {c['holder_max_single']:.0f}%"

            lines.append(
                f"<b>{i}. {c['name']} ({c['symbol']})</b>{holder_warn}\n"
                f"   📈 final={c['best_final_score']:.0f} · survival={c['best_survival_score']:.0f} "
                f"· سن={c['min_age_days']}d · ظاهر شد: {c['appearances']}x · {conf_str}\n"
                f"   💡 {theses.get(c['symbol'], '—')}"
            )
            lines.append("")
    else:
        lines.append("هیچ کوین آماده‌ای این دوره یافت نشد.")
        lines.append("")

    if watchlist:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━",
            "🟡 <b>واچ‌لیست (veto ساختاری — فعلاً فقط پیگیر)</b>",
            "",
        ]
        for c in watchlist[:3]:
            veto_short = _short_veto(c["veto_layers_seen"])
            lines.append(
                f"• <b>{c['name']} ({c['symbol']})</b> — {veto_short}"
                f" | survival={c['best_survival_score']:.0f}"
            )
        lines.append("")

    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        "⚠️ <i>این گزارش بر اساس داده‌های تاریخی QuantumAlphaBot است."
        " قبل از خرید، وضعیت ماکرو را بررسی کن.</i>",
        "",
        f"🔄 گزارش بعدی: ~۱۴ روز دیگر",
    ]

    return "\n".join(lines)


def _confidence_label(confs: list[str]) -> str:
    if not confs:
        return "—"
    high = confs.count("HIGH")
    med  = confs.count("MEDIUM")
    low  = confs.count("LOW")
    if high >= 2:
        return "⭐⭐⭐ HIGH"
    elif high == 1:
        return "⭐⭐ HIGH×1"
    elif med >= 1:
        return "⭐ MEDIUM"
    else:
        return "LOW"


def _short_veto(layers: list[str]) -> str:
    if not layers:
        return "نامشخص"
    known = {
        "HOLDER_DANGER":        "holder متمرکز",
        "HOLDER_RED":           "holder قرمز",
        "STRUCTURAL_DECLINE":   "ریزش ساختاری",
        "DRAWDOWN":             "drawdown شدید",
        "LLM_VERDICT":          "رد LLM",
        "LLM_CONFIDENCE_LOW":   "اطمینان پایین LLM",
        "SOCIAL_ZERO":          "فعالیت اجتماعی صفر",
    }
    labels = [known.get(l, l) for l in layers if l != "MACRO_CYCLE"]
    return " + ".join(labels) if labels else "macro"


# ──────────────────────────────────────────────────────────────
# ارسال تلگرام
# ──────────────────────────────────────────────────────────────

def send_telegram(text: str) -> bool:
    bot_token = os.getenv("SENTINEL_BOT_TOKEN", "")
    chat_id   = os.getenv("SENTINEL_CHAT_ID", "")
    if not bot_token or not chat_id:
        logger.error("SENTINEL_BOT_TOKEN یا SENTINEL_CHAT_ID تنظیم نشده")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)
        resp.raise_for_status()
        logger.info("گزارش با موفقیت به تلگرام ارسال شد")
        return True
    except Exception as e:
        logger.error(f"ارسال تلگرام شکست خورد: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# بازه زمانی ۱۴ روزه
# ──────────────────────────────────────────────────────────────

def _last_run_days() -> Optional[float]:
    """چند روز از آخرین اجرا گذشته؟ None اگه اولین بار است."""
    if not TIMESTAMP_FILE.exists():
        return None
    try:
        ts = float(TIMESTAMP_FILE.read_text().strip())
        return (time.time() - ts) / 86400
    except Exception:
        return None


def _save_run_timestamp():
    TIMESTAMP_FILE.parent.mkdir(parents=True, exist_ok=True)
    TIMESTAMP_FILE.write_text(str(time.time()))


# ──────────────────────────────────────────────────────────────
# ورودی اصلی
# ──────────────────────────────────────────────────────────────

def run(force: bool = False) -> bool:
    """
    اجرای کامل گزارش.
    force=True → بازه زمانی نادیده گرفته می‌شود.
    برمی‌گرداند: True اگه گزارش ارسال شد.
    """
    # ─── بررسی بازه ─────────────────────────────
    days_since = _last_run_days()
    if not force and days_since is not None and days_since < MIN_INTERVAL_DAYS:
        logger.info(
            f"آخرین اجرا {days_since:.1f} روز پیش بود "
            f"(حداقل {MIN_INTERVAL_DAYS} روز لازم است) — skip"
        )
        return False

    logger.info("شروع گزارش دوهفتگی پرتفوی...")

    # ─── خواندن ledger ───────────────────────────
    cycles = load_ledger(LEDGER_PATH)
    if not cycles:
        logger.error("هیچ سیکلی در ledger نبود — خروج")
        return False

    # ─── تجمیع ───────────────────────────────────
    agg = aggregate_candidates(cycles)
    if not agg:
        logger.warning("هیچ کوین ACCUMULATE‌ای در ledger یافت نشد")
        _save_run_timestamp()
        send_telegram(
            "📊 <b>گزارش دوهفتگی SENTINEL</b>\n\n"
            "این دوره هیچ کوین ACCUMULATE‌ای در QuantumAlphaBot ثبت نشده بود.\n"
            "🔄 دوره بعدی: ~۱۴ روز دیگر"
        )
        return True

    # ─── فیلتر و رنک‌بندی ────────────────────────
    ranked = filter_and_rank(agg)
    if not ranked:
        logger.warning("بعد از فیلتر هیچ کاندیدی باقی نماند")
        _save_run_timestamp()
        send_telegram(
            "📊 <b>گزارش دوهفتگی SENTINEL</b>\n\n"
            "کوین‌های ACCUMULATE وجود دارند اما هیچکدام آستانه‌ی کیفیت را رد نکردند.\n"
            f"(survival ≥ {MIN_SURVIVAL}, final ≥ {MIN_FINAL}, سن &lt; {MAX_AGE_DAYS} روز)\n"
            "🔄 دوره بعدی: ~۱۴ روز دیگر"
        )
        return True

    top = ranked[:TOP_N_THESIS]
    logger.info(f"بهترین {len(top)} کوین: {[c['symbol'] for c in top]}")

    # ─── thesis نویسی ─────────────────────────────
    theses: dict[str, str] = {}
    investable = [c for c in top if c["macro_only"]]
    for c in investable[:TOP_N_THESIS]:
        logger.info(f"درحال نوشتن thesis برای {c['symbol']}...")
        theses[c["symbol"]] = generate_thesis(c)
        time.sleep(1)   # کمی صبر بین درخواست‌ها

    # ─── فرمت و ارسال ────────────────────────────
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report   = format_telegram_report(ranked, theses, len(cycles), run_date)

    logger.info("پیام تلگرام آماده شد — در حال ارسال...")
    success = send_telegram(report)

    if success:
        _save_run_timestamp()
        logger.info("timestamp آخرین اجرا ذخیره شد")

        # ─── لاگ خلاصه ───────────────────────────
        logger.info("─── خلاصه گزارش ───────────────────────────")
        for i, c in enumerate(ranked[:TOP_N_THESIS], 1):
            marker = "🟢" if c["macro_only"] else "🟡"
            logger.info(
                f"  {i}. {marker} {c['symbol']:8s} "
                f"lt_score={c['lt_score']:6.1f} "
                f"appearances={c['appearances']} "
                f"survival={c['best_survival_score']:.0f}"
            )
    return success


# ──────────────────────────────────────────────────────────────
# اجرای مستقیم
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SENTINEL Portfolio Advisor — گزارش دوهفتگی کوین‌های پیشنهادی"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="اجرا بدون چک کردن بازه ۱۴ روزه"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="گزارش را چاپ کن ولی به تلگرام نفرست"
    )
    args = parser.parse_args()

    if args.dry_run:
        # اجرای dry-run — نمایش بدون ارسال
        cycles = load_ledger(LEDGER_PATH)
        if cycles:
            agg    = aggregate_candidates(cycles)
            ranked = filter_and_rank(agg)
            top    = ranked[:TOP_N_THESIS]
            theses = {c["symbol"]: generate_thesis(c) for c in top if c["macro_only"]}
            run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            report   = format_telegram_report(ranked, theses, len(cycles), run_date)
            print("\n" + "═" * 60)
            print(report)
            print("═" * 60 + "\n")
            print(f"[dry-run] ارسال انجام نشد. کاندیدها: {len(ranked)}")
        sys.exit(0)

    ok = run(force=args.force)
    sys.exit(0 if ok else 1)
