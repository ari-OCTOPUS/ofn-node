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

    # ── چرا این‌جا «مشاهده» می‌کنیم و «فراخوانی» نمی‌کنیم (اثباتِ زندهٔ ۱۳:۱۲) ──
    # `organism.py` از قبل هر تیک `recall_trend.sample()` و `tool_request.scan()`
    # را صدا می‌زند. نسخهٔ اولِ این تابع دوباره صدایشان زد و در همان تیک:
    #   · recall دو ردیفِ **یکسان** نوشت → پنجرهٔ `trend()` نصف شد؛
    #   · scan سهمیه را سوخته دید و `too-soon` گرفت، پس دفتر
    #     `tool_request_ok: false` ثبت کرد — یعنی «این چرخه ابزار نخواست»،
    #     در حالی که همان چرخه یک درخواستِ دقیق و delivered ساخته بود.
    # آن یک **دروغِ سنجش** بود، دقیقاً از جنسی که کلِ این هارنس برای بستنش است.
    # پس سنجه از دفترِ روی دیسک خوانده می‌شود، نه از فراخوانیِ دوباره.

    # ۱) بازیابی — سنجهٔ «به یاد می‌آورد؟». فقط اگر سری کاملاً خالی بود خودمان
    # یک نمونه می‌گیریم (تا چرخهٔ اول روی ترازوی خالی ننشیند).
    try:
        import recall_trend as _rt
        _rows_rt = _rt._rows()
        if _rows_rt:
            _last = _rows_rt[-1]
            out["recall"] = {"ok": True, "observed": True, "samples": len(_rows_rt),
                             **{k: _last.get(k) for k in
                                ("events", "keys", "reach_median", "self_ratio",
                                 "coverage")}}
        else:
            out["recall"] = _rt.sample(cycle=d["cycle_id"], now=now)
    except Exception as e:  # noqa: BLE001 — هیچ سنجه‌ای چرخه را نمی‌کشد
        out["recall"] = {"ok": False, "reason": f"{type(e).__name__}"}

    # ۲) نیازِ ابزار — سنجهٔ «دقیق و به‌موقع می‌خواهد؟». شمارشِ انباشتی؛ دلتای
    # بینِ دو چرخهٔ متوالی همان «چند درخواست در این چرخه» است. هیچ سهمیه‌ای
    # سوزانده نمی‌شود و هیچ تماسِ پولی‌ای از این مسیر نمی‌رود.
    try:
        import tool_request as _tr
        _trs = [r for r in _tr._rows() if r.get("schema") == _tr.SCHEMA]
        out["tool_request"] = {
            "ok": True, "observed": True, "total": len(_trs),
            "precise": sum(1 for r in _trs if r.get("precise")),
            "delivered": sum(1 for r in _trs if r.get("delivered")),
            "blocking": sum(1 for r in _trs if r.get("blocking"))}
    except Exception as e:  # noqa: BLE001
        out["tool_request"] = {"ok": False, "reason": f"{type(e).__name__}"}

    # ۳) دفتر — سنجهٔ «مسیر را وسطِ کار اصلاح می‌کند؟»
    _tro = out.get("tool_request") or {}
    _rco = out.get("recall") or {}
    rec = record(goal=goal, method=method, why=why, goal_source=goal_source,
                 cycle=d["cycle_id"], now=now,
                 outcome={"recall_ok": bool(_rco.get("ok")),
                          "recall_events": _rco.get("events"),
                          "tool_request_ok": bool(_tro.get("ok")),
                          "tool_requests_total": _tro.get("total"),
                          "tool_requests_precise": _tro.get("precise")})
    out["journal"] = rec
    _mark_done(d["cycle_id"])
    return {"ok": True, **out}


# ─── صداکنندهٔ سطحِ beat ────────────────────────────────────────────────────
def beat(*, channel=None, now: "float | None" = None) -> dict:  # noqa: ARG001
    """کلِ چرخه از یک نقطه: ارزیابیِ معوق → هدف → پیش‌ثبت → اجرا.

    این همان صداکننده‌ای است که نبودش تنها بلاکرِ ساختاریِ آزمون بود
    (SELF-GOAL-CHARTER §۷). سوار بر beat ِ موجودِ organism — poller ِ نو ممنوع.

    ترتیب و قواعدِ سخت:
      ۱) ارزیابیِ معوقِ چرخه‌های قبلی **قبل** از هدفِ نو — تا مولدِ هدف حکمِ
         تازهٔ FAIL را ببیند و چرخشِ روش مکانیکی بماند.
      ۲) هدفِ بی‌ترازو → چرخه اجرا نمی‌شود (اسلات هم نمی‌سوزد؛ tick ِ بعد دوباره).
      ۳) پیش‌ثبتِ ناموفق → **fail-closed**: هیچ اجرایی. target ِ ثبت‌نشده یعنی
         بعداً قابلِ جابه‌جایی است — همان چیزی که PRE-0 ممنوع کرده.
      ۴) `channel` فقط برای آینده نگه داشته شده؛ v1 کارت نمی‌فرستد (کارتِ
         on-demand از `card()` در capability_registry هست — نویزِ گروه ممنوع).
    """
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    out: dict = {}
    # ۱) ارزیابیِ معوق — ارزان و idempotent؛ هر tick امن است.
    try:
        import cycle_evaluator as _ce
        ev = _ce.evaluate_pending(now=now)
        if ev.get("evaluated"):
            out["evaluated"] = ev["evaluated"]
            out["verdicts"] = [{k: v.get(k) for k in ("verdict", "goal_key", "cycle_id")}
                               for v in (ev.get("verdicts") or [])]
    except Exception as e:  # noqa: BLE001 — ارزیابی هرگز beat را نمی‌کشد
        out["eval_error"] = type(e).__name__
    d = due(now)
    out.update({"cycle_id": d["cycle_id"], "slot": d["slot"]})
    if not d["due"]:
        return {"ok": False, "reason": "not-due", **out}
    # ۲) هدف — از مولد؛ بی‌ترازو = بی‌چرخه.
    try:
        import goal_generator as _gg
        g = _gg.propose(now=now)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"generator-error:{type(e).__name__}", **out}
    if not g.get("ok"):
        return {"ok": False, "reason": "no-valid-goal",
                "skipped": g.get("skipped"), **out}
    # ۳) پیش‌ثبت — fail-closed. بدونِ ردیفِ prereg روی دیسک، اجرا ممنوع.
    try:
        import prereg as _pr
        p = _pr.register(g, cycle=d["cycle_id"], now=now)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"prereg-error:{type(e).__name__}", **out}
    if not p.get("ok"):
        return {"ok": False, "reason": "prereg-failed",
                "detail": p.get("reason"), **out}
    # ۴) اجرا — همان run ِ موجود (بازیابی → اسکنِ ابزار → دفتر + mark_done).
    r = run(goal=g["goal"], method=g["method"], why=g.get("why", ""),
            goal_source=str(g.get("goal_source") or "self"), now=now)
    out.update({"ok": bool(r.get("ok")), "prereg_id": p.get("prereg_id"),
                "goal_key": g.get("goal_key"),
                "candidate": g.get("candidate_key"),
                "method_note": g.get("method_note"),
                "switch": (r.get("journal") or {}).get("kind"),
                "run_reason": r.get("reason")})
    return out


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
