"""H1 buy.nsw tender adapter — acceptance tests."""
import json
import pathlib
import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "buysw"

# ---- lazy import: adapter not written yet → tests that need it skip gracefully ----
def _import_adapter():
    try:
        from ofn.agents import h1_buysw
        return h1_buysw
    except ImportError:
        pytest.skip("h1_buysw adapter not yet implemented")


# ---- fixtures ----
@pytest.fixture
def schema_example():
    return json.loads((FIXTURES / "schema_example.json").read_text())

@pytest.fixture
def synthetic():
    return json.loads((FIXTURES / "synthetic_tenders.json").read_text())

@pytest.fixture
def accept_tender(synthetic):
    return synthetic["releases"][0]

@pytest.fixture
def reject_location_tender(synthetic):
    return synthetic["releases"][1]

@pytest.fixture
def reject_keyword_tender(synthetic):
    return synthetic["releases"][2]


# ---- 1. parse: schema example has expected structure ----
def test_schema_has_tender_fields(schema_example):
    """Schema example must contain the fields our parser needs."""
    release = schema_example["releases"][0]
    tender = release["tender"]
    assert "RFTUUID" in tender
    assert "title" in tender
    assert "eTenderStatus" in tender
    assert "tenderPeriod" in tender
    assert "deliveryLocation" in tender
    buyer = release["buyer"]
    assert "name" in buyer


# ---- 2. parse tender response ----
def test_parse_tender_response(accept_tender):
    mod = _import_adapter()
    result = mod.parse_tender(accept_tender)
    assert result is not None
    assert result["tender_id"] == "lead:tender:buysw:aaaa1111-2222-3333-444455556666"
    assert result["title"] == "External Painting Services - Bankstown Public School"
    assert result["buyer_name"] == "NSW Department of Education"
    assert result["closing_at"] == "2026-09-15T17:00:00Z"
    assert result["source"] == "buy_nsw_etendering"
    assert result["access_mode"] == "official_api"


# ---- 3. filter: accept painting + Sydney ----
def test_filter_accept_painting_sydney(accept_tender):
    mod = _import_adapter()
    parsed = mod.parse_tender(accept_tender)
    assert mod.filter_painting_tender(parsed) is True


# ---- 4. filter: reject QLD location ----
def test_filter_reject_qld(reject_location_tender):
    mod = _import_adapter()
    parsed = mod.parse_tender(reject_location_tender)
    assert mod.filter_painting_tender(parsed) is False


# ---- 5. filter: reject paint supply (not service) ----
def test_filter_reject_supply(reject_keyword_tender):
    mod = _import_adapter()
    parsed = mod.parse_tender(reject_keyword_tender)
    assert mod.filter_painting_tender(parsed) is False


# ---- 6. deterministic ID from RFTUUID ----
def test_deterministic_id(accept_tender):
    mod = _import_adapter()
    r1 = mod.parse_tender(accept_tender)
    r2 = mod.parse_tender(accept_tender)
    assert r1["tender_id"] == r2["tender_id"]


# ---- 7. minimum value filter ----
def test_minimum_value_reject():
    mod = _import_adapter()
    tiny = {
        "buyer": {"name": "Test"},
        "tender": {
            "RFTUUID": "tiny-0001-0002-0003-000000000000",
            "title": "Painting a garden shed",
            "description": "Small paint job",
            "eTenderStatus": "published",
            "status": "active",
            "tenderPeriod": {"startDate": "2026-08-01T00:00:00Z", "endDate": "2026-09-01T00:00:00Z"},
            "value": {"amount": 200, "currency": "AUD"},
            "deliveryLocation": {"gazetteer": {"scheme": "xNSWRegions", "Identifiers": ["Sydney"]}},
            "items": [{"classification": {"scheme": "UNSPSC", "id": "72151300", "description": "Painting"}}]
        }
    }
    parsed = mod.parse_tender(tiny)
    assert mod.filter_painting_tender(parsed) is False


def test_minimum_value_unknown_keeps():
    """Tender without value → keep (unknown = flag for review, don't discard)."""
    mod = _import_adapter()
    no_val = {
        "buyer": {"name": "Test"},
        "tender": {
            "RFTUUID": "noval-0001-0002-0003-000000000000",
            "title": "External Painting - School",
            "description": "Repaint exterior",
            "eTenderStatus": "published",
            "status": "active",
            "tenderPeriod": {"startDate": "2026-08-01T00:00:00Z", "endDate": "2026-09-01T00:00:00Z"},
            "deliveryLocation": {"gazetteer": {"scheme": "xNSWRegions", "Identifiers": ["Sydney"]}},
            "items": [{"classification": {"scheme": "UNSPSC", "id": "72151300", "description": "Painting"}}]
        }
    }
    parsed = mod.parse_tender(no_val)
    assert mod.filter_painting_tender(parsed) is True


# ---- 8. score_inputs mapping ----
def test_score_inputs_range(accept_tender):
    mod = _import_adapter()
    parsed = mod.parse_tender(accept_tender)
    inputs = mod.build_score_inputs(parsed)
    for key in ("P", "G", "E", "D", "M", "Q", "R", "C"):
        assert key in inputs, f"missing score key {key}"
        assert 0.0 <= inputs[key] <= 1.0, f"{key}={inputs[key]} out of range"


# ---- 9. golden vector: SKIP until API key arrives ----
@pytest.mark.skip(reason="golden_response.json missing — needs real API key from Ari")
def test_golden_vector_filter():
    """Will test filter logic against real API data. Blocked on API key."""
    pass
