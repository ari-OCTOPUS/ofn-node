#!/usr/bin/env python3
"""
cardiac.py — لایهٔ آلوستاتیکِ ضربان: سه قانونِ بیولوژیک (additive، پشتِ flag، fail-soft).

نظریهٔ کامل: 07 - Knowledge/CARDIAC-ALLOMETRY-v1.md

سه قانون (همه پشتِ OCTOPUS_WIRE_BIO=1، پیش‌فرض خاموز = no regression):
  ۱) bio_rhythm(mass) → period_s   نرخ تابعِ حجم (M^(−۱/۴)، نه ثابت)
  ۲) BeatBudget(daily_cap)          بودجهٔ ضربان (سقفِ روزانه، مجبور به انتخاب)
  ۳) baroreflex(stimulus)           پاسخِ فوریِ محیط (شتاب/کُندیِ موقت)

خطوطِ قرمز:
  - هیچ‌کدام منطقِ HLC/phi/effector-gate را لمس نمی‌کنند (TINVها دست‌نخورده).
  - فقط period_s را (به‌صورتِ advisory) پیشنهاد می‌کنند — pacemaker تصمیم می‌گیرد.
  - bio_rhythm + budget + baroreflex هرگز negative یا صفر برنمی‌گردانند (کفِ سخت).
  - fail-soft: خطایِ هر قانون → fallback به period فعلی، نه کرش.
  - $0، آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import math
import os
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402


def flag(name: str) -> bool:
    """env-flag با پیش‌فرض خاموز."""
    return os.environ.get(name, "0") == "1"


# ─── پیکربندی (env-tunable) ─────────────────────────────────────────────────────
BASE_PERIOD_S = float(os.environ.get("CHRONO_PERIOD_S", "60.0"))   # ضربانِ پایه
BIO_RESTING_FLOOR_S = float(os.environ.get("CARDIAC_RESTING_FLOOR_S", "30.0"))   # کفِ سخت
BIO_MAX_PERIOD_S = float(os.environ.get("CARDIAC_MAX_PERIOD_S", "900.0"))        # سقفِ نهنگ
BIO_DAILY_BEAT_CAP = int(os.environ.get("CARDIAC_DAILY_BEAT_CAP", "288"))         # ~۲۴h ÷ ۵دقیقه
BIO_REF_MASS = float(os.environ.get("CARDIAC_REF_MASS", "4.0"))   # mass مرجع (نهنگ/موش)
BIO_BAROREFLEX_TTL_S = float(os.environ.get("CARDIAC_BAROREFLEX_TTL_S", "300.0"))


# ════════════════════════════════════════════════════════════════════════════════
# قانونِ ۱ — bio_rhythm: نرخ تابعِ حجم (M^(−۱/۴))
# ════════════════════════════════════════════════════════════════════════════════
def estimate_mass() -> float:
    """جرمِ مفهومیِ ارگانیسم = تعدادِ پروژه‌هایِ فعّال + جریان‌هایِ فعال + کاربران.
    ساده، قابلِ اندازه‌گیری، بدونِ PII. حداقلِ پیچیدگی (CARDIAC-ALLOMETRY §8 [CHOICE]).
    """
    mass = 0.0
    # پروژه‌هایِ فعّال: اسکنِ state/ یا budgets.yaml (cheap، آفلاین)
    try:
        budgets = opslib.load_budgets()
        organs = budgets.get("organs") or {}
        for name, conf in organs.items():
            if isinstance(conf, dict):
                if str(conf.get("status", "active")).lower() in ("active", "live", "ok"):
                    mass += 1.0
    except Exception:  # noqa: BLE001
        pass
    # جریان‌هایِ درآمدِ CONFIRMED: از attribution
    try:
        fit = _read_state("fitness-latest.json")
        attr = fit.get("attribution") or {}
        mass += float(attr.get("confirmed", 0))
    except Exception:  # noqa: BLE001
        pass
    return max(mass, 1.0)   # کف: ۱ (تنها پروژه = جرمِ حداقل)


def bio_rhythm(mass: float | None = None) -> dict:
    """قانونِ ۱: period تابعِ حجم. موجودِ بزرگ‌تر → ضربانِ کندتر (نهنگ).
    برمی‌گرداند: {period_s, mass, pace, reason}. هرگز سقف/کف را رد نمی‌کند.
    معادله: period = BASE × (mass/REF)^(۱/۴)  (وارونهٔ M^(−۱/۴) برایِ period)
    """
    if not flag("OCTOPUS_WIRE_BIO"):
        return {"period_s": BASE_PERIOD_S, "mass": None, "pace": "static",
                "reason": "OCTOPUS_WIRE_BIO off — period ثابت (رفتارِ فعلی)"}
    m = mass if mass is not None else estimate_mass()
    m = max(float(m), 1.0)
    # allometric: period ∝ mass^(۱/۴). ضریبِ ملایم (نه رادیکال).
    scale = (m / BIO_REF_MASS) ** 0.25
    period = BASE_PERIOD_S * scale
    period = max(BIO_RESTING_FLOOR_S, min(BIO_MAX_PERIOD_S, period))
    # طبقه‌بندیِ pace (r/K، CARDIAC-ALLOMETRY §3)
    if scale < 0.85:
        pace, reason = "mice", f"جرمِ کم (m={m:.1f}) → ضربانِ تند و سبک (آزمایش)"
    elif scale > 1.4:
        pace, reason = "whale", f"جرمِ زیاد (m={m:.1f}) → ضربانِ کند و عمیق (تحکیم)"
    else:
        pace, reason = "balanced", f"جرمِ متعادل (m={m:.1f})"
    return {"period_s": period, "mass": m, "pace": pace, "reason": reason}


# ════════════════════════════════════════════════════════════════════════════════
# قانونِ ۲ — BeatBudget: بودجهٔ ضربان (~۱۰⁹، مجبور به انتخاب)
# ════════════════════════════════════════════════════════════════════════════════
def _setpoint_cap(state_dir: Path | None = None) -> int | None:
    """capِ روزانه از setpointِ قلب (knobِ مالک: «/heart set cap» → HeartParams.daily_beat_cap).
    ممیزیِ 07-24: digest این cap را نمایش می‌داد ولی enforcement (همین BeatBudget) فقط env را
    می‌خواند — knob سبزِ دروغ بود. کران (0,2000] = ABS_BEAT_CAP_MAX ِ interface؛ خارجِ کران/غایب
    → None (fallback به daily_cap). fail-soft، هر tick یک readِ کوچک.
    state_dir تزریقی است تا از همان درختی خوانده شود که budget در آن می‌نویسد (ایزولاسیون)."""
    try:
        p = (state_dir or opslib.STATE_DIR) / "pulse" / "heart-setpoint-latest.json"
        if not p.exists():
            return None
        c = int(json.loads(p.read_text("utf-8")).get("daily_beat_cap") or 0)
        return c if 0 < c <= 2000 else None
    except (OSError, ValueError, TypeError):
        return None


class BeatBudget:
    """بودجهٔ ضربانِ روزانه. وقتی تمام شد، pacemaker فقط ضربانِ پایه می‌زند
    (نه کارِ ارزشمند). این، سیستم را مجبور به انتخاب می‌کند — پادزهرِ ماشینِ معمار‌ساز.
    thread-safe، disk-backed (state/cardiac-budget.json)."""

    def __init__(self, daily_cap: int | None = None,
                 path: Path | None = None):
        # daily_cap صریح (تست/فراخوان) همیشه برنده است؛ فقط پیش‌فرض اجازه می‌دهد
        # setpointِ مالک آن را override کند — تا knobِ «/heart set cap» واقعاً اثر کند
        # بی‌آنکه سقفِ صریحِ یک فراخوان بی‌صدا عوض شود.
        self._cap_explicit = daily_cap is not None
        self.daily_cap = int(daily_cap if daily_cap is not None else BIO_DAILY_BEAT_CAP)
        self.path = path or (opslib.STATE_DIR / "cardiac-budget.json")
        self._lk = threading.Lock()

    def _cap(self) -> int:
        """سقفِ مؤثر: صریح → همان؛ وگرنه setpointِ قلب (کنارِ همین state) یا پیش‌فرضِ env."""
        if self._cap_explicit:
            return self.daily_cap
        return _setpoint_cap(self.path.parent) or self.daily_cap

    def _load(self) -> dict:
        try:
            if self.path.exists():
                return json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError):
            pass
        return {"date": "", "spent": 0, "resting": 0}

    def _save(self, d: dict) -> None:
        try:
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
            os.replace(tmp, self.path)
        except OSError:
            pass   # fail-soft: بودجهٔ بدونِ persist هم کار می‌کند (این پروسه)

    def _today(self) -> str:
        return opslib.today()

    def spend(self, kind: str = "active") -> dict:
        """یک ضربان خرج کن. kind ∈ {active, resting}.
        active = کارِ ارزشمند (از بودجه می‌خورد)؛ resting = ضربانِ پایه (مجانی).
        برمی‌گرداند: {remaining, depleted, mode}."""
        if not flag("OCTOPUS_WIRE_BIO"):
            return {"remaining": None, "depleted": False, "mode": "unlimited"}
        with self._lk:
            d = self._load()
            today = self._today()
            if d.get("date") != today:   # روزِ جدید → reset
                d = {"date": today, "spent": 0, "resting": 0}
            if kind == "active":
                d["spent"] = int(d.get("spent", 0)) + 1
            else:
                d["resting"] = int(d.get("resting", 0)) + 1
            self._save(d)
            # .get: فایلِ دست‌کاری‌شدهٔ بدونِ spent در مسیرِ resting دیگر KeyError نمی‌دهد.
            cap = self._cap()
            remaining = max(0, cap - int(d.get("spent", 0)))
            depleted = int(d.get("spent", 0)) >= cap
            return {"remaining": remaining, "depleted": depleted,
                    "mode": "resting-only" if depleted else "active"}

    def status(self) -> dict:
        """وضعیتِ فقط‌خواندنیِ بودجه برای UI."""
        if not flag("OCTOPUS_WIRE_BIO"):
            return {"enabled": False, "daily_cap": self.daily_cap}
        d = self._load()
        # بازبینیِ خصمانه 2026-07-17: بدونِ این، اولین tickِ روزِ بعد از یک روزِ depleted،
        # depletedِ کهنه (دیروز) را می‌دید — periodِ کش‌آمده + خرجِ resting به‌جای active.
        if d.get("date") != self._today():
            d = {"date": self._today(), "spent": 0, "resting": 0}
        cap = self._cap()
        return {"enabled": True, "date": d.get("date"),
                "spent": d.get("spent", 0), "resting": d.get("resting", 0),
                "daily_cap": cap,
                "remaining": max(0, cap - d.get("spent", 0)),
                "depleted": d.get("spent", 0) >= cap}


# ════════════════════════════════════════════════════════════════════════════════
# قانونِ ۳ — baroreflex: پاسخِ فوریِ محیط (شتاب/کُندیِ موقت)
# ════════════════════════════════════════════════════════════════════════════════
class Baroreflex:
    """وقتی یک محرکِ بیرونی می‌آید (پیام، فروش، تعامل)، period را موقتاً کم می‌کند
    (شتاب). وقتی فشار/استرس هست، period را زیاد می‌کند (کُندیِ محافظ). پاسخِ پیوسته،
    نه باینری. TTL: اثرِ محرک بعد از CARDIAC_BAROREFLEX_TTL_S محو می‌شود."""

    def __init__(self, ttl_s: float = BIO_BAROREFLEX_TTL_S):
        self.ttl_s = ttl_s
        self._lk = threading.Lock()
        self._stimuli: list[tuple[float, float]] = []   # (ts, factor); factor<1 = شتاب

    def stimulate(self, factor: float, kind: str = "external") -> None:
        """factor > ۱ = کُندی (فشار)؛ factor < ۱ = شتاب (تعامل).
        مثال: فروش جدید → factor=۰.۶ (شتاب ۴۰٪). CONFLICT → factor=۱.۵ (کُندی)."""
        if not flag("OCTOPUS_WIRE_BIO"):
            return
        factor = max(0.2, min(3.0, float(factor)))   # کف/سقفِ ایمن
        with self._lk:
            self._stimuli.append((time.time(), factor))

    def current_factor(self) -> float:
        """ضریبِ فعّال (geometric meanِ محرک‌هایِ زنده). ۱.۰ = بدون اثر."""
        if not flag("OCTOPUS_WIRE_BIO"):
            return 1.0
        now = time.time()
        with self._lk:
            live = [f for (ts, f) in self._stimuli if now - ts < self.ttl_s]
            self._stimuli = [(ts, f) for (ts, f) in self._stimuli if now - ts < self.ttl_s]
        if not live:
            return 1.0
        # geometric mean (عادلانه برای شتاب/کُندی)
        log_sum = sum(math.log(f) for f in live)
        raw = math.exp(log_sum / len(live))
        # کف/سقف دوباره: خطای اعشاریِ exp(log) ممکنه bounds رو رد کنه
        return max(0.2, min(3.0, raw))


# ════════════════════════════════════════════════════════════════════════════════
# ترکیب — periodِ مؤثر
# ════════════════════════════════════════════════════════════════════════════════
_budget: BeatBudget | None = None
_baro: Baroreflex | None = None


def _read_state(name: str) -> dict:
    try:
        p = opslib.STATE_DIR / name
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def effective_period(base_period_s: float = BASE_PERIOD_S,
                     budget: BeatBudget | None = None,
                     baro: Baroreflex | None = None) -> dict:
    """periodِ مؤثر = base × bio_scale × baro_factor × budget_mode.
    برگرداندن: {period_s, bio, budget, baro, effective}. pacemaker این را به‌عنوانِ
    پیشنهاد می‌بیند (advisory) — نه overrideِ مطلق."""
    if not flag("OCTOPUS_WIRE_BIO"):
        return {"period_s": base_period_s, "bio": None, "budget": None, "baro": None,
                "effective": False, "reason": "OCTOPUS_WIRE_BIO off"}
    bio = bio_rhythm()
    b = budget or _budget or _get_budget()
    br = baro or _baro or _get_baro()
    bs = b.status()
    bf = br.current_factor()
    period = bio["period_s"] * bf
    # اگر بودجه depleted است، فقط resting — period به سمتِ سقف می‌رود (whale-mode عمیق)
    if bs.get("depleted"):
        period = max(period, BIO_MAX_PERIOD_S * 0.6)
    period = max(BIO_RESTING_FLOOR_S, min(BIO_MAX_PERIOD_S, period))
    return {"period_s": period, "bio": bio, "budget": bs, "baro_factor": bf,
            "effective": True, "reason": bio["reason"] +
            (f" · baro={bf:.2f}" if abs(bf - 1.0) > 0.01 else "") +
            (" · بودجه تمام (resting)" if bs.get("depleted") else "")}


def _get_budget() -> BeatBudget:
    global _budget
    if _budget is None:
        _budget = BeatBudget()
    return _budget


def _get_baro() -> Baroreflex:
    global _baro
    if _baro is None:
        _baro = Baroreflex()
    return _baro


def get_layer() -> tuple[BeatBudget | None, Baroreflex | None]:
    """singletonهای لایه (برای وصل‌شدن از organism.py/dashboard). اگر flag off → (None,None)."""
    if not flag("OCTOPUS_WIRE_BIO"):
        return (None, None)
    return (_get_budget(), _get_baro())


def status_snapshot() -> dict:
    """snapshot ماشین‌خوان برای ORGANISM-STATE/UI. فقط‌خواندنی، fail-soft."""
    if not flag("OCTOPUS_WIRE_BIO"):
        return {"enabled": False}
    try:
        bio = bio_rhythm()
        bs = _get_budget().status()
        bf = _get_baro().current_factor()
        return {"enabled": True, "bio_rhythm": bio, "budget": bs,
                "baroreflex_factor": round(bf, 3)}
    except Exception as e:  # noqa: BLE001 — §۴: نباید tick/UI را بکشد
        return {"enabled": True, "error": f"{type(e).__name__}: {e}"}
