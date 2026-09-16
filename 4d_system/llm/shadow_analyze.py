"""
llm/shadow_analyze.py — تحلیلِ شواهدِ سایه‌ای و صدورِ حکمِ تصمیمِ فاز ۲ — بک‌لاگ B11.

فاز ۱ (llm/shadow_compare.py) دو پشتهٔ LLM را روی پرامپت‌های ثابت اجرا و هر
مقایسه را در outputs/llm_shadow.jsonl می‌نویسد. این ماژول همان فایلِ **تجمیع‌شدهٔ
چند-روزه** را می‌خواند، آمار می‌گیرد، و طبقِ «معیارِ تصمیمِ فاز ۲»ِ BACKLOG یک
حکم صادر می‌کند — بدونِ هیچ سوئیچِ زنده، بدونِ ویرایشِ سورس، بدونِ روشن‌کردنِ فلگ.

قاعدهٔ shadow-first پابرجاست: این ابزار فقط **می‌خواند** و **گزارش** می‌دهد. حتی
حکمِ MIGRATE فقط یک «توصیهٔ انسانی، پشتِ فلگ» است؛ خودِ ابزار هیچ رفتاری را
تغییر نمی‌دهد.

معیارِ تصمیمِ فاز ۲ (نقلِ BACKLOG، پس از ≥۳۰ رکورد):
  اگر یک پشته error_rate و تأخیرِ میانگینِ **هر دو** بدتر دارد و mean_similarity>۰٫۷
     → مهاجرت به برنده، پشتِ فلگ؛
  اگر similarity<۰٫۵ → اول واگراییِ محتوایی بررسی شود (سوییچ ممنوع).

هر چیزِ دیگری (بندِ خاکستریِ [۰٫۵،۰٫۷]، تساوی/split، دادهٔ کم‌تر از ۳۰، نبودِ
similarity) عمداً به یک حکمِ «غیرِ‌سوییچِ» صریح نگاشته می‌شود — نه اختراعِ سیاست.

نکتهٔ import: سطحِ ماژول فقط stdlib است. importهای پروژه (config.settings برای
مسیر، llm.shadow_compare.summarize) داخلِ توابع انجام می‌شوند تا importِ ماژول
در محیطِ تست هیچ وابستگیِ سنگینی نخواهد (مثلِ shadow_compare).

اجرا:  python -m llm.shadow_analyze
"""
from __future__ import annotations

import json
import logging
import math
import statistics
from collections import Counter
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = [
    "MIN_RECORDS", "SIM_FORBID", "SIM_MIGRATE", "IN_FILENAME",
    "decide", "analyze", "load_records", "render_report",
]

# ── ثابت‌های معیار (نقلِ مستقیم از BACKLOG) ──────────────────────────────────
MIN_RECORDS = 30      # «پس از ≥۳۰ رکورد»
SIM_FORBID = 0.5      # similarity < 0.5 → سوییچ ممنوع
SIM_MIGRATE = 0.7     # mean_similarity > 0.7 → شرطِ لازمِ مهاجرت
IN_FILENAME = "llm_shadow.jsonl"   # همتای shadow_compare.OUT_FILENAME

# آستانه‌های صرفاً هشداری (هرگز حکم را عوض نمی‌کنند)
_LOW_CONF_RATE = 0.5      # اگر کم‌تر از نیمِ رکوردها قابل‌مقایسه بود → کم‌اعتماد
_THIN_ERR_GAP = 0.05      # فاصلهٔ error_rate کم‌تر از این = برتریِ نازک
_THIN_LAT_FRAC = 0.10     # فاصلهٔ تأخیر کم‌تر از ۱۰٪ = برتریِ نازک


# ── بخشِ خالص: منطقِ تصمیم (بدونِ I/O، بدونِ importِ پروژه) ────────────────────
def _is_num(x) -> bool:
    """عددِ حقیقیِ متناهی؟ (bool و None و NaN/inf رد می‌شوند)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _strictly_worse(va, vb) -> str | None:
    """کدام سمت «بدتر» (عددِ بزرگ‌تر) است؟ تساوی/غیرقابل‌مقایسه → None.

    برای هر دو سنجه، بزرگ‌تر یعنی بدتر (error_rate بالاتر = خطای بیشتر؛
    latency بالاتر = کندتر). تساوی عمداً None است تا «بدتر» صدق نکند.
    """
    if not (_is_num(va) and _is_num(vb)):
        return None
    if va > vb:
        return "a"
    if vb > va:
        return "b"
    return None


def decide(summary: dict) -> dict:
    """حکمِ فاز ۲ را از خروجیِ summarize() صادر می‌کند. تابعِ خالص؛ هرگز خطا نمی‌دهد.

    فقط ۶ کلیدِ قراردادیِ summarize() را می‌خواند:
      count, error_rate_a/b, mean_latency_a/b_s, mean_similarity.

    برمی‌گرداند:
      {"verdict": str, "action": str, "switch_allowed": bool,
       "winner": "a"|"b"|None, "loser": "a"|"b"|None,
       "reason": str, "criterion": {...شواهدِ بند-به-بند...}}

    switch_allowed فقط و فقط در حکمِ MIGRATE برابرِ True است.
    ترتیبِ آبشار طوری است که مجموعهٔ احکام «متمانع و جامع» می‌ماند:
      (۱) count<30 → INSUFFICIENT_DATA
      (۲) sim غیرِعددی → NO_SIMILARITY_DATA
      (۳) sim<0.5 → HOLD_INVESTIGATE_DIVERGENCE  (گیتِ ایمنی، پیش از مهاجرت)
      (۴) 0.5≤sim≤0.7 → HOLD_SIMILARITY_INCONCLUSIVE  (بندِ خاکستریِ بسته)
      (۵) sim>0.7 → بازنده هست؟ MIGRATE : HOLD_NO_CLEAR_LOSER
    """
    count = summary.get("count")
    if not isinstance(count, int) or isinstance(count, bool):
        count = 0
    er_a, er_b = summary.get("error_rate_a"), summary.get("error_rate_b")
    lat_a, lat_b = summary.get("mean_latency_a_s"), summary.get("mean_latency_b_s")
    sim = summary.get("mean_similarity")

    worse_err = _strictly_worse(er_a, er_b)
    worse_lat = _strictly_worse(lat_a, lat_b)
    # بازندهٔ روشن فقط وقتی وجود دارد که «همان سمت» روی هر دو سنجه بدتر باشد
    single_loser = worse_err if (worse_err is not None and worse_err == worse_lat) else None
    winner = ("b" if single_loser == "a" else "a") if single_loser is not None else None

    trace = {
        "count": count, "min_records": MIN_RECORDS,
        "records_sufficient": count >= MIN_RECORDS,
        "mean_similarity": sim,
        "similarity_gt_0_7": (sim > SIM_MIGRATE) if _is_num(sim) else None,
        "similarity_lt_0_5": (sim < SIM_FORBID) if _is_num(sim) else None,
        "worse_error_rate": worse_err, "worse_latency": worse_lat,
        "single_loser": single_loser, "winner_side": winner,
    }

    def V(verdict, action, switch, reason, w=None, l=None):
        return {"verdict": verdict, "action": action, "switch_allowed": switch,
                "winner": w, "loser": l, "reason": reason, "criterion": trace}

    # ۱) پیش‌شرط: ≥۳۰ رکورد (فایلِ خالی/همه-خراب هم count=0 → همین‌جا)
    if count < MIN_RECORDS:
        need = max(0, MIN_RECORDS - count)
        return V("INSUFFICIENT_DATA", "collect_more", False,
                 f"{count}/{MIN_RECORDS} رکورد؛ {need} رکوردِ دیگر لازم است تا معیارِ فاز ۲ اعمال شود.")
    # ۲) similarity باید عددِ متناهی باشد تا هیچ‌کدام از دو بند ارزیابی‌شدنی باشد
    if not _is_num(sim):
        return V("NO_SIMILARITY_DATA", "investigate", False,
                 "mean_similarity=None/غیرمتناهی (در هر رکورد دستِ‌کم یک سمت خطا داده)؛ "
                 "شکستِ خطای هر پشته را بررسی کن.")
    # ۳) گیتِ ایمنیِ «سوییچ ممنوع» (بندِ ۲) — پیش از منطقِ مهاجرت
    if sim < SIM_FORBID:
        return V("HOLD_INVESTIGATE_DIVERGENCE", "investigate", False,
                 f"mean_similarity={sim} < 0.5: اول واگراییِ محتوایی بررسی شود؛ سوییچ ممنوع.",
                 w=None, l=single_loser)   # بازنده صرفاً شاهد است، نه قابلِ‌اقدام
    # ۴) بندِ خاکستریِ بستهٔ [0.5, 0.7] — BACKLOG سیاستی ندارد → توقف
    if sim <= SIM_MIGRATE:
        return V("HOLD_SIMILARITY_INCONCLUSIVE", "hold", False,
                 f"mean_similarity={sim} در بندِ بستهٔ [0.5,0.7]؛ برای مهاجرت اکیداً >0.7 لازم است.",
                 w=winner, l=single_loser)   # شاهد است؛ switch_allowed همچنان False
    # ۵) sim>0.7: مهاجرت فقط اگر یک پشته روی «هر دو» سنجه اکیداً بدتر باشد
    if single_loser is None:
        return V("HOLD_NO_CLEAR_LOSER", "hold", False,
                 f"mean_similarity={sim} > 0.7 اما هیچ پشته‌ای روی هر دو سنجه اکیداً بدتر نیست "
                 f"(err={worse_err}, lat={worse_lat}: تساوی/split/غیرقابل‌مقایسه).")
    return V("MIGRATE", "migrate", True,
             f"پشتهٔ {winner} روی هر دو سنجه (error_rate و latency) اکیداً بهتر است و similarity={sim} > 0.7. "
             f"توصیه: مهاجرت به {winner} **پشتِ یک فلگ** (هیچ سوئیچِ زنده‌ای انجام نشد).",
             w=winner, l=single_loser)


# ── بخشِ خالص: کمک‌تابع‌های تجمیع ────────────────────────────────────────────
def _rec_similarity(r: dict):
    """similarityِ عددیِ یک رکورد یا None."""
    s = (r.get("metrics") or {}).get("similarity")
    return s if _is_num(s) else None


def _side_error(r: dict, side: str):
    """نامِ نوعِ خطای یک سمت (یا None)."""
    return (r.get(side) or {}).get("error")


def _side_latency(r: dict, side: str):
    lat = (r.get(side) or {}).get("latency_s")
    return lat if _is_num(lat) else None


def _similarity_bands(records: list[dict]) -> dict:
    """توزیعِ similarityِ رکوردها بینِ بندها (شاهدِ پشتِ میانگین)."""
    bands = {"lt_0_5": 0, "mid_0_5_0_7": 0, "gt_0_7": 0, "none": 0}
    for r in records:
        s = _rec_similarity(r)
        if s is None:
            bands["none"] += 1
        elif s < SIM_FORBID:
            bands["lt_0_5"] += 1
        elif s <= SIM_MIGRATE:
            bands["mid_0_5_0_7"] += 1
        else:
            bands["gt_0_7"] += 1
    return bands


def _date_span(records: list[dict]) -> dict:
    """بازهٔ زمانیِ شواهد از فیلدِ ts (ISO). tsهای خراب رد می‌شوند.

    tsهای offset-aware به UTCِ naive نرمال می‌شوند تا min/max هرگز خطای
    «مقایسهٔ aware با naive» ندهد (تحملِ دادهٔ دست‌سازِ چند-روزهٔ مختلط).
    """
    stamps = []
    for r in records:
        ts = r.get("ts")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            stamps.append(dt)
    if not stamps:
        return {"first_ts": None, "last_ts": None, "days": None}
    first, last = min(stamps), max(stamps)
    return {"first_ts": first.isoformat(), "last_ts": last.isoformat(),
            "days": (last - first).days if len(stamps) >= 2 else None}


def _resolve_label(records: list[dict], side: str) -> str | None:
    """پرتکرارترین برچسبِ پشته (stack_a/stack_b) برای گزارشِ انسانی."""
    key = "stack_a" if side == "a" else "stack_b"
    labels = Counter(r.get(key) for r in records if isinstance(r.get(key), str))
    if not labels:
        return None
    return labels.most_common(1)[0][0]


def analyze(records: list[dict], summarizer: Callable[[list], dict] | None = None) -> dict:
    """تحلیلِ کاملِ رکوردهای تجمیع‌شده + حکمِ فاز ۲. تابعِ خالص و قطعی.

    summarizer تزریق‌پذیر است (پیش‌فرض: llm.shadow_compare.summarize) تا تست
    بدونِ وابستگی به دیکشنری‌های دستی کار کند و ماژول سطحِ بالا stdlib بماند.
    هر دسترسی دفاعی است؛ رکوردهای ناقص/غیرِدیکشنری حکم را نمی‌شکنند.
    """
    if summarizer is None:
        from llm.shadow_compare import summarize as summarizer  # importِ داخلی عمدی

    records = [r for r in records if isinstance(r, dict)]
    summary = summarizer(records)
    decision = decide(summary)
    count = summary.get("count") or 0

    # ── شواهدِ similarity ──
    sims = [s for s in (_rec_similarity(r) for r in records) if s is not None]
    similarity_n = len(sims)
    comparable_rate = round(similarity_n / count, 4) if count else None
    similarity_stats = {
        "min": round(min(sims), 4) if sims else None,
        "median": round(statistics.median(sims), 4) if sims else None,
        "max": round(max(sims), 4) if sims else None,
    }
    similarity_bands = _similarity_bands(records)
    low_confidence_similarity = bool(
        count and comparable_rate is not None and comparable_rate < _LOW_CONF_RATE)

    # ── شواهدِ خطا ──
    err_a = Counter(e for e in (_side_error(r, "a") for r in records) if e)
    err_b = Counter(e for e in (_side_error(r, "b") for r in records) if e)
    error_count_a = sum(1 for r in records if _side_error(r, "a") is not None)
    error_count_b = sum(1 for r in records if _side_error(r, "b") is not None)
    both_error_count = sum(
        1 for r in records
        if _side_error(r, "a") is not None and _side_error(r, "b") is not None)
    degenerate = {
        "stack_a_all_error": bool(count and error_count_a == count),
        "stack_b_all_error": bool(count and error_count_b == count),
    }

    # ── تأخیرِ robust (تصمیم طبقِ BACKLOG با میانگین است؛ median فقط زمینه) ──
    lat_a = [x for x in (_side_latency(r, "a") for r in records) if x is not None]
    lat_b = [x for x in (_side_latency(r, "b") for r in records) if x is not None]
    median_latency_a_s = round(statistics.median(lat_a), 6) if lat_a else None
    median_latency_b_s = round(statistics.median(lat_b), 6) if lat_b else None

    # ── تفکیکِ per-prompt (لیستِ کارِ «کجا را نگاه کنم» برای احکامِ بررسی) ──
    groups: dict[str, list] = {}
    for r in records:
        key = r.get("prompt")
        if not isinstance(key, str):
            key = "<malformed>"
        groups.setdefault(key, []).append(r)
    per_prompt = []
    for prompt, grp in groups.items():
        gs = summarizer(grp)
        gsims = [s for s in (_rec_similarity(r) for r in grp) if s is not None]
        per_prompt.append({
            "prompt": prompt,
            "n": gs.get("count"),
            "mean_similarity": gs.get("mean_similarity"),
            "min_similarity": round(min(gsims), 4) if gsims else None,
            "error_rate_a": gs.get("error_rate_a"),
            "error_rate_b": gs.get("error_rate_b"),
            "mean_latency_a_s": gs.get("mean_latency_a_s"),
            "mean_latency_b_s": gs.get("mean_latency_b_s"),
        })
    # بدترین-واگرایی اول: None (بدونِ دادهٔ مقایسه) به ابتدا، سپس similarityِ صعودی
    per_prompt.sort(key=lambda p: (
        p["mean_similarity"] if _is_num(p["mean_similarity"]) else -1.0, p["prompt"]))

    # ── متادادهٔ پوششِ شواهد ──
    runs = len({r.get("run_id") for r in records if isinstance(r.get("run_id"), str)})
    date_span = _date_span(records)
    stack_labels = {
        "a": Counter(r.get("stack_a") for r in records if isinstance(r.get("stack_a"), str)),
        "b": Counter(r.get("stack_b") for r in records if isinstance(r.get("stack_b"), str)),
    }
    pair_counter = Counter(
        (r.get("stack_a"), r.get("stack_b")) for r in records
        if isinstance(r.get("stack_a"), str) and isinstance(r.get("stack_b"), str))
    stack_pairs = sorted(
        ({"stack_a": a, "stack_b": b, "count": c} for (a, b), c in pair_counter.items()),
        key=lambda d: (-d["count"], d["stack_a"], d["stack_b"]))
    mixed_stack_pairs = len(pair_counter) > 1

    # ── حلِ برچسبِ برنده/بازنده برای گزارشِ انسانی ──
    winner_side, loser_side = decision.get("winner"), decision.get("loser")
    winner_label = _resolve_label(records, winner_side) if winner_side else None
    loser_label = _resolve_label(records, loser_side) if loser_side else None
    migration_target = winner_label if decision.get("verdict") == "MIGRATE" else None

    # ── هشدارِ نازک‌بودنِ برتری (فقط هشداری) ──
    margin_caveat = False
    if decision.get("verdict") == "MIGRATE":
        ea, eb = summary.get("error_rate_a"), summary.get("error_rate_b")
        la, lb = summary.get("mean_latency_a_s"), summary.get("mean_latency_b_s")
        if _is_num(ea) and _is_num(eb) and _is_num(la) and _is_num(lb):
            err_gap = abs(ea - eb)
            lat_frac = abs(la - lb) / max(la, lb) if max(la, lb) > 0 else 0.0
            margin_caveat = bool(err_gap < _THIN_ERR_GAP or lat_frac < _THIN_LAT_FRAC)

    # پرچمِ هشدارِ زودهنگام: دادهٔ ناکافی اما میانگینِ در-حالِ‌رشد قبلاً <0.5
    early_divergence_flag = bool(
        decision.get("verdict") == "INSUFFICIENT_DATA"
        and _is_num(summary.get("mean_similarity"))
        and summary.get("mean_similarity") < SIM_FORBID)

    analysis = {
        "summary": summary,
        "decision": decision,
        "thresholds": {"min_records": MIN_RECORDS,
                       "sim_forbid": SIM_FORBID, "sim_migrate": SIM_MIGRATE},
        "similarity_n": similarity_n,
        "comparable_rate": comparable_rate,
        "similarity_stats": similarity_stats,
        "similarity_bands": similarity_bands,
        "low_confidence_similarity": low_confidence_similarity,
        "error_types": {"a": dict(err_a), "b": dict(err_b)},
        "error_count_a": error_count_a,
        "error_count_b": error_count_b,
        "both_error_count": both_error_count,
        "degenerate": degenerate,
        "median_latency_a_s": median_latency_a_s,
        "median_latency_b_s": median_latency_b_s,
        "per_prompt": per_prompt,
        "runs": runs,
        "date_span": date_span,
        "stack_labels": {"a": dict(stack_labels["a"]), "b": dict(stack_labels["b"])},
        "stack_pairs": stack_pairs,
        "mixed_stack_pairs": mixed_stack_pairs,
        "winner_label": winner_label,
        "loser_label": loser_label,
        "migration_target": migration_target,
        "margin_caveat": margin_caveat,
        "early_divergence_flag": early_divergence_flag,
    }
    analysis["report_text"] = render_report(analysis)
    return analysis


# ── رندرِ گزارشِ دو-زبانه (خالص و قطعی؛ بدونِ ساعتِ دیواری) ────────────────────
_ACTION_NEXT = {
    "collect_more": ("baزهم shadow_compare را اجرا کن تا به ≥۳۰ رکورد برسی.",
                     "Keep running shadow_compare until >=30 records accumulate."),
    "investigate": ("خروجیِ پرامپت‌های پُرواگرایی (بالای جدولِ per-prompt) را diff کن؛ سوییچ ممنوع.",
                    "Diff outputs of the top-divergent prompts; switching is forbidden."),
    "hold": ("جمع‌آوری را ادامه بده یا ابهامِ پرامپت‌ها را کم کن.",
             "Keep collecting and/or tighten the prompts."),
    "migrate": ("فلگ را پیاده کن، برنده را پشتِ فلگ shadow کن، سپس دوباره راستی‌آزمایی.",
                "Implement the flag, shadow the winner behind it, then re-verify."),
}


def render_report(analysis: dict) -> str:
    """گزارشِ خواناندنیِ دو-زبانه از یک خروجیِ analyze(). خالص و قطعی."""
    d = analysis.get("decision") or {}
    s = analysis.get("summary") or {}
    th = analysis.get("thresholds") or {}
    verdict = d.get("verdict", "?")
    switch = d.get("switch_allowed", False)
    lines: list[str] = []
    L = lines.append

    L("=" * 68)
    L(f"  B11 فاز ۲ — حکمِ shadow: {verdict}")
    L(f"  switch_allowed = {switch}   |   action = {d.get('action')}")
    L("=" * 68)
    L("این ابزار هیچ سوئیچِ زنده‌ای نمی‌زند و هیچ سورس/فلگی را تغییر نمی‌دهد "
      "(shadow-first).")
    L("This tool performs NO live switch and edits NO source; MIGRATE is a "
      "human-owned, flag-gated recommendation only.")
    L("")
    L(f"دلیل: {d.get('reason', '')}")
    L("")

    # رکوردها و پوشش
    L(f"رکوردها: {s.get('count')}/{th.get('min_records')}  |  اجراها (runs): {analysis.get('runs')}  "
      f"|  بازه: {(analysis.get('date_span') or {}).get('days')} روز")
    if analysis.get("early_divergence_flag"):
        L("⚠ هشدارِ زودهنگام: هنوز <۳۰ رکورد، اما میانگینِ similarity قبلاً <0.5 است — سوییچ نکن.")

    # پشته‌ها
    la = _resolve_label_from_labels(analysis, "a")
    lb = _resolve_label_from_labels(analysis, "b")
    L(f"پشته‌ها: A={la}  |  B={lb}")
    if analysis.get("mixed_stack_pairs"):
        L("⚠ برچسبِ پشته‌ها بینِ اجراها یکسان نیست (mixed backends) — مقایسه apples-to-apples نیست.")

    # خطا
    L(f"error_rate: a={s.get('error_rate_a')}  b={s.get('error_rate_b')}  "
      f"(count a={analysis.get('error_count_a')} b={analysis.get('error_count_b')} "
      f"both={analysis.get('both_error_count')})")
    if analysis.get("error_types", {}).get("a") or analysis.get("error_types", {}).get("b"):
        L(f"  انواعِ خطا: a={analysis['error_types']['a']}  b={analysis['error_types']['b']}")
    deg = analysis.get("degenerate") or {}
    if deg.get("stack_a_all_error") or deg.get("stack_b_all_error"):
        L(f"  ⚠ پشتهٔ همیشه-خطا: {deg}")

    # تأخیر
    L(f"mean_latency_s: a={s.get('mean_latency_a_s')}  b={s.get('mean_latency_b_s')}  "
      f"(median a={analysis.get('median_latency_a_s')} b={analysis.get('median_latency_b_s')})")

    # similarity
    L(f"mean_similarity: {s.get('mean_similarity')}  "
      f"(آستانه‌ها: <{th.get('sim_forbid')} ممنوع، >{th.get('sim_migrate')} مهاجرت)")
    L(f"  بندها: {analysis.get('similarity_bands')}  |  "
      f"n_قابل‌مقایسه={analysis.get('similarity_n')} "
      f"(rate={analysis.get('comparable_rate')})  آماره={analysis.get('similarity_stats')}")
    if analysis.get("low_confidence_similarity"):
        L("  ⚠ کم‌اعتماد: کم‌تر از نیمِ رکوردها خروجیِ قابل‌مقایسه داشتند.")

    # برنده/بازنده
    if analysis.get("winner_label") or analysis.get("loser_label"):
        L(f"برنده={analysis.get('winner_label')}  بازنده={analysis.get('loser_label')}  "
          f"(هدفِ مهاجرت={analysis.get('migration_target')})")
    if analysis.get("margin_caveat"):
        L("  ⚠ برتریِ برنده نازک است — پیش از روشن‌کردنِ فلگ، شواهدِ بیشتری جمع کن.")

    # per-prompt worklist (۵ ردیفِ بدترین)
    pp = analysis.get("per_prompt") or []
    if pp:
        L("")
        L("per-prompt (بدترین-واگرایی اول):")
        for row in pp[:5]:
            pr = (row.get("prompt") or "")[:52]
            L(f"  sim={row.get('mean_similarity')}  min={row.get('min_similarity')}  "
              f"n={row.get('n')}  err_a={row.get('error_rate_a')} err_b={row.get('error_rate_b')}  "
              f":: {pr}")

    # اقدامِ بعدی
    fa, en = _ACTION_NEXT.get(d.get("action"), ("", ""))
    L("")
    L(f"اقدامِ بعدی: {fa}")
    L(f"Next: {en}")
    L("=" * 68)
    return "\n".join(lines)


def _resolve_label_from_labels(analysis: dict, side: str) -> str | None:
    """پرتکرارترین برچسبِ یک سمت از stack_labels (برای گزارش)."""
    labels = (analysis.get("stack_labels") or {}).get(side) or {}
    if not labels:
        return None
    return max(labels.items(), key=lambda kv: kv[1])[0]


# ── بخشِ I/O (importهای پروژه فقط این‌جا) ─────────────────────────────────────
def load_records(path=None) -> list[dict]:
    """خواندنِ رکوردهای تجمیع‌شده از JSONL. هرگز خطا نمی‌دهد.

    - path=None → outputs/llm_shadow.jsonl (از config.settings.OUTPUT_DIR).
    - فایلِ نبود → [].
    - خطوطِ خالی/خراب/غیرِدیکشنری رد می‌شوند (تعدادشان لاگ می‌شود).
    """
    if path is None:
        try:
            from config.settings import OUTPUT_DIR
            path = OUTPUT_DIR / IN_FILENAME
        except Exception as e:
            logger.error("cannot resolve OUTPUT_DIR: %s", type(e).__name__)
            return []

    records: list[dict] = []
    skipped = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    skipped += 1
                    continue
                if isinstance(obj, dict):
                    records.append(obj)
                else:
                    skipped += 1
    except FileNotFoundError:
        logger.info("no evidence file yet: %s", path)
        return []
    except OSError as e:
        logger.error("cannot read %s: %s", path, type(e).__name__)
        return []

    if skipped:
        logger.warning("skipped %d malformed line(s) in %s", skipped, path)
    return records


def main() -> int:
    import sys
    logging.basicConfig(level=logging.INFO)
    # کنسولِ ویندوز اغلب cp1252 است؛ گزارشِ فارسی باید utf-8 چاپ شود
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    records = load_records()
    analysis = analyze(records)
    print(analysis["report_text"])
    print()
    print(json.dumps({"decision": analysis["decision"], "summary": analysis["summary"]},
                     ensure_ascii=False, indent=2))
    try:
        from config.settings import OUTPUT_DIR
        print(f"\nevidence ← {OUTPUT_DIR / IN_FILENAME}")
    except Exception:
        pass
    return 0   # فقط-خواندنی/توصیه‌ای → همیشه exit 0


if __name__ == "__main__":
    raise SystemExit(main())
