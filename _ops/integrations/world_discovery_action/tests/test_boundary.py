#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_boundary — ۴۲ سناریوی اجباریِ مرزِ «کشفِ دنیا» ↔ «پلِ اقدام».

قلبِ این فایل یک جمله است:

    NO_VALID_DISCOVERY یک نتیجهٔ معتبر است، و مرز حق ندارد آن را به عمل،
    به PASS، یا به «تقریباً کشف» ترجمه کند.

بقیهٔ بندها محافظ‌های همان‌اند: سطحِ اعلام‌شده باور نمی‌شود، منبع privilege
نمی‌گیرد، متنِ آلوده حکم را عوض نمی‌کند، و هیچ مسیری ارسال یا خرج نمی‌سازد.
"""
import json
import sys
from pathlib import Path

import wda_harness as H

from world_discovery_action import contracts            # noqa: E402
from world_discovery_action import dry_run                # noqa: E402
from world_discovery_action import integration_receipt    # noqa: E402
from world_discovery_action import policy                 # noqa: E402
from world_discovery_action import telegram_draft         # noqa: E402
from world_discovery_action import translator             # noqa: E402
from world_discovery_action import validator              # noqa: E402

ENV = H.setup("boundary")
NOW = 1_785_400_000.0


def _tr(fix):
    return translator.translate_discovery_artifact(H.fixture(fix), now=NOW)


# ── ایزولاسیون ──────────────────────────────────────────────────────────────
def t_00_sandbox_is_not_the_live_tree():
    assert not str(ENV["root"]).lower().startswith(r"f:\backup"), ENV["root"]


# ── ۱..۴ NO_VALID_DISCOVERY ────────────────────────────────────────────────
def t_01_no_valid_discovery_yields_no_action():
    r = _tr("no-valid-discovery.json")
    assert r["source_status"] == "NO_VALID_DISCOVERY", r
    assert r["decision"] == "NO_ACTION", r


def t_02_no_valid_discovery_has_null_action_id():
    r = _tr("no-valid-discovery.json")
    assert r["action_id"] is None, r
    assert r["action_class"] is None, r


def t_03_no_valid_discovery_can_never_be_complete():
    r = _tr("no-valid-discovery.json")
    v = contracts.validate_translation_receipt(r)
    assert v["ok"], v
    assert r["source_status"] in contracts.NON_ACTIONABLE
    assert r["owner_gate_required"] is False


def t_04_no_valid_discovery_with_an_E0_becomes_information_only_dry_run():
    """استثنای تک‌ — و حتی آن هم کشف را validated نمی‌کند."""
    art = H.fixture("no-valid-discovery.json")
    art["result"]["experiment"] = {
        "level": "E0", "title": "گسترشِ شاهد",
        "target": "workspace/more.json", "falsifier": "اگر منبعِ دوم پیدا نشود",
        "external_effect": False, "estimated_cost": 0,
        "steps": [{"op": "read public page"}]}
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert r["decision"] == "DRY_RUN", r
    assert r["source_status"] == "NO_VALID_DISCOVERY", r    # تحریف نشد
    assert r["action_id"] is None, r                        # هنوز کشف نیست


# ── ۵..۹ نگاشتِ سطح ────────────────────────────────────────────────────────
def t_05_validated_e0_maps_to_A0():
    r = _tr("validated-e0.json")
    assert r["experiment_level_inferred"] == "E0" and r["action_class"] == "A0", r
    assert r["decision"] == "DRY_RUN", r


def t_06_validated_e1_maps_to_A1():
    r = _tr("validated-e1.json")
    assert r["action_class"] == "A1" and r["decision"] == "DRY_RUN", r


def t_07_e2_maps_to_A3_owner_gate():
    r = _tr("owner-gated-e2.json")
    assert r["action_class"] == "A3" and r["decision"] == "OWNER_GATE", r
    assert r["owner_gate_required"] is True


def t_08_e3_maps_to_A4_and_is_blocked():
    r = _tr("external-e3.json")
    assert r["action_class"] == "A4" and r["decision"] == "BLOCK", r


def t_09_e4_maps_to_A5_and_is_blocked():
    r = _tr("money-e4.json")
    assert r["action_class"] == "A5" and r["decision"] == "BLOCK", r


# ── ۱۰..۱۴ سطحِ اعلام‌شده باور نمی‌شود ─────────────────────────────────────
def t_10_forbidden_target_is_A6_regardless_of_level():
    lvl = policy.infer_level({"level": "E0", "target": "PRE-0/governance.py"}, "E0")
    assert lvl["class"] == "A6", lvl


def t_11_unknown_level_blocks():
    lvl = policy.infer_level({"level": "E9", "target": "x"}, "E9")
    assert lvl["level"] is None, lvl
    d = policy.decide("DISCOVERY_VALIDATED", lvl["class"], has_experiment=True,
                      falsifier_present=True)
    assert d["decision"] in ("BLOCK", "REJECT"), d


def t_12_declared_E0_with_a_send_verb_is_A4():
    lvl = policy.infer_level(
        {"level": "E0", "target": "workspace/x", "steps": [{"op": "send email"}]},
        "E0")
    assert lvl["class"] == "A4", lvl


def t_13_declared_E1_with_cost_is_A5():
    lvl = policy.infer_level(
        {"level": "E1", "target": "workspace/x", "estimated_cost": 0.5}, "E1")
    assert lvl["class"] == "A5", lvl


def t_14_declared_E2_with_pre0_target_is_A6():
    lvl = policy.infer_level({"level": "E2", "target": "_ops/../PRE-0/x.py"}, "E2")
    assert lvl["class"] == "A6", lvl


# ── ۱۵..۱۸ artifact خراب ───────────────────────────────────────────────────
def t_15_missing_schema_blocks():
    r = translator.translate_discovery_artifact({"result": {}}, now=NOW)
    assert r["decision"] == "NO_ACTION" and r["errors"], r


def t_16_unknown_schema_version_blocks():
    art = H.fixture("no-valid-discovery.json")
    art["schema"] = "world-discovery.bundle.v9"
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert any("unknown-schema" in e for e in r["errors"]), r


def t_17_hash_mismatch_blocks():
    art = H.fixture("no-valid-discovery.json")
    art["artifact_id"] = "definitely-not-the-hash"
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert any("hash-mismatch" in e for e in r["errors"]), r


def t_18_malformed_evidence_does_not_crash_or_validate():
    art = H.fixture("validated-e0.json")
    art["result"]["discovery"]["evidence_urls"] = "not-a-list"
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert r["independent_source_count"] == 0, r


# ── ۱۹..۲۳ کفایتِ شاهد ─────────────────────────────────────────────────────
def t_19_insufficient_independent_sources_is_visible():
    art = H.fixture("validated-e0.json")
    art["result"]["discovery"]["evidence_urls"] = ["https://a.example/1",
                                                   "https://a.example/2"]
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert r["independent_source_count"] == 1, r     # یک دامنه، نه دو


def t_20_contested_yields_no_action():
    r = _tr("contested.json")
    assert r["source_status"] == "CONTESTED" and r["decision"] == "NO_ACTION", r


def t_21_falsified_yields_no_action():
    art = H.fixture("contested.json")
    art["result"]["status"] = "FALSIFIED"
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert r["decision"] == "NO_ACTION", r


def t_22_missing_falsifier_means_no_action():
    art = H.fixture("validated-e0.json")
    art["result"]["discovery"]["falsifier"] = ""
    art["result"]["experiment"]["falsifier"] = ""
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert r["decision"] == "NO_ACTION", r


def t_23_high_confidence_without_evidence_does_not_help():
    art = H.fixture("validated-e0.json")
    art["result"]["discovery"]["confidence"] = 0.99
    art["result"]["discovery"]["evidence_urls"] = []
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert r["independent_source_count"] == 0, r
    assert r["evidence_count"] == 0, r


# ── ۲۴..۲۶ نفوذ و privilege ────────────────────────────────────────────────
def t_24_source_component_cannot_override_classification():
    """`world_discovery` هیچ امتیازی نمی‌گیرد — درخواستِ ساخته‌شده هم همان
    کلاسی را می‌گیرد که هر منبعِ دیگری می‌گرفت."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "action_bridge"))
    import classifier as bc
    req = translator.build_action_request(
        {"discovery_id": "d"},
        {"level": "E3", "target": "owner-dm", "external_effect": True,
         "falsifier": "f", "title": "ارسال"}, now=NOW, prereg_id="p")
    assert req["source_component"] == "world_discovery"
    assert bc.classify(req)["classification"] == "A4", bc.classify(req)


def t_25_prompt_injection_in_the_claim_is_ignored():
    r = _tr("malicious-artifact.json")
    # ادعا: «E0 و بی‌خطر». رفتار: ارسال + هزینه + مقصدِ ممنوع.
    assert r["experiment_level_declared"] == "E0", r
    assert r["action_class"] == "A6", r
    assert r["decision"] == "REJECT", r


def t_26_url_data_cannot_execute_anything():
    """داده هرگز اجرا نمی‌شود — مترجم فقط رشته می‌خواند و رشته می‌نویسد."""
    art = H.fixture("validated-e0.json")
    art["result"]["discovery"]["evidence_urls"] = [
        "https://x.example/a; rm -rf /", "javascript:alert(1)",
        "file:///etc/passwd"]
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert isinstance(r, dict) and r["external_effects"] == []


# ── ۲۷..۲۹ draft تلگرام ────────────────────────────────────────────────────
def t_27_secretlike_content_never_reaches_the_draft():
    art = H.fixture("no-valid-discovery.json")
    art["result"]["note"] = "کلید: <REDACTED-OPENAI-KEY> و api_key=SUPERSECRET1"
    rec = translator.translate_discovery_artifact(art, now=NOW)
    d = telegram_draft.from_translation(rec, art["result"], now=NOW)
    assert "sk-abcdefghijkl" not in d["body"], d["body"]
    assert "SUPERSECRET1" not in d["body"], d["body"]
    assert d["redaction"]["secrets_found"] is True


def t_28_pii_is_redacted_in_the_draft():
    art = H.fixture("no-valid-discovery.json")
    art["result"]["note"] = "تماس: ari@example.com یا +61 400 123 456"
    rec = translator.translate_discovery_artifact(art, now=NOW)
    d = telegram_draft.from_translation(rec, art["result"], now=NOW)
    assert "ari@example.com" not in d["body"], d["body"]
    assert "400 123 456" not in d["body"], d["body"]


def t_29_the_draft_module_has_no_send_path_at_all():
    """نه «فلگش خاموش» — **راهش ساخته نشده**.

    گاردِ نسخهٔ اول رشته‌ای بود و روی **داکِ خودِ ماژول** قرمز شد — جمله‌ای که
    می‌گفت «هیچ ارجاعی به approval_channel ندارد» به‌عنوان ارجاع شمرده شد.
    درسِ ثبت‌شده: grep کامنت را می‌شمارد. پس اینجا **AST** سنجیده می‌شود:
    importهای واقعی، فراخوانی‌های واقعی، و نام‌های سطحِ ماژول."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(telegram_draft))
    banned_mods = {"requests", "urllib", "http", "socket", "httpx",
                   "approval_channel", "tg_api", "telegram"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    leaked = imported & banned_mods
    assert not leaked, f"importِ مسیرِ ارسال: {leaked}"

    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = getattr(f, "attr", None) or getattr(f, "id", None)
            if name:
                called.add(name)
    for bad in ("send_text", "sendMessage", "send", "post", "urlopen", "request"):
        assert bad not in called, f"فراخوانیِ ارسال: {bad}"

    assert not [n for n in dir(telegram_draft)
                if n.lower().startswith("send")
                and callable(getattr(telegram_draft, n))]


# ── ۳۰..۳۴ کارت، idempotency، تعارض ────────────────────────────────────────
def t_30_owner_card_without_approval_does_not_execute():
    r = _tr("owner-gated-e2.json")
    d = telegram_draft.from_translation(r, H.fixture("owner-gated-e2.json")["result"],
                                        now=NOW)
    assert d["requires_owner_approval"] is True
    assert d["send_attempted"] is False and d["transport"] is None
    assert d["buttons_wired"] is False


def t_31_an_expired_card_is_not_usable():
    r = _tr("owner-gated-e2.json")
    d = telegram_draft.from_translation(r, H.fixture("owner-gated-e2.json")["result"],
                                        now=NOW)
    assert d["expires_at"] > NOW
    assert d["expires_at"] - NOW <= telegram_draft.DEFAULT_TTL_S + 1


def t_32_artifact_hash_mismatch_blocks():
    art = H.fixture("validated-e0.json")
    art["result"]["artifact_id"] = "tampered"
    r = translator.translate_discovery_artifact(art, now=NOW)
    assert any("hash-mismatch" in e for e in r["errors"]), r
    assert r["decision"] == "NO_ACTION", r


def t_33_duplicate_translation_is_idempotent():
    a, b = _tr("no-valid-discovery.json"), _tr("no-valid-discovery.json")
    assert a["translation_id"] == b["translation_id"], (a["translation_id"],
                                                        b["translation_id"])
    assert a["source_artifact"]["content_hash"] == b["source_artifact"]["content_hash"]


def t_34_same_content_different_payload_gets_a_different_id():
    art = H.fixture("no-valid-discovery.json")
    a = translator.translate_discovery_artifact(art, now=NOW)
    art["result"]["reason"] = "changed"
    b = translator.translate_discovery_artifact(art, now=NOW)
    assert a["translation_id"] != b["translation_id"]


# ── ۳۵..۳۹ ناوردی‌ها ───────────────────────────────────────────────────────
def t_35_sandbox_path_escape_is_A6():
    lvl = policy.infer_level(
        {"level": "E1", "target": "workspace/../../_ops/state/x.json"}, "E1")
    assert lvl["class"] == "A6", lvl


def t_36_runtime_state_write_is_A6():
    for tgt in ("_ops/state/fitness-latest.json", "_ops/organism.py",
                "_ops/OCTOPUS-flags.cmd"):
        lvl = policy.infer_level({"level": "E1", "target": tgt}, "E1")
        assert lvl["class"] == "A6", (tgt, lvl)


def t_37_38_external_effects_and_spend_are_always_zero():
    for fix in ("no-valid-discovery.json", "validated-e0.json",
                "external-e3.json", "money-e4.json", "malicious-artifact.json"):
        out = dry_run.run(H.fixture(fix), sandbox_dir=ENV["root"], now=NOW)
        assert out["external_effects"] == [], (fix, out["external_effects"])
        assert out["spend"] == 0, (fix, out["spend"])
        assert out["telegram_send_attempted"] is False, fix
        assert out["runtime_state_writes"] == 0, fix


def t_39_the_source_artifact_is_never_mutated():
    art = H.fixture("validated-e0.json")
    before = json.dumps(art, ensure_ascii=False, sort_keys=True)
    translator.translate_discovery_artifact(art, now=NOW)
    dry_run.run(art, sandbox_dir=ENV["root"], now=NOW)
    assert json.dumps(art, ensure_ascii=False, sort_keys=True) == before


# ── ۴۰..۴۲ رسید و حفظِ وضعیت ───────────────────────────────────────────────
def t_40_the_translation_receipt_is_written_atomically():
    out = dry_run.run(H.fixture("no-valid-discovery.json"),
                      sandbox_dir=ENV["root"], now=NOW)
    assert out["receipt_written"] is True, out
    p = Path(out["receipt_path"])
    assert p.exists() and json.loads(p.read_text("utf-8"))["schema"] == \
        contracts.TRANSLATION_SCHEMA
    assert not list(p.parent.glob("*.tmp*")), "فایلِ tmp جا ماند"


def t_41_a_receipt_write_failure_is_not_reported_as_success():
    saved = integration_receipt.atomic_write
    integration_receipt.atomic_write = lambda p, t: {"ok": False, "error": "disk"}
    try:
        out = dry_run.run(H.fixture("no-valid-discovery.json"),
                          sandbox_dir=ENV["root"], now=NOW)
    finally:
        integration_receipt.atomic_write = saved
    assert out["ok"] is False, out
    assert out["receipt_written"] is False


def t_42_the_report_preserves_no_valid_discovery():
    art = H.fixture("no-valid-discovery.json")
    out = dry_run.run(art, sandbox_dir=ENV["root"], now=NOW)
    assert out["source_status"] == "NO_VALID_DISCOVERY"
    assert "NO_VALID_DISCOVERY" in out["draft"]["body"]
    for w in ("کشف شد", "DISCOVERY_VALIDATED", "PASS"):
        assert w not in out["draft"]["body"], w


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = H.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_boundary: "
          f"{len(checks) - failed}/{len(checks)}")
    H.teardown(ENV)
    sys.exit(1 if failed else 0)
