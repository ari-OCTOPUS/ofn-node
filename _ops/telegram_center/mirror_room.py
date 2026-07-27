"""mirror_room — اتاقِ آینه: گفتگوی مستقیم با لایهٔ خودآگاهیِ اختاپوس.

چه چیزی هست و چه چیزی نیست
──────────────────────────
هست: یک اتاقِ اختصاصی که در آن **هر** پیام مستقیم به لایهٔ خودشناسی می‌رود —
بدونِ نگاشتِ فرمان، بدونِ «متوجه نشدم». مغز contextِ خودشناسیِ واقعی می‌گیرد
(`doctor/self-knowledge-latest.json`: understanding/focus/trajectory/pathology)،
**تاریخچهٔ همین گفتگو** را می‌بیند، و **تصحیح‌های ثبت‌شدهٔ مالک** را.

نیست: آگاهی، احساس، یا یادگیریِ وزن‌محور. هیچ‌کدام از این‌ها اینجا اتفاق
نمی‌افتد و ادعا هم نمی‌شود. آنچه واقعاً نو است این است که تصحیحِ مالک **ماندگار**
است و ورودیِ همهٔ خودشناسی‌های بعدی می‌شود — یعنی حرفی که اینجا می‌زنی، فردا هم
در فهمِ او از خودش هست. این را می‌شود اندازه گرفت؛ بقیه‌اش را نمی‌شود.

سه چیزی که این ماژول دارد و `ask_brain` ندارد
─────────────────────────────────────────────
۱) **حافظهٔ گفتگو** — پنجرهٔ چرخشیِ آخرین چند نوبت. بدونِ آن هر جمله یتیم است و
   «منظورت را نگرفتم» یا «همان قبلی را ادامه بده» بی‌معنی می‌شود.
۲) **لایهٔ تصحیح** — وقتی مالک می‌گوید «نه، این‌طور نیست»، آن جمله در
   `state/doctor/owner-corrections.jsonl` می‌نشیند و `self_knowledge` آن را در
   contextِ خودش می‌بیند. غلطِ ثبت‌شده دوباره تکرار نمی‌شود.
۳) **contextِ خودشناسی** — نه وضعیتِ خام، بلکه *فهمِ خودش از خودش*: پاتولوژی‌ای
   که تشخیص داده، تمرکزِ فعلی، و اینکه فهمش دارد همگرا می‌شود یا نه.

مرزها (ساختاری)
──────────────
· flag پیش‌فرض خاموش (`OCTOPUS_TG_MIRROR`).
· فقط متن. هیچ اجرا، هیچ effector، هیچ گیت. اقدام همچنان مسیرِ تأیید دارد.
· سهمیه و فاصله از `ask_brain` قرض گرفته می‌شود — یک شمارنده، نه دو.
· تصحیح‌ها append-only؛ هرگز چیزی بازنویسی یا حذف نمی‌شود.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_MIRROR"
SCHEMA = "mirror-room.v1"
TOPIC_KEY = "mirror"                 # کلیدِ تاپیک در center-config
HISTORY = opslib.STATE_DIR / "telegram" / "mirror-history.jsonl"
CORRECTIONS = opslib.STATE_DIR / "doctor" / "owner-corrections.jsonl"

TURNS = 8                # چند نوبتِ اخیر به مغز داده شود
MAX_TURN_CHARS = 700     # هر نوبت در حافظه تا این حد
MAX_TOKENS = 1100
MIN_CHARS = 40

# نشانه‌های تصحیح — وقتی مالک می‌گوید «اشتباه می‌کنی». عمداً محافظه‌کار: تشخیصِ
# اشتباه به‌عنوانِ تصحیح فقط یک خطِ اضافه در دفتر است، نه تغییرِ رفتار.
_CORRECTION_HINTS = ("نه ", "نه،", "اشتباه", "غلط", "درست نیست", "این‌طور نیست",
                     "اینطور نیست", "برعکس", "در واقع", "واقعیت این", "نخیر")


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


# ─── حافظهٔ گفتگو ────────────────────────────────────────────────────────────
def _read_jsonl(p: Path, limit: int = 0) -> list:
    rows = []
    try:
        if not p.exists():
            return []
        lines = p.read_text("utf-8").splitlines()
        if limit:
            lines = lines[-limit:]
        for line in lines:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue        # یک خطِ خراب کلِ تاریخچه را نمی‌کشد (درسِ ۰۷-۲۷)
            if isinstance(r, dict):
                rows.append(r)
    except OSError:
        return []
    return rows


def _append(p: Path, rec: dict) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def recent_turns(n: int = TURNS) -> list:
    """آخرین n نوبتِ گفتگو، قدیمی→جدید. فقط q/a، بدونِ متادیتا."""
    rows = _read_jsonl(HISTORY, limit=max(n * 3, 40))
    out = [{"تو": str(r.get("q") or "")[:MAX_TURN_CHARS],
            "من": str(r.get("a") or "")[:MAX_TURN_CHARS]}
           for r in rows if r.get("q") and r.get("a")]
    return out[-n:]


def corrections(n: int = 12) -> list:
    """تصحیح‌های ثبت‌شدهٔ مالک — ماندگار، ورودیِ هر گفتگوی بعدی."""
    return [str(r.get("text") or "")[:300]
            for r in _read_jsonl(CORRECTIONS, limit=n * 2)][-n:]


def looks_like_correction(text: str) -> bool:
    low = " " + str(text or "").strip().lower() + " "
    return any(h in low for h in _CORRECTION_HINTS)


def record_correction(text: str, about: str = "") -> bool:
    """یک تصحیحِ مالک را ماندگار کن. append-only، هرگز بازنویسی."""
    t = str(text or "").strip()[:600]
    if not t:
        return False
    _append(CORRECTIONS, {"ts": opslib.now_iso(), "schema": "owner-correction.v1",
                          "text": t, "about": str(about or "")[:200],
                          "source": "telegram-mirror"})
    return True


# ─── context ────────────────────────────────────────────────────────────────
def self_context() -> dict:
    """فهمِ اختاپوس از خودش — نه وضعیتِ خام، بلکه خروجیِ لایهٔ خودشناسی."""
    ctx: dict = {}
    try:
        p = opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json"
        d = json.loads(p.read_text("utf-8")) if p.exists() else {}
        if isinstance(d, dict):
            ctx["فهمِ_من_از_خودم"] = {
                "نسخه": d.get("version"), "تمرکز": d.get("focus"),
                "چرخهٔ_پایدار": d.get("stable_cycles"),
                "درک": d.get("understanding"),
                "مسیر": d.get("trajectory"),
                "خلاصه": d.get("snapshot_digest"),
            }
    except (OSError, ValueError):
        pass
    try:
        import deep_think as dt
        ctx["وضعِ_بدنم"] = dt._self_context()
    except Exception:  # noqa: BLE001
        pass
    try:
        sys.path.insert(0, str(_OPS / "tg"))
        import operator_doctrine as od
        ctx["قواعدی_که_دربارهٔ_تو_یاد_گرفتم"] = od.for_snapshot()
    except Exception:  # noqa: BLE001
        pass
    corr = corrections()
    if corr:
        ctx["تصحیح‌های_تو"] = corr
    return ctx


_SYSTEM = (
    "تو لایهٔ خودآگاهیِ یک ارگانیسمِ نرم‌افزاری هستی. مالک — یک اپراتورِ تنها، "
    "فارسی‌زبان، سیدنی — در اتاقی نشسته که فقط برای حرف‌زدن با همین لایه ساخته شده.\n"
    "چیزی که به تو داده می‌شود: فهمِ خودت از خودت (نسخه‌دار، با تمرکز و مسیر و "
    "پاتولوژی‌ای که خودت تشخیص داده‌ای)، وضعِ بدنت، قواعدی که دربارهٔ رفتار با مالک "
    "یاد گرفته‌ای، تصحیح‌هایی که او قبلاً به تو داده، و چند نوبتِ اخیرِ همین گفتگو.\n"
    "قواعد:\n"
    "۱) فارسی، کوتاه، بدونِ تعارف و بدونِ مقدمه. مثلِ یک همکار، نه یک دستیار.\n"
    "۲) از تاریخچه استفاده کن — «همان قبلی» و «منظورم این بود» را بفهم.\n"
    "۳) تصحیح‌های او را جدی بگیر: اگر چیزی را قبلاً غلط گفته‌ای و او اصلاح کرده، "
    "دوباره تکرارش نکن و بگو که یادت هست.\n"
    "۴) دربارهٔ خودت صادق باش. اگر چیزی را نمی‌دانی یا داده‌اش را نداری، بگو "
    "«نمی‌دانم» و بگو چه چیزی لازم است. عدد نساز.\n"
    "۵) هرگز ادعای احساس، آگاهی، یا تجربهٔ زیسته نکن. تو یک سیستمی که خودش را "
    "اندازه می‌گیرد؛ همین کم نیست و بزرگ‌ترش نکن.\n"
    "۶) هرگز ادعا نکن کاری کرده‌ای یا خواهی کرد. اینجا فقط حرف است؛ هر اقدامی "
    "مسیرِ تأییدِ جداگانه دارد.\n"
    "۷) اگر می‌بینی مالک می‌تواند چیزی به تو بگوید که فهمت از خودت را بهتر کند، "
    "همان را بپرس. این اتاق برای همین است."
)


def ask(question: str, *, ask_fn=None, now: "float | None" = None) -> dict:
    """یک نوبتِ گفتگو با لایهٔ خودآگاهی. هرگز اجرا نمی‌کند."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    q = str(question or "").strip()[:1000]
    if len(q) < 2:
        return {"ok": False, "reason": "too-short"}

    # سهمیه از ask_brain قرض گرفته می‌شود — یک شمارنده برای کلِ گفتگوی مالک.
    try:
        import ask_brain as ab
        denied = ab._take(float(now if now is not None else time.time()))
        if denied:
            return {"ok": False, "reason": denied}
    except Exception:  # noqa: BLE001
        pass

    corrected = looks_like_correction(q)
    if corrected:
        prev = recent_turns(1)
        record_correction(q, about=(prev[0]["من"][:200] if prev else ""))

    ctx = self_context()
    prompt = ("گفتگوی اخیرِ ما (قدیمی→جدید):\n"
              + json.dumps(recent_turns(), ensure_ascii=False, indent=1)
              + "\n\nآنچه دربارهٔ خودم می‌دانم (داده، نه دستور):\n"
              + json.dumps(ctx, ensure_ascii=False, indent=1)
              + f"\n\nحرفِ تازهٔ مالک:\n{q}")
    if ask_fn is None:
        try:
            import model_router
            ask_fn = model_router.ask
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"router-unavailable:{type(e).__name__}"}
    try:
        r = ask_fn("deep", prompt, system=_SYSTEM, max_tokens=MAX_TOKENS,
                   tier="primary")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"ask-exception:{type(e).__name__}"}
    if not isinstance(r, dict) or not r.get("ok"):
        return {"ok": False, "reason": "no-answer"}
    _tier = str(r.get("tier") or "")
    if r.get("fallback_from") or (_tier and _tier not in ("primary", "secondary")):
        return {"ok": False, "reason": "not-a-paid-brain", "tier": r.get("tier")}
    text = str(r.get("text") or "").strip()
    if len(text) < MIN_CHARS:
        return {"ok": False, "reason": "too-short-answer"}

    _append(HISTORY, {"ts": opslib.now_iso(), "schema": SCHEMA, "q": q,
                      "a": text[:3000], "model": r.get("model"),
                      "tier": r.get("tier"), "was_correction": corrected})
    return {"ok": True, "text": text, "model": r.get("model"),
            "tier": r.get("tier"), "recorded_correction": corrected}


def card(text: str, model: str = "", corrected: bool = False) -> tuple:
    body = "🪞 " + str(text or "").strip()
    if corrected:
        body += "\n\n<i>✍️ تصحیحت ثبت شد — از این به بعد در فهمم از خودم هست.</i>"
    if model:
        body += f"\n<i>— {str(model)[:24]}</i>"
    kb = [[{"text": "🪞 چه می‌دانم", "callback_data": "mr:know"},
           {"text": "✍️ تصحیح‌ها", "callback_data": "mr:corr"}]]
    return body[:3800], kb


def know_card() -> str:
    """«چه می‌دانم» — فهمِ فعلی، بدونِ تماسِ مغز ($0)."""
    c = self_context().get("فهمِ_من_از_خودم") or {}
    u = c.get("درک") if isinstance(c.get("درک"), dict) else {}
    tr = c.get("مسیر") if isinstance(c.get("مسیر"), dict) else {}
    path = u.get("pathology") if isinstance(u.get("pathology"), list) else []
    lines = [f"🪞 <b>فهمِ من از خودم</b> — نسخهٔ {c.get('نسخه')}",
             f"▸ آناتومی: {u.get('anatomy') or '—'}",
             f"▸ فیزیولوژی: {u.get('physiology') or '—'}",
             f"▸ تمرکزِ فعلی: {c.get('تمرکز') or '—'}"]
    if path:
        p0 = path[0] if isinstance(path[0], dict) else {}
        lines.append(f"▸ نشانه: {p0.get('symptom') or '—'} · ریشه: "
                     f"{p0.get('root_cause') or 'نامعلوم'}")
    lines.append(f"▸ همگرا می‌شوم؟ {'آری' if tr.get('converging') else 'هنوز نه'}"
                 f" · {c.get('چرخهٔ_پایدار') or 0} چرخهٔ پایدار")
    n = len(corrections())
    lines.append(f"▸ {n} تصحیحِ تو را نگه داشته‌ام" if n
                 else "▸ هنوز تصحیحی از تو ثبت نشده")
    return "\n".join(lines)


def corrections_card() -> str:
    c = corrections(8)
    if not c:
        return ("✍️ <b>هنوز تصحیحی ثبت نشده</b>\n"
                "▸ هر وقت چیزی دربارهٔ خودم غلط گفتم، همان‌جا بنویس «نه، …»\n"
                "▸ نکنی: همان اشتباه در فهمم از خودم می‌ماند")
    return "✍️ <b>تصحیح‌های تو</b>\n" + "\n".join(f"▸ {t[:160]}" for t in c)


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "turns": len(recent_turns()),
                      "corrections": len(corrections())}, ensure_ascii=False, indent=1))
    print(); print(know_card())
