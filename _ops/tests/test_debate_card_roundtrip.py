#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_debate_card_roundtrip.py — پلِ رأیِ مناظره، از دو سرِ **واقعی**.

`test_debate_owner_verdict.py` هر تکه را جدا سنجید و همه سبز بودند. این فایل همان
تکه‌ها را **به‌هم وصل** می‌سنجد، روی مسیرِ تولیدی:

    ارگانیسم `_queue_survivor` → survivors-pending.jsonl
      → مرکز `Center._approvals_queue_page()` (همان تابعی که دکمهٔ منو صدا می‌زند)
        → مالک روی دکمهٔ واقعی می‌زند → `Center._handle_approval_callback`
          → approval_store + فایلِ per-decision
            → ارگانیسم `owner_verdict_for` رأی را می‌بیند و دوباره نمی‌پرسد.

چرا لازم بود: با `OCTOPUS_WIRE_CB_TOKEN` روشن، `_approvals_queue_page` توکن را از
snapshot ِ `load_pending()` امضا می‌کرد، ولی jobِ مناظره را **خودِ render** (داخلِ
`ingest_debate_survivors`) بعد از آن snapshot وارد صف می‌کند. پس mint با dictِ تهی
امضا می‌زد (type=None · risk=None · expires="") و handler لحظهٔ تپ jobِ واقعی را
می‌خواند → hash فرق می‌کرد → «توکنِ نامعتبر». دکمه دیده می‌شد، مالک می‌زد، هیچ رأیی
ثبت نمی‌شد و همان ایده دوباره صف می‌شد. تستِ قبلی این را نمی‌دید چون mint ِ ساختگی
(`lambda jid, a: f"t{a}"`) می‌داد، نه mint ِ خودِ مرکز.

$0 آفلاین. هیچ state ِ زنده‌ای لمس نمی‌شود (آخرین چک اثباتش است).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("debate-card-roundtrip")
import opslib        # noqa: E402
import debate_loop   # noqa: E402

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS / "telegram_center"))
import approval_store as aps    # noqa: E402
import callback_token as cbtok  # noqa: E402
import render                   # noqa: E402
import center as center_mod     # noqa: E402

# ── ایزولهٔ approval_store ─────────────────────────────────────────────────────
# مسیرهای این ماژول از __file__ ساخته می‌شوند نه از env، پس harness ایزوله‌شان
# نمی‌کند. بدونِ این چند خط، تست به approvals.json ِ **زنده** می‌نوشت.
_LIVE_APPROVALS = aps._APPROVALS_JSON
_LIVE_STAMP = (_LIVE_APPROVALS.exists(),
               _LIVE_APPROVALS.stat().st_size if _LIVE_APPROVALS.exists() else -1,
               _LIVE_APPROVALS.stat().st_mtime_ns if _LIVE_APPROVALS.exists() else -1)
_SANDBOX = Path(ENV["root"]) / "_octopus"
aps._APPROVALS_JSON = _SANDBOX / "state" / "approvals.json"
aps._AUDIT_PATH = _SANDBOX / "logs" / "audit.log"
aps._LEGACY_DIR = opslib.STATE_DIR / "telegram" / "approvals"
assert str(aps._APPROVALS_JSON).startswith(str(ENV["root"])), "صفِ تأیید ایزوله نشد"
assert aps._LEGACY_DIR == debate_loop._verdict_dir(), "پلِ verdict بینِ دو پروسه نمی‌خواند"
center_mod.aps_mod = aps        # همان ماژولِ ایزوله‌شده، نه fake

# مقدارِ آزمایشیِ HMAC — نه secret ِ واقعی و نه از هیچ فایلی خوانده می‌شود.
_TEST_CB_SECRET = "roundtrip-test-value-not-a-secret"
_OWNER = 777

TOPIC = {"id": "seed-3", "source": "SEED_TOPICS", "text": "موضوعِ آزمایشی"}
MUSE = {"idea": "سنجشِ ارزشِ per-organ از رویدادهای تأییدشده", "why_genius": "g",
        "why_insane": "i", "est_tokens": 10, "quality_bar": "normal",
        "epistemic_tag": "SPEC"}
ARCH = {"verdict": "pass", "kill_condition": "k", "cheapest_test": "c",
        "epistemic_tag": "SPEC"}
SIG = debate_loop.survivor_sig(TOPIC["id"], MUSE["idea"])
JID = debate_loop.survivor_job_id(SIG)


class _FakeClient:
    """کلاینتِ تلگرام بدونِ شبکه — هیچ پیامی واقعاً ارسال نمی‌شود."""

    def __init__(self, owner=_OWNER):
        self.owner_id = owner
        self.owner_chat_id = owner
        self.center_chat_id = 999

    def wired(self):
        return True

    def is_owner(self, u):
        frm = ((u.get("message") or {}).get("from")
               or (u.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def edit(self, *a, **k):
        return True

    def answer_callback(self, *a, **k):
        return True

    def send(self, *a, **k):
        return 1


def _center():
    return center_mod.Center(client=_FakeClient(), render_mod=render)


def _cbq(data, chat=_OWNER):
    return {"id": "cb1", "from": {"id": _OWNER},
            "message": {"message_id": 1, "chat": {"id": chat}}, "data": data}


def _reset(verdicts: bool = True) -> None:
    if aps._APPROVALS_JSON.exists():
        aps._APPROVALS_JSON.unlink()
    if debate_loop.PENDING_JSONL.exists():
        debate_loop.PENDING_JSONL.unlink()
    if debate_loop.QUEUE_MD.exists():
        debate_loop.QUEUE_MD.unlink()
    vdir = debate_loop._verdict_dir()
    if verdicts and vdir.exists():
        for f in vdir.glob("dbt-*.json"):
            f.unlink()


def _armed(cb_token: bool = True) -> None:
    """هر دو پروسه مسلح: ارگانیسم (نویسنده) و مرکز (خواننده)."""
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    if cb_token:
        os.environ["OCTOPUS_WIRE_CB_TOKEN"] = "1"
        os.environ["OCTOPUS_CB_SECRET"] = _TEST_CB_SECRET
    else:
        os.environ.pop("OCTOPUS_WIRE_CB_TOKEN", None)
        os.environ.pop("OCTOPUS_CB_SECRET", None)


def _buttons(kb: list) -> list:
    return [b.get("callback_data", "") for row in kb for b in row]


def _my_button(kb: list, action: str) -> str:
    got = [d for d in _buttons(kb) if d.split(":")[:3] == ["ap", action, JID]]
    assert len(got) == 1, f"دکمهٔ {action} برای {JID} یکتا نیست: {_buttons(kb)}"
    return got[0]


def _card_after_queue(cb_token: bool = True) -> tuple:
    """مسیرِ کامل: ارگانیسم می‌نویسد، بعد مرکز همان کارتی را می‌سازد که منو می‌سازد."""
    _armed(cb_token)
    _reset()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is True
    assert debate_loop.PENDING_JSONL.exists(), "ارگانیسم پروژکشن ننوشت"
    assert aps.get(JID) is None, "مرکز هنوز کارت نساخته — job نباید موجود باشد"
    return _center()._approvals_queue_page()


# ═══ ۱. ایده از پروسهٔ ارگانیسم به کارتِ مرکز می‌رسد ═══════════════════════════
def t_survivor_reaches_the_real_card():
    text, kb = _card_after_queue()
    assert "مناظره" in text, text
    assert MUSE["idea"][:25] in text, "متنِ ایده روی کارت نیست"
    ok = _my_button(kb, "ok")
    assert ok.split(":")[3], f"توکن الحاق نشد: {ok}"
    assert len(ok.encode("utf-8")) <= 64, f"از سقفِ ۶۴ بایتِ تلگرام رد شد: {ok}"
    # و ingest واقعاً jobِ صف را ساخت (نه فقط یک ردیفِ نمایشی)
    job = aps.get(JID)
    assert isinstance(job, dict) and job["type"] == "debate", job
    assert job["status"] == "pending" and job["risk"] == "medium", job


# ═══ ۲. تپِ مالک روی همان دکمه، رأی را ثبت می‌کند ═══════════════════════════════
def t_owner_tap_on_the_real_button_lands():
    _text, kb = _card_after_queue()
    data = _my_button(kb, "no")
    out = _center()._handle_approval_callback(_cbq(data), data)
    assert out.get("rejected") is None, f"دکمهٔ کارت رد شد: {out}"
    assert out.get("id") == JID and out.get("ok") is True, out
    assert aps.get(JID)["status"] == "rejected", aps.get(JID)


def t_the_verdict_crosses_back_to_the_organism():
    """نصفِ دومِ پل: رأی باید به پروسهٔ نویسنده برگردد وگرنه همان ایده دوباره می‌آید."""
    _text, kb = _card_after_queue()
    data = _my_button(kb, "no")
    _center()._handle_approval_callback(_cbq(data), data)
    assert debate_loop.owner_verdict_for(SIG) == "rejected", \
        "رأی به حلقهٔ مناظره نرسید — ایدهٔ ردشده دوباره صف می‌شود"
    if debate_loop.QUEUE_MD.exists():
        debate_loop.QUEUE_MD.unlink()   # تنها دلیلِ ممکنِ رد شدن، خودِ رأی باشد
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is False, \
        "ایدهٔ ردشده دوباره صف شد"


# ═══ ۳. توکن به jobِ واقعی بایند است، نه به یک dictِ تهی ═══════════════════════
def t_token_binds_to_the_real_job_not_an_empty_one():
    """گاردِ مستقیمِ رگرسیون: مقدارِ پیش‌از‌فیکس محاسبه و **رد** می‌شود."""
    _text, kb = _card_after_queue()
    tok = _my_button(kb, "ok").split(":")[3]
    job = aps.get(JID)
    c = _center()
    good = cbtok.mint(JID, "ok", _OWNER, c._ap_action_hash("ok", JID, job),
                      str(job.get("expires_epoch", "")))
    stale = cbtok.mint(JID, "ok", _OWNER, c._ap_action_hash("ok", JID, {}), "")
    assert good and stale and good != stale, "سناریو برپا نشد (دو توکن یکی درآمدند)"
    assert tok == good, "توکن با jobِ واقعی امضا نشده"
    assert tok != stale, "توکن با dictِ تهی امضا شده — همان باگِ «توکنِ نامعتبر»"


def t_a_job_already_in_pending_keeps_its_old_binding():
    """ضدِ over-reach: jobی که در snapshot هست باید **همان** بایندِ قبلی را بگیرد."""
    _armed()
    _reset()
    job = {"id": "job-plain", "type": "task", "title": "کارِ ساده", "risk": "read"}
    aps.add_pending(dict(job))
    stored = aps.get("job-plain")
    _text, kb = _center()._approvals_queue_page()
    got = [d for d in _buttons(kb) if d.split(":")[:3] == ["ap", "ok", "job-plain"]]
    assert len(got) == 1, _buttons(kb)
    c = _center()
    want = cbtok.mint("job-plain", "ok", _OWNER,
                      c._ap_action_hash("ok", "job-plain", stored),
                      str(stored.get("expires_epoch", "")))
    assert got[0].split(":")[3] == want, "بایندِ jobِ عادی عوض شد"


# ═══ ۴. گاردها برداشته نشده‌اند ════════════════════════════════════════════════
def t_tampered_token_is_still_rejected():
    _text, kb = _card_after_queue()
    data = _my_button(kb, "ok")
    seg = data.split(":")
    seg[3] = ("0" * len(seg[3])) if seg[3] != "0" * len(seg[3]) else "1" * len(seg[3])
    bad = ":".join(seg)
    out = _center()._handle_approval_callback(_cbq(bad), bad)
    assert out.get("rejected") == "bad-token", out
    assert aps.get(JID)["status"] == "pending", "توکنِ جعلی رأی ثبت کرد!"


def t_tokenless_legacy_callback_is_still_rejected():
    _text, _kb = _card_after_queue()
    legacy = f"ap:ok:{JID}"
    out = _center()._handle_approval_callback(_cbq(legacy), legacy)
    assert out.get("rejected") == "bad-token", out
    assert aps.get(JID)["status"] == "pending", "callbackِ بی‌توکن رأی ثبت کرد!"


def t_wrong_destination_is_still_rejected():
    _text, kb = _card_after_queue()
    data = _my_button(kb, "ok")
    out = _center()._handle_approval_callback(_cbq(data, chat=123456), data)
    assert out.get("rejected") == "bad-destination", out
    assert aps.get(JID)["status"] == "pending", "مقصدِ غریبه رأی ثبت کرد!"


# ═══ ۵. فلگ‌ها خاموش = امروز ══════════════════════════════════════════════════
def t_without_cb_token_the_card_is_tokenless_and_works():
    """فلگِ توکن خاموش (وضعیتِ امروزِ زنده) → callbackِ سه‌بخشی، و رأی می‌نشیند."""
    _text, kb = _card_after_queue(cb_token=False)
    data = _my_button(kb, "no")
    assert data == f"ap:no:{JID}", data
    out = _center()._handle_approval_callback(_cbq(data), data)
    assert out.get("id") == JID and out.get("ok") is True, out
    assert debate_loop.owner_verdict_for(SIG) == "rejected"


def t_debate_flag_off_leaves_the_card_untouched():
    os.environ["OCTOPUS_WIRE_CB_TOKEN"] = "1"
    os.environ["OCTOPUS_CB_SECRET"] = _TEST_CB_SECRET
    os.environ.pop("OCTOPUS_WIRE_DEBATE_VERDICT", None)
    _reset()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is True
    assert not debate_loop.PENDING_JSONL.exists(), "با فلگِ خاموش پروژکشن نوشته شد"
    text, kb = _center()._approvals_queue_page()
    assert "مناظره" not in text, text
    assert aps.get(JID) is None, "با فلگِ خاموش jobِ مناظره ساخته شد"
    assert not [d for d in _buttons(kb) if JID in d], _buttons(kb)


def t_only_the_writer_armed_means_no_card_and_no_lost_record():
    """نصفه‌مسلح: ارگانیسم می‌نویسد، مرکز خاموش. کارت خالی است ولی ردیف **گم نمی‌شود**
    — به‌محضِ مسلح‌شدنِ مرکز همان ردیف تبدیل به کارت می‌شود (ثبت همیشه، تحویل گیت‌دار)."""
    _armed()
    _reset()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is True
    os.environ.pop("OCTOPUS_WIRE_DEBATE_VERDICT", None)      # فقط سمتِ مرکز خاموش
    text, _kb = _center()._approvals_queue_page()
    assert "مناظره" not in text, "مرکزِ خاموش کارت ساخت"
    assert debate_loop.PENDING_JSONL.exists(), "ردیفِ نوشته‌شده پاک شد"
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"          # مرکز مسلح می‌شود
    text2, kb2 = _center()._approvals_queue_page()
    assert "مناظره" in text2, "ردیفِ قبلی بعد از مسلح‌شدن کارت نشد"
    assert _my_button(kb2, "ok")


def t_second_render_does_not_duplicate_the_job():
    _text, _kb = _card_after_queue()
    created = aps.get(JID)["created_at"]
    _t2, kb2 = _center()._approvals_queue_page()
    assert aps.get(JID)["created_at"] == created, "ingest دوباره job ساخت"
    assert len([d for d in _buttons(kb2) if d.split(":")[:3] == ["ap", "ok", JID]]) == 1


def t_live_approval_queue_was_never_touched():
    now = (_LIVE_APPROVALS.exists(),
           _LIVE_APPROVALS.stat().st_size if _LIVE_APPROVALS.exists() else -1,
           _LIVE_APPROVALS.stat().st_mtime_ns if _LIVE_APPROVALS.exists() else -1)
    assert now == _LIVE_STAMP, f"صفِ زندهٔ تأیید عوض شد! {_LIVE_STAMP} → {now}"


CHECKS = [
    ("ایدهٔ ارگانیسم به کارتِ واقعیِ مرکز می‌رسد", t_survivor_reaches_the_real_card),
    ("تپِ مالک روی دکمهٔ همان کارت رأی را ثبت می‌کند",
     t_owner_tap_on_the_real_button_lands),
    ("رأی به پروسهٔ ارگانیسم برمی‌گردد و ایده دوباره نمی‌آید",
     t_the_verdict_crosses_back_to_the_organism),
    ("توکن با jobِ واقعی امضا می‌شود نه با dictِ تهی",
     t_token_binds_to_the_real_job_not_an_empty_one),
    ("jobی که از قبل در صف است بایندِ قبلی‌اش را نگه می‌دارد",
     t_a_job_already_in_pending_keeps_its_old_binding),
    ("توکنِ دستکاری‌شده هنوز رد می‌شود", t_tampered_token_is_still_rejected),
    ("callbackِ قدیمیِ بی‌توکن هنوز رد می‌شود",
     t_tokenless_legacy_callback_is_still_rejected),
    ("مقصدِ نامعتبر هنوز رد می‌شود", t_wrong_destination_is_still_rejected),
    ("بدونِ فلگِ توکن، کارت tokenless است و رأی می‌نشیند",
     t_without_cb_token_the_card_is_tokenless_and_works),
    ("فلگِ مناظره خاموش → نه پروژکشن، نه کارت، نه دکمه",
     t_debate_flag_off_leaves_the_card_untouched),
    ("نصفه‌مسلح: کارت نیست ولی ردیف گم نمی‌شود",
     t_only_the_writer_armed_means_no_card_and_no_lost_record),
    ("رندرِ دوم job را تکراری نمی‌سازد", t_second_render_does_not_duplicate_the_job),
    ("صفِ زندهٔ تأیید دست‌نخورده ماند", t_live_approval_queue_was_never_touched),
]

if __name__ == "__main__":
    print(f"پلِ رأیِ مناظره — رفت‌وبرگشتِ کامل ({len(CHECKS)} چک)")
    assert len(CHECKS) >= 13, "فهرستِ چک‌ها ناقص است — تستِ بی‌صدا"
    failed = harness.run(CHECKS)
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} پاس")
    sys.exit(1 if failed else 0)
