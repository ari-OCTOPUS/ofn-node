#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_canonical_access_model — مدلِ مصوبِ دسترسی، قفل‌شده.

رأیِ مالک ۲۰۲۶-۰۷-۳۰ (VQ-TG-CONTRACT-001) گزینهٔ **A** را canonical کرد:

    Outer DM   = گفت‌وگوی کامل با کلِ اختاپوس
    Inner DM   = سلامت، هشدار، approval، رسید
    Group      = فقط پاها، هر پا در تاپیکِ خودش

بدونِ این فایل، «canonical» فقط یک کلمه در یک JSON بود. حالا اگر کسی — انسان یا
پچِ خودکار — مدل را به سمتِ B (هر دو DM مکالمهٔ کامل) ببرد، این تست قرمز
می‌شود. تغییرِ عمدیِ مدل باید **اول** این گارد را عوض کند و در VERDICT_QUEUE
ثبت شود؛ همان maintenance lane، نه یک ویرایشِ بی‌صدا.

⚠️ این فایل **تصویب** را می‌سنجد، نه **زنده بودن** را. مدل مصوب است و کد طبقش
نوشته شده، ولی `input_surface_policy` هنوز به `center.py` وصل نیست
(VQ-TG-GAP-INPUT-001). دو چیزِ متفاوت — و این تست هر دو را صریح ثبت می‌کند.
"""
import json
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-canonical")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import input_surface_policy as isp  # noqa: E402

CONTRACT = _OPS / "telegram_contract" / "TELEGRAM-ACCESS-CONTRACT.v1.json"
OWNER = 6150431610
GROUP = -1004475788460
TOPICS = {"lead": 11, "ziman": 12, "mining": 13}


def _contract() -> dict:
    return json.loads(CONTRACT.read_text("utf-8"))


def _msg(*, chat_id, chat_type, text="", thread=None, from_id=OWNER):
    m = {"chat": {"id": chat_id, "type": chat_type},
         "from": {"id": from_id}, "text": text}
    if thread is not None:
        m["message_thread_id"] = thread
    return {"message": m}


def _c(upd, role="outer"):
    return isp.classify(upd, bot_role=role, owner_id=OWNER, group_id=GROUP,
                        topics=TOPICS)


# ── تصویبِ ماشین‌خوان ───────────────────────────────────────────────────────
def t_the_contract_records_the_owner_ratification():
    d = _contract()
    assert d["status"] == "OWNER_RATIFIED_NOT_INTEGRATED", d["status"]
    r = d["owner_ratification"]
    assert r["decision"] == "A", r
    assert r["verdict_card"] == "VQ-TG-CONTRACT-001", r
    assert r["ratified_at"] == "2026-07-30", r


def t_ratification_is_explicitly_not_permission_to_go_live():
    """مهم‌ترین بندِ این فایل: تصویبِ مدل ≠ مجوزِ اتصال/ارسال/فلگ/ری‌استارت."""
    r = _contract()["owner_ratification"]
    scope = str(r["scope_of_ratification"])
    for word in ("اتصال", "ارسال", "فلگ", "ری‌استارت"):
        assert word in scope, f"دامنهٔ تصویب دربارهٔ «{word}» ساکت است"
    assert "NOT_LIVE" in str(r["runtime_status"]), r


def t_the_three_surfaces_are_exactly_the_ratified_ones():
    surfaces = _contract()["surfaces"]
    assert set(surfaces) == {"owner_outer_dm", "owner_inner_dm",
                             "legs_forum_group"}, sorted(surfaces)
    assert surfaces["legs_forum_group"]["role"] == "legs-only", surfaces


# ── رفتارِ کد باید با مدلِ مصوب بخواند ─────────────────────────────────────
def t_outer_dm_is_the_full_conversation_surface():
    d = _c(_msg(chat_id=OWNER, chat_type="private", text="هدفت چیه؟"))
    assert d["allow"] is True and d["mode"] == "core_conversation", d


def t_inner_dm_is_not_a_second_full_conversation_surface():
    """این دقیقاً تفاوتِ A با B است. اگر روزی B شد، این بند اولین قرمز است."""
    d = _c(_msg(chat_id=OWNER, chat_type="private",
                text="بیا دربارهٔ استراتژی حرف بزنیم"), role="inner")
    assert d["allow"] is False, d
    assert d["mode"] != "core_conversation", d
    assert d["redirect"] == "outer_dm", d


def t_the_group_is_legs_only_in_behaviour_not_just_in_the_document():
    denied = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11,
                     text="/budget"))
    assert denied["allow"] is False and denied["redirect"] == "outer_dm", denied
    allowed = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11,
                      text="وضعیتش چیه؟"))
    assert allowed["allow"] is True and allowed["mode"] == "leg_scoped", allowed


# ── صداقتِ وضعیت ───────────────────────────────────────────────────────────
def t_the_policy_is_ratified_but_still_not_wired():
    """«فیکس شد ≠ زنده شد» — این بند تا لحظهٔ اتصال قرمز نمی‌شود، ولی وقتی
    وصل شد **باید** به‌روز شود؛ وگرنه سند از واقعیت عقب می‌مانَد."""
    center = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    wired = "input_surface_policy" in center
    r = _contract()["owner_ratification"]
    if wired:
        assert "NOT_LIVE" not in str(r["runtime_status"]), \
            "به center وصل شده ولی قرارداد هنوز NOT_LIVE می‌گوید — سند را به‌روز کن"
    else:
        assert "NOT_LIVE" in str(r["runtime_status"]), r


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_canonical_access_model: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
