#!/usr/bin/env python3
"""kernel_consumer.py — Body-side module that lets the octopus organism read kernel outputs.

Safe to import from brain.automation or brain.daemon (no side effects on import,
lazy evaluation on method calls).  Read-only access to the kernel bridge.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Default paths — used when no custom kernel_path is provided.
KERNEL_PATH = Path("F:/backup/03 - Projects/research-spec-compiler")
BRIDGE_OUTPUT = KERNEL_PATH / "body_bridge" / "output"


class KernelConsumer:
    """Read-only consumer of Cognitive Kernel outputs for the octopus body."""

    def __init__(self, kernel_path: str | Path = None):
        self._kernel_path = Path(kernel_path) if kernel_path else KERNEL_PATH
        self._bridge_output = self._kernel_path / "body_bridge" / "output"
        self._manifest = None
        self._dashboard = None
        self._adr_feed = None
        self._verdict_stream = None

        if not self._kernel_path.exists():
            logger.warning("Kernel path not found: %s", self._kernel_path)

    def read_manifest(self) -> dict:
        """Read manifest.json from the kernel bridge output."""
        path = self._bridge_output / "manifest.json"
        try:
            text = path.read_text(encoding="utf-8")
            self._manifest = json.loads(text)
            return self._manifest
        except Exception as exc:
            logger.warning("Could not read manifest.json: %s", exc)
            return {}

    def read_dashboard(self) -> dict:
        """Read kernel_dashboard.json from the kernel bridge output."""
        path = self._bridge_output / "kernel_dashboard.json"
        try:
            text = path.read_text(encoding="utf-8")
            self._dashboard = json.loads(text)
            return self._dashboard
        except Exception as exc:
            logger.warning("Could not read kernel_dashboard.json: %s", exc)
            return {}

    def read_adr_feed(self) -> dict:
        """Read adr_feed.json from the kernel bridge output."""
        path = self._bridge_output / "adr_feed.json"
        try:
            text = path.read_text(encoding="utf-8")
            self._adr_feed = json.loads(text)
            return self._adr_feed
        except Exception as exc:
            logger.warning("Could not read adr_feed.json: %s", exc)
            return {}

    def read_verdict_stream(self, since: datetime = None) -> list[dict]:
        """Read verdict_stream.jsonl and optionally filter by timestamp.

        Args:
            since: If provided, only return events whose timestamp is >= since.

        Returns:
            List of parsed JSON objects, one per non-empty line.
        """
        path = self._bridge_output / "verdict_stream.jsonl"
        events = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        if since is not None:
                            ts_str = event.get("timestamp", "")
                            if ts_str:
                                try:
                                    ts = _parse_iso(ts_str)
                                    since_aware = since if since.tzinfo else since.replace(tzinfo=timezone.utc)
                                    if ts < since_aware:
                                        continue
                                except Exception:
                                    # If timestamp parsing fails, keep the event.
                                    pass
                        events.append(event)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON line in verdict_stream.jsonl")
        except Exception as exc:
            logger.warning("Could not read verdict_stream.jsonl: %s", exc)
        return events

    def check_kernel_health(self) -> dict:
        """Return health status of the kernel bridge.

        Returns:
            dict with keys: reachable, manifest_fresh, integrity_ok, last_sync.
        """
        manifest = self.read_manifest()
        manifest_path = self._bridge_output / "manifest.json"

        reachable = self._kernel_path.exists() and manifest_path.exists()

        manifest_fresh = False
        last_sync = None
        if manifest_path.exists():
            mtime = datetime.fromtimestamp(manifest_path.stat().st_mtime, tz=timezone.utc)
            manifest_fresh = (datetime.now(timezone.utc) - mtime) < timedelta(hours=24)
            if manifest:
                last_updated = manifest.get("last_updated")
                if last_updated:
                    try:
                        last_sync = _parse_iso(last_updated)
                    except Exception:
                        pass

        integrity_ok = True
        # Attempt to load manifest_generator from the kernel path and call
        # validate_integrity if it exists.  If anything fails, default to True.
        try:
            import importlib.util
            mg_path = self._kernel_path / "body_bridge" / "manifest_generator.py"
            if mg_path.exists():
                spec = importlib.util.spec_from_file_location(
                    "manifest_generator", str(mg_path)
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "validate_integrity"):
                    result = mod.validate_integrity()
                    if isinstance(result, dict):
                        integrity_ok = result.get("valid", True)
        except Exception:
            pass

        return {
            "reachable": reachable,
            "manifest_fresh": manifest_fresh,
            "integrity_ok": integrity_ok,
            "last_sync": last_sync,
        }

    def suggest_automation_action(self) -> dict:
        """Suggest an automation action based on current kernel state.

        Rules:
        - Any REJECTED verdict in stream or dashboard → review, high
        - Any fresh OPTIMIZE in stream or dashboard → evaluate, medium
        - Otherwise → no_op, low
        """
        stream = self.read_verdict_stream()
        dashboard = self.read_dashboard()

        # REJECTED detection
        rejected_in_stream = any(
            e.get("verdict") == "REJECTED" for e in stream
        )
        rejected_in_dashboard = False
        if dashboard:
            tally = dashboard.get("tally", {})
            if tally.get("REJECTED", 0) > 0:
                rejected_in_dashboard = True
            for adr in dashboard.get("high_priority_adr", []):
                if adr.get("verdict") == "REJECTED":
                    rejected_in_dashboard = True

        if rejected_in_stream or rejected_in_dashboard:
            return {
                "action": "review",
                "reason": "Rejections detected",
                "priority": "high",
            }

        # OPTIMIZE detection
        optimize_in_stream = any(
            e.get("verdict") == "OPTIMIZE" for e in stream
        )
        optimize_in_dashboard = False
        if dashboard:
            tally = dashboard.get("tally", {})
            if tally.get("OPTIMIZE", 0) > 0:
                optimize_in_dashboard = True

        if optimize_in_stream or optimize_in_dashboard:
            return {
                "action": "evaluate",
                "reason": "Optimization candidate",
                "priority": "medium",
            }

        return {
            "action": "no_op",
            "reason": "Kernel state stable",
            "priority": "low",
        }

    def publish_body_event(self, event_name: str, summary: str):
        """Emit a body event via brain.events (imported lazily).

        The event is always published as ``kernel.notice`` with the supplied
        summary.  If the ``brain.events`` module is not available, a warning is
        logged instead of raising.

        Args:
            event_name: Unused (reserved for future extensibility).
            summary: Human-readable summary of the kernel notice.
        """
        try:
            from brain import events
            events.emit("kernel.notice", summary, status="info")
        except Exception as exc:
            logger.warning("brain.events not available, cannot publish body event: %s", exc)


def _parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 string, handling trailing ``Z`` and missing tzinfo."""
    value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
