"""External witness — the second-witness locks (OCTOPUS-AUTONOMY-SPEC §2/§6).

Pins: conflicts are recorded and NEVER resolved; the ledger is append-only
with verifiable line hashes; tampering is detected; a value change without a
ruling is a SILENT_FLIP; a claim older than the cadence is a STALE_CLAIM;
and the module has zero send paths and zero writes outside its own ledger."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))
sys.path.insert(0, str(AGENTS.parents[1]))

import external_witness as ew  # noqa: E402


def test_imports() -> None:
    assert ew.SCHEMA == "octopus.external-witness.v1"


def test_ledger_is_append_only_with_verifiable_hashes(tmp_path) -> None:
    ledger = tmp_path / "claims-ledger.jsonl"
    a = ew.append_claim({"claim": "flag:X", "value": "1"}, ledger)
    b = ew.append_claim({"claim": "flag:X", "value": "1",
                         "ruling_id": "gate-2"}, ledger)
    assert ew.verify_ledger(ledger) == []
    assert a["line_sha256"] != b["line_sha256"]


def test_tampered_ledger_line_is_detected(tmp_path) -> None:
    ledger = tmp_path / "claims-ledger.jsonl"
    ew.append_claim({"claim": "flag:X", "value": "1"}, ledger)
    # rewrite a value in place (the exact attack this detects)
    lines = ledger.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[0])
    rec["value"] = "0"  # silent rewrite, hash untouched
    lines[0] = json.dumps(rec, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert ew.verify_ledger(ledger) == ["0"]


def test_value_change_without_ruling_is_silent_flip(tmp_path) -> None:
    ledger = tmp_path / "claims-ledger.jsonl"
    ew.append_claim({"claim": "flag:WAL", "value": "0"}, ledger)
    ew.append_claim({"claim": "flag:WAL", "value": "1"}, ledger)  # بی‌رأی!
    ew.append_claim({"claim": "flag:CAP", "value": "5",
                     "ruling_id": "2026-08-12"}, ledger)
    ew.append_claim({"claim": "flag:CAP", "value": "7",
                     "ruling_id": "ruling-later"}, ledger)  # با رأی
    flips = ew.detect_silent_flip(ledger)
    assert len(flips) == 1
    assert flips[0]["claim"] == "flag:WAL"
    assert flips[0]["from"] == "0" and flips[0]["to"] == "1"


def test_stale_claim_detected_from_registry_age(tmp_path) -> None:
    # FLAG-CLAIMS lives in the repo tree; craft a minimal registry via
    # monkeypatched path
    import datetime as dt
    fake = tmp_path / "FLAG-CLAIMS.json"
    old = (dt.datetime.now(dt.timezone.utc) -
           dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fresh = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fake.write_text(json.dumps({
        "schema": "octopus.flag-claims.v1",
        "claims": [
            {"name": "A", "value": "1", "measured_at": old, "command": "cmd"},
            {"name": "B", "value": "2", "measured_at": fresh,
             "command": "cmd"},
        ]}), encoding="utf-8")
    orig = ew.FLAG_CLAIMS
    ew.FLAG_CLAIMS = fake
    try:
        checks = {c["claim"]: c for c in ew.check_flag_claims()}
    finally:
        ew.FLAG_CLAIMS = orig
    assert checks["flag:A"]["verdict"] == "STALE_CLAIM"
    assert checks["flag:A"]["age_days"] >= 29
    assert checks["flag:B"].get("verdict") != "STALE_CLAIM"


def test_unarmed_run_is_honest_json_never_crashes() -> None:
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "external_witness.py"), "--no-ledger"],
        capture_output=True, text=True, timeout=90, cwd=str(AGENTS),
        env=dict(__import__("os").environ,
                 PYTHONUTF8="1", PYTHONIOENCODING="utf-8"),
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    report = json.loads(proc.stdout)
    assert report["schema"] == "octopus.external-witness.v1"
    assert "never resolved" in report["banner"]


def test_main_head_conflict_is_recorded_not_resolved(monkeypatch) -> None:
    monkeypatch.setattr(ew, "fetch_github_main_sha",
                        lambda timeout=15: ("aaaaaaaa", "stub"))
    monkeypatch.setattr(ew, "read_local_git_head",
                        lambda g: ("bbbbbbbb", "stub"))
    c = ew.check_main_head(Path("."))
    assert c["verdict"] == "DIVERGED"
    assert c["witness"] == "WITNESS_A"
    # و هیچ فیلد «resolved» یا «fixed» وجود ندارد — اختلاف فقط ثبت است
    assert "resolved" not in c and "fix" not in c


# ── منفی‌های §۶ ─────────────────────────────────────────────────────────────

def test_witness_has_zero_send_paths() -> None:
    src = (AGENTS / "external_witness.py").read_text(encoding="utf-8")
    for banned in ("sendMessage", "smtp", "sendmail", "POST"):
        assert banned not in src, banned
    # تنها باز کردن فایل برای نوشتن = لجر (حالت append)
    import re
    writes = re.findall(r'open\([^)]*"[wa+]', src)
    assert writes, "expected at least the ledger append open()"
    for w in writes:
        assert '"a' in w and '"w' not in w and '"r+' not in w, w


def test_witness_never_rewrites_ledger_or_docs() -> None:
    src = (AGENTS / "external_witness.py").read_text(encoding="utf-8")
    assert "os.replace" not in src          # اتمیک-نویسی مال doctor است
    assert "write_text" not in src          # فقط open(...,"a") برای لجر
    assert "OWNER-GO-LOCKS" not in src      # اسناد قفل: خواندنی، نه نوشتنی
