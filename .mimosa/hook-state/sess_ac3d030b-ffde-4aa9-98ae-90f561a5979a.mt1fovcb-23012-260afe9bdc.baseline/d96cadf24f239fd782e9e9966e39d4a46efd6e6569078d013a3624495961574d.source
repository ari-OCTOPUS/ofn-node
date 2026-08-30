#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تستِ doctor_link — پلِ outboxِ دکترِ اختاپوس به مرکزِ تلگرام.

هرمتیک: ORG_ROOT **قبل از هر import** به یک درختِ موقت pin می‌شود (درسِ
shadow-suite: بدونِ pin، ماژول به درختِ زنده resolve می‌شود و تست دیسکِ زنده
را می‌خواند/می‌نویسد). هیچ شبکه‌ای صدا زده نمی‌شود — client و feeder ساختگی‌اند.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="doctor-link-t-")
os.environ["ORG_ROOT"] = _TMP                      # قبل از importِ opslib/doctor_link
os.environ.pop("OPS_DIR", None)
os.environ.pop("OCTOPUS_DOCTOR_TOPIC_ID", None)
os.environ["OCTOPUS_WIRE_DOCTOR_TG"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "telegram_center"))
import doctor_link  # noqa: E402

PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name}" + (f"  — {detail}" if detail else ""))


class FakeClient:
    def __init__(self):
        self.sent = []
        self._mid = 100

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self._mid += 1
        self.sent.append({"text": text, "topic_id": topic_id,
                          "keyboard": keyboard, "mid": self._mid})
        return self._mid


class FakeCenter:
    def __init__(self):
        self._client = FakeClient()
        self.toasts = []

    def _answer(self, cbq, text):
        self.toasts.append(text)


def _card(mission, gate, buttons=True):
    payload = {"chat_id": "", "text": f"کارتِ {gate} برای {mission}",
               "parse_mode": "Markdown"}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": [[
            {"text": "✅", "callback_data": f"ok:{gate}:{mission}"},
            {"text": "❌", "callback_data": f"no:{gate}:{mission}"}]]}
    return {"ts": 1.0, "mission_id": mission, "gate": gate, "payload": payload}


def main() -> int:
    print("=" * 60)
    print("doctor_link — پلِ outboxِ دکتر به مرکزِ تلگرام")
    print("=" * 60)

    check("ORG_ROOT به درختِ موقت pin شده — نه درختِ زنده",
          str(doctor_link.DOCTOR_ROOT).startswith(_TMP))

    doctor_link.OUTBOX.parent.mkdir(parents=True, exist_ok=True)
    with doctor_link.OUTBOX.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_card("m-1", "intent"), ensure_ascii=False) + "\n")
        fh.write(json.dumps(_card("m-2", "diff", buttons=False),
                            ensure_ascii=False) + "\n")

    c = FakeCenter()

    # ── فلگ خاموش = no-op مطلق
    out = doctor_link.beat(c)
    check("فلگ خاموش ⇒ هیچ ارسالی", out.get("reason") == "flag-off"
          and not c._client.sent)

    # ── فلگ روشن: دو کارتِ صف‌شده فرستاده می‌شوند
    os.environ["OCTOPUS_WIRE_DOCTOR_TG"] = "1"
    out = doctor_link.beat(c)
    check("دو کارتِ نو فرستاده شد", out["sent"] == 2, str(out))
    check("کارتِ رأی‌دار keyboard دارد و کارتِ قرمز ندارد",
          c._client.sent[0]["keyboard"] is not None
          and c._client.sent[1]["keyboard"] is None)
    check("cursor نوشته شد (restart-safe)", doctor_link.CURSOR.exists())

    # ── beatِ دوم بدونِ رکوردِ نو ⇒ صفر ارسال
    out = doctor_link.beat(c)
    check("beatِ بعدی بدونِ رکوردِ نو ⇒ صفر ارسال", out["sent"] == 0)

    # ── رکوردِ تکراری (همان mission:gate دوباره append شود) ⇒ dedup
    with doctor_link.OUTBOX.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_card("m-1", "intent"), ensure_ascii=False) + "\n")
    out = doctor_link.beat(c)
    check("کارتِ هم‌کلید (mission:gate) دوباره فرستاده نمی‌شود",
          out["sent"] == 0 and out["skipped"] >= 1)

    # ── سقفِ روزانه
    cur = json.loads(doctor_link.CURSOR.read_text("utf-8"))
    cur["day_count"] = doctor_link.MAX_PER_DAY
    doctor_link.CURSOR.write_text(json.dumps(cur), encoding="utf-8")
    with doctor_link.OUTBOX.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_card("m-3", "intent"), ensure_ascii=False) + "\n")
    out = doctor_link.beat(c)
    check("سقفِ روزانه ⇒ skip، نه ارسال", out["sent"] == 0 and out["skipped"] >= 1)

    # ── بدونِ client ⇒ fail-soft
    class NoClient:
        _client = None
    check("centerِ بی‌client ⇒ no-client، نه استثنا",
          doctor_link.beat(NoClient()).get("reason") == "no-client")

    # ── تشخیصِ callbackِ دکتر: فقط سه‌تکه با gateِ شناخته
    check("ok:intent:m-1 مالِ دکتر است", doctor_link.is_doctor_callback("ok:intent:m-1"))
    check("no:diff:m-9 مالِ دکتر است", doctor_link.is_doctor_callback("no:diff:m-9"))
    check("ok:123 (کارتِ تصمیمِ مرکز) مالِ دکتر نیست",
          not doctor_link.is_doctor_callback("ok:123"))
    check("later:intent:m-1 مالِ دکتر نیست",
          not doctor_link.is_doctor_callback("later:intent:m-1"))
    check("ok:approve:x (gateِ ناشناخته) مالِ دکتر نیست",
          not doctor_link.is_doctor_callback("ok:approve:x"))

    # ── handle_callback: مصرف + toast؛ شکستِ feeder هم مصرف می‌شود (نه سقوط به fallback)
    cbq = {"id": "cb1", "data": "ok:intent:m-1", "from": {"id": 42}}
    got = doctor_link.handle_callback(c, cbq, feeder=lambda q: True)
    check("رأیِ دکتر مصرف شد و toastِ موفق آمد",
          got is True and c.toasts and "ثبت شد" in c.toasts[-1])
    got = doctor_link.handle_callback(c, cbq, feeder=lambda q: False)
    check("شکستِ feeder ⇒ باز هم مصرف (fallback رأیِ بی‌ربط ثبت نکند) + toastِ خطا",
          got is True and "نرسید" in c.toasts[-1])
    check("callbackِ غیرِ دکتر مصرف نمی‌شود",
          doctor_link.handle_callback(c, {"data": "ok:123"}) is False)
    os.environ["OCTOPUS_WIRE_DOCTOR_TG"] = "0"
    check("فلگ خاموش ⇒ حتی رأیِ سه‌تکه هم مصرف نمی‌شود",
          doctor_link.handle_callback(c, cbq) is False)

    # ── (۲۰۲۶-۰۷-۳۱، رفعِ outer-11/inner-1/group-8) وقتی center ِ_route_send
    # دارد، کارت از مسیرِ روتر می‌رود (doctor-intent/doctor-diff → DM)، نه از
    # client.send مستقیم (که به گروه می‌افتاد). FakeCenter با _route_send:
    class RoutingCenter:
        def __init__(self):
            self.routed = []
        def _route_send(self, stream, text, *, cfg=None, keyboard=None, pin=False):
            self.routed.append({"stream": stream, "text": text,
                                "keyboard": keyboard})
            return 200 + len(self.routed)
    os.environ["OCTOPUS_WIRE_DOCTOR_TG"] = "1"
    rc = RoutingCenter()
    doctor_link.OUTBOX.parent.mkdir(parents=True, exist_ok=True)
    # یک فایلِ تازهٔ outbox + cursor صفر (مستقل از stateِ تست‌های قبلی)
    doctor_link.OUTBOX.write_text(
        json.dumps(_card("m-route", "intent"), ensure_ascii=False) + "\n",
        encoding="utf-8")
    if doctor_link.CURSOR.exists():
        doctor_link.CURSOR.unlink()
    out = doctor_link.beat(rc)
    check("center با _route_send ⇒ کارت از روتر می‌رود (نه client.send مستقیم)",
          out["sent"] == 1 and rc.routed and rc.routed[0]["stream"] == "doctor-intent",
          str(out) + " routed=" + str(rc.routed))
    check("کارتِ doctor از طریقِ روتر keyboard نگه می‌دارد",
          rc.routed and rc.routed[0]["keyboard"] is not None)
    os.environ["OCTOPUS_WIRE_DOCTOR_TG"] = "0"

    print("\n" + "=" * 60)
    print(f"نتیجه: {len(PASS)} سبز · {len(FAIL)} قرمز")
    for f in FAIL:
        print(f"  ❌ {f}")
    print("=" * 60)
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
