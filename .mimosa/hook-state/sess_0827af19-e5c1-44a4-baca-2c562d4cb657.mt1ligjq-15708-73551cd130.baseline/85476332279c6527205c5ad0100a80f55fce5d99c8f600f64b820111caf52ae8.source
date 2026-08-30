#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_ops_buttons — دکمه‌های `/ops` در خودِ چت (لِینِ chat-actions).

مالک حکم داد این دکمه‌ها **می‌توانند جهش بدهند**، یعنی وزنِ کامل دارند. پس
این فایل پنج چیز را قفل می‌کند، هر کدام با یک تپِ واقعی روی `Center` ِ واقعی
و `FakeClient` (صفر شبکه):

  ۱. **فلگ خاموش = امروز، بایت‌به‌بایت.** نه کیبوردی می‌آید، نه `ops:` به
     روتر می‌رسد، نه ریپلایِ نشان‌دار دزدیده می‌شود. سنجه سخت‌گیر است:
     حتی kwargِ `keyboard` هم نباید به `send` پاس شود.
  ۲. **غیرمالک هیچ.** نه رکورد، نه پیام، نه answer، نه رسید — یک بایت هم لو
     نمی‌رود. (سکوتِ عمدی؛ همان قراردادِ test_tg_callback_answer.)
  ۳. **دبل‌تپ = یک رکورد.** با `IdempotencyStore` ِ خودِ Ops Studio، نه یک
     کلیدِ خانگی.
  ۴. **هر مسیر answer می‌گیرد** — شاملِ رد، ناشناخته و شناسهٔ خراب. دکمه‌ای
     که تا ابد می‌چرخد دکمهٔ مرده است و این ریپو از همین سوخته.
  ۵. **رد هم رسید دارد.** موتورِ اکشن برای DENIED/BLOCKED پیش از
     `audit.append` برمی‌گردد، پس اگر مرکز خودش ننویسد، «هیچ اتفاقی نیفتاد»
     و «رد شد» یک شکل می‌شوند.

انزوا: `OCTOPUS_OPS_RUNTIME_DIR` کلِ حالتِ Ops Studio (دیتابیس + idempotency +
رسیدها) را به temp ِ harness می‌برد. مسیرِ `/ops` هم با یک stub ِ
`agi2027_control.integration` بسته می‌شود تا ControlPlane ِ واقعی داخلِ
worktree فایل نسازد؛ خودِ سیمِ واقعی جداگانه سنجیده می‌شود (t_n).
"""
import json
import shutil
import sqlite3
import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402

ENV = harness.setup("tg-ops-buttons")     # قبل از هر importی که state می‌نویسد

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import os        # noqa: E402
import opslib    # noqa: E402
import center    # noqa: E402

OWNER = 777
STRANGER = 666
GROUP = -1004475788460
FLAG = center.OPS_BUTTONS_FLAG            # OCTOPUS_TG_OPS_BUTTONS
RUNTIME = Path(ENV["root"] if isinstance(ENV, dict) and "root" in ENV
               else opslib.STATE_DIR) / "ops-runtime"
CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"


# ── محیط ───────────────────────────────────────────────────────────────────
class FakeClient:
    """`send` عمداً `**kw` می‌گیرد: تنها راهِ اثباتِ «هیچ kwargِ اضافه‌ای پاس
    نشد» همین است — امضای واقعی `keyboard=None` پیش‌فرض دارد و غیبتِ آرگومان
    را از `None` قابلِ تفکیک نمی‌کند."""

    def __init__(self, owner_id=OWNER):
        self.owner_id = owner_id
        self.owner_chat_id = owner_id
        self.center_chat_id = GROUP
        self.calls: list = []
        self._mid = 500

    def wired(self):
        return True

    def send(self, text, **kw):
        self.calls.append(("send", {"text": text, "kw": dict(kw)}))
        self._mid += 1
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id}))
        return True

    def pin_message(self, message_id, chat_id=None):
        return True

    def create_topic(self, name, chat_id=None):
        return 50

    def set_commands(self, commands, scope=None):
        return True

    def delete_commands(self, scope=None):
        return True

    def poll_updates(self, offset=0, timeout_s=25):
        return []

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"id": callback_id, "text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def _reset(flag_on: bool = False, url: str = ""):
    """هر سنجه از صفر: دیتابیس، رسیدها، config، فلگ‌ها."""
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)
    shutil.rmtree(RUNTIME, ignore_errors=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_OPS_RUNTIME_DIR"] = str(RUNTIME)
    os.environ.pop("OCTOPUS_OPS_DB_PATH", None)
    os.environ.pop("OCTOPUS_OPS_AUDIT_PATH", None)
    os.environ.pop("OCTOPUS_OPS_IDEMPOTENCY_PATH", None)
    if flag_on:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)
    if url:
        os.environ["OCTOPUS_MINIAPP_URL"] = url
    else:
        os.environ.pop("OCTOPUS_MINIAPP_URL", None)
    os.environ.pop("OCTOPUS_TG_MINIAPP", None)
    CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CFG_PATH.write_text(json.dumps({"chat_id": GROUP,
                                    "topics": {"lead": 22, "system": 28}},
                                   ensure_ascii=False), "utf-8")
    fc = FakeClient()
    return fc, center.Center(client=fc, clock=lambda: 1000.0, render_mod=None)


class _ControlStub:
    """`/ops` را از ControlPlane ِ واقعی جدا می‌کند (وگرنه تست داخلِ
    `_ops/agi2027_runtime` ِ همین درخت sqlite می‌سازد)."""

    def __enter__(self):
        mod = types.ModuleType("agi2027_control.integration")
        mod.try_handle_control = lambda text, actor, **kw: (
            {"ok": True, "status": "OK"}
            if str(text or "").strip().split()[0].lower() in ("/ops",) else None)
        mod.format_control_result = lambda res: "control " + str(res.get("status"))
        self._old = sys.modules.get("agi2027_control.integration")
        sys.modules["agi2027_control.integration"] = mod
        return self

    def __exit__(self, *a):
        if self._old is not None:
            sys.modules["agi2027_control.integration"] = self._old
        else:
            sys.modules.pop("agi2027_control.integration", None)
        return False


def _msg(text, mid=3, reply_text=None, frm=OWNER):
    m = {"message_id": mid, "from": {"id": frm},
         "chat": {"id": OWNER, "type": "private"}, "text": text}
    if reply_text is not None:
        m["reply_to_message"] = {"message_id": mid - 1, "text": reply_text}
    return {"update_id": mid, "message": m}


def _cbq(data, cid="cb1", frm=OWNER):
    return {"update_id": 90, "callback_query": {
        "id": cid, "from": {"id": frm}, "data": data,
        "message": {"message_id": 5, "chat": {"id": OWNER, "type": "private"}}}}


def _rows(table):
    db = RUNTIME / "octopus_ops.sqlite3"
    if not db.exists():
        return []
    conn = sqlite3.connect(str(db))
    try:
        return conn.execute(f"SELECT * FROM {table}").fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def _receipts():
    p = RUNTIME / "ops-buttons-audit.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _kbs(fc):
    return [c["kw"].get("keyboard") for c in fc.named("send")]


# ── ۱) فلگ خاموش = امروز ───────────────────────────────────────────────────
def t_a_flag_off_the_ops_answer_is_keyboardless_and_shape_identical():
    """خاموش ⇒ نه کیبورد، نه حتی kwargِ `keyboard`، نه کلیدِ اضافه در خروجی."""
    fc, c = _reset(flag_on=False)
    with _ControlStub():
        res = c.handle_update(_msg("/ops"))
    assert res == {"kind": "agi2027-control", "status": "OK", "ok": True,
                   "sent": True}, res
    sends = fc.named("send")
    assert len(sends) == 1, sends
    assert "keyboard" not in sends[0]["kw"], \
        f"فلگ خاموش ولی kwargِ keyboard پاس شد: {sends[0]['kw']}"


def t_b_flag_off_an_ops_press_falls_through_to_todays_ignore_path():
    """خاموش ⇒ `ops:` verb ناشناخته می‌ماند: همان «نادیده»ی امروز، صفر جهش."""
    fc, c = _reset(flag_on=False)
    res = c.handle_update(_cbq("ops:lead", cid="cb-off"))
    assert res == {"kind": "callback", "verdict": None}, res
    assert fc.named("answer")[-1]["text"] == "نادیده", fc.named("answer")
    assert _rows("leads") == [] and _receipts() == [], "خاموش ولی اثر گذاشت"


def t_c_flag_off_a_marked_reply_is_not_intercepted():
    """خاموش ⇒ ریپلایِ نشان‌دار هیچ لیدی نمی‌سازد و مسیرِ پیام دزدیده نمی‌شود."""
    fc, c = _reset(flag_on=False)
    res = c.handle_update(_msg("علی چتسوود", mid=11,
                               reply_text="x " + center.OPS_ASK_LEAD))
    assert (res or {}).get("kind") != "ops-reply", res
    assert _rows("leads") == [], "فلگ خاموش ولی لید ساخته شد"


# ── ۲) شکلِ کیبورد ─────────────────────────────────────────────────────────
def t_d_flag_on_ops_carries_the_six_buttons_within_telegrams_budget():
    fc, c = _reset(flag_on=True)
    with _ControlStub():
        res = c.handle_update(_msg("/ops"))
    assert res.get("ops_buttons") == 3, res
    kb = _kbs(fc)[0]
    assert kb and len(kb) == 3, kb
    flat = [b for row in kb for b in row]
    assert len(flat) == 6, flat
    for b in flat:
        cd = b.get("callback_data")
        if cd is not None:
            assert len(cd.encode("utf-8")) <= 64, (cd, len(cd.encode("utf-8")))
            assert cd.split(":")[0] == "ops", cd
    labels = "".join(b["text"] for b in flat)
    for want in ("کاکپیت", "کارهای امروز", "لیدِ نو", "ثبتِ پول",
                 "وضعیتِ مغز", "تأییدها"):
        assert want in labels, f"دکمهٔ «{want}» غایب: {labels}"


def t_e_navigation_buttons_become_web_app_only_when_a_live_url_exists():
    """بدونِ URL ِ زنده دکمهٔ web_app **ساخته نمی‌شود** (کارتِ مرده هرگز)؛
    با URL، ناوبری به تب‌هایی می‌رود که امروز در index.html هستند."""
    fc, c = _reset(flag_on=True)
    kb_dark = c._ops_keyboard("/ops")
    assert not any("web_app" in b for row in kb_dark for b in row), kb_dark
    fc, c = _reset(flag_on=True, url="https://cockpit.example/app")
    kb = c._ops_keyboard("/ops")
    tabs = [b["web_app"]["url"] for row in kb for b in row if "web_app" in b]
    assert len(tabs) == 3, tabs
    assert tabs[0].endswith("#tab=home"), tabs
    assert tabs[1].endswith("#tab=studio"), tabs
    assert tabs[2].endswith("#tab=approvals"), tabs
    muts = [b["callback_data"] for row in kb for b in row
            if "callback_data" in b]
    assert sorted(muts) == ["ops:brain", "ops:lead", "ops:money"], muts


def t_f_only_the_ops_command_gets_the_keyboard():
    fc, c = _reset(flag_on=True)
    assert c._ops_keyboard("/repair list") is None
    assert c._ops_keyboard("") is None
    assert c._ops_keyboard("/ops status") is not None
    assert c._ops_keyboard("/OPS@octopus_bot") is not None


# ── ۳) هر مسیر answer می‌گیرد ──────────────────────────────────────────────
def t_g_every_ops_path_answers_the_callback_including_refusals():
    datas = ["ops:lead", "ops:money", "ops:brain", "ops:ui", "ops:tsk",
             "ops:apr", "ops:t:", "ops:t:lead_probe", "ops:zz", "ops"]
    for i, d in enumerate(datas):
        fc, c = _reset(flag_on=True)
        res = c.handle_update(_cbq(d, cid=f"cb-{i}"))
        assert res is not None and res.get("kind") == "ops-button", (d, res)
        ans = fc.named("answer")
        assert ans and ans[-1]["id"] == f"cb-{i}", \
            f"«{d}» بدونِ answerCallbackQuery برگشت — spinner ِ زنده"
        assert ans[-1]["text"], f"«{d}» answer ِ خالی داد — مالک نمی‌فهمد چه شد"
        assert _receipts(), f"«{d}» رسید نگذاشت"


def t_h_a_press_that_needs_input_creates_nothing_even_twice():
    """دکمهٔ ورودی‌خواه فقط راهنما می‌فرستد — دبل‌تپ هم صفر رکورد."""
    fc, c = _reset(flag_on=True)
    c.handle_update(_cbq("ops:lead", cid="p1"))
    c.handle_update(_cbq("ops:lead", cid="p2"))
    assert _rows("leads") == [], "تپِ راهنما لید ساخت"
    outs = [r["outcome"] for r in _receipts()]
    assert outs == ["PROMPTED", "PROMPTED"], outs
    assert all(r["mutated"] is False for r in _receipts())
    prompts = [s["text"] for s in fc.named("send")]
    assert all(center.OPS_ASK_LEAD in t for t in prompts), prompts


# ── ۴) ثبت idempotent ──────────────────────────────────────────────────────
def _make_lead(c, mid=21, body="ali-chatswood"):
    return c.handle_update(_msg(body, mid=mid,
                                reply_text="راهنما " + center.OPS_ASK_LEAD))


def t_i_the_reply_flow_records_exactly_one_lead_even_when_redelivered():
    fc, c = _reset(flag_on=True)
    r1 = _make_lead(c)
    assert r1["kind"] == "ops-reply" and r1["outcome"] == "APPLIED", r1
    assert len(_rows("leads")) == 1, _rows("leads")
    r2 = _make_lead(c)                       # همان update، دوباره
    assert r2["outcome"] == "DUPLICATE", r2
    assert r2["mutated"] is False, r2
    assert len(_rows("leads")) == 1, f"تحویلِ دوباره لیدِ دوم ساخت: {_rows('leads')}"


def t_j_double_press_of_a_mutating_button_creates_exactly_one_record():
    """`ops:t:<lead>` تنها دکمهٔ جهش‌زای بی‌ورودی است — دبل‌تپ مستقیم سنجیده
    می‌شود: دومی DUPLICATE می‌گیرد و ردیفِ دوم ساخته نمی‌شود."""
    fc, c = _reset(flag_on=True)
    _make_lead(c)
    kb = [k for k in _kbs(fc) if k]
    assert kb, "کارتِ لید دکمهٔ پیگیری نداشت"
    cd = kb[-1][0][0]["callback_data"]
    assert cd.startswith("ops:t:"), cd
    assert len(cd.encode("utf-8")) <= 64, cd
    a = c.handle_update(_cbq(cd, cid="t1"))
    b = c.handle_update(_cbq(cd, cid="t2"))
    assert a["outcome"] == "APPLIED" and a["mutated"] is True, a
    assert b["outcome"] == "DUPLICATE" and b["mutated"] is False, b
    assert len(_rows("tasks")) == 1, f"دبل‌تپ دو کار ساخت: {_rows('tasks')}"
    assert [x["text"] for x in fc.named("answer")][-2:] == \
        [center._OPS_TOAST["APPLIED"], center._OPS_TOAST["DUPLICATE"]]


def t_k_money_is_only_recorded_never_moved():
    fc, c = _reset(flag_on=True)
    res = c.handle_update(_msg("۴۵۰ بیعانهٔ چتسوود", mid=31,
                               reply_text="راهنما " + center.OPS_ASK_MONEY))
    assert res["outcome"] == "APPLIED", res
    rows = _rows("value_events")
    assert len(rows) == 1, rows
    conn = sqlite3.connect(str(RUNTIME / "octopus_ops.sqlite3"))
    try:
        got = conn.execute("SELECT value_type, output_score, event "
                           "FROM value_events").fetchone()
    finally:
        conn.close()
    assert got[0] == "money" and float(got[1]) == 450.0, got
    assert got[2] == "money_in", got
    said = " ".join(s["text"] for s in fc.named("send"))
    assert "هیچ پولی جابه‌جا نشد" in said, said


# ── ۵) ردها ثبت می‌شوند ────────────────────────────────────────────────────
def t_l_a_refused_input_is_audited_and_writes_no_record():
    """موتورِ اکشن برای رد **قبل از** audit برمی‌گردد؛ اگر مرکز خودش ننویسد،
    رد و «هیچ» یک شکل می‌شوند. این‌جا قفل می‌شود."""
    fc, c = _reset(flag_on=True)
    res = c.handle_update(_msg("یه مقدار پول", mid=41,
                               reply_text="راهنما " + center.OPS_ASK_MONEY))
    assert res["outcome"] == "REFUSED" and res["reason"] == "missing_amount", res
    assert _rows("value_events") == [], "ردِ ورودی رکورد ساخت"
    recs = _receipts()
    assert recs and recs[-1]["outcome"] == "REFUSED", recs
    assert recs[-1]["reason"] == "missing_amount", recs[-1]
    assert recs[-1].get("ts"), "رسید بی‌زمان — «کِی» گم است"
    assert recs[-1].get("actor") == OWNER, recs[-1]


def t_m_a_forged_lead_id_is_refused_answered_and_audited():
    fc, c = _reset(flag_on=True)
    res = c.handle_update(_cbq("ops:t:", cid="bad"))
    assert res["outcome"] == "BLOCKED" and res["mutated"] is False, res
    assert fc.named("answer")[-1]["id"] == "bad"
    assert _rows("tasks") == [], "شناسهٔ خراب کار ساخت"
    assert _receipts()[-1]["reason"] == "invalid_lead_id", _receipts()[-1]


# ── ۶) غیرمالک ─────────────────────────────────────────────────────────────
def t_n_a_non_owner_press_changes_nothing_and_reveals_nothing():
    """حتی answer هم نمی‌گیرد — پاسخ وجودِ بات را لو می‌دهد (قراردادِ موجود)."""
    fc, c = _reset(flag_on=True)
    _make_lead(c)
    before_tasks, before_recs = len(_rows("tasks")), len(_receipts())
    fc.calls.clear()
    res = c.handle_update(_cbq("ops:t:lead_ali-chatswood", cid="cbx",
                               frm=STRANGER))
    assert res is None, res
    assert fc.calls == [], f"غیرمالک پاسخ گرفت: {fc.calls}"
    assert len(_rows("tasks")) == before_tasks, "غیرمالک کار ساخت"
    assert len(_receipts()) == before_recs, "غیرمالک رسید ساخت — نشتِ اطلاعات"
    res2 = c.handle_update(_msg("ali2", mid=51, frm=STRANGER,
                                reply_text="راهنما " + center.OPS_ASK_LEAD))
    assert res2 is None and len(_rows("leads")) == 1, (res2, _rows("leads"))


# ── ۷) سیمِ واقعی (بدونِ stub، بدونِ نوشتن) ────────────────────────────────
def t_o_the_lane_rides_the_existing_ops_route_not_a_second_one():
    """`/ops` همچنان مالِ control-plane است و مرکز روتِ دومی برایش نساخته."""
    from agi2027_control import integration as real   # noqa: WPS433
    assert real.is_control_command("/ops") is True
    assert real.is_control_command("/lead") is False
    src = (_HERE.parent / "telegram_center" / "center.py").read_text("utf-8")
    assert src.count("_agi_try_control(text") == 1, \
        "بیش از یک صداکنندهٔ control-plane — روتِ دوم ساخته شده"
    assert '"/ops"' not in src.split("handlers = {")[1].split("}")[0], \
        "`/ops` به جدولِ handlers ِ مرکز اضافه شده — یعنی روتِ دوم"


# ── ۸) شناسهٔ شکننده ─────────────────────────────────────────────────────
def t_p_a_lead_id_that_cannot_survive_a_callback_roundtrip_gets_no_button():
    """شناسه‌ای که در `callback_data` می‌شکند **دکمه نمی‌گیرد**.

    `make_id` نویسه‌های `.:@` را هم مجاز می‌داند، ولی `:` جداکنندهٔ خودِ
    callback است: `ops:t:ali:chatswood` در روتر به `ali` بریده می‌شود و کارِ
    پیگیری به لیدِ **دیگری** می‌خورد. بدونِ این سنجه، شُل‌کردنِ آن regex
    بی‌صدا سبز می‌ماند — جهشِ «regex → فقط truthy» زنده برمی‌گشت.

    نیمهٔ دوم: بلندترین هندلِ مجاز هم باید زیرِ سقفِ ۶۴بایتیِ تلگرام بماند —
    یعنی `OPS_HANDLE_MAX` خودش باربر است، نه تزئینی."""
    fc, c = _reset(flag_on=True)
    res = c.handle_update(_msg("ali:chatswood", mid=61,
                               reply_text="راهنما " + center.OPS_ASK_LEAD))
    assert res["outcome"] == "APPLIED", res
    assert ":" in str(res["record_id"]), res
    assert _kbs(fc) == [None], \
        f"شناسهٔ شکننده دکمهٔ پیگیری گرفت: {_kbs(fc)}"
    fc, c = _reset(flag_on=True)
    c.handle_update(_msg("a" * (center.OPS_HANDLE_MAX + 20), mid=63,
                         reply_text="راهنما " + center.OPS_ASK_LEAD))
    kb = [k for k in _kbs(fc) if k]
    assert kb, "هندلِ بلندِ مجاز دکمه نگرفت — سقف یا regex تراز نیست"
    cd = kb[-1][0][0]["callback_data"]
    assert len(cd.encode("utf-8")) <= 64, (cd, len(cd.encode("utf-8")))


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_ops_buttons: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
