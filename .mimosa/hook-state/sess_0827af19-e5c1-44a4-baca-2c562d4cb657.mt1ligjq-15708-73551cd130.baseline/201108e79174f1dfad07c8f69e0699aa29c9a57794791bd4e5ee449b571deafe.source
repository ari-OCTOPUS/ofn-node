#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""coherence.py — پروبِ انسجام: شکارِ ادعاهایی که نمی‌توانند غلط باشند.

═══ چرا این فایل هست ═══
جلسهٔ ۲۰۲۶-۰۷-۲۵ نُه نقص را با عدد گرفت و همه یک بیماری بودند:

  phi=300               → سقفِ محاسباتیِ خودش، نه حیاتِ اندام (p_later کفِ 1e-300)
  σ=1.00                → گرافِ بی‌یال، خوانده‌شده به‌عنوان «critical»
  Δ_self clamp→0        → عددِ منفیِ واقعی (-0.027، n=536) پنهان می‌شد
  deadline_proximity    → ددلاینِ گذشته فشار را تا ابد روی ۰.۹۹۸ قفل می‌کرد
  fugu_quota.fail       → timeoutِ محلی را «شکستِ فروشنده» می‌شمرد (۱۵/۱۵)
  outward_locked        → regexش قالبِ پرنشدهٔ خودش را match می‌کرد → گیتِ باز = «بسته»
  approvals.jsonl       → ۱۴ ردیفِ ساختگیِ actor=owner در ردِ تأییدِ انسانی
  «171 tests green»     → سند، در حالی که شمارشِ ایستا ۱۸۹+ و اسکن ۲۰۷ داد
  «standalone git repo» → پوشه‌ای با صفر `.git`

هیچ‌کدام «باگ» به معنای متعارف نبودند. همه **ادعاهایی بودند که راهِ غلط‌بودن
نداشتند** — عددی که فقط خودش را می‌سنجید، یا سندی که هیچ‌چیز آن را رد نمی‌کرد.
قاعدهٔ ۱ دفترِ تز («هیچ ردیفی بدونِ شرطِ مرگ») پادزهرِ همان است، ولی روی ردیف‌های
دفتر اعمال می‌شود نه روی خودِ ارگانیسم. این ماژول همان قاعده را به کلِ بدن می‌برد.

═══ چه چیزی هست و چه چیزی نیست ═══
هست: یک پروبِ **فقط‌خواندنیِ** fail-soft که برای هر ادعای سنجش‌پذیر می‌پرسد
«این می‌تواند غلط باشد؟» و اگر نه، دلیلش را با مسیرِ شاهد برمی‌گرداند.
نیست: مانیتورِ سلامت. سالم/ناسالم بودنِ سیستم را نمی‌سنجد — فقط **صادق بودنِ
حرف‌هایش** را. یک ارگانیسمِ بیمار می‌تواند کاملاً منسجم باشد، و یک ارگانیسمِ سالم
می‌تواند دربارهٔ خودش دروغ بگوید. این دومی را می‌گیرد.

هرگز چیزی نمی‌نویسد، هرگز raise نمی‌کند، هرگز فایلِ راز/PII نمی‌خواند.
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

FLAG = "OCTOPUS_WIRE_COHERENCE"

_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state"

# ── واژگانِ حکم ─────────────────────────────────────────────────────────────
#   ok                  ادعا می‌تواند غلط باشد و شاهدش با آن سازگار است
#   saturated           عدد به سقف/کفِ محاسباتیِ خودش چسبیده ⇒ اندازه‌گیری نیست
#   degenerate          سنسور بی‌ورودی عدد می‌دهد ⇒ نبودِ داده را با سیگنال عوض کرده
#   self_referential    سنجه عمدتاً از خروجیِ خودِ سیستم ساخته شده
#   clamped             علامت/بازه ساختاراً محدود شده ⇒ ردِ ادعا ممکن نیست
#   drift               سند و کد دو عدد می‌دهند
#   provenance_missing  شاهد وجود دارد ولی منشأش قابلِ تشخیص نیست
#   unfalsifiable       ادعا شرطِ مرگ ندارد
#   no_input            ورودیِ چک پیدا نشد ⇒ چک اجرا نشد (و این را پنهان نمی‌کنیم)
VERDICTS = ("ok", "stale", "saturated", "degenerate", "self_referential", "clamped",
            "drift", "provenance_missing", "unfalsifiable", "no_input", "unknown")


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:  # noqa: BLE001 — پروب هرگز نمی‌شکند
        return default


def _f(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _finding(cid, verdict, claim, why, evidence=None, thesis_row=None, value=None,
             age_h=None):
    return {"id": cid, "verdict": verdict, "claim": claim, "why": why,
            "evidence": evidence or [], "thesis_row": thesis_row, "value": value,
            "age_h": (round(age_h, 2) if isinstance(age_h, (int, float)) else None)}


# ── ضدِ «سبز از راهِ نبود» ───────────────────────────────────────────────────
# نسخهٔ اولِ همین فایل چهار چک را **بی‌صدا** رد کرد چون مسیر/کلید را اشتباه حدس
# زده بودم، و گزارش «۵ چک» داد که شبیهِ موفقیت بود. این دقیقاً همان بیماری‌ای است
# که این ماژول شکارش می‌کند، در خودش. پس: نبودِ ورودی **یافته** است، نه سکوت.
def _find_key(obj, key, _depth=0):
    """کلید را در هر عمقی پیدا می‌کند (اولین تطابق). None اگر نبود."""
    if _depth > 6 or obj is None:
        return None
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = _find_key(v, key, _depth + 1)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj[:40]:
            r = _find_key(v, key, _depth + 1)
            if r is not None:
                return r
    return None


# ── ضدِ کهنگی ───────────────────────────────────────────────────────────────
# نسخهٔ دومِ همین فایل `deadline_proximity = 0.182 (10d)` را «ok» اعلام کرد، در
# حالی که ارگانیسمِ زنده ۰.۹۹۸ و `-5d` داشت: `_locate` یک اسنپ‌شاتِ **۱۵ روز
# کهنه** را خوانده بود. پروبی که روی دادهٔ کهنه حکم می‌دهد، خودش همان ادعای
# غیرِابطال‌پذیری را می‌سازد که شکارش می‌کند. پس سنِ شاهد بخشی از حکم است.
STALE_AFTER_H = 6.0


def _age_h(p: Path) -> "float | None":
    try:
        import time as _t
        return (_t.time() - p.stat().st_mtime) / 3600.0
    except OSError:
        return None


def _locate(state_dir: Path, key: str, candidates: "list[str]"):
    """(value, path, age_h) از **تازه‌ترین** کاندیدی که کلید را دارد.

    ترتیبِ کاندیدها اولویت نمی‌دهد — سنِ فایل می‌دهد. وگرنه یک اسنپ‌شاتِ کهنه
    که اتفاقاً کلید را دارد، دادهٔ زنده را پنهان می‌کند."""
    hits = []
    for rel in candidates:
        p = state_dir / rel
        d = _read_json(p)
        if d is None:
            continue
        v = _find_key(d, key)
        if v is not None:
            hits.append((_age_h(p) if _age_h(p) is not None else 1e9, v, p))
    if not hits:
        return None, None, None
    hits.sort(key=lambda t: t[0])
    age, v, p = hits[0]
    return v, p, age


def _no_input(cid, key, candidates, thesis_row=None):
    return _finding(
        cid, "no_input", f"کلیدِ «{key}» در هیچ‌کدام از کاندیدها پیدا نشد",
        "این چک اجرا نشد. سکوت به‌جای گزارش، همان «سبز از راهِ نبود» است — پس "
        "صریحاً ثبت می‌شود تا شمارِ چک‌ها با شمارِ چک‌های واقعاً اجراشده اشتباه نشود.",
        [str(c) for c in candidates], thesis_row)


# ── ۱ · اشباع: عددی که به سقفِ محاسباتیِ خودش چسبیده ────────────────────────
def check_saturation(state_dir: Path) -> list:
    """phi-accrual روی سقف = اعلامِ مرگ بر مبنای اشباع، نه اندازه‌گیری.

    مرجعِ عددی: `p_later` کفِ 1e-300 دارد ⇒ phi سقفش ۳۰۰ است. هر phi≈۳۰۰
    یعنی «فاصله از سقف قابلِ تشخیص نیست»، نه «اندام مرده است»."""
    CAND = ["ORGANISM-STATE.json", "cortex/cortex-state.json",
            "pulse/heartstate-latest.json", "legs/lead-naghshi-last-failure.json"]
    CEIL = 300.0
    v, path, age = _locate(state_dir, "phi", CAND)
    if v is None:
        return [_no_input("saturation:phi", "phi", CAND, "phi-liveness")]
    f = _f(v)
    if f is None:
        return [_no_input("saturation:phi", "phi(عددی)", CAND, "phi-liveness")]
    if f >= CEIL - 0.5:
        return [_finding(
            "saturation:phi", "saturated", f"phi = {f}",
            f"سقفِ محاسباتیِ phi همین {CEIL} است (p_later کفِ 1e-300). عدد روی سقف "
            f"یعنی «تفاوت قابلِ تشخیص نیست»، نه یک اندازه‌گیریِ واقعی — و بر همین "
            f"مبنا ۶۶ ری‌استارتِ self-heal شلیک شد.",
            [str(path)], "phi-liveness", f, age)]
    return [_finding("saturation:phi", "ok", f"phi = {f}",
                     f"زیرِ سقفِ {CEIL} ⇒ عدد اطلاعات دارد.",
                     [str(path)], "phi-liveness", f, age)]


# ── ۲ · دژنره: سنسورِ بی‌ورودی که عدد می‌دهد ────────────────────────────────
def check_degenerate_sensor(state_dir: Path) -> list:
    """σ روی گرافی که یال ندارد. gap=0 و σ=1 از **نبودِ داده** می‌آید نه بحران."""
    CAND = ["cortex/cortex-state.json", "doctor/box-latest.json",
            "pulse/heartstate-latest.json", "export/octopus-status-bundle.json"]
    sigma, path, age = _locate(state_dir, "sigma", CAND)
    if sigma is None:
        return [_no_input("degenerate:sigma", "sigma", CAND, "spectral-sigma")]
    sv = _f(sigma)
    if sv is None:
        return [_no_input("degenerate:sigma", "sigma(عددی)", CAND, "spectral-sigma")]
    d = _read_json(path) or {}
    gap = _f(_find_key(d, "spectral_gap"))
    if gap is None:
        gap = _f(_find_key(d, "gap"))
    edges = _find_key(d, "n_edges")
    n = _find_key(d, "n_nodes")
    degenerate = ((gap is not None and abs(gap) < 1e-9)
                  or (isinstance(edges, int) and edges == 0)
                  or (isinstance(n, int) and n < 2))
    if degenerate:
        return [_finding(
            "degenerate:sigma", "degenerate", f"σ = {sv} (gap={gap}, edges={edges}, n={n})",
            "گرافِ رویداد یال ندارد — یال فقط از خطا ساخته می‌شود، پس ارگانیسمِ "
            "بی‌خطا گرافِ تهی دارد. σ در این حالت نبودِ داده را با بحران عوض می‌کند؛ "
            "همان چیزی که ۸ RFCِ بایت‌به‌بایت‌یکسان ساخت.",
            [str(path)], "spectral-sigma", sv, age)]
    if gap is None and edges is None and n is None:
        # بارِ سومِ همان درس، این‌بار در خودِ این چک: بی‌شکلِ گراف نمی‌توانم
        # دژنره‌بودن را **رد** کنم. σ=0.0 (نه ۱.۰) نشانهٔ خوبی است چون حالتِ دژنره
        # σ=1.0 می‌داد — ولی «نشانهٔ خوب» با «تأیید» یکی نیست.
        return [_finding(
            "degenerate:sigma", "no_input",
            f"σ = {sv} ولی شکلِ گراف (gap/edges/n) در هیچ کاندیدی نبود",
            "σ=0.0 دلگرم‌کننده است چون حالتِ دژنره σ=1.0 می‌داد، ولی بدونِ شکلِ گراف "
            "نمی‌توانم دژنره‌نبودن را اثبات کنم. «نشانهٔ خوب» ≠ «تأیید».",
            [str(path)], "spectral-sigma", sv, age)]
    return [_finding("degenerate:sigma", "ok", f"σ = {sv} (gap={gap})",
                     "گراف غیرِتهی ⇒ σ معنا دارد.", [str(path)], "spectral-sigma", sv, age)]


# ── ۳ · خودمرجعی و clamp: سنجهٔ سرعت که از ضربانِ خودش ساخته شده ────────────
def check_self_reference(state_dir: Path) -> list:
    CAND = ["pulse/heart-shadow-latest.json", "pulse/heart-signals-latest.json",
            "pulse/heartstate-latest.json", "export/octopus-status-bundle.json"]
    out = []
    share, sp, age = _locate(state_dir, "metronome_share", CAND)
    if share is None:
        out.append(_no_input("selfref:metronome", "metronome_share", CAND,
                             "metronome-guard"))
    else:
        sv = _f(share)
        d = _read_json(sp) or {}
        auth = _find_key(d, "authoritative")
        selfref = _find_key(d, "self_referential")
        if sv is not None and sv > 0.9 and auth is True:
            out.append(_finding(
                "selfref:metronome", "self_referential",
                f"metronome_share = {sv} ولی authoritative = True",
                "بیش از ۹۰٪ استریم از ضربانِ خودِ سیستم است. سنجه‌ای که عمدتاً "
                "خروجیِ خودش را می‌خورد نمی‌تواند معتبر اعلام شود.",
                [str(sp)], "metronome-guard", sv, age))
        else:
            out.append(_finding(
                "selfref:metronome", "ok",
                f"metronome_share = {sv}, authoritative = {auth}, self_referential = {selfref}",
                "گارد کار می‌کند: سهمِ بالای متروَنوم به authoritative=False می‌رسد.",
                [str(sp)], "metronome-guard", sv, age))

    raw, dp, age = _locate(state_dir, "delta_self_raw", CAND)
    if raw is None:
        raw, dp, age = _locate(state_dir, "delta_self", CAND)
    if raw is None:
        out.append(_no_input("clamped:delta_self", "delta_self", CAND, "delta-self"))
        return out
    rv = _f(raw)
    d = _read_json(dp) or {}
    pubv = _f(_find_key(d, "delta_self_live"))
    if rv is not None and rv < -1e-9 and pubv is not None and abs(pubv) < 1e-9:
        out.append(_finding(
            "clamped:delta_self", "clamped",
            f"delta_self خام {rv} ولی منتشرشده {pubv}",
            "clamp عددِ منفی را به صفر می‌بَرد، پس ادعای «دسترسیِ درونی کمک می‌کند» "
            "هرگز قابلِ ردکردن نیست. عددِ منفی خودش نتیجه است، نه خطا.",
            [str(dp)], "delta-self", rv, age))
    else:
        out.append(_finding(
            "clamped:delta_self", "ok", f"delta_self = {rv}",
            "علامت صادقانه منتشر می‌شود (منفی هم مجاز است) ⇒ ادعا ابطال‌پذیر است. "
            + (f"و امروز واقعاً منفی است ({rv}) — یعنی clamp برداشته شده."
               if (rv is not None and rv < 0) else ""),
            [str(dp)], "delta-self", rv, age))
    return out


# ── ۴ · فوریتِ ابدی: ددلاینی که گذشته و هنوز فشار می‌سازد ──────────────────
def check_expired_urgency(state_dir: Path) -> list:
    CAND = ["ORGANISM-STATE.json", "cortex/self-model.json",
            "export/octopus-status-bundle.json"]
    prox, path, age = _locate(state_dir, "deadline_proximity", CAND)
    if prox is None:
        return [_no_input("expired:urgency", "deadline_proximity", CAND,
                          "metabolic-budget")]
    pv = _f(prox)
    d = _read_json(path) or {}
    ref = str(_find_key(d, "deadline_ref") or "")
    m = re.search(r"\((-?\d+)d\)", ref)
    days = int(m.group(1)) if m else None
    if pv is not None and days is not None and days < 0 and pv > 0.5:
        return [_finding(
            "expired:urgency", "saturated",
            f"deadline_proximity = {pv} از ددلاینِ {days} روز گذشته ({ref})",
            "سیگموید برای «۱۴ روزِ پایانی» طراحی شده و برای days<0 انقضا ندارد؛ با "
            "گذرِ زمان به ۱.۰ می‌رود و همان‌جا می‌ماند. و چون pressure = max(...)، این "
            "تِرم سیگنال را **اشباع** می‌کند: یک اضطرارِ واقعی (FREEZE/halt) هم دیگر "
            "نمی‌تواند فشار را بالا ببرد — گاورنرِ آلوستاتیک توانِ واکنش را از دست می‌دهد.",
            [str(path), "_ops/budget/budgets.yaml"], "metabolic-budget", pv, age)]
    return [_finding("expired:urgency", "ok",
                     f"deadline_proximity = {pv} ({ref or 'بی‌ددلاین'})",
                     "ددلاینِ گذشته فوریت نمی‌سازد.", [str(path)],
                     "metabolic-budget", pv, age)]


# ── ۵ · شکستی که مالِ فروشنده نیست ─────────────────────────────────────────
def check_failure_attribution(state_dir: Path) -> list:
    """۱۵ از ۳۰ فراخوانِ پولی روی سقفِ سوکتِ خودمان مرد، و kill-switch آن را
    «شکستِ فروشنده» شمرد. اگر همهٔ شکست‌ها یک نوع باشند و آن نوع timeout باشد،
    شمارنده دربارهٔ فروشنده حرفی نمی‌زند."""
    out = []
    p = state_dir / "paid-calls.jsonl"
    try:
        rows = [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]
    except Exception:  # noqa: BLE001
        return out
    if not rows:
        return out
    bad = [r for r in rows if not r.get("ok")]
    if not bad:
        out.append(_finding("attribution:paid", "ok", f"{len(rows)} فراخوان، صفر شکست",
                            "چیزی برای انتساب نیست.", ["state/paid-calls.jsonl"]))
        return out
    kinds = {str(r.get("error") or "?") for r in bad}
    timeouts = [r for r in bad if "timeout" in str(r.get("error") or "").lower()]
    if len(timeouts) == len(bad) and len(bad) >= 3:
        # نسخهٔ اول کلِ پراکندگی را می‌گرفت و چون لاگ **دو رژیمِ سقف** دارد
        # (۴۵s و بعد ۲۰s) عددِ گمراه‌کننده می‌داد. درست: خوشه‌بندی به دیوارها و
        # سنجشِ پراکندگیِ *درونِ* هر دیوار — امضای سقفِ ثابت همان است.
        ms = sorted(_f(r.get("ms"), 0) or 0 for r in timeouts)
        walls: dict = {}
        for x in ms:
            walls.setdefault(round(x / 5000.0), []).append(x)
        worst = 0.0
        for grp in walls.values():
            if len(grp) >= 2:
                worst = max(worst, (grp[-1] - grp[0]) / max(1.0, grp[-1]))
        spread = worst
        out.append(_finding(
            "attribution:paid", "degenerate",
            f"{len(bad)}/{len(rows)} شکست، همه از نوع {kinds}",
            f"هیچ خطای واقعیِ فروشنده وجود ندارد (صفر ۴۰۱/۵xx). و پراکندگیِ زمانِ "
            f"شکست‌ها درونِ هر دیوار {spread:.1%} است ({len(walls)} دیوارِ متمایز) ⇒ روی "
            f"سقف‌های ثابت مرده‌اند، که امضای "
            f"سقفِ محلی است نه بی‌ثباتیِ فروشنده. شمارنده‌ای که این را «شکستِ "
            f"فروشنده» بشمارد، ساعتِ خودمان را می‌سنجد.",
            ["state/paid-calls.jsonl"], None, len(bad)))
    else:
        out.append(_finding("attribution:paid", "ok",
                            f"{len(bad)}/{len(rows)} شکست، انواع: {kinds}",
                            "شکست‌ها یک‌جنس نیستند ⇒ انتساب معنا دارد.",
                            ["state/paid-calls.jsonl"], None, len(bad)))
    return out


# ── ۶ · گیتی که قالبِ پرنشدهٔ خودش را «ثبت‌شده» می‌خواند ────────────────────
def check_gate_matches_own_template(root: Path) -> list:
    """`outward_locked` با `Branch\\s*A\\b` قالبِ «Branch A/B» را match می‌کرد.
    الگوی عمومی: هر گیتی که با regex دنبالِ «ثبت» می‌گردد و placeholder را می‌گیرد."""
    out = []
    src = root / "03 - Projects" / "اونلی فنز" / "langar" / "langar_bot.py"
    doc = root / "03 - Projects" / "اونلی فنز" / "PROJECT.md"
    try:
        code = src.read_text("utf-8")
        text = doc.read_text("utf-8")
    except Exception:  # noqa: BLE001
        return out
    fixed = "(?!\\s*/)" in code and "___" in code
    tmpl = [ln for ln in text.splitlines() if "Branch A" in ln and "___" in ln]
    if tmpl and not fixed:
        out.append(_finding(
            "gate:self_template", "degenerate",
            "outward_locked() قالبِ پرنشدهٔ خودش را «ثبت‌شده» می‌خواند",
            "خطِ PROJECT.md هنوز `___` دارد (پرنشده) ولی regex آن را match می‌کند، "
            "پس گیتِ **باز** خودش را «بسته» گزارش می‌کند. fail-open روی گیتِ ایمنی.",
            [str(src), str(doc)], "effect-gate-once"))
    else:
        out.append(_finding(
            "gate:self_template", "ok",
            "outward_locked() قالبِ پرنشده را رد می‌کند",
            "لُکاهدِ منفی + شرطِ نبودِ `___` ⇒ پیش‌فرض قفل، و قالب باز نمی‌کند.",
            [str(src)], "effect-gate-once"))
    return out


# ── ۷ · شاهدِ بی‌منشأ: ردیفی که نمی‌دانیم واقعی است یا تست ─────────────────
def check_evidence_provenance(root: Path) -> list:
    out = []
    p = root / "03 - Projects" / "اونلی فنز" / "langar" / "approvals.jsonl"
    try:
        rows = [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]
    except Exception:  # noqa: BLE001
        return out
    if not rows:
        return out
    unmarked = [r for r in rows if "origin" not in r]
    human = [r for r in unmarked if str(r.get("actor")) in ("owner", "operator")]
    if human:
        out.append(_finding(
            "provenance:approvals", "provenance_missing",
            f"{len(unmarked)}/{len(rows)} ردیفِ بی‌مهرِ منشأ، {len(human)} با actorِ انسانی",
            "ردِ حسابرسیِ «تأییدِ انسانی» بدونِ مهرِ منشأ نمی‌تواند ردیفِ تست را از "
            "ردیفِ واقعی جدا کند. و جدولِ رأیِ واقعی صفر ردیف دارد، پس این فایل تنها "
            "چیزی است که شبیهِ مدرکِ تأیید به‌نظر می‌رسد — بی‌آنکه بشود ردش کرد.",
            [str(p)], None, len(human)))
    else:
        out.append(_finding("provenance:approvals", "ok",
                            f"{len(rows)} ردیف، همه مهرِ منشأ دارند",
                            "ردیفِ ساختگی از واقعی قابلِ تفکیک است.", [str(p)]))
    return out


# ── ۸ · drift: عددی که سند می‌گوید و کد نمی‌گوید ────────────────────────────
def check_doc_drift(targets: list) -> list:
    """هر (سند، الگوی عدد، شمارشِ ایستا) که با هم نخواند."""
    out = []
    for label, doc_path, pattern, counted in targets:
        try:
            txt = Path(doc_path).read_text("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        claims = {int(m) for m in re.findall(pattern, txt)}
        if not claims:
            continue
        if counted is not None and all(c != counted for c in claims):
            out.append(_finding(
                f"drift:{label}", "drift",
                f"سند می‌گوید {sorted(claims)}، شمارشِ ایستا {counted}",
                "عددی که هیچ‌چیز آن را دوباره نمی‌سنجد، به‌مرورِ زمان از کد جدا "
                "می‌شود و بعد به‌عنوان واقعیت نقل می‌شود.",
                [str(doc_path)], None, counted))
        else:
            out.append(_finding(f"drift:{label}", "ok",
                                f"سند {sorted(claims)} = شمارش {counted}",
                                "سند با کد می‌خواند.", [str(doc_path)], None, counted))
    return out


# ── ۹ · ادعای بی‌شرطِ مرگ در دفترِ تز ──────────────────────────────────────
def check_thesis_falsifiability(state_dir: Path) -> list:
    out = []
    d = _read_json(state_dir / "thesis" / "thesis-ledger.json")
    if not isinstance(d, dict):
        return out
    rows = d.get("rows") or []
    bad = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        kill = str(r.get("kill") or "").strip().strip("—-— ")
        if len(kill) < 12 and str(r.get("status")) != "UNFALSIFIABLE_AS_STATED":
            bad.append(str(r.get("id")))
    if bad:
        out.append(_finding(
            "thesis:falsifiability", "unfalsifiable",
            f"{len(bad)} ردیف بی‌شرطِ مرگ: {bad[:4]}",
            "قاعدهٔ ۱ دفتر: ادعایی که راهِ ابطال ندارد ادعا نیست.",
            ["state/thesis/thesis-ledger.json"], None, len(bad)))
    else:
        out.append(_finding(
            "thesis:falsifiability", "ok",
            f"{len(rows)} ردیف، همه شرطِ مرگ دارند (یا صریحاً UNFALSIFIABLE علامت خورده‌اند)",
            "قاعدهٔ ۱ برقرار است.", ["state/thesis/thesis-ledger.json"], None, len(rows)))
    return out


# ── جمع‌بندی ───────────────────────────────────────────────────────────────
def run(root: "Path | None" = None, state_dir: "Path | None" = None) -> dict:
    """همهٔ چک‌ها. هرگز raise نمی‌کند. خروجی: {findings, counts, dishonest}."""
    root = Path(root) if root else _HERE.parent
    sd = Path(state_dir) if state_dir else STATE
    findings: list = []
    for fn, args in ((check_saturation, (sd,)), (check_degenerate_sensor, (sd,)),
                     (check_self_reference, (sd,)), (check_expired_urgency, (sd,)),
                     (check_failure_attribution, (sd,)),
                     (check_gate_matches_own_template, (root,)),
                     (check_evidence_provenance, (root,)),
                     (check_thesis_falsifiability, (sd,))):
        try:
            findings.extend(fn(*args))
        except Exception as e:  # noqa: BLE001 — یک چکِ شکسته بقیه را نمی‌کشد
            findings.append(_finding(f"error:{fn.__name__}", "unknown", "چک اجرا نشد",
                                     f"{type(e).__name__}: {str(e)[:90]}"))
    try:
        findings.extend(check_doc_drift([
            ("blackbox_tests", "F:/_______Black Box/BLACK-BOX.md",
             r"(\d{2,4})\s+tests?\s+green", 189),
        ]))
    except Exception:  # noqa: BLE001
        pass

    # هیچ «ok»ی روی شاهدِ کهنه باقی نمی‌ماند
    for f in findings:
        a = f.get("age_h")
        if f["verdict"] == "ok" and isinstance(a, (int, float)) and a > STALE_AFTER_H:
            f["verdict"] = "stale"
            f["why"] = (f"شاهد {a:.1f} ساعت کهنه است (سقف {STALE_AFTER_H}h). حکمِ «ok» "
                        f"روی دادهٔ کهنه خودش یک ادعای غیرِابطال‌پذیر است. " + f["why"])
    counts: dict = {}
    for f in findings:
        counts[f["verdict"]] = counts.get(f["verdict"], 0) + 1
    dishonest = [f for f in findings if f["verdict"] not in ("ok", "unknown")]
    return {"findings": findings, "counts": counts,
            "dishonest": len(dishonest), "total": len(findings),
            "flag": FLAG, "enabled": enabled()}


if __name__ == "__main__":  # pragma: no cover — پروبِ دستی، صفر اثرِ جانبی
    r = run()
    print(f"پروبِ انسجام — {r['total']} چک، {r['dishonest']} ادعای غیرِابطال‌پذیر\n")
    order = {"saturated": 0, "degenerate": 1, "clamped": 2, "self_referential": 3,
             "drift": 4, "provenance_missing": 5, "unfalsifiable": 6, "no_input": 7, "stale": 8,
             "unknown": 9, "ok": 10}
    for f in sorted(r["findings"], key=lambda x: order.get(x["verdict"], 9)):
        mark = "✓" if f["verdict"] == "ok" else "✗"
        print(f"{mark} [{f['verdict']:18s}] {f['id']}")
        print(f"    ادعا: {f['claim']}")
        if f["verdict"] != "ok":
            print(f"    چرا : {f['why']}")
            if f["thesis_row"]:
                print(f"    ردیفِ دفترِ تز: {f['thesis_row']}")
        print()
    print("شمارش:", json.dumps(r["counts"], ensure_ascii=False))
