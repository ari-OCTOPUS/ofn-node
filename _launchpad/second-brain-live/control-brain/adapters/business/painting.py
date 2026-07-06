# -*- coding: utf-8 -*-
"""آداپتر ربات نقاشی — لیدگیری نقاشی ساختمان سیدنی. صاحب: خود آری."""
from __future__ import annotations

from adapters.business.base import BusinessConfig, GenericOwnerInteraction, GenericResearchEngine

CFG = BusinessConfig(
    id="painting",
    name="Sydney Painting (لیدگیری نقاشی)",
    owner_ref="admin",
    owner_name="آری",
    market="Sydney NSW painting contractor leads",
    tone="مستقیم و عملیاتی، رفیقانه",
    topics=[
        "پیدا کردن لیدهای نقاشی commercial و strata در سیدنی",
        "قراردادهای دولتی و tender های نقاشی NSW",
        "بهینه‌سازی Google Business Profile برای trade services",
        "قیمت‌گذاری و برآورد پروژه‌های premium residential",
        "شراکت با builder ها و آژانس‌های املاک برای کار مستمر",
    ],
    context_note="محدودهٔ پروژه ۲۰هزار تا ۲میلیون AUD · دسته‌ها: gov/commercial/strata/residential-premium · ابزار hunter/harvester از قبل دارد",
)


class Research(GenericResearchEngine):
    def __init__(self, gateway, memory):
        super().__init__(CFG, gateway, memory)


class Owner(GenericOwnerInteraction):
    def __init__(self, gateway, memory):
        super().__init__(CFG, gateway, memory)
