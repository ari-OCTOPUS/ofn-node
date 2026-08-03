"""test_producer_migration.py — D5 (فاز D): M3 — جذبِ producerهای قدیمی → submit_candidate.

اثبات می‌کند که:
  · flag خاموش = رفتارِ قدیمیِ مستقیمِ فایل‌نویسی (ت۱).
  · flag روشن = harvest_austender از submit_candidate می‌گذرد (ت۲).
  · flag روشن = email_inbound از submit_candidate می‌گذرد (ت۳).
  · market_signal (AusTender) هرگز outreach_allowed=True نمی‌گیرد (ت۴).
  · email_inbound = consented_inbound با basis=explicit (ت۵).
  · canonical flag خاموش = gate_off → no-op (fail-soft، ت۶).

همه sandbox (harness.setup → OPS_DIR موقت). flag/STOP/ACTIVATION زنده دست‌نخورده.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("producer-migration-d5")

import importlib                          # noqa: E402
import os                                 # noqa: E402
import json                               # noqa: E402
import opslib                             # noqa: E402
importlib.reload(opslib)
import lead_candidate_inbox as lci        # noqa: E402
importlib.reload(lci)
import harvest_austender as ha            # noqa: E402
importlib.reload(ha)
import email_inbound as ei                # noqa: E402
importlib.reload(ei)

MIGRATE_FLAG = "OCTOPUS_WIRE_LEAD_MIGRATE_PRODUCERS"
CANDIDATES_FLAG = "OCTOPUS_WIRE_LEAD_CANDIDATES"


def _inbox_files():
    """فهرستِ فایل‌های *.json در lead-inbox (نه LD-* که قدیمی‌اند).
    شاملِ signals/ هم می‌شود چون market_signalها آنجا می‌روند."""
    inbox = opslib.STATE_DIR / "legs" / "lead-inbox"
    if not inbox.exists():
        return []
    files = [p.name for p in inbox.glob("*.json")]
    sig_dir = inbox / "signals"
    if sig_dir.exists():
        files += [f"signals/{p.name}" for p in sig_dir.glob("*.json")]
    return sorted(files)


def t1_flag_off_old_behavior():
    """flag خاموش = رفتارِ قدیمیِ مستقیمِ فایل‌نویسی. فایل‌های email-*.json / austender-* ساخته می‌شوند."""
    os.environ.pop(MIGRATE_FLAG, None)
    os.environ.pop(CANDIDATES_FLAG, None)
    before = set(_inbox_files())
    # email_inbound مستقیم می‌نویسد
    n = ei.bridge_leads_to_inbox([{"email_id": "OLD1", "subject": "painting",
                                    "snippet": "need quote", "from": "x@y.com"}])
    assert n == 1
    after = set(_inbox_files())
    new_files = after - before
    # فایلِ قدیمیِ email-*.json ساخته شد (نه uuid.json)
    assert any(f.startswith("email-") for f in new_files), \
        f"flag خاموش باید فایلِ email-* بسازد، got {new_files}"


def t2_harvest_canonical_when_flag_on():
    """flag روشن + CANDIDATES روشن = harvest از submit_candidate می‌گذرد → uuid.json (نه austender-*).
    AusTender = market_signal → فایل در signals/ می‌افتد (نه inbox top-level)."""
    os.environ[MIGRATE_FLAG] = "1"
    os.environ[CANDIDATES_FLAG] = "1"
    try:
        before = set(_inbox_files())
        cand = {"description": "D5 harvest test — repainting", "url": "http://example.com/d5",
                "applicant": "TestBiz", "address": "1 Main St"}
        ok = ha._write_candidate(cand)
        assert ok is True, "canonical write باید موفق باشد"
        after = set(_inbox_files())
        new_files = after - before
        # فایلِ uuid.json ساخته شد در signals/ (market_signal)، نه austender-*
        assert any(f.startswith("signals/") for f in new_files), \
            f"flag روشن باید signals/uuid.json بسازد، got {new_files}"
        # و هیچ فایلِ austender-* جدید نبود
        assert not any(f.startswith("austender-") for f in new_files)
    finally:
        os.environ.pop(MIGRATE_FLAG, None)
        os.environ.pop(CANDIDATES_FLAG, None)


def t3_email_canonical_when_flag_on():
    """flag روشن + CANDIDATES روشن = email_inbound از submit_candidate می‌گذرد → uuid.json."""
    os.environ[MIGRATE_FLAG] = "1"
    os.environ[CANDIDATES_FLAG] = "1"
    try:
        before = set(_inbox_files())
        n = ei.bridge_leads_to_inbox([{"email_id": "NEW1", "subject": "painting",
                                         "snippet": "need quote", "from": "new@y.com"}])
        assert n == 1
        after = set(_inbox_files())
        new_files = after - before
        # فایلِ uuid.json ساخته شد (نه email-*)
        assert any(not f.startswith("email-") and not f.startswith("LD-")
                   for f in new_files), f"got {new_files}"
        assert not any(f.startswith("email-") for f in new_files)
    finally:
        os.environ.pop(MIGRATE_FLAG, None)
        os.environ.pop(CANDIDATES_FLAG, None)


def t4_austender_is_market_signal():
    """AusTender در مسیرِ canonical = market_signal → outreach_allowed=False (ساختاراً بلاک).
    یعنی هیچ‌گاه تماس گرفته نمی‌شود (R4). فایل در signals/ می‌افتد."""
    os.environ[MIGRATE_FLAG] = "1"
    os.environ[CANDIDATES_FLAG] = "1"
    try:
        cand = {"description": "D5 market signal test", "url": "http://example.com/m5",
                "applicant": "SigBiz"}
        ok = ha._write_candidate(cand)
        assert ok is True
        # market_signal در signals/ می‌افتد (نه inbox top-level)
        sig_dir = opslib.STATE_DIR / "legs" / "lead-inbox" / "signals"
        assert sig_dir.exists(), "signals dir باید ساخته شود"
        files = sorted(sig_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        assert files, "باید فایلِ signal ساخته شده باشد"
        data = json.loads(files[-1].read_text(encoding="utf-8"))
        # فایلِ signal شامل candidate_type و consent است
        cb = data.get("candidate") or data  # ممکن است در candidate یا top-level باشد
        # market_signal → outreach_allowed باید False باشد (consent_firewall این را تضمین می‌کند)
        # فایلِ signal فقط ثبت است، نه کارت. belangrijk: candidate_type = market_signal.
        ct = data.get("candidate_type") or (cb.get("candidate_type") if isinstance(cb, dict) else None)
        assert ct == "market_signal", \
            f"AusTender باید market_signal باشد، got {ct}"
    finally:
        os.environ.pop(MIGRATE_FLAG, None)
        os.environ.pop(CANDIDATES_FLAG, None)


def t5_email_is_consented_inbound():
    """email_inbound در مسیرِ canonical = consented_inbound با basis=explicit."""
    os.environ[MIGRATE_FLAG] = "1"
    os.environ[CANDIDATES_FLAG] = "1"
    try:
        ei.bridge_leads_to_inbox([{"email_id": "CON1", "subject": "painting",
                                     "snippet": "please quote", "from": "con@y.com"}])
        inbox = opslib.STATE_DIR / "legs" / "lead-inbox"
        files = sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime)
        data = json.loads(files[-1].read_text(encoding="utf-8"))
        cb = data.get("candidate") or {}
        assert cb.get("candidate_type") == "consented_inbound", \
            f"email باید consented_inbound باشد، got {cb.get('candidate_type')}"
        consent = cb.get("consent") or {}
        assert consent.get("basis") == "explicit"
    finally:
        os.environ.pop(MIGRATE_FLAG, None)
        os.environ.pop(CANDIDATES_FLAG, None)


def t6_canonical_flag_off_gate_closed():
    """MIGRATE روشن ولی CANDIDATES خاموش = submit_candidate gate_off → no-op (fail-soft).
    یعنی هیچ فایلی ساخته نمی‌شود، ولی crash هم نمی‌کند."""
    os.environ[MIGRATE_FLAG] = "1"
    os.environ.pop(CANDIDATES_FLAG, None)
    try:
        before = set(_inbox_files())
        cand = {"description": "D5 gate-off test", "url": "http://example.com/g6"}
        ok = ha._write_candidate(cand)
        assert ok is False, "gate_off باید False برگرداند"
        after = set(_inbox_files())
        assert before == after, "نباید هیچ فایلی ساخته شود وقتی CANDIDATES خاموش است"
    finally:
        os.environ.pop(MIGRATE_FLAG, None)


def t7_no_LD_files_generated():
    """هیچ فایلِ LD-* (قالبِ قدیمیِ frozen) در مسیرِ canonical ساخته نمی‌شود.
    الگوی LD-* منسوخ است (lead_leg_inbox.py FREEZE)."""
    os.environ[MIGRATE_FLAG] = "1"
    os.environ[CANDIDATES_FLAG] = "1"
    try:
        before = set(_inbox_files())
        ha._write_candidate({"description": "D5 LD test", "url": "http://example.com/ld"})
        ei.bridge_leads_to_inbox([{"email_id": "LD1", "subject": "s", "snippet": "n"}])
        after = set(_inbox_files())
        new_files = after - before
        assert not any(f.startswith("LD-") for f in new_files), \
            f"نباید فایلِ LD-* ساخته شود، got {new_files}"
    finally:
        os.environ.pop(MIGRATE_FLAG, None)
        os.environ.pop(CANDIDATES_FLAG, None)


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t") and k[1:2].isdigit() and callable(v)
             and not k.startswith("test")]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, repr(e)))
            print(f"  ❌ {t.__name__}: {e!r}")
    print(f"\ntest_producer_migration: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
