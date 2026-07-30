#!/usr/bin/env python3
"""test_cycle — حلقهٔ آزمونِ ۷ روزه: کادنسِ خودش، دفترِ خودش، و آشکارسازِ چرخشِ روش.

رأیِ مالک ۲۰۲۶-۰۷-۳۰: «تست رو بکن روزی دوبار و همشم خودش تصمیم بگیره.»

چرا کادنسِ جدا و نه دو برابر کردنِ بلوکِ روزانه
──────────────────────────────────────────────
بلوکِ روزانهٔ `organism.py` با `opslib.today() != last_daily` گیت می‌شود
(organism.py:774) — یعنی fitness، replication، NOTE(ORGANISM_DAILY)، reconcile،
actuator و C6 همه در یک بستهٔ روزی‌یک‌بار هستند. دو برابر کردنِ آن گیت، **همهٔ
آن‌ها** را دو برابر می‌کرد؛ ولی چیزی که آزمون لازم دارد دو چرخهٔ *یادگیری* است،
نه دو اسنپ‌شاتِ fitness. پس این ماژول کادنسِ خودش را دارد و بلوکِ روزانه
دست‌نخورده می‌ماند.

آشکارسازِ چرخشِ روش — دردی که این می‌بندد
────────────────────────────────────────
«حلقهٔ روشنِ بی‌محصول»: تا امروز هیچ‌چیز «روشِ A دو بار شکست، رفتم سراغِ B» را از
«همان حلقه را ۱۰ بار زدم» تفکیک نمی‌کرد. هر دو در لاگ شبیهِ «فعال» به‌نظر
می‌آیند. این‌جا هر چرخه روشش را اعلام می‌کند و تفاوت با چرخهٔ قبل **شمرده**
می‌شود — چرخش با دلیل، یا تکرارِ بی‌تغییر با شمارنده. هیچ‌کدام صفت نمی‌گیرد؛
هر دو عدد می‌شوند.

⚠️ شمارندهٔ تکرار **روی خودِ روش** کلید می‌خورد نه روی زمان — درسِ «شمارنده در
کلیدِ dedup»: اگر گذشتِ زمان را «تغییر» بشماری، گاردِ درست روی مکانیزمِ غلط
می‌نشیند و صفر اثر دارد.

$0 · stdlib · fail-soft · propose-only (هیچ اثرِ بیرونی از این فایل).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_TEST_CYCLE"
SCHEMA = "test_cycle.v1"
CARD_TITLE = "🔬 حلقهٔ آزمون"

STATE = opslib.STATE_DIR / "test_cycle" / "state.json"
JOURNAL = opslib.STATE_DIR / "test_cycle" / "journal.jsonl"

SLOTS_ENV = "OCTOPUS_TEST_CYCLE_SLOTS"          # چند چرخه در روز
SPLIT_ENV = "OCTOPUS_TEST_CYCLE_SPLIT_HOUR"     # مرزِ ساعتِ اسلات‌ها
_DEFAULT_SLOTS = 2
_DEFAULT_SPLIT = 12


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    try:
        return int(str(os.environ.get(name, "")).strip())
    except (TypeError, ValueError):
        return default


def _slots() -> int:
    return max(1, min(_int_env(SLOTS_ENV, _DEFAULT_SLOTS), 24))


def _split_hour() -> int:
    return max(1, min(_int_env(SPLIT_ENV, _DEFAULT_SPLIT), 23))


# ─── کادنس ──────────────────────────────────────────────────────────────────
def slot_of(now: "float | None" = None) -> int:
    """کدام اسلاتِ امروز. `now` کاملاً تزریق‌شدنی است — هیچ شاخه‌ای ساعتِ دیوار را
    پشتِ سرِ صداکننده نمی‌خواند (درسِ «ساعتِ نیمه‌تزریقی = بمبِ ساعتی»)."""
    import datetime as _dt
    ts = float(now if now is not None else time.time())
    hour = _dt.datetime.fromtimestamp(ts).hour
    n = _slots()
    if n <= 1:
        return 0
    if n == 2:
        return 0 if hour < _split_hour() else 1
    return min(n - 1, (hour * n) // 24)


def _day(now: "float | None" = None) -> str:
    import datetime as _dt
    ts = float(now if now is not None else time.time())
    return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def cycle_id(now: "float | None" = None) -> str:
    return f"{_day(now)}#{slot_of(now)}"


def _load() -> dict:
    try:
        if STATE.exists():
            d = json.loads(STATE.read_text("utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {"done": []}


def _save(d: dict) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, STATE)
    except OSError:
        pass


def due(now: "float | None" = None) -> dict:
    """آیا چرخهٔ این اسلات هنوز اجرا نشده؟"""
    cid = cycle_id(now)
    done = _load().get("done") or []
    return {"due": cid not in done, "cycle_id": cid,
            "slot": slot_of(now), "slots_per_day": _slots()}


def _mark_done(cid: str) -> None:
    d = _load()
    done = list(d.get("done") or [])
    if cid not in done:
        done.append(cid)
    d["done"] = done[-64:]          # فقط تاریخِ نزدیک لازم است
    _save(d)


# ─── دفتر ───────────────────────────────────────────────────────────────────
def _rows() -> list:
    out: list = []
    try:
        if not JOURNAL.exists():
            return out
        with open(JOURNAL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("schema") == SCHEMA:
                    out.append(d)
    except OSError:
        pass
    return out


def _method_key(method: str) -> str:
    """کلیدِ پایدارِ روش — چرخش روی **محتوای روش** سنجیده می‌شود، نه روی زمان."""
    norm = " ".join(str(method or "").strip().lower().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]


def detect_switch(goal_key: str, method: str) -> dict:
    """این چرخه روش را عوض کرد یا همان را تکرار کرد؟

    مقایسه با **آخرین چرخهٔ همان هدف**. اگر هدف تازه است، نه چرخش است نه تکرار
    — و صریح `first` برمی‌گردد، چون «صفرِ ساکت» شبیهِ «تکرار» به‌نظر می‌آید."""
    mk = _method_key(method)
    prev = None
    for r in _rows():
        if r.get("goal_key") == goal_key:
            prev = r
    if prev is None:
        return {"kind": "first", "method_key": mk, "repeat_n": 1,
                "prev_method_key": None}
    pk = prev.get("method_key")
    if pk == mk:
        return {"kind": "repeat", "method_key": mk, "prev_method_key": pk,
                "repeat_n": int(prev.get("repeat_n", 1) or 1) + 1}
    return {"kind": "switch", "method_key": mk, "prev_method_key": pk,
            "repeat_n": 1, "switched_from": str(prev.get("method") or "")[:200]}


def record(*, goal: str, method: str, why: str = "", cycle: "str | None" = None,
           goal_source: str = "self", outcome: "dict | None" = None,
           now: "float | None" = None) -> dict:
    """یک چرخه را در دفتر بنشان (شاملِ حکمِ چرخش/تکرار).

    `goal_source` عمداً ثبت می‌شود: رأیِ مالک این بود که هدف را خودش بگذارد، پس
    اگر روزی هدف از بیرون تزریق شود، کارتِ نمره باید بتواند تفکیک کند."""
    goal_key = _method_key(goal)          # همان نرمال‌سازی، برای هدف
    sw = detect_switch(goal_key, method)
    rec = {"ts": opslib.now_iso(), "schema": SCHEMA,
           "cycle_id": cycle or cycle_id(now), "slot": slot_of(now),
           "goal": str(goal or "")[:400], "goal_key": goal_key,
           "goal_source": str(goal_source or "")[:40],
           "method": str(method or "")[:400], "why": str(why or "")[:300],
           "outcome": outcome or {}, **sw}
    try:
        opslib.append_jsonl(JOURNAL, rec)
    except (OSError, ValueError):
        return {"ok": False, "reason": "write-failed", **rec}
    return {"ok": True, **rec}


# ─── اجرای یک چرخه ──────────────────────────────────────────────────────────
def run(*, goal: str, method: str, why: str = "", goal_source: str = "self",
        now: "float | None" = None, force: bool = False) -> dict:
    """یک چرخهٔ آزمون: سنجه‌ها را نمونه بگیر، نیازِ ابزار را اسکن کن، دفتر بنویس.

    ترتیب عمدی است: اول **بازیابی** (چه چیزی از گذشته مربوط است)، بعد اسکنِ
    ابزار، آخر ثبت. چون بازیابی باید بتواند روشِ همین چرخه را عوض کند."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    d = due(now)
    if not d["due"] and not force:
        return {"ok": False, "reason": "not-due", **d}

    out: dict = {"cycle_id": d["cycle_id"], "slot": d["slot"]}

    # ۱) بازیابی — سنجهٔ «به یاد می‌آورد؟»
    try:
        import recall_trend as _rt
        out["recall"] = _rt.sample(cycle=d["cycle_id"], now=now)
    except Exception as e:  # noqa: BLE001 — هیچ سنجه‌ای چرخه را نمی‌کشد
        out["recall"] = {"ok": False, "reason": f"{type(e).__name__}"}

    # ۲) نیازِ ابزار — سنجهٔ «دقیق و به‌موقع می‌خواهد؟»
    try:
        import tool_request as _tr
        out["tool_request"] = _tr.scan(cycle=d["cycle_id"], now=now)
    except Exception as e:  # noqa: BLE001
        out["tool_request"] = {"ok": False, "reason": f"{type(e).__name__}"}

    # ۳) دفتر — سنجهٔ «مسیر را وسطِ کار اصلاح می‌کند؟»
    rec = record(goal=goal, method=method, why=why, goal_source=goal_source,
                 cycle=d["cycle_id"], now=now,
                 outcome={"recall_ok": bool((out.get("recall") or {}).get("ok")),
                          "tool_request_ok": bool((out.get("tool_request") or {}).get("ok"))})
    out["journal"] = rec
    _mark_done(d["cycle_id"])
    return {"ok": True, **out}


# ─── کارتِ نمره ─────────────────────────────────────────────────────────────
def scorecard() -> dict:
    """شمارشِ خامِ سنجه‌های آزمون. هیچ صفتی — فقط عدد.

    آستانه‌ها این‌جا **نیستند**: آن‌ها در فایلِ پیش‌ثبت روی دیسک‌اند و باید قبل از
    اولین چرخه mtime گرفته باشند. اگر آستانه این‌جا می‌بود، می‌شد بعد از دیدنِ
    نتیجه تغییرش داد — همان `alter_acceptance_criteria` که governance ممنوع کرده."""
    rows = _rows()
    switches = [r for r in rows if r.get("kind") == "switch"]
    repeats = [r for r in rows if r.get("kind") == "repeat"]
    stuck = max([int(r.get("repeat_n", 1) or 1) for r in rows] or [0])
    self_set = [r for r in rows if r.get("goal_source") == "self"]

    tr_total = tr_precise = tr_blocking = 0
    waits: list = []
    try:
        import tool_request as _tr
        for r in _tr._rows():
            if r.get("schema") == _tr.SCHEMA:
                tr_total += 1
                tr_precise += 1 if r.get("precise") else 0
                tr_blocking += 1 if r.get("blocking") else 0
            elif r.get("schema") == _tr.SCHEMA + ".answer":
                if isinstance(r.get("wait_s"), (int, float)):
                    waits.append(float(r["wait_s"]))
    except Exception:  # noqa: BLE001
        pass

    recall: dict = {}
    try:
        import recall_trend as _rt
        recall = _rt.trend()
    except Exception:  # noqa: BLE001
        pass

    return {
        "cycles": len(rows),
        "cycles_self_set": len(self_set),
        "method_switches": len(switches),
        "method_repeats": len(repeats),
        "longest_unchanged_streak": stuck,
        "tool_requests": tr_total,
        "tool_requests_precise": tr_precise,
        "tool_requests_blocking": tr_blocking,
        "owner_answers": len(waits),
        "median_wait_s": (sorted(waits)[len(waits) // 2] if waits else None),
        "recall_trend": recall.get("overall") if recall.get("ok") else recall.get("reason"),
        "recall_improved": recall.get("improved"),
        "recall_worsened": recall.get("worsened"),
    }


def card() -> tuple:
    """بی‌آرگومان، پس `capability_registry` خودش پیدایش می‌کند."""
    import html
    s = scorecard()
    d = due()
    body = (f"🔬 <b>حلقهٔ آزمون</b> — {s['cycles']} چرخه "
            f"({s['cycles_self_set']} خودتعیین)\n"
            f"اسلاتِ الان: {d['slot']} از {d['slots_per_day']} · "
            f"{'⏳ موعدش است' if d['due'] else '✅ اجرا شده'}\n\n"
            f"<b>اصلاحِ مسیر</b>\n"
            f"  چرخشِ روش: <b>{s['method_switches']}</b> · "
            f"تکرار: {s['method_repeats']}\n"
            f"  بلندترین زنجیرهٔ بی‌تغییر: {s['longest_unchanged_streak']}\n\n"
            f"<b>درخواستِ ابزار</b>\n"
            f"  {s['tool_requests']} درخواست، <b>{s['tool_requests_precise']}</b> دقیق"
            f" ({s['tool_requests_blocking']} بازدارنده)\n"
            f"  رأیِ تو: {s['owner_answers']}")
    if s.get("median_wait_s") is not None:
        body += f" · انتظارِ میانه: {int(s['median_wait_s'] // 60)} دقیقه"
    body += (f"\n\n<b>بردِ بازیابی</b>\n  روند: "
             f"{html.escape(str(s.get('recall_trend')))}")
    if s.get("recall_improved") is not None:
        body += f" ({s['recall_improved']} بهتر، {s['recall_worsened']} بدتر)"
    return body[:3500], []


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "due": due(),
                      "scorecard": scorecard(), "journal": str(JOURNAL)},
                     ensure_ascii=False, indent=1))
