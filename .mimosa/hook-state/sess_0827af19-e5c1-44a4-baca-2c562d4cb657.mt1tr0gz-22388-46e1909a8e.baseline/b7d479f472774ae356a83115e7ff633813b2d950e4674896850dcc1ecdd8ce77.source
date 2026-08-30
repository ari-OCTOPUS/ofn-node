#!/usr/bin/env python3
"""Natural-language facade for Outer DM. Read-only/propose-only; no transport or execution."""
from __future__ import annotations

import re

from . import catalog, status, views

_CAPS = re.compile(r"(همه.*قابلیت|قابلیت.*نشان|چه.*توان|capabilit|چی.*بلدی)", re.I)
_GOAL = re.compile(r"(چه هدف|هدفت|هدف فعلی|الان.*هدف)", re.I)
_RUNTIME = re.compile(r"(شاهد.*runtime|واقعاً.*زنده|حقیقت.*زنده|کد است یا زنده|runtime)", re.I)
_BLOCK = re.compile(r"(چه.*مانع|بلاکر|گیر کرده|تکمیل.*نشد|چرا.*نمی)", re.I)
_DISC = re.compile(r"(کشف تازه|world discovery|کشف دنیا|امروز.*کشف)", re.I)
_HOME = re.compile(r"^(خانه|منو|شروع|help|راهنما|/start|/menu)\s*$", re.I)
_READ_MISSION = re.compile(r"(مأموریت|ماموریت).*(فقط.*خوان|read.?only)", re.I)
_NO_SEND = re.compile(r"(بدون.*اجازه.*نفرست|هیچ.*چیز.*نفرست|خودکار.*نفرست|do not send|don't send)", re.I)
_SEND = re.compile(r"(بفرست|ارسال|send|ایمیل|پیام بیرونی|پست کن)", re.I)


def handle(text: str) -> dict:
    q = str(text or "").strip()
    rows = catalog.discover()
    if not q or _HOME.search(q):
        return _reply("home", views.home(rows), keyboard=[
            [{"text": "🧩 قابلیت‌ها", "callback_data": "oc:caps"}],
            [{"text": "🎯 هدف فعلی", "callback_data": "oc:goal"},
             {"text": "🫀 حقیقت runtime", "callback_data": "oc:runtime"}],
            [{"text": "⛔ موانع", "callback_data": "oc:blockers"},
             {"text": "🌍 کشف دنیا", "callback_data": "oc:discovery"}],
        ])
    if _CAPS.search(q):
        return _reply("capabilities", views.capabilities(rows), keyboard=views.keyboard(rows))
    if _GOAL.search(q):
        return _reply("goal", status.current_goal())
    if _RUNTIME.search(q):
        return _reply("runtime", status.runtime_truth())
    if _BLOCK.search(q):
        return _reply("blockers", status.blockers())
    if _DISC.search(q):
        return _reply("discovery", status.discovery())
    if _NO_SEND.search(q):
        return _reply("safety-boundary",
            "✅ ثبتِ مکالمه‌ای: این رابط هیچ پیام، خرج یا اثر بیرونی انجام نمی‌دهد.\n"
            "هر ارسال واقعی باید action جدا، کارت bound، رأی تازه و receipt داشته باشد.",
            data={"status": "NO_EXTERNAL_EFFECT_WITHOUT_FRESH_OWNER_APPROVAL"})
    if _READ_MISSION.search(q):
        p = status.readonly_mission(q)
        return _reply("readonly-proposal",
            "📋 مأموریت فقط‌خواندنی آماده شد، ولی هنوز submit نشده.\n"
            f"نیت: {p['intent']}\nخرج: ۰ · اثر بیرونی: ۰\n"
            "برای اجرا باید به Mission/Action Bridge زنده متصل شود.", data=p)
    if _SEND.search(q):
        return _reply("owner-gate",
            "🔐 این درخواست اثر بیرونی دارد. این رابط آن را اجرا نمی‌کند.\n"
            "فقط می‌توانم یک draft و کارت رأی بسازم؛ ارسال واقعی نیازمند رأی تازه و receipt است.",
            data={"status": "BLOCKED_BY_OWNER", "external_effect": True})
    row = catalog.find(q, rows)
    if row:
        return _reply("capability", views.capability(row),
                      data={"capability_id": row["capability_id"], "status": row["status"]})
    return _reply("clarify",
        "من این درخواست را به‌طور امن به یک قابلیت مشخص وصل نکردم. یکی را بگو:\n"
        "• هدف فعلی\n• حقیقت runtime\n• موانع\n• World Discovery\n• قابلیت‌ها\n"
        "یا نتیجه، معیار موفقیت و خط قرمز را در یک جمله بنویس.",
        data={"status": "CLARIFY", "original": q[:300]})


def callback(data: str) -> dict:
    d = str(data or "")
    if d == "oc:home": return handle("خانه")
    if d == "oc:caps": return handle("همه قابلیت‌ها")
    if d == "oc:goal": return handle("هدف فعلی")
    if d == "oc:runtime": return handle("شاهد runtime")
    if d == "oc:blockers": return handle("موانع")
    if d == "oc:discovery": return handle("World Discovery")
    if d.startswith("oc:c:"):
        cid = d[5:]
        row = next((r for r in catalog.discover() if r["capability_id"] == cid), None)
        return _reply("capability", views.capability(row),
                      data={"capability_id": cid, "status": row["status"] if row else "UNKNOWN"})
    if d.startswith("oc:p:"):
        try: page = int(d[5:])
        except ValueError: page = 0
        rows = catalog.discover()
        return _reply("capabilities", views.capabilities(rows), keyboard=views.keyboard(rows, page))
    return _reply("blocked", "این دکمه شناخته‌شده نیست و هیچ عملی انجام نشد.",
                  data={"status": "BLOCKED_UNKNOWN_CALLBACK"})


def _reply(kind: str, text: str, *, keyboard=None, data=None) -> dict:
    return {"schema": "owner-console.reply.v1", "kind": kind, "text": str(text),
            "keyboard": list(keyboard or []), "data": dict(data or {}),
            "external_effect": False, "estimated_cost": 0,
            "send_attempted": False, "authorization": None}
