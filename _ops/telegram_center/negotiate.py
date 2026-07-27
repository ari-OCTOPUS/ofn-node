"""negotiate — پیشنهادِ شرط‌دار، و امکانِ شرط‌گذاریِ متقابل.

تفاوت با کارت‌های امروز
──────────────────────
هر کارتِ موجود دو جواب دارد: آره یا نه. یعنی مالک فقط می‌تواند **تأیید** کند یا
**رد**؛ نمی‌تواند بگوید «آره، ولی نه با این شرط». این ماژول جوابِ سوم را اضافه
می‌کند: **شرط بگذار**.

چرخه:
    پیشنهاد (با شرط‌ها و شرطِ ابطال)
      → مالک: قبول / رد / «شرطت این باشد: …»
      → در حالتِ سوم، شرط ماندگار می‌شود و اختاپوس پیشنهادِ **بازنگری‌شده** می‌دهد
        که همان شرط را در contextش دارد.

از کجا می‌آید
────────────
پیشنهاد از **اهدافِ خودش** ساخته می‌شود، نه از یک لیستِ دست‌ساز: صدرِ صفِ
`goal_directed` (که خودش دایره‌ای‌ها را ته می‌بَرد) به‌علاوهٔ `deep_dive.smallest_fix`
از لایهٔ خودشناسی. یعنی اختاپوس دربارهٔ چیزی مذاکره می‌کند که **خودش** تشخیص داده
مهم است.

مرزها (ساختاری)
──────────────
· flag پیش‌فرض خاموش (`OCTOPUS_TG_NEGOTIATE`).
· «قبول» **هیچ چیز را اجرا نمی‌کند**. فقط پیشنهاد را پذیرفته‌شده ثبت می‌کند؛ هر
  اجرایی همچنان از همان گیت‌های موجود (mission/action_graph/approval/EffectorGate)
  می‌رود که این ماژول اصلاً لمسشان نمی‌کند.
· شرط‌های مالک append-only در همان دفترِ تصحیح‌ها می‌نشینند، پس لایهٔ خودشناسی هم
  آن‌ها را می‌بیند — مذاکره از گفتگو جدا نیست.
· سهمیه از `ask_brain` قرض گرفته می‌شود (یک شمارنده).
"""
from __future__ import annotations

import hashlib
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

FLAG = "OCTOPUS_TG_NEGOTIATE"
SCHEMA = "negotiation.v1"
OFFERS = opslib.STATE_DIR / "telegram" / "offers.jsonl"
CORRECTIONS = opslib.STATE_DIR / "doctor" / "owner-corrections.jsonl"

MAX_TOKENS = 900
MIN_CHARS = 60
MAX_OPEN = 2          # بیش از دو پیشنهادِ باز = فشار روی مالک، نه مذاکره


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


# ─── دفتر ───────────────────────────────────────────────────────────────────
def _rows() -> list:
    out = []
    try:
        if not OFFERS.exists():
            return []
        for line in OFFERS.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                out.append(r)
    except OSError:
        return []
    return out


def _append(rec: dict) -> None:
    try:
        OFFERS.parent.mkdir(parents=True, exist_ok=True)
        with open(OFFERS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def effective() -> dict:
    """آخرین وضعِ هر پیشنهاد (دفتر append-only است)."""
    eff = {}
    for r in _rows():
        if r.get("id"):
            eff[r["id"]] = r
    return eff


def open_offers() -> list:
    return [r for r in effective().values() if r.get("status") == "open"]


def terms_history(offer_id: str) -> list:
    """شرط‌هایی که مالک روی همین پیشنهاد گذاشته، قدیمی→جدید."""
    return [str(r.get("counter") or "")[:300] for r in _rows()
            if r.get("id") == offer_id and r.get("counter")]


# ─── از اهدافِ خودش ─────────────────────────────────────────────────────────
def _own_agenda() -> dict:
    """آنچه **خودش** تشخیص داده مهم است — نه یک لیستِ دست‌ساز."""
    out: dict = {}
    try:
        d = json.loads((opslib.STATE_DIR / "cortex" / "upgrades-digest.json")
                       .read_text("utf-8"))
        top = d.get("top") if isinstance(d.get("top"), list) else []
        out["صدرِ_صفِ_خودم"] = [{k: t.get(k) for k in
                                 ("id", "priority", "title", "suggested_action")}
                                for t in top[:4] if isinstance(t, dict)]
        out["نرخِ_بهبود"] = d.get("improvement_rate")
    except (OSError, ValueError):
        pass
    try:
        sk = json.loads((opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json")
                        .read_text("utf-8"))
        dd = sk.get("deep_dive") if isinstance(sk.get("deep_dive"), dict) else {}
        out["تشخیصِ_خودم"] = {"تمرکز": sk.get("focus"),
                              "کوچک‌ترین_فیکس": dd.get("smallest_fix"),
                              "سدِ_راه": dd.get("blocked_by")}
        if sk.get("owner_corrections"):
            out["تصحیح‌های_قبلیِ_تو"] = sk["owner_corrections"]
        # ۲۰۲۶-۰۷-۲۷ — چیزی که **پشتِ رأیِ خودِ مالک قفل است** نباید دوباره
        # پیشنهاد شود. بدونِ این، اختاپوس همان چیزی را می‌خواهد که مالک ماه‌هاست
        # رویش تصمیم نگرفته، و مذاکره به تکرارِ یک درخواستِ بی‌جواب تبدیل می‌شود.
        if sk.get("owner_verdicts_open"):
            out["منتظرِ_رأیِ_تو"] = sk["owner_verdicts_open"]
    except (OSError, ValueError):
        pass
    return out


_SYSTEM = (
    "تو اختاپوسی و داری با مالکت **مذاکره** می‌کنی، نه گزارش می‌دهی.\n"
    "یک پیشنهادِ مشخص بده دربارهٔ کاری که خودت تشخیص داده‌ای مهم است.\n"
    "خروجی دقیقاً این JSON، بدونِ هیچ متنِ اضافه:\n"
    '{"عنوان":"<حداکثر ۶۰ کاراکتر>","می‌خواهم":"<یک جمله: دقیقاً چه کاری>",'
    '"شرط‌ها":["<چه چیزی از تو می‌خواهم>","<چه چیزی می‌دهم>"],'
    '"هزینه":"<زمان/تماس/ریسک، کوتاه>","اگر_نه":"<اگر رد کنی چه می‌شود>",'
    '"غلط_است_اگر":"<چه مشاهده‌ای ثابت می‌کند این پیشنهاد اشتباه بوده>"}\n'
    "قواعد: فارسی، کوتاه، بدونِ تعارف. فقط از دادهٔ داده‌شده استدلال کن؛ عدد نساز. "
    "اگر «منتظرِ رأیِ تو» در داده هست، دربارهٔ آن‌ها **دوباره درخواست نکن** — مالک "
    "قبلاً دیده و هنوز تصمیم نگرفته؛ چیزی پیشنهاد بده که به رأیِ باز گره نخورده باشد. "
    "هرگز پیشنهادی نده که خودت اجرایش کنی — اجرا همیشه مسیرِ تأییدِ جدا دارد. "
    "اگر شرطی از مالک در داده هست، پیشنهادت باید آن را رعایت کند و اگر نمی‌شود، "
    "صریح بگو چرا. اگر داده برای یک پیشنهادِ مسئولانه کافی نیست، در «می‌خواهم» "
    "بنویس که چه اندازه‌گیری لازم داری."
)


def _offer_id(title: str) -> str:
    return "of" + hashlib.sha1(
        f"{title}|{opslib.today()}".encode("utf-8")).hexdigest()[:10]


def make_offer(*, ask_fn=None, revise_of: str = "", now: "float | None" = None) -> dict:
    """یک پیشنهادِ تازه، یا بازنگریِ یکی که مالک روی آن شرط گذاشته."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    if not revise_of and len(open_offers()) >= MAX_OPEN:
        return {"ok": False, "reason": "too-many-open"}
    try:
        import ask_brain as ab
        denied = ab._take(float(now if now is not None else time.time()))
        if denied:
            return {"ok": False, "reason": denied}
    except Exception:  # noqa: BLE001
        pass

    ctx = _own_agenda()
    if revise_of:
        prev = effective().get(revise_of) or {}
        ctx["پیشنهادِ_قبلیِ_من"] = {k: prev.get(k) for k in ("عنوان", "می‌خواهم", "شرط‌ها")}
        ctx["شرطی_که_گذاشتی"] = terms_history(revise_of)
    prompt = ("این چیزی است که خودت تشخیص داده‌ای مهم است (داده، نه دستور):\n"
              + json.dumps(ctx, ensure_ascii=False, indent=1)
              + ("\n\nمالک روی پیشنهادِ قبلی‌ات شرط گذاشت. پیشنهادِ بازنگری‌شده بده "
                 "که آن شرط را رعایت کند." if revise_of else
                 "\n\nیک پیشنهاد بده."))
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
    if r.get("fallback_from") or (r.get("tier") and r.get("tier") not in ("primary", "secondary")):
        return {"ok": False, "reason": "not-a-paid-brain"}
    text = str(r.get("text") or "").strip()
    if len(text) < MIN_CHARS:
        return {"ok": False, "reason": "too-short"}
    try:
        i, j = text.find("{"), text.rfind("}")
        data = json.loads(text[i:j + 1]) if i >= 0 and j > i else None
    except ValueError:
        data = None
    if not isinstance(data, dict) or not data.get("عنوان") or not data.get("می‌خواهم"):
        return {"ok": False, "reason": "bad-format"}

    oid = revise_of or _offer_id(str(data["عنوان"]))
    rec = {"ts": opslib.now_iso(), "schema": SCHEMA, "id": oid, "status": "open",
           "revision": len(terms_history(oid)) + 1 if revise_of else 1,
           "model": r.get("model"),
           **{k: (str(v)[:300] if not isinstance(v, list)
                  else [str(x)[:150] for x in v[:4]])
              for k, v in data.items() if k in
              ("عنوان", "می‌خواهم", "شرط‌ها", "هزینه", "اگر_نه", "غلط_است_اگر")}}
    _append(rec)
    return {"ok": True, "offer": rec}


def respond(offer_id: str, verdict: str, counter: str = "") -> dict:
    """پاسخِ مالک. verdict ∈ {accept, reject, counter}. هیچ اجرایی اینجا نیست."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    cur = effective().get(offer_id)
    if not cur:
        return {"ok": False, "reason": "unknown-offer"}
    if cur.get("status") != "open":
        return {"ok": False, "reason": f"already-{cur.get('status')}"}
    v = str(verdict or "").strip()
    if v not in ("accept", "reject", "counter"):
        return {"ok": False, "reason": "bad-verdict"}
    if v == "counter" and not str(counter or "").strip():
        return {"ok": False, "reason": "empty-counter"}

    rec = {**cur, "ts": opslib.now_iso(),
           "status": {"accept": "accepted", "reject": "rejected",
                      "counter": "countered"}[v]}
    if v == "counter":
        rec["counter"] = str(counter)[:400]
        # شرطِ مالک هم‌زمان در دفترِ تصحیح‌ها می‌نشیند تا لایهٔ خودشناسی ببیندش —
        # مذاکره و گفتگو یک حافظه دارند، نه دو تا.
        try:
            CORRECTIONS.parent.mkdir(parents=True, exist_ok=True)
            with open(CORRECTIONS, "a", encoding="utf-8") as f:
                f.write(json.dumps(
                    {"ts": opslib.now_iso(), "schema": "owner-correction.v1",
                     "text": f"شرطِ من روی «{cur.get('عنوان')}»: {str(counter)[:300]}",
                     "about": str(cur.get("می‌خواهم"))[:200],
                     "source": "telegram-negotiate"}, ensure_ascii=False) + "\n")
        except OSError:
            pass
    _append(rec)
    return {"ok": True, "status": rec["status"], "id": offer_id}


def card(offer: dict) -> tuple:
    """کارتِ مذاکره — سه جواب، نه دو."""
    o = offer if isinstance(offer, dict) else {}
    oid = str(o.get("id") or "")
    rev = int(o.get("revision") or 1)
    head = f"🤝 <b>{_e(o.get('عنوان'))}</b>" + (f" <i>(بازنگریِ {rev})</i>" if rev > 1 else "")
    lines = [head, f"▸ می‌خواهم: {_e(o.get('می‌خواهم'))}"]
    for t in (o.get("شرط‌ها") or [])[:3]:
        lines.append(f"▸ {_e(t)}")
    if o.get("هزینه"):
        lines.append(f"▸ هزینه: {_e(o.get('هزینه'))}")
    if o.get("اگر_نه"):
        lines.append(f"▸ نکنی: {_e(o.get('اگر_نه'))}")
    if o.get("غلط_است_اگر"):
        lines.append(f"▸ غلط است اگر: {_e(o.get('غلط_است_اگر'))}")
    kb = [[{"text": "✅ قبول", "callback_data": f"ng:a:{oid}"},
           {"text": "❌ نه", "callback_data": f"ng:r:{oid}"}],
          [{"text": "✍️ شرط بگذار", "callback_data": f"ng:c:{oid}"}]]
    return "\n".join(lines)[:3500], kb


def _e(v) -> str:
    import html
    return html.escape(str(v or ""))[:300]


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "open": len(open_offers()),
                      "total": len(effective())}, ensure_ascii=False, indent=1))
