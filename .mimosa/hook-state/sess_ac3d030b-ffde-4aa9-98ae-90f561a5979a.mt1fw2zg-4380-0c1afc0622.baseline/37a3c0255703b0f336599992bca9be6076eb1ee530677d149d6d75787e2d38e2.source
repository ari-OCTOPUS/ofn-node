"""output_critic — ارگانیسم خروجیِ **خودش** را می‌سنجد، تا بتواند بهتر شود.

رأیِ مالک ۲۰۲۶-۰۷-۲۷: «عین معلم بالاسرش باش» + «یادش بده بتونه خودشو بسازه برا
بهترین شدن».

چرا این حلقه گم بود
───────────────────
اختاپوس امروز ۸۳ پیامِ خودکار فرستاد و **هیچ‌کدام نمره نگرفت**. یادگیری‌اش فقط
از رأیِ مالک روی *پیشنهادها* می‌آمد؛ ولی بیشترِ چیزی که مالک از او می‌بیند
پیشنهاد نیست — دایجست است، کشف است، آلارم است. آن‌ها بی‌داور بودند.

نتیجه‌اش در دادهٔ همان روز دیده می‌شود:
  · ۳۵٪ از «چیزهایی که یاد گرفتم» **تکراری** بود — هفت بار همان جست‌وجو روی یک
    شناسهٔ داخلیِ بی‌معنا (`A08` → «A8»).
  · کارتِ «نیازت دارم» چهار بار با **همان سه آیتم** آمد؛ فقط شمارندهٔ آلارم عوض
    می‌شد. این اطلاع‌رسانی نیست، غر زدن است.
  · دکتر دو بار با فاصلهٔ ساعت‌ها گفت «خطای پرتکرار — **نامعلوم، نیاز به کاوش**»
    و هیچ کاوشی نکرد.

هیچ‌کدامِ این‌ها باگ نیستند. همه‌شان «کار می‌کنند». مسئله این است که هیچ‌چیز
نمی‌گفت **بد**ند.

چه چیزی را می‌سنجد — و چرا فقط همین‌ها
──────────────────────────────────────
چهار سنجهٔ **عینی**، نه سلیقه‌ای. سنجهٔ سلیقه‌ای نمرهٔ بی‌پایه می‌سازد و نمرهٔ
بی‌پایه بدتر از نبودِ نمره است (همان درسِ حلقهٔ معلم):

  `repetition`   — همان متن/موضوع را چند بار گفته‌ام؟
  `actionability`— آیا کاری که پیشنهاد می‌دهم از جایی که مالک می‌خوانَد ممکن است؟
  `novelty`      — نسبت به دفعهٔ قبل چیزِ تازه‌ای دارد؟
  `self_answer`  — آیا سؤالی پرسیده‌ام که جوابش در دستِ خودم بود؟

مرزها
─────
· فقط‌خواندنی. هیچ پیامی را نمی‌فرستد، جلوی هیچ پیامی را نمی‌گیرد.
· نمره‌اش **پیشنهاد** است نه فیلتر — سانسورِ خودکارِ خروجی یعنی سیستمی که
  می‌تواند بدی‌اش را از چشمِ مالک پنهان کند.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "output-critic.v1"
CARD_TITLE = "🎓 نقدِ خروجیِ خودم"

# دستوری که در متن پیشنهاد می‌شود ولی از گروه نمی‌رسد = پیشنهادِ بن‌بست.
# ⚠️ حروفِ فارسی هم لازم است: `/توان` یک دستورِ واقعیِ همین سیستم است. الگویی که
# فقط لاتین بشناسد، همان نیمه‌زبانی است که امروز در گاردِ اختیار هم دیده شد.
_CMD = re.compile(r"[«\"'\s(]/([\w؀-ۿ]{3,16})")
# سؤالی که جوابش در دادهٔ خودِ سیستم است — «نامعلوم» روی چیزی که خودش نوشته.
_SELF_ANSWERABLE = re.compile(r"(نامعلوم|نیاز به کاوش|مشخص نیست|نمی‌دانم)")


def _reachable_commands() -> set:
    """دستورهایی که واقعاً از گروه کار می‌کنند (هر دو روتر + پل)."""
    out = set()
    try:
        c = (_HERE / "telegram_center" / "center.py").read_text("utf-8")
        i = c.index("handlers = {")
        j = c.index("fn = handlers.get(cmd)", i)
        out |= {m.group(1) for m in re.finditer(r'"/([a-z_]+)"\s*:', c[i:j])}
        if "_bridge_to_organism" in c:
            a = (_HERE / "budget" / "approval_channel.py").read_text("utf-8")
            out |= set(re.findall(r'"/([a-z_]+)"', a))
    except (OSError, ValueError):
        pass
    return out


def grade(messages: list) -> dict:
    """نمرهٔ چهاربعدیِ یک دستهٔ پیام. ورودی: [{ts, text, stream}].

    هر نمره در [0,1] و **بالاتر بهتر**. `None` یعنی سنجیدنی نبود — نه صفر."""
    msgs = [m for m in (messages or []) if isinstance(m, dict)]
    if not msgs:
        return {"schema": SCHEMA, "n": 0, "scores": {}, "findings": []}

    texts = [str(m.get("text") or "") for m in msgs]
    findings = []

    # ۱ تکرار — روی نرمال‌شده، تا شمارنده‌های متغیر تکرار را پنهان نکنند
    norm = [re.sub(r"\d+", "#", t)[:200] for t in texts]
    uniq = len(set(norm))
    repetition = round(uniq / len(norm), 3)
    if repetition < 0.7:
        dup = len(norm) - uniq
        findings.append(f"{dup} پیام تکرارِ نزدیک بودند — شمارنده عوض شد، حرف نه")

    # ۲ عمل‌پذیری — دستوری که پیشنهاد می‌دهد باید برسد
    ok_cmds = _reachable_commands()
    suggested = {m.group(1) for t in texts for m in _CMD.finditer(t)}
    dead = sorted(suggested - ok_cmds) if ok_cmds else []
    actionability = round(1 - len(dead) / max(1, len(suggested)), 3) if suggested else None
    if dead:
        findings.append(f"دستورهای بن‌بست پیشنهاد شد: {', '.join('/' + d for d in dead[:5])}")

    # ۳ تازگی — چند پیام چیزی فراتر از پیامِ قبلیِ همان جریان دارند
    by_stream: dict = {}
    for m, t in zip(msgs, norm):
        by_stream.setdefault(str(m.get("stream") or "?"), []).append(t)
    fresh = sum(1 for v in by_stream.values() for a, b in zip(v, v[1:]) if a != b)
    pairs = sum(max(0, len(v) - 1) for v in by_stream.values())
    novelty = round(fresh / pairs, 3) if pairs else None
    if novelty is not None and novelty < 0.5:
        findings.append("بیشترِ دایجست‌ها با قبلی‌شان فرقی نداشتند")

    # ۴ خودپاسخ — «نامعلوم» گفتن دربارهٔ چیزی که خودش تولید کرده
    unknown = sum(1 for t in texts if _SELF_ANSWERABLE.search(t))
    self_answer = round(1 - unknown / len(texts), 3)
    if unknown:
        findings.append(f"{unknown} بار «نامعلوم/نیاز به کاوش» گفت بدونِ اینکه کاوش کند")

    return {"schema": SCHEMA, "ts": opslib.now_iso(), "n": len(msgs),
            "scores": {"repetition": repetition, "actionability": actionability,
                       "novelty": novelty, "self_answer": self_answer},
            "findings": findings}


def _recent(hours: float = 24.0) -> list:
    """پیام‌های خودکارِ اخیر از دفترهای موجود. متن هرگز ذخیره نشده، پس از
    منابعِ محتوایی خوانده می‌شود — و اگر نبود، صادقانه خالی برمی‌گردد."""
    out = []
    cutoff = time.time() - hours * 3600
    # ۲۰۲۶-۰۷-۲۸ — `held-stream.jsonl` اضافه شد، و دلیلش یک کوریِ ساختاری است.
    #
    # `actionability` تا امروز تقریباً همیشه `None` برمی‌گشت («سنجیدنی نبود»).
    # علت نه باگ بود نه بدشانسی: این سنجه می‌پرسد «فرمانی که پیشنهاد دادم واقعاً
    # می‌رسد؟» ولی دو منبعِ نمونه (`discoveries` و `initiative`) تقریباً هرگز
    # فرمان پیشنهاد نمی‌کنند. کارت‌هایی که **می‌کنند** — `/review` در کارتِ
    # نیازها، `/doctor focus`، `/heart set` — هیچ‌وقت در نمونه نبودند.
    #
    # یعنی مهم‌ترین سنجه دقیقاً به داده‌ای نگاه نمی‌کرد که وجودش را توجیه می‌کند.
    # و این همان شکافی است که ۳۲ فرمانِ نرسیده را ماه‌ها پنهان نگه داشت: کارت
    # می‌گفت «/review بزن» و `/review` به هیچ باتی وصل نبود.
    #
    # `held-stream.jsonl` (سیاستِ سطحِ نسخهٔ ۲) **متنِ کاملِ کارت** را نگه می‌دارد،
    # پس حالا سنجه چیزی برای سنجیدن دارد. عمداً همان منبع: چیزی که نگه داشته شد
    # هم پیامی است که ارگانیسم *می‌خواست* بگوید — و ادعایش باید درست باشد چه
    # فرستاده شود چه نه.
    for rel, kind in (("discoveries.jsonl", "discovery"),
                      ("telegram/initiative.jsonl", "initiative"),
                      ("telegram/held-stream.jsonl", "held")):
        p = opslib.STATE_DIR / rel
        try:
            for ln in p.read_text("utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                try:
                    ts = float(r.get("ts") or 0)
                except (TypeError, ValueError):
                    ts = 0.0
                if ts and ts < cutoff:
                    continue
                txt = str(r.get("summary") or r.get("text") or "")
                if txt:
                    out.append({"ts": ts, "text": txt, "stream": kind})
        except OSError:
            continue
    return out


def report(hours: float = 24.0) -> dict:
    return grade(_recent(hours))


def card() -> str:
    """کارتِ معلم — و صادق وقتی چیزی برای سنجیدن نیست."""
    import html
    r = report()
    if not r["n"]:
        return ("🎓 <b>چیزی برای نقد نیست</b>\n"
                "▸ متنِ پیام‌های خودکار ذخیره نمی‌شود (فقط هش و طول)، پس فقط "
                "کشف‌ها و ابتکارها سنجیده می‌شوند.\n"
                "▸ نمره وقتی هم بیاید <b>فیلتر</b> نیست — سانسورِ خودکارِ خروجی "
                "یعنی سیستمی که می‌تواند بدی‌اش را از چشمِ تو <b>پنهان</b> کند.\n"
                "▸ نکنی: هیچ.")
    s = r["scores"]
    lines = [f"🎓 <b>نقدِ {r['n']} خروجیِ اخیرِ خودم</b>", ""]
    labels = {"repetition": "تکرارنبودن", "actionability": "عمل‌پذیری",
              "novelty": "تازگی", "self_answer": "خودپاسخی"}
    for k, lab in labels.items():
        v = s.get(k)
        if v is None:
            lines.append(f"▸ {lab}: <i>سنجیدنی نبود</i>")
        else:
            mark = "🟢" if v >= 0.8 else ("🟡" if v >= 0.5 else "🔴")
            lines.append(f"▸ {lab}: {mark} <code>{v}</code>")
    if r["findings"]:
        lines += ["", "<b>چه چیزی را بد انجام دادم:</b>"]
        for f in r["findings"][:5]:
            lines.append(f"   · {html.escape(f)}")
    lines += ["",
              "▸ این نمره <b>پیشنهاد</b> است نه فیلتر. سانسورِ خودکارِ خروجی یعنی "
              "سیستمی که می‌تواند بدی‌اش را از چشمِ تو پنهان کند.",
              "",
              "▸ نکنی: هیچ — فقط می‌دانم کجا بد بودم."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps(report(), ensure_ascii=False, indent=1))
