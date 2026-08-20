"""Lab-only append-only evidence store. Not a daemon. Auto-delete OFF."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .observation import Observation


def _canonical(rec: dict[str, Any]) -> str:
    return json.dumps(rec, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def record_hash(rec: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(rec).encode("utf-8")).hexdigest()


class EvidenceStore:
    """JSONL justified: ~1.16MB/day @113s vs many small files; rotation designed, delete OFF."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = set()
        if self.path.exists():
            for ln in self.path.read_text("utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    rec = json.loads(ln)
                    oid = rec.get("observation_id")
                    if oid:
                        self._seen.add(str(oid))
                except json.JSONDecodeError:
                    continue

    def append(self, obs: Observation) -> dict[str, Any]:
        rec = obs.to_dict()
        rec["schema"] = "shadow-evidence.v1"
        rec["record_hash"] = record_hash(rec)
        oid = str(rec.get("observation_id") or "")
        if oid in self._seen:
            return {"ok": True, "duplicate": True, "observation_id": oid}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        prior = self.path.read_text("utf-8") if self.path.exists() else ""
        tmp.write_text(prior + line, encoding="utf-8")
        try:
            with tmp.open("ab") as fh:
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            pass
        os.replace(tmp, self.path)
        self._seen.add(oid)
        return {"ok": True, "duplicate": False, "observation_id": oid, "record_hash": rec["record_hash"]}

    def record_gap(self, beat: int, reason: str, decision_time: datetime) -> dict[str, Any]:
        rec = {
            "schema": "shadow-evidence-gap.v1",
            "kind": "GAP",
            "beat": int(beat),
            "reason": reason,
            "occurred_at": None,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "decision_time": decision_time.astimezone(timezone.utc).isoformat(),
            "note": "missing beat is not synthesized",
        }
        rec["record_hash"] = record_hash(rec)
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        return rec

    def snapshot_latest(self, latest_path: Path, *, beat_claim: int | None, historical: bool) -> dict[str, Any]:
        """Read-only copy of a mutable latest.json into this store as UNLOCATED if historical."""
        raw = json.loads(latest_path.read_text("utf-8"))
        payload = json.dumps(raw, sort_keys=True).encode("utf-8")
        sh = hashlib.sha256(payload).hexdigest()
        return {
            "source": str(latest_path),
            "source_hash": sh,
            "beat_in_file": raw.get("beat"),
            "historical_claim": historical,
            "beat_claim": beat_claim,
            "can_prove_historical": (not historical) and beat_claim == raw.get("beat"),
        }

    @staticmethod
    def rotation_policy() -> dict[str, Any]:
        return {
            "hot_days": 14,
            "warm_days": 90,
            "cap_mb": 200,
            "auto_delete": False,
            "justification": "1515B/beat * 86400/113 ≈ 1.16MB/day; jsonl cheaper than per-beat files",
        }
