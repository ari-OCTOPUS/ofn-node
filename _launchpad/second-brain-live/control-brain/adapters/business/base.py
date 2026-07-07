# -*- coding: utf-8 -*-
"""پایه‌ی پلاگینی آداپترهای بیزنس — پیاده‌سازی عمومی دو رکن (فاز ۳).

هر بیزنس فقط یک BusinessConfig می‌دهد (+ در صورت نیاز override نقطه‌ای).
بیزنس چهارم/پنجم = یک فایل جدید در همین پوشه — Core دست نمی‌خورد.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import List

from core.contracts import Brief, Feedback, OutboxMessage, OwnerInteractionEngine, ResearchEngine

_BRIEF_FORMAT = (
    "خروجی را دقیقاً با همین قالب بده (هر مورد یک خط، بدون توضیح اضافه):\n"
    "عنوان: <یک خط>\nفرصت: <۲-۳ جمله>\nچرا: <چرا الان و برای این بیزنس>\n"
    "اقدام: <یک اقدام مشخص و کوچک این هفته>\nمنبع: <URL یا 'تحلیل داخلی'>"
)


@dataclass
class PersonalGenome:
    """ژنوم شخصیِ یک بخش — DNA منحصربه‌فردش. کنار ژنوم اصلیِ مشترک (core/ + contracts).

    فیلدهای «هویت/استراتژی» از BusinessConfig نسل قبل به ارث رسیده‌اند (سازگاری کامل).
    فیلدهای «شخصیت/استقلال» نو هستند و همه default دارند → کد قدیمی بدون تغییر کار می‌کند.
    قیدهای استقلال (autonomy/budget_share/privacy_class) زیرِ سقفِ ژنوم اصلی اجرا می‌شوند.
    """
    # — هویت (ژنوم پایه) —
    id: str                       # همان id در projects.yaml
    name: str
    owner_ref: str                # id گیرنده در users.yaml (mom/admin/saba)
    owner_name: str
    market: str                   # بازار/جغرافیا برای جستجو
    tone: str                     # لحن پیام رکن B (سازگاری؛ voice جایگزین غنی‌ترش است)
    topics: List[str] = field(default_factory=list)   # زوایای تحقیق (چرخشی + وزن‌دار)
    context_note: str = ""        # واقعیت‌های ثابت بیزنس (ظرفیت، قواعد، قیود)
    # — شخصیت (نو: هویت صریح، جایگزینِ خودشیفتگی) —
    persona: str = ""             # سیستم‌پرامپت هویتِ رکن A؛ خالی = پیش‌فرض حرفه‌ای متواضع
    voice: str = ""               # لحن رکن B؛ خالی = همان tone
    values: List[str] = field(default_factory=list)   # خط‌قرمز/سبک برند (مثلاً ToS-safe)
    # — استراتژی (نو) —
    goals: List[str] = field(default_factory=list)    # اهداف درآمدی/رشد این بخش
    channels: List[str] = field(default_factory=lambda: ["telegram"])  # آماده برای whatsapp/instagram
    # — استقلال و حکومت (نو؛ زیر سقف ژنوم اصلی) —
    autonomy: str = "propose_only"   # propose_only | bounded_auto | status_only
    budget_share: float = 0.0        # سهم سقف روزانه (جمع همه ≤ ۱.۰)
    privacy_class: str = "normal"    # normal | sensitive (→ هرگز Fugu، مثل Project-F/حسابداری)
    evolution_optin: bool = False    # مغز تکاملی حق پیشنهاد جهش روی این ژنوم دارد؟
    kpis: List[str] = field(default_factory=list)     # سنجهٔ «برازندگی» این بخش

    def __post_init__(self):
        if not self.voice:
            self.voice = self.tone
        if not self.persona:
            self.persona = (f"همکار ارشد درآمدزایی «{self.name}» — حرفه‌ای، کمک‌کننده، "
                            f"متواضع با اعتمادبه‌نفس. بدون خودستایی.")


# سازگاری عقب‌رو: کد قدیمی هنوز BusinessConfig(...) می‌سازد — همان کلاس است.
BusinessConfig = PersonalGenome


def parse_brief(business: str, text: str) -> Brief:
    """پاسخ LLM → Brief. سخت‌گیر نیست: هر فیلد پیدا نشد، fallback امن."""
    def grab(label: str, default: str = "") -> str:
        m = re.search(rf"^{label}\s*[:：]\s*(.+)$", text, re.M)
        return m.group(1).strip() if m else default

    title = grab("عنوان") or (text.strip().splitlines() or ["فرصت جدید"])[0][:80]
    return Brief(
        business=business,
        title=title[:120],
        opportunity=grab("فرصت", text.strip()[:400]),
        why=grab("چرا", "—"),
        action=grab("اقدام", "—"),
        source=grab("منبع", "تحلیل داخلی"),
    )


class GenericResearchEngine(ResearchEngine):
    """رکن A عمومی: جستجوی وب (Tavily) + LLM (DeepSeek) + حلقه یادگیری وزن موضوع‌ها."""

    def __init__(self, cfg: BusinessConfig, gateway, memory):
        self.cfg = cfg
        self.business = cfg.id
        self.gw = gateway
        self.mem = memory

    # --- وزن موضوع‌ها (یادگیری) ---
    def _weights(self) -> dict:
        rows = self.mem.knowledge_search("", business=self.cfg.id, n=50)
        for r in rows:
            if r.startswith("WEIGHTS:"):
                try:
                    return json.loads(r[8:])
                except Exception:  # noqa: BLE001
                    pass
        return {}

    def _save_weights(self, w: dict) -> None:
        self.mem.knowledge_add("WEIGHTS:" + json.dumps(w, ensure_ascii=False),
                               tag=f"weights:{self.cfg.id}", business=self.cfg.id)

    def _pick_topic(self) -> str:
        if not self.cfg.topics:
            return f"راه‌های افزایش درآمد {self.cfg.name}"
        w = self._weights()
        ranked = sorted(self.cfg.topics, key=lambda t: w.get(t, 0), reverse=True)
        # چرخش روزانه بین ۳ موضوع برتر تا تنوع بماند
        return ranked[date.today().toordinal() % min(3, len(ranked))]

    def gather_context(self) -> str:
        fbs = self.mem.feedback_for(self.cfg.id, n=10)
        fb_txt = "؛ ".join(("👍" if f.useful else "👎") + (f" {f.note}" if f.note else "")
                           for f in fbs) or "هنوز بازخوردی نیست"
        recent = [b.title for b in self.mem.recent_briefs(4, business=self.cfg.id)]
        return (f"بیزنس: {self.cfg.name} — بازار: {self.cfg.market}\n"
                f"قیود ثابت: {self.cfg.context_note}\n"
                f"بازخوردهای اخیر ادمین: {fb_txt}\n"
                f"بریف‌های اخیر (تکرار نکن): {recent}")

    def run(self, context: str) -> Brief:
        topic = self._pick_topic()
        web = self.gw.search(f"{topic} {self.cfg.market} {date.today().year}", business=self.cfg.id)
        web_txt = "\n".join(f"- {r['title']}: {r['content'][:250]} ({r['url']})"
                            for r in web[:4]) or "نتیجه وب در دسترس نبود — از تحلیل داخلی استفاده کن"
        prompt = (f"{context}\n\nموضوع تحقیق امروز: {topic}\n\nیافته‌های وب:\n{web_txt}\n\n"
                  f"یک فرصت درآمدزایی مشخص و عملی برای این بیزنس پیشنهاد بده. {_BRIEF_FORMAT}")
        out = self.gw.llm(prompt, system=self.cfg.persona + " تحلیل‌گر کسب‌وکارهای کوچک استرالیا؛ عملی و بی‌تعارف.",
                          business=self.cfg.id, use_cache=False)
        brief = parse_brief(self.cfg.id, out)
        self.mem.add_brief(brief)
        self.mem.knowledge_add(f"{brief.title} → {brief.action}", tag="brief-digest",
                               business=self.cfg.id, source=brief.source)
        return brief

    def learn(self, feedbacks) -> None:
        # محدودیت v1 (یافتهٔ code-review): وزن به موضوعِ فعلی نسبت داده می‌شود نه موضوعِ
        # بریفِ بازخوردخورده — تقریب قابل‌قبول تا وقتی topic روی خود Brief ذخیره شود (فاز ۵).
        w = self._weights()
        topic = self._pick_topic()
        for f in feedbacks:
            w[topic] = w.get(topic, 0) + (1 if f.useful else -1)
        self._save_weights(w)


class GenericOwnerInteraction(OwnerInteractionEngine):
    """رکن B عمومی: بریف → پیام گرم برای صاحب بیزنس؛ همیشه از صف تأیید (ADR-006)."""

    channel = "telegram"

    def __init__(self, cfg: BusinessConfig, gateway, memory):
        self.cfg = cfg
        self.business = cfg.id
        self.gw = gateway
        self.mem = memory

    def compose(self, brief: Brief) -> OutboxMessage:
        prompt = (f"این بریف را به یک پیام تلگرامی کوتاه (حداکثر ۶ جمله) برای "
                  f"«{self.cfg.owner_name}» تبدیل کن. لحن: {self.cfg.voice}. "
                  f"بدون اصطلاح فنی؛ آخرش یک قدم سادهٔ پیشنهادی.\n\n"
                  f"عنوان: {brief.title}\nفرصت: {brief.opportunity}\nاقدام: {brief.action}")
        try:
            text = self.gw.llm(prompt, business=self.cfg.id, use_cache=False, max_tokens=400)
        except Exception:  # noqa: BLE001 — آفلاین/بودجه: نسخهٔ قالبی امن
            text = (f"سلام {self.cfg.owner_name} جان 🌟\nیک ایده برای {self.cfg.name}: "
                    f"{brief.title}\nقدم پیشنهادی: {brief.action}")
        return OutboxMessage(business=self.cfg.id, channel=self.channel,
                             to_ref=self.cfg.owner_ref, text=text.strip()[:3500],
                             brief_id=brief.id)

    def discover(self) -> List[OutboxMessage]:
        """پیش‌فرض: هیچ — بیزنس‌ها override می‌کنند (مثلاً مناسبت‌های زیمان)."""
        return []
