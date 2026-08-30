#!/usr/bin/env python3
"""phase2_cli.py — Phase 2 commands for Ziman (additive to worker.py).

Commands:
  python phase2_cli.py --product-card <family> <title> [--qty N] [--price N]
  python phase2_cli.py --inventory-snapshot <method> [--C1 N] [--C2 N] [--C3 N] [--C4 N]
  python phase2_cli.py --photo-index <dir>
  python phase2_cli.py --telegram-dry <cmd>
  python phase2_cli.py --selftest

Standards: OLP-1, additive, propose-only, $0 offline, no external action.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ziman.config import load_config  # noqa: E402
from ziman.product import (  # noqa: E402
    CommercialBlock,
    InventoryBlock,
    InventorySnapshot,
    ProductCard,
    anti_misread_guard,
    capacity_fail_closed,
    index_photos,
    next_product_id,
    save_product_card,
)
from ziman.telegram_adapter import ZimanTelegramAdapter  # noqa: E402

CFG_PATH = ROOT / "ziman.yaml"
PRODUCTS_DIR = ROOT / "products"
DRAFTS = ROOT / "drafts"


def _log(msg: str):
    print(f"[phase2] {msg}", flush=True)


def cmd_product_card(args):
    family = args.family
    title = args.title
    qty = args.qty
    price = args.price
    if price is not None:
        _log("Refused: --price cannot mark a public price approved. Create the card without a price; owner approval is a separate gate.")
        return 2

    # Determine perishable from family
    perishable = family == "C4"
    policy = "local_only" if family == "C4" else "unknown"

    # Generate next ID
    existing = [p.stem for p in PRODUCTS_DIR.glob("ZM-*.json")] if PRODUCTS_DIR.exists() else []
    pid = next_product_id(family, existing)

    card = ProductCard(
        product_id=pid,
        family_id=family,
        title=title,
        status="draft",
        classification={"perishable": perishable, "personalisable": False},
        inventory=InventoryBlock(
            quantity_on_hand=qty,
            measured_at=datetime.now(timezone.utc).isoformat() if qty is not None else None,
        ),
        commercial=CommercialBlock(price_status="unknown"),
        fulfilment={"policy": policy, "delivery_promise_authority": False},
        evidence={"source_pointers": ["phase2_cli.py --product-card"], "confidence": 0.6},
        governance={"canonical": False, "owner_approved": False, "updated_at": datetime.now(timezone.utc).isoformat()},
    )

    errs = card.validate()
    if errs:
        _log(f"Validation errors for {pid}:")
        for e in errs:
            _log(f"  • {e}")
        return 1

    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    out = save_product_card(card, PRODUCTS_DIR)
    _log(f"Product Card saved: {out}")
    print(json.dumps(card.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_inventory_snapshot(args):
    counts = [args.C1, args.C2, args.C3, args.C4]
    if any(value < 0 for value in counts):
        _log("Refused: family unit counts must be non-negative.")
        return 2
    if args.owner_revalidated and args.capacity is None:
        _log("Refused: --owner-revalidated requires an explicit --capacity value.")
        return 2
    capacity_ceiling = capacity_fail_closed(args.capacity, args.owner_revalidated)
    capacity_evidence = "OWNER_INPUT" if args.owner_revalidated else "UNVERIFIED"
    capacity_source = "owner_revalidated" if args.owner_revalidated else "not supplied"
    snap = InventorySnapshot(
        snapshot_id=f"ZM-INV-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        measured_at=datetime.now(timezone.utc).isoformat(),
        measured_by="owner",
        method=args.method,
        totals={"physical_units_total": sum(v for v in [args.C1, args.C2, args.C3, args.C4] if v)},
        families={
            "C1": {"units": args.C1},
            "C2": {"units": args.C2},
            "C3": {"units": args.C3},
            "C4": {"units": args.C4},
        },
        capacity={
            "units_per_week_ceiling": capacity_ceiling if args.capacity is not None else None,
            "evidence_class": capacity_evidence,
            "source": capacity_source,
        },
        conflicts_acknowledged=["CF-01", "CF-02"],
        governance={"canonical": False, "updated_at": datetime.now(timezone.utc).isoformat()},
    )
    out = DRAFTS / f"{snap.snapshot_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap.to_dict(), ensure_ascii=False, indent=2), "utf-8")
    _log(f"Inventory Snapshot saved: {out}")
    print(json.dumps(snap.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_photo_index(args):
    photo_dir = Path(args.photo_dir)
    mp = index_photos(photo_dir)
    out = DRAFTS / f"{mp.map_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mp.to_dict(), ensure_ascii=False, indent=2), "utf-8")
    _log(f"Photo Map saved: {out} ({len(mp.entries)} entries)")
    print(json.dumps(mp.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_telegram_dry(args):
    cfg = load_config(CFG_PATH)
    adapter = ZimanTelegramAdapter(
        capacity_ceiling=cfg["capacity"].get("units_per_week_ceiling"),
        inventory_hint=cfg["capacity"].get("current_inventory"),
        drafts_count=len(list(DRAFTS.glob("*.md"))) if DRAFTS.exists() else 0,
        money_link="ZIMAN",
    )
    result = adapter.route(args.cmd)
    print(f"Command: {args.cmd}\n{'─' * 40}\n{result}\n{'─' * 40}")
    return 0


def cmd_selftest():
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("✅ " if cond else "❌ ") + name)
        ok = ok and bool(cond)

    # ProductCard
    c = ProductCard(product_id="ZM-C3-0001", family_id="C3", title="Test")
    check("ProductCard basic", c.validate() == [])
    c4 = ProductCard(product_id="ZM-C4-0001", family_id="C4", classification={"perishable": True}, fulfilment={"policy": "pickup"})
    check("C4 invariant", c4.validate() == [])
    # ATP
    inv = InventoryBlock(quantity_on_hand=10, quantity_reserved=3, measured_at="2026-07-12")
    check("ATP compute", inv.compute_atp() == 7)
    # anti-misread
    check("anti_misread_guard", anti_misread_guard("50 unique SKUs")["allowed"] is False)
    print("\n" + ("Phase 2 selftest: all green ✅" if ok else "Phase 2 selftest: failed ❌"))
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description="Ziman Phase 2 CLI (local drafts only; no external execution)")
    action = p.add_mutually_exclusive_group()
    action.add_argument("--product-card", nargs=2, metavar=("FAMILY", "TITLE"),
                        help="create a draft Product Card")
    action.add_argument("--inventory-snapshot", metavar="METHOD",
                        choices=["physical_count", "photo_estimate", "partial"],
                        help="create a draft inventory snapshot")
    action.add_argument("--photo-index", metavar="PHOTO_DIR", help="read-only photo index")
    action.add_argument("--telegram-dry", metavar="COMMAND", help="format a dry-run Telegram reply")
    action.add_argument("--selftest", action="store_true", help="run local Phase 2 checks")
    p.add_argument("--qty", type=int, default=None, help="measured quantity for a draft card")
    p.add_argument("--price", type=float, default=None,
                   help="rejected: price approval must happen in a separate owner gate")
    p.add_argument("--C1", type=int, default=0)
    p.add_argument("--C2", type=int, default=0)
    p.add_argument("--C3", type=int, default=0)
    p.add_argument("--C4", type=int, default=0)
    p.add_argument("--capacity", type=int, default=None,
                   help="only supply after owner revalidation")
    p.add_argument("--owner-revalidated", action="store_true")
    args = p.parse_args()

    if args.product_card:
        args.family, args.title = args.product_card
        if args.family not in {"C1", "C2", "C3", "C4"}:
            p.error("FAMILY must be one of C1, C2, C3, C4")
        return cmd_product_card(args)
    if args.inventory_snapshot:
        args.method = args.inventory_snapshot
        return cmd_inventory_snapshot(args)
    if args.photo_index:
        args.photo_dir = args.photo_index
        return cmd_photo_index(args)
    if args.telegram_dry:
        args.cmd = args.telegram_dry
        return cmd_telegram_dry(args)
    if args.selftest:
        return cmd_selftest()

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
