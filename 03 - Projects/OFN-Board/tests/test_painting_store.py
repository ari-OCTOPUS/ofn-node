import os
import sqlite3
import tempfile

from ofn.adapters.lead_store import LeadStore

NOW = "2027-01-15T08:00:00Z"


def store():
    d = tempfile.TemporaryDirectory()
    st = LeadStore(os.path.join(d.name, "painting.sqlite"))
    return d, st


def test_source_registry_updates_existing_rows():
    d, st = store()
    try:
        st.ensure_source_registry("lead", [{"source_id":"web", "name":"Website", "category":"owned", "integration_path":"webhook", "status":"planned", "intent_score":.5, "risk_score":.2}], NOW)
        st.ensure_source_registry("lead", [{"source_id":"web", "name":"Website", "category":"owned", "integration_path":"webhook", "status":"priority", "intent_score":.9, "risk_score":.1}], NOW)
        rows = st.sources("lead")
        assert len(rows) == 1
        assert rows[0]["status"] == "priority"
        assert rows[0]["score"] > 0
    finally:
        st.close(); d.cleanup()


def test_lead_reads_include_score_explanation():
    d, st = store()
    try:
        out = st.create_lead("lead", {"name":"A", "phone":"1", "job_type":"urgent exterior", "distance_km":5}, now_iso=NOW)
        lead = st.get("lead", out["lead"]["lead_id"])
        assert lead["score_detail"]["explanation"]
        assert st.list_leads("lead")[0]["score_detail"]["recommendation"]
    finally:
        st.close(); d.cleanup()


def test_b2b_tender_vendor_are_draft_first_and_explainable():
    d, st = store()
    try:
        acct = st.create_account("lead", {"business_name":"Example Strata", "segment":"strata", "score_inputs":{"P":.9,"G":.8,"M":.8,"E":.8,"R":.7,"risk":.2,"cost":.2}}, now_iso=NOW)
        assert acct["ok"] and acct["explanation"]
        t = st.create_tender("lead", {"title":"Maintenance Painting", "score_inputs":{"P":.95,"G":.9,"E":.8,"D":.8,"M":.7,"Q":.9,"R":.1,"C":.2}}, now_iso=NOW)
        assert t["ok"] and t["recommendation"] in {"BID", "CONSIDER"}
        blocked_t = st.create_tender("lead", {"title":"Do not submit", "status":"submitted"}, now_iso=NOW)
        assert not blocked_t["ok"]
        v = st.create_vendor_application("lead", {"company_name":"Example FM", "missing":["insurance"]}, now_iso=NOW)
        assert v["ok"] and v["status"] == "pack_incomplete"
        blocked_v = st.create_vendor_application("lead", {"company_name":"Example FM", "status":"approved"}, now_iso=NOW)
        assert not blocked_v["ok"]
    finally:
        st.close(); d.cleanup()


def test_lead_score_uses_lead_priority_model_and_is_incomplete():
    """Gap #1: leads must use the tested `lead_priority` model (stored in
    score_json), not the legacy keyword count. Sparse data flags incomplete."""
    d, st = store()
    try:
        out = st.create_lead("lead", {"name": "A", "phone": "1", "job_type": "quote whole house", "distance_km": 5, "budget_text": "around 4000"}, now_iso=NOW)
        lead = st.get("lead", out["lead"]["lead_id"])
        detail = lead["score_detail"]
        assert detail.get("model") == "lead_priority"
        assert "incomplete" in detail
        assert "recommendation" in detail and detail["recommendation"]
        # The model speaks in components; the legacy heuristic did not.
        assert isinstance(detail.get("components"), dict)
        assert set(detail["components"]) == {"V", "I", "G", "T", "Q", "R", "C"}
    finally:
        st.close(); d.cleanup()


def test_lead_score_json_persists_and_survives_read():
    """score_json is stored on the row, not synthesized at read time."""
    d, st = store()
    try:
        out = st.create_lead("lead", {"name": "B", "phone": "2", "message": "urgent exterior repaint, need a quote this week", "distance_km": 8}, now_iso=NOW)
        lead_id = out["lead"]["lead_id"]
        # Read straight from the row, bypassing the _lead_detail resolver.
        row = st._conn.execute("SELECT score_json FROM painting_leads WHERE lead_id = ?", (lead_id,)).fetchone()
        assert row["score_json"] and row["score_json"] != "{}"
        # get() must surface that same payload (model provenance preserved).
        assert st.get("lead", lead_id)["score_detail"]["model"] == "lead_priority"
    finally:
        st.close(); d.cleanup()


def test_update_lead_recomputes_score_when_relevant_field_changes():
    """Changing message/distance recomputes score, temperature and score_json;
    an explicit owner-set score is not clobbered."""
    d, st = store()
    try:
        out = st.create_lead("lead", {"name": "C", "phone": "3", "message": "thinking about painting", "distance_km": 40}, now_iso=NOW)
        lead_id = out["lead"]["lead_id"]
        before = st.get("lead", lead_id)
        far_score = before["score"]
        # Move close + add urgency/scope: score should rise, payload refresh.
        st.update_lead("lead", lead_id, {"message": "urgent whole house quote this week", "distance_km": 6}, now_iso=NOW)
        after = st.get("lead", lead_id)
        assert after["score"] >= far_score
        assert after["score_detail"]["model"] == "lead_priority"
        # An explicit owner override wins over the model recompute.
        st.update_lead("lead", lead_id, {"score": 12, "message": "changed again"}, now_iso=NOW)
        assert st.get("lead", lead_id)["score"] == 12
    finally:
        st.close(); d.cleanup()


def test_legacy_lead_db_without_score_json_is_migrated_on_boot():
    """A file created by the old schema (no score_json) must be folded forward
    when LeadStore opens it, and its rows must still read without error."""
    d = tempfile.TemporaryDirectory()
    path = os.path.join(d.name, "painting.sqlite")
    # Build an old-shape table exactly as it shipped before score_json existed.
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE painting_leads (lead_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL DEFAULT 'lead', "
        "source TEXT NOT NULL, source_ref TEXT NOT NULL DEFAULT '', customer_name TEXT NOT NULL DEFAULT '', "
        "phone TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', suburb TEXT NOT NULL DEFAULT '', "
        "distance_km REAL, job_type TEXT NOT NULL DEFAULT '', rooms TEXT NOT NULL DEFAULT '', "
        "budget_text TEXT NOT NULL DEFAULT '', message TEXT NOT NULL DEFAULT '', score INTEGER NOT NULL DEFAULT 0, "
        "temperature TEXT NOT NULL DEFAULT 'new', status TEXT NOT NULL DEFAULT 'new', next_action TEXT NOT NULL DEFAULT '', "
        "assigned_to TEXT NOT NULL DEFAULT '', tags_json TEXT NOT NULL DEFAULT '[]', notes TEXT NOT NULL DEFAULT '', "
        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO painting_leads (lead_id, tenant_id, source, customer_name, phone, score, temperature, status, created_at, updated_at) "
        "VALUES ('lead:legacy', 'lead', 'manual', 'Legacy', '1', 55, 'warm', 'new', ?, ?)", (NOW, NOW)
    )
    conn.commit(); conn.close()

    st = LeadStore(path)
    try:
        cols = {r[1] for r in st._conn.execute("PRAGMA table_info(painting_leads)")}
        assert "score_json" in cols                      # migration folded it in
        legacy = st.get("lead", "lead:legacy")
        assert legacy is not None                         # old row still reads
        assert legacy["score_detail"]["explanation"]      # fallback explain works
        # New writes after migration use the model payload.
        fresh = st.create_lead("lead", {"name": "New", "phone": "9", "message": "quote needed"}, now_iso=NOW)
        assert fresh["lead"]["score_detail"]["model"] == "lead_priority"
    finally:
        st.close(); d.cleanup()
