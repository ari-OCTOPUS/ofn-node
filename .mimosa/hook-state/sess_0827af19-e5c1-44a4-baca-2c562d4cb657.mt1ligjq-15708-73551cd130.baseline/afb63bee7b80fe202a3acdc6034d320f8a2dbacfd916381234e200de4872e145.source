#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_research_ingest.py — research digest → MemoryGate episodic + trail (no authority)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "memory"),
           str(_HERE.parent / "outcomes"), str(_HERE.parent / "budget"),
           str(_HERE.parent / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("research-ingest")

import research_ingest as ri  # noqa: E402
import memory_store as ms  # noqa: E402
import gate as mg  # noqa: E402


def _digest():
    return {
        "ts": "2026-08-11T00:00:00+00:00",
        "schema": "research-latest.v1",
        "n_topics": 1,
        "findings": [{
            "topic": "vector memory databases",
            "query": "vector memory databases",
            "n": 1,
            "hits": [{
                "title": "Vector DB Overview",
                "url": "https://example.com/vdb",
                "snippet": "A short overview of vector memory stores.",
                "source": "wikipedia",
            }],
        }],
        "cost_aud": 0,
    }


def t_ingest_commits_and_trails_when_gate_on():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        state = Path(td) / "state"
        state.mkdir(parents=True)
        os.environ["OCTOPUS_STATE_DIR"] = str(state)
        os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
        summary = ri.ingest_digest(_digest(), root=state)
        assert summary["ok"] is True
        assert summary["n_hits"] == 1
        assert summary["committed"] >= 1, summary
        assert summary.get("may_authorize") is False
        trail = Path(summary["trail"])
        assert trail.exists()
        line = json.loads(trail.read_text(encoding="utf-8").splitlines()[0])
        assert line["mkey"].startswith("research:")
        assert line["gate_verb"] == "commit"
        st = ms.MemoryStore()  # uses OCTOPUS_STATE_DIR
        try:
            row = st.get("episodic", line["mkey"])
            assert row and "Vector DB Overview" in row["content"]
        finally:
            st.close()


def t_recall_from_trail_when_gate_off():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        state = Path(td) / "state"
        state.mkdir(parents=True)
        os.environ["OCTOPUS_STATE_DIR"] = str(state)
        os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "0"
        summary = ri.ingest_digest(_digest(), root=state)
        assert summary["ok"] and summary["n_hits"] == 1
        assert summary["committed"] == 0
        hits = ri.recall_recent("vector", k=3, root=state)
        assert hits, hits
        assert hits[0]["may_authorize"] is False
        assert "Vector DB" in hits[0]["content"]


def t_run_and_persist_includes_memory_ingest():
    import web_research as wr
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        state = Path(td) / "state"
        state.mkdir(parents=True)
        os.environ["OCTOPUS_STATE_DIR"] = str(state)
        os.environ["OCTOPUS_WIRE_WEB_RESEARCH"] = "1"
        os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "0"
        wr.RESEARCH_PATH = state / "pulse" / "research-latest.json"
        fake = (
            '<a class="result__a" href="https://ex.com/a">Autonomous Agents Survey</a>'
            '<a class="result__snippet">survey of agents</a>'
        )

        def _opener(url: str) -> str:
            if "duckduckgo" in url:
                return fake
            if "opensearch" in url:
                return json.dumps([
                    "q", ["Autonomous agent"], [""],
                    ["https://en.wikipedia.org/wiki/Autonomous_agent"],
                ])
            if "summary" in url:
                return json.dumps({
                    "title": "Autonomous agent",
                    "extract": "An agent acts.",
                    "content_urls": {
                        "desktop": {"page": "https://en.wikipedia.org/wiki/Autonomous_agent"},
                    },
                })
            if "arxiv" in url:
                return (
                    "<feed><entry><title>Agents</title><summary>agents</summary>"
                    "<id>http://arxiv.org/abs/1.2</id></entry></feed>"
                )
            return ""

        out = wr.run_and_persist(["autonomous ai agents"], opener=_opener)
        assert out.get("ok") is True, out
        assert "memory_ingest" in out
        assert out["memory_ingest"].get("may_authorize") is False
        trail = Path(out["memory_ingest"]["trail"])
        assert trail.exists()


def run():
    t_ingest_commits_and_trails_when_gate_on()
    t_recall_from_trail_when_gate_off()
    t_run_and_persist_includes_memory_ingest()
    print("PASS research_ingest")


if __name__ == "__main__":
    run()
