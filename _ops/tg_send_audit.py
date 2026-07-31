#!/usr/bin/env python3
"""ممیزیِ ایستایِ مسیرِ ارسالِ تلگرام — و اعترافِ صریح به حدودِ خودش.

چرا این ماژول با احتیاطِ غیرعادی نوشته شده
──────────────────────────────────────────
اولین نسخهٔ این ممیزی روی `center.py` اجرا شد و گفت **صفر تخلف**: هر ۱۰ مسیرِ
پاسخ `topic_id=` را پاس می‌کردند. ولی لاگِ زنده در همان لحظه ۴۸ پیامِ بی‌تاپیک
نشان می‌داد. هر دو راست می‌گفتند:

    topic_id=self._reply_thread(msg)      # ایستا: ✅ پاس داده شده
                                          # زنده:  ❌ None، چون فلگ لود نیست

یعنی یک ممیزیِ ایستا که فقط «آیا `topic_id` نوشته شده؟» را بپرسد، **سبزِ
دروغین** تولید می‌کند — همان بیماریِ §۱، این‌بار در خودِ ابزارِ تشخیص.

پس این ماژول سه طبقه گزارش می‌دهد، نه دو:

    certain      topic_id=<عددِ ثابت>            → ایستا اثبات‌شده
    conditional  topic_id=<هر عبارتِ دیگر>        → **ممکن است زنده None شود**
    absent       اصلاً topic_id ندارد             → قطعاً General

و `proven_rate` فقط `certain` را می‌شمارد. هیچ ادعای «درست است» از روی
`conditional` ساخته نمی‌شود. تنها شاهدِ زنده `tg_trace.py` است.

اجرا:
    python _ops/tg_send_audit.py                  # کلِ درختِ _ops
    python _ops/tg_send_audit.py --json
    python _ops/tg_send_audit.py path/to/file.py …
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

SCHEMA = "tg-send-audit.v1"

# ── دو فرستندهٔ مستقل، دو سیاستِ متفاوتِ تاپیک ──────────────────────────────
#
#   tg_api.TgClient.send(...)              پارامترِ صریحِ `topic_id` دارد
#   approval_channel.send_text(...)        از ۰۷-۳۱ **هم** `topic_id` دارد؛ اگر
#                                          داده نشود، تاپیک را از `stream`
#                                          استنتاج می‌کند و آن هم تنها وقتی
#                                          `chat_id` صریح داده نشده باشد.
#
# ⚠️ اصلاحِ ۲۰۲۶-۰۷-۳۱ — این کامنت تا امروز می‌گفت «send_text ِ topic_id ندارد».
# آن جمله از ۲۸ جولای مانده بود و **دیگر درست نبود**: پارامتر اضافه شده و در
# `send_text` صریحاً برنده است (`thread = int(topic_id) if isinstance(...)`).
# چون طبقه‌بندِ زیر هرگز `topic_id` را روی `send_text` نگاه نمی‌کرد، هر سه
# فراخوانیِ `approval_channel.poll_once` — که دقیقاً `topic_id=_thr` پاس
# می‌دهند — تا ابد «بی‌تاپیک» شمرده می‌شدند. یعنی ابزارِ اندازه‌گیری، سه
# **قرمزِ دروغین** تولید می‌کرد؛ همان بیماریِ سبزِ دروغین، آینه‌شده.
#
# نتیجهٔ عملی که هنوز پابرجاست: پاسخِ مستقیمی که `chat_id`ِ گروه بگیرد **و**
# `topic_id` ندهد، از مسیرِ دوم همیشه بی‌تاپیک می‌رود — یعنی در General.
SEND_METHODS = ("send", "send_text")
STREAM_ROUTED = ("send_text",)
# جایگاهِ positional ِ `topic_id` در امضای send_text:
#   send_text(self, text, reply_markup=None, chat_id=None, stream=None, topic_id=None)
# (شمارش بدونِ self، چون گرهٔ Call هم `self` را ندارد.)
_SEND_TEXT_POS = {"chat_id": 2, "stream": 3, "topic_id": 4}
# پارامترهایی که «این تابع دارد به یک پیامِ ورودی جواب می‌دهد» را لو می‌دهند.
REPLY_PARAMS = ("msg", "message", "update")


def _enclosing_map(tree):
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = ([a.arg for a in node.args.args]
                    + [a.arg for a in node.args.kwonlyargs]
                    + [a.arg for a in node.args.posonlyargs])
            spans.append((node.lineno, getattr(node, "end_lineno", node.lineno),
                          node.name, args))
    spans.sort(key=lambda s: (s[1] - s[0]))       # درونی‌ترین اول
    return spans


def _enclosing(spans, line):
    for lo, hi, name, args in spans:
        if lo <= line <= hi:
            return name, args
    return "<module>", []


def _classify_topic(call):
    """سه‌طبقه‌ایِ §بالا. تنها لیترالِ عددی «اثبات‌شده» است."""
    for kw in call.keywords:
        if kw.arg != "topic_id":
            continue
        v = kw.value
        if isinstance(v, ast.Constant):
            if v.value is None:
                return "absent", "None"
            if isinstance(v.value, int):
                return "certain", repr(v.value)
            return "conditional", repr(v.value)
        try:
            expr = ast.unparse(v)
        except Exception:  # noqa: BLE001 — py<3.9
            expr = "<expr>"
        return "conditional", expr
    # kwargs باز شده (**opts) → نمی‌دانیم
    if any(kw.arg is None for kw in call.keywords):
        return "conditional", "**kwargs"
    return "absent", None


def audit_source(src: str, filename: str = "<mem>") -> list:
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [{"file": filename, "line": getattr(exc, "lineno", 0),
                 "error": f"SyntaxError: {exc.msg}"}]
    spans = _enclosing_map(tree)
    sites = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in SEND_METHODS:
            continue
        kinds = {kw.arg for kw in node.keywords if kw.arg}
        # `x.send(...)` هایی که تلگرام نیستند باید رد شوند، وگرنه `sock.send(buf)`
        # به‌عنوانِ «ارسالِ بی‌تاپیک» گزارش می‌شود و کلِ عدد بی‌معنا می‌گردد.
        # سه شاهد: امضای تلگرامی، یا نامِ متدِ اختصاصی، یا نامِ گیرنده.
        recv = ast.unparse(node.func.value) if hasattr(ast, "unparse") else ""
        looks_tg = (
            bool(kinds & {"topic_id", "chat_id", "keyboard", "pin",
                          "reply_markup", "stream"})
            or node.func.attr in STREAM_ROUTED
            or any(tok in recv.lower()
                   for tok in ("client", "channel", "tg", "bot", "telegram")))
        if not looks_tg:
            continue
        fn, args = _enclosing(spans, node.lineno)
        if node.func.attr in STREAM_ROUTED:
            topic_kind, topic_expr = _classify_stream_routed(node, kinds)
            sender = "stream_routed"
        else:
            topic_kind, topic_expr = _classify_topic(node)
            sender = "topic_param"
        sites.append({
            "file": filename, "line": node.lineno, "func": fn,
            "method": node.func.attr, "sender": sender,
            "receiver": ast.unparse(node.func.value) if hasattr(ast, "unparse") else "?",
            "is_reply_path": any(p in args for p in REPLY_PARAMS),
            "topic": topic_kind, "topic_expr": topic_expr,
            "kwargs": sorted(kinds),
        })
    return sites


def _arg_node(call, name):
    """گرهٔ آرگومانِ `name` — چه kwarg باشد چه positional. نبود → None."""
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    pos = _SEND_TEXT_POS.get(name)
    if pos is not None and len(call.args) > pos:
        return call.args[pos]
    return None


def _classify_stream_routed(call, kinds):
    """`send_text`: اول `topic_id` صریح، بعد استنتاج از `stream`.

    منطقِ واقعیِ approval_channel.send_text :
        thread = int(topic_id) if isinstance(topic_id, int) else None
        if thread is None and chat_id is None and stream:  → مسیریابی به تاپیک
    پس دقیقاً به همان ترتیب:
      · topic_id = عددِ ثابت      → ایستا اثبات‌شده → `certain`
      · topic_id = هر عبارتِ زنده → ممکن است None شود → `conditional`
      · topic_id = None/غیرعددی   → `isinstance(...,int)` رد می‌شود، thread همچنان
                                    None است ⇒ می‌افتد به قواعدِ زیر (نه یک طبقهٔ
                                    جدا؛ وگرنه دروغ می‌گفتیم)
      · chat_id صریح             → هرگز تاپیک ندارد → `absent`
      · فقط stream               → شاید تاپیک بگیرد → `conditional`
      · هیچ‌کدام                 → DMِ مالک، تاپیک بی‌معناست → `dm`
    """
    node = _arg_node(call, "topic_id")
    if node is not None:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return "certain", repr(node.value)
            # None یا لیترالِ غیرعددی: عملاً «داده نشده» — ادامه به قواعدِ پایین.
        else:
            try:
                return "conditional", ast.unparse(node)
            except Exception:  # noqa: BLE001 — py<3.9
                return "conditional", "<expr>"
    elif any(kw.arg is None for kw in call.keywords):
        # `**opts` می‌تواند topic_id داشته باشد — ایستا نمی‌دانیم.
        return "conditional", "**kwargs"
    has_chat = "chat_id" in kinds or len(call.args) >= 3
    has_stream = "stream" in kinds or len(call.args) >= 4
    if has_chat:
        return "absent", "chat_id صریح → send_text تاپیک نمی‌گذارد"
    if has_stream:
        return "conditional", "_stream_route(stream)"
    return "dm", "owner DM"


CLASSES = ("certain", "conditional", "absent", "dm")


def summarise(sites: list) -> dict:
    errs = [s for s in sites if "error" in s]
    sites = [s for s in sites if "error" not in s]
    by = {c: 0 for c in CLASSES}
    per_file = {}
    for s in sites:
        cls = s["topic"]
        by[cls] = by.get(cls, 0) + 1
        f = per_file.setdefault(s["file"], {"total": 0, **{c: 0 for c in CLASSES}})
        f["total"] += 1
        f[cls] = f.get(cls, 0) + 1
    reply = [s for s in sites if s["is_reply_path"]]
    total = len(sites)
    return {
        "schema": SCHEMA,
        "total_sites": total,
        "by_topic": by,
        "reply_paths": len(reply),
        "reply_absent": sum(1 for s in reply if s["topic"] == "absent"),
        "reply_conditional": sum(1 for s in reply if s["topic"] == "conditional"),
        # عمداً «pass rate» نامیده نشد: تنها لیترال اثبات‌شده است.
        "proven_rate": (by["certain"] / total) if total else None,
        "unproven": by["conditional"] + by["absent"],
        "parse_errors": errs,
        "per_file": dict(sorted(per_file.items(),
                                key=lambda kv: -kv[1]["absent"])),
    }


def audit_paths(paths) -> tuple:
    sites = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files = sorted(p.rglob("*.py"))
        else:
            files = [p]
        for f in files:
            if "__pycache__" in f.parts:
                continue
            try:
                src = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # فیلترِ ارزان قبل از پارس. نسخهٔ اولِ همین خط `".send("` بود و
            # `send_text` را کاملاً از ممیزی بیرون انداخت — یعنی ابزارِ کشفِ
            # نقطهٔ کور، خودش یک نقطهٔ کور داشت.
            if not any(f".{m}(" in src for m in SEND_METHODS):
                continue
            sites.extend(audit_source(src, str(f)))
    return sites, summarise(sites)


def render(sites, summary) -> str:
    b = summary["by_topic"]
    out = [
        f"📡 ممیزیِ مسیرِ ارسال — {summary['total_sites']} نقطهٔ ارسال",
        f"   اثبات‌شده(literal) {b['certain']}   "
        f"مشروط(runtime) {b['conditional']}   بی‌تاپیک {b['absent']}",
        f"   مسیرهای پاسخ: {summary['reply_paths']}  "
        f"(بی‌تاپیک {summary['reply_absent']}، مشروط {summary['reply_conditional']})",
        "",
        "⚠️ «مشروط» یعنی ایستا نمی‌شود گفت درست است — فقط tg_trace روی لاگِ زنده",
        "   می‌تواند بگوید واقعاً تاپیک خورده یا نه.",
    ]
    bad = [s for s in sites if s.get("topic") == "absent"]
    if bad:
        out.append("")
        out.append(f"🕳 {len(bad)} ارسالِ بدونِ هیچ topic_id:")
        for s in bad[:20]:
            out.append(f"   {Path(s['file']).name}:{s['line']}  {s['func']}()  "
                       f"kwargs={s['kwargs']}")
        if len(bad) > 20:
            out.append(f"   … و {len(bad) - 20} تای دیگر")
    return "\n".join(out)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    targets = [a for a in argv if not a.startswith("--")]
    if not targets:
        targets = [Path(__file__).resolve().parent]
    sites, summary = audit_paths(targets)
    if "--json" in argv:
        print(json.dumps({"summary": summary, "sites": sites},
                         ensure_ascii=False, indent=2))
    else:
        print(render(sites, summary))
    return 0 if summary["reply_absent"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
