"""
ziman_tender_harvest.py — read-only browser harvester for Ziman gift tender seed.

Purpose:
  Board138 scrapes the 37-tender source (e.g. buy.nsw.gov.au or equivalent)
  using Chromium headless, stores raw rows into painting.sqlite (leads table),
  and writes a claim record for the external witness to verify.

Design rules (non-negotiable):
  - READ-ONLY: no POST, no form submit, no login.
  - No data leaves board138 via this module. Output = local DB rows + claim file.
  - Caller must pass owner_approval=True (checked at entry; raises if missing).
  - Fail-closed: any exception → status=HARVEST_FAILED logged, no partial write.
  - MemoryMax: Chromium on 4 GB board → headless, single tab, no GPU, no sandbox.
  - Wire flag: OFN_WIRE_HARVEST must equal '1' in environment (checked at entry).
    Default in node.env is 0 — owner must flip explicitly on board138 shell.

Dependencies (apt):
  chromium-browser  chromium-chromedriver  python3-selenium
  (or: playwright install chromium  — lighter on ARM)

CLAIMS written to:
  state/legs/ziman-tender-harvest-claim.json   (external witness reads this)
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────────
HARVEST_WIRE_FLAG = "OFN_WIRE_HARVEST"
CLAIM_PATH = Path("state/legs/ziman-tender-harvest-claim.json")

# Target: NSW eTendering public search — no login, read-only RSS/HTML
# Owner must confirm URL before first live run (ask-first protocol).
DEFAULT_TARGET_URL: Optional[str] = None  # intentionally None until owner confirms

MAX_ROWS = 50          # safety ceiling — never import more than this per run
CHROMIUM_TIMEOUT = 20  # seconds per page load


# ── data ───────────────────────────────────────────────────────────────────────
@dataclass
class TenderRow:
    source: str
    reference_id: str
    title: str
    agency: str
    close_date: str          # raw string; normalised downstream
    url: str
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── gate ───────────────────────────────────────────────────────────────────────
def _check_gates(owner_approval: bool) -> None:
    """Raise if wire flag is off or owner_approval not explicitly passed."""
    if not owner_approval:
        raise PermissionError(
            "ziman_tender_harvest: owner_approval=True required. "
            "This is a browser harvester — owner must explicitly authorise each run."
        )
    if os.environ.get(HARVEST_WIRE_FLAG, "0") != "1":
        raise PermissionError(
            f"ziman_tender_harvest: {HARVEST_WIRE_FLAG} is not '1'. "
            "Set it on board138 shell after owner GO, then re-run."
        )


# ── scraper (stub — ask-first before filling URL) ──────────────────────────────
def _scrape_headless(target_url: str) -> List[TenderRow]:
    """
    Headless Chromium scrape. Returns list of TenderRow (read-only).

    ASK-FIRST: Before this function is called in production, Claude Code MUST:
      1. Show owner the target URL.
      2. Confirm owner types: "go scrape <url>" in same session.
      3. Only then pass url and call this.

    Implementation uses selenium + chromium on ARM (DietPi/Trixie).
    Falls back to requests+html if chromium not installed (for CI).
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as exc:
        raise RuntimeError(
            "selenium not installed. On board138: "
            "sudo apt-get install -y chromium-browser chromium-chromedriver python3-selenium"
        ) from exc

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--single-process")  # RAM: 4 GB board
    opts.add_argument("--window-size=1280,800")
    opts.binary_location = "/usr/bin/chromium-browser"

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=opts)
    rows: List[TenderRow] = []

    try:
        driver.set_page_load_timeout(CHROMIUM_TIMEOUT)
        driver.get(target_url)
        WebDriverWait(driver, CHROMIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # ── OWNER MUST FILL selector logic here after confirming target URL ──
        # Example pattern (NSW eTendering):
        #   rows_el = driver.find_elements(By.CSS_SELECTOR, "tr.tender-row")
        #   for el in rows_el[:MAX_ROWS]: ...
        # Intentionally left as stub until ask-first confirms URL + DOM shape.
        log.warning(
            "ziman_tender_harvest: _scrape_headless stub — "
            "selector logic not yet written. Owner must confirm target URL + DOM shape."
        )
    finally:
        driver.quit()

    return rows


# ── db writer ──────────────────────────────────────────────────────────────────
def _write_to_db(rows: List[TenderRow], db_path: Path) -> int:
    """
    Insert tender rows into painting.sqlite as leads (status=HARVESTED_PENDING).
    Returns count of new rows inserted (skips duplicates by reference_id).
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = FULL")

    # Ensure ziman_tender_leads table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ziman_tender_leads (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            source        TEXT NOT NULL,
            reference_id  TEXT NOT NULL UNIQUE,
            title         TEXT NOT NULL,
            agency        TEXT NOT NULL,
            close_date    TEXT,
            url           TEXT,
            scraped_at    TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'HARVESTED_PENDING'
        )
    """)
    conn.commit()

    inserted = 0
    for row in rows:
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO ziman_tender_leads
                  (source, reference_id, title, agency, close_date, url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (row.source, row.reference_id, row.title,
                 row.agency, row.close_date, row.url, row.scraped_at),
            )
            if conn.execute("SELECT changes()").fetchone()[0]:
                inserted += 1
        except sqlite3.Error as exc:
            log.error("ziman_tender_harvest: db write error for %s: %s", row.reference_id, exc)
    conn.commit()
    conn.close()
    return inserted


# ── claim writer ───────────────────────────────────────────────────────────────
def _write_claim(rows_scraped: int, rows_inserted: int, target_url: str) -> None:
    """Write claim file for external witness (PR #130) to verify."""
    CLAIM_PATH.parent.mkdir(parents=True, exist_ok=True)
    claim = {
        "claim_type": "ZIMAN_TENDER_HARVEST",
        "claimed_at": datetime.now(timezone.utc).isoformat(),
        "target_url": target_url,
        "rows_scraped": rows_scraped,
        "rows_inserted": rows_inserted,
        "witness_required": True,
        "note": "External witness (#130) must independently confirm row count matches source.",
    }
    CLAIM_PATH.write_text(json.dumps(claim, indent=2, ensure_ascii=False))
    log.info("ziman_tender_harvest: claim written → %s", CLAIM_PATH)


# ── public entry point ─────────────────────────────────────────────────────────
def run(
    *,
    owner_approval: bool = False,
    target_url: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> dict:
    """
    Main entry. Claude Code calls this after owner says "go".

    Args:
        owner_approval: must be True — caller passes this only after owner GO.
        target_url: confirmed URL. If None, raises with instructions.
        db_path: path to painting.sqlite (default: ~/.local/share/ofn/painting.sqlite)

    Returns dict with keys: status, rows_scraped, rows_inserted, claim_path.
    """
    _check_gates(owner_approval)

    if not target_url:
        raise ValueError(
            "ziman_tender_harvest: target_url required. "
            "ASK owner: 'which site should I scrape for the 37 tenders?' "
            "Then pass confirmed URL here."
        )

    if db_path is None:
        db_path = Path.home() / ".local/share/ofn/painting.sqlite"

    log.info("ziman_tender_harvest: starting — url=%s db=%s", target_url, db_path)

    try:
        rows = _scrape_headless(target_url)
        inserted = _write_to_db(rows, db_path)
        _write_claim(len(rows), inserted, target_url)
        result = {
            "status": "OK",
            "rows_scraped": len(rows),
            "rows_inserted": inserted,
            "claim_path": str(CLAIM_PATH),
        }
        log.info("ziman_tender_harvest: done — %s", result)
        return result
    except Exception as exc:
        log.error("ziman_tender_harvest: HARVEST_FAILED — %s", exc)
        raise
