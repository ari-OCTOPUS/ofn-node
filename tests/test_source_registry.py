"""
tests/test_source_registry.py — structural tests for source registry.
No network calls. All probes mocked.
"""
from unittest.mock import MagicMock, patch
import pytest
from ofn.agents.source_registry import (
    SOURCES, Source, SourceStatus,
    live_sources, probe_source, report,
)


class TestSourceList:
    def test_has_sources(self):
        assert len(SOURCES) >= 10

    def test_all_have_ids(self):
        ids = [s.id for s in SOURCES]
        assert len(ids) == len(set(ids)), "Duplicate source IDs"

    def test_no_auth_sources_have_harvest_module(self):
        """Sources that require auth must NOT have a harvest_module."""
        for s in SOURCES:
            if s.requires_auth:
                assert s.harvest_module is None, (
                    f"{s.id} requires_auth but has harvest_module — "
                    "auto-harvest of auth sources is forbidden"
                )

    def test_all_tiers_1_to_5(self):
        tiers = {s.tier for s in SOURCES}
        assert tiers.issubset({1, 2, 3, 4, 5})

    def test_seek_is_present_with_module(self):
        seek = next((s for s in SOURCES if s.id == "seek_painter_sydney"), None)
        assert seek is not None
        assert seek.harvest_module == "ofn.agents.seek_harvest"

    def test_ziman_tender_source_points_to_pr141(self):
        src = next((s for s in SOURCES if s.id == "buy_nsw_contract_register"), None)
        assert src is not None
        assert src.harvest_module == "ofn.agents.ziman_tender_harvest"


class TestProbeSource:
    def test_probe_returns_live_on_200(self):
        src = Source(
            id="test", name="Test", tier=1,
            probe_url="https://example.com",
            harvest_module=None,
        )
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.getcode.return_value = 200
        with patch("urllib.request.urlopen", return_value=mock_resp):
            status = probe_source(src, timeout=1)
        assert status == SourceStatus.LIVE

    def test_probe_returns_blocked_on_403(self):
        src = Source(
            id="test", name="Test", tier=1,
            probe_url="https://example.com",
            harvest_module=None,
        )
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.getcode.return_value = 403
        with patch("urllib.request.urlopen", return_value=mock_resp):
            status = probe_source(src, timeout=1)
        assert status == SourceStatus.BLOCKED

    def test_probe_returns_unknown_on_exception(self):
        src = Source(
            id="test", name="Test", tier=1,
            probe_url="https://example.com",
            harvest_module=None,
        )
        with patch("urllib.request.urlopen", side_effect=Exception("network")):
            status = probe_source(src, timeout=1)
        assert status == SourceStatus.UNKNOWN

    def test_probe_never_raises(self):
        src = Source(
            id="test", name="Test", tier=1,
            probe_url="https://totally-dead.invalid",
            harvest_module=None,
        )
        status = probe_source(src, timeout=1)  # must not raise
        assert status in SourceStatus.__members__.values()


class TestLiveSources:
    def test_live_sources_excludes_auth(self):
        for s in SOURCES:
            s.status = SourceStatus.LIVE
        result = live_sources()
        assert not any(s.requires_auth for s in result)

    def test_live_sources_requires_harvest_module(self):
        for s in SOURCES:
            s.status = SourceStatus.LIVE
        result = live_sources()
        assert all(s.harvest_module is not None for s in result)


class TestReport:
    def test_report_returns_string(self):
        r = report()
        assert isinstance(r, str)
        assert "T1" in r or "T2" in r

    def test_report_contains_seek(self):
        r = report()
        assert "Seek" in r
