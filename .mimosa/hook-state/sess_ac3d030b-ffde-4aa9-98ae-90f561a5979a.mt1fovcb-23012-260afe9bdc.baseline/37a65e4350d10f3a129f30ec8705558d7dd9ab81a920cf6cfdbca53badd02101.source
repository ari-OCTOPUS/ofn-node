"""
coordinator/run.py — orchestrator اصلی
=======================================
اجرا:
  python coordinator/run.py          ← هر ۶ ساعت
  python coordinator/run.py --once   ← یک بار و خروج

pipeline:
  1. paper_ledger.jsonl را می‌خواند (آخرین سیکل QA)
  2. کاندیداها را استخراج می‌کند
  3. Sentinel signals اجرا می‌شود
  4. Confluence score محاسبه می‌شود
  5. Telegram alert فرستاده می‌شود
  6. decisions.jsonl ذخیره می‌شود
"""
import sys, argparse, time
from pathlib import Path
from datetime import datetime

# coordinator خودش را به path اضافه می‌کند
sys.path.insert(0, str(Path(__file__).parent))

from config import DECISIONS_LOG
from candidate_bridge import load_candidates
from confluence_scorer import ConfluenceScorer
from dual_notifier import send, save_decisions


def run_once():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"  COORDINATOR  |  {ts}")
    print(f"{'='*60}")

    # ── Step 1: خواندن آخرین سیکل QA ─────────────────────────────────────
    print("\n── Step 1: Load QA candidates ─────────────────────────────")
    candidates, meta = load_candidates()

    if not candidates:
        print("  No candidates to evaluate — skipping")
        return

    print(f"  {len(candidates)} candidates from cycle {meta.get('cycle_ts','?')[:16]}")

    # ── Step 2: Sentinel signals + Confluence ────────────────────────────
    print("\n── Step 2: Confluence scoring ─────────────────────────────")
    scorer  = ConfluenceScorer()
    results = scorer.score_all(candidates)

    # ── Step 3: نمایش خلاصه ──────────────────────────────────────────────
    print("\n── RESULTS ─────────────────────────────────────────────────")
    print(f"  {'Symbol':<8} {'Score':>5} {'Confluence':>11} {'Sentinel':>12} {'Action'}")
    print(f"  {'-'*60}")
    for r in sorted(results, key=lambda x: -x.confluence):
        print(f"  {r.symbol:<8} {r.final_score:>5.1f} {r.confluence:>11.3f} "
              f"{r.sentinel_quadrant:>12} {r.action}")

    # ── Step 4: Telegram ──────────────────────────────────────────────────
    print("\n── Step 3: Telegram ─────────────────────────────────────────")
    send(results, meta)

    # ── Step 5: Log ───────────────────────────────────────────────────────
    save_decisions(results, meta, DECISIONS_LOG)
    print(f"\n  ✓ Done — {datetime.now().strftime('%H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(description="Dual-Bot Coordinator")
    parser.add_argument("--once", action="store_true", help="یک بار اجرا")
    args = parser.parse_args()

    try:
        run_once()
    except Exception as e:
        print(f"\n[Coordinator] ERROR: {e}")
        raise

    if args.once:
        sys.exit(0)

    import schedule
    schedule.every(6).hours.do(run_once)
    print("\nScheduled every 6h. Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
