#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_receipts.py — «آن پیامی که فرستادم، چه بر سرش آمد؟»

چرا این ابزار هست (فاز ۰ ِ پلنِ حلقهٔ دوتایی، ۲۰۲۶-۰۸-۰۴)
──────────────────────────────────────────────────────────
شکایتِ زیستهٔ مالک این بود: «هرکاری می‌کنم دیده نمی‌شود.» تا امروز، این جمله
**اثباتِ‌ناپذیر** بود — نه برای او، نه برای من:

    inbound-log.jsonl   می‌گفت «رسید»        (زمان: ISO ِ محلی)
    tg-send-log.jsonl   می‌گفت «فرستادم»     (زمان: اپاکِ اعشاری)

و هیچ کلیدِ مشترکی نداشتند. پس «آیا آن ورودی جواب گرفت؟» فقط با **همسایگیِ
زمانی** حدس زده می‌شد — و وقتی دو بات به یک چت می‌فرستند، آن حدس ابطال‌ناپذیر
است. یعنی هم «دیده شدم» و هم «دیده نشدم» با همان داده قابلِ دفاع بودند.

این ماژول آن حدس را به یک **join** تبدیل می‌کند، روی `update_id`.

چهار حکمِ ممکن برای هر ورودی
─────────────────────────────
    ✅ ANSWERED   ارسالی با همان `update_id` ثبت شده (state=sent)
    📝 EXPLAINED  جواب نرفت، ولی ردیفِ «چرا» هست — مالک می‌تواند بفهمد
    ⏸ HELD       پیام ساخته شد ولی سیاست نگهش داشت (held/blocked) — گم نشده
    ❌ SILENT     نه جواب، نه دلیل ← **این تنها شکستِ واقعی است**
    ❔ PRE-RIG    قبل از زنده‌شدنِ همبستگی رسیده ⇒ حکم صادر نمی‌شود

⚠️ ردیفِ PRE-RIG عمدی است. درسِ ثبت‌شده: «نبودِ داده حکم نیست». ورودی‌هایی که
پیش از زنده‌شدنِ مهرِ همبستگی آمده‌اند، `update_id` روی ارسالشان ندارند —
نامیدنشان «SILENT» یک اتهامِ ساختگی است، نه یک یافته.

ناوردی‌ها: فقط‌خواندنی · stdlib-only · صفر شبکه · هرگز متنِ پیام یا secret
چاپ نمی‌کند (هیچ‌کدام از دو لاگ اصلاً متن ذخیره نمی‌کنند).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import statistics
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402

SCHEMA = "tg-receipts.v1"

#: تفاوتِ زمانیِ قابل‌قبول بینِ تفسیرِ ما از ISO و اپاکِ ارسال. بیش از این
#: یعنی منطقهٔ زمانی را غلط تفسیر کرده‌ایم. (⚠️ درسِ ثبت‌شده: یک ناهم‌خوانیِ
#: UTC/محلی یک بار سقفِ پول را ده ساعت در روز کور کرد و کسی نفهمید — پس این
#: ابزار فرضِ خودش را **می‌سنجد**، نه اینکه به آن اعتماد کند.)
_TZ_SANITY_S = 120.0


def _inbound_path() -> Path:
    return opslib.STATE_DIR / "telegram" / "inbound-log.jsonl"


def _send_path() -> Path:
    return opslib.STATE_DIR / "tg-send-log.jsonl"


def _read_jsonl(p: Path) -> list:
    out = []
    try:
        if not p.exists():
            return []
        for ln in p.read_text("utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue          # یک بایتِ خراب کلِ گزارش را نمی‌کشد
    except OSError:
        return []
    return out


def _iso_to_epoch(s: str):
    """ISO ِ **بی‌منطقه** → اپاک، با تفسیرِ «محلی».

    `opslib.now_iso()` امروز `datetime.now()` است یعنی ساعتِ محلی. اگر روزی
    به UTC عوض شود، `tz_sane` در خروجی قرمز می‌شود و این ابزار **می‌گوید**
    که اعدادِ تأخیرش بی‌معنی‌اند — به‌جای اینکه بی‌صدا عددِ غلط بدهد."""
    try:
        return _dt.datetime.fromisoformat(str(s)).timestamp()
    except (TypeError, ValueError):
        return None


def collect(*, inbound: "list | None" = None, sends: "list | None" = None) -> dict:
    """هستهٔ خالص — دو فهرست ردیف می‌گیرد و تصویرِ join‌شده می‌دهد.

    تزریق‌پذیر است تا تست بتواند بدونِ دست‌زدن به لاگِ **زنده** بسنجدش
    (درسِ ثبت‌شده: «هر مسیرِ تحتِ آزمون را ایزوله کن»)."""
    inbound = _read_jsonl(_inbound_path()) if inbound is None else list(inbound)
    sends = _read_jsonl(_send_path()) if sends is None else list(sends)

    arrivals: dict = {}
    dispositions: dict = {}
    for r in inbound:
        uid = r.get("update_id")
        if uid is None:
            continue
        if "outcome" in r:
            dispositions.setdefault(uid, []).append(r)
        else:
            arrivals.setdefault(uid, r)

    replies: dict = {}
    correlated_send_ts = []
    for r in sends:
        uid = r.get("update_id")
        if uid is None:
            continue
        replies.setdefault(uid, []).append(r)
        try:
            correlated_send_ts.append(float(r.get("ts") or 0))
        except (TypeError, ValueError):
            pass

    # مرزِ «رِیگ»: زودترین ارسالی که مهرِ همبستگی دارد. ورودیِ قبل از این،
    # ساختاراً نمی‌توانسته برچسب بگیرد ⇒ درباره‌اش حکم نمی‌دهیم.
    rig_epoch = min(correlated_send_ts) if correlated_send_ts else None

    # سنجشِ فرضِ منطقهٔ زمانی روی جفت‌های واقعی، نه روی ادعا.
    offsets = []
    for uid, reps in replies.items():
        a = arrivals.get(uid)
        if not a:
            continue
        ae = _iso_to_epoch(a.get("ts"))
        if ae is None:
            continue
        try:
            offsets.append(min(float(x.get("ts") or 0) for x in reps) - ae)
        except (TypeError, ValueError):
            continue
    tz_sane = None
    tz_median = None
    if offsets:
        tz_median = statistics.median(offsets)
        tz_sane = abs(tz_median) <= _TZ_SANITY_S

    rows = []
    for uid, a in sorted(arrivals.items(), key=lambda kv: str(kv[1].get("ts") or "")):
        reps = replies.get(uid, [])
        disp = dispositions.get(uid, [])
        sent = [r for r in reps
                if str(r.get("state") or "") == "sent" and r.get("ok") is not False]
        withheld = [r for r in reps if str(r.get("state") or "") in ("held", "blocked")]
        ae = _iso_to_epoch(a.get("ts"))

        if sent:
            verdict = "ANSWERED"
        elif withheld:
            verdict = "HELD"
        elif disp:
            verdict = "EXPLAINED"
        elif rig_epoch is not None and ae is not None and ae < rig_epoch:
            verdict = "PRE-RIG"
        elif rig_epoch is None:
            verdict = "PRE-RIG"          # همبستگی هنوز هرگز زنده نبوده
        else:
            verdict = "SILENT"

        latency = None
        if sent and ae is not None:
            try:
                latency = round(min(float(r.get("ts") or 0) for r in sent) - ae, 1)
            except (TypeError, ValueError):
                latency = None

        rows.append({
            "update_id": uid,
            "ts": a.get("ts"),
            "bot": a.get("bot"),
            "kind": a.get("kind"),
            "cmd": a.get("cmd") or "",
            "chat_kind": a.get("chat_kind"),
            "from_owner": a.get("from_owner"),
            "verdict": verdict,
            "replies": len(reps),
            "outcome": (disp[-1].get("outcome") if disp else None),
            "reason": (disp[-1].get("reason") if disp else None),
            "detail": (disp[-1].get("detail") if disp else None),
            "latency_s": latency,
        })

    counts: dict = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    return {
        "schema": SCHEMA,
        "arrivals": len(arrivals),
        "disposition_rows": sum(len(v) for v in dispositions.values()),
        "correlated_sends": sum(len(v) for v in replies.values()),
        "rig_live": rig_epoch is not None,
        "tz_sane": tz_sane,
        "tz_median_offset_s": (round(tz_median, 1) if tz_median is not None else None),
        "counts": counts,
        "rows": rows,
    }


# ── نمایش ────────────────────────────────────────────────────────────────────
_FA = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
_LRI, _PDI = "⁦", "⁩"     # ایزولهٔ bidi دورِ تکهٔ لاتین (منشور UX-۹)

_MARK = {"ANSWERED": "✅", "EXPLAINED": "📝", "HELD": "⏸",
         "SILENT": "❌", "PRE-RIG": "❔"}


def _fa(v) -> str:
    return str(v).translate(_FA)


def _iso(s) -> str:
    """فقط ساعت — تاریخ در گزارشِ یک نشست نویز است."""
    t = str(s or "")
    return t.split("T")[1] if "T" in t else t


def _ltr(s) -> str:
    """تکهٔ لاتین را ایزوله کن وگرنه در متنِ فارسی جهتش برعکس می‌شود.
    ⚠️ دورِ متنِ **فارسی** نگذار — همان bidi ای را می‌شکند که قرار بود درست کند."""
    s = str(s or "")
    return f"{_LRI}{s}{_PDI}" if s and s.isascii() else s


def report(data: "dict | None" = None, *, limit: int = 20,
           silent_only: bool = False) -> str:
    d = data if data is not None else collect()
    rows = d["rows"]
    if silent_only:
        rows = [r for r in rows if r["verdict"] == "SILENT"]
    rows = rows[-int(limit):] if limit else rows

    out = []
    c = d["counts"]
    head = (f"📥 ورودی {_fa(d['arrivals'])} · "
            f"✅ {_fa(c.get('ANSWERED', 0))} · "
            f"📝 {_fa(c.get('EXPLAINED', 0))} · "
            f"⏸ {_fa(c.get('HELD', 0))} · "
            f"❌ {_fa(c.get('SILENT', 0))} · "
            f"❔ {_fa(c.get('PRE-RIG', 0))}")
    out.append(head)

    if not d["rig_live"]:
        out.append("⚠️ مهرِ همبستگی هنوز روی هیچ ارسالی ننشسته — یعنی مرکز پس از "
                   "زنده‌شدنِ این قابلیت هنوز چیزی نفرستاده. تا آن لحظه هیچ "
                   "حکمِ ❌ صادر نمی‌شود.")
    if d["tz_sane"] is False:
        out.append(f"⚠️ تفسیرِ منطقهٔ زمانی مشکوک است (اختلافِ میانه "
                   f"{_fa(d['tz_median_offset_s'])} ثانیه) — اعدادِ تأخیر را "
                   f"باور نکن تا این رفع شود.")

    out.append("")
    for r in rows:
        mark = _MARK.get(r["verdict"], "·")
        bits = [f"{mark} {_iso(r['ts'])}",
                _ltr(str(r["update_id"])),
                _ltr(r["cmd"] or r["kind"] or "")]
        if r["latency_s"] is not None:
            bits.append(f"{_fa(r['latency_s'])}s")
        if r["verdict"] == "EXPLAINED":
            bits.append(f"چرا: {_ltr(r['outcome'])} / {_ltr(r['reason'])}")
        if r["verdict"] == "SILENT":
            bits.append("← نه جواب، نه دلیل")
        out.append("  " + " · ".join(b for b in bits if b))

    if not rows:
        out.append("  (چیزی برای نشان‌دادن نیست)")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="جوینِ ورود × تعیین‌تکلیف × پاسخ، روی update_id")
    ap.add_argument("--last", type=int, default=20, help="چند ورودیِ آخر")
    ap.add_argument("--silent-only", action="store_true",
                    help="فقط آن‌هایی که نه جواب گرفتند نه دلیل")
    ap.add_argument("--json", action="store_true", help="خروجیِ ماشین‌خوان")
    a = ap.parse_args(argv)
    d = collect()
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(report(d, limit=a.last, silent_only=a.silent_only))
    # ❌ واقعی = کدِ خروجیِ غیرصفر، تا حلقهٔ دوتایی بتواند اسکریپتی هم حکم بدهد.
    return 1 if d["counts"].get("SILENT") else 0


if __name__ == "__main__":
    sys.exit(main())
