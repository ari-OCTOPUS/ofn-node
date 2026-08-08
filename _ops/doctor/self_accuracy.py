#!/usr/bin/env python3
"""self_accuracy.py — معیارِ دقتِ خودمدل (C3، ۲۰۲۶-۰۷-۲۸).

بازسنجیِ ۲۰۲۶-۰۷-۲۵ گفت C3 «NOT_MEASURED» است: خودگزارشِ LLM در
`self_knowledge.snapshot()` با **هیچ منبعِ حقیقتی** مقایسه نمی‌شود، و اعتمادِ LLM
(`confidence`) یک self-assessment بی‌اعتباری است. فیکسِ کوریِ `LEGS_UNWRAP` حالا
۴ لِگ را دیده می‌سازد، ولی هنوز نمی‌داند تصویرش چقدر دقیق است. این ماژول آن شکاف
را می‌بندد: اولین سنجهٔ ملموسِ «چقدر از خودم نمی‌دانم».

چرا اولین قدم به‌سوی AGI است (تعریفِ مالک = آگاهی/خودمدل): تا امروز ارگانیسم
می‌توانست با اطمینانِ کامل غلط بگوید — همین که در ۰۷-۲۵ اتفاق افتاد («۱ لِگِ مرده»
در حالی که ۴ لِگ بود). وقتی مدلِ خود صادق نباشد، هر پچ روی آن سوار (جراحیِ کور)
خطرناک است. پس خودمدلِ صادق، پیش‌نیازِ خود-اصلاحیِ ایمن (C4) است.

خطِ قرمز — یادگیری ≠ تغییر: فقط‌خواندنی نسبت به state/ژنوم/ledger/kill-switch؛ تنها
خروجیِ نو، append-only به `state/doctor/self-accuracy.jsonl` (سریِ زمانیِ صداقت —
دقیقاً همان چیزی که بازسنجیِ ۰۷-۲۵ گفت «وجود ندارد»). $0 · fail-soft · هرگز tickِ
ارگانیسم را بلاک نمی‌کند. پشتِ `OCTOPUS_SELFKNOW_ACCURACY` (پیش‌فرض خاموش).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent               # _ops/doctor
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

FLAG_NAME = "OCTOPUS_SELFKNOW_ACCURACY"

# ── واسنجیِ عددِ اطمینان (WS-B، ۲۰۲۶-۰۷-۲۸) ─────────────────────────────────────
# تا امروز این ماژول فقط *برابریِ فیلد* را می‌سنجید (legs/revenue/wire_on) و عددِ
# `confidence`ِ خودمدل — همان self-assessmentی که بازسنجیِ ۰۷-۲۵ «بی‌اعتبار» خواند —
# هرگز نمره نمی‌گرفت. حالا می‌گیرد: هر فیلد یک نتیجهٔ دودویی y∈{0,1} می‌دهد و
# Brier = میانگینِ (confidence − y)² روی همان فیلدها.
#
# فضای نامِ مشترک (رفعِ «دو keyspace»): ادعا و حقیقت هر دو زیرِ `selfknow.<field>`
# می‌روند — کلیدِ ادعا == کلیدِ حقیقت، پس calibration_probe می‌تواند جفت کند. این
# دقیقاً همان الگویی است که goal_directed برای `up-*` دارد.
#
# ضدِ خودگریدی (ناوردیِ calibration_probe:21-22): عددِ confidence **هرگز** واردِ
# محاسبهٔ y نمی‌شود. y فقط از مقایسهٔ گزارش با ORGANISM-STATE.json/fitness-latest.json
# می‌آید. بالا بردنِ confidence نمی‌تواند y را بهتر کند — فقط Brier را بدتر می‌کند.
CALIB_FLAG = "CORTEX_SELF_MONITOR"      # همان فلگی که calibration_probe/self_model دارند
CLAIM_KEY_PREFIX = "selfknow."          # فضای نامِ صریح و مستند (نه ضمنی)

# فیلدهایی که خودمدل درباره‌شان ادعا دارد و ما با منبعِ حقیقت می‌سنجیم. هر کدام یک
# تابعِ `_actual_*` دارد که از state واقعی می‌خواند، و یک تابعِ `_reported_*` که ادعای
# snapshot را برمی‌دارد. هر جفت → یک ردیفِ checking.
#
# انتخابِ فیلدها بر اساسِ سابقهٔ دروغ‌های اثبات‌شده: `legs` (۰۷-۲۵: ۱ به‌جای ۴) و
# `revenue` (۰۷-۲۷: خرج به‌جای درآمد) دقیقاً همان‌هایی‌اند که زشته‌ترین باورهای غلط را
# ساختند. `wire_on`/`wire_off` هم چون اتصالِ واقعی ارگانیسم است. این لیست رشد می‌کند.


def check_flag() -> bool:
    return os.environ.get(FLAG_NAME, "0") == "1"


def _trail_path() -> Path:
    return opslib.STATE_DIR / "doctor" / "self-accuracy.jsonl"


def _claims_path() -> Path:
    """لِجِرِ ادعاهای خود — همان فایلی که self_model/goal_directed می‌نویسند و
    calibration_probe.CLAIMS می‌خواند. تابع است نه ثابت، تا monkeypatchِ
    opslib.STATE_DIR در تست واقعاً مسیر را جابه‌جا کند."""
    return opslib.STATE_DIR / "cortex" / "self-claims.jsonl"


def _self_monitor_on() -> bool:
    """فلگِ CORTEX_SELF_MONITOR روشن؟ (دقیقاً منطقِ calibration_probe/self_model/
    goal_directed — وجود/truthy = روشن)."""
    v = str(os.environ.get(CALIB_FLAG, "")).strip().lower()
    return v not in ("", "0", "false", "no", "off")


def _read_json(rel: str, default=None):
    try:
        return json.loads((opslib.STATE_DIR / rel).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {} if default is None else default


# ── منابعِ حقیقت (از state واقعی، نه از ادعای snapshot) ────────────────────────
def _actual_legs() -> set:
    """نامِ لِگ‌های واقعی از ORGANISM-STATE — همان unwrap که snapshot با LEGS_UNWRAP
    می‌کند، ولی این‌جا مستقل از فلگ همیشه لایهٔ درونی را می‌گیرد (منبعِ حقیقت نباید
    خودش کور باشد). PII-free: فقط نامِ لِگ، بدونِ محتوا."""
    org = _read_json("ORGANISM-STATE.json", {})
    if not isinstance(org, dict):
        return set()
    names: set = set()
    inner = org.get("business_legs")
    # همان ساختارِ دو-لایه‌ای که ۰۷-۲۵ پیدا شد: بیرونی یک عددِ beat دارد، درونی لِگ‌ها.
    if isinstance(inner, dict) and isinstance(inner.get("business_legs"), dict):
        names |= set(inner["business_legs"].keys())
    elif isinstance(inner, dict):
        names |= set(inner.keys())
    # بازوهای با کلیدِ جدا (ziman/leg/cartographer) — نیمهٔ گمشدهٔ ۰۷-۲۷
    # ⚠️ self_knowledge خط ۲۰۶ این‌ها را به‌نامِ متفاوت گزارش می‌دهد:
    #   org key "leg" → reported as "lead"
    # پس این‌جا هم باید به همان نام بشماریم تا drift نگیرد.
    for k, reported_as in (("ziman", "ziman"), ("leg", "lead"),
                           ("cartographer", "cartographer")):
        blk = org.get(k)
        if isinstance(blk, dict) and blk:
            names.add(reported_as)
    # ۲۰۲۶-۰۸-۰۸: self_knowledge خط ۲۲۴ یک leg مصنوعی به نام "system" اضافه می‌کند
    # برای بخش‌های درونی (heart, cortex, doctor, money و غیره از part-loops-latest).
    # اگر part-loops-latest وجود دارد، "system" هم بخشی از آناتومیِ گزارش‌شده است.
    # بدونِ این، self_accuracy همیشه یک drift می‌داد چون "system" را در reported
    # می‌دید ولی در actual نه.
    pl_file = opslib.STATE_DIR / "cortex" / "part-loops-latest.json"
    if pl_file.exists():
        names.add("system")
    # ونچر هم اگر پروژهٔ استودیو وجود دارد
    vp = opslib.ORG_ROOT / "03 - Projects"
    if vp.exists():
        names.add("studio_pf")
    return names


def _actual_revenue() -> float:
    """درآمدِ محقق‌شده به دلار — همان `_revenue_confirmed` که self_knowledge دارد،
    ولی مستقل بازنویسی شده تا منبعِ حقیقت از خودِ ادعا تغذیه نکند (شکستنِ دایره)."""
    att = (_read_json("fitness-latest.json", {}) or {}).get("attribution") or {}
    cells = att.get("revenue_by_cell") or att.get("by_cell") or {}
    if not isinstance(cells, dict):
        return 0.0
    total = 0.0
    for v in cells.values():
        try:
            total += float(v or 0.0)
        except (TypeError, ValueError):
            continue
    return round(total, 2)


def _actual_wire() -> tuple[set, set]:
    """(روشن، خاموش) از wiringِ واقعی ORGANISM-STATE — منبعِ حقیقتِ اتصال."""
    wiring = (_read_json("ORGANISM-STATE.json", {}) or {}).get("wiring")
    if not isinstance(wiring, dict):
        return set(), set()
    keys = {k for k in wiring if str(k).startswith("wire_")}
    on = {k for k in keys if wiring[k]}
    off = {k for k in keys if not wiring[k]}
    return on, off


# ── ادعاهای snapshot (آنچه خودمدل می‌گوید) ──────────────────────────────────────
def _reported_legs(snap: dict) -> set:
    legs = snap.get("legs")
    return set(legs.keys()) if isinstance(legs, dict) else set()


def _reported_revenue(snap: dict) -> float:
    r = snap.get("revenue")
    try:
        return round(float(r or 0.0), 2)
    except (TypeError, ValueError):
        return 0.0


def _reported_wire(snap: dict) -> tuple[set, set]:
    on = set(snap.get("wire_on") or [])
    off = set(snap.get("wire_off") or [])
    return on, off


def _check(name: str, reported, actual) -> dict | None:
    """یک مقایسهٔ تک‌فیلد. برابری با == سنجیده می‌شود (set/float/هرچیز). None یعنی
    منبعِ حقیقت در دسترس نبود (مثلاً state خالی) → آن فیلد شمرده نمی‌شود نه غلط."""
    if actual is None:
        return None
    ok = reported == actual
    drift = None
    if not ok:
        # برای setها: تفاضلِ متقارن را بشمار تا «چقدر دور» برمعدد شود.
        if isinstance(reported, set) and isinstance(actual, set):
            drift = len(reported ^ actual)
        else:
            drift = "mismatch"
    return {"field": name, "reported": _jsonable(reported),
            "actual": _jsonable(actual), "ok": ok, "drift": drift}


def _jsonable(v):
    """set را به sorted list تبدیل کن تا در JSON سریال شود."""
    return sorted(v) if isinstance(v, set) else v


# ── عددِ اطمینان: ادعا، و نمره‌اش ───────────────────────────────────────────────
def _prior_confidence() -> float | None:
    """اطمینانی که خودمدل در **دورِ قبل** اعلام کرد (`understanding.confidence` در
    `state/doctor/self-knowledge-latest.json`).

    چرا دورِ قبل و نه همین دور: در `self_knowledge.run()` سنجشِ دقت *پیش از*
    `synthesize()` اجرا می‌شود، پس اطمینانِ این دور هنوز وجود ندارد. استفاده از
    نسخهٔ قبل ساختارِ درستِ پیش‌بینی→نتیجه را می‌دهد (ادعا اول، حقیقت بعد) و
    ساختاراً جلوی «اطمینان را بعد از دیدنِ نتیجه تنظیم کن» را می‌گیرد.

    نبود/غیرعددی → None (نمره‌ای داده نمی‌شود؛ نبودِ شاهد، شاهدِ نبود نیست).
    ورودیِ ۰..۱۰۰ هم پذیرفته و نرمال می‌شود."""
    u = (_read_json("doctor/self-knowledge-latest.json", {}) or {}).get("understanding")
    if not isinstance(u, dict):
        return None
    c = u.get("confidence")
    if isinstance(c, bool) or not isinstance(c, (int, float)):
        return None
    c = float(c)
    if c > 1.0:
        c = c / 100.0
    return round(max(0.0, min(1.0, c)), 6)


def _confidence_brier(checks: list, conf: float | None) -> float | None:
    """Brier عددِ اطمینان روی همین دور: میانگینِ (conf − y)² که y=1 اگر آن فیلد
    درست بوده باشد. همان فرمولِ calibration_probe._brier — عمداً یکسان تا سریِ
    محلی و سریِ probe قابلِ مقایسه بمانند. بدونِ conf یا بدونِ فیلد → None."""
    if conf is None or not checks:
        return None
    return round(sum((conf - (1 if c["ok"] else 0)) ** 2 for c in checks) / len(checks), 6)


def _emit_calibration_pair(checks: list, conf: float | None) -> int:
    """جفتِ (ادعا، حقیقت) هم‌کلید بنویس تا calibration_probe بتواند جفت کند.

      · ادعا  → `cortex/self-claims.jsonl` : {key: "selfknow.<field>", confidence}
      · حقیقت → `doctor/self-accuracy.jsonl` : {key: "selfknow.<field>", correct: 0/1}

    هر دو زیرِ **CORTEX_SELF_MONITOR** (خاموشِ پیش‌فرض → صفر ردیف، byte-identical).
    ناوردی: `correct` فقط از `c["ok"]` می‌آید — یعنی از مقایسهٔ گزارش با stateِ
    مستقل. `conf` هیچ‌جا در تعیینِ `correct` دخالت ندارد (ضدِ خودگریدی).
    خروجی = تعدادِ جفت‌های نوشته‌شده. fail-soft."""
    if conf is None or not checks or not _self_monitor_on():
        return 0
    written = 0
    try:
        cp = _claims_path()
        cp.parent.mkdir(parents=True, exist_ok=True)
        ts = opslib.now_iso()
        for c in checks:
            key = f"{CLAIM_KEY_PREFIX}{c['field']}"
            opslib.append_jsonl(cp, {"key": key, "confidence": conf, "ts": ts,
                                     "source": "self_accuracy",
                                     "schema": "self-claim.v1"})
            _append_trail({"ts": ts, "key": key, "correct": 1 if c["ok"] else 0,
                           "kind": "truth", "schema": "selfknow-truth.v1"})
            written += 1
    except Exception as e:  # noqa: BLE001 — صدورِ جفت هرگز سنجش را نمی‌کشد
        try:
            opslib.alert([f"self_accuracy calibration pair failed: {e}"])
        except Exception:  # noqa: BLE001
            pass
    return written


def measure(snap: dict, *, persist: bool = True) -> dict:
    """دقتِ خودمدل را در برابرِ منابعِ حقیقتِ مستقل می‌سنجد.

    خروجی: {ts, fields_checked, fields_correct, accuracy, drifts[]}.
      · accuracy = correct / checked (۰..۱). اگر صفر فیلد قابل‌سنجش بود → None
        (نه ۰ نه ۱: «نامعلوم»، صادقانه‌تر از هر عددِ ساختگی).
      · drifts = لیستِ فیلدهای غلط با reported/actual.

    fail-soft: هر خطا → {accuracy: None, error: ...}؛ هرگز فراخواننده را نمی‌کشد.
    هرگز state/ژنوم/ledger را نمی‌نویسد — فقط `self-accuracy.jsonl` (append-only)."""
    try:
        checks = [
            _check("legs", _reported_legs(snap), _actual_legs()),
            _check("revenue", _reported_revenue(snap), _actual_revenue()),
            _check("wire_on", _reported_wire(snap)[0], _actual_wire()[0]),
        ]
        checks = [c for c in checks if c is not None]
        checked = len(checks)
        correct = sum(1 for c in checks if c["ok"])
        accuracy = round(correct / checked, 3) if checked else None
        drifts = [c for c in checks if not c["ok"]]
        # عددِ اطمینان هم نمره می‌گیرد، نه فقط برابریِ فیلد (WS-B): conf از نسخهٔ
        # قبلِ خودشناسی، y از همین سنجشِ مستقل. هیچ‌کدام دیگری را نمی‌سازد.
        conf = _prior_confidence()
        rec = {
            "ts": opslib.now_iso(),
            "fields_checked": checked,
            "fields_correct": correct,
            "accuracy": accuracy,
            "confidence": conf,
            "confidence_brier": _confidence_brier(checks, conf),
            "drifts": [{"field": d["field"], "reported": d["reported"],
                        "actual": d["actual"], "drift": d["drift"]} for d in drifts],
        }
        if persist:
            # جفتِ هم‌کلید اول (زیرِ CORTEX_SELF_MONITOR؛ خاموش → صفر ردیف)، بعد خلاصه.
            emitted = _emit_calibration_pair(checks, conf)
            if emitted:
                rec["claims_emitted"] = emitted
            _append_trail(rec)
        return rec
    except Exception as e:  # noqa: BLE001 — سنجشِ صداقت هرگز خودشناسی را نکشد
        return {"accuracy": None, "error": type(e).__name__, "drifts": []}


def _append_trail(rec: dict) -> None:
    """سریِ زمانیِ صداقت — append-only، atomic-per-line (الگوی opslib.append_jsonl).
    این فایل تا امروز وجود نداشت: بازسنجیِ ۰۷-۲۵ گفت C8 «حاضر ولی نه سنجش‌پذیر» است،
    و C3 «NOT_MEASURED». این ردیف‌ها همان «چقدر از خودم دروغ می‌گویم» را در زمان ثبت
    می‌کنند — پیش‌نیازِ هر پچِ ایمن (C4)."""
    try:
        p = _trail_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def run_from_snapshot(snap: dict) -> dict:
    """نقطهٔ ورودِ wiring: self_knowledge.run() این را با snapshot خود صدا می‌زند.
    نامِ `run_from_snapshot` صریح است تا با `self_knowledge.run()` اشتباه نشود.
    فلگ خاموش → {} (byte-identical با نبودِ ماژول)."""
    if not check_flag():
        return {}
    return measure(snap, persist=True)


if __name__ == "__main__":
    # smoke آفلاین: snapshotِ نمونه بساز و بسنج. در پروسهٔ تستِ واقعی، snapshot از
    # state سندباکس خوانده می‌شود؛ این‌جا فقط خودِ تابع را تمرین می‌کنیم.
    _HERE.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(FLAG_NAME, "1")
    fake_snap = {"legs": {"mining": {"live": False}}, "revenue": 0.0,
                 "wire_on": ["wire_doctor"], "wire_off": []}
    print(json.dumps(run_from_snapshot(fake_snap), ensure_ascii=False, indent=2))
