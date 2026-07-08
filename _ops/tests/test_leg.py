#!/usr/bin/env python3
"""تست Phase 4 · L-0 + L-1 — چارچوبِ پا و Lead-نقاشی (paper، $0 آفلاین).

L-0 ایزولاسیون (INV-17، IsolationModel.md): پا نمی‌تواند بیرونِ allowlist بخواند؛
secrets همیشه خالی؛ spawn=0؛ خروجی فقط proposal؛ money_linkِ حل‌نشده = incubating.

L-1 Lead-نقاشی: یک دلارِ paper مسیرِ PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED را با
attributionِ درست طی می‌کند. هیچ اثرِ برگشت‌ناپذیری بدونِ human-append شلیک نمی‌شود.

$0 آفلاین: هیچ شبکه/کلیدی. attribution/reconcile واقعی روی ledger موقتِ harness.
organ_table قابل‌تزریق (بدونِ budgets.yaml واقعی برای تستِ incubating).
"""
import csv as _csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("leg")
# مسیرِ legs به sys.path
_LEGS = ENV["ops"] / "legs"
# legs/ موقت نیست (کد واقعی) — از REAL_VAULT بخوان
_REAL_LEGS = Path(r"F:\backup\_ops\legs")
if str(_REAL_LEGS) not in sys.path:
    sys.path.insert(0, str(_REAL_LEGS))

import attribution    # noqa: E402
import reconcile       # noqa: E402
from leg import Leg, TaskPacket, Proposal        # noqa: E402
from lead_leg import LeadLeg, LEAD_CELLS          # noqa: E402


def _packet(**kw):
    """TaskPacket با پیش‌فرض‌های معقول."""
    defaults = {"leg_id": "lead-naghshi", "organ": "LEAD_PAINTING",
                "read_allowlist": ("03 - Projects/Lead-نقاشی/PROJECT.md",),
                "tools": ("draft_quote",), "budget_aud": 5.0, "spawn": 0, "secrets": ()}
    defaults.update(kw)
    return TaskPacket(**defaults)


# ════════════════════════════════════════════════════════════════════════════════
# L-0 · ایزولاسیونِ Worker (INV-17، IsolationModel.md)
# ════════════════════════════════════════════════════════════════════════════════

def t_taskpacket_rejects_wildcard_allowlist():
    """wildcard در read_allowlist ممنوع (D2 — نه کلِ vault)."""
    try:
        TaskPacket(leg_id="x", organ="y", read_allowlist=("*",))
        assert False, "باید رد شود"
    except ValueError as e:
        assert "wildcard" in str(e), e


def t_taskpacket_rejects_empty_allowlist():
    """allowlist خالی ممنوع — پا حداقل یک نوت می‌بیند."""
    try:
        TaskPacket(leg_id="x", organ="y", read_allowlist=())
        assert False, "باید رد شود"
    except ValueError as e:
        assert "read_allowlist" in str(e), e


def t_taskpacket_secrets_always_empty():
    """secrets غیرخالی ممنوع (D1 — اعتبارنامه از مرز عبور نمی‌کند)."""
    try:
        TaskPacket(leg_id="x", organ="y",
                   read_allowlist=("a",), secrets=("TOKEN",))
        assert False, "باید رد شود"
    except ValueError as e:
        assert "secrets" in str(e), e


def t_taskpacket_spawn_always_zero():
    """spawn≠0 ممنوع (INV-17 — worker تا proposal محدود است)."""
    try:
        TaskPacket(leg_id="x", organ="y", read_allowlist=("a",), spawn=1)
        assert False, "باید رد شود"
    except ValueError as e:
        assert "spawn" in str(e), e


def t_taskpacket_rejects_negative_budget():
    """budget منفی ممنوع."""
    try:
        TaskPacket(leg_id="x", organ="y", read_allowlist=("a",), budget_aud=-1.0)
        assert False, "باید رد شود"
    except ValueError:
        pass


def t_leg_cannot_read_outside_allowlist():
    """پا نمی‌تواند نوتِ خارجِ allowlist بخواند (fail-closed: None، نه exception)."""
    ch = Leg(_packet(read_allowlist=("allowed/note.md",)))
    # fs_get فیک: فقط خواندن از دیکشنری
    store = {"allowed/note.md": "hello", "secret/other.md": "TOPSECRET"}
    assert ch.read_brief("allowed/note.md", fs_get=lambda n: store.get(n)) == "hello"
    assert ch.read_brief("secret/other.md", fs_get=lambda n: store.get(n)) is None


def t_leg_can_read_exactly_allowlisted():
    """پا دقیقاً نوت‌های allowlistش را می‌خواند (نه بیشتر)."""
    allow = ("a.md", "b.md")
    ch = Leg(_packet(read_allowlist=allow))
    store = {"a.md": "A", "b.md": "B", "c.md": "C"}
    for n in allow:
        assert ch.read_brief(n, fs_get=lambda k: store.get(k)) == store[n]
    assert ch.read_brief("c.md", fs_get=lambda k: store.get(k)) is None


def t_leg_output_only_proposal():
    """خروجیِ پا فقط proposal است (D3 — structural output confinement).
    هیچ متدِ send/publish/pay/send_message وجود ندارد."""
    ch = Leg(_packet())
    # emit_proposal فقط proposal برمی‌گرداند
    p = ch.emit_proposal("report", {"x": 1})
    assert isinstance(p, Proposal)
    assert p.kind == "report" and p.payload == {"x": 1}
    # provenance رویش مهر خورده
    d = p.to_dict()
    assert d["leg_id"] == "lead-naghshi" and d["hash"]
    # متدهای ممنوع وجود ندارند
    for forbidden in ("send", "publish", "pay", "trade", "send_message", "call_customer"):
        assert not hasattr(ch, forbidden), f"پا نباید {forbidden} داشته باشد"


def t_money_link_incubating_without_organ():
    """پای بدونِ organِ حل‌شده = incubating (INV-14). organ_table فاقد LEAD_PAINTING."""
    organs = {"EXISTING_ORGAN": {}}        # LEAD_PAINTING نیست
    ch = Leg(_packet(organ="LEAD_PAINTING"), organ_table=organs)
    assert ch.money_link == "incubating"
    # incubating → organ_gate.reserve deny می‌کند
    r = ch.reserve_budget(1.0)
    assert r["allow"] is False and "incubating" in r["reason"], r


def t_money_link_active_with_organ():
    """پا با organِ موجود = active."""
    organs = {"LEAD_PAINTING": {"floor": 1}}
    ch = Leg(_packet(organ="LEAD_PAINTING"), organ_table=organs)
    assert ch.money_link == "active"


def t_incubating_cannot_reserve_budget():
    """پای incubating هرگز بودجه نمی‌گیرد (fail-closed)."""
    organs = {"OTHER": {}}
    ch = Leg(_packet(organ="LEAD_PAINTING"), organ_table=organs)
    r = ch.reserve_budget(0.5)
    assert r["allow"] is False


def t_task_budget_cap_enforced():
    """سقفِ hardِ task_packet.budget_aud اعمال می‌شود (وقتی active)."""
    organs = {"LEAD_PAINTING": {"floor": 1}}
    ch = Leg(_packet(organ="LEAD_PAINTING", budget_aud=2.0), organ_table=organs)
    # بالای سقفِ task → deny (قبل از organ_gate)
    r = ch.reserve_budget(3.0)
    assert r["allow"] is False and "over-task-budget" in r["reason"], r


def t_status_readonly_snapshot():
    """status یک snapshot فقط‌خواندنی است (شامل secrets_count=0)."""
    ch = Leg(_packet())
    s = ch.status()
    assert s["money_link"] in ("active", "incubating")
    assert s["secrets_count"] == 0
    assert s["spawn"] == 0
    assert s["proposals_emitted"] == 0


# ════════════════════════════════════════════════════════════════════════════════
# L-1 · Lead-نقاشی — یک دلارِ paper: PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED
# ════════════════════════════════════════════════════════════════════════════════

def _csv_dir(rows):
    d = Path(tempfile.mkdtemp(prefix="leg-recon-"))
    with open(d / "drop.csv", "w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(reconcile.COLUMNS))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return d


def _lead_leg():
    """LeadLeg با attribution/reconcile واقعی روی ledger موقت."""
    return LeadLeg(_packet(organ="LEAD_PAINTING"),
                   organ_table={"LEAD_PAINTING": {"floor": 1}},
                   attribution=attribution, reconcile=reconcile)


def t_intake_mints_proposal_only():
    """intake فقط PROPOSAL mint می‌کند — نه پول، نه ارسال."""
    leg = _lead_leg()
    r = leg.intake("بازسازی آشپزخانه", 5000.0, "lead.doer", "سیدنی")
    assert r["ok"] is True, r
    assert r["attribution_id"].startswith("LEAD-"), r
    # هنوز CLAIMED/CONFIRMED نیست
    rev = leg.confirmed_revenue()
    assert rev["by_cell"].get("lead.doer") is None     # PROPOSAL ≠ fitness


def t_intake_invalid_name_failclosed():
    """نامِ خالی → fail-closed."""
    leg = _lead_leg()
    assert leg.intake("", 100.0)["ok"] is False
    assert leg.intake(None, 100.0)["ok"] is False


def t_intake_invalid_amount_failclosed():
    """مبلغِ غیرعددی → fail-closed."""
    leg = _lead_leg()
    assert leg.intake("نام", "یک میلیون")["ok"] is False
    assert leg.intake("نام", -5.0)["ok"] is False


def t_intake_unknown_cell_defaults():
    """cell ناشناخته → پیش‌فرضِ lead.doer."""
    leg = _lead_leg()
    r = leg.intake("نام", 100.0, "bogus.cell")
    assert r["ok"] and r["cell"] == "lead.doer", r


def t_draft_quote_has_attribution_id():
    """draft_quote حاوی attribution_id است (Track B carrier — روی quote چاپ می‌شود)."""
    leg = _lead_leg()
    intake = leg.intake("کار نقاشی", 4000.0, "lead.doer")
    aid = intake["attribution_id"]
    p = leg.draft_quote(aid, "نقاشیِ داخلی ۳ خوابه", (4500.0, 6000.0),
                        assumptions=["دو رو رنگ", "بدون داربست"])
    assert p.kind == "draft_quote"
    assert p.payload["attribution_id"] == aid
    assert p.payload["price_range_aud"] == [4500.0, 6000.0]
    assert p.payload["draft_only"] is True
    # ضدِ scope-creep: not_included موجود
    assert len(p.payload["not_included"]) >= 1
    # provenance
    assert p.to_dict()["hash"]


def t_draft_quote_no_irreversible_effect():
    """draft_quote هیچ اثرِ بیرونی ندارد — فقط proposal در حافظه."""
    leg = _lead_leg()
    intake = leg.intake("کار", 1000.0)
    p = leg.draft_quote(intake["attribution_id"], "scope", (900.0, 1100.0))
    # فقط در proposals است، نه در ledger
    assert p in leg.proposals
    lg = attribution._ledger()
    # نوعِ draft_quote در ledger نیست (فقط MONEY_ATTRIBUTION از intake)
    types = {(r.get("payload") or {}).get("state") for r in
             lg.filter(event_type="MONEY_ATTRIBUTION")}
    assert "draft_quote" not in types


def t_claim_advances_to_claimed_only():
    """claim → CLAIMED، نه CONFIRMED. هنوز fitness نیست."""
    leg = _lead_leg()
    intake = leg.intake("کار", 2000.0, "lead.doer", day="2026-07-08")
    aid = intake["attribution_id"]
    r = leg.claim(aid, "INV-001", 2000.0, day="2026-07-08")
    assert r["ok"] and r["state"] == "CLAIMED", r
    # هنوز CONFIRMED نیست
    assert leg.confirmed_revenue()["by_cell"].get("lead.doer") is None


def t_paper_dollar_full_cycle():
    """دلارِ paperِ کامل: PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED با attribution درست.
    این گیتِ P4 است: اولین دلارِ CONFIRMED با attribution_coverage."""
    leg = _lead_leg()
    # ۱) intake = PROPOSAL
    intake = leg.intake("نقاشیِ نمای ساختمان", 5500.0, "lead.doer", day="2026-07-08")
    aid = intake["attribution_id"]
    assert aid.startswith("LEAD-20260708-")
    # ۲) draft quote (با attribution_id روی آن)
    leg.draft_quote(aid, "نمای ساختمان ۲۰۰m²", (5000.0, 6000.0))
    # ۳) claim = CLAIMED (کوت ارسال شد)
    leg.claim(aid, "INV-2026-001", 5500.0, day="2026-07-08")
    # ۴) reconcile با CSV → CONFIRMED (در پنجرهٔ ۷ روز)
    d = _csv_dir([{"date": "2026-07-10", "amount_aud": "5500", "lead_id": aid, "source": "bank"}])
    rep = leg.run_reconcile(reconcile_dir=d, write=True)
    assert [c["attribution_id"] for c in rep["confirmed"]] == [aid], rep
    assert rep["confirmed"][0]["amount_aud"] == 5500.0
    # ۵) fitness فقط CONFIRMED را می‌شمارد
    rev = leg.confirmed_revenue()
    assert rev["by_cell"]["lead.doer"] == 5500.0, rev
    # coverage یک متریکِ جهانی است (از کلِ ledger)؛ اینجا فقط بررسی می‌کنیم که
    # حداقل یک confirmation هست و خودِ این دلار CONFIRMED شد.
    assert rev["confirmed"] >= 1, rev


def t_no_confirm_without_matching_csv():
    """بدونِ CSVِ match‌خور → این لید در CLAIMED می‌ماند، هرگز CONFIRMED.
    (by_cell انباشتِ جهانی است؛ بررسیِ per-id از fold().)"""
    leg = _lead_leg()
    intake = leg.intake("کار بدونِ CSV", 3000.0, "lead.doer", day="2026-07-08")
    aid = intake["attribution_id"]
    leg.claim(aid, "INV-NOCSV", 3000.0, day="2026-07-08")
    # reconcile با CSVِ خالی
    rep = leg.run_reconcile(reconcile_dir=_csv_dir([]), write=True)
    assert rep["confirmed"] == []
    # این لید خاص هنوز CLAIMED است، نه CONFIRMED
    latest = attribution.fold()
    assert latest.get(aid, {}).get("state") == "CLAIMED", latest.get(aid)


def t_leg_does_not_write_confirmed():
    """پا هرگز CONFIRMED نمی‌نویسد — فقط reconcile-job. این structural است."""
    leg = _lead_leg()
    intake = leg.intake("کار", 1500.0, "lead.doer", day="2026-07-08")
    aid = intake["attribution_id"]
    leg.claim(aid, "INV", 1500.0, day="2026-07-08")
    d = _csv_dir([{"date": "2026-07-09", "amount_aud": "1500", "lead_id": aid, "source": "bank"}])
    leg.run_reconcile(reconcile_dir=d, write=True)
    # CONFIRMED را فقط actor=reconcile-job نوشته
    lg = attribution._ledger()
    confirms = [r for r in lg.filter(event_type="MONEY_ATTRIBUTION")
                if (r.get("payload") or {}).get("attribution_id") == aid
                and (r.get("payload") or {}).get("state") in attribution.CONFIRMED_STATES]
    assert confirms and all(r["actor"] == "reconcile-job" for r in confirms), confirms
    ok, msg = lg.verify()
    assert ok, msg


def t_customer_contact_is_human_gated():
    """تماسِ مشتری human-gated است — پا فقط draft تولید می‌کند، نه فراخوانی.
    این با نداشتنِ متدِ call/send نشان داده می‌شود."""
    leg = _lead_leg()
    intake = leg.intake("کار", 800.0)
    p = leg.draft_quote(intake["attribution_id"], "scope", (700.0, 900.0))
    assert p.payload["next_step"].startswith("تماس")     # next_step = human-gated
    # پا ابزارِ تماس ندارد
    assert not hasattr(leg, "call") and not hasattr(leg, "send")


if __name__ == "__main__":
    failed = harness.run([
        # L-0 ایزولاسیون
        ("[L-0] wildcard در allowlist ممنوع", t_taskpacket_rejects_wildcard_allowlist),
        ("[L-0] allowlist خالی ممنوع", t_taskpacket_rejects_empty_allowlist),
        ("[L-0] secrets غیرخالی ممنوع (D1)", t_taskpacket_secrets_always_empty),
        ("[L-0] spawn≠0 ممنوع (INV-17)", t_taskpacket_spawn_always_zero),
        ("[L-0] budget منفی ممنوع", t_taskpacket_rejects_negative_budget),
        ("[L-0] خواندنِ خارجِ allowlist = رد", t_leg_cannot_read_outside_allowlist),
        ("[L-0] خواندنِ دقیقِ allowlist", t_leg_can_read_exactly_allowlisted),
        ("[L-0] خروجی فقط proposal (D3) + متدهای ممنوع نیست", t_leg_output_only_proposal),
        ("[L-0] money_link: نبودِ organ = incubating", t_money_link_incubating_without_organ),
        ("[L-0] money_link: organ موجود = active", t_money_link_active_with_organ),
        ("[L-0] incubating نمی‌تواند بودجه بگیرد", t_incubating_cannot_reserve_budget),
        ("[L-0] سقفِ task_budget اعمال می‌شود", t_task_budget_cap_enforced),
        ("[L-0] status فقط‌خواندنی (secrets_count=0)", t_status_readonly_snapshot),
        # L-1 Lead-نقاشی
        ("[L-1] intake فقط PROPOSAL (نه پول/ارسال)", t_intake_mints_proposal_only),
        ("[L-1] intake نامِ خالی → fail-closed", t_intake_invalid_name_failclosed),
        ("[L-1] intake مبلغِ نامعتبر → fail-closed", t_intake_invalid_amount_failclosed),
        ("[L-1] intake cell ناشناخته → پیش‌فرض", t_intake_unknown_cell_defaults),
        ("[L-1] draft_quote حاوی attribution_id", t_draft_quote_has_attribution_id),
        ("[L-1] draft_quote هیچ اثرِ بیرونی ندارد", t_draft_quote_no_irreversible_effect),
        ("[L-1] claim → CLAIMED نه CONFIRMED", t_claim_advances_to_claimed_only),
        ("[L-1] دلارِ paperِ کامل: PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED", t_paper_dollar_full_cycle),
        ("[L-1] بدونِ CSVِ match → CLAIMED می‌ماند", t_no_confirm_without_matching_csv),
        ("[L-1] پا CONFIRMED نمی‌نویسد (فقط reconcile-job)", t_leg_does_not_write_confirmed),
        ("[L-1] تماسِ مشتری human-gated (پا call/send ندارد)", t_customer_contact_is_human_gated),
    ])
    sys.exit(1 if failed else 0)
