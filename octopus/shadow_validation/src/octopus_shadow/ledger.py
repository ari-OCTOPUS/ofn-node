from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

GENESIS = "0" * 64
RUNTIME_ROOT = Path("/var/lib/octopus/state/runtime")
CHAOS_ROOT = Path("/var/lib/octopus/state/chaos")
LIVE_JSONL_ROOT = Path("/var/lib/octopus/state/world_model")
NAMESPACES = frozenset({"runtime", "chaos"})


class LedgerError(ValueError):
    pass


def is_runtime_path(path: str | Path) -> bool:
    resolved = Path(path).expanduser().resolve()
    parts = {part.lower() for part in resolved.parts}
    if "runtime" in parts or "world_model" in parts:
        return True
    for root in (RUNTIME_ROOT, LIVE_JSONL_ROOT):
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


class PredictionLedger:
    """Append-only hash-chained SQLite events. Predictions are never updated."""

    def __init__(self, path: str | Path, namespace: str = "runtime") -> None:
        if namespace not in NAMESPACES:
            raise LedgerError("invalid_namespace")
        self.path = Path(path)
        self.namespace = namespace
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.database = sqlite3.connect(self.path)
        self.database.execute("PRAGMA journal_mode=WAL")
        self.database.execute("PRAGMA synchronous=FULL")
        self.database.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                prediction_id TEXT NOT NULL,
                created_ns INTEGER NOT NULL,
                body TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                event_hash TEXT UNIQUE NOT NULL,
                namespace TEXT NOT NULL DEFAULT 'runtime'
                    CHECK(namespace IN ('runtime','chaos')),
                executable INTEGER NOT NULL DEFAULT 0 CHECK(executable=0),
                action TEXT NOT NULL DEFAULT 'NONE' CHECK(action='NONE')
            )
            """
        )
        self.database.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS one_prediction_per_id
            ON events(prediction_id) WHERE event_type='PREDICTION'
            """
        )
        self.database.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS one_outcome_per_id
            ON events(prediction_id) WHERE event_type='OUTCOME'
            """
        )
        self.database.commit()

    @staticmethod
    def canonical_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def _head(self) -> str:
        row = self.database.execute("SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return row[0] if row else GENESIS

    def _insert(
        self,
        event_type: str,
        prediction_id: str,
        body: dict[str, Any],
        created_ns: int | None = None,
    ) -> str:
        created_ns = int(created_ns if created_ns is not None else time.time_ns())
        canonical_body = self.canonical_json(body)
        previous_hash = self._head()
        material = f"{previous_hash}|{event_type}|{prediction_id}|{created_ns}|{canonical_body}".encode("utf-8")
        event_hash = hashlib.sha256(material).hexdigest()
        try:
            with self.database:
                self.database.execute(
                    """
                    INSERT INTO events(
                        event_type, prediction_id, created_ns, body, prev_hash, event_hash,
                        namespace, executable, action
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'NONE')
                    """,
                    (
                        event_type,
                        prediction_id,
                        created_ns,
                        canonical_body,
                        previous_hash,
                        event_hash,
                        self.namespace,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            if "one_prediction_per_id" in message:
                raise LedgerError("duplicate_prediction") from exc
            if "one_outcome_per_id" in message:
                raise LedgerError("duplicate_outcome") from exc
            raise LedgerError("integrity_error") from exc
        return event_hash

    def prediction(self, body: dict[str, Any], created_ns: int | None = None) -> str:
        prediction_id = str(body.get("prediction_id") or f"pred-{uuid.uuid4().hex}")
        existing = self.database.execute(
            "SELECT 1 FROM events WHERE event_type='PREDICTION' AND prediction_id=?",
            (prediction_id,),
        ).fetchone()
        if existing is not None:
            raise LedgerError("duplicate_prediction")
        payload = dict(body)
        payload["prediction_id"] = prediction_id
        payload.setdefault("schema", "octopus.prediction.v1")
        payload.setdefault("namespace", self.namespace)
        payload["executable"] = 0
        payload["action"] = "NONE"
        self._insert("PREDICTION", prediction_id, payload, created_ns=created_ns)
        return prediction_id

    def outcome(self, prediction_id: str, body: dict[str, Any], created_ns: int | None = None) -> str:
        pred = self.database.execute(
            "SELECT created_ns FROM events WHERE event_type='PREDICTION' AND prediction_id=?",
            (prediction_id,),
        ).fetchone()
        if pred is None:
            raise LedgerError("outcome_without_prediction")
        existing = self.database.execute(
            "SELECT 1 FROM events WHERE event_type='OUTCOME' AND prediction_id=?",
            (prediction_id,),
        ).fetchone()
        if existing is not None:
            raise LedgerError("duplicate_outcome")
        created_ns = int(created_ns if created_ns is not None else time.time_ns())
        if created_ns <= int(pred[0]):
            raise LedgerError("outcome_not_after_prediction")
        payload = dict(body)
        payload["prediction_id"] = prediction_id
        payload.setdefault("schema", "octopus.prediction-outcome.v1")
        payload.setdefault("namespace", self.namespace)
        payload["executable"] = 0
        payload["action"] = "NONE"
        return self._insert("OUTCOME", prediction_id, payload, created_ns=created_ns)

    def verify(self) -> tuple[bool, int | None]:
        previous = GENESIS
        for seq, event_type, prediction_id, created_ns, body, prev_hash, event_hash in self.database.execute(
            "SELECT seq, event_type, prediction_id, created_ns, body, prev_hash, event_hash FROM events ORDER BY seq"
        ):
            if prev_hash != previous:
                return False, seq
            material = f"{previous}|{event_type}|{prediction_id}|{created_ns}|{body}".encode("utf-8")
            expect = hashlib.sha256(material).hexdigest()
            if expect != event_hash:
                return False, seq
            previous = event_hash
        return True, None

    def close(self) -> None:
        self.database.close()


class SyntheticLedger(PredictionLedger):
    """Chaos-only sqlite. Refuses runtime and live world_model paths."""

    def __init__(self, path: str | Path) -> None:
        if is_runtime_path(path):
            raise LedgerError("synthetic_database_cannot_open_runtime_path")
        super().__init__(path, namespace="chaos")
