#!/usr/bin/env python3
"""pulse_arbiter.py — HH-P11: داورِ نبض (سه قلب، یک ضربان).

سه قلبِ مستقل هر کدام یک period تولید می‌کنند اما تا امروز جدا از هم سیم‌کشی بودند:
  ۱) cardiac        — آلومتریک: period ∝ mass^¼ × baro × budget  (cardiac.effective_period)
  ۲) control_law    — velocity-first: period = BASE·exp(K_P·err) × cpi × budget (heart.heart_step)
  ۳) chrono_rhythm  — ریتمِ HRV/mode: T_beat = T0·exp(κ·readiness−λ·stress)·(1+ε·ξ)

این ماژول هر سه را **موازی و read-only** می‌خواند و در **یک** periodِ advisory آشتی می‌دهد —
بدونِ fuse کردنِ کدِ ماژول‌ها (M-HEART §مخاطب: «کد را بازاستفاده کن؛ هرگز fuse نکن»).
هر قلب ماژولِ مستقلِ خودش می‌ماند؛ داور فقط *خروجی‌شان* را می‌خواند و رأی‌گیری می‌کند.

خطوطِ قرمز (ADR-001 coupled-not-merged + M-HEART §۴/§۶):
  · محاسبهٔ candidate **advisory** است؛ عبور به `organism.py:_sleep_s` فقط از seamِ
    owner-gated و با authority guard + anchor معتبر انجام می‌شود. این ماژول هرگز بودجه،
    ledger یا EffectorGate را نمی‌نویسد. سینک: `state/pulse/arbiter-latest.json`.
  · **پشتِ flag، پیش‌فرض خاموش** (`OCTOPUS_WIRE_PULSE_ARBITER`): flag off → `persist()` no-op و
    seamِ زنده byte-identical با امروز می‌ماند (no regression).
  · **سیم‌کشیِ زنده owner-gated است** — `wire_open()` به envهای صریح و
    `ACTIVATION-PULSE-ARBITER.flag` نیاز دارد. G4 حتی پس از بازشدن outer wire، رأیِ
    control_lawِ shadow را observable-but-ineligible نگه می‌دارد و cadence را با anchor
    ثابتِ pre-G4 از تسریع ناخواسته محافظت می‌کند.
  · `chrono.py` دست‌نزدنی؛ هیچ import از chrono/effects/money. $0 · آفلاین · stdlib · fail-soft.

قانونِ آشتی (طراحیِ این ماژول — «ترمز غالب، شتاب اجماعی»):
  · هر قلبی که در حالتِ ترمز است (fail-closed / RED / budget-depleted / drift / σ-over-cap)
    period را دستِ‌کم تا مقدارِ ترمزش بالا می‌برد — **شتاب هرگز ترمز را خلع‌سلاح نمی‌کند**.
  · برای تندشدن (period < base) همهٔ قلب‌های حاضر باید موافق باشند: اجماع = میانگینِ هندسیِ
    وزن‌دار (precision-weighted geometric mean). یک قلبِ محتاط اجماع را به بالا می‌کشد.
  · effective = max(اجماع، قوی‌ترین ترمز)، سپس clamp سختِ [FLOOR, MAX] (حرفِ آخر).

۲۰۲۷-alignment (active-inference، [[2027 Standards Base & Backlog]] #۲): وزنِ precisionِ هر
کانال به‌جای ثابتِ دست‌چین، **inverse-variance** (pymdp γ) از سیگنالِ خودش می‌شود — پشتِ
`PULSE_ARBITER_PRECISION` (پیش‌فرض خاموش → precisionِ دستیِ فعلی byte-identical). control_law
precisionِ کانونیِ خودش را بازاستفاده می‌کند (صفر کپیِ منطق، §۵)؛ cardiac/rhythm از periodِ اخیر.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import deque
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/heart
_OPS = _HERE.parent                              # _ops
for _p in (str(_OPS / "budget"), str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

SCHEMA = "pulse-arbiter.v1"
AUTHORITY_POLICY = "pulse-authority-g4.v1"
LATEST = opslib.STATE_DIR / "pulse" / "arbiter-latest.json"
SINK = opslib.STATE_DIR / "pulse" / "arbiter-shadow.jsonl"
ACT_ARBITER = opslib.OPS / "ACTIVATION-PULSE-ARBITER.flag"
FLAG_ENV = "OCTOPUS_WIRE_PULSE_ARBITER"

# همان کران‌های سه قلب (env-tunable، دیفالتِ یکسان با cardiac/control_law)
BASE_PERIOD_S = float(os.environ.get("CHRONO_PERIOD_S", "60.0"))
FLOOR_S = float(os.environ.get("CARDIAC_RESTING_FLOOR_S", "30.0"))
MAX_S = float(os.environ.get("CARDIAC_MAX_PERIOD_S", "900.0"))
# periodِ ترمزِ سخت (fail-closed/RED = استراحتِ عمیق). دیفالت = سقف.
BRAKE_PERIOD_S = float(os.environ.get("PULSE_ARBITER_BRAKE_S", str(MAX_S)))
# کفِ precision برای قلبِ حاضر (تا Σπ هرگز صفر نشود و رأیش کاملاً محو نشود)
PI_FLOOR = 0.05

#: ریتمِ اعلام‌شدهٔ `heart-shadow-latest.json` — هر ~۵ بیت. برای تشخیصِ HELD لازم
#: است: این ظرف کندتر **نوشته** می‌شود از آنچه **خوانده** می‌شود.
_SHADOW_CADENCE_S = float(os.environ.get("PULSE_ARBITER_SHADOW_CADENCE_S", "220.0"))

# ── 2027-alignment (active-inference): precisionِ inverse-variance به‌جای gainِ دستی ──
# استانداردِ ۲۰۲۷ (pymdp γ / predictive-coding؛ [[2027 Standards Base & Backlog]] #۲):
# وزنِ هر کانال = inverse-varianceِ سیگنالِ خودش، نه ثابتِ دست‌چین (۱.۰/۰.۷). پشتِ فلگِ
# جدا، پیش‌فرض خاموش → precisionِ دستیِ فعلی byte-identical می‌ماند (هم‌سبکِ HEART_PRECISION_WEIGHT).
FLAG_PRECISION = "PULSE_ARBITER_PRECISION"
_PRECISION_WINDOW = int(os.environ.get("PULSE_ARBITER_PRECISION_WINDOW", "12"))
# بافرِ رولینگِ per-channel (in-process، مثلِ HRV بافرِ rhythm) — بدونِ هیچ state روی دیسک
_period_hist: dict[str, deque] = {}

_COLOR_RANK = {"GREEN": 0, "AMBER": 1, "RED": 2}
_RANK_COLOR = {0: "GREEN", 1: "AMBER", 2: "RED"}


def flag(name: str) -> bool:
    """env-flag با پیش‌فرض خاموش (allowlistِ truthy، هم‌راستا با heartstate)."""
    return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "yes", "on")


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def inverse_variance_precision(samples) -> float:
    """precisionِ active-inference = 1/(1+CV²) روی نمونه‌های اخیرِ همان کانال (pymdp γ).
    سیگنالِ پایدار (CV کوچک) → π→۱؛ کانالِ پرنوسان → π پایین. کمتر از ۲ نمونهٔ معتبر یا
    میانگینِ ≤۰ → ۱.۰ (byte-identical با gainِ دستی وقتی داده کم است). درسِ replay §۵:
    ورودیِ non-finite/≤۰ پاک می‌شود تا هرگز NaN/Inf/کرش ندهد."""
    xs = [float(s) for s in samples
          if isinstance(s, (int, float)) and math.isfinite(float(s)) and float(s) > 0]
    if len(xs) < 2:
        return 1.0
    mean = sum(xs) / len(xs)
    if mean <= 0:
        return 1.0
    var = sum((x - mean) ** 2 for x in xs) / len(xs)
    cv2 = var / (mean * mean)
    return _clamp(1.0 / (1.0 + cv2), 0.0, 1.0)


def _apply_precision(votes: list[dict]) -> list[dict]:
    """۲۰۲۷-alignment: وزنِ هر کانال را به inverse-variance تبدیل کن — فقط با فلگ.
    control_law: اگر precisionِ کانونیِ خودش (control_law.precision_weight، در تلمتری)
    موجود بود همان بازاستفاده می‌شود (صفر کپیِ منطق، طبقِ ۲۰۲۷ §۵)؛ وگرنه inverse-variance.
    cardiac/rhythm: inverse-varianceِ periodِ اخیرِ خودشان. فلگ خاموش → precisionِ دستی
    دست‌نخورده و کلیدِ موقت `_canonical_precision` همیشه پاک می‌شود (خروجی byte-identical)."""
    on = flag(FLAG_PRECISION)
    for v in votes:
        canonical = v.pop("_canonical_precision", None)   # کلیدِ موقت همیشه پاک می‌شود
        if not on:
            continue
        if isinstance(canonical, (int, float)) and math.isfinite(float(canonical)):
            v["precision"] = _clamp(float(canonical), 0.0, 1.0)
            v["precision_src"] = "control_law.precision_weight"
        if not v.get("present") or v.get("eligible_for_live") is not True or not v.get("period_s"):
            continue
        name = v["heart"]
        buf = _period_hist.setdefault(name, deque(maxlen=_PRECISION_WINDOW))
        buf.append(float(v["period_s"]))
        if not (isinstance(canonical, (int, float)) and math.isfinite(float(canonical))):
            v["precision"] = inverse_variance_precision(buf)
            v["precision_src"] = "inverse-variance"
    return votes


def _finite_period(value, *, floor_s: float = FLOOR_S,
                   max_s: float = MAX_S) -> "float | None":
    try:
        period = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(period) or not floor_s <= period <= max_s:
        return None
    return period


def _authority_vote(vote: dict, *, authority: str,
                    reasons: list[str]) -> dict:
    """Keep an observation visible while making it ineligible for live arbitration."""
    observed = vote.get("period_s")
    vote.update({
        "present": False,
        "period_s": observed,
        "observed_period_s": observed,
        "eligible_for_live": False,
        "authority": authority,
        "authority_reasons": [str(r) for r in reasons if str(r)],
    })
    return vote


def _mark_live_authority(vote: dict, authority: str,
                         reasons: "list[str] | None" = None) -> dict:
    vote["eligible_for_live"] = bool(vote.get("present"))
    vote["authority"] = authority
    vote["authority_reasons"] = list(reasons or [])
    return vote


def _control_authority(rec) -> tuple[bool, str, list[str]]:
    """G4: control-law observations have no live authority in this gate.

    ``production_wire.open`` belongs to the shadow producer and is useful evidence,
    but it is not a capability token for the pulse arbiter.  Gate 1 will introduce a
    committed authority envelope.  Until then control-law remains observable only.
    """
    reasons: list[str] = []
    if not isinstance(rec, dict) or not rec:
        return False, "ADVISORY_COMPUTE", ["no committed authority envelope"]
    if rec.get("mode") != "shadow":
        reasons.append("record provenance is not canonical shadow mode")
    production = rec.get("production_wire")
    if not isinstance(production, dict) or production.get("open") is not True:
        reasons.append("shadow production wire is not open")
    if rec.get("gate0_live_producer") is not True:
        reasons.append("Gate-0 live producer is not authoritative")
    provenance = rec.get("sog_provenance")
    if provenance not in ("VERIFIED",):
        reasons.append("SOG provenance is not VERIFIED")
    reasons.append("G4 grants no control-law live authority before HeartStore Gate 1")
    return False, "SHADOW_ONLY", reasons


# ════════════════════════════════════════════════════════════════════════════════
# هستهٔ خالص — سه رأی → یک period. بدونِ I/O، کاملاً تست‌پذیر.
# ════════════════════════════════════════════════════════════════════════════════
def _vote(name: str, period, braking: bool, precision: float,
          color: str = "GREEN", present: bool = True, note: str = "",
          mode: str = "LIVE", dof: int = 0, last_change_ts=None) -> dict:
    """یک رأیِ نرمال‌شدهٔ قلب. period=None یا present=False → قلب رأی نمی‌دهد (abstain).

    ۲۰۲۶-۰۸-۰۳ (گامِ ۱۰، جزءِ C11): هر رأی حالا `mode`/`dof`/`last_change_ts` هم
    حمل می‌کند. بدونِ این‌ها «حاضر بودن» و «حرف تازه داشتن» یکی می‌شدند — و همان
    باعث شد داور با یک متحرک و دو ثابت، `driver="consensus"` و `n_present=3` و
    `color=GREEN` منتشر کند. حضور رأی نیست؛ **حرکت** رأی است.

        LIVE      عدد واقعاً تازه است
        HELD      اسنپ‌شاتِ نگه‌داشته‌شده (نوشته کندتر از خوانده)
        CONSTANT  تابعِ قطعیِ ورودی‌هایی که تکان نمی‌خورند (dof=1)
        UNKNOWN   نمی‌دانیم
    """
    p = None
    if present and period is not None:
        try:
            p = float(period)
            if not math.isfinite(p) or p <= 0:
                p = None
        except (TypeError, ValueError):
            p = None
    return {
        "heart": name,
        "present": bool(present and p is not None),
        "period_s": p,
        "braking": bool(braking),
        "precision": _clamp(float(precision) if precision is not None else 1.0, 0.0, 1.0),
        "color": color if color in _COLOR_RANK else "GREEN",
        "note": note,
        "mode": mode if mode in ("LIVE", "HELD", "CONSTANT", "UNKNOWN") else "UNKNOWN",
        "dof": int(dof) if isinstance(dof, int) else 0,
        "last_change_ts": last_change_ts,
        "eligible_for_live": bool(present and p is not None),
        "authority": "LEGACY_ELIGIBLE" if present and p is not None else "ABSTAIN",
        "authority_reasons": [],
    }


def arbitrate(votes: list[dict], base_period_s: float = BASE_PERIOD_S,
              floor_s: float = FLOOR_S, max_s: float = MAX_S,
              brake_period_s: float = BRAKE_PERIOD_S) -> dict:
    """قانونِ داوریِ خالص. ورودی: لیستِ رأی‌های `_vote`. خروجی: dictِ ماشین‌خوان.

    گام‌ها (ترمز غالب، شتاب اجماعی):
      ۱) قلب‌های حاضر را جدا کن (present=True، period معتبر). هیچ حاضری → base، abstain.
      ۲) ترمزها: هر قلبِ braking یک periodِ ترمز (= max(period خودش، brake_period_s)) می‌دهد.
      ۳) اجماع = میانگینِ هندسیِ وزن‌دار (precision) روی *همهٔ* حاضرها.
      ۴) effective = max(اجماع، قوی‌ترین ترمز). سپس clamp سختِ [floor, max].
      ۵) رنگِ آشتی = بدترین (محافظه‌کارترین) رنگِ حاضرها.
    """
    present = [v for v in votes if v.get("present")
               and v.get("eligible_for_live") is True and v.get("period_s")]
    if not present:
        return {
            "effective_period_s": round(_clamp(base_period_s, floor_s, max_s), 2),
            "base_period_s": base_period_s, "consensus_s": None,
            "brake_s": None, "color": "GREEN", "driver": "abstain",
            "reasons": ["هیچ قلبی رأی نداد — periodِ پایه (رفتارِ فعلی)"],
            "votes": votes, "n_present": 0, "n_braking": 0,
            "n_moving": 0, "n_held": 0, "n_constant": 0, "n_unknown_mode": 0,
        }

    # ترمزها — هر ترمز دستِ‌کم تا brake_period_s بالا می‌برد (شتاب خلعش نمی‌کند)
    brakes = [max(float(v["period_s"]), brake_period_s)
              for v in present if v.get("braking")]
    brake_s = max(brakes) if brakes else None

    # اجماع = میانگینِ هندسیِ وزن‌دار (precision با کفِ PI_FLOOR برای حاضرها)
    num = 0.0
    den = 0.0
    for v in present:
        pi = max(PI_FLOOR, float(v["precision"]))
        num += pi * math.log(float(v["period_s"]))
        den += pi
    consensus = math.exp(num / den) if den > 0 else base_period_s

    effective = consensus if brake_s is None else max(consensus, brake_s)
    effective = _clamp(effective, floor_s, max_s)

    # رنگِ آشتی = بدترینِ حاضرها
    worst_rank = max(_COLOR_RANK.get(v.get("color", "GREEN"), 0) for v in present)
    color = _RANK_COLOR[worst_rank]

    # رانندهٔ نبض (چه کسی period را تعیین کرد) + دلایل
    reasons: list[str] = []
    if brake_s is not None and effective >= brake_s - 1e-6:
        drivers = [v["heart"] for v in present
                   if v.get("braking") and max(float(v["period_s"]), brake_period_s) >= brake_s - 1e-6]
        driver = "brake:" + "+".join(drivers) if drivers else "brake"
        for v in present:
            if v.get("braking"):
                reasons.append(f"ترمزِ «{v['heart']}»: {v.get('note') or 'braking'} → period≥{brake_s:.0f}s")
    else:
        # ── قاعدهٔ سختِ C11 (۲۰۲۶-۰۸-۰۳): «اجماع» فقط وقتی معنا دارد که بیش از یک
        # قلب واقعاً حرف تازه بزند. سنجیده: با یک متحرک و دو ثابت، این تابع
        # `driver="consensus"` و `n_present=3` و `color=GREEN` منتشر می‌کرد —
        # بلندترین دروغِ باربرِ ارگانیسم. حضور رأی نیست؛ حرکت رأی است.
        movers = [v["heart"] for v in present if v.get("mode") == "LIVE"]
        if len(movers) == 1:
            driver = f"solo:{movers[0]}"
            reasons.append(f"تنها «{movers[0]}» متحرک است؛ بقیه نگه‌داشته/ثابت‌اند — "
                           f"اجماع نیست، یک قلب می‌راند → {consensus:.0f}s")
        elif not movers:
            driver = "frozen"
            reasons.append(f"هیچ قلبی حرف تازه ندارد (همه HELD/CONSTANT) → {consensus:.0f}s "
                           f"عددی ثابت است، نه اجماع")
        else:
            driver = "consensus"
            fastest = min(present, key=lambda v: float(v["period_s"]))
            reasons.append(f"اجماعِ {len(movers)} قلبِ متحرک (از {len(present)} حاضر، وزن‌دار) "
                           f"→ {consensus:.0f}s؛ تندترین «{fastest['heart']}» "
                           f"{float(fastest['period_s']):.0f}s")
    if color == "RED":
        reasons.append("رنگِ آشتی RED — throttle/observe (بدترین قلبِ حاضر)")

    return {
        "effective_period_s": round(effective, 2),
        "base_period_s": base_period_s,
        "consensus_s": round(consensus, 2),
        "brake_s": None if brake_s is None else round(brake_s, 2),
        "color": color,
        "driver": driver,
        "reasons": reasons,
        "votes": votes,
        "n_present": len(present),
        "n_braking": len(brakes),
        # C11: تفکیکِ «حاضر» از «متحرک». `n_present=3` تنها چیزی بود که منتشر
        # می‌شد و همان اطمینانِ کاذب می‌ساخت — سه رأی، ولی یکی حرف تازه داشت.
        "n_moving": sum(1 for v in present if v.get("mode") == "LIVE"),
        "n_held": sum(1 for v in present if v.get("mode") == "HELD"),
        "n_constant": sum(1 for v in present if v.get("mode") == "CONSTANT"),
        "n_unknown_mode": sum(1 for v in present if v.get("mode") == "UNKNOWN"),
    }


# ════════════════════════════════════════════════════════════════════════════════
# جمع‌آوریِ رأی‌ها از سه قلب (read-only، fail-soft، بدونِ side-effect)
# ════════════════════════════════════════════════════════════════════════════════
def _cardiac_vote(cardiac_snapshot: dict | None = None) -> dict:
    """قلبِ ۱ — cardiac (آلومتریک). read-only از `cardiac.status_snapshot`/`effective_period`.
    ترمز = بودجهٔ ضربان ته‌کشیده (resting-only)."""
    try:
        snap = cardiac_snapshot
        if snap is None:
            import cardiac  # _ops/cardiac.py
            snap = cardiac.status_snapshot()
        if not snap or not snap.get("enabled"):
            return _vote("cardiac", None, False, 0.0, present=False,
                         note="OCTOPUS_WIRE_BIO خاموش — abstain")
        bio = snap.get("bio_rhythm") or {}
        bud = snap.get("budget") or {}
        baro = snap.get("baroreflex_factor")
        period = bio.get("period_s")
        if baro is not None and period is not None:
            period = float(period) * float(baro)
        depleted = bool(bud.get("depleted"))
        pace = bio.get("pace", "balanced")
        color = "AMBER" if depleted else "GREEN"
        # تمبرِ ساختاری (C11): `bio_rhythm.period_s` تابعِ قطعیِ mass است و mass فقط
        # از organهای بودجه و `fitness attribution.confirmed` رشد می‌کند. تا وقتی
        # mass روی کفِ ۱.۰ نشسته، این عدد ریاضیاً ثابت است — پس CONSTANT با dof=1،
        # بدونِ نیاز به هیچ تاریخچه‌ای. سنجیده: از ۰۷-۲۸ همان ۴۲.۴۲۶۴ ثانیه.
        _mass = bio.get("mass")
        _pinned = (_mass is None) or (float(_mass) <= 1.0)
        _mode = "CONSTANT" if _pinned else "LIVE"
        return _mark_live_authority(
            _vote("cardiac", period, depleted, 1.0, color=color,
                  mode=_mode, dof=1 if _pinned else 0,
                  note=f"pace={pace}" + (" · بودجه تمام" if depleted else "")),
            "CARDIAC_RUNTIME")
    except Exception as e:  # noqa: BLE001 — قلبِ غایب هرگز داور را نمی‌کشد
        return _vote("cardiac", None, False, 0.0, present=False,
                     note=f"err:{type(e).__name__}")


def _control_vote(heart_shadow: dict | None = None) -> dict:
    """قلبِ ۲ — control_law (velocity-first). read-only از `shadow.read_shadow_latest`
    یا محاسبهٔ خالصِ `heart_step(gather_inputs())`. ترمز = fail_closed_reason غیرِ None."""
    try:
        rec = heart_shadow
        if rec is not None and not isinstance(rec, dict):
            return _authority_vote(
                _vote("control_law", None, False, 0.0, present=False,
                      note="malformed control-law observation"),
                authority="MALFORMED_INPUT",
                reasons=["control-law observation is not an object"])
        if rec is None:
            from heart import shadow as _sh
            rec = _sh.read_shadow_latest()
        tel = {}
        period = None
        if rec:
            period = rec.get("period_s")
            tel = rec.get("telemetry") or {}
        else:
            # هیچ رکوردِ سایه‌ای نیست → محاسبهٔ خالصِ read-only (بدونِ نوشتن)
            from heart import control_law as _cl
            sig, tel = _cl.heart_step(_cl.gather_inputs())
            period = sig.period_s
        gates = tel.get("gates") or {}
        reason = gates.get("fail_closed_reason")
        drift = bool(gates.get("drift_flag"))
        braking = bool(reason) or drift
        pi = gates.get("precision")
        precision = float(pi) if isinstance(pi, (int, float)) else 1.0
        color = "RED" if braking else "GREEN"
        note = reason or ("drift" if drift else "velocity-tracking")
        # تمبرِ کهنگی (C11): این ظرف هر ~۵ بیت (~۲۲۰s) **نوشته** و هر تیک (~۵۷s)
        # **خوانده** می‌شود. یعنی چهار تیک از پنج، یک اسنپ‌شاتِ نگه‌داشته‌شده به‌عنوان
        # رأیِ زنده شمرده می‌شد. با `ts` ِ خودِ رکورد سنجیده می‌شود، نه با mtime —
        # ۱۴ از ۲۰ فایلِ این پوشه گیت‌tracked اند و mtime شان آرتیفکتِ merge است.
        _mode, _dof = "LIVE", 0
        try:
            import provenance as _prov   # _ops/provenance.py
            _st = _prov.stamp(period, "heart-shadow-latest.json",
                              _prov.observed_in(rec or {}), _SHADOW_CADENCE_S)
            _mode = _st.get("mode", "UNKNOWN")
            _dof = int(_st.get("dof") or 0)
        except Exception:  # noqa: BLE001
            _mode = "UNKNOWN"
        vote = _vote("control_law", period, braking, precision, color=color,
                     mode=_mode, dof=_dof, note=str(note))
        # Precision is observation metadata, not authority. Keep the canonical value
        # available for forensic output even when G4 excludes this vote from live math.
        if isinstance(pi, (int, float)):
            vote["_canonical_precision"] = float(pi)
        allowed, authority, authority_reasons = _control_authority(rec)
        if not allowed:
            return _authority_vote(vote, authority=authority,
                                   reasons=authority_reasons)
        return _mark_live_authority(vote, authority, authority_reasons)
    except Exception as e:  # noqa: BLE001
        return _vote("control_law", None, False, 0.0, present=False,
                     note=f"err:{type(e).__name__}")


def _rhythm_vote(rhythm_state: dict | None = None) -> dict:
    """قلبِ ۳ — chrono_rhythm (HRV/mode). read-only از rhythm_state (dictِ `rhythm_beat`).
    نکتهٔ آشتی: RED در ریتم یعنی throttle/observe (mode_focus=CALM) — پس در نبضِ واحد
    **ترمز** است، نه T_beatِ تندِ واکنشیِ خودش. آستانه‌های سلامتِ HRV از قبل داخلِ
    `_mode_map` رنگ را می‌سازند؛ پس ترمز را فقط به RED گره می‌زنیم (نه hrv خام — که در
    گامِ سرد=0 «کمبودِ داده» است نه فروپاشی)."""
    try:
        st = rhythm_state
        if st is None:
            sys.path.insert(0, str(_OPS / "chrono_rhythm"))
            from rhythm import Rhythm  # type: ignore
            # گامِ خنثیِ read-only (readiness/stress متوسط) — فقط برای رأیِ مستقل
            r = Rhythm()
            s = r.step(readiness=0.5, stress=0.3, novelty=0.3, sigma=0.5)
            st = {"mode_color": s.mode_color, "T_beat": s.T_beat,
                  "hrv": s.hrv, "mode_focus": s.mode_focus}
        if not st:
            return _vote("rhythm", None, False, 0.0, present=False, note="abstain")
        color = st.get("mode_color", "GREEN")
        t_beat = st.get("T_beat")
        hrv = st.get("hrv")
        braking = (color == "RED")     # RED = throttle/observe (mode_focus=CALM)
        note = f"mode={st.get('mode_focus', '?')}/{color}"
        if isinstance(hrv, (int, float)):
            note += f" · hrv={hrv:.2f}"
        # تنها قلبِ واقعاً متحرک: `organism.py` هر تیک `rhythm_beat` را تازه صدا
        # می‌زند، پس این عدد در همان تیک ساخته شده. سنجیده: ۱۰۰٪ حرکتِ اجماع فقط
        # نویزِ ۱/f همین یکی است.
        return _mark_live_authority(
            _vote("rhythm", t_beat, braking, 0.7, color=color, note=note,
                  mode="LIVE", dof=0),
            "RHYTHM_RUNTIME")
    except Exception as e:  # noqa: BLE001
        return _vote("rhythm", None, False, 0.0, present=False,
                     note=f"err:{type(e).__name__}")


def gather_views(cardiac_snapshot: dict | None = None,
                 heart_shadow: dict | None = None,
                 rhythm_state: dict | None = None) -> list[dict]:
    """سه رأی را موازی جمع کن. ورودی‌های از پیش‌گردآوری‌شده (توسطِ همان tickِ organism)
    ترجیح داده می‌شوند تا کارِ تکراری/side-effect نباشد؛ وگرنه هر قلب read-only محاسبه می‌شود.
    سپس ۲۰۲۷-alignment: precisionِ inverse-variance اعمال می‌شود (فقط با PULSE_ARBITER_PRECISION)."""
    votes = [_cardiac_vote(cardiac_snapshot),
             _control_vote(heart_shadow),
             _rhythm_vote(rhythm_state)]
    return _apply_precision(votes)


def _valid_live_baseline(previous) -> tuple["float | None", list[str]]:
    """Return the fixed pre-G4 non-acceleration anchor.

    The first G4 beat migrates a valid legacy live record by anchoring its applied
    period. Later beats reuse ``authority_floor_s`` rather than the previous applied
    period, so a transient slow/braking candidate never ratchets the floor upward.
    A temporarily closed outer wire preserves the anchor as long as the G4 record
    itself was durably written.
    """
    reasons: list[str] = []
    if not isinstance(previous, dict):
        return None, ["previous arbiter record is not an object"]
    if previous.get("schema") != SCHEMA:
        reasons.append("previous arbiter schema mismatch")
    if previous.get("written") is not True:
        reasons.append("previous arbiter record was not durably written")

    if previous.get("authority_policy") == AUTHORITY_POLICY:
        period = _finite_period(previous.get("authority_floor_s"))
        if period is None:
            reasons.append("G4 authority floor is invalid")
    else:
        if previous.get("wire_open") is not True:
            reasons.append("legacy arbiter wire was not open")
        period = _finite_period(previous.get("effective_period_s"))
        if period is None:
            reasons.append("legacy effective period is invalid")
    return (period if not reasons else None), reasons


def _apply_live_authority(snap: dict, previous=None) -> dict:
    """Apply G4's fixed non-acceleration anchor to a candidate snapshot.

    The first G4 beat imports the prior valid live period as ``authority_floor_s``.
    Every later beat reuses that fixed anchor, never the previous applied period.
    Therefore removing the ineligible shadow vote cannot accelerate the organism,
    while a transient valid brake can clear back to the pre-G4 cadence instead of
    ratcheting the organism permanently slower. Gate 1 is required to move the anchor.
    """
    out = dict(snap or {})
    candidate = _finite_period(out.get("candidate_period_s",
                                       out.get("effective_period_s")))
    anchor, baseline_reasons = _valid_live_baseline(previous)
    out["authority_policy"] = AUTHORITY_POLICY
    out["candidate_period_s"] = candidate
    out["candidate_driver"] = out.get("driver")
    out["applied_period_known"] = False
    out["authority_hold_applied"] = False
    out["authority_floor_s"] = None if anchor is None else round(anchor, 2)
    if anchor is None:
        out["authority_floor_source"] = "INVALID_OR_MISSING"
    elif (isinstance(previous, dict)
          and previous.get("authority_policy") == AUTHORITY_POLICY):
        out["authority_floor_source"] = "G4_FIXED_ANCHOR"
    else:
        out["authority_floor_source"] = "LEGACY_LIVE_BASELINE"
    requested = bool(out.get("wire_requested_open", out.get("wire_open")))
    out["wire_requested_open"] = requested
    if not requested:
        out["wire_open"] = False
        out["authority_status"] = "WIRE_CLOSED"
        return out

    if candidate is None or anchor is None:
        reasons = list(out.get("wire_reasons") or [])
        if candidate is None:
            reasons.append("candidate period is invalid")
        reasons.extend(baseline_reasons)
        reasons.append("G4 refuses live promotion without a valid prior live baseline")
        out["wire_open"] = False
        out["wire_reasons"] = reasons
        out["wire_reasons_n"] = len(reasons)
        out["authority_status"] = "NO_VALID_BASELINE"
        return out

    applied = max(candidate, anchor)
    held = applied > candidate + 1e-9
    out["effective_period_s"] = round(applied, 2)
    out["applied_period_known"] = True
    out["authority_hold_applied"] = held
    out["wire_open"] = True
    if held:
        out["driver"] = "authority-hold"
        out["authority_status"] = "HELD_NO_ACCELERATION"
        reasons = list(out.get("reasons") or [])
        reasons.append(
            f"G4 authority hold: candidate {candidate:.2f}s < fixed pre-G4 "
            f"anchor {anchor:.2f}s; acceleration refused")
        out["reasons"] = reasons
    else:
        out["authority_status"] = "CANDIDATE_SLOWER_OR_EQUAL"
    return out


# ════════════════════════════════════════════════════════════════════════════════
# API عمومی — snapshot / persist / wire_open / read_latest
# ════════════════════════════════════════════════════════════════════════════════
def arbiter_snapshot(cardiac_snapshot: dict | None = None,
                     heart_shadow: dict | None = None,
                     rhythm_state: dict | None = None,
                     beat: int = 0) -> dict:
    """snapshotِ ماشین‌خوانِ داور برای ORGANISM-STATE/UI. **هیچ نوشتن، هیچ effector.**
    همیشه امن است حتی با flag خاموش — فقط محاسبه/گزارش."""
    views = gather_views(cardiac_snapshot, heart_shadow, rhythm_state)
    out = arbitrate(views)
    out["candidate_period_s"] = out["effective_period_s"]
    out["candidate_driver"] = out["driver"]
    out["applied_period_known"] = False
    out["authority_hold_applied"] = False
    out["authority_floor_s"] = None
    out["authority_status"] = "ADVISORY_CANDIDATE"
    out["authority_policy"] = AUTHORITY_POLICY
    out["ts"] = opslib.now_iso()
    out["schema"] = SCHEMA
    out["beat"] = beat
    out["advisory_only"] = True
    out["precision_mode"] = ("active-inference (inverse-variance)"
                             if flag(FLAG_PRECISION) else "static")
    wire, wire_reasons = wire_open()
    out["wire_requested_open"] = wire
    out["wire_open"] = False
    out["wire_reasons"] = list(wire_reasons)
    out["wire_reasons_n"] = len(wire_reasons)
    return out


def persist(cardiac_snapshot: dict | None = None,
            heart_shadow: dict | None = None,
            rhythm_state: dict | None = None, beat: int = 0) -> dict:
    """snapshot را بساز و — **فقط اگر flag روشن بود** — در سینکِ جدا بنویس.
    flag خاموش → هیچ نوشتنی (`written=False`). هرگز periodِ ارگانیسم را نمی‌نویسد."""
    candidate_snap = arbiter_snapshot(cardiac_snapshot, heart_shadow, rhythm_state, beat)
    candidate_snap["written"] = False
    if not flag(FLAG_ENV):
        return _apply_live_authority(candidate_snap, previous=read_latest())
    halt_reason = "STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else opslib.halted()
    if halt_reason:
        snap = _apply_live_authority(candidate_snap, previous=read_latest())
        snap["written"] = False
        snap["wire_open"] = False
        snap["applied_period_known"] = False
        snap["authority_status"] = "HALTED"
        snap["wire_reasons"] = list(snap.get("wire_reasons") or []) + [
            f"live use refused under {halt_reason}"]
        snap["wire_reasons_n"] = len(snap["wire_reasons"])
        return snap
    snap = candidate_snap
    try:
        LATEST.parent.mkdir(parents=True, exist_ok=True)
        # Single-writer atomicity: read the prior record, apply the hold, and write
        # under one cross-process lock so two writers cannot both read the same floor
        # and race the applied period backwards.
        with opslib.LockedJson(LATEST) as lj:
            # Re-read every owner gate at the commit point. The activation file can
            # disappear after arbiter_snapshot(); stale-open must never be committed.
            gate_open, gate_reasons = wire_open()
            candidate_snap["wire_requested_open"] = gate_open
            candidate_snap["wire_reasons"] = list(gate_reasons)
            candidate_snap["wire_reasons_n"] = len(gate_reasons)
            snap = _apply_live_authority(candidate_snap, previous=lj.read())
            # Re-check kill inside the lock: a STOP/HALT that appeared after the
            # early guard must not be written as a live period (TOCTOU close).
            halt_reason = ("STOP-ORGANISM" if opslib.STOP_ORGANISM.exists()
                           else opslib.halted())
            if halt_reason:
                snap["wire_open"] = False
                snap["applied_period_known"] = False
                snap["authority_status"] = "HALTED"
                snap["wire_reasons"] = list(snap.get("wire_reasons") or []) + [
                    f"live use refused under {halt_reason}"]
                snap["wire_reasons_n"] = len(snap["wire_reasons"])
                snap["written"] = False
                return snap
            # written پیش از نوشتن ست می‌شود تا نسخهٔ روی دیسک هم صادق باشد —
            # همان الگویِ heartstate.py::persist (قبلاً فایل همیشه written:false حمل می‌کرد).
            snap["written"] = True
            lj.write(snap)
        # LATEST is the commit authority. Once it is durably written the beat is
        # committed, so a failure in the secondary sink/divergence below is logged
        # but never downgrades the already-committed live period.
        try:
            opslib.append_jsonl(SINK, {"ts": snap["ts"], "beat": beat,
                                       "effective_period_s": snap["effective_period_s"],
                                       "candidate_period_s": snap.get("candidate_period_s"),
                                       "authority_floor_s": snap.get("authority_floor_s"),
                                       "authority_status": snap.get("authority_status"),
                                       "driver": snap["driver"], "color": snap["color"],
                                       "wire_open": snap["wire_open"]})
            snap["sink_written"] = True
        except Exception as e:  # noqa: BLE001 — secondary sink never un-commits LATEST
            snap["sink_written"] = False
            opslib.alert_throttled(
                [f"pulse-arbiter secondary sink failed (LATEST committed): {e}"],
                key="pulse-arbiter-sink-secondary", window_s=3600.0)
        # Talk Discovery / heart unification: optional shadow divergence vs production
        # period hint (does NOT change effective period or age_tick).
        try:
            from heart.pulse_shadow_compare import record_divergence
            prod = float(
                (snap.get("effective_period_s") if snap.get("applied_period_known") else None)
                or (cardiac_snapshot or {}).get("effective_period")
                or BASE_PERIOD_S
            )
            record_divergence(
                production_period=prod,
                shadow_period=float(snap.get("candidate_period_s") or prod),
                run_id=str(snap.get("ts") or ""),
                tick=int(beat),
                inputs={"driver": snap.get("driver"), "color": snap.get("color")},
            )
        except Exception:  # noqa: BLE001 — divergence is optional observability
            pass
    except Exception as e:  # noqa: BLE001 — سایه نباید tick را بکشد
        snap["written"] = False                       # fail-soft
        snap["wire_open"] = False
        snap["applied_period_known"] = False
        snap["authority_status"] = "PERSIST_FAILED"
        snap["wire_reasons"] = list(snap.get("wire_reasons") or []) + [
            "arbiter state persistence failed; live use refused"]
        snap["wire_reasons_n"] = len(snap["wire_reasons"])
        # WinError 5 (os.replace cross-process lock) گذراست و self-healing — تکرارِ
        # همان پیام هر epoch آلارمِ واقعی (halt/STOP) را زیر نویز می‌برد. throttle:
        # ۱ alert/saat با همان key؛ پیامِ نو همیشه فوراً عبور می‌کند (alert_throttled
        # §fail-open). LockedJson قبلاً ۵ retry + receipt زده — این فقط سطحِ نویز است.
        opslib.alert_throttled(
            [f"pulse-arbiter sink write failed: {e}"],
            key="pulse-arbiter-sink-write", window_s=3600.0)
    return snap


def wire_open() -> tuple[bool, list[str]]:
    """آیا داور مجاز است periodِ **زندهٔ** ارگانیسم را براند؟ (نه فقط سایه.)
    مثلِ `shadow.production_wire_open` تا رأیِ صریحِ مالک ساختاراً بسته است:
      OCTOPUS_WIRE_PULSE_ARBITER ∧ OCTOPUS_WIRE_BIO ∧ ACTIVATION-PULSE-ARBITER.flag
      ∧ تاریخ ≥ 2026-07-21. امروز = بسته (درست همین است)."""
    reasons: list[str] = []
    if not flag(FLAG_ENV):
        reasons.append(f"{FLAG_ENV} خاموش")
    if not flag("OCTOPUS_WIRE_BIO"):
        reasons.append("OCTOPUS_WIRE_BIO خاموش")
    ok, why = opslib.live_gate_open(ACT_ARBITER)
    if not ok:
        reasons.append(f"live-gate: {why}")
    return (len(reasons) == 0, reasons)


def effective_period_if_open(default_s: float,
                             cardiac_snapshot: dict | None = None,
                             heart_shadow: dict | None = None,
                             rhythm_state: dict | None = None) -> tuple[float, dict]:
    """periodِ داور را **فقط اگر `wire_open()`** برگردان؛ وگرنه `default_s` (سایه).
    این تنها نقطهٔ عبورِ داور به seamِ زندهٔ organism است — و ساختاراً امروز بسته.
    خروجی: (period_s برای مصرف، snapshot برای state). fail-soft: خطا → default.
    kill supreme: زیرِ STOP/HALT هرگز period زنده برنمی‌گرداند (هم‌ارزِ persist)."""
    try:
        snap = _apply_live_authority(
            arbiter_snapshot(cardiac_snapshot, heart_shadow, rhythm_state),
            previous=read_latest())
        halt_reason = ("STOP-ORGANISM" if opslib.STOP_ORGANISM.exists()
                       else opslib.halted())
        if halt_reason:
            snap["wire_open"] = False
            snap["applied_period_known"] = False
            snap["authority_status"] = "HALTED"
            return float(default_s), snap
        if snap.get("wire_open") and snap.get("applied_period_known"):
            return float(snap["effective_period_s"]), snap
        return float(default_s), snap
    except Exception:  # noqa: BLE001
        return float(default_s), {"advisory_only": True, "error": True}


def read_latest() -> dict:
    try:
        return json.loads(LATEST.read_text("utf-8")) if LATEST.exists() else {}
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    print(json.dumps(arbiter_snapshot(), ensure_ascii=False, indent=2))
