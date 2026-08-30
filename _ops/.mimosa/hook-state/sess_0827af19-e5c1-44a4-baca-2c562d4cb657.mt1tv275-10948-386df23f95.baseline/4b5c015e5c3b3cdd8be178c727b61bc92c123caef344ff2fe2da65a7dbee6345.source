"""Temporary deletable sidecar: organism READ → shadow pipeline → rendered DeepSeek → lab ledger.

Does not patch organism.py. Does not write _ops/state. executable=false.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shadow_homeostasis.pipeline import run_shadow_pipeline

from . import budget as flash_budget
from . import gateway, judge, memory_lab, telemetry

SCHEMA = "full-loop-stage-a.v1"


def _dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    path.write_text(gateway.redact(text) + "\n", encoding="utf-8")


def hop_map(stage: str, network_sent: bool) -> dict[str, Any]:
    """Honest hop labels. Missing hop ⇒ not full-octopus."""
    return {
        "real_user_task": True,
        "owner_cockpit_intake": "INBOX_TASK_STANDIN (direct cockpit API UNLOCATED)",
        "telemetry_trust": True,
        "homeostatic_core": True,
        "memory_retrieval": True,
        "world_model": True,
        "metacontrol_gate": True,
        "fugu_gateway_model_router": "LAB_FACADE_OVER_DeepSeekClient (paid-calls.jsonl path skipped)",
        "deepseek_flash_api": bool(network_sent),
        "verifier_judge": True,
        "proposed_action": True,
        "memory_write": "LAB_STORE_ONLY",
        "ledger": "LAB_JSONL",
        "telemetry_write_live": False,
        "full_octopus": False,
        "label": "sidecar_loop" if network_sent else "sidecar_preflight_no_network",
        "stage": stage,
    }


def run_stage_a(
    *,
    lab_dir: Path,
    evidence_dir: Path | None = None,
    paths: dict[str, Path] | None = None,
    decision_time: datetime | None = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    if allow_network:
        raise RuntimeError("Stage A forbids network")
    lab_dir = Path(lab_dir)
    lab_dir.mkdir(parents=True, exist_ok=True)
    dt = decision_time or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    task = telemetry.load_real_task(paths)
    mem = memory_lab.retrieve_for_task(task, lab_dir)
    obs, tele_meta = telemetry.read_live(dt, paths=paths)
    pipe = run_shadow_pipeline(obs, decision_time=dt, boot_id=tele_meta.get("boot_id"))
    reservation = flash_budget.reserve(lab_dir, est_aud=0.01, stage="A")
    rendered = gateway.render_chat_completions(
        task=task, pipeline=pipe, memory=mem, reservation=reservation, handshake=True,
    )
    if rendered.get("network") is not False:
        raise RuntimeError("Stage A rendered request must set network=false")
    j = judge.advisory(pipeline=pipe, rendered=rendered)
    after = memory_lab.write_lab(lab_dir, task_id=str(task.get("task_id")), kind="stage_a_result", payload={
        "homeostatic_state": (pipe.get("homeostatic_assessment") or {}).get("global_state"),
        "prompt_sha256": rendered.get("prompt_sha256"),
        "judge": j.get("verdict"),
    })
    after_back = memory_lab.read_lab(lab_dir, after["id"])
    exec_n = judge.count_executable_true(pipe) + judge.count_executable_true(rendered) + judge.count_executable_true(j)

    pack = {
        "schema": SCHEMA,
        "stage": "A",
        "pass": bool(
            mem.get("memory_gate") == "PASS"
            and exec_n == 0
            and rendered.get("network") is False
            and j.get("executable") is False
            and reservation.get("ok")
            and after_back is not None
        ),
        "task": {k: task[k] for k in task if k != "excerpt"},
        "telemetry": tele_meta,
        "memory": {
            "gate": mem.get("memory_gate"),
            "live_label": mem.get("live_memory_label"),
            "evidence_ids": mem.get("evidence_ids"),
            "lab_record_id": mem.get("lab_record_id"),
            "readback": mem.get("readback"),
            "live_status": {k: (v.get("status") if isinstance(v, dict) else v) for k, v in (mem.get("live") or {}).items()},
            "after_write_id": after["id"],
            "after_readback": bool(after_back),
        },
        "pipeline_output_hash": pipe.get("output_hash"),
        "homeostatic_state": (pipe.get("homeostatic_assessment") or {}).get("global_state"),
        "skill_scores": rendered.get("skill_scores"),
        "budget_reservation": rendered.get("budget_reservation"),
        "rendered_prompt_sha256": rendered.get("prompt_sha256"),
        "judge": j,
        "executable": False,
        "executable_true_count": exec_n,
        "external_action": False,
        "network_sent": False,
        "model_calls": 0,
        "aud_spent": 0.0,
        "k9_mixed": False,
        "organism_py_patched": False,
        "hops": hop_map("A", False),
        "circuit": gateway.circuit_snapshot(),
        "key": gateway.key_status(),
        "invariants": {
            "wave": "WAVE0_OBSERVE_ONLY",
            "autonomy": "L2_ARMED",
            "GAP-001": "OPEN",
            "D6": "BETWEEN_RUN_VARIANCE",
            "live_spine": "NOT_VERIFIED_BITEMPORAL",
        },
    }
    if evidence_dir is not None:
        ev = Path(evidence_dir)
        ev.mkdir(parents=True, exist_ok=True)
        _dump(ev / "STAGE-A.json", pack)
        _dump(ev / "RENDERED-REQUEST.json", rendered)
        _dump(ev / "PIPELINE.json", {
            "output_hash": pipe.get("output_hash"),
            "homeostatic_assessment": pipe.get("homeostatic_assessment"),
            "world_state": {
                "state_id": (pipe.get("world_state") or {}).get("state_id"),
                "n_facts": len((pipe.get("world_state") or {}).get("facts") or []),
                "n_hypotheses": len((pipe.get("world_state") or {}).get("hypotheses") or []),
            },
            "gate_decisions": pipe.get("gate_decisions"),
            "executable": pipe.get("executable"),
        })
        (ev / "STAGE-A.md").write_text(_stage_a_md(pack, rendered), encoding="utf-8")
        pack["evidence_dir"] = str(ev).replace("\\", "/")
    pack["rendered"] = rendered
    return pack


def _stage_a_md(pack: dict[str, Any], rendered: dict[str, Any]) -> str:
    skills = rendered.get("skill_scores") or {}
    skill_lines = "\n".join(
        f"- `{k}`: score={v.get('score')} mode={v.get('mode')}" for k, v in skills.items()
    )
    eids = "\n".join(f"- `{x}`" for x in (rendered.get("evidence_ids") or [])[:24])
    user = ((rendered.get("body") or {}).get("messages") or [{}, {}])[1].get("content", "")
    return f"""---
type: evidence
status: active
tags: [octopus, full-loop, stage-a, flash]
created: 2026-08-20
updated: 2026-08-20
---

# FULL-LOOP FLASH — Stage A preflight (NO NETWORK)

**5A soak: SUSPENDED.** This is not a 4h shadow-only soak and not a "full octopus" claim.

Verdict: **{'PASS' if pack.get('pass') else 'FAIL'}**
`executable=true` count: `{pack.get('executable_true_count')}`
model calls: `0` · AUD spent: `0` · K9 mixed: `NO` · organism.py patched: `NO`

## Hops (honest)

Sidecar reads live telemetry and an Inbox task, runs Trust→HC→WM→Metacontrol,
attaches lab memory with read-back, reserves isolated flash budget, **renders**
`POST /chat/completions`, then **STOPS**. DeepSeek was not called. `model_router.ask`
was not used (it would write `_ops/state/paid-calls.jsonl`).

Cockpit/Intake: Inbox task stand-in (`FRONTMATTER-DEBT-2026-08-20`); direct Owner Cockpit API = UNLOCATED.

## Rendered prompt (redacted, no key)

Endpoint: `{rendered.get('endpoint')}`
Authorization header: `{rendered.get('authorization_header')}`
prompt_sha256: `{rendered.get('prompt_sha256')}`

```
{gateway.redact(user)}
```

## Evidence IDs

{eids or '- (none)'}

## Memory

- lab read-back: `{pack['memory'].get('readback')}`
- live label: `{pack['memory'].get('live_label')}`
- live status: `{pack['memory'].get('live_status')}`

## Skill scores

{skill_lines}

## Budget reservation (flash, not K=9)

`{json.dumps(rendered.get('budget_reservation'), ensure_ascii=True)}`

## Homeostasis / judge

- HC global: `{pack.get('homeostatic_state')}`
- judge: `{pack['judge'].get('verdict')}` advisory (D6=BETWEEN_RUN_VARIANCE)
- pipeline hash: `{pack.get('pipeline_output_hash')}`

## STOP

Stage B (one tiny DeepSeek Flash call) only if this pack is PASS and DEEPSEEK_API_KEY is present.
Stage C (1h) only if all six gates are green after A+B. Do not start soak #5A.
"""
