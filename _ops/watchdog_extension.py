#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watchdog_extension.py — CH-17: Watchdog alerts extractor extension.

این ماژول watchdog را به unified_bus وصل می‌کند (NOTE subtype=WATCHDOG_ALERT).
health checks: port alive, state freshness, STOP flags, governor-alerts.md.
additive — هیچ کد موجودی را نمی‌شکند.
"""
from __future__ import annotations

import json
import logging
import re
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent              # _ops
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402

logger = logging.getLogger(__name__)

# مسیرهای کلیدی
ORGANISM_PORT = 8771
STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"
GOVERNOR_ALERTS = opslib.OPS / "governor" / "governor-alerts.md"
STOP_FLAGS = [
    opslib.OPS.parent / "STOP",
    opslib.OPS / "STOP-ORGANISM",
    opslib.OPS / "STOP-METABOLIC",
]

# آستانه‌های freshness (ثانیه)
STATE_STALE_SEC = 3600        # 60 دقیقه
ALERT_DEDUP_SEC = 300           # 5 دقیقه dedup


class WatchdogHealthCheck:
    """یک health check تکی (name, check_fn, severity)."""

    def __init__(self, name: str, check_fn, severity: str = "info"):
        self.name = name
        self.check_fn = check_fn
        self.severity = severity  # info | warning | critical


class WatchdogMonitor:
    """مانیتور watchdog با unified_bus integration.

    وظایف:
      1. health checks دوره‌ای (port, state, STOP flags, governor alerts)
      2. publish alert از نوع NOTE+subtype=WATCHDOG_ALERT به unified_bus
      3. dedup — یک alert در ۵ دقیقه فقط یک‌بار publish می‌شود
    """

    def __init__(self, bus=None, state_file: Path = STATE_FILE,
                 port: int = ORGANISM_PORT, stop_flags: list[Path] | None = None,
                 alerts_md: Path = GOVERNOR_ALERTS):
        self._bus = bus
        self._state_file = Path(state_file)
        self._port = port
        self._stop_flags = [Path(p) for p in (stop_flags or STOP_FLAGS)]
        self._alerts_md = Path(alerts_md)
        self._last_alert_ts: dict[str, float] = {}   # dedup cache
        self._checks = self._build_checks()

    def _build_checks(self) -> list[WatchdogHealthCheck]:
        """لیستِ health checks پیش‌فرض."""
        return [
            WatchdogHealthCheck("port_alive", self._check_port, "critical"),
            WatchdogHealthCheck("state_freshness", self._check_state_freshness, "warning"),
            WatchdogHealthCheck("stop_flags", self._check_stop_flags, "critical"),
            WatchdogHealthCheck("governor_alerts", self._check_governor_alerts, "warning"),
        ]

    # ─── individual checks ───────────────────────────────────────────────────

    def _check_port(self) -> dict[str, Any]:
        """چکِ زنده‌بودنِ پورت organism."""
        try:
            with socket.create_connection(("127.0.0.1", self._port), timeout=1.5):
                return {"alive": True, "port": self._port}
        except OSError as exc:
            return {"alive": False, "port": self._port, "error": str(exc)}

    def _check_state_freshness(self) -> dict[str, Any]:
        """چکِ کهنگیِ ORGANISM-STATE.json."""
        if not self._state_file.exists():
            return {"exists": False, "stale": True, "age_sec": None}
        try:
            mtime = self._state_file.stat().st_mtime
            age = time.time() - mtime
            return {"exists": True, "stale": age > STATE_STALE_SEC, "age_sec": round(age, 1)}
        except OSError as exc:
            return {"exists": False, "stale": True, "error": str(exc)}

    def _check_stop_flags(self) -> dict[str, Any]:
        """چکِ پرچم‌های STOP."""
        found = []
        for p in self._stop_flags:
            if p.exists():
                found.append(str(p.name))
        return {"stopped": bool(found), "flags": found}

    def _check_governor_alerts(self) -> dict[str, Any]:
        """خواندنِ آخرین alertهای فعال از governor-alerts.md."""
        try:
            if not self._alerts_md.exists():
                return {"exists": False, "recent": []}
            text = self._alerts_md.read_text("utf-8")
            alerts = self._parse_alerts_md(text)
            # فقط alertهای ۲۴ ساعت اخیر
            cutoff = time.time() - 24 * 3600
            recent = [a for a in alerts if a.get("ts", 0) > cutoff]
            return {"exists": True, "recent": recent[:20], "total": len(alerts)}
        except Exception as exc:  # noqa: BLE001
            return {"exists": True, "error": str(exc), "recent": []}

    @staticmethod
    def _parse_alerts_md(text: str) -> list[dict]:
        """Parse governor-alerts.md → list of alert dicts."""
        alerts = []
        # pattern: ## 2026-07-12T01:38:33 (metabolism)
        header_pat = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+\(([^)]+)\)")
        current_ts = None
        current_source = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = header_pat.match(line)
            if m:
                try:
                    dt = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
                    current_ts = dt.replace(tzinfo=timezone.utc).timestamp()
                except ValueError:
                    current_ts = None
                current_source = m.group(2).strip()
                continue
            if line.startswith("- ⚠️") or line.startswith("- ⚠"):
                msg = line.lstrip("- ⚠️").lstrip("- ⚠").strip()
                if msg:
                    alerts.append({
                        "ts": current_ts or 0,
                        "source": current_source or "unknown",
                        "message": msg,
                    })
        return alerts

    # ─── run & publish ───────────────────────────────────────────────────────

    def run_checks(self) -> list[dict]:
        """اجرا همهٔ health checks و برگرداندنِ alertهای فعال."""
        active = []
        for hc in self._checks:
            try:
                result = hc.check_fn()
                result["check_name"] = hc.name
                result["severity"] = hc.severity
                if self._is_alert(result):
                    active.append(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception("check %s failed", hc.name)
                active.append({
                    "check_name": hc.name,
                    "severity": "critical",
                    "error": str(exc),
                    "check_failed": True
                })
        return active

    def _is_alert(self, result: dict) -> bool:
        """آیا نتیجهٔ یک check باید alert شود؟"""
        name = result.get("check_name")
        if name == "port_alive":
            return not result.get("alive", True)
        if name == "state_freshness":
            return result.get("stale", False)
        if name == "stop_flags":
            return result.get("stopped", False)
        if name == "governor_alerts":
            return bool(result.get("recent"))
        return False

    def publish_alerts(self, alerts: list[dict] | None = None) -> list[dict]:
        """alertهای فعال را به unified_bus publish کن (dedup)."""
        if alerts is None:
            alerts = self.run_checks()
        published = []
        now = time.time()
        for alert in alerts:
            key = alert.get("check_name", "unknown")
            last = self._last_alert_ts.get(key, 0)
            if now - last < ALERT_DEDUP_SEC:
                continue  # dedup
            self._last_alert_ts[key] = now
            payload = {
                "check_name": key,
                "severity": alert.get("severity", "info"),
                "details": alert,
                "ts": now,
            }
            if self._bus is not None:
                try:
                    bus_payload = {"subtype": "WATCHDOG_ALERT", **payload}
                    entry = self._bus.publish("NOTE", bus_payload, actor="watchdog", is_human=False)
                    published.append({"published": True, "entry": entry, "payload": bus_payload})
                except Exception as exc:  # noqa: BLE001
                    logger.error("publish failed for %s: %s", key, exc)
                    published.append({"published": False, "error": str(exc), "payload": payload})
            else:
                # fallback: events.jsonl
                published.append({"published": False, "fallback": "no-bus", "payload": payload})
                try:
                    import events
                    events.emit("watchdog.alert", "watchdog", status="alert",
                                summary=f"{key}: {alert.get('details', alert)}",
                                next_action="check organism health")
                except Exception:  # noqa: BLE001
                    pass
        return published

    def tick(self) -> dict:
        """یک tick کامل: run checks + publish. خروجی = summary."""
        alerts = self.run_checks()
        published = self.publish_alerts(alerts)
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "alerts_found": len(alerts),
            "alerts_published": len([p for p in published if p.get("published")]),
            "healthy": len(alerts) == 0,
            "checks": [a["check_name"] for a in alerts],
        }


def default_monitor() -> WatchdogMonitor:
    """ساختن یک WatchdogMonitor با bus پیش‌فرض (اگر unified_bus import شود)."""
    bus = None
    try:
        import unified_bus
        bus = unified_bus.UnifiedBus()
    except Exception:  # noqa: BLE001
        pass
    return WatchdogMonitor(bus=bus)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    mon = default_monitor()
    summary = mon.tick()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
