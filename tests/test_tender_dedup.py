"""I2 exact-dedup behaviour on painting_tenders (via create_tender UPSERT).

Proves the Definition of Done: replaying an identical tender payload many
times yields exactly ONE row, and a changed close date updates the same row
(revision) rather than creating a duplicate.
"""
import os
import tempfile
from ofn.adapters.lead_store import LeadStore

NOW = "2027-01-15T08:00:00Z"


def store():
    d = tempfile.TemporaryDirectory()
    st = LeadStore(os.path.join(d.name, "painting.sqlite"))
    return d, st


def _tender(tid="lead:tender:buysw:aaaa-1111", closing="2026-09-15T17:00:00Z"):
    return {
        "tender_id": tid,
        "title": "External Painting Services - Bankstown Public School",
        "source": "buy_nsw_etendering",
        "location": "Sydney",
        "closing_at": closing,
        "access_mode": "official_api",
        "score_inputs": {"P": .9, "G": .9, "E": .7, "D": .8, "M": .5, "Q": .7, "R": .3, "C": .3},
    }


# ---- 1. replay 100x -> exactly ONE row ----
def test_replay_100x_single_row():
    d, st = store()
    try:
        for _ in range(100):
            res = st.create_tender("lead", _tender(), now_iso=NOW)
            assert res["ok"] is True
        rows = st.tenders("lead", limit=500)
        matching = [r for r in rows if r["tender_id"] == "lead:tender:buysw:aaaa-1111"]
        assert len(matching) == 1, f"expected 1 row, got {len(matching)}"
    finally:
        st.close()
        d.cleanup()


# ---- 2. changed close date -> same row updated (revision, not duplicate) ----
def test_changed_close_date_is_revision_not_duplicate():
    d, st = store()
    try:
        st.create_tender("lead", _tender(closing="2026-09-15T17:00:00Z"), now_iso=NOW)
        st.create_tender("lead", _tender(closing="2026-09-20T17:00:00Z"), now_iso=NOW)
        rows = st.tenders("lead", limit=500)
        matching = [r for r in rows if r["tender_id"] == "lead:tender:buysw:aaaa-1111"]
        assert len(matching) == 1, f"expected 1 row after date change, got {len(matching)}"
        assert matching[0]["closing_at"] == "2026-09-20T17:00:00Z", "close date should be updated"
    finally:
        st.close()
        d.cleanup()


# ---- 3. different tender_id -> two distinct rows (no false merge) ----
def test_distinct_ids_stay_separate():
    d, st = store()
    try:
        st.create_tender("lead", _tender(tid="lead:tender:buysw:aaaa-1111"), now_iso=NOW)
        st.create_tender("lead", _tender(tid="lead:tender:buysw:bbbb-2222"), now_iso=NOW)
        rows = st.tenders("lead", limit=500)
        ids = {r["tender_id"] for r in rows}
        assert "lead:tender:buysw:aaaa-1111" in ids
        assert "lead:tender:buysw:bbbb-2222" in ids
    finally:
        st.close()
        d.cleanup()


# ---- 4. tenant isolation: same tender_id under different tenant stays separate ----
def test_tenant_isolation():
    d, st = store()
    try:
        st.create_tender("lead", _tender(), now_iso=NOW)
        rows_lead = st.tenders("lead", limit=500)
        rows_other = st.tenders("other", limit=500)
        assert len(rows_lead) >= 1
        assert all(r["tenant_id"] == "lead" for r in rows_lead)
        assert len(rows_other) == 0, "other tenant must not see lead's tenders"
    finally:
        st.close()
        d.cleanup()


# ---- 5. normalization invariant: title variants collapse to the SAME tender_id ----
# Guards _slug() behaviour. If someone weakens _slug (e.g. removes .lower()),
# dedup silently breaks and duplicate tenders slip through. This locks it.
def test_title_variants_dedupe_via_slug():
    d, st = store()
    try:
        # same tender, no RFTUUID -> tender_id derived from title via _slug
        base = {
            "title": "External Painting - School X",
            "source": "buy_nsw_etendering",
            "score_inputs": {"P": .9, "G": .9, "E": .7, "D": .8, "M": .5, "Q": .7, "R": .3, "C": .3},
        }
        variant = dict(base, title="EXTERNAL   PAINTING  -  SCHOOL  X")  # case + spacing differ

        r1 = st.create_tender("lead", base, now_iso=NOW)
        r2 = st.create_tender("lead", variant, now_iso=NOW)

        # both must resolve to the same derived tender_id
        assert r1["tender"] == r2["tender"], (
            f"title variants produced different ids: {r1['tender']} vs {r2['tender']}"
        )
        rows = st.tenders("lead", limit=500)
        matching = [r for r in rows if r["tender_id"] == r1["tender"]]
        assert len(matching) == 1, f"expected 1 row for title variants, got {len(matching)}"
    finally:
        st.close()
        d.cleanup()
