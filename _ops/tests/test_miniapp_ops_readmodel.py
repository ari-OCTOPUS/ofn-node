#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_ops_readmodel — /api/ops به‌عنوانِ تنها سطحِ صادقِ خواندنی.

    ادعاهای زیرِ آزمون (هرکدام با یک جهشِ کُشنده روی رشتهٔ یکتا سنجیده شد):
      · هیچ کلیدِ موجودی نه نام عوض کرده نه معنا (owner_auth، actions.registry،
        actions.blocked_prefixes، leads/tasks/value_events).
      · چهار بخشِ تازه (brain/governor/obsidian/next_steps) حاضرند.
      · منبعِ نخواندنیِ brain ⇒ available=false + دلیل، و پاسخ همچنان 200.
      · هر عددِ brain مشتقِ یک فایلِ نام‌برده است، نه عددِ ساختگی.
      · governor هیچ مسیری را بدونِ سنجشِ وجود ادعا نمی‌کند؛ drift مشتق است.
      · obsidian فایلِ غایب را «غایب» گزارش می‌کند (وگرنه خودش drift است).
      · هر زیرمسیر دقیقاً برشِ همان بخش است و **همان** گاردِ والدش را دارد.
      · کش ۲–۵ ثانیه‌ای است و یک خطا هرگز به‌جای موفقیت سرو نمی‌شود.

    سبکِ main-style: harness.setup اول، توابعِ t_*، harness.run، sys.exit.
"""
import hashlib
import hmac
import json
import os
import sys
import tempfile
import urllib.parse
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("miniapp-ops-readmodel")

# انبارِ Ops را **قبل از** هر import به یک پوشهٔ موقت پین کن — وگرنه این تست
# sqlite ِ زندهٔ درختِ کاری را می‌خواند و «برشِ لیدها» با «برشِ کارها» تصادفاً
# یکی می‌شود (هر دو صفر) و جهش نمی‌تواند بکشدش.
_OPS_RT = tempfile.mkdtemp(prefix="ops-readmodel-")
os.environ["OCTOPUS_OPS_RUNTIME_DIR"] = _OPS_RT
os.environ["OCTOPUS_OPS_DB_PATH"] = str(Path(_OPS_RT) / "ops.sqlite3")
os.environ["OCTOPUS_OPS_AUDIT_PATH"] = str(Path(_OPS_RT) / "audit.jsonl")
os.environ["OCTOPUS_OPS_IDEMPOTENCY_PATH"] = str(Path(_OPS_RT) / "idem.sqlite3")

import miniapp_gateway as mg  # noqa: E402
import miniapp_state as ms  # noqa: E402


def _seed():
    """۲ لید و ۱ کار — تا leads_total ≠ tasks_total و برش‌ها قابلِ‌تمیز باشند."""
    from agi2027_control.ops_actions import OpsActionEngine  # noqa: WPS433
    eng = OpsActionEngine(ms._ROOT)
    try:
        owner = {"is_owner": True}
        eng.execute("lead.create", {"handle": "@a", "stage": "new"}, owner,
                    action_id="seed-lead-a")
        eng.execute("lead.create", {"handle": "@b", "stage": "warm"}, owner,
                    action_id="seed-lead-b")
        eng.execute("task.create", {"title": "پیگیری", "kind": "followup"}, owner,
                    action_id="seed-task-a")
    finally:
        eng.close()


_seed()

NOW = 1_785_400_000.0
TOKEN = "123456789:AA" + "y" * 32          # توکنِ **جعلیِ** تستی
OWNER = "777"

# کلیدهایی که قبل از این تغییر وجود داشتند — نامشان قرارداد است، نه سلیقه.
LEGACY_TOP_KEYS = ("status", "leads_total", "lead_stages", "tasks_total",
                   "task_status", "value_events_total", "value_events_per_leg",
                   "owner_auth", "actions")
LEGACY_ACTION_KEYS = ("enabled_when", "registry", "blocked_prefixes",
                      "safe_local_actions", "blocked_external_automation")
NEW_SECTIONS = ("brain", "governor", "obsidian", "next_steps")
SUB_PATHS = ("/api/ops/brain", "/api/ops/leads", "/api/ops/tasks")


def _init_data(user_id=777, auth_date=NOW - 10, token=TOKEN, tamper=False):
    data = {"auth_date": str(int(auth_date)),
            "user": json.dumps({"id": user_id, "first_name": "ari"},
                               ensure_ascii=False)}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    h = hmac.new(secret, dcs.encode("utf-8"), hashlib.sha256).hexdigest()
    if tamper:
        h = ("0" if h[0] != "0" else "1") + h[1:]
    data["hash"] = h
    return urllib.parse.urlencode(data)


def _ops(**kw) -> dict:
    ms.cache_clear()
    return ms.get_ops_state(**kw)


def _get(path: str) -> dict:
    """dispatch واقعی (همان مسیری که gateway می‌رود) → dict ِ decode‌شده."""
    ms.cache_clear()
    st, body, ctype = ms.dispatch_api(path)
    assert st == 200, (path, st, body[:120])
    assert "json" in ctype, ctype
    return json.loads(body)


class _Clock:
    """ساعتِ تزریقی برای کش — تستِ انقضا هرگز به ساعتِ دیوار وابسته نیست."""

    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


# ── ۱. هیچ کلیدِ موجودی نمی‌شکند ─────────────────────────────────────────────
def t_every_pre_existing_key_keeps_its_name_and_meaning():
    d = _ops()
    for k in LEGACY_TOP_KEYS:
        assert k in d, f"کلیدِ موجود گم شد: {k}"
    assert d["status"] == "ok", d.get("status")
    for k in ("leads_total", "tasks_total", "value_events_total"):
        assert isinstance(d[k], int), (k, type(d[k]))
    for k in ("lead_stages", "task_status", "value_events_per_leg"):
        assert isinstance(d[k], dict), (k, type(d[k]))
    for k in ("configured", "bot_token", "owner_id"):
        assert k in d["owner_auth"], f"owner_auth.{k} گم شد"
    for k in LEGACY_ACTION_KEYS:
        assert k in d["actions"], f"actions.{k} گم شد"


def t_the_action_registry_is_read_from_the_engine_not_hand_copied():
    """اگر اکشنی به موتور اضافه شود، این سطح باید خودکار همانی بماند."""
    sys.path.insert(0, str(_OPS)) if str(_OPS) not in sys.path else None
    from agi2027_control.ops_actions import ALLOWED_ACTIONS, BLOCKED_PREFIXES
    a = _ops()["actions"]
    assert a["registry"] == sorted(ALLOWED_ACTIONS), a["registry"]
    assert a["blocked_prefixes"] == list(BLOCKED_PREFIXES), a["blocked_prefixes"]
    assert a["safe_local_actions"] == sorted(ALLOWED_ACTIONS), a["safe_local_actions"]
    assert a["blocked_external_automation"] == list(BLOCKED_PREFIXES)
    for p in ("onlyfans.", "fansly."):
        assert p in a["blocked_prefixes"], p


# ── ۲. چهار بخشِ تازه ────────────────────────────────────────────────────────
def t_the_four_new_sections_are_present_with_their_declared_shape():
    d = _ops()
    for s in NEW_SECTIONS:
        assert s in d, f"بخشِ تازه غایب: {s}"
    b = d["brain"]
    assert set(("available", "daemon", "consolidation")) <= set(b), b.keys()
    for k in ("reachable", "ticks", "errors", "last_tick", "generation"):
        assert k in b["daemon"], f"brain.daemon.{k}"
    for k in ("available", "conclusions_count", "frontier_count", "last_verified"):
        assert k in b["consolidation"], f"brain.consolidation.{k}"
    g = d["governor"]
    for k in ("policy_doc", "canonical_provider", "drift_status", "routes"):
        assert k in g, f"governor.{k}"
    for r in ("local", "fugu", "fugu_ultra", "fugu_cyber"):
        assert r in g["routes"], f"governor.routes.{r}"
    o = d["obsidian"]
    assert "reference_dir_configured" in o and isinstance(o["docs"], dict), o.keys()
    assert isinstance(d["next_steps"], list) and d["next_steps"], d["next_steps"]
    for step in d["next_steps"]:
        assert set(("id", "title", "status")) <= set(step), step
        assert step["status"] in ("done", "open", "unknown"), step


# ── ۳. fail-soft: brain نخواندنی، پاسخ همچنان 200 ────────────────────────────
def t_an_unreadable_brain_is_available_false_with_a_reason_and_still_http_200():
    with tempfile.TemporaryDirectory() as d:
        empty = Path(d) / "gone"                      # عمداً ساخته نمی‌شود
        old = (ms._4D_OUTPUTS, ms._4D_CONSOLIDATION_PY, ms._NEURAL_CONSOLIDATION)
        ms._4D_OUTPUTS = empty
        ms._4D_CONSOLIDATION_PY = empty / "consolidation.py"
        ms._NEURAL_CONSOLIDATION = empty / "consolidation.json"
        try:
            ms.cache_clear()
            st, body, _ = ms.dispatch_api("/api/ops")
            assert st == 200, st                       # ← fail-soft، نه 500
            b = json.loads(body)["brain"]
            assert b["available"] is False, b
            assert b["reason"], "available=false بدونِ دلیل = دروغِ خاموش"
            assert b["daemon"]["reachable"] is False, b["daemon"]
            for k in ("ticks", "errors", "last_tick", "generation"):
                assert b["daemon"][k] is None, (k, b["daemon"][k])
            c = b["consolidation"]
            assert c["available"] is False and c["reason"], c
            for k in ("conclusions_count", "frontier_count", "last_verified"):
                assert c[k] is None, (k, c[k])
            sub = _get("/api/ops/brain")               # زیرمسیر هم 200 می‌ماند
            assert sub["brain"]["available"] is False, sub
        finally:
            (ms._4D_OUTPUTS, ms._4D_CONSOLIDATION_PY,
             ms._NEURAL_CONSOLIDATION) = old
            ms.cache_clear()


def t_a_brain_source_that_raises_never_kills_the_whole_answer():
    def boom(*a, **k):
        raise RuntimeError("منبعِ مغز منفجر شد")

    old = ms._brain_daemon
    ms._brain_daemon = boom
    try:
        ms.cache_clear()
        st, body, _ = ms.dispatch_api("/api/ops")
        assert st == 200, st
        d = json.loads(body)
        assert d["brain"]["available"] is False, d["brain"]
        assert "brain_read_failed" in str(d["brain"].get("reason")), d["brain"]
        assert d["governor"]["routes"], "یک بخشِ خراب بقیه را کشت"
        assert d["obsidian"]["docs"], "یک بخشِ خراب بقیه را کشت"
    finally:
        ms._brain_daemon = old
        ms.cache_clear()


def t_brain_numbers_are_derived_from_named_files_not_invented():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "outputs"
        se = out / "self_evolved"
        se.mkdir(parents=True)
        (out / "daemon_state.json").write_text(json.dumps(
            {"total_ticks": 41, "errors_this_run": 2,
             "last_tick_at": "2026-08-03T01:02:03", "generation": 9}), "utf-8")
        (se / "conclusions.json").write_text(json.dumps(
            {"conclusions_fa": ["الف", "ب", "ج"]}), "utf-8")
        (se / "frontier.json").write_text(json.dumps(
            {"c1": {}, "c2": {}, "c3": {}, "c4": {}}), "utf-8")
        (se / "consolidation.json").write_text(json.dumps(
            [{"cycle": 1, "timestamp": 1785676362.0, "verified_sources": ["frontier"]}]),
            "utf-8")
        neural = Path(d) / "neural.json"
        neural.write_text(json.dumps([{"cycle": 1}, {"cycle": 2}]), "utf-8")
        engine = Path(d) / "consolidation.py"
        engine.write_text("# fixture", "utf-8")
        old = (ms._4D_OUTPUTS, ms._4D_CONSOLIDATION_PY, ms._NEURAL_CONSOLIDATION)
        ms._4D_OUTPUTS, ms._4D_CONSOLIDATION_PY, ms._NEURAL_CONSOLIDATION = \
            out, engine, neural
        try:
            b = ms.get_brain_state()
        finally:
            (ms._4D_OUTPUTS, ms._4D_CONSOLIDATION_PY,
             ms._NEURAL_CONSOLIDATION) = old
            ms.cache_clear()
    assert b["available"] is True, b
    assert b["daemon"] == {"reachable": True, "reason": None,
                           "source": "4d_system/outputs/daemon_state.json",
                           "missing_fields": [], "ticks": 41, "errors": 2,
                           "last_tick": "2026-08-03T01:02:03",
                           "generation": 9}, b["daemon"]
    c = b["consolidation"]
    assert c["conclusions_count"] == 3, c          # = len(conclusions_fa)
    assert c["frontier_count"] == 4, c             # = تعدادِ سلولِ آرشیو
    assert c["neural_cycles"] == 2, c              # = طولِ فهرستِ چرخه‌ها
    assert c["last_verified"] and c["last_verified"].startswith("2026-"), c
    assert c["last_verified_sources"] == ["frontier"], c


# ── ۴. governor: هیچ ادعایی بدونِ سنجشِ وجود ─────────────────────────────────
def t_governor_returns_null_with_a_reason_when_the_paths_do_not_exist():
    with tempfile.TemporaryDirectory() as d:
        g = ms.get_governor_state(root=Path(d))
    assert g["policy_doc"] is None and g["policy_doc_reason"], g
    assert g["canonical_provider"] is None and g["canonical_provider_reason"], g
    assert g["canonical_choke_point"] is None, g
    assert g["drift_status"]["status"] == "unknown", g["drift_status"]


def t_governor_asserts_the_two_documents_only_after_confirming_them():
    g = _ops()["governor"]
    root = ms._ROOT
    assert g["policy_doc"] == "docs/fugu_usage_policy.md", g["policy_doc"]
    assert g["canonical_provider"] == "_ops/cortex/model_router.py", g
    assert (root / g["policy_doc"]).is_file(), "سند اعلام شد ولی روی دیسک نیست"
    assert (root / g["canonical_provider"]).is_file(), "provider اعلام شد ولی نیست"
    assert g["canonical_choke_point"] == "ask()", g


def t_governor_drift_is_measured_from_the_document_not_declared():
    g = _ops()["governor"]
    ds = g["drift_status"]
    assert ds["declared_paths"], "هیچ مسیری از سند استخراج نشد"
    for item in ds["declared_paths"]:
        if item["exists"]:
            assert item["resolved"] and (ms._ROOT / item["resolved"]).exists(), item
        else:
            assert item["resolved"] is None, item
            assert item["declared"] in ds["missing"], item
    assert ds["status"] in ("drift", "aligned"), ds
    if ds["missing"]:
        assert ds["status"] == "drift", ds
        assert ds["notes"], "مسیرِ گم‌شده بدونِ یادداشت = drift ِ خاموش"


def t_the_policy_doc_names_a_provider_this_repo_does_not_have():
    """wlos/ در این درخت وجود ندارد — سطحِ حقیقت باید همین را بگوید، نه تکرارش."""
    g = _ops()["governor"]
    ds = g["drift_status"]
    wl = [m for m in ds["missing"] if m.startswith("wlos/")]
    assert not (ms._ROOT / "wlos").exists(), "فرضِ تست کهنه شد: wlos/ حالا هست"
    assert wl, f"سند wlos را نام می‌برد ولی drift گزارش نشد: {ds['missing']}"


def t_governor_routes_report_real_reachability_from_ask():
    r = _ops()["governor"]["routes"]
    assert r["local"]["reachable_from_ask"] is True, r["local"]
    assert r["fugu"]["reachable_from_ask"] is True, r["fugu"]
    assert r["fugu"]["tier"] == "primary" and r["fugu"]["role"] == "orchestr", r["fugu"]
    for name in ("fugu_ultra", "fugu_cyber"):
        assert r[name]["reachable_from_ask"] is False, r[name]
        assert r[name]["tier"] is None, r[name]
        assert r[name]["reason"], f"{name} غیرقابلِ‌دسترس بدونِ دلیل"
    assert r["fugu_cyber"]["model"] is None, "مدلِ ساختگی برای ردهٔ ناموجود"


# ── ۵. obsidian: فایلِ غایب باید «غایب» گزارش شود ────────────────────────────
def t_obsidian_reports_a_missing_document_as_missing():
    bogus = "06 - Architecture Maps/NO-SUCH-DOC-9d1f.md"
    old = ms._OBSIDIAN_DOCS
    ms._OBSIDIAN_DOCS = old + (bogus,)
    try:
        o = ms.get_obsidian_state()
    finally:
        ms._OBSIDIAN_DOCS = old
        ms.cache_clear()
    assert bogus in o["docs"], o["docs"].keys()
    assert o["docs"][bogus]["exists"] is False, o["docs"][bogus]
    assert bogus in o["missing"] and o["missing_count"] >= 1, o
    for rel, v in o["docs"].items():
        assert v["exists"] == (ms._ROOT / rel).exists(), rel


def t_obsidian_never_echoes_the_reference_dir_value():
    sentinel = "Zz-REFDIR-SENTINEL-4417"
    prev = os.environ.get("REFERENCE_DIR")
    os.environ["REFERENCE_DIR"] = str(Path(tempfile.gettempdir()) / sentinel)
    try:
        o = ms.get_obsidian_state()
        assert o["reference_dir_configured"] is False, o
        assert o["reference_dir_reason"], o
        assert sentinel not in json.dumps(o, ensure_ascii=False), "مسیر echo شد"
    finally:
        if prev is None:
            os.environ.pop("REFERENCE_DIR", None)
        else:
            os.environ["REFERENCE_DIR"] = prev
        ms.cache_clear()


# ── ۶. زیرمسیرها = برشِ دقیقِ همان بخش ───────────────────────────────────────
def t_each_sub_endpoint_matches_its_slice_of_api_ops():
    full = _get("/api/ops")
    # پیش‌شرطِ خودِ تست: دو شمارنده باید متفاوت باشند وگرنه تطابق بی‌معنی است.
    assert full["leads_total"] == 2 and full["tasks_total"] == 1, \
        (full["leads_total"], full["tasks_total"])
    b = _get("/api/ops/brain")
    assert b["section"] == "brain" and b["status"] == "ok", b
    assert b["brain"] == full["brain"], "برشِ brain با /api/ops یکی نیست"
    ld = _get("/api/ops/leads")
    assert ld["leads_total"] == full["leads_total"], (ld, full["leads_total"])
    assert ld["lead_stages"] == full["lead_stages"], ld
    tk = _get("/api/ops/tasks")
    assert tk["tasks_total"] == full["tasks_total"], tk
    assert tk["task_status"] == full["task_status"], tk


def t_the_light_sub_endpoints_do_not_build_the_heavy_sections():
    """/api/ops/leads نباید brain/governor/obsidian را بسازد (هدفِ split)."""
    ld = _get("/api/ops/leads")
    for s in NEW_SECTIONS:
        assert s not in ld, f"برشِ سبک بخشِ سنگینِ {s} را ساخت"


def t_an_unknown_sub_path_is_still_404():
    ms.cache_clear()
    st, _, _ = ms.dispatch_api("/api/ops/nope")
    assert st == 404, st


# ── ۷. گاردِ یکسانِ gateway روی والد و زیرمسیرها ─────────────────────────────
def t_the_sub_endpoints_are_registered_in_the_gateway_read_allowlist():
    for p in SUB_PATHS:
        assert p in mg.READ_API_PATHS, f"{p} در فهرستِ خواندنیِ gateway نیست"
    assert "/api/ops" in mg.READ_API_PATHS


def t_sub_endpoints_enforce_exactly_the_same_auth_as_their_parent():
    prev = {k: os.environ.get(k) for k in
            ("TG_CENTER_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID", mg.READ_GATE_FLAG)}
    os.environ["TG_CENTER_BOT_TOKEN"] = TOKEN
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = OWNER
    try:
        # ⚠️ ۲۰۲۶-۰۸-۰۴ — این بلوک برعکس شد، و **کد درست بود نه تست**.
        #
        # نسخهٔ قبلی می‌گفت «فلگِ غایب ⇒ گیت **باز** ⇒ ۲۰۰ بدونِ احراز» و
        # assert می‌کرد `read_gate_enabled() is False`. ولی کامیتِ `87c3063`
        # («برشِ ۳: ۱۱ مسیرِ خواندنی پیش‌فرض بسته شد») پیش‌فرضِ کد را عمداً
        # از باز به **بسته** برد — چون آن ۱۱ مسیر روی یک تونلِ **عمومی** سرو
        # می‌شوند و «غیاب = باز» یعنی هر کسی که URL را دارد می‌خواندشان.
        # آن کامیت این فایل را به‌روز نکرد چون همان روز کلاً قرمز بود
        # (‏۳/۲۸، به‌خاطرِ ۳۲۵ خطِ گم‌شده) و کسی این تکِ تست را ندید.
        #
        # پس این‌جا انتظار به وضعِ **امن** به‌روز شد. دندان کم نشد — بیشتر شد:
        # حالا صراحتاً assert می‌کند که غیابِ فلگ یعنی **بسته**، یعنی اگر کسی
        # روزی پیش‌فرض را به «باز» برگرداند این تست قرمز می‌شود.
        os.environ.pop(mg.READ_GATE_FLAG, None)
        assert mg.read_gate_enabled() is True, (
            "پیش‌فرضِ گیتِ خواندن به **باز** برگشت — ۱۱ مسیرِ خواندنی روی تونلِ "
            "عمومی بی‌احراز می‌شوند (رگرسیونِ 87c3063)")
        for p in ("/api/ops",) + SUB_PATHS:
            ms.cache_clear()
            st, body, _ = mg.handle("GET", p, {}, now=NOW)
            assert st == 403, (p, st, "غیابِ فلگ باید ببندد نه باز کند")
            assert b"owner_auth_required" in body, (p, body)
        # و با initData ِ معتبر همان مسیرها باید باز شوند — وگرنه رفعِ امنیتی
        # به «هیچ‌کس هرگز نمی‌تواند بخواند» تبدیل شده، که خودش یک باگ است.
        for p in ("/api/ops",) + SUB_PATHS:
            ms.cache_clear()
            st, _, _ = mg.handle("GET", p, {"X-Tg-Init-Data": _init_data()}, now=NOW)
            assert st == 200, (p, st, "مالکِ معتبر هم رد شد")
        # فلگِ روشن = همان دیوارِ HMAC روی **هر** مسیرِ خواندنی.
        os.environ[mg.READ_GATE_FLAG] = "1"
        for p in ("/api/ops",) + SUB_PATHS:
            ms.cache_clear()
            st, body, _ = mg.handle("GET", p, {}, now=NOW)
            assert st == 403, (p, st)
            assert b"owner_auth_required" in body, (p, body)
            ms.cache_clear()
            st2, _, _ = mg.handle("GET", p, {"X-Tg-Init-Data": _init_data(tamper=True)},
                                  now=NOW)
            assert st2 == 403, (p, st2)
            ms.cache_clear()
            st3, _, _ = mg.handle("GET", p, {"X-Tg-Init-Data": _init_data(user_id=888)},
                                  now=NOW)
            assert st3 == 403, (p, "کاربرِ غیرمالک رد شد؟")
            ms.cache_clear()
            st4, body4, _ = mg.handle("GET", p, {"X-Tg-Init-Data": _init_data()},
                                      now=NOW)
            assert st4 == 200, (p, st4, body4[:120])
    finally:
        os.environ.pop(mg.READ_GATE_FLAG, None)
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        ms.cache_clear()


def t_no_read_route_bypasses_the_shared_gate_function():
    """قاعده بسته می‌شود نه شکاف: هر مسیرِ خواندنی باید در همان تک‌فهرست باشد."""
    src = Path(ms.__file__).read_text("utf-8", errors="replace")
    import re
    block = re.search(r"handlers = \{(.*?)\n    \}", src, re.S)
    assert block, "بلوکِ handlers پیدا نشد"
    routes = set(re.findall(r'"(/api/[^"]+)"', block.group(1)))
    missing = sorted(routes - mg.READ_API_PATHS)
    assert not missing, f"مسیرِ خواندنیِ بی‌گارد در gateway: {missing}"


# ── ۸. کش ───────────────────────────────────────────────────────────────────
def t_the_snapshot_cache_is_between_two_and_five_seconds():
    prev = os.environ.get("OCTOPUS_MINIAPP_CACHE_TTL_S")
    try:
        os.environ.pop("OCTOPUS_MINIAPP_CACHE_TTL_S", None)
        assert 2.0 <= ms._cache_ttl() <= 5.0, ms._cache_ttl()
        os.environ["OCTOPUS_MINIAPP_CACHE_TTL_S"] = "999"
        assert ms._cache_ttl() == 5.0, "سقفِ کش رعایت نشد ⇒ دادهٔ کهنه"
    finally:
        if prev is None:
            os.environ.pop("OCTOPUS_MINIAPP_CACHE_TTL_S", None)
        else:
            os.environ["OCTOPUS_MINIAPP_CACHE_TTL_S"] = prev


def t_the_cache_serves_within_ttl_and_expires_after_it():
    calls = {"n": 0}

    def builder(root):
        calls["n"] += 1
        return {"status": "ok", "n": calls["n"]}

    clock = _Clock()
    old_mono, old_ops = ms._mono, ms.get_ops_state
    ms._mono, ms.get_ops_state = clock, builder
    try:
        ms.cache_clear()
        a = _get("/api/ops")["n"] if False else None      # noqa: F841 (خوانایی)
        ms.cache_clear()
        st, b1, _ = ms.dispatch_api("/api/ops")
        st, b2, _ = ms.dispatch_api("/api/ops")           # داخلِ TTL ⇒ همان
        assert json.loads(b1)["n"] == json.loads(b2)["n"] == 1, (b1, b2)
        assert calls["n"] == 1, calls
        clock.t += 1.0                                    # هنوز داخلِ TTL=3
        st, b3, _ = ms.dispatch_api("/api/ops")
        assert json.loads(b3)["n"] == 1 and calls["n"] == 1, calls
        clock.t += 10.0                                   # بعد از انقضا
        st, b4, _ = ms.dispatch_api("/api/ops")
        assert json.loads(b4)["n"] == 2, (b4, calls)
        assert calls["n"] == 2, calls
    finally:
        ms._mono, ms.get_ops_state = old_mono, old_ops
        ms.cache_clear()


def t_the_cache_never_serves_a_stale_error_as_a_success():
    state = {"mode": "ok"}

    def builder(root):
        if state["mode"] == "ok":
            return {"status": "ok", "leads_total": 7}
        return {"status": "error", "reason": "DiskWentAway"}

    clock = _Clock()
    old_mono, old_ops = ms._mono, ms.get_ops_state
    ms._mono, ms.get_ops_state = clock, builder
    try:
        ms.cache_clear()
        st, b1, _ = ms.dispatch_api("/api/ops")
        assert json.loads(b1)["status"] == "ok", b1
        state["mode"] = "broken"
        clock.t += 10.0                                   # کشِ سالم منقضی شد
        st, b2, _ = ms.dispatch_api("/api/ops")
        d2 = json.loads(b2)
        assert d2["status"] == "error" and d2["reason"] == "DiskWentAway", d2
        # و پاسخِ خراب هرگز خودش کش نمی‌شود:
        st, b3, _ = ms.dispatch_api("/api/ops")
        assert json.loads(b3)["status"] == "error", b3
        # و وقتی منبع برگشت، همان لحظه حقیقت را می‌گوید (نه خطای کش‌شده):
        state["mode"] = "ok"
        st, b4, _ = ms.dispatch_api("/api/ops")
        assert json.loads(b4)["status"] == "ok", b4
    finally:
        ms._mono, ms.get_ops_state = old_mono, old_ops
        ms.cache_clear()


def t_an_exception_inside_a_handler_is_never_cached():
    def boom(root):
        raise RuntimeError("منبع مرد")

    old = ms.get_ops_state
    ms.get_ops_state = boom
    try:
        ms.cache_clear()
        st, body, _ = ms.dispatch_api("/api/ops")
        assert st == 500, st
        assert "/api/ops" not in ms._CACHE, "خطا وارد کش شد"
    finally:
        ms.get_ops_state = old
        ms.cache_clear()


# ── ۹. سطحِ خواندنی هیچ‌وقت نمی‌نویسد ────────────────────────────────────────
def t_the_read_model_stays_read_only():
    """AST نه grep — کامنت/داکسترینگ نباید مثبتِ کاذب بسازد و متن نباید پنهان کند."""
    import ast
    tree = ast.parse(Path(ms.__file__).read_text("utf-8", errors="replace"))
    banned = {"write_text", "write_bytes", "mkdir", "unlink", "rmtree",
              "touch", "remove", "rename", "replace"}
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in banned:
            hits.append(f"{node.func.attr}@line{node.lineno}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "open":
            hits.append(f"open@line{node.lineno}")
    assert not hits, f"مسیرِ نوشتن در سطحِ فقط‌خواندنی: {hits}"


# ── ۱۰. شکاف‌هایی که جهش‌آزماییِ مستقلِ ممیز نشان داد (۲۰۲۶-۰۸-۰۳) ────────────
def t_the_cache_is_keyed_per_path_not_shared():
    """کلیدِ کش باید per-path باشد وگرنه یک برش پاسخِ برشِ دیگر را سرو می‌کند.

    تست‌های بالا قبل از **هر** dispatch کش را پاک می‌کنند، پس دو مسیرِ متفاوت
    هرگز داخلِ یک پنجرهٔ TTL دیده نمی‌شدند — یعنی کلیدِ کش بی‌ناظر بود. در تولید
    هیچ‌کس کش را پاک نمی‌کند، پس دقیقاً همان‌جا که ناظر نبود، خطرِ واقعی است."""
    clock = _Clock()
    old_mono = ms._mono
    ms._mono = clock
    try:
        ms.cache_clear()
        a = json.loads(ms.dispatch_api("/api/ops")[1])
        b = json.loads(ms.dispatch_api("/api/ops/leads")[1])    # داخلِ همان TTL
        c = json.loads(ms.dispatch_api("/api/ops/tasks")[1])    # بدونِ cache_clear
        assert b.get("section") == "leads", b
        assert c.get("section") == "tasks", c
        assert "brain" in a and "brain" not in b, (sorted(a), sorted(b))
        assert b["leads_total"] == 2 and c["tasks_total"] == 1, (b, c)
    finally:
        ms._mono = old_mono
        ms.cache_clear()


def t_the_light_slice_never_calls_the_heavy_builder():
    """«کلیدش در پاسخ نیست» ثابت نمی‌کند «ساخته نشد» — خودِ فراخوانی را بشمار.

    گاردِ شکلِ پاسخ یک برشِ سبک را که مغز را می‌سازد و نتیجه را دور می‌ریزد
    سبز می‌کند؛ هدفِ split سرعت است نه شکل."""
    calls = {"n": 0}
    old = ms.get_brain_state

    def counting(*a, **k):
        calls["n"] += 1
        return old(*a, **k)

    ms.get_brain_state = counting
    try:
        ms.cache_clear()
        ms.dispatch_api("/api/ops/leads")
        ms.dispatch_api("/api/ops/tasks")
        assert calls["n"] == 0, f"برشِ سبک {calls['n']} بار بخشِ سنگین را ساخت"
        ms.cache_clear()
        ms.dispatch_api("/api/ops/brain")
        assert calls["n"] >= 1, "برشِ brain اصلاً بخشِ brain را نساخت"
    finally:
        ms.get_brain_state = old
        ms.cache_clear()


def t_the_drift_step_follows_the_measured_drift_status():
    """قدمِ drift باید از خودِ سنجه بیاید — یک «done» ِ ثابت هم امروز سبز می‌ماند."""
    old = ms._governor_drift
    try:
        for status, expect in (("drift", "open"), ("aligned", "done"),
                               ("unknown", "unknown")):
            ms._governor_drift = (lambda s: (lambda *a, **k: {
                "status": s, "reason": None, "declared_paths": [],
                "missing": [], "notes": []}))(status)
            steps = {x["id"]: x["status"] for x in ms.get_next_steps()}
            assert steps["fugu-policy-drift"] == expect, \
                (status, steps["fugu-policy-drift"])
    finally:
        ms._governor_drift = old
        ms.cache_clear()


def t_a_half_built_ui_is_not_reported_as_a_finished_step():
    """چهار تب یک **فهرستِ لازم**اند نه املاهای جایگزین: دو از چهار هنوز open است.

    بدونِ این فیکسچر، `any()` به‌جای `all()` هم سبز می‌ماند — چون امروز هر چهار
    تب حاضرند و پایه هرگز زیرِ سطحِ هدف نمی‌رود."""
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "miniapp").mkdir()
        (Path(d) / "miniapp" / "index.html").write_text(
            '<div data-tab="brain"></div><div data-tab="governor"></div>', "utf-8")
        (Path(d) / "miniapp" / "app.js").write_text("// هنوز خالی\n", "utf-8")
        old = ms._HERE
        ms._HERE = Path(d)
        try:
            steps = {x["id"]: x["status"] for x in ms.get_next_steps()}
        finally:
            ms._HERE = old
            ms.cache_clear()
    assert steps["miniapp-tabs"] == "open", steps["miniapp-tabs"]
    assert steps["command-palette"] == "open", steps["command-palette"]
    assert steps["next-best-action"] == "open", steps["next-best-action"]


CHECKS = [
    ("کلیدهای موجود دست‌نخورده", t_every_pre_existing_key_keeps_its_name_and_meaning),
    ("registry از خودِ موتور", t_the_action_registry_is_read_from_the_engine_not_hand_copied),
    ("چهار بخشِ تازه با شکلِ اعلام‌شده", t_the_four_new_sections_are_present_with_their_declared_shape),
    ("brain نخواندنی ⇒ available=false + 200", t_an_unreadable_brain_is_available_false_with_a_reason_and_still_http_200),
    ("منبعِ منفجرشده کلِ پاسخ را نمی‌کشد", t_a_brain_source_that_raises_never_kills_the_whole_answer),
    ("اعدادِ brain مشتقِ فایل‌اند", t_brain_numbers_are_derived_from_named_files_not_invented),
    ("governor بدونِ فایل ⇒ null + دلیل", t_governor_returns_null_with_a_reason_when_the_paths_do_not_exist),
    ("governor فقط بعد از تأیید ادعا می‌کند", t_governor_asserts_the_two_documents_only_after_confirming_them),
    ("drift از خودِ سند مشتق است", t_governor_drift_is_measured_from_the_document_not_declared),
    ("سند providerِ ناموجود را نام می‌برد", t_the_policy_doc_names_a_provider_this_repo_does_not_have),
    ("routes دسترسیِ واقعی را می‌گوید", t_governor_routes_report_real_reachability_from_ask),
    ("obsidian فایلِ غایب را غایب می‌گوید", t_obsidian_reports_a_missing_document_as_missing),
    ("obsidian مسیرِ مرجع را echo نمی‌کند", t_obsidian_never_echoes_the_reference_dir_value),
    ("هر زیرمسیر = برشِ دقیقِ همان بخش", t_each_sub_endpoint_matches_its_slice_of_api_ops),
    ("برشِ سبک بخشِ سنگین نمی‌سازد", t_the_light_sub_endpoints_do_not_build_the_heavy_sections),
    ("زیرمسیرِ ناشناخته ⇒ 404", t_an_unknown_sub_path_is_still_404),
    ("زیرمسیرها در فهرستِ خواندنیِ gateway", t_the_sub_endpoints_are_registered_in_the_gateway_read_allowlist),
    ("گاردِ زیرمسیر = گاردِ والد", t_sub_endpoints_enforce_exactly_the_same_auth_as_their_parent),
    ("هیچ مسیرِ خواندنیِ بی‌گارد", t_no_read_route_bypasses_the_shared_gate_function),
    ("TTL کش بینِ ۲ تا ۵ ثانیه", t_the_snapshot_cache_is_between_two_and_five_seconds),
    ("کش داخلِ TTL سرو و بعدش منقضی", t_the_cache_serves_within_ttl_and_expires_after_it),
    ("کش خطای کهنه را موفقیت نمی‌کند", t_the_cache_never_serves_a_stale_error_as_a_success),
    ("استثنا هرگز کش نمی‌شود", t_an_exception_inside_a_handler_is_never_cached),
    ("سطحِ خواندنی نمی‌نویسد", t_the_read_model_stays_read_only),
    ("کش per-path است نه مشترک", t_the_cache_is_keyed_per_path_not_shared),
    ("برشِ سبک بخشِ سنگین را صدا نمی‌زند", t_the_light_slice_never_calls_the_heavy_builder),
    ("قدمِ drift از خودِ سنجه می‌آید", t_the_drift_step_follows_the_measured_drift_status),
    ("UI ِ نیمه‌ساخته «done» نمی‌شود", t_a_half_built_ui_is_not_reported_as_a_finished_step),
]


if __name__ == "__main__":
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_miniapp_ops_readmodel: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
