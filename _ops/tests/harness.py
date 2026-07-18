#!/usr/bin/env python3
"""
harness.py — محیط ایزولهٔ تست: یک مینی-vault موقت می‌سازد و envها را قبل از import
ماژول‌ها ست می‌کند. هیچ تستی به state واقعی (ledger واقعی، budget-state واقعی،
core.db واقعی، HEARTBEAT واقعی) دست نمی‌زند.

الگو در هر فایل تست (ترتیب مهم است — env قبل از import opslib):
    import harness
    ENV = harness.setup("test-name")
    import opslib, ...
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

REAL_VAULT = Path(os.environ.get("REAL_VAULT", r"F:\backup"))
REAL_GENOME = REAL_VAULT / "07 - Knowledge" / "genome-system"

TEST_BUDGETS = """\
global:
  cap_monthly: 30
  currency: AUD
  epoch: daily
  explore_pct: 0.10
  spike_pct: 25
  idle_epochs: 5
  lend_max_pct: 15
  weights: {value: 0.30, urgency: 0.25, efficiency: 0.20, human: 0.20, waste: 0.05}
projects:
  PROJECT_F:      {floor: 3,  human_priority: 2.0, deadline: 2026-07-20}
  ARCHITECT_SYS:  {floor: 2,  human_priority: 1.0}
  GENOME_SYS:     {floor: 2,  human_priority: 1.0}
  ZIMAN:          {floor: 1,  human_priority: 0.5}
routing:
  econ:
    provider: deepseek
    model: deepseek-v4-flash
    base_url: "https://api.deepseek.com"
  reason:
    provider: deepseek
    model: deepseek-v4-flash
    mode: thinking
    base_url: "https://api.deepseek.com"
  orchestr:
    provider: sakana
    model: fugu
    base_url: "TBD"
"""


def setup(name: str) -> dict:
    root = Path(tempfile.mkdtemp(prefix=f"organism-{name}-"))
    ops = root / "_ops"
    (ops / "budget").mkdir(parents=True)
    (ops / "state").mkdir(parents=True)
    (ops / "debate").mkdir(parents=True)
    (ops / "neural").mkdir(parents=True)   # state ماژول‌های neural (OPS_DIR-اول)
    genome = root / "genome-system"
    (genome / "ledger").mkdir(parents=True)
    brain = root / "brain"
    (brain / "logs").mkdir(parents=True)
    arch = root / "04 - Architect System"
    (arch / "prompts").mkdir(parents=True)
    (root / "_memory").mkdir(parents=True)
    (root / "00 - Inbox").mkdir(parents=True)
    (root / "00 - Inbox" / "AGENT_QUESTIONS.md").write_text("# سوالات\n", "utf-8")
    # sandbox ِ state ماژول‌های Project-F (PF_BRAIN_DIR/PF_STUDIO_DIR): تست هرگز کنارِ
    # ماژول (داخلِ repo) نمی‌نویسد. config واقعیِ استودیو فقط کپی/خوانده می‌شود.
    pf_brain = root / "pf" / "brain"
    pf_brain.mkdir(parents=True)
    pf_studio = root / "pf" / "studio"
    pf_studio.mkdir(parents=True)
    _src_cfg = REAL_VAULT / "03 - Projects" / "اونلی فنز" / "studio" / "config.json"
    if _src_cfg.exists():
        shutil.copy2(_src_cfg, pf_studio / "config.json")

    (ops / "budget" / "budgets.yaml").write_text(TEST_BUDGETS, "utf-8")
    # ledger.py واقعی ژنوم — تست پل ledger روی کد واقعی، ولی فایل jsonl موقت
    shutil.copy2(REAL_GENOME / "ledger" / "ledger.py", genome / "ledger" / "ledger.py")
    # پرامپت‌های نقش واقعی
    for f in ("debate-muse-role.txt", "debate-architect-role.txt", "metabolic-governor-v0.1.txt"):
        src = REAL_VAULT / "04 - Architect System" / "prompts" / f
        if src.exists():
            shutil.copy2(src, arch / "prompts" / f)
    # core.db خالی با schema واقعی usage/outbox (زیرمجموعهٔ لازم تست)
    con = sqlite3.connect(brain / "core.db")
    con.execute("CREATE TABLE usage(id INTEGER PRIMARY KEY, day TEXT, provider TEXT, "
                "business TEXT, tokens_in INTEGER, tokens_out INTEGER, cost_usd REAL)")
    con.execute("CREATE TABLE outbox(id INTEGER PRIMARY KEY, business TEXT, channel TEXT, "
                "to_ref TEXT, text TEXT, brief_id INTEGER, status TEXT, notified INTEGER, "
                "ts TEXT, resolved_ts TEXT, detail TEXT)")
    con.commit()
    con.close()

    env = {
        "ORG_ROOT": str(root),
        "OPS_DIR": str(ops),
        "SCRIPTS_DIR": str(REAL_VAULT / "04 - Architect System" / "scripts"),
        "GENOME_DIR": str(genome),
        "BRAIN_DIR": str(brain),
        "BUDGET_STATE": str(ops / "budget" / "budget-state.json"),
        "PF_BRAIN_DIR": str(pf_brain),
        "PF_STUDIO_DIR": str(pf_studio),
    }
    os.environ.update(env)
    # کدِ زیرِ تست = همان tree که این harness داخلش است — نه REAL_VAULT. وگرنه تستِ
    # worktree ماژول‌های _ops را از tree زنده import می‌کند (کدِ کامیت‌نشده ≠ کدِ تحتِ تست).
    _ops_self = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_ops_self / "budget"))
    sys.path.insert(0, str(_ops_self / "debate"))
    sys.path.insert(0, str(_ops_self))
    return {"root": root, "ops": ops, "genome": genome, "brain": brain, "arch": arch, **env}


def add_usage(brain: Path, rows: list[tuple]) -> None:
    """rows: (day, provider, business, tokens_in, tokens_out, cost_usd)"""
    con = sqlite3.connect(brain / "core.db")
    con.executemany("INSERT INTO usage(day,provider,business,tokens_in,tokens_out,cost_usd) "
                    "VALUES (?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


def add_outbox_rows(brain: Path, rows: list[tuple]) -> None:
    """rows: (business, status)"""
    con = sqlite3.connect(brain / "core.db")
    con.executemany("INSERT INTO outbox(business,status,ts) VALUES (?,?,datetime('now'))", rows)
    con.commit()
    con.close()


def add_outbox_jsonl(brain: Path, events: list[dict]) -> None:
    import json
    with open(brain / "logs" / "outbox.jsonl", "a", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def ok(name: str) -> None:
    print(f"  ✅ {name}")


def run(checks: list[tuple[str, callable]]) -> int:
    failed = 0
    for name, fn in checks:
        try:
            fn()
            ok(name)
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")
    return failed
