#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_phase0_receipt_rig.py — رِیگِ رسید باید **خودش** اثبات‌پذیر باشد.

فاز ۰ ِ پلنِ حلقهٔ دوتایی (۲۰۲۶-۰۸-۰۴). قاعدهٔ حاکم بر آن پلن این است:

    هیچ فازی سبز نمی‌شود مگر تکِ مالک رسیدش را در لاگ بگذارد.

ولی آن قاعده روی یک ابزار سوار است — و ابزارِ اندازه‌گیریِ نیازموده، بدتر از
نبودِ ابزار است: عددِ غلط می‌دهد و کسی شک نمی‌کند. پس این فایل خودِ رِیگ را
می‌سنجد، **رفتاری** و از مسیرِ تولیدی (`run_once` ِ واقعی و
`tg_send_log.record` ِ واقعی)، نه از روی متنِ کد.

سه چیزی که این‌جا قفل می‌شود
─────────────────────────────
۱. **مهرِ همبستگی.** تا امروز `inbound-log` (ISO ِ محلی) و `tg-send-log`
   (اپاکِ اعشاری) هیچ کلیدِ مشترکی نداشتند، پس «آن پیامِ من جواب گرفت؟» یک
   حدسِ زمانی بود. حالا پاسخ همان `update_id` را حمل می‌کند.

۲. **سکوت‌های نام‌دار.** پروبِ زندهٔ همین فاز دو چیز را تصحیح کرد:
   · فرمانِ ناشناخته **ساکت نیست** — پلِ ارگانیسم جواب می‌دهد (فرضِ اولیه‌ام
     غلط بود و پروب گرفتش).
   · ولی فرمانِ **گیت‌شده با فلگِ خاموش** واقعاً ساکت است، و بدتر از آن:
     پلی که `sent=False` برمی‌گرداند از بالادست «رسیدگی شد» به‌نظر می‌رسد.
     سکوتی که **موفق ظاهر می‌شود** بدترین نوع است.

۳. **صداقتِ ابزار.** `tg_receipts` حق ندارد دربارهٔ ورودی‌های قبل از زنده‌شدنِ
   رِیگ حکمِ ❌ بدهد (نبودِ داده حکم نیست)، و باید فرضِ منطقهٔ زمانیِ خودش را
   **بسنجد** نه اینکه به آن اعتماد کند — یک ناهم‌خوانیِ UTC/محلی یک بار سقفِ
   پول را ده ساعت در روز کور کرد.
"""
import ast
import importlib.util
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402  ← **اول**؛ هر import ِ زودتر ایزوله را می‌شکند

ENV = harness.setup("phase0-rig")

CENTER = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"
CSRC = CENTER.read_text("utf-8", errors="replace")
CTREE = ast.parse(CSRC)


def _fn(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _center():
    """‏Center ِ واقعی با کلاینتِ ساختگی — همان الگوی تست‌های خواهر."""
    spec = importlib.util.spec_from_file_location("cp_p0", CENTER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    c = m.Center.__new__(m.Center)

    class _Client:
        owner_chat_id = 555

        def __init__(self):
            self.sent = []

        def send(self, *a, **k):
            self.sent.append((a, k))
            return 1

    c._client = _Client()
    c.stopped = lambda: False
    c._wired = lambda: True
    c._poll_fails = 0
    state = Path(m.opslib.STATE_DIR)
    assert str(harness.REAL_VAULT).lower() not in str(state).lower(), (
        "‼️ state ِ تست داخلِ درختِ زنده افتاد", str(state))
    return m, c, state


def _rows(p: Path):
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _drive(c, updates):
    c._client.poll_updates = lambda offset=0, timeout_s=0: updates
    return c.run_once()


# ── ۱. لنگرها ────────────────────────────────────────────────────────────────
def t_a_every_anchor_exists():
    """گاردِ «اسکنر کور شده» — نمادِ جابه‌جاشده نباید سبزِ کاذب بدهد."""
    assert _fn(CTREE, "_bind_send_correlation") is not None, \
        "‏Center درِ مهرِ همبستگی را ندارد"
    assert _fn(CTREE, "_log_disposition") is not None
    import tg_send_log as t
    for name in ("bind_update", "clear_update", "current_update"):
        assert callable(getattr(t, name, None)), (name, "در tg_send_log نیست")
    import tg_receipts as r
    assert callable(getattr(r, "collect", None))


def t_b_the_binding_wraps_dispatch_and_is_released_in_finally():
    """⚠️ `finally` باربر است، نه آرایشی.

    بدونِ آن، یک استثنا برچسب را روی نخ جا می‌گذارد و **ارسالِ بعدی** — که
    مالِ updateِ دیگری است — به updateِ مرده چسبانده می‌شود. یعنی دقیقاً یک
    رسیدِ جعلی، همان چیزی که کلِ این فاز می‌خواهد ریشه‌کن کند.

    AST، نه زیررشته: کامنت‌های فارسیِ همین بلوک هر assert ِ متنی را می‌کشند.
    """
    ro = _fn(CTREE, "run_once")
    assert ro is not None
    tries = [n for n in ast.walk(ro) if isinstance(n, ast.Try)]

    def _calls(nodes):
        return {getattr(x.func, "attr", getattr(x.func, "id", ""))
                for n in nodes for x in ast.walk(n) if isinstance(x, ast.Call)}

    guarded = [t for t in tries
               if "handle_update" in _calls(t.body)
               and "_bind_send_correlation" in _calls(t.finalbody)]
    assert guarded, (
        "‏handle_update داخلِ try ای نیست که در `finally` برچسب را آزاد کند — "
        "یک استثنا برچسب را به updateِ بعدی نشت می‌دهد")

    # و بستن باید **قبل** از dispatch باشد، وگرنه پاسخ‌های زودهنگام بی‌برچسب‌اند
    seg = ast.get_source_segment(CSRC, ro) or ""
    i_bind = seg.find("_bind_send_correlation")
    i_disp = seg.find("self.handle_update")
    assert 0 <= i_bind < i_disp, "برچسب بعد از dispatch بسته می‌شود"


# ── ۲. مهرِ همبستگی، رفتاری و از مسیرِ تولیدی ────────────────────────────────
def t_c_a_bound_send_carries_the_update_id():
    """`tg_send_log.record` ِ **واقعی** — نه یک fake که تابعِ واقعی را دور بزند."""
    import os
    import tg_send_log as t
    os.environ["OCTOPUS_TG_SEND_LOG"] = "1"
    p = t._path()
    assert str(harness.REAL_VAULT).lower() not in str(p).lower(), ("‼️ زنده", str(p))
    before = len(_rows(p))

    t.bind_update(4242)
    t.record(chat_id=1, text="پاسخ به مالک", stream="probe")
    t.clear_update()
    t.record(chat_id=1, text="نبضِ خودجوش", stream="beat")

    rows = _rows(p)[before:]
    assert len(rows) == 2, rows
    assert rows[0].get("update_id") == 4242, (
        "پاسخ مهرِ همبستگی ندارد ⇒ «جواب گرفت؟» دوباره یک حدسِ زمانی است", rows[0])
    assert "update_id" not in rows[1], (
        "ارسالِ خودجوش (beat/تایمر) نباید به هیچ ورودی نسبت داده شود", rows[1])


def t_d_an_invalid_id_clears_rather_than_keeping_the_previous_one():
    """⚠️ حالتِ لبه‌ای که برچسبِ دروغ می‌سازد: اگر `bind_update` روی ورودیِ
    نامعتبر **برچسبِ قبلی را نگه دارد**، پاسخِ این update به updateِ قبلی
    چسبانده می‌شود. برچسبِ دروغ از نبودِ برچسب بدتر است."""
    import os
    import tg_send_log as t
    os.environ["OCTOPUS_TG_SEND_LOG"] = "1"
    p = t._path()
    before = len(_rows(p))
    t.bind_update(111)
    t.bind_update(None)             # ← نامعتبر
    t.record(chat_id=1, text="بعد از شناسهٔ نامعتبر", stream="probe")
    rows = _rows(p)[before:]
    assert rows and "update_id" not in rows[0], (
        "شناسهٔ نامعتبر برچسبِ قبلی را نگه داشت ⇒ رسیدِ جعلی", rows[0])


# ── ۳. سکوت‌های نام‌دار، از مسیرِ واقعیِ run_once ────────────────────────────
def t_e_a_flag_gated_command_is_explained_not_silent():
    """`/panel` با فلگِ خاموش: هیچ جوابی نمی‌رود (رفتار عمدی، بی‌تغییر) — ولی
    از این پس **قابلِ فهم** است. درسِ «مسیریابی به فلگِ خاموش»: مسیرِ درست به
    فرمانِ خاموش، از بیرون عیناً شبیهِ خرابی است."""
    m, c, state = _center()
    _drive(c, [{"update_id": 9101,
                "message": {"text": "/panel", "chat": {"id": 555, "type": "private"},
                            "from": {"id": 555}}}])
    rows = _rows(state / "telegram" / "inbound-log.jsonl")
    disp = [r for r in rows if r.get("kind") == "disposition"]
    assert disp, "فرمانِ گیت‌شده هنوز بی‌دلیل ساکت است"
    assert disp[-1]["outcome"] == "gated-command", disp[-1]
    assert disp[-1]["reason"], "دلیل باید نامِ فلگ را ببرد وگرنه مالک نمی‌داند چه کند"


def t_f_arrival_and_disposition_share_one_update_id():
    """قلبِ رِیگ. دو ردیفِ درست که به‌هم وصل نمی‌شوند، عملاً هیچ‌اند."""
    m, c, state = _center()
    _drive(c, [{"update_id": 9102,
                "message": {"text": "/panel", "chat": {"id": 555, "type": "private"},
                            "from": {"id": 555}}}])
    rows = [r for r in _rows(state / "telegram" / "inbound-log.jsonl")
            if r.get("update_id") == 9102]
    kinds = {r.get("kind") for r in rows}
    assert "disposition" in kinds and len(rows) >= 2, (
        "ورود و تعیین‌تکلیف زیرِ یک update_id ننشستند ⇒ جوین‌ناپذیر", rows)


def t_g_a_bridge_that_reports_an_unsent_reply_is_recorded():
    """⚠️ سکوتِ **خودنمایان‌گر**: پل همیشه dict برمی‌گرداند، حتی وقتی
    `send` ترکیده و `mid=None` شده. آن dict از بالادست «موفق» به‌نظر می‌رسد،
    پس هیچ‌کس دنبالِ دلیل نمی‌گردد — ولی مالک هیچ ندیده."""
    m, c, state = _center()
    c._bridge_to_organism = lambda text, chat_id, msg: {
        "kind": "bridged", "cmd": text.split()[0], "sent": False}
    _drive(c, [{"update_id": 9103,
                "message": {"text": "/zzznotacommand",
                            "chat": {"id": 555, "type": "private"},
                            "from": {"id": 555}}}])
    disp = [r for r in _rows(state / "telegram" / "inbound-log.jsonl")
            if r.get("kind") == "disposition" and r.get("update_id") == 9103]
    assert disp, "پلی که چیزی نفرستاد، بی‌رد ماند — سکوتی که موفق ظاهر می‌شود"
    assert disp[-1]["outcome"] == "bridge-send-failed", disp[-1]


def t_h_the_disposition_row_stores_no_message_text():
    """§۱۰. رسید باید بگوید «چرا»، نه اینکه بایگانیِ دومِ مکالمه بسازد.

    ⚠️ نسخهٔ اولِ این تست **بی‌دندان** بود و جهشِ نشتی از کنارش رد شد. علت:
    فقط مسیرِ `u=None` را می‌راند (فرمانِ گیت‌شده)، و آن‌جا `msg` خالی است پس
    هیچ متنی برای نشت‌کردن وجود ندارد — گاردی که ساختاراً نمی‌توانست قرمز
    شود. مسیرِ **واقعاً خطرناک** آن است که `u` ِ کامل را پاس می‌دهد
    (`not-owner`، خطِ ۲۴۵۸)، چون آن‌جا `msg.get("text")` پیامِ زنده است.
    حالا هر دو شکل رانده می‌شوند."""
    m, c, state = _center()
    secret_ish = "خصوصی-۹۹۷۷-متنِ-پیام"
    _drive(c, [
        # (الف) مسیرِ u=None — فرمانِ گیت‌شده
        {"update_id": 9104,
         "message": {"text": f"/panel {secret_ish}",
                     "chat": {"id": 555, "type": "private"},
                     "from": {"id": 555}}},
        # (ب) مسیرِ u ِ کامل — غیرمالک؛ این‌جاست که متن در دسترسِ نشت است
        {"update_id": 9105,
         "message": {"text": f"سلام {secret_ish}",
                     "chat": {"id": 777, "type": "private"},
                     "from": {"id": 999}}},
    ])
    rows = _rows(state / "telegram" / "inbound-log.jsonl")
    disp = [r for r in rows if r.get("kind") == "disposition"]
    outs = {r.get("outcome") for r in disp}
    assert "not-owner" in outs, (
        "مسیرِ غیرمالک رانده نشد ⇒ این گارد دوباره بی‌دندان است", outs)
    raw = (state / "telegram" / "inbound-log.jsonl").read_text("utf-8")
    assert secret_ish not in raw, "متنِ پیام در لاگ نشت کرد — نشتیِ PII"


# ── ۴. صداقتِ خودِ ابزار ─────────────────────────────────────────────────────
def _iso(h, mnt, s=0):
    return f"2026-08-04T{h:02d}:{mnt:02d}:{s:02d}"


def _epoch(h, mnt, s=0):
    import datetime
    return datetime.datetime.fromisoformat(_iso(h, mnt, s)).timestamp()


def t_i_the_three_verdicts_are_distinguished():
    import tg_receipts as r
    inbound = [
        {"ts": _iso(10, 0), "update_id": 1, "kind": "text", "cmd": "/now"},
        {"ts": _iso(10, 1), "update_id": 2, "kind": "text", "cmd": "/panel"},
        {"ts": _iso(10, 2), "update_id": 2, "kind": "disposition",
         "outcome": "gated-command", "reason": "فلگ خاموش"},
        {"ts": _iso(10, 3), "update_id": 3, "kind": "text", "cmd": "/ghost"},
    ]
    sends = [{"ts": _epoch(10, 0, 1), "update_id": 1, "state": "sent"}]
    d = r.collect(inbound=inbound, sends=sends)
    v = {row["update_id"]: row["verdict"] for row in d["rows"]}
    assert v[1] == "ANSWERED", v
    assert v[2] == "EXPLAINED", v
    assert v[3] == "SILENT", (
        "ورودیِ بی‌جواب و بی‌دلیل باید ❌ شود — این تنها شکستِ واقعی است", v)
    assert d["rows"][0]["latency_s"] == 1.0, d["rows"][0]


def t_j_pre_rig_arrivals_are_never_accused_of_silence():
    """⚠️ «نبودِ داده حکم نیست». ورودی‌های پیش از زنده‌شدنِ مهرِ همبستگی
    ساختاراً نمی‌توانستند برچسب بگیرند؛ نامیدنشان SILENT یک اتهامِ ساختگی
    است، نه یک یافته."""
    import tg_receipts as r
    inbound = [{"ts": _iso(9, 0), "update_id": 77, "kind": "text", "cmd": "/old"},
               {"ts": _iso(11, 0), "update_id": 88, "kind": "text", "cmd": "/new"}]
    sends = [{"ts": _epoch(10, 0), "update_id": 55, "state": "sent"}]
    d = r.collect(inbound=inbound, sends=sends)
    v = {row["update_id"]: row["verdict"] for row in d["rows"]}
    assert v[77] == "PRE-RIG", ("ورودیِ قبل از رِیگ متهم شد", v)
    assert v[88] == "SILENT", ("ورودیِ بعد از رِیگ باید واقعاً سنجیده شود", v)

    # و وقتی رِیگ اصلاً هرگز زنده نبوده، هیچ ❌ ای صادر نمی‌شود
    d2 = r.collect(inbound=inbound, sends=[])
    assert d2["rig_live"] is False
    assert all(row["verdict"] == "PRE-RIG" for row in d2["rows"]), d2["rows"]


def t_k_the_tool_checks_its_own_timezone_assumption():
    """⚠️ یک ناهم‌خوانیِ UTC/محلی یک بار سقفِ پول را ده ساعت در روز کور کرد و
    هیچ‌کس نفهمید. پس این ابزار فرضش را **می‌سنجد**: اگر تفسیرِ ساعت غلط
    باشد، باید بگوید — نه اینکه بی‌صدا تأخیرِ بی‌معنی گزارش کند."""
    import tg_receipts as r
    inbound = [{"ts": _iso(10, 0), "update_id": 1, "kind": "text", "cmd": "/now"}]
    ok = r.collect(inbound=inbound,
                   sends=[{"ts": _epoch(10, 0, 2), "update_id": 1, "state": "sent"}])
    assert ok["tz_sane"] is True, ok

    skewed = r.collect(inbound=inbound,
                       sends=[{"ts": _epoch(10, 0) + 36000, "update_id": 1,
                               "state": "sent"}])
    assert skewed["tz_sane"] is False, (
        "‏۱۰ ساعت اختلاف را «سالم» خواند ⇒ خودسنجی کور است", skewed)
    assert "⚠️" in r.report(skewed), "گزارش دربارهٔ فرضِ مشکوکِ خودش ساکت است"


def t_l_a_withheld_reply_is_not_counted_as_silence():
    """پیامی که سیاست نگهش داشت **گم نشده** — و اگر ❌ شمرده شود، رِیگ گرگ‌گرگ
    می‌کند و خاموش می‌شود (درسِ ثبت‌شده)."""
    import tg_receipts as r
    d = r.collect(
        inbound=[{"ts": _iso(10, 0), "update_id": 5, "kind": "text", "cmd": "/x"}],
        sends=[{"ts": _epoch(10, 0, 1), "update_id": 5, "state": "held"}])
    assert d["rows"][0]["verdict"] == "HELD", d["rows"][0]
    assert d["counts"].get("SILENT", 0) == 0, d["counts"]


# ── ۵. باتِ درونی — جایی که ترافیکِ واقعیِ DM ِ مالک می‌گذرد ─────────────────
def t_m_the_inner_bot_binds_too_or_the_rig_lies():
    """⚠️ اگر فقط مرکز مهر بزند، هر پیامی که باتِ **درونی** درست جواب داده در
    گزارش ❌ SILENT دیده می‌شود — ابزاری که برای اثباتِ «دیده شدی» ساخته شد،
    مدرکِ جعلیِ «دیده نشدی» تولید می‌کند. و گاردی که گرگ‌گرگ کند خاموش
    می‌شود. همان اشتباهِ «چشم روی باتی که حرف نمی‌زند»، این‌بار در خروجی.

    رفتاری و دقیق: برچسب را در **لحظهٔ ارسال** می‌خوانیم (از داخلِ transport ِ
    تزریق‌شده)، نه بعدش."""
    import os
    import tempfile
    import approval_channel as ac
    import tg_send_log as t
    os.environ["OCTOPUS_TG_SEND_LOG"] = "1"

    d = Path(tempfile.mkdtemp(prefix="p0-inner-"))
    assert str(harness.REAL_VAULT).lower() not in str(d).lower()

    # ⚠️ `/queue` عمدی است، نه دلبخواه: زیرِ همین فیکسچر، `handle_command` برای
    # `/help`، `/id`، فرمانِ ناشناخته و متنِ سادهٔ فارسی **None** برمی‌گرداند —
    # یعنی صفر ارسال، یعنی تستی که هیچ نمی‌سنجد. (اینکه آن None ها آرتیفکتِ
    # توکنِ ساختگی‌اند یا سکوتِ واقعیِ تولیدی، با تکِ زندهٔ مالک روشن می‌شود؛
    # این‌جا فقط لنگرِ یک ارسالِ **واقعاً رخ‌داده** لازم است.)
    seen = []
    upd = {"ok": True, "result": [{
        "update_id": 9201,
        "message": {"chat": {"id": 4242}, "from": {"id": 4242},
                    "text": "/queue"}}]}

    def _post(url, body, timeout=10.0):
        seen.append(t.current_update())     # ← برچسب **حینِ** ارسال
        return {"ok": True, "result": {"message_id": 1}}

    ch = ac.TelegramApprovalChannel(
        token="test-token", owner_chat_id=4242,
        http_get=lambda url, timeout: upd,
        http_post=_post, state_dir=d / "state")

    assert callable(getattr(ch, "_bind_send_correlation", None)), \
        "باتِ درونی درِ مهرِ همبستگی را ندارد"
    ch.poll_once()

    assert seen, "هیچ ارسالی رخ نداد ⇒ این تست چیزی را نمی‌سنجد (گاردِ بی‌دندان)"
    assert seen[0] == 9201, (
        "پاسخِ باتِ درونی بی‌برچسب رفت ⇒ tg_receipts آن را ❌ SILENT می‌خواند", seen)
    assert t.current_update() is None, (
        "برچسب بعد از پایانِ دور آزاد نشد — ارسالِ خودجوشِ بعدی رسیدِ جعلی می‌گیرد")


def t_n_a_stale_label_from_a_crashed_round_is_cleared_on_entry():
    """اگر فراخوانِ قبلی وسطِ حلقه ترکیده باشد، برچسبش روی نخ می‌ماند. بدونِ
    پاک‌سازیِ ورودی، **اولین** ارسالِ دورِ بعد به updateِ مرده نسبت داده
    می‌شود — یک رسیدِ جعلی که هیچ‌کس به آن شک نمی‌کند."""
    import tempfile
    import approval_channel as ac
    import tg_send_log as t

    d = Path(tempfile.mkdtemp(prefix="p0-stale-"))
    ch = ac.TelegramApprovalChannel(
        token="test-token", owner_chat_id=4242,
        http_get=lambda url, timeout: {"ok": True, "result": []},
        http_post=lambda url, body, timeout=10.0: {"ok": True},
        state_dir=d / "state")

    t.bind_update(111111)                  # ← بازماندهٔ دورِ ترکیده
    ch.poll_once()                         # دورِ خالی، صفر update
    assert t.current_update() is None, (
        "برچسبِ جامانده پاک نشد ⇒ اولین پاسخِ بعدی به updateِ مرده می‌چسبد")

    # ⚠️ و حالتی که **فقط** پاک‌سازیِ ورودی می‌تواند بگیرد: خروجِ زودهنگام،
    # قبل از رسیدن به آزادسازیِ پس‌از‌حلقه. نسخهٔ اولِ این تست این را نداشت و
    # جهشِ متناظر زنده ماند — چون دورِ خالی هم به آزادسازیِ پس‌از‌حلقه می‌رسید
    # و هر دو مکانیزم یک نتیجه می‌دادند. یک assert که دو علت را از هم جدا
    # نکند، هیچ‌کدام را نمی‌سنجد.
    def _boom(url, timeout):
        raise OSError("شبکه قطع")

    ch2 = ac.TelegramApprovalChannel(
        token="test-token", owner_chat_id=4242, http_get=_boom,
        http_post=lambda url, body, timeout=10.0: {"ok": True},
        state_dir=d / "state2")
    t.bind_update(222222)
    ch2.poll_once()                        # خطای شبکه ⇒ return زودهنگام
    assert t.current_update() is None, (
        "خروجِ زودهنگام برچسب را جا گذاشت — آزادسازیِ پس‌از‌حلقه اصلاً اجرا "
        "نمی‌شود، پس فقط پاک‌سازیِ **ورودی** این را می‌بندد")


# ── ۶. دو سکوتی که ممیزیِ ۱۱-ایجنته تأیید کرد ───────────────────────────────
def t_o_a_message_with_no_text_body_is_explained():
    """استیکر/لوکیشن/مخاطب/نظرسنجی… می‌رسند و بی‌صدا می‌میرند. عکس و ویسِ DM
    این‌جا **نمی‌رسند** (قلابِ capture بالاتر جوابشان را می‌دهد و برمی‌گردد)،
    پس این ردیف مثبتِ کاذب نمی‌سازد."""
    m, c, state = _center()
    _drive(c, [{"update_id": 9301,
                "message": {"sticker": {"file_id": "x"},
                            "chat": {"id": 555, "type": "private"},
                            "from": {"id": 555}}}])
    disp = [r for r in _rows(state / "telegram" / "inbound-log.jsonl")
            if r.get("kind") == "disposition" and r.get("update_id") == 9301]
    assert disp, "پیامِ بی‌متن هنوز بی‌دلیل ساکت است"
    assert disp[-1]["outcome"] == "no-text-body", disp[-1]
    assert disp[-1]["detail"] == "sticker", (
        "نوعِ پیام ثبت نشد ⇒ نمی‌شود فهمید کدام دسته گم می‌شود", disp[-1])

    # و شاخهٔ fallback: نوعی که در فهرست نیست باید «other» شود، نه خالی.
    # (بدونِ این مورد، جهشِ متناظر زنده می‌ماند — موردِ استیکر هرگز به fallback
    # نمی‌رسد، پس آن شاخه **دیده‌نشده** بود.)
    _drive(c, [{"update_id": 9303,
                "message": {"game": {"title": "x"},
                            "chat": {"id": 555, "type": "private"},
                            "from": {"id": 555}}}])
    d2 = [r for r in _rows(state / "telegram" / "inbound-log.jsonl")
          if r.get("kind") == "disposition" and r.get("update_id") == 9303]
    assert d2 and d2[-1]["detail"] == "other", (
        "نوعِ ناشناخته دستهٔ fallback نگرفت", d2)


def t_p_the_free_text_terminus_no_longer_swallows_in_silence():
    """⚠️ بدترینِ پنج سکوت: پایانهٔ **همهٔ** متنِ آزادِ فارسیِ مالک. چون استثنا
    این‌جا گرفته می‌شود، هرگز به `run_once` و نامهٔ مرده نمی‌رسد — نه جواب، نه
    نامهٔ مرده، نه هشدار. تنها تابعی که کارش «هرگز ساکت نباش» است."""
    m, c, state = _center()
    c._chat_room = lambda msg, text: None      # مسیر را به پایانه هدایت کن

    def _boom(*a, **k):
        raise RuntimeError("متنِ محرمانهٔ مالک نباید این‌جا نشت کند")

    c._client.send = _boom
    _drive(c, [{"update_id": 9302,
                "message": {"text": "سلامِ ساده",
                            "chat": {"id": 555, "type": "private"},
                            "from": {"id": 555}}}])
    raw = (state / "telegram" / "inbound-log.jsonl").read_text("utf-8")
    disp = [r for r in _rows(state / "telegram" / "inbound-log.jsonl")
            if r.get("kind") == "disposition" and r.get("update_id") == 9302]
    assert disp, "پایانهٔ متنِ آزاد هنوز بی‌صدا می‌بلعد"
    assert disp[-1]["outcome"] == "ask-error", disp[-1]
    assert disp[-1]["detail"] == "RuntimeError", (
        "نوعِ استثنا ثبت نشد", disp[-1])
    # §۱۰ — پیامِ استثنا می‌تواند حرفِ خودِ مالک را داخلش داشته باشد
    assert "محرمانه" not in raw, "متنِ استثنا در لاگ نشت کرد — نشتیِ PII"


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_phase0_receipt_rig: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
