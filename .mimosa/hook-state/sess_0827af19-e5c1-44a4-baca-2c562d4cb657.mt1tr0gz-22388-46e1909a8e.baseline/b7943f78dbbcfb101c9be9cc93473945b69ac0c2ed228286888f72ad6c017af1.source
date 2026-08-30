#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_kernel_bridge_reader — تست‌های WP-D: body_bridge shadow reader.

تست می‌کند:
  - freshness: fresh / stale / missing تفکیک می‌شوند
  - integrity: corrupt تفکیک می‌شوند
  - schema_compat: incompatible تفکیک می‌شوند
  - هیچ‌کدام به empty/healthy تبدیل نمی‌شوند
  - default OFF
  - هیچ import از 4d_system ندارد
  - هیچ production decision change نمی‌دهد
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("kernel-bridge-reader")


def _reload_reader(bridge_output: Path, report_path: Path):
    """Reload kernel_bridge_reader with paths pointed at temp dirs."""
    import kernel_bridge_reader as kbr
    kbr.BRIDGE_OUTPUT = bridge_output
    kbr.REPORT_PATH = report_path
    return kbr


def _make_bridge_dir() -> Path:
    d = Path(os.environ.get("ORG_ROOT", "/tmp")) / "fake_bridge" / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─── TESTS ────────────────────────────────────────────────────────────────────

def t_default_off():
    """reader باید default OFF باشد."""
    import kernel_bridge_reader as kbr
    os.environ.pop("OCTOPUS_WIRE_KERNEL_BRIDGE_READER", None)
    assert not kbr._is_enabled()


def t_no_import_from_4d_system():
    """هیچ import واقعی از 4d_system نباید باشد (نه صرفاً mention در comment)."""
    import kernel_bridge_reader as kbr
    import ast
    src = Path(kbr.__file__).read_text("utf-8")
    tree = ast.parse(src)
    # Check all import statements
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "4d_system" not in alias.name, \
                    f"نباید 4d_system را import کند: {alias.name}"
                assert "kernel_consumer" not in alias.name, \
                    f"نباید kernel_consumer را import کند: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert "4d_system" not in module, \
                f"نباید از 4d_system import کند: {module}"
            assert "kernel_consumer" not in module, \
                f"نباید kernel_consumer را import کند: {module}"


def t_missing_artifact_not_healthy():
    """artifact مفقود نباید healthy باشد."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    r = kbr.read_status()
    assert r["artifacts"]["manifest"]["freshness"] == "missing"
    assert r["overall_ok"] == False, "مفقودبودن نباید overall_ok=True"


def t_corrupt_artifact_not_healthy():
    """artifact corrupt نباید ok باشد."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    (d / "manifest.json").write_text("{corrupt json", "utf-8")
    r = kbr.read_status()
    assert r["artifacts"]["manifest"]["integrity"] == "corrupt"


def t_stale_artifact_marked_stale():
    """artifact قدیمی باید stale باشد، نه fresh."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    # Write a valid manifest with old mtime
    (d / "manifest.json").write_text(
        json.dumps({"generated_at": "2026-01-01", "schema": "v1"}), "utf-8")
    # Set mtime to 100 hours ago
    old_ts = time.time() - 100 * 3600
    os.utime(str(d / "manifest.json"), (old_ts, old_ts))
    r = kbr.read_status(max_age_h=48)
    assert r["artifacts"]["manifest"]["freshness"] == "stale"


def t_fresh_artifact_marked_fresh():
    """artifact تازه باید fresh باشد."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    (d / "manifest.json").write_text(
        json.dumps({"generated_at": "2026-08-10", "schema": "v1"}), "utf-8")
    r = kbr.read_status(max_age_h=48)
    assert r["artifacts"]["manifest"]["freshness"] == "fresh"


def t_schema_incompatible_detected():
    """schema ناسازگار باید incompatible باشد."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    # Write a manifest without expected keys
    (d / "manifest.json").write_text(
        json.dumps({"unexpected_key": "value"}), "utf-8")
    r = kbr.read_status()
    assert r["artifacts"]["manifest"]["schema_compat"] == "incompatible"


def t_jsonl_corrupt_lines_counted():
    """خطوط corrupt در JSONL باید شمرده شوند."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    (d / "verdict_stream.jsonl").write_text(
        '{"valid": true}\n{corrupt\n{"also valid": true}\n', "utf-8")
    r = kbr.read_status()
    vs = r["artifacts"]["verdict_stream"]
    assert vs["integrity"] == "corrupt"
    assert vs["detail"]["corrupt_lines"] >= 1


def t_persist_only_when_enabled():
    """persist_report نباید بنویسد وقتی OFF است."""
    d = _make_bridge_dir()
    report_path = d.parent / "report-off.json"
    kbr = _reload_reader(d, report_path)
    os.environ.pop("OCTOPUS_WIRE_KERNEL_BRIDGE_READER", None)
    result = kbr.persist_report()
    assert result["ok"] == False
    assert not report_path.exists()


def t_persist_writes_when_enabled():
    """persist_report باید بنویسد وقتی ON است."""
    d = _make_bridge_dir()
    report_path = d.parent / "report-on.json"
    kbr = _reload_reader(d, report_path)
    os.environ["OCTOPUS_WIRE_KERNEL_BRIDGE_READER"] = "1"
    try:
        result = kbr.persist_report()
        assert result["ok"] == True
        assert report_path.exists()
        data = json.loads(report_path.read_text("utf-8"))
        assert data["schema"] == "KernelBridgeReaderReport.v1"
    finally:
        os.environ.pop("OCTOPUS_WIRE_KERNEL_BRIDGE_READER", None)


def t_never_raises_on_missing_dir():
    """read_status نباید crash کند حتی اگر bridge output dir غایب باشد."""
    kbr = _reload_reader(Path("/nonexistent/bridge/output"),
                         Path("/nonexistent/report.json"))
    r = kbr.read_status()  # should not raise
    assert "artifacts" in r


def t_all_artifacts_checked():
    """هر چهار artifact باید بررسی شوند."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    r = kbr.read_status()
    expected = {"manifest", "adr_feed", "verdict_stream", "kernel_dashboard"}
    assert set(r["artifacts"].keys()) == expected


def t_overall_ok_only_when_all_ok():
    """overall_ok فقط وقتی همه fresh+ok+compatible باشند."""
    d = _make_bridge_dir()
    report_path = d.parent / "report.json"
    kbr = _reload_reader(d, report_path)
    # All four artifacts present and valid
    (d / "manifest.json").write_text(
        json.dumps({"generated_at": "2026-08-10", "schema": "v1"}), "utf-8")
    (d / "adr_feed.json").write_text(
        json.dumps({"adrs": [], "generated_at": "2026-08-10"}), "utf-8")
    (d / "verdict_stream.jsonl").write_text(
        json.dumps({"claim_id": "C1"}) + "\n", "utf-8")
    (d / "kernel_dashboard.json").write_text(
        json.dumps({"manifest": {}, "adr_feed": {}, "verdict_stream": {}}), "utf-8")
    r = kbr.read_status()
    assert r["overall_ok"] == True, "all-ok باید overall_ok=True بسازد"


# ─── RUN ──────────────────────────────────────────────────────────────────────

CHECKS = [
    ("default-off", t_default_off),
    ("no-import-from-4d-system", t_no_import_from_4d_system),
    ("missing-artifact-not-healthy", t_missing_artifact_not_healthy),
    ("corrupt-artifact-not-healthy", t_corrupt_artifact_not_healthy),
    ("stale-artifact-marked-stale", t_stale_artifact_marked_stale),
    ("fresh-artifact-marked-fresh", t_fresh_artifact_marked_fresh),
    ("schema-incompatible-detected", t_schema_incompatible_detected),
    ("jsonl-corrupt-lines-counted", t_jsonl_corrupt_lines_counted),
    ("persist-only-when-enabled", t_persist_only_when_enabled),
    ("persist-writes-when-enabled", t_persist_writes_when_enabled),
    ("never-raises-on-missing-dir", t_never_raises_on_missing_dir),
    ("all-artifacts-checked", t_all_artifacts_checked),
    ("overall-ok-only-when-all-ok", t_overall_ok_only_when_all_ok),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
