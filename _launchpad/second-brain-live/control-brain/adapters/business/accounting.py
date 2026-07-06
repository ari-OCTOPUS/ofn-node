# -*- coding: utf-8 -*-
"""آداپتر حسابداری — اتوماسیون دفترداری/مالیات. صاحب: خود آری."""
from __future__ import annotations

from adapters.business.base import BusinessConfig, GenericOwnerInteraction, GenericResearchEngine

CFG = BusinessConfig(
    id="accounting",
    name="ربات حسابداری",
    owner_ref="admin",
    owner_name="آری",
    market="Australia small business accounting ATO",
    tone="دقیق و خلاصه، با عدد",
    topics=[
        "کسورات مالیاتی FY2026-27 برای sole trader و کسب‌وکار کوچک استرالیا",
        "اتوماسیون دفترداری و رسیدها (bookkeeping automation)",
        "ددلاین‌های BAS/ATO و جریمه‌های قابل‌اجتناب",
        "instant asset write-off و تغییرات سقف آن",
        "فروش خدمات دفترداری خودکار به کسب‌وکارهای فارسی‌زبان سیدنی",
    ],
    context_note="سقف instant asset write-off از 1 Jul 2026 → $1,000 · حسابدار هنوز انتخاب نشده · رجیستر انطباق ناقص",
)


class Research(GenericResearchEngine):
    def __init__(self, gateway, memory):
        super().__init__(CFG, gateway, memory)


class Owner(GenericOwnerInteraction):
    def __init__(self, gateway, memory):
        super().__init__(CFG, gateway, memory)
