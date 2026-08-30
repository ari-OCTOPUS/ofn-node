#!/usr/bin/env python3
"""ردِ ارسال‌های تلگرام — «فرستادم» در برابرِ «کجا نشست».

مسئله‌ای که این ماژول حل می‌کند
────────────────────────────────
شبِ ۲۷ جولای معلوم شد بات **بی‌وقفه** جواب می‌دهد و مالک هیچ‌کدام را نمی‌بیند:
۴۸ پیام / ۵۹٬۴۵۶ نویسه در ۱۲ ساعت به گروه رفته **بدونِ `message_thread_id`**،
یعنی در تاپیکِ General نشسته — جایی که کسی نگاه نمی‌کند. `ok=True` هر ۱۶۲ ارسال.
یعنی «موفق» بود و «رسید» نبود، و هیچ سطحی این تفاوت را نشان نمی‌داد.

`_ops/state/tg-send-log.jsonl` این داده را از قبل داشت (tg_api.py:296 می‌نویسدش)
و **صفر مصرف‌کننده** داشت. این ماژول همان مصرف‌کننده است.

سنجهٔ ابطال‌پذیر
────────────────
    misrouted = ارسال‌هایی که به **گروه** رفتند و تاپیک نداشتند
اگر فلگِ `OCTOPUS_TG_TOPIC_REPLY` واقعاً بارگذاری شود، این عدد باید در پنجرهٔ
بعدی به صفر میل کند. اگر نکرد، فلگ بارگذاری نشده — و این را بدونِ حدس می‌فهمیم.

قواعد
─────
* فقط‌خواندنی، fail-soft، **content-free**: هرگز متنِ پیام چاپ نمی‌شود
  (لاگ هم فقط `sha` و `chars` دارد، نه متن — همان‌طور که باید).
* شناسه‌های عددیِ چت هرگز کامل چاپ نمی‌شوند؛ فقط برچسبِ «گروه» یا «خصوصی».

اجرا:
    python _ops/tg_trace.py            # ۱۵ ارسالِ آخر
    python _ops/tg_trace.py 40         # ۴۰ ارسالِ آخر
    python _ops/tg_trace.py --json     # ماشین‌خوان
    python _ops/tg_trace.py --since 6  # فقط ۶ ساعتِ اخیر
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SCHEMA = "tg-trace.v1"
DEFAULT_LIMIT = 15


def _ops_root() -> Path:
    return Path(__file__).resolve().parent


def _default_paths():
    r = _ops_root()
    return (r / "state" / "tg-send-log.jsonl",
            r / "state" / "telegram" / "center-config.json")


def load_config(config_path):
    """chat_id و نگاشتِ تاپیک‌ها. هر خطا → پیش‌فرضِ خالی (fail-soft)."""
    try:
        d = json.loads(Path(config_path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None, {}
    topics = d.get("topics") if isinstance(d.get("topics"), dict) else {}
    by_id = {}
    for name, num in topics.items():
        try:
            by_id[int(num)] = str(name)
        except (TypeError, ValueError):
            continue
    return d.get("chat_id"), by_id


def load_rows(log_path, since_hours=None, now=None):
    """خواندنِ jsonl. خطوطِ خراب رد می‌شوند و **شمرده** می‌شوند، نه بلعیده."""
    rows, broken = [], 0
    try:
        text = Path(log_path).read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return [], -1
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:  # noqa: BLE001
            broken += 1
            continue
        if isinstance(d, dict):
            rows.append(d)
        else:
            broken += 1
    if since_hours:
        cut = (time.time() if now is None else now) - float(since_hours) * 3600.0
        rows = [r for r in rows if _ts(r) >= cut]
    return rows, broken


def _ts(row) -> float:
    t = row.get("ts")
    if isinstance(t, (int, float)):
        return float(t)
    return 0.0


def classify(row, group_chat_id, topics_by_id):
    """مقصدِ یک ارسال. سه حالت، و فقط یکی‌شان مشکل است."""
    chat = row.get("chat")
    topic = row.get("topic")
    same_group = (group_chat_id is not None
                  and str(chat) == str(group_chat_id))
    if not same_group:
        return "dm", None                       # خصوصی: تاپیک بی‌معناست ✅
    if topic is None:
        return "group_general", None            # ❌ در General می‌افتد
    return "group_topic", topics_by_id.get(int(topic) if isinstance(topic, int) else -1,
                                           f"#{topic}")


def analyse(rows, group_chat_id, topics_by_id) -> dict:
    out = {
        "schema": SCHEMA,
        "total": len(rows),
        "ok": sum(1 for r in rows if r.get("ok") is True),
        "failed": sum(1 for r in rows if r.get("ok") is False),
        "dm": 0, "group_topic": 0, "group_general": 0,
        "misrouted_chars": 0,
        "by_stream": {},
        "window": {"from": None, "to": None},
    }
    for r in rows:
        kind, _name = classify(r, group_chat_id, topics_by_id)
        out[kind] += 1
        stream = str(r.get("stream"))
        s = out["by_stream"].setdefault(stream, {"total": 0, "general": 0})
        s["total"] += 1
        if kind == "group_general":
            s["general"] += 1
            out["misrouted_chars"] += int(r.get("chars") or 0)
    if rows:
        ts = [_ts(r) for r in rows if _ts(r) > 0]
        if ts:
            out["window"] = {"from": min(ts), "to": max(ts)}
    out["misrouted"] = out["group_general"]
    # سنجهٔ گیت: نسبتِ ارسال‌های گروهی که به تاپیکِ درست رفتند.
    grp = out["group_topic"] + out["group_general"]
    out["group_topic_rate"] = (out["group_topic"] / grp) if grp else None
    return out


def _clock(ts):
    if not ts:
        return "??:??:??"
    return time.strftime("%m-%d %H:%M:%S", time.localtime(ts))


def render(rows, stats, topics_by_id, group_chat_id, limit=DEFAULT_LIMIT) -> str:
    """کارتِ انسانی. عددِ مهم اول؛ «اگر هیچ کاری نکنی» آخر."""
    if stats["total"] == 0:
        return "🔭 هیچ ارسالی در این پنجره ثبت نشده."
    head = [
        f"🔭 ردِ ارسال — {stats['total']} ارسال، "
        f"{_clock((stats['window'] or {}).get('from'))} → "
        f"{_clock((stats['window'] or {}).get('to'))}",
        f"✅ موفق {stats['ok']}   ❌ ناموفق {stats['failed']}",
        f"📥 خصوصی {stats['dm']}   🎯 تاپیکِ درست {stats['group_topic']}   "
        f"🕳 General {stats['group_general']}",
    ]
    if stats["misrouted"]:
        head.append(
            f"🚩 {stats['misrouted']} پیام ({stats['misrouted_chars']:,} نویسه) "
            f"به گروه رفت بدونِ تاپیک → در General نشست، جایی که نگاه نمی‌کنی.")
        worst = sorted(stats["by_stream"].items(),
                       key=lambda kv: -kv[1]["general"])
        worst = [(k, v) for k, v in worst if v["general"]][:3]
        if worst:
            head.append("   مقصر: " + "، ".join(
                f"{k} ({v['general']}/{v['total']})" for k, v in worst))
    lines = []
    for r in rows[-limit:]:
        kind, name = classify(r, group_chat_id, topics_by_id)
        where = {"dm": "خصوصی", "group_general": "🕳 General"}.get(kind, f"🎯 {name}")
        mark = "✅" if r.get("ok") is True else "❌"
        lines.append(f"  {_clock(_ts(r))} {mark} {where:<16} "
                     f"{str(r.get('stream') or '—'):<10} {r.get('chars') or 0} نویسه")
    tail = ("\nاگر هیچ کاری نکنی: همین نسبت ادامه پیدا می‌کند."
            if stats["misrouted"] else "")
    return "\n".join(head + ["", *lines]) + tail


def trace(log_path=None, config_path=None, limit=DEFAULT_LIMIT, since_hours=None):
    """APIِ اصلی. هیچ‌وقت استثنا پرتاب نمی‌کند."""
    try:
        lp, cp = _default_paths()
        lp = Path(log_path) if log_path else lp
        cp = Path(config_path) if config_path else cp
        chat_id, topics = load_config(cp)
        rows, broken = load_rows(lp, since_hours=since_hours)
        stats = analyse(rows, chat_id, topics)
        stats["broken_lines"] = broken
        stats["config_found"] = chat_id is not None
        return rows, stats, topics, chat_id
    except Exception as exc:  # noqa: BLE001
        return [], {"schema": SCHEMA, "total": 0, "error":
                    f"{type(exc).__name__}: {exc}"}, {}, None


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    limit, since = DEFAULT_LIMIT, None
    for i, a in enumerate(argv):
        if a.isdigit():
            limit = int(a)
        elif a == "--since" and i + 1 < len(argv):
            try:
                since = float(argv[i + 1])
            except ValueError:
                pass
    rows, stats, topics, chat_id = trace(limit=limit, since_hours=since)
    if "--json" in argv:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(render(rows, stats, topics, chat_id, limit=limit))
    return 0 if not stats.get("misrouted") else 1


if __name__ == "__main__":
    raise SystemExit(main())
