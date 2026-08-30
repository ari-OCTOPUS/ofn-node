"""owner_auth_log — حرفِ مجوزِ مالک جایی می‌نشیند، ولی هیچ‌وقت خودش اجرا نمی‌شود.

مسئله
─────
قراردادِ GENOME LOCK پنج عبارتِ مجوز تعریف می‌کند (`OWNER_AUTH: COMMIT` ·
`RESTART ORGANISM` · `DEPLOY MASTER` · `ARM FLAG <name>` · `TRAIN NOW`). گرپِ
۲۰۲۶-۰۷-۲۷ نشان داد **هیچ خطی از کدِ ارگانیسم این عبارت‌ها را نمی‌شناسد**.

یعنی مجوز فقط یک قرارداد بینِ مالک و هر ایجنتی است که همان لحظه چت را می‌خواند.
اگر مالک نیمه‌شب بنویسد «OWNER_AUTH: ARM FLAG X» و هیچ ایجنتی بیدار نباشد، آن
جمله **تبخیر می‌شود**. تصمیمِ مالک ضعیف‌ترین حلقهٔ زنجیره بود: فرّارتر از هر
داده‌ای که سیستم نگه می‌دارد.

چرا این ماژول ثبت می‌کند ولی اجرا نمی‌کند
──────────────────────────────────────────
وسوسه‌اش روشن است: «مالک نوشت ARM FLAG، خب فلگ را روشن کن.» ولی آن یعنی یک
**فلیپ‌کنندهٔ خودکارِ فلگ که ماشه‌اش متنِ چت است** — و متن جعل‌شدنی، فوروارد‌شدنی
و تزریق‌پذیر است. مسلح‌کردنِ فلگ یک عملِ استقرار است، نه یک پیام.

پس مرز این است: **کلمه ماندگار می‌شود، عمل نمی‌شود.** رکورد برای انسان یا
ایجنتی است که کار را انجام می‌دهد؛ خودِ ارگانیسم از این فایل هیچ اجازه‌ای
استخراج نمی‌کند.

⚠️ برای هر خواننده‌ای در آینده: ردیف‌های این فایل **ادعای** مجوزند، نه مجوزِ
اثبات‌شده. `chat_ok=false` یعنی از کانالی آمده که مالکِ احرازشده نبود.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "owner-auth.v1"
CARD_TITLE = "🔑 مجوزهای ثبت‌شده"

# دقیقاً پنج شکلِ قرارداد. عمداً سخت‌گیر: هر چیزِ دیگری مجوز نیست.
_PATTERNS = {
    "COMMIT": re.compile(r"OWNER_AUTH:\s*COMMIT\b(?P<arg>.*)", re.I),
    "RESTART": re.compile(r"OWNER_AUTH:\s*RESTART\s+ORGANISM\b(?P<arg>.*)", re.I),
    "DEPLOY": re.compile(r"OWNER_AUTH:\s*DEPLOY\s+MASTER\b(?P<arg>.*)", re.I),
    "ARM_FLAG": re.compile(r"OWNER_AUTH:\s*ARM\s+FLAG\s+(?P<arg>[A-Za-z0-9_]+)", re.I),
    "TRAIN": re.compile(r"OWNER_AUTH:\s*TRAIN\s+NOW\b(?P<arg>.*)", re.I),
}

# مقدارِ راز هرگز نباید در آرگومان بنشیند. نامِ فلگ مجاز است، مقدارش نه.
_SECRETISH = re.compile(
    r"(\d{8,12}:AA[\w-]{30,}|sk-[\w-]{20,}|-----BEGIN|[0-9a-fA-F]{40,})")


def _path() -> Path:
    return opslib.STATE_DIR / "owner-auth.jsonl"


def parse(text: str) -> "dict | None":
    """آیا این پیام یکی از پنج عبارتِ مجوز است؟ وگرنه None."""
    t = str(text or "")
    for kind, rx in _PATTERNS.items():
        m = rx.search(t)
        if not m:
            continue
        arg = (m.group("arg") or "").strip()[:200]
        if _SECRETISH.search(arg):
            # مقدارِ راز در آرگومان = رد. نه ثبت می‌شود نه echo.
            return {"kind": kind, "arg": "", "rejected": "secret-shaped"}
        return {"kind": kind, "arg": arg, "rejected": ""}
    return None


def record(text: str, *, chat_ok: bool, source: str = "tg") -> "dict | None":
    """ثبتِ append-only. `chat_ok` یعنی از کانالِ احرازشدهٔ مالک آمده.

    رکورد **همیشه** نوشته می‌شود، حتی وقتی chat_ok=False — چون ادعای مجوز از
    کانالِ ناشناس خودش یک رویدادِ امنیتی است که باید دیده شود، نه بی‌صدا افتد."""
    hit = parse(text)
    if hit is None:
        return None
    rec = {"schema": SCHEMA, "ts": opslib.now_iso(), "kind": hit["kind"],
           "arg": hit["arg"], "chat_ok": bool(chat_ok), "source": str(source)[:16],
           "rejected": hit["rejected"], "executed": False,
           "_note": "ادعای مجوز — نه اجرا. هیچ کدی از این فایل اجازه استخراج نمی‌کند."}
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        rec["written"] = True
    except OSError:
        rec["written"] = False
    return rec


def pending(limit: int = 20) -> list:
    """مجوزهایی که ثبت شده‌اند و هنوز کسی اجرایشان نکرده."""
    rows = []
    try:
        for ln in _path().read_text("utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("chat_ok") and not r.get("executed") and not r.get("rejected"):
                rows.append(r)
    except OSError:
        pass
    return rows[-max(1, int(limit)):]


def ack(rec: dict) -> str:
    """جوابِ فوریِ تلگرام. صریح می‌گوید چه شد و چه **نشد**."""
    import html
    k = str((rec or {}).get("kind") or "")
    if (rec or {}).get("rejected"):
        return ("🔑 <b>ثبت نشد</b>\n"
                "▸ آرگومان شبیهِ راز بود. نامِ فلگ بنویس، نه مقدارش.\n"
                "▸ نکنی: هیچ.")
    if not (rec or {}).get("chat_ok"):
        return ("🔑 <b>از این کانال قبول نیست</b>\n"
                "▸ ثبت شد به‌عنوانِ ادعا، ولی مجوز شمرده نمی‌شود.\n"
                "▸ نکنی: هیچ.")
    label = {"COMMIT": "کامیت", "RESTART": "ریستارتِ ارگانیسم",
             "DEPLOY": "دیپلوی به master", "ARM_FLAG": "مسلح‌کردنِ فلگ",
             "TRAIN": "شروعِ آموزش"}.get(k, k)
    arg = html.escape(str((rec or {}).get("arg") or ""))[:120]
    return (f"🔑 <b>ثبت شد: {label}</b>" + (f" — <code>{arg}</code>" if arg else "") + "\n"
            "▸ این حرف حالا روی دیسک است و گم نمی‌شود.\n"
            "▸ <b>ولی من خودم اجرایش نمی‌کنم.</b> فلیپِ فلگ و کامیت و ریستارت "
            "عملِ استقرارند نه پیام؛ متنِ چت جعل‌شدنی است.\n"
            "▸ نکنی: همین‌طور در صف می‌ماند.")


def card() -> str:
    """کارتِ «چه مجوزهایی داده‌ای و هنوز اجرا نشده‌اند»."""
    import html
    rows = pending()
    if not rows:
        return ("🔑 <b>مجوزی در صف نیست</b>\n"
                "▸ عبارت‌ها: <code>OWNER_AUTH: COMMIT</code> · "
                "<code>RESTART ORGANISM</code> · <code>DEPLOY MASTER</code> · "
                "<code>ARM FLAG &lt;نام&gt;</code> · <code>TRAIN NOW</code>\n"
                "▸ نکنی: هیچ.")
    lines = [f"🔑 <b>{len(rows)} مجوزِ ثبت‌شده، هنوز اجرا نشده</b>", ""]
    for r in rows[-10:]:
        arg = html.escape(str(r.get("arg") or ""))[:50]
        lines.append(f"▸ <code>{html.escape(str(r.get('kind')))}</code> "
                     f"{arg} — {html.escape(str(r.get('ts'))[:16])}")
    lines += ["",
              "▸ این‌ها ثبت‌اند نه اجرا. کسی که کار را می‌کند باید خودش تأیید کند "
              "که از کانالِ تو آمده.",
              "▸ نکنی: در صف می‌مانند."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    demo = ["OWNER_AUTH: ARM FLAG OCTOPUS_WIRE_TRAJECTORY_LOG",
            "OWNER_AUTH: RESTART ORGANISM",
            "سلام چطوری",
            "OWNER_AUTH: COMMIT sk-" + "a" * 25]
    print(json.dumps([{"in": d[:40], "hit": parse(d)} for d in demo],
                     ensure_ascii=False, indent=1))
