"""telegram_adapter.py — Telegram gateway for Ziman (propose-only, no send).

Standards: OLP-1 · dry-run · gateway only · never canonical memory.
Produces formatted digests for telegram_center; never talks to API directly.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .command_registry import ZimanCommandRegistry
from .product import InventorySnapshot, PhotoProductMap, ProductCard

# فرمانِ canonical (رجیستری) → کلیدِ داخلیِ این adapter (/ziman_*).
# هم /status و هم /ziman_status باید مسیر یابند.
_CANON_TO_LEGACY = {
    "/status": "/ziman_status",
    "/summary": "/ziman_inventory",
    "/product": "/ziman_products",
    "/photo": "/ziman_photos",
    "/risks": "/ziman_experiments",
    "/queue": "/ziman_decisions",
}


# ── Digest formatters ──────────────────────────────────────────────────────

def status_digest(
    capacity_ceiling: int | None,
    inventory_hint: int | None,
    drafts_count: int,
    product_families: list[str],
    money_link: str,
) -> str:
    ceil_s = str(capacity_ceiling) if capacity_ceiling is not None else "?"
    inv_s = str(inventory_hint) if inventory_hint is not None else "?"
    fam_s = ",".join(product_families)
    return (
        f"🖼 Ziman · {money_link}\n"
        f"ظرفیت {ceil_s}/هفته · موجودی≈{inv_s} · drafts={drafts_count}\n"
        f"families={fam_s} · propose-only · D4 on · zero external exec"
    )


def inventory_digest(snap: InventorySnapshot) -> str:
    lines = [
        f"📦 Inventory snapshot: {snap.snapshot_id}",
        f"تاریخ: {snap.measured_at} · روش: {snap.method}",
    ]
    total = snap.totals.get("physical_units_total")
    if total is not None:
        lines.append(f"کل فیزیکی: {total} واحد")
    for fam, data in (snap.families or {}).items():
        u = data.get("units")
        s = data.get("sku_count")
        if u is not None:
            lines.append(f"  {fam}: {u} واحد" + (f" / {s} SKU" if s else ""))
    cap = snap.capacity.get("units_per_week_ceiling")
    if cap is not None:
        lines.append(f"سقف ظرفیت: {cap}/هفته ({snap.capacity.get('evidence_class', '?')})")
    if snap.conflicts_acknowledged:
        lines.append(f"⚠️ conflicts: {', '.join(snap.conflicts_acknowledged)}")
    return "\n".join(lines)


def product_digest(card: ProductCard) -> str:
    """Short 4-line ADHD-first product summary for Telegram."""
    atp = card.inventory.compute_atp()
    atp_s = str(atp) if atp is not None else "?"
    price = card.commercial.public_price_aud
    price_s = f"${price}" if price is not None else "—"
    status = card.status
    return (
        f"🎁 {card.product_id}: {card.title or '(بدون عنوان)'}\n"
        f"   خانواده: {card.family_id} · وضعیت: {status}\n"
        f"   موجودی: {card.inventory.quantity_on_hand or '?'} · ATP: {atp_s}\n"
        f"   قیمت: {price_s} ({card.commercial.price_status})"
    )


def experiment_proposal_digest(
    exp_id: str,
    hypothesis: str,
    audience: str,
    product_ids: list[str],
    duration_days: int,
    primary_metric: str,
    success_threshold: str,
) -> str:
    return (
        f"🧪 Experiment proposal: {exp_id}\n"
        f"فرضیه: {hypothesis}\n"
        f"مخاطب: {audience} · محصولات: {', '.join(product_ids)}\n"
        f"مدت: {duration_days} روز · شاخص: {primary_metric} · موفقیت: {success_threshold}"
    )


def photo_map_digest(mp: PhotoProductMap, max_entries: int = 5) -> str:
    lines = [f"📸 Photo map: {mp.map_id} ({len(mp.entries)} عکس)"]
    for e in (mp.entries or [])[:max_entries]:
        pid = e.get("product_id") or "—"
        lines.append(f"  {e.get('photo_path','?')[:40]} → {pid}")
    if len(mp.entries) > max_entries:
        lines.append(f"  ... و {len(mp.entries) - max_entries} عکس دیگر")
    return "\n".join(lines)


# ── Command router (dry-run) ───────────────────────────────────────────────

class ZimanTelegramAdapter:
    """Receives virtual Telegram commands and returns text (never sends)."""

    def __init__(
        self,
        product_cards: list[ProductCard] | None = None,
        inventory_snapshot: InventorySnapshot | None = None,
        photo_map: PhotoProductMap | None = None,
        capacity_ceiling: int | None = None,
        inventory_hint: int | None = None,
        drafts_count: int = 0,
        money_link: str = "ZIMAN",
        registry: ZimanCommandRegistry | None = None,
    ):
        self.cards = product_cards or []
        self.snapshot = inventory_snapshot
        self.photo_map = photo_map
        self.capacity_ceiling = capacity_ceiling
        self.inventory_hint = inventory_hint
        self.drafts_count = drafts_count
        self.money_link = money_link
        self.registry = registry or ZimanCommandRegistry.load()

    def classify(self, cmd: str) -> dict:
        """طبقه‌بندیِ ریسک/حالتِ فرمان از رجیستریِ واحد (فقط اطلاعاتی)."""
        return self.registry.classify(cmd)

    def _governance_tag(self, cmd: str) -> str:
        info = self.registry.classify(cmd)
        if not info.get("known"):
            return ""
        return f"⟦{info['risk']}·{info['mode']}⟧ "

    def catalog_digest(self) -> str:
        """خلاصهٔ کاتالوگِ گراندشده (از catalog_loader). فقط-خواندنی."""
        try:
            from .catalog_loader import catalog_summary, load_catalog
            s = catalog_summary(load_catalog())
        except Exception:  # noqa: BLE001 — کاتالوگ نبود → پیامِ امن
            return "🎁 کاتالوگ در دسترس نیست."
        if not s.get("total"):
            return "🎁 کاتالوگ خالی است."
        fam = " · ".join(f"{k}={v}" for k, v in sorted(s["by_family"].items()))
        return (
            f"🎁 کاتالوگ · کل={s['total']}\n"
            f"{fam}\n"
            f"perishable={s['perishable']} · local_only={s['local_only']} · "
            f"قیمت‌گذاری‌شده={s['priced']} (propose-only تا ZIM-V5)\n"
            "📝 drafts: python worker.py --once (--dm/--posts) — انتشار فقط با تأییدِ انسانی."
        )

    def route(self, cmd: str, args: list[str] | None = None) -> str:
        """Route a command string to the correct formatter.

        هم فرمانِ canonical (رجیستری) و هم aliasِ قدیمیِ /ziman_* پذیرفته می‌شود.
        """
        args = args or []
        # اول aliasِ قدیمیِ /ziman_* → فرمانِ canonical (از رجیستری)، بعد
        # canonical → کلیدِ داخلی. این‌طور classify و route هرگز اختلاف ندارند.
        cmd = self.registry.canonical(cmd)
        cmd = _CANON_TO_LEGACY.get(cmd, cmd)
        if cmd == "/catalog":
            return self.catalog_digest()
        if cmd == "/ziman_status":
            return status_digest(
                self.capacity_ceiling, self.inventory_hint,
                self.drafts_count, ["C1", "C2", "C3", "C4"], self.money_link
            )
        if cmd == "/ziman_inventory":
            if self.snapshot:
                return inventory_digest(self.snapshot)
            return "📦 هنوز snapshot موجودی ثبت نشده."
        if cmd == "/ziman_products":
            if not self.cards:
                return "🎁 هنوز Product Cardای ثبت نشده."
            return "\n\n".join(product_digest(c) for c in self.cards[:10])
        if cmd == "/ziman_photos":
            if self.photo_map:
                return photo_map_digest(self.photo_map)
            return "📸 هنوز photo map ساخته نشده."
        if cmd == "/ziman_experiments":
            return (
                "🧪 Experiments (proposed):\n"
                "1) Warm-market DM test — C3 hero, 6 units\n"
                "2) Instagram caption test — C1/C3 mix, 7 days\n"
                "3) Referral seeding — 2 strategic gifts\n"
                "همه به تأیید انسانی نیاز دارند."
            )
        if cmd == "/ziman_decisions":
            return (
                "⚖️ Verdict Queue:\n"
                "- ثبت سقف ظرفیت (CF-01)\n"
                "- شمارش موجودی واقعی (CF-02)\n"
                "- انتخاب کانال اول\n"
                "تصمیمات در VERDICT_QUEUE.md"
            )
        if cmd == "/halt_ziman":
            return (
                "🛑 HALT acknowledged (dry-run).\n"
                "در runtime واقعی: limb-halt marker ساخته می‌شود + tick متوقف."
            )
        return f"❓ Unknown command: {cmd}"

    def to_json(self) -> str:
        return json.dumps({
            "money_link": self.money_link,
            "cards_count": len(self.cards),
            "has_snapshot": self.snapshot is not None,
            "has_photo_map": self.photo_map is not None,
            "capacity_ceiling": self.capacity_ceiling,
            "inventory_hint": self.inventory_hint,
        }, ensure_ascii=False)
