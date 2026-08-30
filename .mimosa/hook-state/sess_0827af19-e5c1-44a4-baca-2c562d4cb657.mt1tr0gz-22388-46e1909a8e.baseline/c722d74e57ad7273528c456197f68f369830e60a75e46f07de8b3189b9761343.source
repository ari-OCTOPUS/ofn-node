"""Tests for dashboard_sync.py."""
import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path("F:/backup/03 - Projects/research-spec-compiler/body_bridge").resolve()))

import dashboard_sync as ds


@pytest.fixture
def temp_env(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out_dir = root / "body_bridge" / "output"
        out_dir.mkdir(parents=True)

        monkeypatch.setattr(ds, "KERNEL_ROOT", root)
        monkeypatch.setattr(ds, "BODY_OUTPUT", out_dir)
        monkeypatch.setattr(ds, "DASHBOARD_PATH", out_dir / "kernel_dashboard.json")
        monkeypatch.setattr(ds, "LEDGER_PATH", root / "CLAIMS_LEDGER.csv")
        if hasattr(ds, "_MODULE_DIR"):
            monkeypatch.setattr(ds, "_MODULE_DIR", out_dir.parent)
        if hasattr(ds, "_KERNEL_ROOT"):
            monkeypatch.setattr(ds, "_KERNEL_ROOT", root)

        # Write upstream feeds
        manifest = {
            "kernel_name": "Cognitive Kernel 0.1",
            "experiments": [{"name": "e1", "status": "done"}],
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        adr_feed = {
            "adrs": [
                {"adr_number": 1, "title": "A", "verdict": "INTEGRATE", "date": "2026-07-13", "spec": "s1.yaml"},
                {"adr_number": 2, "title": "B", "verdict": "REJECTED", "date": "2026-07-14", "spec": "s2.yaml"},
                {"adr_number": 3, "title": "C", "verdict": "OPTIMIZE", "date": "2026-07-14", "spec": "s3.yaml"},
            ],
            "total": 3,
        }
        (out_dir / "adr_feed.json").write_text(json.dumps(adr_feed), encoding="utf-8")

        # Verdict stream (jsonl)
        with (out_dir / "verdict_stream.jsonl").open("w", encoding="utf-8") as f:
            f.write(json.dumps({"claim_id": "ADR-001", "verdict": "INTEGRATE", "timestamp": "2026-07-14T10:00:00Z"}) + "\n")
            f.write(json.dumps({"claim_id": "ADR-002", "verdict": "REJECTED", "timestamp": "2026-07-14T10:01:00Z"}) + "\n")

        # GEOMETRY.md
        geo = root / "GEOMETRY.md"
        geo.write_text("[RUN] ontology_shift\n[RUN] multimetric_memory\n[MAP] attractor_memory\n", encoding="utf-8")

        # Ledger
        ledger = root / "CLAIMS_LEDGER.csv"
        ledger.write_text(
            "claim_id,claim,c_level,verdict,primary_metric,primary_value,evidence_tag,source,spec,seed_family,caveats\n"
            "ADR-001,Claim1,C0,INTEGRATE,m1,0.80,FACT,src,s1.yaml,123,none\n"
            "ADR-002,Claim2,C0,REJECTED,m1,0.20,FACT,src,s2.yaml,123,none\n",
            encoding="utf-8",
        )

        yield root, out_dir


class TestDashboardSync:
    def test_sync_produces_dashboard(self, temp_env):
        root, out_dir = temp_env
        dash = ds.sync()
        assert out_dir.joinpath("kernel_dashboard.json").exists()
        assert dash["adr_count"] == 3
        assert dash["experiment_count"] == 1
        assert "tally" in dash
        assert dash["identity_anchor"] == 0.135073

    def test_tally_counts(self, temp_env):
        root, out_dir = temp_env
        dash = ds.sync()
        tally = dash["tally"]
        assert tally["INTEGRATE"] >= 1
        assert tally["REJECTED"] >= 1

    def test_high_priority_adr(self, temp_env):
        root, out_dir = temp_env
        dash = ds.sync()
        high = dash["high_priority_adr"]
        assert any(a.get("adr_number") == 2 for a in high)

    def test_geometry_status(self, temp_env):
        root, out_dir = temp_env
        dash = ds.sync()
        geo = dash["geometry_status"]
        assert geo is not None

    def test_persian_report(self, temp_env):
        root, out_dir = temp_env
        dash = ds.sync()
        report = dash["persian_report"]
        assert "کرنل" in report
        assert "ADR" in report

    def test_get_metric(self, temp_env):
        root, out_dir = temp_env
        ds.sync()
        assert ds.get_metric("adr_count") == 3
        assert ds.get_metric("identity_anchor") == 0.135073
        assert ds.get_metric("nonexistent.key") is None

    def test_body_bridge_status(self, temp_env):
        root, out_dir = temp_env
        dash = ds.sync()
        bbs = dash["body_bridge_status"]
        assert "last_sync" in bbs
        assert isinstance(bbs["fresh_events_available"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
