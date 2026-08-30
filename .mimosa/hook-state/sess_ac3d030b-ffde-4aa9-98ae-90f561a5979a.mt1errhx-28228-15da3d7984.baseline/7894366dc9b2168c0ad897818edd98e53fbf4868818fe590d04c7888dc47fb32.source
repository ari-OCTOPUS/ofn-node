# -*- coding: utf-8 -*-
"""رجیستری پلاگینی بیزنس‌ها — بیزنس جدید = یک import اینجا، همین."""
from adapters.business import accounting, painting, ziman
from adapters.business.base import PersonalGenome

ALL = {
    "ziman": ziman,
    "painting": painting,
    "accounting": accounting,
}

# Project-F 🔒 — ژنومِ config-only: قفلِ GATE 0، status_only، بدون engine (صفر اجرا).
# در رجیستری/داشبورد دیده می‌شود ولی هیچ رکن A/B ندارد تا وقتی آری بازش کند.
PROJECTF_GENOME = PersonalGenome(
    id="projectf",
    name="Project-F 🔒 (OnlyFans)",
    owner_ref="saba",
    owner_name="صبا",
    market="OnlyFans creator marketing",
    tone="محتاط و ToS-safe",
    persona="مارکترِ محتاطِ ToS-safe — تا GATE 0 هیچ اجرایی نمی‌کند؛ فقط وضعیت.",
    values=["ToS-safe مطلق", "بدون auto-post خودمختار", "احترام به GATE 0"],
    autonomy="status_only",
    budget_share=0.0,
    privacy_class="sensitive",   # ← هرگز به Fugu نمی‌رود (گارد ژنوم اصلی)
    evolution_optin=False,
    kpis=["(منتظر verdict GATE 0)"],
)


def genomes() -> dict:
    """همهٔ ژنوم‌های شخصی (زندهٔ engine‌دار + config-onlyِ قفل‌شده) → {id: PersonalGenome}."""
    g = {bid: mod.CFG for bid, mod in ALL.items()}
    g["projectf"] = PROJECTF_GENOME
    return g


def engines_for(business_id: str, gateway, memory):
    """(ResearchEngine, OwnerInteractionEngine) برای یک بیزنس."""
    mod = ALL[business_id]
    return mod.Research(gateway, memory), mod.Owner(gateway, memory)
