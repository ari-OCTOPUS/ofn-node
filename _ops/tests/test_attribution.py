#!/usr/bin/env python3
"""تست Track B · attribution + reconcile (offline/paper، fail-closed ضدِ گیم).
اثباتِ ناوردی‌ها: PROPOSAL هرگز fitness نمی‌شود · claim بدونِ CSV = هیچ fitness ·
CSVِ match‌خور = CONFIRMED→fitness · out-of-window/amount-mismatch/no-lead_id = UNMATCHED ·
double-claim = نادیده (CONFIRMEDِ اصلی محفوظ، درآمد یک‌بار) · CONFIRMED فقط از actor=reconcile-job."""
import csv as _csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("attribution")
import attribution  # noqa: E402
import reconcile    # noqa: E402
import fitness      # noqa: E402


def _csv_dir(rows: list[dict]) -> Path:
    d = Path(tempfile.mkdtemp(prefix="recon-"))
    with open(d / "drop.csv", "w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(reconcile.COLUMNS))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return d


def _mk(cell, amount, day):
    aid = attribution.propose(cell, amount, day=day)["payload"]["attribution_id"]
    attribution.claim(aid, "INV-" + aid, amount, day=day)
    return aid


def t_propose_mints_never_fitness():
    rec = attribution.propose("lead.t1", 400.0, "کار نقاشی الف", day="2026-07-01")
    assert rec["payload"]["attribution_id"] == "LEAD-20260701-001", rec["payload"]
    assert attribution.confirmed_revenue()["by_cell"].get("lead.t1") is None   # PROPOSAL ≠ fitness


def t_claim_without_csv_no_fitness():
    _mk("lead.t2", 480.0, "2026-07-02")
    rep = reconcile.run(reconcile_dir=_csv_dir([]), write=True)   # هیچ ردیفی
    assert rep["confirmed"] == [], rep
    assert attribution.confirmed_revenue()["by_cell"].get("lead.t2") is None   # claim تنها ≠ fitness


def t_matching_csv_confirms_to_fitness():
    aid = _mk("lead.t3", 480.0, "2026-07-03")
    d = _csv_dir([{"date": "2026-07-05", "amount_aud": "480", "lead_id": aid, "source": "bank"}])
    rep = reconcile.run(reconcile_dir=d, write=True)
    assert [c["attribution_id"] for c in rep["confirmed"]] == [aid], rep
    assert attribution.confirmed_revenue()["by_cell"]["lead.t3"] == 480.0
    frep = fitness.compute(write=False)                          # CONFIRMED → fitness (paper)
    assert frep["attribution"]["revenue_by_cell"].get("lead.t3") == 480.0, frep["attribution"]


def t_out_of_window_unmatched():
    aid = _mk("lead.t4", 300.0, "2026-07-04")
    d = _csv_dir([{"date": "2026-07-20", "amount_aud": "300", "lead_id": aid, "source": "bank"}])  # ۱۶ روز
    rep = reconcile.run(reconcile_dir=d, write=True)
    assert rep["confirmed"] == [] and any("out-of-window" in u["reason"] for u in rep["unmatched"]), rep
    assert attribution.confirmed_revenue()["by_cell"].get("lead.t4") is None


def t_amount_mismatch_unmatched():
    aid = _mk("lead.t5", 300.0, "2026-07-05")
    d = _csv_dir([{"date": "2026-07-06", "amount_aud": "500", "lead_id": aid, "source": "bank"}])
    rep = reconcile.run(reconcile_dir=d, write=True)
    assert rep["confirmed"] == [] and any("amount-mismatch" in u["reason"] for u in rep["unmatched"]), rep


def t_no_lead_id_unmatched():
    d = _csv_dir([{"date": "2026-07-06", "amount_aud": "100", "lead_id": "", "source": "bank"}])
    rep = reconcile.run(reconcile_dir=d, write=True)
    assert rep["confirmed"] == [] and any(u["reason"] == "no-lead_id" for u in rep["unmatched"]), rep


def t_double_claim_dedup():
    aid = _mk("lead.t7", 200.0, "2026-07-07")
    r1 = reconcile.run(reconcile_dir=_csv_dir(
        [{"date": "2026-07-08", "amount_aud": "200", "lead_id": aid, "source": "bank"}]), write=True)
    assert [c["attribution_id"] for c in r1["confirmed"]] == [aid], r1
    r2 = reconcile.run(reconcile_dir=_csv_dir(
        [{"date": "2026-07-09", "amount_aud": "200", "lead_id": aid, "source": "bank"}]), write=True)
    assert r2["confirmed"] == [] and r2["double_claims"], r2
    assert attribution.confirmed_revenue()["by_cell"]["lead.t7"] == 200.0   # درآمد یک‌بار، نه دوبار


def t_confirmed_written_only_by_reconcile_actor():
    aid = _mk("lead.t8", 150.0, "2026-07-08")
    reconcile.run(reconcile_dir=_csv_dir(
        [{"date": "2026-07-09", "amount_aud": "150", "lead_id": aid, "source": "bank"}]), write=True)
    lg = attribution._ledger()
    confirms = [r for r in lg.filter(event_type="MONEY_ATTRIBUTION")
                if (r.get("payload") or {}).get("attribution_id") == aid
                and (r.get("payload") or {}).get("state") in attribution.CONFIRMED_STATES]
    assert confirms and all(r["actor"] == "reconcile-job" for r in confirms), confirms
    ok, msg = lg.verify()
    assert ok, msg   # زنجیرهٔ hash سالم پس از همهٔ appendها


if __name__ == "__main__":
    failed = harness.run([
        ("PROPOSAL mint می‌شود ولی هرگز fitness نیست", t_propose_mints_never_fitness),
        ("claim بدونِ CSV → هیچ کریدیتِ fitness", t_claim_without_csv_no_fitness),
        ("CSVِ match‌خور → CONFIRMED → fitness (paper)", t_matching_csv_confirms_to_fitness),
        ("خارج از پنجرهٔ ۷ روز → UNMATCHED", t_out_of_window_unmatched),
        ("mismatch مبلغ → UNMATCHED", t_amount_mismatch_unmatched),
        ("بدونِ lead_id → UNMATCHED", t_no_lead_id_unmatched),
        ("double-claim → نادیده، درآمد یک‌بار", t_double_claim_dedup),
        ("CONFIRMED فقط با actor=reconcile-job + زنجیره سالم", t_confirmed_written_only_by_reconcile_actor),
    ])
    sys.exit(1 if failed else 0)
