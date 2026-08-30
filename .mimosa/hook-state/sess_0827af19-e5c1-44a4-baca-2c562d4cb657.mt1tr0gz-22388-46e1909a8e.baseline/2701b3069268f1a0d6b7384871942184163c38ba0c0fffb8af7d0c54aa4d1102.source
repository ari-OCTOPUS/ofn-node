"""owner_ping — یک پیامِ متنی از فایل به تلگرامِ مالک.

چرا وجود دارد: مالک ۲۰۲۶-۰۷-۲۷ گفت «چند ساعت نیستم، همه‌چیز را تلگرام بگو».
تا امروز تنها راهِ رسیدنِ متن به مالک از داخلِ حلقهٔ زندهٔ `center` بود؛ برای
گزارشِ کارِ یک جلسه، درِ ورودیِ سبک لازم بود.

قواعد:
  · متن **از فایل** خوانده می‌شود، نه از آرگومان — تا هیچ محتوایی در تاریخچهٔ شل
    و لاگِ پروسه‌ها ننشیند.
  · هیچ توکن/chat-id هرگز چاپ نمی‌شود؛ خروجی فقط ok/شمارهٔ پیام است.
  · `_scrub` مرکز اعمال می‌شود (پاریته با بقیهٔ سطحِ تلگرام) تا واژه‌های ممنوعِ
    containment از این در هم بیرون نروند.
  · تکه‌تکه می‌کند: تلگرام سقفِ ۴۰۹۶ کاراکتر دارد و پیامِ بلندتر **بی‌صدا** رد
    می‌شود — یعنی دقیقاً حالتی که گزارشِ مهم گم می‌شود.

اجرا: `_ops\\tools\\owner-ping.cmd <path-to-utf8-text-file> [topic_id]`
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LIMIT = 3500          # زیرِ سقفِ ۴۰۹۶ تلگرام، با جا برای هدرِ تکه


def chunks(text: str, limit: int = LIMIT):
    """تکه‌کردن روی مرزِ خط — هرگز وسطِ یک تگِ HTML نمی‌بُرد."""
    out, cur = [], []
    n = 0
    for line in str(text or "").splitlines():
        line = line[:limit]
        if n + len(line) + 1 > limit and cur:
            out.append("\n".join(cur))
            cur, n = [], 0
        cur.append(line)
        n += len(line) + 1
    if cur:
        out.append("\n".join(cur))
    return out or [""]


def main(argv) -> int:
    if len(argv) < 2:
        print("usage: owner_ping.py <file> [topic_id]")
        return 2
    try:
        body = Path(argv[1]).read_text("utf-8")
    except OSError as e:
        print(f"فایل خوانده نشد: {e.__class__.__name__}")
        return 2
    topic = argv[2] if len(argv) > 2 else None

    # توکن/chat-id در `.env` است نه در flags.cmd. از لودرِ خودِ ارگانیسم استفاده
    # می‌کنیم که قراردادش صریح است: هرگز مقدار را برنمی‌گرداند و overwrite نمی‌کند.
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001 — نبودِ .env = لولهٔ بسته، نه crash
        pass

    import tg_api
    c = tg_api.TgClient()
    if not c.wired():
        # عمداً نمی‌گوییم کدام‌یک غایب است با مقدار — فقط کدام کلید.
        print("لوله وصل نیست: توکن یا chat-id در محیط نیست")
        return 1

    parts = chunks(body)
    sent = 0
    for i, part in enumerate(parts, 1):
        head = f"<i>({i}/{len(parts)})</i>\n" if len(parts) > 1 else ""
        mid = c.send(head + part, topic_id=topic)
        if mid:
            sent += 1
    print(f"ok: {sent}/{len(parts)} تکه ارسال شد")
    return 0 if sent == len(parts) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
