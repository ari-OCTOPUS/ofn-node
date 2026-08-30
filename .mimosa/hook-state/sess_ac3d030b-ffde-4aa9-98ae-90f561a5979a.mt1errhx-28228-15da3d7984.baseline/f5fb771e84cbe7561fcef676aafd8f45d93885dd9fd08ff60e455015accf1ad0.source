"""Offline test of the LLM 'brain' wiring (no network, no API key).

Injects a fake transport so the real code path (router -> complete -> cost ->
ledger METRIC -> creativity JSON parse -> propose) is exercised end to end.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("ledger", "common", "agents"):
    sys.path.insert(0, str(ROOT / sub))

from config import Genome            # noqa: E402
from ledger import Ledger           # noqa: E402
from llm import LLMClient, creativity_llm_fn  # noqa: E402
from creativity import Creativity   # noqa: E402


def main() -> int:
    genome = Genome.load(ROOT / "genome")
    ledger = Ledger(Path(tempfile.mkdtemp()) / "ledger.jsonl")

    # fake Anthropic Messages response for the creativity task
    def fake(model, system, user, max_tokens):
        assert model == "claude-sonnet-5", f"creativity should route to default tier, got {model}"
        payload = {
            "idea": "Batch the nightly digest and only escalate 'surprising' notes.",
            "why_it_might_be_genius": "cuts digest cost ~5x",
            "why_it_might_be_insane": "'surprising' classifier could hide a P0 note",
            "confidence": 0.3,
            "kill_criteria": "if any P0 note is missed in a week, revert",
            "smallest_test": "shadow-run 7 days vs full digest",
            "reversible": True,
        }
        return {"content": [{"type": "text", "text": "```json\n" + json.dumps(payload) + "\n```"}],
                "usage": {"input_tokens": 1000, "output_tokens": 200}, "model": model}

    client = LLMClient(genome, api_key="test", transport=fake, ledger=ledger)

    # 1) routing + cost metering (Sonnet 5 intro price 2/10)
    out = client.complete("creativity", "sys", "user")
    expected = 1000 / 1e6 * 2 + 200 / 1e6 * 10   # = 0.004
    assert abs(out["cost_usd"] - expected) < 1e-9, out
    assert out["tier"] == "default"
    print(f"1) router+cost: creativity -> {out['model']} tier={out['tier']} "
          f"cost=${out['cost_usd']:.4f}")

    # 2) real llm_fn path -> valid PROPOSAL through the humility gate
    fn = creativity_llm_fn(client)
    rec = Creativity(ledger).propose(topic="cost", llm_fn=fn)
    assert rec["type"] == "PROPOSAL" and rec["payload"]["kill_criteria"]
    assert 0.0 <= rec["payload"]["confidence"] <= 1.0
    print("2) creativity(real llm_fn): PROPOSAL parsed from model JSON, contract enforced")

    # 3) cost guard: a huge-usage call flags over_cap (doctor -> Opus 5/25)
    def big(model, system, user, mt):
        return {"content": [{"type": "text", "text": "{}"}],
                "usage": {"input_tokens": 9_000_000, "output_tokens": 0}}
    c2 = LLMClient(genome, transport=big, ledger=ledger)
    o2 = c2.complete("doctor", "s", "u")          # 9M * $5/M = $45 > $2 cap
    assert o2["over_cap"] and o2["model"] == "claude-opus-4-8", o2
    print(f"3) cost-guard: doctor call ${o2['cost_usd']:.2f} > cap -> over_cap={o2['over_cap']}")

    # 4) cost METRICs actually landed in the ledger
    metrics = [e for e in ledger.filter(event_type="METRIC") if "llm_cost_usd" in e["payload"]]
    assert len(metrics) >= 2, "llm cost not metered to ledger"
    ok, msg = ledger.verify()
    assert ok, msg
    print(f"4) ledger: {len(metrics)} llm-cost METRICs logged; hash-chain intact")

    print("\nPASS: brain wiring green (offline, fake transport).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
