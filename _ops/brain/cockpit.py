#!/usr/bin/env python3
"""cockpit.py — Brain Cockpit v1: کاکپیتِ چندپروژه‌ایِ آری.

TELEGRAM-BRAIN-COCKPIT-v1.md §۲: آری = meta-approver + استراتژِ همهٔ پاها.
کاکپیت باید در یک‌نگاه بدهد: (الف) صفِ تأییدِ تجمیعی، (ب) وضعیتِ هر پا،
(ج) سلامتِ ارگانیسم، (د) نمای پول، (ه) آلارمِ RED، (و) بریفِ روز.

خطوطِ قرمز (§۴): approve تنها مسیرِ settle (TINV-7) · توکن env-only ·
Project-F فقط «درفت در صف» (صفر رسانه/هویت) · money قفل · propose-only.

هیچ import از *_gate/chrono/money production. $0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


# ۶ پایِ رسمی
LEGS = [
    {"id": "lead-naghshi", "icon": "🎯", "name": "Lead-نقاشی", "color": "🟢", "desc": "درآمد#۱ · lead فعال"},
    {"id": "project-f", "icon": "🎬", "name": "Project-F", "color": "🟡", "desc": "validation · درفت در صف"},
    {"id": "crypto", "icon": "📈", "name": "Crypto", "color": "🔵", "desc": "read-only · بریفِ روز"},
    {"id": "accounting", "icon": "🧮", "name": "Accounting", "color": "🔵", "desc": "گزارش"},
    {"id": "mining", "icon": "⛏", "name": "Mining", "color": "⚪", "desc": "scouting"},
    {"id": "ziman", "icon": "🖼", "name": "Ziman", "color": "⚪", "desc": "پلن"},
]


@dataclass
class ApprovalItem:
    """یک آیتم در صفِ تأییدِ تجمیعی."""
    project: str
    action: str
    amount_aud: float
    guard: str
    effect_id: str = ""
    status: str = "pending"   # pending | approved | denied


class BrainCockpit:
    """کاکپیتِ آری. خروجی = HTML غنی (propose-only، shadow).
    منبعِ داده: state/*.json (read-only) + صفِ تأیید (advisory).

    P-L6: صفِ تأیید یک **نمایِ فقط‌خواندنی** است، نه یک منبعِ حقیقتِ موازی.
    اگر `effect_status_fn` تزریق شود، وضعیتِ هر آیتم از منبعِ authoritative
    (gateِ تک‌گلوگاه) مشتق می‌شود و هرگز خودسرانه «approved» نمی‌شود. بدونِ آن،
    صف صریحاً به‌عنوانِ shadow برچسب می‌خورد. cockpit هرگز settle نمی‌کند."""

    def __init__(self, state_dir: str | Path | None = None,
                 effect_status_fn=None):
        """effect_status_fn: callable اختیاری `(effect_id: str) -> str | None`.
        منبعِ authoritative وضعیتِ effect (مثلاً متدِ status_of روی گیتِ تک‌گلوگاه).
        اگر None → صفِ تأیید به‌عنوانِ shadow نمایش داده می‌شود و هرگز
        «approved/settled» ادعا نمی‌کند."""
        self._state_dir = Path(state_dir) if state_dir else (
            Path(__file__).resolve().parents[1] / "state")
        self._approval_queue: list[ApprovalItem] = []
        self._effect_status_fn = effect_status_fn

    @property
    def is_shadow(self) -> bool:
        """آیا صف بدونِ منبعِ authoritative است؟ (shadow = ممکن است واگرا باشد)."""
        return self._effect_status_fn is None

    def _reconcile_effect_status(self) -> None:
        """وضعیتِ هر آیتمِ دارایِ effect_id را از منبعِ authoritative مشتق کن.
        P-L6: این تنها راهی است که آیتمِ cockpit «approved» می‌شود — از منبعِ
        authoritative، نه از تصمیمِ خودسرانهٔ cockpit. بدونِ status_fn → بدونِ
        تغییر (shadow). status همیشه به‌طور کامل از منبع مشتق می‌شود، تا حتی
        دستکاریِ دستیِ محلی هم برگردانده شود به حقیقتِ منبع.

        نگاشت: settled/releasable → approved (تأییدشده/آزادشده)
                refused          → denied
                pending/None/ناموجود → pending (صریحاً، حتی اگر محلی چیز دیگری باشد)"""
        if self._effect_status_fn is None:
            return   # shadow: هیچ ادعایی بدونِ منبع
        for item in self._approval_queue:
            if not item.effect_id:
                continue
            try:
                real = self._effect_status_fn(item.effect_id)
            except Exception:  # noqa: BLE001 — منبع fail-soft
                continue
            if real in ("settled", "releasable"):
                item.status = "approved"
            elif real == "refused":
                item.status = "denied"
            else:
                item.status = "pending"   # pending/None/ناموجود — صریحاً بازنویسی

    def _read_json(self, name: str) -> dict:
        p = self._state_dir / name
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _read_mode(self) -> str:
        """mode color از rhythm (fallback 🟢)."""
        try:
            import sys as _sys
            rh_dir = Path(__file__).resolve().parents[1] / "chrono_rhythm"
            if str(rh_dir) not in _sys.path:
                _sys.path.insert(0, str(rh_dir))
            from rhythm import Rhythm
            rh = Rhythm()
            rh.step(readiness=0.6, stress=0.2, novelty=0.3, sigma=0.5)
            s = rh.state
            icons = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
            return f"{icons.get(s.mode_color, '🟢')} {s.mode_color}"
        except Exception:  # noqa: BLE001
            return "🟢 GREEN"

    # ─── منوی اصلی ──────────────────────────────────────────────────────────────
    def main_menu(self) -> str:
        """§۲: منوی اصلی با inline-keyboard."""
        mode = self._read_mode()
        n = len([a for a in self._approval_queue if a.status == "pending"])
        return (f"🧠 <b>مغزِ اختاپوس</b> — کاکپیتِ آری · {mode}\n"
                f"<i>دکمه‌ها را برای کار انتخاب کن.</i>\n"
                f"{'🔔 تأییدِ منتظر: ' + str(n) if n > 0 else '✅ صفِ تأیید خالی'}")

    # ─── 🐙 ارگانیسم ────────────────────────────────────────────────────────────
    def organism_status(self) -> str:
        """§۲: وضعیتِ ارگانیسم (قلب/گیت/دکتر/germline/affinent)."""
        org = self._read_json("ORGANISM-STATE.json")
        mode = self._read_mode()
        if not org:
            return f"🐙 ارگانیسم · {mode}\n<i>هنوز روشن نشده.</i>"
        month = org.get("month") or {}
        sigma = self._read_json("replication-latest.json").get("sigma", {})
        sigma_eff = sigma.get("sigma_effective", 0) if isinstance(sigma, dict) else 0
        lag = org.get("germline_lag_h", "—")
        return (f"🐙 ارگانیسم · {mode}\n──────────\n"
                f"📊 σ {sigma_eff} · تعارض {len(org.get('conflicts') or [])}\n"
                f"💾 germline: {lag}h\n"
                f"💵 خرجِ ماه: AU${month.get('aud', 0):.2f}\n"
                f"<i>فقط‌خواندنی.</i>")

    # ─── ✅ صفِ تأییدِ تجمیعی ──────────────────────────────────────────────────
    def approval_queue_html(self) -> str:
        """§۲: صفِ تأیید از همهٔ پاها. آری تنها نقطهٔ human-append.
        P-L6: ابتدا وضعیت از منبعِ authoritative همگام می‌شود (اگر موجود)،
        تا هرگز با گیتِ تک‌گلوگاه واگرا نگردد. در غیرِ این‌صورت shadow برچسب می‌خورد."""
        self._reconcile_effect_status()   # تازه‌سازیِ وضعیت از منبعِ حقیقت
        shadow_tag = " 👤<i>shadow</i>" if self.is_shadow else ""
        pending = [a for a in self._approval_queue if a.status == "pending"]
        if not pending:
            return f"✅ <b>صفِ تأیید</b>{shadow_tag}\n──────────\n<i>صف خالی است.</i>"
        lines = [f"✅ <b>صفِ تأییدِ تجمیعی</b>{shadow_tag}", "──────────"]
        for i, a in enumerate(pending, 1):
            lines.append(f"{i}. [{a.project}] {a.action} · AU${a.amount_aud:.2f} · {a.guard}")
        lines.append("<i>تأیید = human-append (TINV-7).</i>")
        return "\n".join(lines)

    def add_approval(self, project: str, action: str, amount_aud: float,
                     guard: str = "pending", effect_id: str = "") -> None:
        """افزودن به صفِ تأیید (advisory)."""
        self._approval_queue.append(ApprovalItem(
            project=project, action=action, amount_aud=amount_aud,
            guard=guard, effect_id=effect_id))

    # ─── 📊 وضعیتِ ۶ پا ─────────────────────────────────────────────────────────
    def legs_status(self) -> str:
        """§۲: وضعیتِ ۶ پا، هرکدام یک‌خط."""
        lines = ["📊 <b>پروژه‌ها</b>", "──────────"]
        for leg in LEGS:
            lines.append(f"{leg['icon']} {leg['name']} {leg['color']} {leg['desc']}")
        return "\n".join(lines)

    # ─── 💵 پول (shadow) ────────────────────────────────────────────────────────
    def money_shadow(self) -> str:
        """§۲: نمای پولِ shadowِ تجمیعی. money-gate 🔒 تا ۲۰۲۶-۰۷-۲۱."""
        org = self._read_json("ORGANISM-STATE.json")
        month = org.get("month") or {}
        today = org.get("today") or {}
        return ("💵 <b>پول (shadow)</b>\n──────────\n"
                f"خرجِ امروز: US${today.get('usd', 0):.4f}\n"
                f"خرجِ ماه: AU${month.get('aud', 0):.2f}\n"
                f"🔒 money-gate قفل تا ۲۰۲۶-۰۷-۲۱\n"
                f"<i>shadow فقط — پولِ واقعی پشتِ گیت.</i>")

    # ─── 🔔 آلارم‌ها ─────────────────────────────────────────────────────────────
    def alarms(self) -> str:
        """§۲: فقط آلارم‌های RED (safety breach · cost-cap · germline کهنه)."""
        org = self._read_json("ORGANISM-STATE.json")
        alarms = []
        if org.get("frozen"):
            alarms.append("❄️ FREEZE فعال")
        if org.get("halted"):
            alarms.append(f"⏹ halted: {org['halted']}")
        lag_alert = org.get("germline_alert", "")
        if lag_alert == "ERROR":
            alarms.append(f"🔴 germline کهنه/غایب")
        if org.get("conflicts"):
            alarms.append(f"⚠️ {len(org['conflicts'])} تعارض")
        if not alarms:
            return "🔔 <b>آلارم‌ها</b>\n──────────\n✅ هیچ آلارمِ RED نیست."
        return "🔔 <b>آلارم‌ها</b>\n──────────\n" + "\n".join(alarms)

    # ─── 📅 بریفِ روز ───────────────────────────────────────────────────────────
    def daily_brief(self) -> str:
        """§۲: ۳ کارِ مهم + چه چیزی منتظرِ تأیید."""
        n_pending = len([a for a in self._approval_queue if a.status == "pending"])
        return (f"📅 <b>بریفِ روز</b>\n──────────\n"
                f"📋 تأییدِ منتظر: {n_pending}\n"
                f"🎯 تمرکز: اولین لیدِ paper (Lead-نقاشی)\n"
                f"🔒 پول قفل تا ۲۱-۰۷\n"
                f"<i>بریف از state + ledger.</i>")
