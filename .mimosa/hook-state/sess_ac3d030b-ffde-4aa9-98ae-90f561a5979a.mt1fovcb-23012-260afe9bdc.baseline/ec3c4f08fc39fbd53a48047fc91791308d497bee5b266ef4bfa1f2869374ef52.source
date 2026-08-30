"""
coordinator/config.py — تنظیمات مرکزی سیستم دوربات
=====================================================
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# ── مسیرها ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent   # Ai bots/

QA_DIR       = ROOT / "QuantumAlphaBot"
SENTINEL_DIR = ROOT / "sentinel"
COORD_DIR    = ROOT / "coordinator"

QA_LEDGER    = QA_DIR / "data" / "paper_ledger.jsonl"
DECISIONS_LOG= COORD_DIR / "data" / "decisions.jsonl"

# ── Telegram (همان bot و chat QA) ─────────────────────────────────────────────
load_dotenv(QA_DIR / ".env", override=False)
TELEGRAM_TOKEN   = os.getenv("QUANTUM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("QUANTUM_CHAT_ID", "")

# ── Confluence thresholds ──────────────────────────────────────────────────────
CONFLUENCE_THRESHOLD = 0.55   # بالاتر از این → ACCUMULATE signal
WATCH_THRESHOLD      = 0.35   # بین این دو → در تلگرام نشان داده می‌شه ولی action نیست

# ── وزن‌های ترکیب ─────────────────────────────────────────────────────────────
# qa_score × QA_WEIGHT + sentinel_score × SENT_WEIGHT = confluence
QA_WEIGHT   = 0.45
SENT_WEIGHT = 0.55

# ── QA score bonuses ──────────────────────────────────────────────────────────
EDGE_BONUS      = 0.20   # اضافه می‌شه اگه edge_present != []
FORENSIC_BONUS  = 0.10   # اضافه می‌شه اگه forensics کاملاً clear بود
QA_SCORE_FLOOR  = 35.0   # زیر این → confluence محاسبه نمی‌شه

# ── Sentinel Kelly floor ──────────────────────────────────────────────────────
MIN_KELLY_FOR_ACTION = 0.35   # زیر این → action نیست (حتی اگه confluence بالا باشه)

# ── Gate‌های سخت — همه باید True باشن ────────────────────────────────────────
# این‌ها در confluence_scorer.py چک می‌شن:
#   ① forensic_vetoed == False
#   ② edge_present != []
#   ③ sentinel_quadrant not in {TRAP, UNKNOWN}
#   ④ macro_cq_score > 25  (macro gate هنوز باز باشه)
BLOCKED_QUADRANTS = {"TRAP", "UNKNOWN"}
MACRO_GATE_FLOOR  = 25   # همان ceiling veto_engine

# ── Action routing ────────────────────────────────────────────────────────────
# ENERGY edge → MINE
# DISLOCATION edge → BUY DCA
# YIELD edge → RUN NODE
# ENERGY + DISLOCATION → MINE + BUY (max accumulation)
MINING_EDGES    = {"ENERGY"}
BUYING_EDGES    = {"DISLOCATION"}
NODE_EDGES      = {"YIELD"}

# ── Sentinel integration ─────────────────────────────────────────────────────
SENTINEL_API_DELAY = 1.5   # ثانیه بین API call‌ها
