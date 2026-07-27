"""deep_think.py — جلسه‌های فکرِ عمیق: دادنِ سؤال‌های *سنگین* به مغزِ گران.

مسئله‌ای که حل می‌کند (اندازه‌گیریِ ۲۰۲۶-۰۷-۲۷):
    اشتراکِ Fugu فلت است (`cost_usd: 0.0`، `subscription: max`) ولی در کلِ ارگانیسم
    دقیقاً **یک** مشتری دارد: تخصیصِ ساعتیِ `governor_epoch`. آن فراخوان ۱۲٬۲۴۲ توکن
    می‌فرستد و ۳۹ تا ۱۱۶ کاراکتر می‌گیرد — یعنی مغزِ orchestration به‌عنوانِ مُهرِ
    ساعتیِ JSON استفاده می‌شود. هر اندامِ دیگری که واقعاً فکر می‌کند یا `secondary`
    است (که `CORTEX_LOCAL_FIRST` به مغزِ رایگانِ محلی می‌بَرَدش) یا اصلاً مغز ندارد:
    `c6_producer` و `c6_trigger` — یعنی کلِ حلقهٔ خودبهبودی — صفر فراخوانِ LLM دارند.

    شاهد: `state/paid-calls.jsonl` ۲۰۲۶-۰۷-۲۷ → ۱۰ فراخوانِ primary، همه role=orchestr،
    فاصلهٔ ~۶۰ دقیقه، `tokens_in` **دقیقاً** ۱۲۲۴۲ در هر ده تا.

چرا «بیشتر» جوابِ غلط است:
    هر فراخوانِ Fugu ۲۶ تا ۳۲ ثانیه طول می‌کشد (همان لاگ، ستونِ `ms`). پس بردنِ
    فراخوان‌های ریزِ پرتکرار (`think` با max_tokens=90) به Fugu فقط ارگانیسم را کند
    می‌کند. «حداکثر استفاده» = حداکثرِ **ارزش در هر فراخوان**، نه حداکثرِ تعداد.

طراحی:
    روز به `DEEP_THINK_SLOTS` بازه تقسیم می‌شود؛ در هر بازه حداکثر یک جلسه. موضوع
    بینِ دو هدفِ اعلام‌شدهٔ مالک می‌چرخد: «خودت را بساز» و «نقاشی را بساز». context
    از فایل‌های state ساخته می‌شود — فقط **تجمیع**، هرگز محتوا. خروجی یک کارتِ
    propose-only است؛ این ماژول هیچ‌چیز را اجرا نمی‌کند.

مرزها (سختِ ساختاری، نه قراردادی):
    · flag پیش‌فرض **خاموش** — خاموش یعنی `run()` بدونِ هیچ I/O برمی‌گردد.
    · هرگز مسیرِ PII باز نمی‌شود. سمتِ بیزنس فقط `len(glob)` می‌شمارد و هرگز
      فایلِ لید را نمی‌خوانَد — نه نام، نه ایمیل، نه متن.
    · هرگز چیزی بیرون نمی‌فرستد جز کارتِ مالک؛ هیچ effector صدا زده نمی‌شود.
    · خطا هرگز beat را نمی‌کشد (fail-soft کامل، §۴).
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_DEEP_THINK"
SCHEMA = "deep-think.v1"
LEDGER = opslib.STATE_DIR / "deep-think" / "sessions.jsonl"
SLOT_STATE = opslib.STATE_DIR / "deep-think" / "slots.json"

# سقفِ محافظه‌کار: چهار جلسه در روز. هر جلسه ~۳۰ ثانیه ⇒ ۲ دقیقه در ۲۴ ساعت.
DEFAULT_SLOTS = 4
MAX_SLOTS = 12                 # کرانِ سختِ بالا — حتی env نمی‌تواند از این رد شود
MAX_TOKENS = 1200              # جوابِ واقعی، نه مُهرِ JSON (governor: ۶۰۰ → ۵۰ کاراکتر)
MIN_ANSWER_CHARS = 200         # کوتاه‌تر از این = جوابِ بی‌ارزش، کارت نمی‌سازیم

TOPIC_SELF = "self"
TOPIC_BUSINESS = "business"


def flag_on() -> bool:
    """env-flag با پیش‌فرضِ خاموش (allowlistِ truthy، هم‌سبکِ بقیهٔ ارگانیسم)."""
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def slots_per_day() -> int:
    """تعدادِ بازه‌های روز. خارج از (0, MAX_SLOTS] → پیش‌فرض (fail-closed به کم)."""
    try:
        n = int(str(os.environ.get("DEEP_THINK_SLOTS", "")).strip())
    except (TypeError, ValueError):
        return DEFAULT_SLOTS
    return n if 0 < n <= MAX_SLOTS else DEFAULT_SLOTS


def current_slot(now: "_dt.datetime | None" = None) -> int:
    """بازهٔ فعلیِ روز ∈ [0, slots). تقسیمِ یکنواختِ ۲۴ ساعت."""
    now = now or _dt.datetime.now()
    n = slots_per_day()
    return min(n - 1, int(now.hour * n / 24))


def topic_for(slot: int) -> str:
    """چرخشِ قطعی بینِ دو هدفِ مالک — بازهٔ زوج «خودت»، فرد «نقاشی»."""
    return TOPIC_SELF if slot % 2 == 0 else TOPIC_BUSINESS


# ─── وضعیتِ بازه (idempotency) ───────────────────────────────────────────────
def _load_slots() -> dict:
    try:
        if SLOT_STATE.exists():
            d = json.loads(SLOT_STATE.read_text("utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {"date": "", "done": []}


# پشتیبانِ درون-پروسه‌ای: اگر نوشتن روی دیسک شکست بخورد، بازه در همین پروسه سوخته
# می‌ماند. بدونِ این، دیسکِ پر/فقط‌خواندنی یعنی یک تماسِ گران در **هر تیک** تا نیمه‌شب
# (ممیزیِ متخاصمِ ۲۰۲۶-۰۷-۲۷: «ضمانتِ سوختنِ بازه پیش از تماس» fail-open بود).
_MEMO: dict = {"date": "", "done": set()}


def _save_slots(d: dict) -> bool:
    try:
        SLOT_STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = SLOT_STATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, SLOT_STATE)
        return True
    except OSError:
        return False


def slot_done(slot: int, today: "str | None" = None) -> bool:
    today = today or opslib.today()
    if _MEMO["date"] == today and slot in _MEMO["done"]:
        return True          # دیسک شاید ننوشته باشد؛ این پروسه یادش هست
    d = _load_slots()
    return d.get("date") == today and slot in (d.get("done") or [])


def mark_slot(slot: int, today: "str | None" = None) -> None:
    today = today or opslib.today()
    if _MEMO["date"] != today:
        _MEMO["date"], _MEMO["done"] = today, set()
    _MEMO["done"].add(slot)          # همیشه، حتی اگر دیسک شکست بخورد
    d = _load_slots()
    if d.get("date") != today:
        d = {"date": today, "done": []}
    if slot not in d["done"]:
        d["done"].append(slot)
    if not _save_slots(d):
        try:
            opslib.alert([f"deep_think: ثبتِ بازهٔ {slot} روی دیسک نشد — "
                          "پشتیبانِ درون-پروسه فعال (بعد از ری‌استارت ممکن است تکرار شود)"])
        except Exception:  # noqa: BLE001
            pass


# ─── ساختِ context (فقط تجمیع — هرگز محتوا، هرگز PII) ────────────────────────
def _jload(p: Path, default=None):
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else default
    except (OSError, ValueError):
        return default


def _count(p: Path) -> int:
    """شمارشِ ورودی‌های یک پوشه **بدونِ بازکردنِ هیچ فایلی** — مرزِ PII."""
    try:
        return sum(1 for _ in p.iterdir()) if p.is_dir() else 0
    except OSError:
        return 0


def _self_context() -> dict:
    """آنچه ارگانیسم دربارهٔ خودش می‌داند — همه از state، همه عددی.

    کلیدها از ساختارِ **واقعیِ** ORGANISM-STATE.json خوانده می‌شوند (بازرسی ۰۷-۲۷).
    اولین نسخهٔ این تابع کلیدهای سطحِ بالای حدسی (`mode`/`phi`) می‌خواند و بخشِ
    «حالت» همیشه `{}` می‌شد — یعنی promptِ گران با contextِ خالی می‌رفت."""
    sd = opslib.STATE_DIR
    org = _jload(sd / "ORGANISM-STATE.json", {}) or {}
    budget = _jload(sd / "cardiac-budget.json", {}) or {}
    heb = _jload(_HERE / "neural" / "hebbian.json", []) or []
    chrono = org.get("chrono") or {}
    wiring = (org.get("wiring") or {})
    diag = chrono.get("legs_diag") or {}
    ctx = {
        "ضربان": {"beat": chrono.get("beat"), "active": budget.get("spent"),
                  "resting": budget.get("resting")},
        "حالت": {"epoch": org.get("epoch_mode"), "frozen": org.get("frozen"),
                 "halted": bool(org.get("halted")), "تعارض": len(org.get("conflicts") or []),
                 "مشکوکِ_صفر": org.get("suspect_zero_total")},
        "اندام‌ها": {k: {"وضع": v.get("state"), "phi": v.get("phi"),
                         "سکوت_ثانیه": round(float(v.get("silence_ms") or 0) / 1000, 1)}
                     for k, v in diag.items() if isinstance(v, dict)},
        "سیم‌کشی": {"روشن": sum(1 for v in wiring.values() if v is True),
                    "خاموش": sum(1 for v in wiring.values() if v is False)},
        "آموخته‌ها": [{"جفت": r.get("signals"), "قدرت": round(float(r.get("strength", 0)), 3),
                       "هم‌رخدادی": r.get("co_occurrences")}
                      for r in heb if isinstance(r, dict)][:12],
    }
    # فرضیه‌های بازِ خودبهبودی — فقط عنوان و probe، نه کلِ ردیف
    try:
        q = sd / "c6" / "hypothesis-queue.jsonl"
        rows = [json.loads(x) for x in q.read_text("utf-8").splitlines() if x.strip()]
        ctx["فرضیه‌های_باز"] = [{"probe": r.get("probe"), "موضوع": str(r.get("subject"))[:80]}
                                for r in rows if r.get("status") in (None, "open", "queued")][:8]
    except (OSError, ValueError):
        ctx["فرضیه‌های_باز"] = []
    return ctx


def _business_context() -> dict:
    """سمتِ نقاشی — **فقط شمارش و متریک**. هیچ فایلِ لیدی باز نمی‌شود (مرزِ سختِ PII).

    `identity` عمداً حذف است: ABN/GST/بانک دادهٔ هویتیِ کسب‌وکار است و برای این
    سؤال لازم نیست؛ آنچه لازم نیست، فرستاده نمی‌شود."""
    sd = opslib.STATE_DIR
    legs = sd / "legs"
    org = _jload(sd / "ORGANISM-STATE.json", {}) or {}
    pm = org.get("proposal_metrics") or {}
    leg = org.get("leg") or {}
    return {
        "لیدهای_ورودی": _count(legs / "lead-inbox"),
        "پیش‌نویس‌های_آماده": _count(legs / "lead-drafts"),
        "فاکتورها": _count(legs / "invoices"),
        "پیشنهادها": {"تحویل‌شده": pm.get("proposals_delivered"),
                      "ارسال‌شده": pm.get("proposals_sent"),
                      "نتیجه‌خورده": pm.get("proposal_outcomes"),
                      "نرخ_پذیرش": pm.get("proposal_accept_rate"),
                      "ارزش_AUD": pm.get("proposal_value_aud")},
        "پای_لید": {"زنده": leg.get("money_link") == "active",
                    "فقط_پیشنهاد": leg.get("propose_only"),
                    "پیشنهادِ_صادرشده": leg.get("proposals_emitted")},
        "توضیح": ("این اعداد شمارشِ فایل و متریک‌اند. محتوای هیچ لیدی خوانده نشده و "
                  "نباید در پاسخ حدس زده شود."),
    }


_SYSTEM = (
    "تو مغزِ عمیقِ یک ارگانیسمِ نرم‌افزاریِ خودگردانی که برای یک اپراتورِ تنها "
    "(فارسی‌زبان، سیدنی) کار می‌کند. یک جلسهٔ فکر در روز به تو می‌رسد و گران است — "
    "پس جوابِ کلی و توصیه‌ای بی‌ارزش است.\n"
    "قواعدِ جواب:\n"
    "۱) فارسی بنویس، کوتاه، بدونِ مقدمه و بدونِ تعارف.\n"
    "۲) دقیقاً **یک** حرکتِ مشخص پیشنهاد بده، نه فهرست.\n"
    "۳) حرکت باید از همان اعدادی که به تو داده شده استنتاج شود — عددش را نقل کن.\n"
    "۴) بگو اگر این حرکت غلط باشد **چه چیزی** آن را غلط نشان می‌دهد (شرطِ ابطال).\n"
    "۵) اگر داده برای یک پیشنهادِ مسئولانه کافی نیست، همین را بگو و بگو چه "
    "اندازه‌گیریِ مشخصی لازم است. «نمی‌دانم» جوابِ معتبری است.\n"
    "۶) هرگز نامِ شخص، ایمیل، یا هر دادهٔ شخصی حدس نزن — به تو داده نشده."
)

_ASK = {
    TOPIC_SELF: (
        "این وضعیتِ امروزِ خودت است:\n{ctx}\n\n"
        "یک چیز را در خودت بهتر کن. کدام؟ چرا از روی همین اعداد؟ "
        "و چه مشاهده‌ای ثابت می‌کند اشتباه کرده‌ای؟"
    ),
    TOPIC_BUSINESS: (
        "این وضعیتِ لولهٔ کارِ نقاشیِ ساختمان است:\n{ctx}\n\n"
        "هدف: مشتریِ بعدی. با همین اعداد، مؤثرترین حرکتِ بعدی چیست؟ "
        "و چه مشاهده‌ای ثابت می‌کند اشتباه کرده‌ای؟"
    ),
}


def build_prompt(topic: str) -> str:
    ctx = _self_context() if topic == TOPIC_SELF else _business_context()
    body = json.dumps(ctx, ensure_ascii=False, indent=1)
    return _ASK[topic].format(ctx=body)


# ─── جلسه ────────────────────────────────────────────────────────────────────
def _append_ledger(rec: dict) -> None:
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def run(*, channel=None, now: "_dt.datetime | None" = None, force: bool = False) -> dict:
    """یک جلسهٔ فکرِ عمیق، اگر بازهٔ فعلی هنوز مصرف نشده باشد.

    flag خاموش → `{"ran": False, "reason": "flag-off"}` بدونِ هیچ I/O.
    `force=True` فقط برای آزمونِ دستیِ مالک؛ idempotency را رد می‌کند نه flag را."""
    if not flag_on():
        return {"ran": False, "reason": "flag-off"}
    now = now or _dt.datetime.now()
    slot = current_slot(now)
    if not force and slot_done(slot):
        return {"ran": False, "reason": "slot-done", "slot": slot}

    topic = topic_for(slot)
    try:
        prompt = build_prompt(topic)
    except Exception as e:  # noqa: BLE001 — ساختِ context هرگز beat را نمی‌کشد
        opslib.alert([f"deep_think context failed: {type(e).__name__}: {e}"])
        return {"ran": False, "reason": "context-error"}

    # بازه را **قبل از** فراخوان علامت می‌زنیم: یک شکستِ گران نباید هر تیک تکرار شود.
    mark_slot(slot)

    try:
        import model_router  # noqa: WPS433 — lazy؛ خودش quota/gate/breaker را می‌بندد
        r = model_router.ask("deep", prompt, system=_SYSTEM,
                             max_tokens=MAX_TOKENS, tier="primary")
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"deep_think ask failed: {type(e).__name__}: {e}"])
        _append_ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "slot": slot,
                        "topic": topic, "ok": False, "reason": "ask-exception"})
        return {"ran": False, "reason": "ask-exception", "slot": slot}

    ok = bool(r.get("ok"))
    text = str(r.get("text") or "").strip()
    rec = {"ts": opslib.now_iso(), "schema": SCHEMA, "slot": slot, "topic": topic,
           "ok": ok, "model": r.get("model"), "chars": len(text),
           "cost_usd": float(r.get("cost_usd") or 0.0)}

    if not ok or len(text) < MIN_ANSWER_CHARS:
        rec["reason"] = "empty-or-short"
        _append_ledger(rec)
        return {"ran": True, "delivered": False, "reason": rec["reason"],
                "slot": slot, "topic": topic, "chars": len(text)}

    # کارتِ propose-only به مالک
    delivered = False
    _chan = channel
    if _chan is None:
        try:
            import wiring as _wiring  # noqa: WPS433
            _chan = _wiring.make_telegram_channel()
        except Exception:  # noqa: BLE001
            _chan = None
    if _chan is not None and hasattr(_chan, "rfc_card"):
        try:
            head = "خودت" if topic == TOPIC_SELF else "نقاشی"
            summary = f"🧠 فکرِ عمیق — {head}\n\n{text}"
            # سقفِ ۶۴ بایتِ callback_data: شناسه کوتاه و قطعی می‌ماند (درسِ ۰۷-۲۶).
            delivered = bool(_chan.rfc_card(rfc_id=f"dt{opslib.today()[5:].replace('-', '')}s{slot}",
                                            summary=summary[:800]))
        except Exception as e:  # noqa: BLE001 — کارت هرگز جلسه را نمی‌کشد
            opslib.alert([f"deep_think card failed: {type(e).__name__}: {e}"])
    rec["delivered"] = delivered
    # متنِ فکر در دفتر می‌ماند: بدونِ آن نه کیفیتِ مغزِ گران سنجیدنی است و نه
    # ارگانیسم می‌تواند بعداً به فکرِ دیروزِ خودش رجوع کند — جلسه‌ای که فراموش
    # می‌شود، خرج است نه سرمایه. contextِ این پرسش اثباتاً بدونِ PII است
    # (t_business_context_counts_files_but_never_opens_them).
    rec["text"] = text[:4000]
    _append_ledger(rec)
    return {"ran": True, "delivered": delivered, "slot": slot, "topic": topic,
            "chars": len(text), "model": r.get("model")}


if __name__ == "__main__":   # pragma: no cover — بازرسیِ دستی
    print(json.dumps({"flag": flag_on(), "slots": slots_per_day(),
                      "slot": current_slot(), "topic": topic_for(current_slot()),
                      "done": slot_done(current_slot())}, ensure_ascii=False, indent=1))
