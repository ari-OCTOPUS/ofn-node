"""test_registry_scan.py — URCP Phase-0 (#۱۰): registry ِ read-only با پیش‌فرضِ unknown.

اثبات‌ها: کشف با unknown-default (A5) · تقدمِ manifest · containment ِ content-free
(پوشه اصلاً خوانده نمی‌شود، صفر echo ِ هویت) · سقفِ خودکارِ R3 · conformance ·
read-only بودن (نوشتن فقط در out ِ تزریقی) · fail-soft روی درختِ ناقص/manifest ِ خراب.
"""
import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("registry_scan")

import registry_scan as rs   # noqa: E402

_PF_NAME = "اونلی فنز"        # فقط در تست (fixture-ساز) — snapshot نباید هرگز echo کند


def _mk_vault(root: Path, with_pf: bool = True) -> Path:
    pj = root / "03 - Projects"
    (pj / "Alpha").mkdir(parents=True, exist_ok=True)      # idempotent — چند تست همین fixture را می‌سازند
    (pj / "Alpha" / "PROJECT.md").write_text(
        "---\ntype: project\nstatus: active\nowner: آری\nrisk_level: medium\n"
        "autonomy_level: read-only\n---\n# Alpha\n", "utf-8")
    (pj / "Beta").mkdir(exist_ok=True)                     # بدونِ PROJECT.md → همه unknown
    (pj / "Gamma").mkdir(exist_ok=True)                    # critical → R4-pending (نه unknown، نه R4)
    (pj / "Gamma" / "PROJECT.md").write_text(
        "---\ntype: project\nstatus: active\nowner: آری\nrisk_level: critical\n---\n# Gamma\n", "utf-8")
    (pj / "_Index").mkdir(exist_ok=True)                   # باید skip شود
    if with_pf:
        secret = pj / _PF_NAME
        secret.mkdir(exist_ok=True)
        (secret / "PROJECT.md").write_text(
            "---\nstatus: active\ntags: [secret-platform]\n---\n", "utf-8")
    ag = root / "05 - Agents"
    ag.mkdir(exist_ok=True)
    (ag / "Research Scout Fleet.md").write_text("---\nowner: آری\n---\n# scout\n", "utf-8")
    (ag / "Mycelium Scout.md").write_text(
        "---\ntype: agent\nowner: آری\nrisk_level: high\n---\n# scout2\n", "utf-8")   # الحاقِ risk ایجنت
    (ag / "AGENT_REGISTRY.md").write_text("# registry\n", "utf-8")   # skip
    (ag / "_Index - Agents.md").write_text("# idx\n", "utf-8")       # skip
    return root


def _mk_manifests(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / "pf.json").write_text(json.dumps({
        "logical_id": "urn:octopus:project:project-f", "entity_type": "Project",
        "display_name": "Project-F", "content_free": True,
        "folder_sha256": hashlib.sha256(_PF_NAME.encode("utf-8")).hexdigest(),
        "physical_path": "(content-free)", "owner": "ari", "risk_tier": "R4",
        "live_state": "live", "approval_state": "approved",
    }, ensure_ascii=False), "utf-8")
    (d / "organ.json").write_text(json.dumps({
        "logical_id": "urn:octopus:organ:heart", "entity_type": "Organ",
        "display_name": "Heart", "physical_path": "_ops/heart",
        "owner": "ari", "risk_tier": "R2", "live_state": "shadow",
        "approval_state": "approved",
    }, ensure_ascii=False), "utf-8")
    (d / "broken.json").write_text("{not json", "utf-8")   # fail-soft
    return d


def _snap(with_pf: bool = True):
    root = _mk_vault(Path(ENV["root"]) / f"v{with_pf}", with_pf)
    ents = _mk_manifests(root / "manifests")
    return rs.build_snapshot(root=root, entities_dir=ents)


def t_discovery_unknown_defaults():
    s = _snap()
    beta = next(e for e in s["entities"] if e["display_name"] == "Beta")
    for k in ("owner", "risk_tier", "live_state", "approval_state"):
        assert beta[k] == rs.UNKNOWN                       # A5: unknown، نه حدس
    assert beta["conformance_score"] < 1.0
    assert not any(e["display_name"] == "_Index" for e in s["entities"])


def t_frontmatter_lift_and_r3_cap():
    s = _snap()
    a = next(e for e in s["entities"] if e["display_name"] == "Alpha")
    assert a["owner"] == "آری" and a["risk_tier"] == "R2"   # medium→R2
    assert a["live_state"] == "live"                        # active→live
    assert a["risk_tier"] in ("R1", "R2", "R3")             # اسکنر هرگز R4/R5 نمی‌دهد
    assert "autonomy_note" in a["notes"]                    # read-only ≠ L*


def t_manifest_overrides_scan():
    s = _snap()
    h = next(e for e in s["entities"] if e["logical_id"] == "urn:octopus:organ:heart")
    assert h["live_state"] == "shadow" and h["source"] == "manifest"
    assert h["conformance_score"] == 1.0


def t_content_free_containment_zero_echo():
    """پوشهٔ حساس هست ولی snapshot فقط Project-F ِ manifest را دارد — صفر echo."""
    s = _snap(with_pf=True)
    pf = next(e for e in s["entities"] if e["logical_id"] == "urn:octopus:project:project-f")
    assert pf["display_name"] == "Project-F" and pf["risk_tier"] == "R4"
    blob = json.dumps(s, ensure_ascii=False)
    for banned in ("اونلی", "onlyfans", "OnlyFans", "صبا", "secret-platform"):
        assert banned not in blob, f"containment شکست: {banned}"
    assert "folder_sha256" not in blob                      # حتی هش هم واردِ snapshot نمی‌شود


def t_agents_discovered_registries_skipped():
    s = _snap()
    names = [e["display_name"] for e in s["entities"] if e["entity_type"] == "Agent"]
    assert "Research Scout Fleet" in names
    assert "AGENT_REGISTRY" not in names and "_Index - Agents" not in names


def t_counts_and_schema():
    s = _snap()
    assert s["schema"] == rs.SCHEMA and s["counts"]["total"] == len(s["entities"])
    assert s["counts"]["unknown_owner"] >= 1                # Beta
    assert 0.0 <= s["counts"]["avg_conformance"] <= 1.0
    assert "🗂" in rs.summary(s)


def t_read_only_and_injected_out_only():
    root = _mk_vault(Path(ENV["root"]) / "ro", with_pf=False)
    ents = _mk_manifests(root / "manifests")
    before = sorted(p.name for p in (root / "03 - Projects").rglob("*"))
    rs.build_snapshot(root=root, entities_dir=ents)         # خالص — هیچ نوشتنی
    after = sorted(p.name for p in (root / "03 - Projects").rglob("*"))
    assert before == after


def t_fail_soft_missing_dirs():
    empty = Path(ENV["root"]) / "empty"
    empty.mkdir(exist_ok=True)
    s = rs.build_snapshot(root=empty, entities_dir=empty / "none")
    assert s["counts"]["total"] == 0 and s["entities"] == []


def t_agent_risk_lifted():
    """الحاق (#۱): risk_level ِ ایجنت هم خوانده می‌شود — parity با پروژه‌ها."""
    s = _snap()
    m = next(e for e in s["entities"] if e["display_name"] == "Mycelium Scout")
    assert m["entity_type"] == "Agent"
    assert m["risk_tier"] == "R3" and m["risk_declared"] == "high"
    # ایجنتِ بدونِ risk_level → همان unknown (تضادِ صادقانه)
    f = next(e for e in s["entities"] if e["display_name"] == "Research Scout Fleet")
    assert f["risk_tier"] == rs.UNKNOWN and f["risk_declared"] == ""


def t_critical_recognized_not_unknown():
    """«بشناس» (#۲): critical صادقانه ثبت می‌شود، از unknown متمایز، ولی R4 خودکار نمی‌گیرد."""
    s = _snap()
    g = next(e for e in s["entities"] if e["display_name"] == "Gamma")
    assert g["risk_declared"] == "critical"                     # صادقانه ثبت شد
    assert g["risk_tier"] == rs.TIER_R4_PENDING                 # نه unknown، نه R4
    assert g["risk_tier"] not in ("R4", "R5", rs.UNKNOWN)       # نه ارتقای خودکار، نه گم‌شدن
    beta = next(e for e in s["entities"] if e["display_name"] == "Beta")
    assert g["risk_tier"] != beta["risk_tier"]                  # critical ≠ «مالک هیچ نگفت»
    assert s["counts"]["pending_r4"] >= 1                       # در summary دیده می‌شود


def t_critical_counts_as_known():
    """critical در سطلِ unknown_risk نمی‌افتد؛ مالک ریسک را اعلام کرده → بیش از «هیچ» می‌ارزد."""
    s = _snap()
    g = next(e for e in s["entities"] if e["display_name"] == "Gamma")
    beta = next(e for e in s["entities"] if e["display_name"] == "Beta")
    assert g["risk_tier"] != rs.UNKNOWN
    assert g["conformance_score"] > beta["conformance_score"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_registry_scan: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
