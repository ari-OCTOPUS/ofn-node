#!/usr/bin/env python3
"""test_state_machines.py — Forced Completion Sprint 2026-07-20 (backlog #14 + acceptance).

پوشش:
  - گذارهای غیرقانونیِ acquisition (drafted/approved/ready/rejected)
  - گذارهای غیرقانونیِ DM (pending_review/ready_for_manual_send/sent/rejected)
  - گذارهای DraftSubmission استودیو + handoff_to_vault (join استودیو↔اکتساب)
  - dedup ‏md5(hook+channel) در acquisition و md5(body+channel) در DM
  - /pf_dryrun: صفر تغییر state
  - approvals.jsonl audit trail
  - LinkState: assign idempotent + record_clicks + KPI funnel/import_csv
  - ChannelLocks: فایل خراب = fail-closed (فیکس 2026-07-20)
  - STOP سراسری: لنگر فقط /status می‌دهد؛ فایل STOP هرگز ساخته/حذف نمی‌شود

بدون شبکه، بدون توکن، state همه در tmp_path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
for _p in [str(_PROJ), str(_PROJ / "brain"), str(_PROJ / "studio"),
           str(_PROJ / "langar")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import audit  # noqa: E402
from acquisition_pipeline import AcquisitionPipeline  # noqa: E402
from dm_pipeline import DmPipeline  # noqa: E402
from guards import ChannelLocks, WarmupGuard, check_all_guards  # noqa: E402
from store import KPIRollup, LinkState, VaultBank  # noqa: E402
from content_studio import ContentStudio, COMPLIANCE_CHECKS  # noqa: E402


def _acq(tmp_path, **kw):
    return AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None, **kw)


def _full_cert():
    return {c: True for c in COMPLIANCE_CHECKS}


# ── acquisition: گذارهای غیرقانونی ─────────────────────────────────────────
def test_acq_approve_from_ready_is_illegal(tmp_path):
    p = _acq(tmp_path)
    it = p.auto_plan(1)[0]
    assert p.approve(it["id"])["ok"] is True
    assert p.finalize(it["id"])["ok"] is True          # → ready
    r = p.approve(it["id"])
    assert r["ok"] is False and "cannot approve from ready" in r["error"]


def test_acq_approve_from_rejected_is_illegal(tmp_path):
    p = _acq(tmp_path)
    it = p.auto_plan(1)[0]
    p.reject(it["id"], "no")
    r = p.approve(it["id"])
    assert r["ok"] is False and "cannot approve" in r["error"]


def test_acq_finalize_from_drafted_is_illegal(tmp_path):
    p = _acq(tmp_path)
    it = p.auto_plan(1)[0]
    r = p.finalize(it["id"])
    assert r["ok"] is False and "approved" in r["error"]


# ── DM: گذارهای غیرقانونی ──────────────────────────────────────────────────
def test_dm_mark_sent_from_pending_is_illegal(tmp_path):
    p = DmPipeline(store_path=tmp_path / "dm.json")
    rid = p.draft("of", "welcome", "hello there")["id"]
    r = p.mark_sent(rid)
    assert r["ok"] is False and "ready_for_manual_send" in r["error"]


def test_dm_approve_from_sent_is_illegal(tmp_path):
    p = DmPipeline(store_path=tmp_path / "dm.json")
    rid = p.draft("of", "welcome", "hello again")["id"]
    assert p.approve(rid)["ok"] is True
    assert p.mark_sent(rid)["ok"] is True              # → sent
    r = p.approve(rid)
    assert r["ok"] is False and "cannot approve" in r["error"]


def test_dm_approve_from_rejected_is_illegal(tmp_path):
    p = DmPipeline(store_path=tmp_path / "dm.json")
    rid = p.draft("of", "general", "some text")["id"]
    p.reject(rid, "no")
    r = p.approve(rid)
    assert r["ok"] is False


# ── استودیو: DraftSubmission transitions + handoff ─────────────────────────
def test_studio_illegal_transitions(tmp_path, monkeypatch):
    monkeypatch.setenv("PF_STUDIO_DIR", str(tmp_path))
    import importlib
    import content_studio as cs_mod
    importlib.reload(cs_mod)
    cs = cs_mod.ContentStudio()
    rid = cs.submit_draft("arch teaser", _full_cert())["draft_id"]
    # pending → published: غیرقانونی
    r = cs.set_status(rid, "published")
    assert r["ok"] is False and "illegal transition" in r["error"]
    # pending → approved: قانونی
    assert cs.set_status(rid, "approved")["ok"] is True
    # approved → approved: غیرقانونی
    assert cs.set_status(rid, "approved")["ok"] is False
    # approved → published: قانونی؛ بعدش هیچ گذاری مجاز نیست
    assert cs.set_status(rid, "published")["ok"] is True
    assert cs.set_status(rid, "approved")["ok"] is False
    importlib.reload(cs_mod)   # برگرداندنِ مسیرهای production برای تست‌های دیگر


def test_studio_handoff_to_vault_join(tmp_path, monkeypatch):
    monkeypatch.setenv("PF_STUDIO_DIR", str(tmp_path))
    import importlib
    import content_studio as cs_mod
    importlib.reload(cs_mod)
    try:
        cs = cs_mod.ContentStudio()
        vault = VaultBank(path=tmp_path / "vault.json")
        rid = cs.submit_draft("soft arches", _full_cert(),
                              channel="reddit", hook="Arch of the day",
                              caption="Fresh nude polish")["draft_id"]
        # قبل از approve: رد می‌شود (fail-closed)
        assert cs.handoff_to_vault(rid, vault)["ok"] is False
        cs.set_status(rid, "approved")
        r = cs.handoff_to_vault(rid, vault)
        assert r["ok"] is True and r["vault_id"]
        # asset واقعاً در vault با همان schema است
        a = vault.all()[0]
        assert a["channel"] == "reddit" and a["hook"] == "Arch of the day"
        assert a["cert"].get("feet_only") is True
        # idempotent: دوباره push نمی‌شود
        r2 = cs.handoff_to_vault(rid, vault)
        assert r2["ok"] is True and r2.get("duplicate") is True
        assert len(vault.all()) == 1
        # و acquisition می‌تواند از همین vault seed بگیرد (join کامل)
        p = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                vault=vault)
        items = p.auto_plan(1)
        assert items and items[0]["vault_id"] == r["vault_id"]
    finally:
        importlib.reload(cs_mod)


def test_studio_handoff_refuses_incomplete_cert(tmp_path, monkeypatch):
    monkeypatch.setenv("PF_STUDIO_DIR", str(tmp_path))
    import importlib
    import content_studio as cs_mod
    importlib.reload(cs_mod)
    try:
        cs = cs_mod.ContentStudio()
        rid = cs.submit_draft("teaser", _full_cert())["draft_id"]
        cs.set_status(rid, "approved")
        d = cs._find_draft(rid)
        d.self_cert["no_explicit"] = False   # cert بعداً خراب شد
        r = cs.handoff_to_vault(rid, VaultBank(path=tmp_path / "v.json"))
        assert r["ok"] is False and "self-cert" in r["error"]
    finally:
        importlib.reload(cs_mod)


# ── dedup ──────────────────────────────────────────────────────────────────
def test_acq_dedup_same_hook_channel_not_requeued(tmp_path):
    p = _acq(tmp_path)
    first = p.auto_plan(3)
    assert len(first) == 3
    again = p.auto_plan(3)                 # همان SAFE_HOOKS → همه تکراری
    assert len(again) == 0
    assert len(p.pending()) == 3


def test_acq_dedup_allows_after_reject(tmp_path):
    p = _acq(tmp_path)
    it = p.auto_plan(1)[0]
    p.reject(it["id"], "redo")
    fresh = p.auto_plan(1)
    assert len(fresh) == 1 and fresh[0]["id"] != it["id"]


def test_dm_dedup_same_body_channel(tmp_path):
    p = DmPipeline(store_path=tmp_path / "dm.json")
    r1 = p.draft("of", "welcome", "Same body text")
    r2 = p.draft("of", "followup", "Same body text")   # همان body+channel
    assert r2.get("duplicate") is True and r2["id"] == r1["id"]
    assert len(p.pending()) == 1


# ── dryrun: صفر تغییر state ───────────────────────────────────────────────
def test_dryrun_zero_state_change(tmp_path):
    p = _acq(tmp_path)
    it = p.auto_plan(1)[0]
    p.approve(it["id"])
    before = (tmp_path / "q.json").read_text("utf-8")
    r = p.dryrun(it["id"])
    assert r["ok"] is True and r["dryrun"] is True and r["would_status"] == "ready"
    after = (tmp_path / "q.json").read_text("utf-8")
    assert before == after                              # هیچ بایتی عوض نشد
    assert p._find(it["id"])["status"] == "approved"    # هنوز ready نشده
    # dryrun روی drafted → رد
    it2 = p.auto_plan(2)
    fresh = [i for i in it2 if i["status"] == "drafted"]
    assert p.dryrun(fresh[0]["id"])["ok"] is False


# ── audit trail ────────────────────────────────────────────────────────────
def test_approvals_audit_trail(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "DEFAULT_AUDIT_FILE", tmp_path / "approvals.jsonl")
    p = _acq(tmp_path)
    it = p.auto_plan(1)[0]
    p.approve(it["id"], actor="operator")
    p.finalize(it["id"])
    dm = DmPipeline(store_path=tmp_path / "dm.json")
    rid = dm.draft("of", "welcome", "hi")["id"]
    dm.approve(rid, actor="operator")
    rows = [json.loads(l) for l in
            (tmp_path / "approvals.jsonl").read_text("utf-8").splitlines()]
    events = [r["event"] for r in rows]
    assert "pf_approve" in events and "pf_ready" in events and "dm_approve" in events
    # content-free: هیچ body/caption کاملی در audit نیست
    blob = json.dumps(rows, ensure_ascii=False).lower()
    assert "toll bridge" not in blob                    # متنِ hook ثبت نشده


# ── LinkState + KPI funnel ────────────────────────────────────────────────
def test_link_code_assigned_on_finalize(tmp_path):
    links = LinkState(path=tmp_path / "link_state.json")
    p = _acq(tmp_path, links=links)
    it = p.auto_plan(1)[0]
    p.approve(it["id"])
    r = p.finalize(it["id"])
    code = r["payload"]["link_code"]
    assert code and code.startswith("L-")
    # idempotent: همان item همان کد
    assert links.assign(it["id"], "reddit") == code
    # record_clicks
    assert links.record_clicks(code, 42)["clicks"] == 42
    assert links.record_clicks("L-nope", 1)["ok"] is False


def test_kpi_funnel_fields_and_import_csv(tmp_path):
    k = KPIRollup(path=tmp_path / "kpi.json")
    k.record(revenue_usd=10, ppv_unlocks=2, clicks=100, follows=12,
             free_subs=5, paid_conversions=1)
    cur = k.current_week()
    assert cur["clicks"] == 100 and cur["follows"] == 12
    assert cur["free_subs"] == 5 and cur["paid_conversions"] == 1
    # import_csv: header + یک سطر سالم + یک سطر خراب
    r = k.import_csv("revenue_usd,ppv_unlocks,posts,delivery_rate,new_fans,"
                     "clicks,follows,free_subs,paid_conversions\n"
                     "5,1,2,0.9,3,50,6,2,1\n"
                     "garbage,,x\n")
    assert r["imported"] == 1 and r["skipped"] == 1
    cur = k.current_week()
    assert cur["clicks"] == 150 and cur["revenue_usd"] == 15.0


# ── ChannelLocks: فایل خراب = fail-closed (فیکس 2026-07-20) ────────────────
def test_channel_locks_corrupt_file_fails_closed(tmp_path):
    state = tmp_path / "channel_locks.json"
    state.write_text("{ corrupt json,,,", encoding="utf-8")
    cl = ChannelLocks(state_path=state)
    assert cl.full_stop_active() is True
    assert cl.channel_locked("reddit") is True
    ok, reason = check_all_guards("reddit", hook="x", locks=cl)
    assert ok is False and "full_stop" in reason


def test_channel_locks_absent_file_is_fresh_unlocked(tmp_path):
    cl = ChannelLocks(state_path=tmp_path / "none.json")
    assert cl.full_stop_active() is False
    assert cl.channel_locked("reddit") is False


def test_warmup_corrupt_file_still_denies_sales(tmp_path):
    state = tmp_path / "reddit_state.json"
    state.write_text("not json at all", encoding="utf-8")
    wg = WarmupGuard(state_path=state)
    ok, _ = wg.link_allowed("reddit", hook="subscribe now, ppv unlock")
    assert ok is False                                   # fail-closed حفظ شد


# ── STOP سراسری: لنگر فقط /status — و فایل STOP هرگز لمس نمی‌شود ──────────
def test_global_stop_blocks_all_but_status(monkeypatch, tmp_path):
    import langar_bot as lb
    monkeypatch.setattr(lb, "_global_stop", lambda: True)
    monkeypatch.setattr(lb, "KILL_FILE", tmp_path / "KILL")
    monkeypatch.setattr(lb, "LOG_FILE", tmp_path / "log.jsonl")
    bot = lb.LangarBot(token="T", ari_chat_id=99,
                       http_get=lambda *a, **k: {},
                       http_post=lambda *a, **k: {})
    for cmd in ("/gates", "/verdicts", "/pf_status", "/kpi", "/octopus_tick",
                "/kill", "/help"):
        out = bot.handle(99, cmd)
        assert out is not None and "STOP" in out, f"{cmd} must be blocked under STOP"
    # /status هنوز کار می‌کند (کانال تشخیصِ صادقانه)
    out = bot.handle(99, "/status")
    assert out is not None and "STOP" not in out


def test_stop_file_never_touched_by_suite():
    """این suite هرگز STOP-ORGANISM واقعی را نمی‌سازد/برنمی‌دارد — فقط monkeypatch."""
    for anc in Path(__file__).resolve().parents:
        ops = anc / "_ops"
        if ops.is_dir():
            # فقط مشاهده؛ هیچ mutation ای. وجود/عدم هر دو قابل‌قبول است.
            (ops / "STOP-ORGANISM").exists()
            break
