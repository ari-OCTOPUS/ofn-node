#!/usr/bin/env python3
"""test_raw_store.py — انبارِ خامِ immutable (فازِ صفر، 2026-07-16).
اثبات: ingest idempotent (provider-id اول، fingerprint fallback) · هرگز overwrite ·
هیچ APIِ mutation · شمارشِ صادق. ایزوله با tmp dir. $0."""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
sys.path.insert(0, str(_HERE.parent / "budget"))
import raw_store as rs  # noqa: E402


def t_a_ingest_idempotent_provider_id():
    with tempfile.TemporaryDirectory() as d:
        rd = Path(d)
        recs = [{"external_id": "tx1", "date": "2026-07-01", "amount_cents": -11000, "desc": "A"},
                {"external_id": "tx2", "date": "2026-07-02", "amount_cents": 50000, "desc": "B"}]
        r1 = rs.ingest("pocketsmith", "anz-main", recs, rd)
        assert r1["ok"] and r1["ingested"] == 2 and r1["skipped_existing"] == 0, r1
        r2 = rs.ingest("pocketsmith", "anz-main", recs, rd)      # دوباره — هیچ ثبتِ نو
        assert r2["ingested"] == 0 and r2["skipped_existing"] == 2, r2
        rows = rs.load_raw("pocketsmith", rd)
        assert len(rows) == 2, rows
        # verbatim + hash نگه داشته شده
        assert rows[0]["raw"]["desc"] == "A" and rows[0]["raw_hash"].startswith("sha256:")


def t_b_fingerprint_fallback():
    """بدونِ external_id → fingerprintِ چندفیلدی؛ همان رکورد دوباره → skip."""
    with tempfile.TemporaryDirectory() as d:
        rd = Path(d)
        rec = {"date": "2026-07-01", "amount_cents": -11000, "desc": "BUNNINGS"}
        r1 = rs.ingest("csv-abbas", "acct", [rec], rd)
        r2 = rs.ingest("csv-abbas", "acct", [rec], rd)
        assert r1["ingested"] == 1 and r2["skipped_existing"] == 1, (r1, r2)
        rid = rs.load_raw("csv-abbas", rd)[0]["raw_id"]
        assert ":fp-" in rid, rid                                # fallback مشخصاً fingerprint


def t_c_no_mutation_api():
    """عمداً هیچ update/delete/save-over وجود ندارد — لایهٔ خام immutable است."""
    for banned in ("update", "delete", "remove", "overwrite", "save", "mutate", "edit"):
        assert not hasattr(rs, banned), f"raw_store نباید {banned} داشته باشد"


def t_d_bad_rows_counted_append_only():
    with tempfile.TemporaryDirectory() as d:
        rd = Path(d)
        r = rs.ingest("x", "a", [{"external_id": "ok1"}, "not-a-dict", None], rd)
        assert r["ingested"] == 1 and r["bad"] == 2, r
        # append است نه بازنویسی: ingest بعدی سطرِ قبلی را نگه می‌دارد
        rs.ingest("x", "a", [{"external_id": "ok2"}], rd)
        p = Path(r["file"])
        lines = [ln for ln in p.read_text("utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2, lines
        assert json.loads(lines[0])["raw_id"].endswith(":ok1")   # سطرِ اول سرِ جایش


def t_e_identical_pair_in_batch_both_stored():
    """audit #19/#36: دو تراکنشِ واقعیِ *یکسان* بدونِ external_id در یک batch → هر دو ثبت
    (ordinal #2)؛ re-ingestِ همان batch → هر دو skip (idempotent می‌ماند)."""
    with tempfile.TemporaryDirectory() as d:
        rd = Path(d)
        rec = {"date": "2026-07-01", "amount_cents": -5000, "desc": "COFFEE"}
        r1 = rs.ingest("csv", "acct", [dict(rec), dict(rec)], rd)
        assert r1["ingested"] == 2 and r1["skipped_existing"] == 0, r1
        ids = [row["raw_id"] for row in rs.load_raw("csv", rd)]
        assert len(set(ids)) == 2 and any(i.endswith("#2") for i in ids), ids
        r2 = rs.ingest("csv", "acct", [dict(rec), dict(rec)], rd)
        assert r2["ingested"] == 0 and r2["skipped_existing"] == 2, r2


def t_f_non_utf8_no_crash():
    """audit #16: بایتِ غیرUTF-8 در فایل → خواندن/ingest بدونِ crash."""
    with tempfile.TemporaryDirectory() as d:
        rd = Path(d)
        rs.ingest("x", "a", [{"external_id": "ok1"}], rd)
        p = rd / "x.jsonl"
        p.write_bytes(p.read_bytes() + b"\xff\xfe{bad}\n")
        rows = rs.load_raw("x", rd)                        # نباید raise کند
        assert len(rows) == 1, rows
        r = rs.ingest("x", "a", [{"external_id": "ok2"}], rd)
        assert r["ok"] and r["ingested"] == 1, r


if __name__ == "__main__":
    for f in (t_a_ingest_idempotent_provider_id, t_b_fingerprint_fallback,
              t_c_no_mutation_api, t_d_bad_rows_counted_append_only,
              t_e_identical_pair_in_batch_both_stored, t_f_non_utf8_no_crash):
        f()
        print("ok", f.__name__)
    print("PASS test_raw_store")
