import json

from ofn.adapters.http_api import ApiApp, HostMap
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.tenancy import TenantRegistry

NOW = 1_800_000_000
SECRET = "painting-owner-api-secret"
OWNER_ID = "5001"
PARTNER_ID = "7001"
OWNER_HOST = "panel.test"


def registry():
    return TenantRegistry({
        "lead": PackSpec(tenant=TenantId("lead"), capacity_units_per_week=8, quota_share=0.4),
        "studio": PackSpec(tenant=TenantId("studio"), capacity_units_per_week=5, quota_share=0.2),
    })


def make_app():
    return ApiApp(
        registry(),
        HostMap(tenants={"lead.test": "lead", "studio.test": "studio"}, owner_host=OWNER_HOST),
        bot_tokens={"lead": "lead-token", "studio": "studio-token", "__owner__": "owner-token"},
        session_secret=SECRET,
        owner_user_ids=(OWNER_ID,),
        partner_user_ids={"lead": (PARTNER_ID,), "studio": (PARTNER_ID,)},
        now=lambda: NOW,
        painting_dashboard=lambda: {
            "ok": True,
            "sources": [{"name": "Website", "score": 0.8}],
            "accounts": [],
            "tenders": [],
            "vendor_applications": [],
        },
        painting_leads=lambda: {"ok": True, "leads": []},
        create_painting_account=lambda data: {"ok": True, "account": "lead:acct:test"},
        create_painting_tender=lambda data: {"ok": True, "tender": "lead:tender:test"},
        create_painting_vendor_application=lambda data: {"ok": True, "application": "lead:vendor:test"},
    )


def owner_headers():
    sess = issue_session("owner", OWNER_ID, SECRET, now_epoch_s=NOW)
    return {"host": OWNER_HOST, "authorization": "Bearer " + sess}


def partner_headers():
    sess = issue_session("lead", PARTNER_ID, SECRET, now_epoch_s=NOW)
    return {"host": OWNER_HOST, "authorization": "Bearer " + sess}


def test_owner_painting_dashboard_and_projection_routes_are_no_store():
    app = make_app()
    for path, key in (
        ("/api/v1/owner/painting/dashboard", "ok"),
        ("/api/v1/owner/painting/sources", "sources"),
        ("/api/v1/owner/painting/accounts", "accounts"),
        ("/api/v1/owner/painting/tenders", "tenders"),
        ("/api/v1/owner/painting/vendor-applications", "vendor_applications"),
    ):
        res = app.handle("GET", path, owner_headers(), b"")
        assert res.status == 200, res.body
        assert key in res.body
        assert res.headers.get("Cache-Control") == "private, no-store"


def test_owner_painting_mutation_routes_exist_and_validate_json():
    app = make_app()
    for path, expected in (
        ("/api/v1/owner/painting/accounts", "account"),
        ("/api/v1/owner/painting/tenders", "tender"),
        ("/api/v1/owner/painting/vendor-applications", "application"),
    ):
        bad = app.handle("POST", path, owner_headers(), b"[]")
        assert bad.status == 400
        ok = app.handle("POST", path, owner_headers(), json.dumps({"name": "X"}).encode())
        assert ok.status == 200, ok.body
        assert expected in ok.body


def test_painting_owner_routes_reject_partner_session_on_owner_host():
    app = make_app()
    res = app.handle("GET", "/api/v1/owner/painting/dashboard", partner_headers(), b"")
    assert res.status == 401
