#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_question_producers — اختاپوس واقعاً می‌پرسد (رأی ۲۴، W4 لِین H).

    هر تولیدکننده روی artifact ِ کاشته‌شده شلیک می‌کند و **بدونِ آن ساکت
    است** · dedup ِ هفته می‌گیرد و rollover آزادش می‌کند · تولید از مسیرِ
    بودجه رد می‌شود و از سقف نمی‌گذرد · هیچ سؤالی حقیقتِ نانوشته ادعا
    نمی‌کند (نقلِ artifact اجباری) · هیچ *مقدارِ* فلگی به متن نشت نمی‌کند
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import harness

ENV = harness.setup("tg-question-producers")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import opslib  # noqa: E402
import question_producers as qp  # noqa: E402
import question_budget as qb  # noqa: E402
import leg_tasks as lt  # noqa: E402

STATE = Path(ENV["OCTOPUS_STATE_DIR"])
OPS = Path(opslib.OPS)

# سه‌شنبه 2026-07-28 10:00 محلی — وسطِ یک هفتهٔ ISO
NOW = datetime(2026, 7, 28, 10, 0).timestamp()
NEXT_WEEK = NOW + 7 * 86400
H = 3600.0

_FLAGS = [c[0] for c in qp.CHARTER_CAPABILITIES]


def _fresh():
    """هر تست از صفرِ مطلق شروع می‌کند — چون scan همهٔ تولیدکننده‌ها را با هم
    می‌دواند، خاموش‌بودنِ بقیه شرطِ خواناییِ تست است."""
    for p in (qp._ledger_path(), qb._path(),
              STATE / "legs" / "lead-pipeline.json",
              STATE / "fitness-latest.json", STATE / "telemetry-latest.json",
              STATE / "cortex" / "outcomes.jsonl",
              OPS / "GOALS-OCTOPUS.md"):
        try:
            p.unlink()
        except OSError:
            pass
    for leg in qp.LEGS:
        try:
            lt._path(leg).unlink()
        except OSError:
            pass
    for p in STATE.glob("flags-loaded-*.json"):
        try:
            p.unlink()
        except OSError:
            pass
    for f in _FLAGS:
        os.environ.pop(f, None)


def _by(items, producer):
    return [it for it in items if it.get("producer") == producer]


def _errors(items):
    return [it for it in items if it.get("status") == "error"]


# ── (۱) پای مسدود بیش از ۲۴ ساعت ──────────────────────────────────────────
def _plant_blocked(leg, text, question, *, age_s):
    t = lt.add(leg, text, now=NOW - age_s)
    return lt.set_state(leg, t["id"], lt.BLOCKED, question=question,
                        now=NOW - age_s)


def t_blocked_leg_over_24h_asks_and_quotes_the_task():
    _fresh()
    t = _plant_blocked("mining", "چک کردن نرخ هش ریگ ۳",
                       "کدام استخر را انتخاب کنم؟", age_s=25 * H)
    got = _by(qp.scan(now=NOW), "blocked-leg")
    assert len(got) == 1, got
    item = got[0]["item"]
    assert "mining" in item["q"] and t["id"] in item["q"], item
    # نقلِ artifact اجباری است — سؤالِ بی‌شاهد ممنوع
    assert "mining-tasks.json" in item["context"], item
    assert "کدام استخر" in item["context"], item
    assert "هدفِ مشترک" in item["goal"], item


def t_blocked_leg_is_silent_below_the_window_and_without_the_artifact():
    _fresh()
    assert _by(qp.scan(now=NOW), "blocked-leg") == [], "بی‌artifact پرسید"
    _fresh()
    _plant_blocked("crypto", "بررسی پوزیشن", "چقدر ریسک؟", age_s=23 * H)
    assert _by(qp.scan(now=NOW), "blocked-leg") == [], "زیر ۲۴ ساعت پرسید"


def t_a_resolved_block_stops_being_a_question():
    """کارِ BLOCKED که مالک جوابش را داد (WORKING) دیگر سؤال نیست."""
    _fresh()
    t = _plant_blocked("lead", "پیگیریِ چتسوود", "آدرس دقیق؟", age_s=30 * H)
    assert lt.resolve_blocked("lead", t["id"], "چتسوود، خیابان ویکتوریا",
                              now=NOW - 2 * H)
    assert _by(qp.scan(now=NOW), "blocked-leg") == []


# ── (۲) لیدِ گیرکرده روی اطلاعاتِ ناقص بیش از ۱۲ ساعت ──────────────────────
def _plant_stuck(lead_id, question, *, age_s, desc="نقاشی داخلیِ واحد ۳"):
    p = STATE / "legs" / "lead-pipeline.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"stuck": {lead_id: {
        "task_id": "TASK-1", "question": question, "since": NOW - age_s,
        "lead": {"description": desc}}}, "followups": {}},
        ensure_ascii=False), "utf-8")


def t_lead_stuck_over_12h_asks_for_exactly_the_missing_field():
    _fresh()
    _plant_stuck("LEAD-abc123", "آدرسِ ملک را نمی‌دانم — کجاست؟", age_s=13 * H)
    got = _by(qp.scan(now=NOW), "lead-missing-info")
    assert len(got) == 1, got
    item = got[0]["item"]
    assert "آدرسِ ملک" in item["q"], item          # دقیقاً همان قلمِ گمشده
    assert "lead-pipeline.json" in item["context"], item
    assert "نقاشی داخلیِ واحد ۳" in item["context"], item


def t_lead_stuck_is_silent_below_the_window_and_without_the_store():
    _fresh()
    assert _by(qp.scan(now=NOW), "lead-missing-info") == []
    _fresh()
    _plant_stuck("LEAD-fresh", "متراژ؟", age_s=11 * H)
    assert _by(qp.scan(now=NOW), "lead-missing-info") == [], "زیر ۱۲ ساعت پرسید"


# ── (۳) قابلیتِ ساخته‌شده ولی خلعِ‌سلاح ────────────────────────────────────
_SENTINEL = "SENTINEL-NOT-A-REAL-VALUE"


def _plant_flags(**flags):
    p = STATE / "flags-loaded-center.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    # کلیدِ شبه-secret عمداً داخلِ فیکسچر است تا گاردِ نشت دندان داشته باشد.
    body = {"SOME_API_KEY": _SENTINEL}
    body.update({k: str(v) for k, v in flags.items()})
    p.write_text(json.dumps({"schema": "flags-loaded.v1", "pid": 1,
                             "flags": body}, ensure_ascii=False), "utf-8")


def t_disarmed_capability_asks_with_its_one_line_consequence():
    _fresh()
    _plant_flags(OCTOPUS_TG_REMINDERS="0")
    got = _by(qp.scan(now=NOW), "disarmed-capability")
    assert len(got) == 1, got
    item = got[0]["item"]
    assert "یادآوریِ زبانِ طبیعی" in item["q"], item
    assert "زنگ می‌زنند" in item["q"], "پیامدِ یک‌خطی نیامد"
    assert "OCTOPUS_TG_REMINDERS" in item["context"], item
    assert "flags-loaded-center.json" in item["context"], item


def t_no_flag_value_ever_leaks_into_a_question():
    """🔐 فایلِ زندهٔ flags کلیدهای secret هم دارد — این ماژول فقط نام و
    مقایسه با «۱» می‌خواند. جهشِ نشتِ مقدار باید این را قرمز کند."""
    _fresh()
    _plant_flags(OCTOPUS_TG_REMINDERS="0")
    blob = json.dumps(qp.scan(now=NOW), ensure_ascii=False)
    assert _SENTINEL not in blob, "مقدارِ فلگ به متنِ سؤال نشت کرد"


def t_armed_capability_is_not_asked_about():
    _fresh()
    _plant_flags(**{f: "1" for f in _FLAGS})
    assert _by(qp.scan(now=NOW), "disarmed-capability") == []


def t_disarmed_producer_is_silent_without_any_flags_file():
    """هیچ پروسه‌ای فلگ‌هایش را ننوشته ⇒ ادعای «خاموش است» شاهد ندارد."""
    _fresh()
    assert _by(qp.scan(now=NOW), "disarmed-capability") == []


# ── (۴) ماهِ بی‌درآمدِ خرج‌دار ─────────────────────────────────────────────
def _plant_money(*, claimed=0, cells=None, aud=12.5, telemetry=True):
    (STATE / "fitness-latest.json").write_text(json.dumps(
        {"ts": "2026-07-25T11:00:54",
         "attribution": {"claimed": claimed, "confirmed": 0,
                         "revenue_by_cell": cells or {}}},
        ensure_ascii=False), "utf-8")
    if telemetry:
        (STATE / "telemetry-latest.json").write_text(json.dumps(
            {"ts": "2026-07-28T09:00:00",
             "month": {"key": "2026-07", "aud": aud}},
            ensure_ascii=False), "utf-8")


def t_zero_revenue_with_real_cost_asks_which_business_to_automate():
    _fresh()
    _plant_money()
    got = _by(qp.scan(now=NOW), "money-zero-revenue")
    assert len(got) == 1, got
    item = got[0]["item"]
    assert "کدام بیزنس" in item["q"], item
    assert "fitness-latest.json" in item["context"], item
    assert "telemetry-latest.json" in item["context"], item
    assert "AU$۱۲.۵" in item["context"], item      # عددِ واقعیِ artifact


def t_money_producer_is_silent_when_revenue_exists_or_cost_is_trivial():
    _fresh()
    _plant_money(claimed=250.0)
    assert _by(qp.scan(now=NOW), "money-zero-revenue") == [], "با درآمد پرسید"
    _fresh()
    _plant_money(cells={"lead.doer": 100})
    assert _by(qp.scan(now=NOW), "money-zero-revenue") == [], "با سلولِ پول پرسید"
    _fresh()
    _plant_money(aud=0.03)
    assert _by(qp.scan(now=NOW), "money-zero-revenue") == [], "سرِ ۳ سِنت پرسید"
    _fresh()
    _plant_money(telemetry=False)      # خرج ناشناخته ⇒ ادعای «خرج داشتیم» نه
    assert _by(qp.scan(now=NOW), "money-zero-revenue") == []


# ── (۵) هدفِ بی‌حرکتِ ۷ روزه ──────────────────────────────────────────────
GOAL_A = "**اولین پولِ مطالبه‌شده:** `attribution.claimed` از صفر دربیاید."
GOAL_B = "حافظهٔ ماندگار مثلِ شرکت‌های بزرگ: با خاموش/روشن هیچ‌چیز گم نشود."


def _plant_goals():
    OPS.mkdir(parents=True, exist_ok=True)
    (OPS / "GOALS-OCTOPUS.md").write_text(
        f"# GOALS\n\n## اهداف\n- {GOAL_A}\n- {GOAL_B}\n", "utf-8")


def _plant_outcomes(rows):
    p = STATE / "cortex" / "outcomes.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                         for r in rows), "utf-8")


def t_a_goal_with_no_movement_in_7_days_is_questioned():
    _fresh()
    _plant_goals()
    recent = datetime.fromtimestamp(NOW - 2 * 86400).isoformat()
    stale = datetime.fromtimestamp(NOW - 9 * 86400).isoformat()
    _plant_outcomes([
        {"ts": recent, "id": "up-1", "serves_goal": GOAL_A, "baseline": {}},
        {"ts": stale, "id": "up-2", "serves_goal": GOAL_B, "baseline": {}},
    ])
    got = _by(qp.scan(now=NOW), "stale-goal")
    assert len(got) == 1, got
    item = got[0]["item"]
    assert "حافظهٔ ماندگار" in item["q"], item      # فقط هدفِ بی‌حرکت
    assert "attribution.claimed" not in item["q"], "هدفِ متحرک را هم پرسید"
    assert "GOALS-OCTOPUS.md" in item["context"], item
    assert "outcomes.jsonl" in item["context"], item


def t_stale_goal_is_silent_when_the_movement_ledger_does_not_exist():
    """غیابِ صادقانه: «حرکتی ندیدم» با «جایی برای دیدن نبود» یکی نیست.
    (جهشِ برداشتنِ گاردِ `is_file` این را قرمز می‌کند.)"""
    _fresh()
    _plant_goals()                       # هدف هست، دفترِ حرکت نیست
    assert not (STATE / "cortex" / "outcomes.jsonl").exists()
    assert _by(qp.scan(now=NOW), "stale-goal") == []


def t_stale_goal_is_silent_without_a_goals_file():
    _fresh()
    _plant_outcomes([{"ts": datetime.fromtimestamp(NOW).isoformat(),
                      "id": "up-1", "serves_goal": GOAL_A, "baseline": {}}])
    assert _by(qp.scan(now=NOW), "stale-goal") == []


# ── dedup ِ هفته ───────────────────────────────────────────────────────────
def t_the_same_question_is_never_asked_twice_in_one_week():
    _fresh()
    _plant_blocked("mining", "چک کردن ریگ", "کدام استخر؟", age_s=25 * H)
    first = _by(qp.scan(now=NOW), "blocked-leg")
    assert len(first) == 1, first
    for k in range(1, 5):                # چهار ضربانِ بعدی — همان artifact
        assert _by(qp.scan(now=NOW + k * H), "blocked-leg") == [], k
    q = json.loads(qb._path().read_text("utf-8"))["queue"]
    assert len(q) == 1, q                # یک آیتم در کلِ صف، نه پنج‌تا
    assert list(qp.asked_keys(NOW)) == [first[0]["key"]]


def t_scan_throttles_itself_so_the_beat_can_call_it_every_tick():
    """ضربانِ مرکز چند-ثانیه‌ای است؛ throttle داخلِ ماژول است تا سیمِ مرکز
    یک خط بماند. `force` فقط برای بازرسیِ دستی."""
    _fresh()
    _plant_blocked("mining", "چک کردن ریگ", "کدام استخر؟", age_s=25 * H)
    assert len(_by(qp.scan(now=NOW), "blocked-leg")) == 1
    _plant_stuck("LEAD-abc", "متراژ؟", age_s=20 * H)     # artifact ِ تازه
    assert qp.scan(now=NOW + 60) == [], "throttle نگرفت"
    assert qp.scan(now=NOW + MINUTES14) == [], "throttle زودتر باز شد"
    got = _by(qp.scan(now=NOW + 16 * 60), "lead-missing-info")
    assert len(got) == 1, got
    # force پنجره را دور می‌زند (بازرسیِ دستی)، ولی dedup را نه
    _fresh()
    _plant_blocked("mining", "چک کردن ریگ", "کدام استخر؟", age_s=25 * H)
    assert len(_by(qp.scan(now=NOW), "blocked-leg")) == 1
    assert qp.scan(now=NOW + 60, deps={"force": True}) == [], \
        "force نباید dedup را بشکند"


MINUTES14 = 14 * 60


def t_the_next_iso_week_frees_the_same_key_again():
    _fresh()
    _plant_blocked("mining", "چک کردن ریگ", "کدام استخر؟", age_s=25 * H)
    k1 = _by(qp.scan(now=NOW), "blocked-leg")[0]["key"]
    assert _by(qp.scan(now=NOW + H), "blocked-leg") == []
    again = _by(qp.scan(now=NEXT_WEEK), "blocked-leg")
    assert len(again) == 1 and again[0]["key"] == k1, again
    assert len(json.loads(qb._path().read_text("utf-8"))["queue"]) == 2


def t_a_failed_dedup_write_blocks_the_submit_loudly():
    """fail-closed: دفتر ذخیره نشد ⇒ هیچ سؤالی ثبت نمی‌شود و خطا **بلند**
    برمی‌گردد (سکوت ممنوع)."""
    _fresh()
    _plant_blocked("mining", "چک کردن ریگ", "کدام استخر؟", age_s=25 * H)
    orig = qp._save_ledger
    qp._save_ledger = lambda d: False
    try:
        items = qp.scan(now=NOW)
    finally:
        qp._save_ledger = orig
    errs = _errors(items)
    assert errs and "dedup" in errs[0]["error"], items
    assert not qb._path().exists() or not json.loads(
        qb._path().read_text("utf-8"))["queue"], "با دفترِ خراب ثبت کرد"


# ── مسیرِ بودجه ────────────────────────────────────────────────────────────
def t_production_never_escapes_the_budget_path():
    """تولید از همان `submit` رد می‌شود: بعد از سوختنِ سقفِ هفته، سؤالِ نو
    صادقانه `deferred` می‌گیرد — نه تحویل، نه دورزدنِ سقف."""
    _fresh()
    for i in range(qb.WEEK_CAP):
        r = qb.submit(f"پرشدنِ بودجه {i}", now=NOW - 100)
        assert qb.mark_asked(r["item"]["id"], now=NOW - 100) is not None
    assert qb.remaining(NOW) == 0
    _plant_blocked("mining", "چک کردن ریگ", "کدام استخر؟", age_s=25 * H)
    got = _by(qp.scan(now=NOW), "blocked-leg")
    assert len(got) == 1 and got[0]["status"] == "deferred", got
    assert qb.pending(NOW) is None, "سؤالِ تولیدشده سقف را دور زد"
    assert qb.used(NOW) == qb.WEEK_CAP


def t_producers_stop_at_the_weekly_production_ceiling():
    _fresh()
    ledger = qp._load_ledger(NOW)
    ledger["keys"] = {f"synthetic:{i}": {"ts": NOW, "producer": "x",
                                         "qid": None}
                      for i in range(qb.WEEK_CAP)}
    assert qp._save_ledger(ledger)
    _plant_blocked("mining", "چک کردن ریگ", "کدام استخر؟", age_s=25 * H)
    assert qp.scan(now=NOW) == [], "از سقفِ تولیدِ هفته گذشت"


def t_one_question_per_producer_per_run():
    _fresh()
    _plant_blocked("mining", "ریگ ۱", "کدام استخر؟", age_s=40 * H)
    _plant_blocked("crypto", "پوزیشن", "چقدر ریسک؟", age_s=30 * H)
    _plant_blocked("ziman", "قاب", "کدام سایز؟", age_s=26 * H)
    got = _by(qp.scan(now=NOW), "blocked-leg")
    assert len(got) == 1, got
    assert "mining" in got[0]["item"]["q"], "قدیمی‌ترین مانع اول نیامد"


def t_all_five_producers_can_fire_in_one_run():
    _fresh()
    _plant_blocked("mining", "ریگ ۱", "کدام استخر؟", age_s=40 * H)
    _plant_stuck("LEAD-xyz", "متراژ چقدر است؟", age_s=20 * H)
    _plant_flags(OCTOPUS_TG_REMINDERS="0")
    _plant_money()
    _plant_goals()
    _plant_outcomes([{"ts": datetime.fromtimestamp(NOW - 2 * 86400).isoformat(),
                      "id": "up-1", "serves_goal": GOAL_A, "baseline": {}}])
    items = qp.scan(now=NOW)
    assert _errors(items) == [], items
    assert {it["producer"] for it in items} == {p for p, _ in qp.PRODUCERS}, \
        [it["producer"] for it in items]
    for it in items:                     # هر سؤال هدف و شاهد دارد — بی‌استثنا
        assert it["item"]["goal"].strip(), it
        assert it["item"]["context"].strip(), it


# ── متنِ سؤال: نقلِ صادق و HTML ِ سالم ─────────────────────────────────────
def t_a_truncated_quote_says_that_it_is_truncated():
    """اجرای واقعی روی درختِ زنده نشان داد نقلِ خطِ GOALS وسطِ جمله بریده
    می‌شد و **کامل** به نظر می‌رسید — نقلِ بریدهٔ بی‌علامت، اختراعِ حقیقت در
    لباسِ نقل‌قول است."""
    _fresh()
    long_q = "چرا " + "طولانی " * 60 + "؟"
    _plant_stuck("LEAD-long", long_q, age_s=20 * H)
    item = _by(qp.scan(now=NOW), "lead-missing-info")[0]["item"]
    assert item["q"].rstrip().endswith("…"), item["q"][-40:]
    assert item["context"].count("…") >= 1, item["context"]
    # و نقلِ کوتاه هرگز علامتِ الکی نمی‌گیرد
    _fresh()
    _plant_stuck("LEAD-short", "متراژ؟", age_s=20 * H)
    item = _by(qp.scan(now=NOW), "lead-missing-info")[0]["item"]
    assert "…" not in item["q"], item["q"]


def t_vault_text_with_html_chars_survives_the_html_render():
    """متنِ artifact از vault می‌آید و مرکز با parse_mode=HTML می‌فرستد؛
    یک `<` ِ بی‌گناه کلِ پیام را بی‌صدا حذف می‌کرد. escape فقط روی تکهٔ
    داده — تگِ `<b>` ِ خودِ قالب باید سالم بماند."""
    _fresh()
    _plant_stuck("LEAD-html", "متراژ < ۵۰ متر است یا > ۵۰؟ (A&B)",
                 age_s=20 * H)
    item = _by(qp.scan(now=NOW), "lead-missing-info")[0]["item"]
    txt = qb.question_text(item)
    assert "&lt;" in txt and "&gt;" in txt and "&amp;" in txt, txt
    assert "متراژ < " not in txt, txt
    assert txt.startswith("❓ <b>") and "</b>" in txt, txt


# ── مرزها ──────────────────────────────────────────────────────────────────
def t_the_module_never_sends_and_touches_no_network():
    import ast
    tree = ast.parse(Path(qp.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for bad in ("send", "send_text", "post", "sendMessage", "urlopen",
                "mark_asked"):
        assert bad not in called, f"question_producers مرز شکست: {bad}"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(qp._ledger_path()).lower().startswith(live), \
        qp._ledger_path()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_question_producers: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
