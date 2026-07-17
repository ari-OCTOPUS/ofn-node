#!/usr/bin/env python3
"""ziman_leg.py — Phase 4 · L-2: پای Ziman Galerry (هدایای دست‌ساز سیدنی).

قرارداد (OLP-1 / OCTOPUS limb):
  * propose-only: draft محتوا / کمپین / گزارش وضعیت — هرگز publish/send/spend
  * D4 capacity guard: هیچ کمپین بالای سقف units/week
  * money_link: organ=ZIMAN در budgets.yaml (floor AU$1)
  * read-allowlist فقط نوت‌های خودِ پروژه (IsolationModel)
  * PII/secrets هرگز در proposal payload

حلقهٔ paper:
  status_snapshot → inventory_report → draft_content → campaign_check
  هر اثر بیرونی → human gate (Telegram / VERDICT_QUEUE)

برنامهٔ ۸ (پلِ کاتالوگ): خانواده‌های واقعی از ziman-catalog.json (read-only، lazy،
fail-soft) — نبود/خرابیِ کاتالوگ → دقیقاً رفتارِ قدیمِ C1–C4.

additive · $0 offline · stdlib-only · fail-closed
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from leg import Leg, Proposal, TaskPacket  # noqa: E402

# CF-06: از همان گاردِ fail-closed استفاده کن (هرگز کپی نکن). fallback فقط تا گیتِ D4
# هرگز روی خطای import به fail-open نیفتد.
try:
    from ziman_phase2 import capacity_fail_closed  # noqa: E402
except Exception:  # pragma: no cover — safety mirror
    def capacity_fail_closed(ceiling, owner_revalidated=False):
        if ceiling is None or not isinstance(ceiling, (int, float)) or ceiling <= 0:
            return 0
        return int(ceiling) if owner_revalidated else min(int(ceiling), 6)

# مسیرهای ثابت vault (نسبی به ORG_ROOT) — فقط همین‌ها در allowlist
ZIMAN_CATALOG_NOTE = "03 - Projects/Ziman Galerry/03-Offering/ziman-catalog.json"

ZIMAN_NOTES = (
    "03 - Projects/Ziman Galerry/PROJECT.md",
    "03 - Projects/Ziman Galerry/MANIFEST.yaml",
    "03 - Projects/Ziman Galerry/Capacity & Channels.md",
    "03 - Projects/Ziman Galerry/Business-Zeiman.md",
    "03 - Projects/Ziman Galerry/Strategy-DecisionLog.md",
    "03 - Projects/Ziman Galerry/OpenQuestions.md",
    "03 - Projects/Ziman Galerry/VERDICT_QUEUE.md",
    "03 - Projects/Ziman Galerry/00-Control/STATUS.md",
    "03 - Projects/Ziman Galerry/09-Agents/CONSTITUTION.md",
    "03 - Projects/Ziman Galerry/10-Interfaces/BIOLOGY-CONTRACT.md",
    "03 - Projects/Ziman Galerry/ziman-agent/ziman.yaml",
    ZIMAN_CATALOG_NOTE,   # برنامهٔ ۸: پلِ کاتالوگ — read-only
)

# خانواده‌های محصول — fallbackِ قدیمی (C1–C4)، فقط وقتی کاتالوگِ زمینی در دسترس نیست.
# منبعِ حقیقت: ziman-catalog.json (۲۰۲۶-۰۷-۱۲، ساخته از ۴۱ عکس؛ خانواده‌های واقعی
# F1_floral / F2_framed / F3_candy_basket / F4_mixed_hamper / OTHER). نبود/خرابیِ
# کاتالوگ → دقیقاً رفتارِ قدیم با همین جدول (fail-soft، بدون کرش).
PRODUCT_FAMILIES = {
    "C1": "Artificial floral arrangements",
    "C2": "Gift baskets",
    "C3": "Framed floral shadow boxes",
    "C4": "Chocolate hampers (local-only, perishable)",
}

# پلِ سازگاری: کدهای قدیمیِ C1–C4 → خانواده‌های واقعیِ کاتالوگ (grounded در توضیحاتِ
# هر دو تاکسونومی). فقط وقتی کاتالوگ لود شده اعمال می‌شود؛ فراخوانِ قدیمی نمی‌شکند.
LEGACY_FAMILY_ALIAS = {
    "C1": "F1_floral",         # آرایه‌های گلِ مصنوعی
    "C2": "F3_candy_basket",   # سبدهای هدیه (شیرینی‌محور)
    "C3": "F2_framed",         # قاب/شادوباکسِ گل
    "C4": "F4_mixed_hamper",   # هَمپرِ شکلات/میکس (فاسدشدنی)
}

# heuristicِ الکل روی فیلد medium (کاتالوگ فیلد صریح alcohol ندارد؛ «wine» با \b
# تا «twine» false-positive نشود؛ «champagne» عمداً حذف — در این دامنه اسمِ رنگ است).
_ALCOHOL_RE = re.compile(
    r"\b(alcohol|wine|liquor|liqueur|vodka|whisky|whiskey|beer|prosecco|brut)\b",
    re.I)

HARD_GATED = frozenset({
    "publish", "send", "dm", "spend", "pay", "refund",
    "create_account", "change_public_price", "offer_discount",
    "promise_delivery", "deploy", "activate_live_automation",
})


def default_packet() -> TaskPacket:
    """TaskPacket استاندارد پای زیمان — secrets خالی، spawn=0، بدون wildcard."""
    return TaskPacket(
        leg_id="ziman-gallery",
        organ="ZIMAN",
        read_allowlist=ZIMAN_NOTES,
        tools=("status_snapshot", "inventory_report", "draft_content",
               "campaign_check", "memory_candidate"),
        budget_aud=1.0,  # هم‌تراز floor ZIMAN در budgets.yaml
        spawn=0,
        secrets=(),
    )


class ZimanLeg(Leg):
    """پای Ziman — marketing + inventory intelligence، propose-only، D4-enforced."""

    def __init__(self, packet: TaskPacket | None = None,
                 organ_table: dict | None = None,
                 capacity_ceiling: int | None = None,
                 catalog_path: str | Path | None = None):
        super().__init__(packet or default_packet(), organ_table=organ_table)
        self._capacity_ceiling = capacity_ceiling  # None = از yaml/vault بخوان
        # CF-06/CF-01: تا revalidation صریحِ مالک، سقفِ ظرفیت fail-closed می‌ماند (۶/هفته).
        self._owner_revalidated = False
        self._agent_root = self._resolve_agent_root()
        self._biology_status: dict | None = None
        # برنامهٔ ۸: پلِ کاتالوگ — تزریق‌پذیر برای تست؛ None = از opslib.ORG_ROOT در لحظهٔ فراخوان
        self._catalog_path = catalog_path
        self._catalog_cache: dict | None = None
        self._catalog_mtime: float | None = None

    # ─── مسیر agent ──────────────────────────────────────────────────────────
    def _resolve_agent_root(self) -> Path | None:
        try:
            import opslib  # noqa: WPS433
            root = opslib.ORG_ROOT
        except Exception:  # noqa: BLE001
            root = Path(r"F:\backup")
        candidates = [
            root / "03 - Projects" / "Ziman Galerry" / "ziman-agent",
            root / "_code" / "Ziman Galerry" / "ziman-agent",
            root / "_launchpad" / "second-brain-live" / "ziman-agent",
        ]
        for c in candidates:
            if (c / "ziman.yaml").exists():
                return c
        return candidates[0] if candidates else None

    def _load_yaml_capacity(self) -> int:
        """سقف ظرفیت از ziman.yaml؛ 0 = ثبت‌نشده (D4 fail-closed برای کمپین حجمی)."""
        if self._capacity_ceiling is not None:
            return int(self._capacity_ceiling)
        try:
            p = (self._agent_root or Path()) / "ziman.yaml"
            if not p.exists():
                return 0
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"units_per_week_ceiling:\s*(\d+)", text)
            return int(m.group(1)) if m else 0
        except (OSError, ValueError):
            return 0

    def _load_inventory_hint(self) -> int | None:
        try:
            p = (self._agent_root or Path()) / "ziman.yaml"
            if not p.exists():
                return None
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"current_inventory:\s*(\d+)", text)
            return int(m.group(1)) if m else None
        except (OSError, ValueError):
            return None

    # ─── پلِ کاتالوگ (برنامهٔ ۸) — read-only، lazy، fail-soft ────────────────
    def _resolve_catalog_path(self) -> Path:
        """مسیرِ کاتالوگ — تزریقی (تست) یا نسبی به opslib.ORG_ROOT در لحظهٔ فراخوان."""
        if self._catalog_path is not None:
            return Path(self._catalog_path)
        try:
            import opslib  # noqa: WPS433 — lazy تا env تست اثر کند
            root = Path(opslib.ORG_ROOT)
        except Exception:  # noqa: BLE001
            root = Path(r"F:\backup")
        return root / ZIMAN_CATALOG_NOTE

    def _load_catalog(self) -> dict | None:
        """کاتالوگِ زمینیِ زیمان (ziman-catalog.json). نبود/خرابی/خارجِ allowlist → None
        (fail-soft: دقیقاً رفتارِ قدیمِ C1–C4، هرگز کرش). cacheِ per-instance با چکِ mtime."""
        try:
            if not self.packet.can_read(ZIMAN_CATALOG_NOTE):
                return None                                    # خارجِ allowlist = رد (D2)
            p = self._resolve_catalog_path()
            if not p.exists():
                return None
            mtime = p.stat().st_mtime
            if self._catalog_cache is not None and self._catalog_mtime == mtime:
                return self._catalog_cache
            # utf-8-sig: فایلِ واقعی BOM دارد (خروجی PowerShell)؛ بدونِ BOM هم سالم می‌خواند.
            data = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
            prods = data.get("products") if isinstance(data, dict) else None
            if not isinstance(prods, list) or not prods:
                return None                                    # شکلِ نامعتبر = fail-soft
            self._catalog_cache = data
            self._catalog_mtime = mtime
            return data
        except (OSError, ValueError, TypeError):
            return None

    def _catalog_families(self) -> dict | None:
        """جمع‌بندیِ per-family از کاتالوگ:
        {family: {count, perishable_count, alcohol_suspect_count, edible:{...}}}
        perishable = فیلدِ صریحِ bool کاتالوگ؛ alcohol_suspect = heuristic روی medium؛
        edible = شمارشِ فیلدِ صریحِ edible. کاتالوگ نبود → None."""
        cat = self._load_catalog()
        if not cat:
            return None
        fams: dict[str, dict] = {}
        for prod in cat.get("products", []):
            if not isinstance(prod, dict):
                continue
            fam = str(prod.get("family") or "UNKNOWN")
            rec = fams.setdefault(fam, {"count": 0, "perishable_count": 0,
                                        "alcohol_suspect_count": 0, "edible": {}})
            rec["count"] += 1
            if prod.get("perishable") is True:
                rec["perishable_count"] += 1
            media = prod.get("medium") or []
            if isinstance(media, list) and any(
                    _ALCOHOL_RE.search(str(m)) for m in media):
                rec["alcohol_suspect_count"] += 1
            ed = str(prod.get("edible") or "unknown")
            rec["edible"][ed] = rec["edible"].get(ed, 0) + 1
        return fams or None

    def product_families(self) -> dict:
        """خانواده‌های فعال {id: name} — از کاتالوگِ واقعی (مرتب به تعدادِ محصول)؛
        نبودِ کاتالوگ → دقیقاً جدولِ قدیمیِ C1–C4."""
        fams = self._catalog_families()
        if fams:
            ordered = sorted(fams, key=lambda f: (-fams[f]["count"], f))
            return {k: k for k in ordered}
        return dict(PRODUCT_FAMILIES)

    def _resolve_family(self, requested) -> str:
        """نگاشتِ خانوادهٔ درخواستی به خانوادهٔ فعال؛ کدِ قدیمیِ C* از راهِ alias.
        ناشناخته → پیش‌فرضِ قدیم (C3 یا aliasِ آن F2_framed)."""
        fams = self.product_families()
        if requested in fams:
            return requested
        alias = LEGACY_FAMILY_ALIAS.get(str(requested), "")
        if alias in fams:
            return alias
        if "C3" in fams:
            return "C3"
        default_alias = LEGACY_FAMILY_ALIAS.get("C3", "")
        if default_alias in fams:
            return default_alias
        return next(iter(fams))

    def _catalog_summary(self) -> dict:
        """بلوکِ additive «catalog» برای status/inventory — هرگز کلیدِ قدیمی را عوض نمی‌کند."""
        fams = self._catalog_families()
        if not fams:
            return {"loaded": False, "source": None, "evidence_class": "UNKNOWN"}
        return {
            "loaded": True,
            "source": ZIMAN_CATALOG_NOTE,
            "product_count": sum(v["count"] for v in fams.values()),
            "family_counts": {k: fams[k]["count"]
                              for k in self.product_families()},
            "perishable_products": sum(v["perishable_count"] for v in fams.values()),
            "alcohol_suspect_products": sum(v["alcohol_suspect_count"]
                                            for v in fams.values()),
            "flags_note": ("perishable = فیلدِ صریحِ کاتالوگ؛ alcohol_suspect = "
                           "heuristic روی medium؛ licensed: فیلدی در کاتالوگ ندارد "
                           "(رجوع: data_gaps خودِ کاتالوگ)."),
            "evidence_class": "GROUNDED",
        }

    # ─── D4 capacity ─────────────────────────────────────────────────────────
    def campaign_check(self, requested_units: int,
                       horizon_weeks: int = 1) -> dict:
        """گارد D4 — pure function روی سقف. هیچ side-effect.

        CF-06: سقفِ خامِ yaml (تأییدنشده، مثلاً ۳۰) قبل از گیت از capacity_fail_closed
        رد می‌شود → تا revalidation مالک سقفِ مؤثر ≤۶/هفته است (fail-closed، نه ۳۰).
        """
        raw_ceiling = self._load_yaml_capacity()
        ceiling = capacity_fail_closed(raw_ceiling,
                                       owner_revalidated=self._owner_revalidated)
        try:
            requested = int(requested_units)
            weeks = max(1, int(horizon_weeks))
        except (TypeError, ValueError):
            return {
                "approved": False, "requested": requested_units,
                "raw_ceiling": raw_ceiling, "ceiling": ceiling, "max_allowed": 0,
                "reason": "رد D4: ورودیِ غیرعددی (fail-closed).",
            }
        if ceiling <= 0:
            return {
                "approved": False, "requested": requested,
                "raw_ceiling": raw_ceiling, "ceiling": ceiling, "max_allowed": 0,
                "reason": ("سقف ظرفیت ثبت/تأیید نشده — تا revalidation مالک، "
                           "هیچ کمپین حجمی مجاز نیست (D4/CF-01)."),
            }
        max_allowed = ceiling * weeks
        if requested <= 0:
            return {
                "approved": True, "requested": requested,
                "raw_ceiling": raw_ceiling, "ceiling": ceiling,
                "max_allowed": max_allowed,
                "reason": "بدون هدف حجمی (محتوای معمولی) — مجاز.",
            }
        if requested > max_allowed:
            return {
                "approved": False, "requested": requested,
                "raw_ceiling": raw_ceiling, "ceiling": ceiling,
                "max_allowed": max_allowed,
                "reason": (f"رد D4: {requested} > {max_allowed} "
                           f"(سقفِ محتاطانه {ceiling}/هفته × {weeks} هفته؛ "
                           f"خامِ yaml={raw_ceiling} تأییدنشده — CF-01)."),
            }
        return {
            "approved": True, "requested": requested,
            "raw_ceiling": raw_ceiling, "ceiling": ceiling,
            "max_allowed": max_allowed,
            "reason": (f"تأیید: {requested} ≤ {max_allowed} "
                       f"(سقفِ محتاطانه {ceiling}/هفته)."),
        }

    # ─── status ──────────────────────────────────────────────────────────────
    def status_snapshot(self) -> dict:
        """وضعیت read-only برای Telegram / organism heartbeat."""
        ceiling = self._load_yaml_capacity()
        inv = self._load_inventory_hint()
        drafts_n = 0
        try:
            ddir = (self._agent_root or Path()) / "drafts"
            if ddir.exists():
                drafts_n = len(list(ddir.glob("*.md")))
        except OSError:
            drafts_n = 0
        return {
            "leg_id": self.packet.leg_id,
            "organ": self.packet.organ,
            "money_link": self.money_link,
            "capacity_ceiling_per_week": ceiling,
            "capacity_ceiling_raw_unverified": ceiling,       # I-5: خامِ yaml (تأییدنشده)
            "capacity_ceiling_effective": capacity_fail_closed(
                ceiling, self._owner_revalidated),            # سقفِ محتاطانه‌ای که واقعاً اعمال می‌شود
            "inventory_hint": inv,
            "inventory_evidence_class": "UNVERIFIED" if inv is not None else "UNKNOWN",
            "product_families": list(self.product_families().keys()),
            "catalog": self._catalog_summary(),   # additive — برنامهٔ ۸
            "drafts_count": drafts_n,
            "autonomy": "propose-only",
            "hard_gated": sorted(HARD_GATED),
            "execution_state": "ZERO outward execution — drafts only",
            "capacity_evidence_class": "CONFLICT" if ceiling else "UNKNOWN",
            "capacity_public_claim_allowed": False,
            "delivery_promise_authority": False,
            "price_authority": False,
            "payment_instruction_authority": False,
            "biology": self._biology_status,
        }

    def accept_biology_status(self, status: dict | None) -> bool:
        """پذیرش read-model قلب/اعصاب/دکتر؛ فقط cache محلی، بدون تغییر قلب یا دکتر.

        فقط schema=ziman-biology.v1 و outward_execution=false پذیرفته می‌شود.
        """
        if not isinstance(status, dict):
            return False
        if status.get("schema") != "ziman-biology.v1":
            return False
        if status.get("outward_execution") is not False:
            return False
        if status.get("ziman_can_write_heart") is not False:
            return False
        self._biology_status = dict(status)
        return True

    # ─── inventory report (proposal) ─────────────────────────────────────────
    def inventory_report(self, family_counts: dict | None = None) -> Proposal:
        """گزارش موجودی — proposal، نه canonical write.
        family_counts: optional {family: n} از مالک/اپراتور (کدِ قدیمیِ C* هم با alias
        پذیرفته می‌شود وقتی کاتالوگ فعال است). با کاتالوگ: شمارشِ واقعیِ per-family +
        پرچم‌های perishable/alcohol_suspect/edible (additive؛ کلیدهای قدیم دست‌نخورده).
        """
        counts = dict(family_counts or {})
        cat_fams = self._catalog_families()
        fams_active = self.product_families()
        resolved: dict = {}
        unknown = []
        for k, v in counts.items():
            key = k if k in fams_active else (
                LEGACY_FAMILY_ALIAS.get(str(k), "") if cat_fams else "")
            if key in fams_active:
                resolved[key] = v
            else:
                unknown.append(k)
        families = {}
        for k, name in fams_active.items():
            entry: dict = {"name": name, "count": resolved.get(k)}
            if cat_fams:                       # پرچم‌های زمینی — فقط additive
                rec = cat_fams.get(k, {})
                entry["catalog_count"] = rec.get("count", 0)
                entry["perishable_count"] = rec.get("perishable_count", 0)
                entry["alcohol_suspect_count"] = rec.get("alcohol_suspect_count", 0)
                entry["edible"] = dict(rec.get("edible", {}))
            families[k] = entry
        payload = {
            "draft_only": True,
            "inventory_hint": self._load_inventory_hint(),
            "capacity_ceiling": self._load_yaml_capacity(),
            "families": families,
            "unknown_keys_rejected": unknown,
            "canonical_write": False,
            "capacity_public_claim_allowed": False,
            "delivery_promise_authority": False,
            "price_authority": False,
            "note": ("50 physical products reported by owner is NOT "
                     "necessarily 50 SKUs and NOT weekly capacity."),
            "next_step": (("Owner confirms catalog families ("
                           + ", ".join(fams_active) + ") then SKU cards")
                          if cat_fams else
                          "Owner classifies into C1–C4 then SKU cards"),
            "catalog": self._catalog_summary(),   # additive — برنامهٔ ۸
        }
        return self.emit_proposal("inventory_report", payload)

    # ─── draft content (proposal) ────────────────────────────────────────────
    def draft_content(self, kind: str = "caption",
                      product_family: str = "C3",
                      occasion: str = "هدیه",
                      campaign_units: int = 0) -> Proposal | dict:
        """تولید draft محتوا. campaign_units>0 → D4 gate اول.
        kind: caption | dm | report
        هرگز publish نمی‌کند — فقط proposal.
        """
        if kind in HARD_GATED or kind in ("publish", "send"):
            return {"ok": False, "error": f"forbidden kind: {kind}"}

        gate = self.campaign_check(campaign_units)
        if not gate["approved"] and campaign_units > 0:
            return {"ok": False, "error": "D4_REJECT", "gate": gate}

        fams_active = self.product_families()
        cat_fams = self._catalog_families() or {}
        family = self._resolve_family(product_family)
        product_name = fams_active[family]

        # قواعد برند سخت: هیچ عدد ظرفیت/قیمت/پرداخت/تحویل عمومی تا تأیید مالک.
        # legacy ziman.yaml ممکن است 30/week داشته باشد، اما status آن CONFLICT است؛
        # بنابراین متن public-facing نباید آن را وعده یا claim کند.
        body_lines = [
            f"🌸 Ziman · {occasion}",
            f"محصول: {product_name} ({family})",
            "گل‌ها مصنوعی و ماندگارند — نه شاخهٔ بریده.",
            "ظرفیت، قیمت، روش پرداخت و زمان تحویل فقط بعد از تأیید مالک اعلام می‌شود.",
            "این پیش‌نویس است — انتشار فقط با تأیید انسانی.",
        ]
        rec = cat_fams.get(family)
        if family == "C4" or (rec and rec.get("perishable_count", 0) > 0):
            # فاسدشدنی: قدیم فقط C4 هاردکد بود؛ با کاتالوگ از فیلدِ perishable مشتق می‌شود.
            body_lines.append(
                f"⚠️ {family} فاسدشدنی: فقط تحویل/پیکاپ محلی — بدون ارسال دور.")
        if rec and rec.get("alcohol_suspect_count", 0) > 0:
            body_lines.append(
                "⚠️ برخی آیتم‌های این خانواده مشکوک به الکل (heuristic روی medium) — "
                "محدودیت سنی/حمل؛ فقط با تأیید مالک.")

        payload = {
            "draft_only": True,
            "kind": kind,
            "product_family": family,
            "requested_family": product_family,                       # additive
            "family_source": "catalog" if cat_fams else "legacy_fallback",  # additive
            "occasion": occasion,
            "body": "\n".join(body_lines),
            "brand_rules": [
                "artificial florals only",
                "no fabricated testimonials",
                "no unapproved price",
                "capacity-first (D4)",
            ],
            "campaign_gate": gate,
            "publish": False,
        }
        return self.emit_proposal("draft_content", payload)

    # ─── memory candidate (not canonical) ────────────────────────────────────
    def memory_candidate(self, claim: str, evidence_pointer: str,
                         confidence: float = 0.5,
                         privacy_class: str = "internal") -> Proposal | dict:
        """کاندید حافظه — فقط provisional؛ canonical write = Memory Curator + human."""
        claim = (claim or "").strip()
        if not claim:
            return {"ok": False, "error": "claim empty"}
        if privacy_class in ("secret", "pii", "customer_address"):
            return {"ok": False, "error": "privacy class forbidden in memory candidate"}
        # scrub secrets-ish patterns
        if re.search(r"(api[_-]?key|token|payid\s*:|password)", claim, re.I):
            return {"ok": False, "error": "possible secret in claim — rejected"}
        payload = {
            "status": "provisional",
            "claim": claim[:500],
            "evidence_pointer": str(evidence_pointer)[:300],
            "confidence": max(0.0, min(1.0, float(confidence))),
            "privacy_class": privacy_class,
            "canonical_write": False,
            "tenant_id": "ZIMAN",
            "requires": ["schema_validation", "evidence_check",
                         "duplicate_check", "curator_gate"],
        }
        return self.emit_proposal("memory_candidate", payload)

    # ─── tick (paper heartbeat for organism) ─────────────────────────────────
    def tick(self) -> dict:
        """یک ضربان سبک: status + optional inventory proposal.
        هیچ شبکه، هیچ spend. مناسب wiring / chrono beat.
        """
        snap = self.status_snapshot()
        # اگر inventory hint هست ولی breakdown نیست → یک proposal یادآوری
        proposals_before = len(self.proposals)
        if snap.get("inventory_hint") and not self.proposals:
            self.inventory_report()
        return {
            "ok": True,
            "status": snap,
            "proposals_delta": len(self.proposals) - proposals_before,
            "proposals_total": len(self.proposals),
        }

    def telegram_digest(self) -> str:
        """۳ خط ADHD-first برای telegram_center."""
        s = self.status_snapshot()
        # I-5: هرگز عددِ خامِ yaml را به‌عنوان واقعیتِ تأییدشده نشان نده.
        eff = s.get("capacity_ceiling_effective")
        raw = s.get("capacity_ceiling_raw_unverified")
        cap_s = (f"~{eff}/هفته (محتاطانه؛ خام {raw} تأییدنشده)"
                 if eff else "ثبت/تأییدنشده")
        inv = s.get("inventory_hint")
        inv_s = f"≈{inv} [تأییدنشده]" if inv is not None else "?"
        link = s.get("money_link", "?")
        drafts = s.get("drafts_count", 0)
        return (
            f"🖼 Ziman · {link}\n"
            f"ظرفیت {cap_s} · موجودی {inv_s} · drafts={drafts}\n"
            f"propose-only · D4 on · zero external exec"
        )
