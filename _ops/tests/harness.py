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

# کدِ زیرِ تست = همان درختی که این harness داخلش زندگی می‌کند (worktree)، نه REAL_VAULT.
# تست‌ها باید ماژول‌های _ops را از این ریشه resolve کنند تا صرفِ‌نظر از REAL_VAULT همیشه
# کدِ *خودشان* را بیازمایند (نه درختِ زنده). REAL_VAULT فقط برای *داده/فایلِ واقعی* است.
SELF_OPS = Path(__file__).resolve().parent.parent   # <worktree>/_ops

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
    (ops / "agi2027_runtime").mkdir(parents=True)
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
        # ⚠️ VQ-HARNESS-STATEDIR-001 (۲۰۲۶-۰۷-۳۰، رأیِ مالک «ریشه رو فیکس کن»).
        # `ORG_ROOT` **کافی نبود**: چند ماژول مسیرِ state را از متغیرِ خودشان
        # می‌گیرند و بدونِ آن به درختِ زنده می‌افتند. مصداقِ اثبات‌شده:
        # `memory/memory_store._default_path()` → `OCTOPUS_STATE_DIR` وگرنه
        # `_HERE.parent/state` — یعنی `F:\backup\_ops\state\memory\memory.db` ِ
        # **زنده**. یک اجرای اشکال‌زدایی سه ردیف در DB ِ واقعی نوشت (با
        # `gate.retract` برگشتند، حذف نشدند). هر تستی که حافظه را لمس می‌کرد
        # این نشتی را داشت — و چون گیت پیش‌فرض خاموش است، بی‌صدا بود.
        "OCTOPUS_STATE_DIR": str(ops / "state"),
        # ⚠️ VQ-WAL-RUNTIME-001 (۲۰۲۶-۰۸-۰۳). `lead_outbound_transport._wal_runtime_dir()`
        # این env را از قبل می‌خواند (docstring خودش هم می‌گفت «تست‌ها می‌توانند override
        # کنند») ولی harness هرگز ست نمی‌کرد — پس هر تستی که این ماژول را import می‌کرد
        # (حتی از راهِ SELF_OPS) به `<worktree>/_ops/agi2027_runtime` ِ **tracked** می‌افتاد:
        # فایل‌های واقعیِ کنترل‌پلین (control-actions.sqlite3، value-ledger.jsonl، …) که در
        # git کامیت شده‌اند. یک اجرای اندازه‌گیری کافی بود تا این ظرف‌ها را dirty کند.
        "OCTOPUS_AGI2027_RUNTIME_DIR": str(ops / "agi2027_runtime"),
    }
    os.environ.update(env)
    # Hermetic Talk Discovery: live shell often exports OCTOPUS_WIRE_COLLAB=1 /
    # OCTOPUS_COLLAB_USE_MODEL=1. Suites that need them re-arm explicitly.
    os.environ["OCTOPUS_WIRE_COLLAB"] = "0"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "0"
    # کدِ زیرِ تست = همان tree که این harness داخلش است — نه REAL_VAULT. وگرنه تستِ
    # worktree ماژول‌های _ops را از tree زنده import می‌کند (کدِ کامیت‌نشده ≠ کدِ تحتِ تست).
    _ops_self = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_ops_self / "budget"))
    sys.path.insert(0, str(_ops_self / "debate"))
    sys.path.insert(0, str(_ops_self))

    # ⚠️ VQ-LIVE-STATE-GUARD-001 (۲۰۲۶-۰۸-۰۳). envهای بالا لازم‌اند ولی **کافی نیستند**:
    # هر ماژولی که مسیرش را نسبت به فایلِ خودش حساب کند (`school_bridge.AWARENESS_STATE`)،
    # یا هر تستی که قبل از `setup()` چیزی import کند، همچنان به `F:\backup\_ops\state`
    # می‌افتد. سنجهٔ ۵۴۰-تستیِ ۰۸-۰۳ چهار نمونهٔ زنده پیدا کرد — یکی اتصالِ **نوشتنی**
    # به `chrono.db`. گارد به‌جای ست‌کردنِ مسیر، خودِ نوشتن را می‌گیرد.
    # گاردِ **شبکه** اینجا مسلح نمی‌شود: `test_llm_routing_smoke` عمداً تماسِ زنده
    # می‌زند. آن یکی فقط در runner ِ ایزوله بالا می‌آید.
    if (os.environ.get("OCTOPUS_TEST_ALLOW_LIVE_STATE") or "") != "1":
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import live_state_guard
            live_state_guard.arm("block")
        except Exception as _e:  # noqa: BLE001
            sys.stderr.write(
                f"⚠️  live_state_guard مسلح نشد ({type(_e).__name__}: {_e}) — "
                f"این اجرا می‌تواند داخلِ state ِ زنده بنویسد\n")

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
