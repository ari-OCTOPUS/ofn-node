#!/usr/bin/env python3
"""content_studio.py — Content Studio v2: باتِ صبا (Project-F).

TELEGRAM-CONTENT-STUDIO-v2.md §۲: استودیوی محتوا برای صبا.
همه workflow-محور، compliant، propose-only. قواعدِ قفل‌شده:
  - فقط متادیتا/پلن/آنالیزِ تجمیعی — هرگز رسانه/هویت/PII فن
  - دوکلیده (صبا ثبت → آری تأیید → انتشارِ درون‌پلتفرم)
  - پرداخت فقط درون‌پلتفرم، صفر مذاکره
  - self-cert اجباری (faceless ✅ · فقط‌پا ✅ · بدون explicit ✅ · ۱۸+/رضایت ✅)
  - محدودهٔ صبا مقدمِ مطلق (یک‌ضربه halt)
  - geo-block ایران
  - بات/توکن/allowlistِ جدا

هیچ import از *_gate/chrono/money production. $0 آفلاین، stdlib-only.
ایزوله در پوشهٔ Project-F.
"""
from __future__ import annotations

import html
from dataclasses import dataclass, field

# قواعدِ قفل‌شده (self-cert checklist)
COMPLIANCE_CHECKS = [
    "faceless",        # بدون چهره
    "feet_only",       # فقط‌پا
    "no_explicit",     # بدون explicit
    "over_18",         # ۱۸+/رضایت
]


@dataclass
class DraftSubmission:
    """یک درفتِ ثبت‌شده. فقط متادیتا — صفر رسانه."""
    draft_id: str
    title: str                 # عنوانِ محتوا (نه رسانه)
    self_cert: dict            # {faceless: bool, feet_only: bool, ...}
    status: str = "pending"    # pending → approved (by آری) → published (درون‌پلتفرم)
    ppv_tier: str | None = None   # wall | low | mid | premium
    price_hint: float = 0.0


@dataclass
class ContentCalendar:
    """تقویمِ محتوا. تمِ فصلی + اسلاتِ ماهانه."""
    season: str = "summer"
    slots: list[dict] = field(default_factory=list)


@dataclass
class PPVPlan:
    """پلنِ PPV سه‌لایه."""
    wall_pct: float = 0.55      # ~۵۵٪ روی wall
    tiers: dict = field(default_factory=lambda: {
        "low": {"price": 5, "desc": "low-ticket"},
        "mid": {"price": 15, "desc": "mid-tier"},
        "premium": {"price": 50, "desc": "premium"},
    })


@dataclass
class AggregateAnalytics:
    """آنالیزِ تجمیعی. صفر PII — فقط KPIهای aggregate."""
    churn_rate: float = 0.27     # هدف ۲۵-۳۰٪
    arpu: float = 60.0           # $۴۰-۸۰
    ppv_unlock_rate: float = 0.28  # ۲۲-۳۵٪
    retention_30d: float = 0.65
    segments: dict = field(default_factory=lambda: {
        "vip": 0.05, "regular": 0.25, "lurker": 0.70})


class ContentStudio:
    """باتِ صبا. propose-only، ایزوله. خروجی = HTML غنی.
    دوکلیده: درفت → آری تأیید → انتشار."""

    def __init__(self):
        self._drafts: list[DraftSubmission] = []
        self._halted = False   # محدودهٔ صبا: یک‌ضربه halt

    def halt(self) -> str:
        """محدودهٔ صبا مقدم — یک‌ضربه halt."""
        self._halted = True
        return "✋ <b>متوقف شد</b>\nمحدودهٔ صبا مقدمِ مطلق. بات متوقف است."

    @property
    def is_halted(self) -> bool:
        return self._halted

    # ─── منوی اصلی ──────────────────────────────────────────────────────────────
    def main_menu(self) -> str:
        if self._halted:
            return self.halt()
        return ("🎬 <b>استودیوی محتوا</b> — Project-F\n"
                "<i>دکمه‌ها را برای کار انتخاب کن.</i>")

    # ─── 📤 ثبتِ درفت (با self-cert) ─────────────────────────────────────────────
    def submit_draft(self, title: str, self_cert: dict | None = None,
                     ppv_tier: str | None = None,
                     price_hint: float = 0.0) -> dict:
        """ثبتِ درفت با self-cert اجباری. رسانهٔ خام رد نمی‌شود.
        خروجی: {ok, draft_id, status}. اگر self-cert ناقص → fail-closed."""
        if self._halted:
            return {"ok": False, "error": "halted"}
        # self-cert اجباری
        cert = self_cert or {}
        missing = [c for c in COMPLIANCE_CHECKS if not cert.get(c)]
        if missing:
            return {"ok": False, "error": f"self-cert ناقص: {missing}"}
        draft_id = f"DRAFT-{len(self._drafts) + 1:04d}"
        draft = DraftSubmission(draft_id=draft_id, title=title,
                                self_cert=cert, ppv_tier=ppv_tier,
                                price_hint=price_hint)
        self._drafts.append(draft)
        return {"ok": True, "draft_id": draft_id, "status": "pending"}

    def drafts_html(self) -> str:
        """لیستِ درفت‌ها با وضعیت."""
        if not self._drafts:
            return "📋 <b>بریف‌ها</b>\n──────────\n<i>هنوز درفتی ثبت نشده.</i>"
        lines = ["📋 <b>بریف‌ها</b>", "──────────"]
        for d in self._drafts:
            icon = {"pending": "⏳", "approved": "✅", "published": "📤"}.get(d.status, "❓")
            lines.append(f"{icon} {d.draft_id} · {d.title} · {d.status}")
        return "\n".join(lines)

    # ─── 💡 پلنِ PPV ─────────────────────────────────────────────────────────────
    def ppv_plan_html(self) -> str:
        """§۲: پلنِ PPV سه‌لایه + پیشنهادِ قیمت (draft)."""
        plan = PPVPlan()
        lines = ["💡 <b>پلنِ PPV</b>", "──────────"]
        lines.append(f"📊 wall: ~{plan.wall_pct*100:.0f}% · PPV: ~{(1-plan.wall_pct)*100:.0f}%")
        for tier, cfg in plan.tiers.items():
            lines.append(f"  {tier}: ${cfg['price']} ({cfg['desc']})")
        lines.append("<i>پیشنهادِ قیمت — آری تأیید می‌کند.</i>")
        return "\n".join(lines)

    # ─── 📈 آنالیزِ تجمیعی ──────────────────────────────────────────────────────
    def analytics_html(self) -> str:
        """§۲: KPIهای تجمیعی. صفر PII فن."""
        a = AggregateAnalytics()
        return (f"📈 <b>آنالیز</b>\n──────────\n"
                f"churn: {a.churn_rate*100:.0f}% (هدف ۲۵-۳۰)\n"
                f"ARPU: ${a.arpu:.0f}\n"
                f"PPV unlock: {a.ppv_unlock_rate*100:.0f}%\n"
                f"retention 30d: {a.retention_30d*100:.0f}%\n"
                f"سگمنت: VIP {a.segments['vip']*100:.0f}% · "
                f"معمولی {a.segments['regular']*100:.0f}% · "
                f"lurker {a.segments['lurker']*100:.0f}%\n"
                f"<i>تجمیعی — صفر PII.</i>")

    # ─── 🔒 قواعد + ✋ محدوده ───────────────────────────────────────────────────
    def rules_html(self) -> str:
        """چک‌لیستِ قفل‌شده."""
        return ("🔒 <b>قواعدِ قفل‌شده</b>\n──────────\n"
                "✅ faceless (بدون چهره)\n"
                "✅ فقط‌پا\n"
                "✅ بدون explicit\n"
                "✅ ۱۸+/رضایت\n"
                "✅ پرداختِ درون‌پلتفرم\n"
                "✅ geo-block ایران\n"
                "✅ دوکلیده (صبا→آری)\n"
                "<i>ردِ هر قاعده = drop.</i>")

    def scope_html(self) -> str:
        """محدودهٔ صبا."""
        return ("✋ <b>محدودهٔ من</b>\n──────────\n"
                "محدودهٔ صبا مقدمِ مطلق.\n"
                "یک‌ضربه halt در هر زمان.\n"
                "<i>برای توقف: /halt</i>")

    # ─── 🔎 ترند/ایده ───────────────────────────────────────────────────────────
    def trend_feed_html(self) -> str:
        """فیدِ ترند/ایده. AI-draft، human-gated."""
        return ("🔎 <b>ترند/ایده</b>\n──────────\n"
                "📌 ترندِ نیش: faceless-feet\n"
                "📌 زمانِ بهینه: evening AEST\n"
                "📌 ایدهٔ کپشن: (AI-draft — نیاز به ویرایش)\n"
                "<i>human-gated — هیچ‌چیز خودکار.</i>")

    # ─── 🗓 تقویم ────────────────────────────────────────────────────────────────
    def calendar_html(self) -> str:
        """§۲: تقویم — تمِ فصلی + اسلاتِ ماهانه + پیشنهادِ زمان. هیچ‌چیز خودکار publish نمی‌شود."""
        cal = ContentCalendar()
        return ("🗓 <b>تقویم</b>\n──────────\n"
                f"تمِ فصل: {cal.season}\n"
                "اسلاتِ ماهانه (پیشنهاد — آری تأیید می‌کند):\n"
                "  • هفتهٔ ۱: تیزر / wall\n"
                "  • هفتهٔ ۲: PPV low\n"
                "  • هفتهٔ ۳: PPV mid\n"
                "  • هفتهٔ ۴: premium + retention\n"
                "⏰ زمانِ بهینه: evening AEST\n"
                "<i>هیچ‌چیز خودکار publish نمی‌شود.</i>")
