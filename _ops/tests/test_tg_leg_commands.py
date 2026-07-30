#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_leg_commands — ۹ فرمانِ طبیعیِ اتاقِ کنترلِ پاها (رأیِ مالک ۰۷-۳۱).

    «وضعیت» باید جواب بگیرد، نه اینکه یک TASK با متنِ «وضعیت» صف شود.

پوشش: طبقه‌بندِ بسته (تطابقِ کامل، صفر بیش‌بست) · اجرای هر فرمان از مسیرِ
ممیزی‌شدهٔ دکمه‌ها · رفعِ مانع با ریپلای به کارتِ 🚧 · گزارشِ روزانه از
حقیقتِ Taskها (با قراردادِ سکوت) · و رگرسیون: پیامِ کاری هنوز Task می‌شود.
"""
import json
import sys
import types
from pathlib import Path

import harness

ENV = harness.setup("tg-leg-commands")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import center          # noqa: E402
import leg_commands as lc   # noqa: E402
import leg_tasks as lt      # noqa: E402

NOW = 1_785_400_000.0
GROUP = -1004475788460
OWNER = 777
CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"


class FakeClient:
    """صفر شبکه — فقط ثبت. owner_chat_id لازم است تا گیتِ ورودی فعال شود."""

    def __init__(self):
        self.owner_chat_id = OWNER
        self.center_chat_id = GROUP
        self.calls: list = []
        self._mid = 100

    def wired(self):
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == OWNER

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream=None):
        self.calls.append(("send", {"text": text, "topic_id": topic_id,
                                    "keyboard": keyboard, "chat_id": chat_id}))
        self._mid += 1
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def pin_message(self, message_id, chat_id=None):
        return True

    def answer_callback(self, callback_id, text=""):
        return True

    def sends(self):
        return [p["text"] for k, p in self.calls if k == "send"]


def _render():
    return types.SimpleNamespace(
        LEGS={"lead": "Lead-نقاشی"},
        collect_feeds=lambda: {},
        render_status=lambda feeds: "",
        render_leg_digest=lambda k, d: "",
        render_decision=lambda item: ("d", None))


def _reset(leg="lead"):
    CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CFG_PATH.write_text(json.dumps(
        {"chat_id": GROUP, "topics": {"lead": 11, "mining": 13}}), "utf-8")
    try:
        lt._path(leg).unlink()
    except OSError:
        pass
    # پاکِ فلگِ pause تا تست‌ها به هم نشت نکنند
    try:
        import power as pw
        pw.resume_leg(leg)
    except Exception:  # noqa: BLE001
        pass


def _center():
    fc = FakeClient()
    return center.Center(client=fc, clock=lambda: NOW,
                         render_mod=_render()), fc


def _leg_msg(text, thread=11, reply_to=None):
    m = {"from": {"id": OWNER}, "chat": {"id": GROUP, "type": "supergroup"},
         "message_thread_id": thread, "is_topic_message": True, "text": text}
    if reply_to is not None:
        m["reply_to_message"] = {"text": reply_to}
    return {"update_id": 1, "message": m}


# ── طبقه‌بند: بسته و بدونِ بیش‌بست ──────────────────────────────────────────
def t_a_all_nine_commands_classify():
    cases = {"وضعیت": "status", "وضعیت این پا چیه؟": "status",
             "صف": "queue", "صف را نشان بده": "queue",
             "ادامه بده": "resume", "متوقف شو": "pause", "توقف": "pause",
             "قدم بعدی": "next", "کار بعدی": "next",
             "مانع چیست": "blockers", "چرا گیر کردی؟": "blockers",
             "شاهد بده": "receipts", "شاهدها": "receipts",
             "گزارش امروز": "report", "گزارش": "report"}
    for text, want in cases.items():
        assert lc.classify(text) == want, (text, lc.classify(text), want)


def t_b_worklike_sentences_are_not_swallowed():
    """درسِ بیش‌بست: فرمان فقط تطابقِ کامل. جملهٔ کاری باید Task بماند."""
    for text in ("وضعیت سایت مشتری را بررسی کن",
                 "ادامه بده تحقیق دیروز را",
                 "گزارش مالی شرکت X را پیدا کن",
                 "صف بندی جدید برای لیدها طراحی کن",
                 "این لینک را بررسی کن"):
        assert lc.classify(text) is None, text


def t_c_enqueue_prefix_strips_and_empty_stays_honest():
    assert lc.strip_enqueue_prefix("این را به صف اضافه کن: بررسی سایت X") == \
        "بررسی سایت X"
    assert lc.strip_enqueue_prefix("به صف اضافه کن بررسی سایت X") == \
        "بررسی سایت X"
    assert lc.strip_enqueue_prefix("این را به صف اضافه کن") == ""
    assert lc.strip_enqueue_prefix("یک کار معمولی") is None


def t_d_every_command_key_has_a_branch_in_the_center():
    """ضدِ دکمهٔ مرده: هر کلیدِ COMMANDS باید در _exec_leg_command شاخه داشته باشد."""
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    body = src.split("def _exec_leg_command")[1][:4000]
    for cmd in lc.COMMANDS:
        assert f'cmd == "{cmd}"' in body, f"فرمانِ {cmd} شاخه ندارد"
    # و مسیرِ پیام واقعاً به classify می‌رسد
    assert "classify" in src.split("def handle_update")[1][:8000], \
        "handle_update فرمانِ طبیعی را طبقه‌بندی نمی‌کند"


# ── اجرا از مسیرِ مرکز (behavioral، نه AST) ─────────────────────────────────
def t_e_status_answers_with_the_card_and_queues_nothing():
    _reset()
    c, fc = _center()
    res = c.handle_update(_leg_msg("وضعیت"))
    assert res and res.get("kind") == "leg-cmd" and res.get("cmd") == "status", res
    assert lt.queue("lead") == [], "«وضعیت» نباید Task بسازد"
    joined = "\n".join(fc.sends())
    assert "وضعیت:" in joined and "در صف:" in joined, joined


def t_f_pause_and_resume_really_flip_the_power_flag():
    _reset()
    import power as pw
    c, fc = _center()
    res = c.handle_update(_leg_msg("متوقف شو"))
    assert res and res.get("cmd") == "pause", res
    assert pw.leg_paused("lead"), "فلگِ pause واقعاً ست نشد"
    res2 = c.handle_update(_leg_msg("ادامه بده"))
    assert res2 and res2.get("cmd") == "resume", res2
    assert not pw.leg_paused("lead"), "فلگِ pause واقعاً پاک نشد"


def t_g_next_starts_the_oldest_queued_task():
    _reset()
    lt.add("lead", "کار اول", now=NOW - 50)
    lt.add("lead", "کار دوم", now=NOW - 40)
    c, fc = _center()
    res = c.handle_update(_leg_msg("قدم بعدی"))
    assert res and res.get("cmd") == "next", res
    states = {t["id"]: t["state"] for t in lt.queue("lead")}
    assert states.get("TASK-1") == lt.WORKING, states
    assert states.get("TASK-2") == lt.QUEUED, states


def t_h_blockers_command_lists_the_open_question():
    _reset()
    t = lt.add("lead", "بررسی tender", now=NOW - 30)
    lt.set_state("lead", t["id"], lt.BLOCKED, question="فایل ضمیمه را بفرست")
    c, fc = _center()
    res = c.handle_update(_leg_msg("مانع چیست"))
    assert res and res.get("cmd") == "blockers", res
    joined = "\n".join(fc.sends())
    assert "فایل ضمیمه" in joined, joined


def t_i_reply_to_the_blocked_card_unblocks_that_task():
    _reset()
    t = lt.add("lead", "بررسی tender", now=NOW - 30)
    b = lt.set_state("lead", t["id"], lt.BLOCKED, question="ضمیمه؟")
    card = lt.blocked_text(b)
    c, fc = _center()
    res = c.handle_update(_leg_msg("ضمیمه در سایت رسمی است، بخش B",
                                   reply_to=card))
    assert res and res.get("kind") == "leg-task-unblock", res
    got = [x for x in lt.queue("lead") if x["id"] == t["id"]][0]
    assert got["state"] == lt.WORKING and not got.get("question"), got
    assert "اطلاعات مالک" in got["text"], got["text"]
    assert lt.queue("lead")[-1]["id"] == t["id"] or len(lt.queue("lead")) == 1, \
        "جوابِ مالک نباید Task ِ نو بسازد"


def t_j_reply_resolve_only_touches_blocked_tasks():
    _reset()
    t = lt.add("lead", "کاری", now=NOW - 30)
    d = lt.set_state("lead", t["id"], lt.DONE, result="تمام")
    c, fc = _center()
    res = c.handle_update(_leg_msg("اطلاعات اضافه",
                                   reply_to=f"🚧 {t['id']} — قدیمی"))
    # کارِ DONE زنده نمی‌شود؛ متن مسیرِ عادی را می‌رود و Task ِ نو می‌شود
    assert res and res.get("kind") == "leg-task", res
    done = [x for x in lt.recent_done("lead") if x["id"] == t["id"]]
    assert done and done[0]["state"] == lt.DONE


def t_k_enqueue_prefix_creates_the_task_from_the_remainder():
    _reset()
    c, fc = _center()
    res = c.handle_update(_leg_msg("این را به صف اضافه کن: بررسی سایت شهرداری"))
    assert res and res.get("kind") == "leg-task", res
    q = lt.queue("lead")
    assert q and q[0]["text"] == "بررسی سایت شهرداری", q


def t_l_regression_a_worklike_message_still_becomes_a_task():
    _reset()
    c, fc = _center()
    res = c.handle_update(_leg_msg("این لید را بررسی کن"))
    assert res and res.get("kind") == "leg-task", res
    assert lt.queue("lead")[0]["state"] == lt.QUEUED


# ── گزارشِ روزانه از حقیقتِ Task ────────────────────────────────────────────
def t_m_daily_report_counts_the_truth_and_stays_silent_when_idle():
    _reset()
    assert lt.daily_report_text("lead", now=NOW) == "", "بی‌فعالیت باید سکوت باشد"
    t1 = lt.add("lead", "کار ۱", now=NOW - 3000)
    lt.set_state("lead", t1["id"], lt.DONE, result="واجد شرایط", now=NOW - 2000)
    t2 = lt.add("lead", "کار ۲", now=NOW - 1000)
    lt.set_state("lead", t2["id"], lt.BLOCKED, question="شماره تماس؟",
                 now=NOW - 500)
    rep = lt.daily_report_text("lead", now=NOW)
    assert "خلاصه روزانه" in rep and "تکمیل: ۱" in rep, rep
    assert "مسدود: ۱" in rep and "شماره تماس" in rep, rep
    assert "خرج: صفر" in rep and "٪" not in rep, rep
    # پنجره واقعاً پنجره است: دو روز بعد همه‌چیز کهنه است ⇒ سکوت
    assert lt.daily_report_text("lead", now=NOW + 2 * 86400) == ""


def t_n_the_beat_digest_carries_the_task_truth():
    """دایجستِ ۲۴ساعتهٔ پا باید گزارشِ Taskها را هم بیاورد (وقتی فعالیتی هست)."""
    _reset()
    t1 = lt.add("lead", "کار دیروز", now=NOW - 4000)
    lt.set_state("lead", t1["id"], lt.DONE, result="اوکی", now=NOW - 3500)
    c, fc = _center()
    c.beat()
    digest = [s for s in fc.sends() if "خلاصه روزانه" in s]
    assert digest, fc.sends()
    assert "تکمیل: ۱" in digest[0], digest[0]


def t_o_the_beat_digest_stays_silent_with_no_activity():
    _reset()
    c, fc = _center()
    c.beat()
    assert not [s for s in fc.sends() if "خلاصه روزانه" in s], fc.sends()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_leg_commands: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
