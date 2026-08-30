#!/usr/bin/env python3
"""تست B3 · فرمِ لیدِ پنل → attribution.propose (فقط PROPOSAL، هیچ CONFIRM/پول/fitness).
اثبات: propose→PROPOSAL در ledger · id یکتا · بدونِ اتصال به fitness · fail-closed روی ورودیِ نامعتبر."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("panel-lead")
sys.path.insert(0, str(harness.SELF_OPS / "panel"))
import server        # noqa: E402  — پنلِ واقعی
import attribution   # noqa: E402


def _states(aid: str) -> list:
    return [(r.get("payload") or {}).get("state")
            for r in attribution._ledger().filter(event_type="MONEY_ATTRIBUTION")
            if (r.get("payload") or {}).get("attribution_id") == aid]


def t_submit_creates_proposal():
    res = server.submit_lead("خانم رضایی — نقاشی هال", "دو اتاق", "480", "lead.doer")
    assert res["ok"] and res["attribution_id"].startswith("LEAD-"), res
    assert _states(res["attribution_id"]) == ["PROPOSAL"], _states(res["attribution_id"])


def t_unique_ids():
    a = server.submit_lead("لید الف", "", "100", "lead.doer")["attribution_id"]
    b = server.submit_lead("لید ب", "", "100", "lead.doer")["attribution_id"]
    assert a != b, (a, b)


def t_proposal_never_in_fitness():
    res = server.submit_lead("لید ج", "", "300", "ziman.doer")
    assert res["ok"], res
    assert attribution.confirmed_revenue()["by_cell"].get("ziman.doer") is None  # PROPOSAL ≠ fitness


def t_invalid_no_name_failclosed():
    res = server.submit_lead("", "x", "100", "lead.doer")
    assert res["ok"] is False and "نام" in res["error"], res


def t_invalid_amount_failclosed():
    res = server.submit_lead("لید د", "", "abc", "lead.doer")
    assert res["ok"] is False, res   # ورودیِ بد → خطا، هیچ رویدادی در ledger نوشته نمی‌شود


def t_bad_cell_defaults_to_lead():
    res = server.submit_lead("لید ه", "", "50", "totally.bogus")
    assert res["ok"] and res["cell"] == "lead.doer", res


def t_render_smoke():
    assert b"<form" in server.render_lead_form() and "LEAD".encode() in server.render_lead_form()
    assert b"LEAD-2026" in server.render_lead_done("LEAD-20260708-001", "lead.doer")


if __name__ == "__main__":
    failed = harness.run([
        ("submit → PROPOSAL در ledger", t_submit_creates_proposal),
        ("id هر لید یکتا", t_unique_ids),
        ("PROPOSAL هرگز واردِ fitness نمی‌شود", t_proposal_never_in_fitness),
        ("بدونِ نام → fail-closed", t_invalid_no_name_failclosed),
        ("مبلغِ نامعتبر → fail-closed", t_invalid_amount_failclosed),
        ("cellِ نامعتبر → پیش‌فرضِ lead.doer", t_bad_cell_defaults_to_lead),
        ("render فرم/نتیجه سالم", t_render_smoke),
    ])
    sys.exit(1 if failed else 0)
