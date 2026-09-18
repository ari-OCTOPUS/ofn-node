#!/usr/bin/env python3
"""revenue_drive.py — the standing MONEY loop (REAL_OWNER_GOAL, deterministic, $0).

Owner order 2026-09-13: «ببین چرا پول تولید نمیکنه ... همیشه بهش فکر کنه».
Every run writes a REVENUE_REVIEW receipt with the real money state (orders,
spend, budget runway) and maintains an owner-review queue for the actions that
need owner approval. It NEVER sends anything externally (RED boundary) and
NEVER spends paid API (everything here is deterministic file/receipt math).
"""
import json
import pathlib
import time

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
RECEIPTS = ROOT / "receipts.jsonl"
OWNER_REVIEW = ROOT / "owner-review.json"
STORE_WATCH = pathlib.Path("/home/ari/octopus-mesh/receipts/store-watch.jsonl")
BUDGET_DIR = pathlib.Path("/home/ari/ofn/state/api-budget")
MONTH_CAP = 100.0

ROOT.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def last_store_row():
    try:
        lines = STORE_WATCH.read_text(errors="replace").strip().splitlines()
        return json.loads(lines[-1]) if lines else {}
    except OSError:
        return {}


def budget_state():
    import sys
    sys.path.insert(0, str(BUDGET_DIR))
    try:
        import api_budget
        return api_budget.status()
    except Exception:  # noqa: BLE001 — budget unknown must not kill the loop
        return {}


def zero_order_streak():
    n = 0
    try:
        for line in reversed(STORE_WATCH.read_text(errors="replace").strip().splitlines()):
            try:
                if json.loads(line).get("o") == 0:
                    n += 1
                else:
                    break
            except json.JSONDecodeError:
                break
    except OSError:
        pass
    return n


store = last_store_row()
bst = budget_state()
month_spent = float(bst.get("month_spent_usd") or 0.0)
window_spent = float(bst.get("window_spent_usd") or 0.0)
window_cap = float(bst.get("window_cap_usd") or 0.0)
runway_days = max(0.0, (MONTH_CAP - month_spent) / 10.0)  # steady cap is $10/24h
streak = zero_order_streak()

review = {
    "schema": "octopus.revenue-review.v1", "at": NOW,
    "store_reachable": bool(store.get("d")),
    "orders_last_check": store.get("o"),
    "zero_order_streak_checks": streak,
    "month_spent_usd": round(month_spent, 6),
    "month_budget_remaining_usd": round(MONTH_CAP - month_spent, 6),
    "window_spent_usd": round(window_spent, 6),
    "window_cap_usd": window_cap,
    "budget_runway_days_at_steady_cap": round(runway_days, 1),
    "paid_api_used_this_review": 0.0,
}
with RECEIPTS.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(review, sort_keys=True) + "\n")

# ---- owner-review queue: ONLY real, approval-gated revenue actions ---------
items = []
if review["store_reachable"] and streak >= 48:   # ≥24h of consecutive zero-order checks
    items.append({
        "id": "TRAFFIC-DECISION", "priority": 1,
        "why": "store LIVE but %d consecutive zero-order checks — demand generation is the "
               "bottleneck, not delivery" % streak,
        "owner_choice_needed": [
            "approve an ad/traffic budget (purchase = RED boundary, needs your approval)",
            "OR approve an owner-sent outreach draft list (public comms = RED boundary)",
            "OR name a target market/channel and I will prepare the campaign assets locally"],
    })
if runway_days < 3.0:
    items.append({
        "id": "BUDGET-LOW", "priority": 1,
        "why": "paid-API runway below 3 days at the steady cap",
        "owner_choice_needed": ["raise the monthly cap", "or keep LOCAL_FIRST strictly"]})
OWNER_REVIEW.write_text(json.dumps({"at": NOW, "items": items}, indent=1,
                                    sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(review))
print("owner_review_items:", [i["id"] for i in items])
