"""API contract tests (skip cleanly when the 'api' extra is not installed)."""

import pytest

pytestmark = pytest.mark.l1

fastapi = pytest.importorskip("fastapi", reason="install extras: pip install -e .[api]")
from fastapi.testclient import TestClient  # noqa: E402

from nbb_cp.api.http import create_app  # noqa: E402


@pytest.fixture()
def client(service):
    return TestClient(create_app(service))


class TestContract:
    def test_health_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["mode"] == "shadow"

    def test_state_snapshot(self, client):
        response = client.get("/state")
        assert response.status_code == 200
        assert response.json()["cap_cents"] == 3000

    def test_audit_endpoint_clean(self, client):
        response = client.get("/audit")
        assert response.status_code == 200
        assert response.json() == {"violations": []}

    def test_proposal_created_201(self, client):
        response = client.post(
            "/proposals",
            json={"organ_id": "ziman", "kind": "grant", "amount_cents": 100},
        )
        assert response.status_code == 201
        assert response.json()["admitted"] is True

    def test_gate_denial_is_409_not_500(self, client):
        response = client.post(
            "/proposals",
            json={"organ_id": "ziman", "kind": "grant", "amount_cents": 999999},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["invariant"] == "INV-1"

    def test_invalid_body_is_422(self, client):
        response = client.post(
            "/proposals",
            json={"organ_id": "ziman", "kind": "grant", "amount_cents": -5},
        )
        assert response.status_code == 422

    def test_unknown_kind_is_422(self, client):
        response = client.post(
            "/proposals",
            json={"organ_id": "ziman", "kind": "conquer", "amount_cents": 5},
        )
        assert response.status_code == 422

    def test_verdict_for_unknown_proposal_404(self, client):
        response = client.post(
            "/proposals/ghost/verdict", json={"approved": True, "by": "armin"}
        )
        assert response.status_code == 404

    def test_execute_unknown_proposal_404(self, client):
        assert client.post("/proposals/ghost/execute").status_code == 404

    def test_full_flow_propose_verdict_execute(self, client):
        created = client.post(
            "/proposals",
            json={
                "organ_id": "ziman", "kind": "effect", "amount_cents": 50,
                "rationale": "publish gallery post", "irreversible": True,
            },
        )
        proposal_id = created.json()["proposal_id"]
        denied = client.post(f"/proposals/{proposal_id}/execute")
        assert denied.status_code == 409  # no verdict yet (INV-2)
        client.post(f"/proposals/{proposal_id}/verdict", json={"approved": True, "by": "armin"})
        executed = client.post(f"/proposals/{proposal_id}/execute")
        assert executed.status_code == 200
        assert executed.json()["simulated"] is True  # shadow mode

    def test_kill_recorded(self, client):
        assert client.post("/kill", params={"by": "armin"}).status_code == 200
