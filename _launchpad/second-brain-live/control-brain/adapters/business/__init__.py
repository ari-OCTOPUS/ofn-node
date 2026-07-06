# -*- coding: utf-8 -*-
"""رجیستری پلاگینی بیزنس‌ها — بیزنس جدید = یک import اینجا، همین."""
from adapters.business import accounting, painting, ziman

ALL = {
    "ziman": ziman,
    "painting": painting,
    "accounting": accounting,
}


def engines_for(business_id: str, gateway, memory):
    """(ResearchEngine, OwnerInteractionEngine) برای یک بیزنس."""
    mod = ALL[business_id]
    return mod.Research(gateway, memory), mod.Owner(gateway, memory)
