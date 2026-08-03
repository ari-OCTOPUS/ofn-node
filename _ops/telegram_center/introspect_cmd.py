#!/usr/bin/env python3
"""introspect_cmd — چهار فرمانِ فقط‌خواندنیِ خودنگری برای تلگرام.

چرا یک ماژولِ جدا و نه چند تابع داخلِ `center.py`
────────────────────────────────────────────────
`center.py` ۱۳۰ کیلوبایت است و همین حالا دستِ یک نشستِ همزمان. هر خطی که
آن‌جا اضافه شود ریسکِ تداخل دارد. پس کلِ منطق این‌جاست و `center.py` فقط
**چهار خط** می‌گیرد — کوچک‌ترین دیفِ ممکن روی داغ‌ترین فایل.

    /flags    مسلح در برابرِ بارگذاری‌شده (flag_drift)
    /trace    پیام‌ها واقعاً کجا نشستند (tg_trace)
    /scan     نقاطِ کورِ خودشناسی (self_scan)
    /insight  فرضیه‌های رتبه‌بندی‌شده + نمرهٔ اجرای قبل (self_insight)

ناوردی‌ها: هیچ‌کدام چیزی را عوض نمی‌کنند · هر خطا به یک جملهٔ فارسی تبدیل
می‌شود نه استثنا · خروجی برای تلگرام بریده می‌شود (سقفِ ۴۰۹۶ نویسه‌ای که
`sendMessage` دارد؛ ردشدن از آن یعنی تلگرام **کلِ** پیام را ۴۰۰ می‌کند و
مالک هیچ‌چیز نمی‌بیند — همان «فرستادم ولی نرسید»ی که این‌ها برای شکارش‌اند).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

CARD_TITLE = "خودنگری"
TG_CAP = 3500          # حاشیهٔ امن زیرِ سقفِ ۴۰۹۶ تلگرام

# ── WS-8 · کارتِ هفتگیِ Brier ────────────────────────────────────────────────
# ⚠️ اسمِ این ثابت عمداً `FLAG` **نیست**: `capability_registry._zero_arg_card`
# هر `FLAG = "..."` ِ سطحِ ماژول را می‌خواند و کلِ کارت را «خاموش» برچسب می‌زند.
# نامِ `FLAG` این‌جا یعنی چهار فرمانِ موجودِ خودنگری هم خاموش دیده شوند — یک
# رگرسیونِ بی‌ربط. پس نامِ اختصاصی.
BRIER_FLAG = "OCTOPUS_WEEKLY_BRIER"
NO_BRIER = "—/نداریم"        # تنها چیزی که جای عدد می‌نشیند وقتی داده نیست
BRIER_LABEL = "Brier"


def _ops_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _import(name):
    root = str(_ops_root())
    if root not in sys.path:
        sys.path.insert(0, root)
    return __import__(name)


def _clip(text: str, cap: int = TG_CAP) -> str:
    text = str(text or "")
    if len(text) <= cap:
        return text
    return text[:cap - 60].rstrip() + "\n…\n(بریده شد — نسخهٔ کامل با --json روی ماشین)"


def _guard(fn, label: str) -> str:
    try:
        return _clip(fn())
    except Exception as exc:  # noqa: BLE001 — یک ابزارِ خراب نباید بات را بکشد
        return f"🚩 {label} در دسترس نیست: {type(exc).__name__}: {exc}"


# ── چهار فرمان ─────────────────────────────────────────────────────────────

def flags_text() -> str:
    def _go():
        fd = _import("flag_drift")
        root = _ops_root()
        # per-process (۲۰۲۶-۰۷-۲۹): تک‌فایل یعنی «آخرین پروسه‌ای که بوت شد» به
        # نامِ همه گزارش می‌شد. probe_all اگر snapshotی نبود، خودش به مسیرِ
        # legacy برمی‌گردد — پس این تغییر بایت‌به‌بایت امن است.
        return fd.render_all(fd.probe_all(root / "OCTOPUS-flags.cmd",
                                          root / "state"))
    return _guard(_go, "پروبِ فلگ")


def trace_text(text: str = "") -> str:
    def _go():
        tg = _import("tg_trace")
        n = next((int(p) for p in str(text).split()[1:] if p.isdigit()), 15)
        rows, stats, topics, chat = tg.trace(limit=n)
        return tg.render(rows, stats, topics, chat, limit=n)
    return _guard(_go, "ردِ ارسال")


def scan_text() -> str:
    return _guard(lambda: _import("self_scan").card(_ops_root()), "اسکنِ خودشناسی")


def insight_text() -> str:
    return _guard(lambda: _import("self_insight").card(_ops_root()), "لایهٔ بینش")


# ══════════════════════════════════════════════════════════════════════════════
# WS-8 · یک عدد در هفته: Brier — و ساختاراً ناتوان از جعلِ آن
#
# سه ایجنت در ۲۴ ساعتِ گذشته یک عددِ Brier **ساختند**. الگویشان یکی بود: عدد را
# از یک رکوردِ ذخیره‌شده (یا از هوا) برداشتند و چاپ کردند، بی‌آنکه جفت‌هایی که
# آن عدد را می‌سازند وجود داشته باشند. پس این کارت طوری نوشته می‌شود که آن کار
# را **نتواند** بکند:
#
#   ۱) عدد هرگز از رکورد خوانده نمی‌شود. از `graded` (فهرستِ (confidence, y))
#      دوباره **محاسبه** می‌شود. جفت نباشد ⇒ عددی نیست که چاپ شود.
#   ۲) اگر رکورد هم عددی داشت، با محاسبهٔ ما مقایسه می‌شود. اختلاف > 1e-6 ⇒
#      کارت **امتناع** می‌کند و اختلاف را اعلام می‌کند (نه اینکه یکی را بردارد).
#   ۳) هر جفتِ بدشکل (y بیرونِ {0,1}، confidence بیرونِ [0,1]، غیرعددی) کلِ
#      محاسبه را باطل می‌کند — نه اینکه بی‌صدا کنار گذاشته شود.
#   ۴) تنها جای فرمت‌کردنِ عدد `_fmt` است و فقط پشتِ `has_data` صدا زده می‌شود.
#
# وضعِ سنجیده‌شدهٔ امروز (۲۰۲۶-۰۸-۰۱): `state/cortex/self-claims.jsonl` وجود
# ندارد ⇒ صفر ادعا ⇒ صفر جفت ⇒ Brier واقعی `None`. کارت همین را می‌گوید.
# ══════════════════════════════════════════════════════════════════════════════

def _num(x):
    """عدد یا None. bool عمداً رد می‌شود (True==1 در پایتون یک تلهٔ کلاسیک است)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    f = float(x)
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def brier_stats(probe_result, history=None) -> dict:
    """**تابعِ خالص**: از خروجیِ `calibration_probe.probe` یک وضعیتِ صادق بساز.

    خروجی: {has_data, reason, n, brier, base_rate, baseline_brier, verdict,
             prev_brier, prev_ts, trend, n_claims, truth_rows}
    `has_data=False` ⇒ `brier is None` — همیشه، بی‌استثنا.
    """
    st = {"has_data": False, "reason": "no-probe", "n": 0, "brier": None,
          "base_rate": None, "baseline_brier": None, "verdict": None,
          "prev_brier": None, "prev_ts": None, "trend": None,
          "n_claims": None, "truth_rows": None, "mismatch": None}
    if not isinstance(probe_result, dict):
        return st
    st["n_claims"] = probe_result.get("n_claims")
    st["truth_rows"] = probe_result.get("truth_rows")
    graded = probe_result.get("graded")
    if not isinstance(graded, list) or not graded:
        st["reason"] = "no-pairs"
        return st
    pairs = []
    for g in graded:
        if not isinstance(g, dict):
            st["reason"] = "bad-pairs"
            return st
        c, y = _num(g.get("confidence")), _num(g.get("y"))
        if c is None or y is None or not (0.0 <= c <= 1.0) or y not in (0.0, 1.0):
            st["reason"] = "bad-pairs"
            return st
        pairs.append((c, y))
    n = len(pairs)
    brier = sum((c - y) ** 2 for c, y in pairs) / n
    rec = _num(probe_result.get("brier"))
    if rec is not None and abs(rec - brier) > 1e-6:
        st["reason"] = "mismatch"
        st["mismatch"] = (round(rec, 6), round(brier, 6))
        return st
    base_rate = sum(y for _c, y in pairs) / n
    baseline = sum((base_rate - y) ** 2 for _c, y in pairs) / n
    st.update({"has_data": True, "reason": "ok", "n": n,
               "brier": round(brier, 6), "base_rate": round(base_rate, 6),
               "baseline_brier": round(baseline, 6),
               "verdict": ("better" if brier < baseline - 1e-9 else
                           "worse" if brier > baseline + 1e-9 else "equal")})
    # روند — تنها منبعِ ممکن، رکوردِ اسنپ‌شاتِ قبلی است (فهرستِ جفت‌ها ذخیره
    # نمی‌شود). پس صریحاً «ثبت‌شده» برچسب می‌خورد، نه «بازسنجیده».
    prev = None
    for row in reversed(list(history or [])):
        if not isinstance(row, dict):
            continue
        pn, pb = row.get("n"), _num(row.get("brier"))
        if not isinstance(pn, int) or pn < 1 or pb is None or not (0.0 <= pb <= 1.0):
            continue
        if row.get("ts") and row.get("ts") == probe_result.get("ts"):
            continue                       # خودِ همین اجرا، نه «قبلی»
        prev = (pb, row.get("ts"))
        break
    if prev:
        st["prev_brier"], st["prev_ts"] = prev[0], prev[1]
        st["trend"] = round(brier - prev[0], 6)
    return st


def _fmt(x) -> str:
    """تنها جایی که یک عددِ Brier به رشته تبدیل می‌شود."""
    return f"{float(x):.4f}"


_REASON_FA = {
    "no-probe": "پروبِ واسنجی اصلاً اجرا نشد.",
    "no-pairs": "هیچ جفتِ (ادعا، نتیجه)ای وجود ندارد.",
    "bad-pairs": "جفت‌ها بدشکل‌اند (y خارج از {۰،۱} یا اطمینانِ نامعتبر) — عدد باطل است.",
    "mismatch": "عددِ ثبت‌شده با بازمحاسبه از جفت‌ها نمی‌خوانَد — چاپ نمی‌شود.",
}


def brier_card(probe_result, history=None) -> str:
    """**تابعِ خالص**: کارتِ هفتگی. بی‌داده ⇒ جملهٔ صادق، هرگز عدد."""
    st = brier_stats(probe_result, history)
    head = f"📉 <b>سنجهٔ هفته — {BRIER_LABEL}</b> (راست‌گویی؛ پایین‌تر بهتر)"
    if not st["has_data"]:
        out = [head, f"{BRIER_LABEL}: {NO_BRIER}",
               "علت: " + _REASON_FA.get(st["reason"], str(st["reason"]))]
        if st["reason"] == "mismatch" and st["mismatch"]:
            out.append(f"ثبت‌شده {st['mismatch'][0]} · بازمحاسبه {st['mismatch'][1]}")
        cl, tr = st["n_claims"], st["truth_rows"]
        out.append("ادعاهای خوانده‌شده: " + ("?" if cl is None else str(cl))
                   + " · ردیفِ حقیقت: " + ("?" if tr is None else str(tr)))
        out.append("▸ نکنی: هیچ — نبودِ عدد خودش خبر است، نه خطا.")
        return "\n".join(out)
    cmp_fa = {"better": "بهتر از حدسِ کور", "worse": "بدتر از حدسِ کور",
              "equal": "دقیقاً هم‌اندازهٔ حدسِ کور"}[st["verdict"]]
    out = [head,
           f"{BRIER_LABEL}: <b>{_fmt(st['brier'])}</b> روی {st['n']} جفت",
           f"حدسِ ثابتِ نرخِ پایه ({_fmt(st['base_rate'])}): "
           f"{_fmt(st['baseline_brier'])} ⇒ {cmp_fa}"]
    if st["trend"] is None:
        out.append("روند: اولین اندازه‌گیری — هنوز روندی نیست.")
    else:
        arrow = "↓ بهتر" if st["trend"] < 0 else ("↑ بدتر" if st["trend"] > 0 else "= بی‌تغییر")
        out.append(f"روند: {arrow} {_fmt(abs(st['trend']))} نسبت به "
                   f"{st['prev_ts'] or 'اسنپ‌شاتِ قبل'} (عددِ قبلی ثبت‌شده است، "
                   "نه بازسنجیده)")
    if st["verdict"] == "worse":
        out.append("▸ یعنی اطمینان‌های اعلام‌شده از یک حدسِ ثابت هم بی‌خاصیت‌ترند.")
    return "\n".join(out)


def _brier_sources():
    """(probe_result, history) از دادهٔ زنده — فقط‌خواندنی، صفر نوشتن."""
    root = _ops_root()
    for p in (str(root / "cortex"), str(root / "budget"), str(root)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import calibration_probe as cp
    res = cp.probe(persist=False)          # persist=False ⇒ هیچ فایلی نوشته نمی‌شود
    hist = []
    try:
        import json as _j
        for ln in cp.HISTORY.read_text("utf-8", errors="replace").splitlines()[-200:]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = _j.loads(ln)
            except ValueError:
                continue
            if isinstance(r, dict):
                hist.append(r)
    except OSError:
        hist = []
    return res, hist


def brier_text() -> str:
    """کارتِ Brier از دادهٔ زنده. هر خطا ⇒ یک جملهٔ فارسی (مثلِ بقیهٔ این ماژول)."""
    return _guard(lambda: brier_card(*_brier_sources()), "کارتِ Brier")


def _brier_on() -> bool:
    return str(os.environ.get(BRIER_FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}


def card() -> str:
    """کارتِ خلاصه — برای کشفِ خودکار توسطِ capability_registry.

    فلگِ `OCTOPUS_WEEKLY_BRIER` خاموش ⇒ رشتهٔ برگشتی **بایت‌به‌بایتِ** دیروز."""
    base = ("🔎 خودنگری\n"
            "  /flags    مسلح در برابرِ بارگذاری‌شده\n"
            "  /trace    پیام‌ها کجا نشستند\n"
            "  /scan     نقاطِ کور\n"
            "  /insight  فرضیه‌ها + نمرهٔ اجرای قبل")
    if not _brier_on():
        return base
    return base + "\n\n" + brier_text()


if __name__ == "__main__":  # pragma: no cover — اجرای دستی
    which = sys.argv[1] if len(sys.argv) > 1 else "card"
    print({"flags": flags_text, "trace": lambda: trace_text(""),
           "scan": scan_text, "insight": insight_text,
           "brier": brier_text,
           "card": card}.get(which, card)())
