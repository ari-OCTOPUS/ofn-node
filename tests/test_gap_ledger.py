"""تست‌های GAP-LEDGER — invariantها را رمزگذاری می‌کنند، نه رفتار را توصیف.

اصل: نقض invariant = halt نه retry. هر تست اینجا یک قانون آهنین را قفل می‌کند.
اجرا: python -m pytest tests/test_gap_ledger.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "ops" / "gap_sources.yaml"
LEDGER = ROOT / "ops" / "GAP-LEDGER.jsonl"
RENDER = ROOT / "ops" / "GAP-LEDGER.md"
TOOL = ROOT / "tools" / "gap_ledger.py"

SELF_CODING_CLASSES = {"A1", "A2", "A3", "A4", "A5"}

# CODE_CLASS_Z — این مسیرها هرگز توسط patch خودنوشت لمس نمی‌شوند
FORBIDDEN_TOKENS = [
    "money_gate", "allowlist", "gates.json", "secret", "key",
    "policy", "GOV-V6", "executor", "MAY_AUTHORIZE",
]


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    assert LEDGER.exists(), "ledger not generated — run tools/gap_ledger.py --emit"
    return [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def source() -> dict:
    with SOURCE.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_source_validates():
    """منبع curated باید معتبر باشد وگرنه هیچ چیز تولید نمی‌شود."""
    r = run("--check")
    assert r.returncode == 0, r.stderr


def test_hash_chain_verifies_from_zero():
    """زنجیرهٔ هش دستکاری را آشکار می‌کند — باید در CI اجرا شود، نه فقط موجود باشد."""
    r = run("--verify-chain")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["status"] == "OK"


def test_ledger_is_machine_generated_not_handwritten(tmp_path):
    """قانون طلایی NOW.md: خروجی باید بازتولیدپذیر باشد.

    اگر کسی JSONL یا md را دستی ویرایش کند، بازتولید با نسخهٔ روی دیسک فرق می‌کند.
    """
    before_ledger = LEDGER.read_text(encoding="utf-8")
    before_render = RENDER.read_text(encoding="utf-8")
    r = run("--emit")
    assert r.returncode == 0, r.stderr
    assert LEDGER.read_text(encoding="utf-8") == before_ledger, "ledger drifted — hand-edited?"
    assert RENDER.read_text(encoding="utf-8") == before_render, "render drifted — hand-edited?"


def test_every_gap_has_executable_closure_criterion(rows):
    """الگوی GAP-001: verify: <فرمان> → expect: <خروجی>. بدون این، «بسته شد» یک ادعاست."""
    for r in rows:
        assert r["verify"].strip(), f"{r['id']}: empty verify"
        assert r["expect"].strip(), f"{r['id']}: empty expect"


def test_self_codable_gaps_have_single_commit_rollback(rows):
    """هر PR خودنوشت باید در یک commit قابل‌revert باشد."""
    for r in rows:
        if r["self_codable"]:
            assert "revert" in r["rollback"] or "بدون تغییر" in r["rollback"], \
                f"{r['id']}: no single-commit rollback"


def test_self_codable_gaps_have_baseline_action(rows):
    """درس ۰.۸۰=۰.۸۰: بدون baseline، کار زیاد با پیشرفت اشتباه گرفته می‌شود."""
    for r in rows:
        if r["self_codable"]:
            assert r["baseline_action"] and r["baseline_action"].strip(), \
                f"{r['id']}: missing baseline_action"


def test_owner_only_gaps_are_never_self_codable(rows):
    """money/price/ads/send/secrets/policy/restart = owner-only، fail-closed."""
    for r in rows:
        if r["class"] in {"Z", "D"}:
            assert r["self_codable"] is False, f"{r['id']}: class {r['class']} must not be self-codable"


def test_no_self_codable_gap_touches_forbidden_surface(rows):
    """CLASS_Z surface نباید توسط پچ خودنوشت تغییر کند.

    تمایز مهم: «سنجیدن» یک سطح حساس مجاز است، «دست زدن» به آن نه.
    یک pytest یا grep یا git-log فقط‌خواندنی است و دقیقاً همان چیزی است
    که invariantهای CLASS_Z را قفل می‌کند (مانند GAP-037/038/039).
    """
    read_only_markers = ("pytest", "git log", "rg ", "jq", "--json", "--dry-run")
    for r in rows:
        if not r["self_codable"]:
            continue
        blob = f"{r['verify']} {r['rollback']}".lower()
        for tok in FORBIDDEN_TOKENS:
            if tok.lower() in blob:
                assert any(m in blob for m in read_only_markers), \
                    f"{r['id']}: self-codable gap mutates forbidden surface '{tok}'"


def test_verify_status_starts_unvalidated(rows):
    """قانون آهنین: بدون رسید = UNKNOWN، هرگز LIVE."""
    for r in rows:
        assert r["verify_status"] == "UNVALIDATED", \
            f"{r['id']}: verify_status must start UNVALIDATED until first real run"
        assert r["measured_delta"] is None, f"{r['id']}: measured_delta must be null before a run"


def test_ids_are_unique_and_sequential(rows):
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate gap ids"
    for i, r in enumerate(rows):
        assert r["seq"] == i, f"{r['id']}: seq out of order"


def test_blocked_gaps_name_their_blocker(rows):
    """شکاف مسدود باید بگوید چه چیزی آن را مسدود کرده — وگرنه بی‌صدا می‌ماند."""
    for r in rows:
        if r["gov_status"] in {"BLOCKED", "PARKED"} or (r["self_codable"] and r["blocked_by"]):
            assert r["blocked_by"], f"{r['id']}: blocked but no blocker named"


def test_canary_gaps_are_unblocked_and_self_codable(rows):
    """هدف canary باید همین الان قابل‌اجرا باشد — وگرنه canary نیست."""
    for r in rows:
        if r["canary"]:
            assert r["self_codable"], f"{r['id']}: canary must be self-codable"
            assert not r["blocked_by"], \
                f"{r['id']}: canary has blocker '{r['blocked_by']}' — not a valid canary"


def test_loop_budget_respected(rows):
    """قانون ضدِ قحطی تعمیم‌یافته: هیچ کلاسی نباید صف حلقه را ببلعد."""
    ready = [r for r in rows if r["self_codable"] and not r["blocked_by"]]
    assert ready, "no unblocked self-codable gaps — loop has nothing to do"
    by_class: dict[str, int] = {}
    for r in ready:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
    worst = max(by_class.values()) / len(ready)
    assert worst <= 0.60, f"one class holds {worst:.0%} of the queue (>60%)"
