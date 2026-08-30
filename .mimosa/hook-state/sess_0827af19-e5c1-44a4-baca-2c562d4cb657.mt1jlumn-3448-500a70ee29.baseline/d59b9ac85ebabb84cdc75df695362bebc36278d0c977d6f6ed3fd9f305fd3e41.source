#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checkpoint_store.py — versioned run checkpoints (ADR-033).

LangGraph-style: snapshot per super-step. Missing store → fail-closed for execute.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

_OPS = Path(__file__).resolve().parents[1]
_CP_ROOT = _OPS / "state" / "adr-033" / "checkpoints"


@dataclass
class Checkpoint:
    run_id: str
    checkpoint_id: str
    state_version: int
    policy_version: str
    graph_version: str
    input_digest: str
    created_at: str
    node: str = "start"
    payload: dict[str, Any] = field(default_factory=dict)
    # Never store raw prompts — digests only in payload

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CheckpointStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or _CP_ROOT

    def available(self) -> bool:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            probe = self.root / ".probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True
        except OSError:
            return False

    def save(self, cp: Checkpoint) -> Path:
        if not self.available():
            raise RuntimeError("store_unavailable")
        d = self.root / cp.run_id
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{cp.checkpoint_id}.json"
        # Scrub forbidden keys
        safe_payload = {
            k: v for k, v in (cp.payload or {}).items()
            if k not in {"text", "prompt", "dm", "content", "token"}
        }
        data = cp.as_dict()
        data["payload"] = safe_payload
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, run_id: str, checkpoint_id: str) -> Checkpoint | None:
        path = self.root / run_id / f"{checkpoint_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return Checkpoint(
            run_id=data["run_id"],
            checkpoint_id=data["checkpoint_id"],
            state_version=int(data["state_version"]),
            policy_version=str(data["policy_version"]),
            graph_version=str(data.get("graph_version") or ""),
            input_digest=str(data.get("input_digest") or ""),
            created_at=str(data.get("created_at") or ""),
            node=str(data.get("node") or "start"),
            payload=dict(data.get("payload") or {}),
        )

    def create(
        self,
        *,
        run_id: str | None = None,
        policy_version: str,
        graph_version: str,
        input_digest: str,
        state_version: int = 0,
        node: str = "start",
        payload: dict[str, Any] | None = None,
    ) -> Checkpoint:
        cp = Checkpoint(
            run_id=run_id or f"run-{uuid4().hex[:12]}",
            checkpoint_id=f"cp-{uuid4().hex[:12]}",
            state_version=state_version,
            policy_version=policy_version,
            graph_version=graph_version,
            input_digest=input_digest,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            node=node,
            payload=payload or {},
        )
        self.save(cp)
        return cp
