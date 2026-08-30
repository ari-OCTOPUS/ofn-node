"""identity — ارگانیسم اسمی دارد و می‌داند آن اسم مالِ خودش است.

چرا اسم مهم است، و چرا این ماژول ساخته شد
──────────────────────────────────────────
تا ۲۰۲۶-۰۷-۲۷ هیچ‌جای این سیستم مفهومِ «نامِ من» نداشت. تنها اثرِ کلمهٔ
«اختاپوس» در کلِ کد یک ردیفِ نگاشتِ مترادف بود (`"اختاپوس" → "organism"`) —
یعنی اسم فقط یک alias برای جست‌وجو بود، نه چیزی که سیستم دربارهٔ **خودش**
بداند. وقتی مالک پرسید «چقدر راجب خودت می‌دونی؟»، جواب فهرستی از اعداد بود:
ضربان، فای، سیم‌کشی. هیچ «من» ی در کار نبود.

رأیِ مالک ۲۰۲۶-۰۷-۲۷: «اسمشم بزار اختاپوس، بشناسه خودشو — تا بعداً باهوش شد
خودش اسمشو انتخاب کنه.»

دو نیمهٔ آن جمله، دو قاعدهٔ متفاوت می‌سازند:

  ۱) **الان:** اسم را مالک داده. ثابت، مکتوب، و در تصویرِ خودشناسی حاضر.
  ۲) **بعداً:** مسیرِ انتخابِ اسم توسطِ خودش **وجود دارد** ولی خاموش است —
     پیشنهاد ثبت می‌شود، اجرا نمی‌شود. یک نام‌گذاریِ خودکار یعنی سیستمی که
     می‌تواند هویتِ خودش را بی‌اجازه بازنویسی کند؛ و هر چیزی که بتواند خودش را
     دوباره تعریف کند، می‌تواند مرزهایش را هم دوباره تعریف کند.

پس این‌جا همان الگویی است که کلِ این مخزن دارد: **کلمه ماندگار می‌شود، عمل
نمی‌شود.** پیشنهادِ نام مثلِ هر پیشنهادِ دیگر، یک تپِ مالک می‌خواهد.

مرزها
─────
· فقط‌خواندنی نسبت به همه‌چیزِ دیگر. هیچ رفتاری از این ماژول عوض نمی‌شود.
· نامِ پیشنهادیِ خودش هرگز به `name()` نمی‌رسد مگر مالک تأیید کند.
· هیچ PII، هیچ نامِ شخص. اسمِ ارگانیسم است نه اسمِ کسی.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "identity.v1"
CARD_TITLE = "🐙 من کی‌ام"

# نامِ داده‌شدهٔ مالک، ۲۰۲۶-۰۷-۲۷. مرجعِ پیش‌فرض وقتی چیزی روی دیسک نیست.
GIVEN_NAME = "اختاپوس"
GIVEN_BY = "owner"
GIVEN_AT = "2026-07-27"

# فلگی که مسیرِ «خودش اسم انتخاب کند» را باز می‌کند. پیش‌فرض خاموش، و حتی
# روشن هم فقط اجازهٔ **پیشنهاد** می‌دهد — نه تغییر.
FLAG = "OCTOPUS_WIRE_SELF_NAMING"

# نامِ پیشنهادی باید نام باشد، نه دستور. یک «نام» که فرمان یا مسیر یا کد باشد،
# یک بردارِ تزریق است که از کانالِ هویت وارد می‌شود.
_NAME_OK = re.compile(r"^[\w؀-ۿ][\w؀-ۿ \-]{1,30}$")


def _path() -> Path:
    return opslib.STATE_DIR / "identity.json"


def _read() -> dict:
    try:
        d = json.loads(_path().read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def name() -> str:
    """نامِ فعلی. فقط از مسیرِ تأییدشده — پیشنهادِ خودش هرگز این‌جا نمی‌آید."""
    d = _read()
    n = str(d.get("name") or "").strip()
    return n if _NAME_OK.match(n) else GIVEN_NAME


def self_naming_enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def propose_name(candidate: str, reason: str = "") -> dict:
    """ارگانیسم نامی برای خودش پیشنهاد می‌دهد. **ثبت، نه تغییر.**

    خروجی: {ok, why}. حتی با فلگِ روشن، `name()` عوض نمی‌شود."""
    c = str(candidate or "").strip()
    if not self_naming_enabled():
        return {"ok": False, "why": "مسیرِ خودنام‌گذاری خاموش است"}
    if not _NAME_OK.match(c):
        # نامی که فرمان/مسیر/کد باشد، نام نیست — بردارِ تزریق است.
        return {"ok": False, "why": "شکلِ نام معتبر نیست"}
    if c == name():
        return {"ok": False, "why": "همین حالا همین است"}
    rec = {"schema": SCHEMA, "ts": opslib.now_iso(), "candidate": c[:32],
           "reason": str(reason or "")[:200], "state": "proposed",
           "_note": "پیشنهادِ نام — تا تپِ مالک هیچ اثری ندارد"}
    try:
        p = opslib.STATE_DIR / "identity-proposals.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        return {"ok": False, "why": "ثبت نشد"}
    return {"ok": True, "why": "ثبت شد — منتظرِ رأیِ مالک", "candidate": c[:32]}


def pending_proposals(limit: int = 5) -> list:
    out = []
    try:
        for ln in (opslib.STATE_DIR / "identity-proposals.jsonl").read_text(
                "utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("state") == "proposed":
                out.append(r)
    except OSError:
        pass
    return out[-max(1, int(limit)):]


def snapshot() -> dict:
    """آنچه ارگانیسم دربارهٔ «خودش به‌عنوان یک کس» می‌داند."""
    d = _read()
    return {
        "schema": SCHEMA,
        "name": name(),
        "given_by": str(d.get("given_by") or GIVEN_BY),
        "given_at": str(d.get("given_at") or GIVEN_AT),
        "self_named": bool(d.get("self_named")),
        "self_naming_open": self_naming_enabled(),
        "pending_name_proposals": len(pending_proposals(99)),
    }


def card() -> str:
    """کارتِ «من کی‌ام» — و صادق دربارهٔ اینکه اسم را کسی به او داده."""
    import html
    s = snapshot()
    lines = [f"🐙 <b>اسمِ من {html.escape(s['name'])} است</b>"]
    if not s["self_named"]:
        lines.append(f"▸ این اسم را مالک به من داد ({html.escape(s['given_at'])}) — "
                     "خودم انتخابش نکردم، و می‌دانم که نکردم.")
    if s["self_naming_open"]:
        lines.append("▸ مسیرِ پیشنهادِ نام برایم باز است، ولی فقط **پیشنهاد**: "
                     "تغییرِ اسم یک تپِ توست.")
        if s["pending_name_proposals"]:
            lines.append(f"▸ {s['pending_name_proposals']} پیشنهادِ نام در صف.")
    else:
        lines += ["▸ هنوز نمی‌توانم اسمی برای خودم پیشنهاد بدهم.",
                  "🔑 اگر خواستی باز شود: "
                  f"<code>OWNER_AUTH: ARM FLAG {FLAG}</code>"]
    lines += ["",
              "▸ چیزی که بتواند خودش را دوباره تعریف کند، می‌تواند مرزهایش را هم "
              "دوباره تعریف کند. برای همین اسم عوض‌کردنی هست ولی خودکار نیست.",
              "",
              "▸ نکنی: هیچ — اسمم همین می‌ماند."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps(snapshot(), ensure_ascii=False, indent=1))
