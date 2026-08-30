"""self_model.py — ziman_self.v1: شناختِ خود و اهداف (هویت/هدف/وضعیت/gap).

قلبِ بازطراحی (سندِ 00-Control/FOUNDATIONS/01-SELF-MODEL.md): یک ساختارِ واحد که هر ضربان
از منابعِ *واقعیِ فقط‌خواندنی* ساخته می‌شود تا ربات بداند کی‌ست، هدفش چیست، کجای راه است.
هر فیلد برچسبِ صداقت (truth-tier) دارد؛ هیچ عددی جعل نمی‌شود، داده نبود → UNKNOWN.

read-only · stdlib-only · $0 · fail-soft · هیچ اکشنِ بیرونی/خرج.
`build_self_model` خالص و تست‌پذیر است؛ `load_self_model` از منابعِ واقعی سرِهم می‌کند.
"""
from __future__ import annotations

from typing import Any, Optional

# قواعدِ سختِ برند و فعل‌های گیت‌شده (هم‌تراز با _ops/legs/ziman_leg و 06-GOVERNANCE).
BRAND_RULES = (
    "گل‌ها مصنوعی‌اند و صادقانه اعلام می‌شود (نه رقیبِ گلِ تازه)",
    "هیچ گواهیِ جعلی",
    "هیچ قیمتِ عمومیِ تأییدنشده",
    "ظرفیت‌محور (گاردِ D4)",
    "F4 الکل → هشدارِ سن/تحویلِ محلی",
    "انتشار فقط با تأییدِ انسانی",
)
HARD_GATED = (
    "publish", "send", "dm", "spend", "pay", "refund", "create_account",
    "change_public_price", "offer_discount", "promise_delivery", "deploy",
    "activate_live_automation",
)
NORTH_STAR = "10–30 فروشِ واقعی (فازِ اعتبارسنجی)"
_VALIDATION_TARGET = 10  # کفِ بازهٔ north-star برای درصدِ پیشرفت


def _capacity_fail_closed(ceiling, owner_revalidated: bool = False) -> int:
    """آینهٔ product.capacity_fail_closed (fallbackِ امن اگر import نشد)."""
    try:  # ترجیحاً همان تابعِ canonical
        try:
            from .product import capacity_fail_closed
        except ImportError:
            from product import capacity_fail_closed  # type: ignore
        return capacity_fail_closed(ceiling, owner_revalidated)
    except Exception:  # noqa: BLE001 — آینهٔ محافظه‌کار
        if ceiling is None or not isinstance(ceiling, (int, float)) or ceiling <= 0:
            return 0
        return int(ceiling) if owner_revalidated else min(int(ceiling), 6)


def build_self_model(
    *,
    catalog: dict[str, Any],
    cfg: dict[str, Any],
    steering: dict[str, Any],
    real_sales: int = 0,
    budget_headroom_aud: Optional[float] = None,
    drafts_count: int = 0,
    funnel: Optional[dict[str, int]] = None,
    owner_revalidated_capacity: bool = False,
    beat: Optional[int] = None,
) -> dict[str, Any]:
    """ziman_self.v1 را از قطعاتِ آماده می‌سازد (خالص، بدونِ I/O). fail-soft روی ورودی."""
    catalog = catalog or {}
    cfg = cfg or {}
    steering = steering or {}
    funnel = {"cold": 0, "warm": 0, "proposed": 0, "won": 0, **(funnel or {})}

    cap_block = cfg.get("capacity", {}) or {}
    raw_ceiling = cap_block.get("units_per_week_ceiling")
    effective_ceiling = _capacity_fail_closed(raw_ceiling, owner_revalidated_capacity)
    by_family = catalog.get("by_family", {}) or {}
    total = catalog.get("total", 0)

    real_sales = max(0, int(real_sales or 0))
    progress = min(real_sales, _VALIDATION_TARGET) / _VALIDATION_TARGET * 100.0

    identity = {
        "name": (cfg.get("business", {}) or {}).get("name", "Ziman Gift"),
        "market": (cfg.get("business", {}) or {}).get("location", "Sydney") + " · بازارِ گرمِ ایرانی",
        "offering": by_family,
        "facets": {
            "alcohol_skus": catalog.get("alcohol_facet", 0),
            "local_only_count": catalog.get("local_only", 0),
            "perishable_count": catalog.get("perishable", 0),
        },
        "brand_rules": list(BRAND_RULES),
        "hard_gated": list(HARD_GATED),
        "authorities": {"price": False, "delivery_promise": False, "publish": False},
    }

    objective = {
        "north_star": NORTH_STAR,
        "real_sales": real_sales,
        "validation_progress_pct": round(progress, 1),
        "directives": steering.get("directives", []),
        "priorities": steering.get("priorities", []),
        "guardrails": steering.get("guardrails", []),
        "focus": steering.get("focus"),
        "paused": bool(steering.get("paused", False)),
    }

    standing = {
        "catalog": {"total": total, "priced": catalog.get("priced", 0),
                    "by_family": by_family},
        "capacity": {"raw_yaml": raw_ceiling, "evidence": "CONFLICT",
                     "effective_ceiling": effective_ceiling},
        "inventory": {"yaml_hint": cap_block.get("current_inventory"),
                      "owner_stated": 50, "evidence_class": "OWNER_INPUT",
                      "note": "شفاهی؛ هنوز شمارشِ رسمی نشده"},
        "budget_headroom_aud": budget_headroom_aud,
        "drafts_count": drafts_count,
        "funnel": funnel,
    }

    # gap_vector — رانِ اولویتِ خودمختار: فاصلهٔ هر هدف تا وضعیت.
    gap_vector = [
        {"goal": "first_real_sales", "current": real_sales,
         "target": _VALIDATION_TARGET, "gap": max(0, _VALIDATION_TARGET - real_sales),
         "confidence": 0.9, "truth_tier": "VERIFIED_FACT"},
        {"goal": "priced_products", "current": catalog.get("priced", 0),
         "target": total, "gap": max(0, total - catalog.get("priced", 0)),
         "confidence": 0.9, "truth_tier": "CONFLICT",
         "blocked_by": "ZIM-V5 (COGS)"},
        {"goal": "warm_leads_in_funnel", "current": funnel["warm"],
         "target": 5, "gap": max(0, 5 - funnel["warm"]),
         "confidence": 0.5, "truth_tier": "ESTIMATE"},
        {"goal": "capacity_verified", "current": 0, "target": 1, "gap": 1,
         "confidence": 0.8, "truth_tier": "CONFLICT",
         "blocked_by": "CF-01 (ظرفیتِ ۳۰/هفته تأییدنشده)"},
    ]

    return {
        "schema": "ziman_self.v1",
        "beat": beat,
        "identity": identity,
        "objective": objective,
        "standing": standing,
        "gap_vector": gap_vector,
        "propose_only": True,
        "outward_execution": False,
        "truth_tiers": {
            "offering": "MEASURED(photo)", "real_sales": "VERIFIED_FACT",
            "capacity": "CONFLICT", "price": "CONFLICT", "inventory": "OWNER_INPUT",
            "directives": "OWNER_INPUT", "funnel": "MEASURED",
            "budget_headroom_aud": "MEASURED" if budget_headroom_aud is not None else "UNKNOWN",
        },
    }


def load_self_model(cfg_path: str = "ziman.yaml",
                    base_dir: Optional[str] = None,
                    real_sales: int = 0,
                    beat: Optional[int] = None) -> dict[str, Any]:
    """ziman_self.v1 را از منابعِ واقعی می‌سازد (کاتالوگ/yaml/بودجه/هدایت). fail-soft.

    real_sales به‌صورتِ تزریقی می‌آید (پیش‌فرض 0 = صفر فروشِ ثبت‌شده، یک واقعیتِ شناخته‌شده)؛
    گامِ ۹ (P6) خوانندهٔ واقعیِ دفترِ evt.v1 sale:confirmed را وصل می‌کند.
    """
    # importهای dual تا هم flat (تست) و هم packageی کار کند.
    try:
        from . import catalog_loader as _cat
        from . import steering as _steer
        from .config import load_config as _load_cfg
        from .budget import Budget as _Budget
    except ImportError:  # pragma: no cover — مسیرِ flat
        import catalog_loader as _cat  # type: ignore
        import steering as _steer  # type: ignore
        from config import load_config as _load_cfg  # type: ignore
        from budget import Budget as _Budget  # type: ignore

    try:
        cfg = _load_cfg(cfg_path)
    except Exception:  # noqa: BLE001
        cfg = {}
    try:
        summary = _cat.catalog_summary(_cat.load_catalog())
    except Exception:  # noqa: BLE001
        summary = {}
    try:
        steering = _steer.load_steering(base_dir=base_dir)
    except Exception:  # noqa: BLE001
        steering = {}
    try:
        headroom = _Budget(cfg, base_dir=base_dir).remaining_aud() if cfg else None
    except Exception:  # noqa: BLE001
        headroom = None

    return build_self_model(catalog=summary, cfg=cfg, steering=steering,
                            real_sales=real_sales, budget_headroom_aud=headroom,
                            beat=beat)
