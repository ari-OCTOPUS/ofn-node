"""R0 spine restore — smoke tests for the revenue-chain agents recovered from
the release/p0 lineage (owner order 2026-09-02, R0-CLOSE lane C).

These are restore-not-rewrite modules: we assert import health, offline
dry-run behaviour (fail-closed, JSON out, never a traceback), and the
presence of the entry points the board's systemd units expect.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

RESTORED = [
    "imap_listener",
    "quote_pipeline",
    "heartbeat",
    "memory_chain",
    "owner_notify",
    "mail_credentials",
    "consent_store",
    "opslib",
]

# D-25 / PORTFOLIO-TENANT-MAP: these names describe nothing in this tree.
RETIRED_VOCABULARY = ("MycoLedger", "EffectorGate")
RESTORED_PATHS = [
    AGENTS / "consent_store.py",
    AGENTS / "imap_listener.py",
    AGENTS / "quote_pipeline.py",
    AGENTS / "heartbeat.py",
    AGENTS / "memory_chain.py",
    AGENTS / "owner_notify.py",
    AGENTS / "mail_credentials.py",
    AGENTS.parent / "budget" / "opslib.py",
]


def test_all_spine_modules_import() -> None:
    for name in RESTORED:
        __import__(name)


def test_imap_listener_dry_run_is_graceful_json() -> None:
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "imap_listener.py"), "--dry"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(AGENTS),
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    payload = json.loads(proc.stdout)
    assert "scanned" in payload and "processed" in payload


def test_quote_pipeline_entrypoint_exists() -> None:
    assert (AGENTS / "quote_pipeline.py").is_file()
    assert (AGENTS / "heartbeat.py").is_file()
    assert (AGENTS.parent / "budget" / "opslib.py").is_file()


def test_restored_sources_omit_retired_vocabulary() -> None:
    """D-25: a negation in a docstring is still the retired token.

    `test_portfolio_map.TestVocabulary` scans shipped sources as raw text.
    Restored p0 files must use the mapped names (risk/consent/release_switch/
    outbox), not the imported aliases.
    """
    for path in RESTORED_PATHS:
        body = path.read_text(encoding="utf-8")
        for name in RETIRED_VOCABULARY:
            assert name not in body, f"{path.name} mentions retired {name!r}"


def test_consent_store_wal_and_full_sync() -> None:
    """CLAUDE.md §7: WAL + synchronous=FULL. NORMAL is not durable under WAL."""
    import consent_store as cs

    with TemporaryDirectory(prefix="ofn-consent-") as tmp:
        store = cs.ConsentStore(path=str(Path(tmp) / "consent.db"))
        try:
            mode = store._conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert str(mode).lower() == "wal"
            # 2 == FULL. NORMAL (1) would trade away power-loss durability.
            assert store._conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        finally:
            store.close()


def test_quote_pipeline_default_is_dry_not_send_authorized() -> None:
    """campaign_envelope_ready / restore ≠ send_authorized.

    cycle() stays dry unless a caller passes dry=False. The CLI requires
    --authorize-send; --dry still wins. quote_sent remains a later, scoped
    authorization — this pin does not grant it.
    """
    import quote_pipeline as qp

    assert inspect.signature(qp.cycle).parameters["dry"].default is True
    src = (AGENTS / "quote_pipeline.py").read_text(encoding="utf-8")
    assert "--authorize-send" in src
    assert "send_authorized" not in src
