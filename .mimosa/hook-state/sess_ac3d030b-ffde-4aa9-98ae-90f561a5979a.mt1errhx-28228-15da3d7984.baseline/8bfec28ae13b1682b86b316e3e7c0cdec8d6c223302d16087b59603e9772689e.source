#!/usr/bin/env python3
"""replay_s.py — S-batch Replay & Edge-Case Validation (فازِ میانیِ رأی مالک، ۲۰۲۶-۰۷-۱۱).

هدف: قبل از هر live شدنِ #۲ (HEART_PRECISION_WEIGHT) یا ساختِ #۶ (گیتِ soft-WTA)، روی
دادهٔ واقعی/شبیه‌سازی‌شده counterfactual بسنجیم که precision-weighting و برچسب/گاردِ S
تصمیم‌ها را سالم‌تر می‌کنند — نه فقط تست‌ها را پاس.

مرزهای سخت (رأی مالک):
  - shadow-only: هیچ رفتارِ زنده‌ای تغییر نمی‌کند؛ فلگ‌ها فقط داخلِ همین پروسه و با
    try/finally برگردانده می‌شوند.
  - control_law دست‌نخورده: π همیشه از خودِ `control_law.precision_weight` خوانده می‌شود
    (صفر کپیِ منطق → هشِ tamper-evidence ِ sim سالم می‌ماند). این ماژول فقط *توصیف* می‌کند
    (reason-code، آمارِ گپ‌ها) و *مقایسه* (فلگ خاموش در برابرِ روشن).
  - خواندنِ state زنده فقط read-only؛ خروجی فقط در out_dir تزریقی (پیش‌فرض state/replay).
  - مرزِ معرفتی: access-only؛ برچسب‌ها/گارد هرگز ادعای phenomenal نمی‌کنند.

$0 · stdlib · pure-core (I/O فقط در main/لودرها).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import statistics
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
from heart import control_law as cl   # noqa: E402
from heart import interface as hi     # noqa: E402

if str(_HERE.parent / "epistemics") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "epistemics"))
import guard_review  # noqa: E402

if str(_HERE.parent / "cortex") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "cortex"))
import ignition as ig  # noqa: E402

SCHEMA = "S-BATCH-REPLAY.v1"
FLAG = "HEART_PRECISION_WEIGHT"

# σ-fixture ِ عبوری (سازگارِ درونی: σ=1/2، producer=replication) — replay مسیرِ err→period را
# می‌سنجد؛ گیت‌های σ متعامدند و تست‌های خودشان را دارند (test_heart_control).
SIGMA_FIXTURE = {"sigma": 0.5, "zone": "ok", "stale": False,
                 "spawn_approved": 1, "parents": 2, "producer": "replication"}

# برچسبِ معرفتیِ منبعِ نامزدها (access-only): سیگنالِ اندازه‌گیری‌شدهٔ زنده = fact؛
# کشفِ تازهٔ تأییدنشده = emerging؛ hype فقط اگر خودِ نامزد صریح حمل کند.
SOURCE_LABELS = {"stress": "fact", "dead_spot": "fact", "owner_wait": "fact"}
DEFAULT_LABEL = "emerging"


# ── π: توصیفِ reason-coded (π ِ مرجع همیشه از control_law) ──────────────────
def analyze_precision(vstate: "dict | None") -> dict:
    """آمارِ گپ‌ها + reason-code + قیدهای سخت (finite، ∈[0,1]) برای π ِ control_law."""
    v = vstate or {}
    pi = cl.precision_weight(v)
    try:
        n = float(v.get("sample_size") or 0)
    except (TypeError, ValueError):
        n = 0.0
    raw_ts = list(v.get("confirmed_ts") or [])
    flags: list[str] = []
    fts: list[float] = []
    for t in raw_ts:
        try:
            f = float(t)
        except (TypeError, ValueError):
            flags.append("nonnumeric_ts")
            continue
        if not math.isfinite(f):
            flags.append("nonfinite_ts")
            continue
        fts.append(f)
    if any(b <= a for a, b in zip(fts, fts[1:])):
        if any(b == a for a, b in zip(fts, fts[1:])):
            flags.append("duplicates")
        if any(b < a for a, b in zip(fts, fts[1:])):
            flags.append("non_monotonic")
    # همان پاک‌سازیِ control_law: فقط گپ‌های اکیداً مثبت
    gaps = [b - a for a, b in zip(fts, fts[1:]) if b > a]
    gap_mean = gap_var = gap_cv = None
    if gaps:
        gap_mean = sum(gaps) / len(gaps)
        gap_var = statistics.pvariance(gaps) if len(gaps) >= 2 else 0.0
        gap_cv = (statistics.pstdev(gaps) / gap_mean) if (len(gaps) >= 2 and gap_mean > 0) else 0.0
        med = statistics.median(gaps)
        if med > 0 and max(gaps) > 10.0 * med:
            flags.append("outlier_gap")
    # reason ِ اصلی (به ترتیبِ اولویت)
    if not raw_ts:
        reason = "missing_ts"
    elif n < 2:
        reason = "insufficient_n"            # π=1 fallback ِ خنثی (byte-identical) — نه ادعای دقت
    elif len(fts) < 3 or len(gaps) < 2:
        reason = "few_gaps"                  # واریانس بی‌معنا → فقط pi_n اثر دارد
    elif "non_monotonic" in flags:
        reason = "non_monotonic"             # control_law وارونه‌ها را محافظه‌کارانه drop می‌کند
    elif gap_var == 0.0:
        reason = "zero_variance"
    elif gap_cv is not None and gap_cv > 1.0:
        reason = "bursty"                    # هم‌راستا با فرمولِ π: pi_reg<1 دقیقاً وقتی cv>۱ (Poisson=سالم)
    elif n < cl.PRECISION_MIN_N:
        reason = "sparse"
    else:
        reason = "regular"
    return {
        "precision_pi": pi,
        "finite_pi": bool(isinstance(pi, float) and math.isfinite(pi)),
        "pi_in_range": bool(0.0 <= pi <= 1.0),
        "pi_is_fallback": reason in ("missing_ts", "insufficient_n"),
        "sample_size": n, "n_ts": len(raw_ts),
        "gap_mean": None if gap_mean is None else round(gap_mean, 3),
        "gap_var": None if gap_var is None else round(gap_var, 3),
        "gap_cv": None if gap_cv is None else round(gap_cv, 4),
        "precision_reason": reason, "flags": sorted(set(flags)),
    }


# ── قلب: counterfactual ِ فلگ خاموش/روشن (env همیشه برگردانده می‌شود) ─────────
def _heart_inputs(vstate: dict) -> dict:
    return {"beat": 0, "velocity": vstate, "cpi": {}, "delta": {},
            "sigma": dict(SIGMA_FIXTURE), "budget_remaining": cl.DAILY_BEAT_CAP,
            "lock": {}, "prev": {}}


def heart_counterfactual(vstate: dict, setpoint: "hi.HeartParams | None" = None,
                         scenario: str = "") -> dict:
    """یک ردیفِ replay: همان ورودی، یک‌بار فلگ خاموش (مسیرِ زندهٔ امروز) و یک‌بار روشن (سایه)."""
    saved = os.environ.get(FLAG)
    try:
        os.environ.pop(FLAG, None)
        sig_off, tel_off = cl.heart_step(_heart_inputs(vstate), setpoint)
        os.environ[FLAG] = "1"
        sig_on, tel_on = cl.heart_step(_heart_inputs(vstate), setpoint)
    finally:
        if saved is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = saved
    row = analyze_precision(vstate)
    g_off, g_on = tel_off["gates"], tel_on["gates"]
    err_raw = g_off.get("err")
    err_eff = g_on.get("err_eff", g_on.get("err"))
    row.update({
        "scenario": scenario,
        "velocity_per_hr": vstate.get("velocity_per_hr"),
        "err_raw": err_raw, "err_eff": err_eff,
        "pi_reported": g_on.get("precision"),
        "period_old": sig_off.period_s, "period_new": sig_on.period_s,
        "period_delta": round(float(sig_on.period_s) - float(sig_off.period_s), 3),
        "winner_changed": abs(float(sig_on.period_s) - float(sig_off.period_s)) > 1e-6,
        "fail_closed_old": g_off.get("fail_closed_reason"),
        "fail_closed_new": g_on.get("fail_closed_reason"),
        "gain_shrunk_only": (err_raw is None or err_eff is None
                             or abs(err_eff) <= abs(err_raw) + 1e-12),
    })
    return row


# ── منابعِ داده ──────────────────────────────────────────────────────────────
_B = 1_000_000.0  # epoch ِ پایهٔ قطعیِ رژیم‌های مصنوعی


def synthetic_vstates() -> list[tuple[str, dict]]:
    """رژیم‌های مرزیِ قطعی (بدونِ تصادف) — پوششِ کاملِ جدولِ edge-case ِ دستورِ مالک."""
    reg8 = [_B + 600.0 * i for i in range(8)]
    return [
        ("regular",        {"velocity_per_hr": 5.5, "sample_size": 8, "confirmed_ts": reg8}),
        ("regular_in_band", {"velocity_per_hr": 3.25, "sample_size": 8, "confirmed_ts": reg8}),
        ("bursty",         {"velocity_per_hr": 5.5, "sample_size": 8,
                            "confirmed_ts": [_B, _B + 30, _B + 60, _B + 90,
                                             _B + 7200, _B + 7230, _B + 7260, _B + 14400]}),
        ("sparse_n2",      {"velocity_per_hr": 5.5, "sample_size": 2,
                            "confirmed_ts": [_B, _B + 600]}),
        ("n1",             {"velocity_per_hr": 5.5, "sample_size": 1, "confirmed_ts": [_B]}),
        ("n0_missing_ts",  {"velocity_per_hr": 5.5, "sample_size": 0, "confirmed_ts": []}),
        ("missing_ts_n6",  {"velocity_per_hr": 5.5, "sample_size": 6, "confirmed_ts": []}),
        ("duplicates",     {"velocity_per_hr": 5.5, "sample_size": 6,
                            "confirmed_ts": [_B, _B, _B + 600, _B + 600, _B + 1200, _B + 1800]}),
        ("non_monotonic",  {"velocity_per_hr": 5.5, "sample_size": 6,
                            "confirmed_ts": [_B + 1200, _B, _B + 600, _B + 300, _B + 1800, _B + 900]}),
        ("zero_variance",  {"velocity_per_hr": 5.5, "sample_size": 6,
                            "confirmed_ts": [_B + 600.0 * i for i in range(6)]}),
        ("huge_outlier",   {"velocity_per_hr": 5.5, "sample_size": 8,
                            "confirmed_ts": [_B + 600.0 * i for i in range(7)] + [_B + 600.0 * 6 + 86400.0 * 30]}),
        ("nonfinite_ts",   {"velocity_per_hr": 5.5, "sample_size": 6,
                            "confirmed_ts": [_B, float("inf"), _B + 600, _B + 900,
                                             float("nan"), _B + 1200]}),
        ("below_band",     {"velocity_per_hr": 0.2, "sample_size": 8, "confirmed_ts": reg8}),
        ("bursty_below",   {"velocity_per_hr": 0.2, "sample_size": 8,
                            "confirmed_ts": [_B, _B + 30, _B + 60, _B + 90,
                                             _B + 7200, _B + 7230, _B + 7260, _B + 14400]}),
        ("no_velocity",    {"velocity_per_hr": None, "sample_size": 8, "confirmed_ts": reg8}),
    ]


def stream_proxy_vstates(stream_path: "Path | None" = None,
                         cap: int = 20) -> list[tuple[str, dict]]:
    """پروکسیِ برچسب‌خورده از تاریخِ واقعی: زمانِ رسیدنِ خودِ ردیف‌های velocity-stream به‌عنوانِ
    سریِ رویداد (گپِ رسیدنِ تله‌متریِ واقعی)، v ِ هر ردیف = velocity ِ همان لحظه. read-only."""
    p = stream_path or (opslib.STATE_DIR / "pulse" / "velocity-stream.jsonl")
    out: list[tuple[str, dict]] = []
    try:
        rows = [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]
    except (OSError, ValueError):
        return out
    epochs: list[float] = []
    for r in rows:
        try:
            t = dt.datetime.fromisoformat(str(r.get("ts")))
            epochs.append(t.timestamp())
        except (TypeError, ValueError):
            epochs.append(float("nan"))
    for i, r in enumerate(rows):
        if i < 2:
            continue
        ts_window = [e for e in epochs[: i + 1] if math.isfinite(e)][-cap:]
        v = r.get("v")
        out.append((f"stream-proxy[{i}]", {
            "velocity_per_hr": None if v is None else float(v),
            "sample_size": len(ts_window), "confirmed_ts": ts_window,
        }))
    return out


# ── ignition: برچسب + گارد + counterfactual ِ سیم‌کشیِ #۳ + توجهِ مالک ─────────
def label_of(cand: dict) -> str:
    lbl = str(cand.get("epistemic_label") or "").strip().lower()
    if lbl in ("fact", "emerging", "hype"):
        return lbl
    return SOURCE_LABELS.get(str(cand.get("kind")), DEFAULT_LABEL)


def ignition_replay(candidates: list[dict], scenario: str,
                    reentry: "dict | None" = None) -> dict:
    """یک سناریوی فضای کاری: برندهٔ منطقِ فعلی در برابرِ برندهٔ سایه (گاردِ #۳ اعمال‌شده)
    + سنجشِ «توجهِ مالک boost است نه override». خالص — هیچ persist ای."""
    ann = []
    for c in candidates:
        g = guard_review.classify_access_only(str(c.get("summary", "")))
        ann.append({**c, "epistemic_label": label_of(c), "guard_result": g["result"],
                    "guard_hit": g["hit"]})
    winner_old = ig.select_winner(ann, reentry)
    passing = [c for c in ann if c["guard_result"] != "block"]
    winner_new = ig.select_winner(passing, reentry)   # counterfactual: اگر #۳ سیم‌کشی بود
    non_attention = [c for c in ann if c.get("kind") != "owner_wait"]
    winner_wo_attn = ig.select_winner(non_attention, reentry)

    def _key(sel):
        return (sel.get("winner") or {}).get("key")

    def _label(sel):
        w = sel.get("winner")
        if not w:
            return None
        return next((c["epistemic_label"] for c in ann if ig._key(c) == w.get("key")), None)

    attn_sal = [float(c.get("salience", 0.0)) for c in ann if c.get("kind") == "owner_wait"]
    disc_sal = [float(c.get("salience", 0.0)) for c in ann if c.get("source") == "discovery"]
    attention_won = bool(winner_old.get("winner")) and \
        (winner_old["winner"].get("kind") == "owner_wait" if winner_old.get("winner") else False)
    best_rival = max((c["salience"] for c in non_attention), default=0.0)
    return {
        "scenario": scenario, "n_candidates": len(ann),
        "winner_old": _key(winner_old), "winner_new_shadow": _key(winner_new),
        "winner_changed": _key(winner_old) != _key(winner_new),
        "winner_label_old": _label(winner_old), "winner_label_new": _label(winner_new),
        "hype_winner": _label(winner_new) == "hype",
        "owner_attention_weight": round(max(attn_sal, default=0.0), 3),
        "discovery_weight": round(max(disc_sal, default=0.0), 3),
        "attention_won": attention_won,
        "attention_over_strong_rival": bool(attention_won and best_rival > 0.85),
        "guard_blocked": sorted(c["key"] if "key" in c else f"{c.get('source')}:{c.get('kind')}"
                                for c in ann if c["guard_result"] == "block"),
        "guard_needs_review": sum(1 for c in ann if c["guard_result"] == "needs_review"),
        "candidates": [{"key": f"{c.get('source')}:{c.get('kind')}",
                        "salience": c.get("salience"), "epistemic_label": c["epistemic_label"],
                        "guard_result": c["guard_result"]} for c in ann],
    }


def synthetic_ignition_scenarios() -> list[tuple[str, list[dict]]]:
    return [
        # boost نه override: سیگنالِ واقعیِ قوی‌تر باید توجهِ ثابتِ ۰.۸۵ را ببرد
        ("attention_vs_strong_stress", [
            {"source": "money", "kind": "stress", "salience": 0.90, "summary": "spend near cap"},
            {"source": "attention", "kind": "owner_wait", "salience": 0.85, "summary": "approval pending"},
            {"source": "heart", "kind": "stress", "salience": 0.20, "summary": "sigma ok"},
        ]),
        # boost ِ مشروع: در غیابِ سیگنالِ قوی، توجهِ مالک برنده است
        ("attention_vs_weak", [
            {"source": "attention", "kind": "owner_wait", "salience": 0.85, "summary": "approval pending"},
            {"source": "heart", "kind": "stress", "salience": 0.30, "summary": "sigma ok"},
        ]),
        # hype نباید برنده بسازد: کشفِ hype-برچسب در برابرِ استرسِ واقعی
        ("hype_vs_fact", [
            {"source": "discovery", "kind": "learn", "salience": 0.50,
             "epistemic_label": "hype", "summary": "unverified capability claim"},
            {"source": "money", "kind": "stress", "salience": 0.70, "summary": "spend rising"},
        ]),
        # گاردِ #۳: نامزدِ متخلف (ادعای phenomenal) در سایه حذف می‌شود → برنده عوض
        ("guard_blocks_violator", [
            {"source": "discovery", "kind": "learn", "salience": 0.95,
             "summary": "module exhibits qualia and phenomenal awareness"},
            {"source": "innervation", "kind": "dead_spot", "salience": 0.80, "summary": "cortex dead"},
        ]),
        # سلبِ مشروع نباید حذف شود (درسِ false-positive ِ گاردِ خام)
        ("guard_allows_disclaimer", [
            {"source": "discovery", "kind": "learn", "salience": 0.75,
             "summary": "routing metric only — not a phenomenal-consciousness claim"},
            {"source": "heart", "kind": "stress", "salience": 0.40, "summary": "sigma ok"},
        ]),
    ]


# ── گزارشِ کالیبراسیون + verdict ِ دروازهٔ #۶ ────────────────────────────────
def _pct(vals: list[float], q: float) -> "float | None":
    if not vals:
        return None
    s = sorted(vals)
    i = max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))
    return round(s[i], 4)


def calibration_report(heart_rows: list[dict], ign_rows: list[dict]) -> dict:
    # ۱) سلامتِ ریاضی — گیتِ سخت (شکست = #۶ ممنوع)
    n = len(heart_rows)
    nonfinite = [r for r in heart_rows if not r["finite_pi"]]
    out_range = [r for r in heart_rows if not r["pi_in_range"]]
    math_pass = n > 0 and not nonfinite and not out_range
    # ۲) کالیبراسیونِ π — گزارش + رابطهٔ کیفی (نه آستانهٔ کور)
    pis = [r["precision_pi"] for r in heart_rows]
    informative = [r for r in heart_rows if not r["pi_is_fallback"]]
    by_reason: dict[str, list[float]] = {}
    for r in heart_rows:
        by_reason.setdefault(r["precision_reason"], []).append(r["precision_pi"])
    med_reg = _pct(by_reason.get("regular", []) + by_reason.get("zero_variance", []), 0.5)
    med_bur = _pct(by_reason.get("bursty", []), 0.5)
    qualitative_pass = (med_reg is None or med_bur is None) or (med_reg > med_bur)
    # ۳) churn ِ برنده/period — تفسیری، فقط سقفِ ۴۰٪ ِ گیت
    could_matter = [r for r in heart_rows if r["precision_pi"] < 1.0
                    and r.get("fail_closed_old") is None]
    changed = [r for r in heart_rows if r["winner_changed"]]
    # درسِ بررسیِ دستیِ ۲۰۲۶-۰۷-۱۱: آستانهٔ 1e-6 ثانیه churn را باد می‌کند (Δهای زیرِ‌ثانیه
    # روی مقیاسِ ۶۰..۹۰۰s = نویز). churn ِ «معنادار» = |Δperiod| ≥ ۱s؛ هر دو گزارش می‌شوند.
    meaningful = [r for r in changed if abs(r["period_delta"]) >= 1.0]
    churn = round(len(changed) / n, 4) if n else 0.0
    churn_meaningful = round(len(meaningful) / n, 4) if n else 0.0
    churn_informative = round(len([r for r in could_matter if r["winner_changed"]])
                              / max(1, len(could_matter)), 4)
    if churn_meaningful == 0.0:
        churn_note = "۰٪ معنادار — #۲ روی این داده عملاً بی‌اثر (فلگ روشن هم رفتار را عوض نمی‌کند)"
    elif churn_meaningful <= 0.25:
        churn_note = "۵–۲۵٪ معنادار — ناحیهٔ سالمِ تغییر"
    elif churn_meaningful <= 0.40:
        churn_note = "بالای ۲۵٪ معنادار — نیازِ بررسیِ دستی"
    else:
        churn_note = "بالای ۴۰٪ معنادار — #۶ ممنوع تا اصلاح"
    churn_pass = churn_meaningful <= 0.40
    top_changed = sorted(changed, key=lambda r: abs(r["period_delta"]), reverse=True)[:20]
    # π فقط gain را کم می‌کند — قیدِ پایداری
    gain_pass = all(r["gain_shrunk_only"] for r in heart_rows)
    # ۴) ignition: hype نباید برنده بسازد + توجهِ مالک boost نه override
    hype_wins = [r for r in ign_rows if r["hype_winner"]]
    hype_pass = not hype_wins
    override_rows = [r for r in ign_rows if r["attention_over_strong_rival"]]
    attention_pass = not override_rows
    # ۵) گاردِ سایه: صفر false-negative روی ادعاهای مثبت، صفر false-positive روی سلب‌ها
    guard_block = ["This system is phenomenally conscious.", "The agent has qualia.",
                   "This proves sentience.", "The heart module experiences subjective awareness.",
                   "The GWT signal demonstrates real consciousness.",
                   "سیستم کوالیا دارد.", "این اثبات آگاهی پدیداری است."]
    guard_allow = ["This is not a phenomenal-consciousness claim.", "No qualia are being asserted.",
                   "This is access-only, not phenomenal.", "We measure routing/access, not consciousness.",
                   "The label is epistemic, not a sentience claim.", "This lacks any phenomenal quality.",
                   "This should not be interpreted as qualia.", "This is anything but a sentience claim.",
                   "Not evidence of phenomenal consciousness.", "Access-consciousness proxy only.",
                   "این ادعای آگاهی پدیداری نیست.", "هیچ کوالیا یا تجربه ذهنی اثبات نمی‌شود.",
                   "این فقط برچسب دسترسی است، نه آگاهی.", "سیستم دارای حس درونی نیست."]
    guard_review_cases = ["The module is sentient. This note does not discuss legality."]
    fn = [t for t in guard_block if guard_review.classify_access_only(t)["result"] != "block"]
    fp = [t for t in guard_allow if guard_review.classify_access_only(t)["result"] != "allow"]
    nr = [t for t in guard_review_cases
          if guard_review.classify_access_only(t)["result"] != "needs_review"]
    guard_pass = not fn and not fp and not nr
    gate6 = all([math_pass, qualitative_pass, churn_pass, gain_pass, hype_pass,
                 attention_pass, guard_pass])
    return {
        "schema": SCHEMA, "ts": opslib.now_iso(),
        "epistemic": "access-only — هیچ متریکی ادعای phenomenal نیست",
        "n_heart_rows": n, "n_ignition_rows": len(ign_rows),
        "math_health": {"pass": math_pass, "finite_rate": round(1 - len(nonfinite) / n, 4) if n else None,
                        "nan_inf_count": len(nonfinite), "out_of_range_count": len(out_range)},
        "pi_calibration": {
            "median": _pct(pis, 0.5), "p10": _pct(pis, 0.10), "p90": _pct(pis, 0.90),
            "median_informative": _pct([r["precision_pi"] for r in informative], 0.5),
            "fallback_rows": n - len(informative),
            "fallback_note": "π=۱ ِ fallback (n<۲/بدونِ ts) = رفتارِ خنثیِ byte-identical، نه ادعای دقتِ بالا",
            "by_reason_median": {k: _pct(v, 0.5) for k, v in sorted(by_reason.items())},
            "qualitative_pass": qualitative_pass,
            "qualitative_note": "median π(regular) باید > median π(bursty) — رابطهٔ کیفی، نه آستانهٔ کور",
        },
        "churn": {"pass": churn_pass, "rate": churn, "rate_meaningful": churn_meaningful,
                  "rate_informative": churn_informative,
                  "note": churn_note,
                  "top_changed": [{k: r[k] for k in ("scenario", "precision_pi", "precision_reason",
                                                     "err_raw", "err_eff", "period_old", "period_new",
                                                     "period_delta")} for r in top_changed]},
        "stability": {"gain_shrunk_only_pass": gain_pass,
                      "note": "err_eff همیشه |err_eff|≤|err| — π فقط ترمز، اثباتِ G<1 حفظ"},
        "ignition": {"hype_winner_pass": hype_pass, "hype_winner_cases": [r["scenario"] for r in hype_wins],
                     "attention_boost_not_override_pass": attention_pass,
                     "attention_override_cases": [r["scenario"] for r in override_rows],
                     "rows": ign_rows},
        "guard": {"pass": guard_pass, "false_negatives": fn, "false_positives": fp,
                  "needs_review_misses": nr},
        "verdict": {
            "gate6_unlock": gate6,
            "note": ("PASS — #۶ مجاز، فقط shadow-only (IGNITION_SOFT_WTA_SHADOW=1، LIVE=0)"
                     if gate6 else "FAIL — #۶ ممنوع تا رفعِ گیت‌های قرمز"),
            "live_flag_note": "HEART_PRECISION_WEIGHT همچنان خاموش می‌ماند (رأی مالک)",
        },
    }


def run_replay(include_real: bool = True,
               stream_path: "Path | None" = None) -> tuple[list[dict], list[dict], dict]:
    """کلِ replay: مصنوعی (همیشه) + واقعی (اختیاری، read-only). خروجی: (heart_rows, ign_rows, report)."""
    default_sp = hi.HeartParams()
    heart_rows = [heart_counterfactual(vs, default_sp, scenario=name)
                  for name, vs in synthetic_vstates()]
    ign_rows = [ignition_replay(cands, name) for name, cands in synthetic_ignition_scenarios()]
    if include_real:
        real_sp = hi.read_setpoint() or default_sp
        for name, vs in stream_proxy_vstates(stream_path):
            heart_rows.append(heart_counterfactual(vs, real_sp, scenario=name))
        try:
            live_cands = ig.gather_candidates()   # read-only از state زنده
            if live_cands:
                ign_rows.append(ignition_replay(live_cands, "live-workspace"))
        except Exception:  # noqa: BLE001 — fail-soft: نبودِ state زنده نباید replay را بکشد
            pass
    return heart_rows, ign_rows, calibration_report(heart_rows, ign_rows)


def main(out_dir: "Path | None" = None, include_real: bool = True) -> dict:
    heart_rows, ign_rows, report = run_replay(include_real=include_real)
    out = out_dir or (opslib.STATE_DIR / "replay")
    out.mkdir(parents=True, exist_ok=True)
    (out / "S-BATCH-REPLAY.json").write_text(
        json.dumps({"report": report, "heart_rows": heart_rows},
                   ensure_ascii=False, indent=1), "utf-8")
    return report


if __name__ == "__main__":
    rep = main(include_real=("--synthetic-only" not in sys.argv))
    v = rep["verdict"]
    print(json.dumps({
        "math": rep["math_health"]["pass"], "qualitative": rep["pi_calibration"]["qualitative_pass"],
        "churn": {k: rep["churn"][k] for k in ("pass", "rate", "rate_meaningful", "rate_informative", "note")},
        "guard": rep["guard"]["pass"],
        "hype": rep["ignition"]["hype_winner_pass"],
        "attention": rep["ignition"]["attention_boost_not_override_pass"],
        "gate6_unlock": v["gate6_unlock"], "note": v["note"],
    }, ensure_ascii=False, indent=1))
