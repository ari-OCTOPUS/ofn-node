"""
Paper-trade cross-cycle tally
==============================
Reads data/paper_ledger.jsonl and prints a calibration report
showing how the bot's signal quality is evolving over time.

Run from project root:
    python paper_report.py

Output covers:
  - Cycle count & date range
  - Macro regime distribution
  - Holder-risk bucket breakdown (max_single_pct)
  - Social spam/galaxy bucket breakdown
  - Veto rule frequency
  - Four gap metrics vs targets (tells you whether calibration is improving)
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))

from modules.paper_trader import PaperTrader

if __name__ == "__main__":
    PaperTrader().print_cross_cycle_tally()
