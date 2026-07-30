"""budget_judge — WAVE W1: قاضیِ بقا که بودجهٔ CPU/API را هر ضربان پخش می‌کند.

قراردادِ حاکم: GENOME LOCK v2026-07-27، LOCK-C.
  · ~۹۰٪ ظرفیت برای خودِ ارگانیسم، **۱۰٪ رزروِ دست‌نخوردنیِ مالک**.
  · هر تیک: CPU، RAM، سهمیهٔ API، عمقِ صف و نرخِ خطا خوانده شود.
  · معادلهٔ بقا بودجه را دوباره پخش کند.
  · سقفِ سخت: لپ‌تاپ هرگز هنگ نکند؛ فشار → کاهشِ **یکنواخت** به لایهٔ کندتر.
  · هرگز asystoleِ خاموش؛ DORMANT فقط از مسیرِ مجازِ fail-closed.

    B_i = 0.9 · B_total · (w_i · u_i · (1−r_i)) / Σ_j (w_j · u_j · (1−r_j))

چرا این ماژول قلبِ دومی نمی‌سازد
────────────────────────────────
`cardiac.py` و `heart/control_law.py` از قبل ضربان را تعیین می‌کنند و
`BeatBudget` سقفِ روزانه را نگه می‌دارد. این ماژول **جایگزینشان نیست**؛ یک
لایهٔ قضاوتِ فقط‌خواندنی است که یک `BudgetPlan` تولید می‌کند. مصرف‌کننده‌ها
بعداً و پشتِ فلگِ خودشان به آن گوش می‌دهند. §۵.۷: «wire don't bypass».

مرزهای ساختاری
──────────────
· پیش‌فرض **dry-run**: بدونِ `OCTOPUS_WIRE_BUDGET_JUDGE=1` هیچ فایلی نوشته نمی‌شود.
· `owner_reserve` هرگز به هیچ پایی تخصیص نمی‌یابد — نه با ورودیِ خراب، نه با
  وزنِ بی‌نهایت، نه با صفر شدنِ مخرج. تستِ totality این را ثابت می‌کند.
· هر تابعِ سهم **کل** است: ورودیِ NaN/inf/منفی/خالی → مقدارِ امنِ تعریف‌شده،
  هرگز استثنا و هرگز تخصیصِ رهاشده.
· نوشتنِ اتمیک + `prev_sha256` (هم‌سبکِ organ-gate-log).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent   # heart/ → _ops/
# ⚠️ عمداً `heart/` و نه `cardiac/`: پوشه‌ای به نامِ cardiac با ماژولِ موجودِ
# `cardiac.py` تصادم می‌کند و `import cardiac` را به پوشهٔ خالی می‌بَرد.
# نسخهٔ اول همین کار را کرد و test_cardiac_allometry بلافاصله قرمز شد.
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_BUDGET_JUDGE"
SCHEMA = "budget-plan.v1"
PLAN_PATH = opslib.STATE_DIR / "pulse" / "budget-plan.json"
LEDGER_PATH = opslib.STATE_DIR / "pulse" / "budget-plan.jsonl"

# LOCK-C: رزروِ مالک. این عدد مرز است، نه تنظیم — تستِ totality رویش قفل دارد.
OWNER_RESERVE = 0.10
ORGANISM_SHARE = 1.0 - OWNER_RESERVE

# سقف‌های سختِ میزبان. فراتر → کاهشِ یکنواخت.
CPU_MAX = float(os.environ.get("OCTOPUS_CPU_MAX_PCT", "80"))
RAM_MAX = float(os.environ.get("OCTOPUS_RAM_MAX_PCT", "85"))

# لایه‌های ضربان (Heart Design v1 — بازتعریف نمی‌شود، فقط انتخاب).
PULSE_LAYERS = ("L0", "L1", "L2", "DORMANT")

# کف و سقفِ سهمِ هر پا — هیچ پایی نه گرسنه می‌ماند نه همه را می‌بلعد.
FLOOR = 0.02
CEIL = 0.45

# وزنِ نقش. Math/Judge وقتی عدم‌قطعیت بالاست بیشتر می‌گیرد (LOCK-C).
ROLE_WEIGHT = {
    "brain": 1.4, "math": 1.3, "doctor": 1.1,
    "lead": 1.2, "ziman": 1.0, "mining": 0.8, "crypto": 0.8,
    "accounting": 0.9, "knowledge": 0.7, "cartographer": 0.6,
}
_DEFAULT_WEIGHT = 0.8


# ─── توابعِ کل (هیچ‌کدام استثنا نمی‌دهند) ───────────────────────────────────
def _f(v, default=0.0) -> float:
    """هر ورودی → floatِ متناهی. NaN/inf/None/متن → default."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    return x if math.isfinite(x) else default


def clamp01(v) -> float:
    x = _f(v, 0.0)
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def host_load() -> dict:
    """بارِ میزبان. بدونِ psutil هم کار می‌کند (fail-soft به ناشناخته)."""
    cpu = ram = None
    try:
        import psutil
        cpu = _f(psutil.cpu_percent(interval=0.0), None)
        ram = _f(psutil.virtual_memory().percent, None)
    except Exception:  # noqa: BLE001 — نبودِ psutil نباید قضاوت را بکشد
        pass
    return {"cpu_pct": cpu, "ram_pct": ram,
            "known": cpu is not None and ram is not None}


def api_headroom() -> dict:
    """چقدر از سهمیهٔ مغزِ پولی مانده. ورودیِ غایب → محافظه‌کارانه نصف."""
    used = cap = None
    try:
        q = json.loads((opslib.STATE_DIR / "fugu-quota.json").read_text("utf-8"))
        used = _f(q.get("used_total"), None)
    except (OSError, ValueError):
        pass
    try:
        cap = _f(os.environ.get("FUGU_DAILY_CALL_CAP"), None)
    except Exception:  # noqa: BLE001
        pass
    if used is None or not cap or cap <= 0:
        return {"used": used, "cap": cap, "headroom": 0.5, "known": False}
    return {"used": used, "cap": cap,
            "headroom": clamp01((cap - used) / cap), "known": True}


def pulse_layer(load: dict, headroom: float) -> tuple:
    """کدام لایهٔ ضربان. **یکنواخت**: فشارِ بیشتر هرگز لایهٔ تندتر نمی‌دهد.

    DORMANT از این‌جا هرگز انتخاب نمی‌شود — خوابِ کامل فقط از مسیرِ مجازِ
    fail-closed می‌آید (Heart v1). این تابع حداکثر تا L2 پایین می‌آید."""
    cpu = _f(load.get("cpu_pct"), 0.0)
    ram = _f(load.get("ram_pct"), 0.0)
    h = clamp01(headroom)
    if cpu >= CPU_MAX or ram >= RAM_MAX:
        return "L2", f"بارِ میزبان بالا (cpu={cpu:.0f}% ram={ram:.0f}%)"
    if cpu >= CPU_MAX * 0.75 or ram >= RAM_MAX * 0.85 or h <= 0.1:
        return "L1", f"فشارِ متوسط (cpu={cpu:.0f}% ram={ram:.0f}% سهمیه={h:.0%})"
    return "L0", "میزبان و سهمیه سالم"


def organ_signals(state: dict | None = None) -> dict:
    """u (فوریت) و r (ریسکِ اخیر) برای هر پا — از stateِ زنده، fail-soft."""
    org = state if isinstance(state, dict) else {}
    if not org:
        try:
            org = json.loads(
                (opslib.STATE_DIR / "ORGANISM-STATE.json").read_text("utf-8"))
        except (OSError, ValueError):
            org = {}
    legs = org.get("business_legs") or {}
    if isinstance(legs.get("business_legs"), dict):
        legs = legs["business_legs"]
    out = {}
    for name, v in (legs.items() if isinstance(legs, dict) else []):
        if not isinstance(v, dict):
            continue
        live = bool(v.get("live"))
        out[name] = {"u": 0.9 if live else 0.3, "r": 0.0 if live else 0.2}
    for extra in ("brain", "math", "doctor"):
        out.setdefault(extra, {"u": 0.7, "r": 0.0})
    return out


def allocate(signals: dict, *, weights: dict | None = None) -> dict:
    """معادلهٔ بقا. **کل**: هر ورودی → تخصیصِ معتبر یا تخصیصِ خالی.

    ناوردی‌های تضمین‌شده:
      · Σ B_i ≤ ORGANISM_SHARE (رزروِ مالک هرگز پخش نمی‌شود)
      · هیچ B_i منفی یا NaN
      · مخرجِ صفر / ورودیِ خالی → تخصیصِ خالی، نه تقسیم بر صفر
    """
    w_map = weights if isinstance(weights, dict) else ROLE_WEIGHT
    terms = {}
    for name, s in (signals.items() if isinstance(signals, dict) else []):
        if not isinstance(name, str) or not name.strip():
            continue
        s = s if isinstance(s, dict) else {}
        w = max(0.0, _f(w_map.get(name, _DEFAULT_WEIGHT), _DEFAULT_WEIGHT))
        u = clamp01(s.get("u", 0.5))
        r = clamp01(s.get("r", 0.0))
        t = w * u * (1.0 - r)
        if t > 0.0 and math.isfinite(t):
            terms[name] = t
    total = sum(terms.values())
    if total <= 0.0 or not math.isfinite(total):
        return {}
    raw = {k: ORGANISM_SHARE * v / total for k, v in terms.items()}
    # کف/سقف، بعد نرمال‌سازیِ دوباره تا مجموع از سهمِ ارگانیسم رد نشود
    capped = {k: min(CEIL, max(FLOOR, v)) for k, v in raw.items()}
    s2 = sum(capped.values())
    if s2 > ORGANISM_SHARE and s2 > 0:
        capped = {k: v * ORGANISM_SHARE / s2 for k, v in capped.items()}
    return {k: round(v, 6) for k, v in capped.items()}


def plan(*, state: dict | None = None, load: dict | None = None,
         api: dict | None = None) -> dict:
    """BudgetPlan v1. فقط‌خواندنی — چیزی نمی‌نویسد."""
    ld = load if isinstance(load, dict) else host_load()
    ap = api if isinstance(api, dict) else api_headroom()
    layer, why = pulse_layer(ld, ap.get("headroom", 0.5))
    sig = organ_signals(state)
    alloc = allocate(sig)
    reasons = [why]
    if not ld.get("known"):
        reasons.append("بارِ میزبان ناشناخته — محافظه‌کارانه قضاوت شد")
    if not ap.get("known"):
        reasons.append("سهمیهٔ API ناشناخته — نصف فرض شد")
    if not alloc:
        reasons.append("هیچ سیگنالِ معتبری نبود — تخصیصِ خالی، رزرو دست‌نخورده")
    return {
        "schema": SCHEMA,
        "ts": opslib.now_iso(),
        "pulse_layer": layer,
        "owner_reserve": OWNER_RESERVE,
        "organism_share": ORGANISM_SHARE,
        "allocated_total": round(sum(alloc.values()), 6),
        "organ_pct": alloc,
        "host": ld,
        "api": ap,
        "reasons": reasons,
        "dry_run": not enabled(),
    }


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _prev_sha() -> str:
    try:
        if not LEDGER_PATH.exists():
            return ""
        lines = [x for x in LEDGER_PATH.read_text("utf-8").splitlines() if x.strip()]
        if not lines:
            return ""
        return hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()
    except OSError:
        return ""


def emit(p: dict | None = None) -> dict:
    """نقشه را بنویس — فقط با فلگ. dry-run → همان نقشه، صفر نوشتن."""
    p = p if isinstance(p, dict) else plan()
    if not enabled():
        return {"ok": True, "written": False, "plan": p}
    rec = {**p, "prev_sha256": _prev_sha()}
    try:
        PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = PLAN_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, PLAN_PATH)
        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        opslib.alert([f"budget_judge: نوشتنِ نقشه شکست ({type(e).__name__}) — "
                      "قضاوت انجام شد ولی ثبت نشد"])
        return {"ok": False, "written": False, "plan": p}
    return {"ok": True, "written": True, "plan": rec}


def card() -> str:
    """کارتِ `/x` — عمداً اعلام می‌کند که ساخته شده ولی مصرف‌کننده ندارد.

    ۲۰۲۶-۰۷-۲۸ — این ماژول یک **تولیدکنندهٔ بی‌مصرف‌کننده** است، و آن تصمیمِ
    طراحی بوده نه فراموشی (سندِ بالای فایل: «مصرف‌کننده‌ها بعداً و پشتِ فلگِ
    خودشان گوش می‌دهند»). مسئله این بود که از بیرون **نامرئی** بود: فلگش را
    می‌شد مسلح کرد و هیچ‌چیز عوض نمی‌شد، بدونِ اینکه جایی بگوید چرا.

    یک قابلیتِ خاموشِ **اعلام‌شده** از یک قابلیتِ خاموشِ **پنهان** بی‌نهایت
    بهتر است — دومی شبیهِ «داریمش» به نظر می‌رسد و نداریمش. این کارت آن را
    به سطح می‌آورد تا در `/x` دیده شود و تصمیمِ سیم‌کشی جایی ثبت بماند.
    """
    on = _enabled() if "_enabled" in globals() else (
        str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on"))
    head = "⚖️ <b>قاضیِ بودجه</b>"
    if not on:
        return (f"{head} · خاموش (عمدی)\n"
                "▸ ساخته شده و سبز است، ولی <b>هیچ مصرف‌کننده‌ای ندارد</b> — "
                "طرحی تولید می‌کند که کسی نمی‌خواند.\n"
                "▸ روشن‌کردنش بدونِ سیم‌کشیِ مصرف‌کننده، فقط یک فایلِ نخوانده می‌سازد.\n"
                "▸ سیم‌کشی‌اش تخصیصِ منابعِ زنده را لمس می‌کند — <b>تصمیمِ مالک</b>، "
                "نه کارِ ایجنت.")
    return (f"{head} · روشن\n"
            "▸ طرحِ بودجه تولید و نوشته می‌شود. ⚠️ مصرف‌کننده هنوز وصل نیست، "
            "پس این عدد <b>هیچ رفتاری را عوض نمی‌کند</b>.")


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps(plan(), ensure_ascii=False, indent=1))
