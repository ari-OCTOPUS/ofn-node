#!/usr/bin/env python3
"""test_ziman_leg.py — تست‌های pure/offline پای زیمان (صفر شبکه، صفر پول)."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_LEGS = _OPS / "legs"
for p in (str(_OPS), str(_LEGS), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

from leg import TaskPacket  # noqa: E402
from ziman_leg import PRODUCT_FAMILIES, ZimanLeg, default_packet  # noqa: E402


def test_default_packet_isolation():
    pkt = default_packet()
    assert pkt.leg_id == "ziman-gallery"
    assert pkt.organ == "ZIMAN"
    assert pkt.spawn == 0
    assert pkt.secrets == ()
    assert "*" not in pkt.read_allowlist
    assert all(pkt.read_allowlist)


def test_money_link_active_when_ziman_in_table():
    leg = ZimanLeg(organ_table={"ZIMAN": {"floor": 1}}, capacity_ceiling=30)
    assert leg.money_link == "active"


def test_money_link_incubating_without_organ():
    leg = ZimanLeg(organ_table={}, capacity_ceiling=30)
    assert leg.money_link == "incubating"


def test_d4_rejects_over_ceiling():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    g = leg.campaign_check(100)
    assert g["approved"] is False
    assert "D4" in g["reason"] or "رد" in g["reason"]


def test_d4_approves_under_fail_closed_ceiling():
    # CF-06: راهِ زندهٔ D4 اکنون از capacity_fail_closed رد می‌شود → سقفِ مؤثر ۶، نه ۳۰.
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    g = leg.campaign_check(5)
    assert g["approved"] is True
    assert g["ceiling"] == 6 and g["raw_ceiling"] == 30


def test_d4_capacity_fail_closed_caps_at_6():
    # CF-06 regression: ۱۰/هفته با سقفِ خامِ ۳۰ باید رد شود چون سقفِ مؤثر ۶ است.
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    g = leg.campaign_check(10)
    assert g["approved"] is False
    assert g["ceiling"] == 6 and g["raw_ceiling"] == 30


def test_d4_nonnumeric_input_fail_closed():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    g = leg.campaign_check("abc")
    assert g["approved"] is False


def test_d4_zero_ceiling_blocks_volume():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=0)
    g = leg.campaign_check(5)
    assert g["approved"] is False


def test_draft_content_propose_only():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    p = leg.draft_content(kind="caption", product_family="C3", occasion="تولد")
    assert hasattr(p, "kind")
    assert p.kind == "draft_content"
    assert p.payload["publish"] is False
    assert p.payload["draft_only"] is True
    assert "مصنوعی" in p.payload["body"]


def test_draft_does_not_claim_conflicted_capacity_payment_or_delivery():
    """حتی اگر legacy yaml/constructor ظرفیت داشته باشد، draft نباید وعدهٔ عمومی بدهد."""
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    p = leg.draft_content(kind="caption", product_family="C3", occasion="تولد")
    body = p.payload["body"]
    assert "30" not in body
    assert "واحد/هفته" not in body
    assert "PayID" not in body
    assert "پرداخت PayID" not in body
    assert "فقط بعد از تأیید مالک" in body


def test_status_declares_no_public_price_delivery_or_payment_authority():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    s = leg.status_snapshot()
    assert s["capacity_public_claim_allowed"] is False
    assert s["delivery_promise_authority"] is False
    assert s["price_authority"] is False
    assert s["payment_instruction_authority"] is False


def test_draft_c4_local_only_warning():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    p = leg.draft_content(product_family="C4")
    assert "C4" in p.payload["body"] or "محلی" in p.payload["body"]


def test_draft_rejects_over_capacity_campaign():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    r = leg.draft_content(campaign_units=200)
    assert isinstance(r, dict)
    assert r.get("error") == "D4_REJECT"


def test_inventory_report_no_canonical_write():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    p = leg.inventory_report({"C1": 10, "C3": 15, "XX": 1})
    assert p.payload["canonical_write"] is False
    assert "XX" in p.payload["unknown_keys_rejected"]
    # برنامهٔ ۸: خانواده‌ها = خانواده‌های فعالِ پا (کاتالوگِ واقعی F1..F4/OTHER اگر
    # در دسترس باشد، وگرنه fallbackِ قدیمیِ C1–C4). assertionِ قبلی C1–C4 را هاردکد می‌کرد.
    assert set(leg.product_families()) == set(p.payload["families"])
    if not p.payload["catalog"]["loaded"]:          # فقط در حالتِ fallback
        assert set(PRODUCT_FAMILIES) == set(p.payload["families"])


def test_memory_candidate_rejects_secrets():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    r = leg.memory_candidate("api_key=sk-xxx", "file://x")
    assert isinstance(r, dict)
    assert r.get("ok") is False


def test_memory_candidate_provisional():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    p = leg.memory_candidate("C3 is hero candidate", "MANIFEST.yaml#offering")
    assert p.payload["status"] == "provisional"
    assert p.payload["canonical_write"] is False


def test_status_and_digest():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    s = leg.status_snapshot()
    assert s["autonomy"] == "propose-only"
    assert s["organ"] == "ZIMAN"
    d = leg.telegram_digest()
    assert "Ziman" in d
    assert "D4" in d


def test_digest_labels_capacity_as_unverified():
    # I-5: دیجست نباید عددِ خامِ ۳۰ را واقعیتِ تأییدشده جا بزند.
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    d = leg.telegram_digest()
    assert "تأییدنشده" in d
    assert "~6/هفته" in d
    s = leg.status_snapshot()
    assert s["capacity_ceiling_effective"] == 6
    assert s["capacity_ceiling_raw_unverified"] == 30
    assert s["inventory_evidence_class"] in ("UNVERIFIED", "UNKNOWN")


def test_tick_ok():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    r = leg.tick()
    assert r["ok"] is True


def test_read_allowlist_enforced():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    assert leg.read_brief("secret/other.md") is None
    # allowlisted path may or may not exist on disk — not None only if file exists
    note = "03 - Projects/Ziman Galerry/PROJECT.md"
    # just ensure can_read is true structurally
    assert leg.packet.can_read(note)


def test_no_send_methods():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    assert not hasattr(leg, "send")
    assert not hasattr(leg, "publish")
    assert not hasattr(leg, "pay")


def test_wildcard_packet_rejected():
    try:
        TaskPacket(
            leg_id="bad", organ="ZIMAN",
            read_allowlist=("*",), tools=(), budget_aud=0,
        )
        assert False, "should reject wildcard"
    except ValueError:
        pass
