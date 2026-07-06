# -*- coding: utf-8 -*-
"""آداپتر زیمان — هدایای دست‌ساز لوکس سیدنی. صاحب: مامان (تولید)."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import List

from adapters.business.base import BusinessConfig, GenericOwnerInteraction, GenericResearchEngine
from core.contracts import OutboxMessage

CFG = BusinessConfig(
    id="ziman",
    name="Ziman Gift",
    owner_ref="mom",
    owner_name="مامان",
    market="Sydney Australia gift market",
    tone="گرم و خانوادگی، ساده، دلگرم‌کننده",
    topics=[
        "فروش هدایای دست‌ساز لوکس در اینستاگرام",
        "قیمت‌گذاری premium برای گل‌آرایی مصنوعی و باکس هدیه",
        "بازار هدایای شرکتی (corporate gifting) سیدنی",
        "فروش مناسبتی (تولد، سالگرد، یلدا) به جامعهٔ فارسی‌زبان استرالیا",
        "کانال‌های فروش محلی: مارکت‌ها و پاپ‌آپ‌های سیدنی",
    ],
    context_note="سقف تولید ۳۰ واحد/هفته (D4) · پرداخت PayID · تحویل محلی سیدنی · گل‌ها مصنوعی‌اند",
)


class Research(GenericResearchEngine):
    def __init__(self, gateway, memory):
        super().__init__(CFG, gateway, memory)


class Owner(GenericOwnerInteraction):
    def __init__(self, gateway, memory):
        super().__init__(CFG, gateway, memory)
        self._za = Path(__file__).resolve().parents[3] / "ziman-agent"

    def _anchors(self) -> List[tuple]:
        y = self._za / "ziman.yaml"
        if not y.exists():
            return []
        txt = y.read_text(encoding="utf-8")
        return [(n, int(m)) for n, m in
                re.findall(r'\{name:\s*"([^"]+)",\s*month:\s*(\d+)\}', txt)]

    def discover(self) -> List[OutboxMessage]:
        """مناسبت ماه جاری/بعد → پیشنهاد آماده‌سازی برای مامان (باز هم از صف تأیید)."""
        out = []
        now_m = date.today().month
        for name, month in self._anchors():
            dist = (month - now_m) % 12
            if dist in (0, 1):
                when = "همین ماه" if dist == 0 else "ماه دیگر"
                out.append(OutboxMessage(
                    business=CFG.id, channel="telegram", to_ref=CFG.owner_ref,
                    text=(f"مامان جان 🌸 «{name}» {when} است!\n"
                          f"پیشنهاد: از الان چند باکس مناسبتی آماده کنیم "
                          f"(یادمان باشد سقف هفته ۳۰ تاست). نظرت چیه؟")))
        return out
