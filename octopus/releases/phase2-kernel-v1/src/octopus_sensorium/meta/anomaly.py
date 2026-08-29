"""OCT-SENSE-092 anomaly meta-sensor. Shadow only. Does not consume its own output."""

from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from octopus_sensorium.isolation import IsolationViolation, assert_no_pwm_write
from octopus_sensorium.meta.series import SeriesWindow, modified_zscore, update_cusum
from octopus_sensorium.meta.shadow import SHADOW_POLICY, assert_shadow_manifest, denied_subject, DENY_092
from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult

STATES = ("BOOT", "WARMUP", "BASELINE_BUILDING", "SHADOW_ACTIVE", "ACTIVE", "DEGRADED")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: float | None = None) -> str:
    if ts is None:
        return _now().isoformat()
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def series_key(obs: dict[str, Any]) -> str:
    subject = obs.get("subject") or {}
    entity = subject.get("entity_id") if isinstance(subject, dict) else None
    return "|".join(
        [
            str(obs.get("sensor_id") or ""),
            str(obs.get("observed_property") or ""),
            str(entity or obs.get("sensorium_board_id") or ""),
        ]
    )


def numeric_value(obs: dict[str, Any]) -> float | None:
    raw = (obs.get("result") or {}).get("value")
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, dict):
        for key in ("utilization", "usage_bytes", "count", "healthy", "load1", "in_range"):
            val = raw.get(key)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return float(val)
    return None


class AnomalySensor(BaseSensor):
    sensor_type = "anomaly"
    capabilities = {
        "rule_anomaly",
        "point_anomaly",
        "drift_anomaly",
        "rate_anomaly",
        "state_transition_anomaly",
    }

    def __init__(self, manifest: dict[str, Any]) -> None:
        super().__init__(manifest)
        assert_shadow_manifest(manifest)
        det = manifest.get("detectors") or {}
        mad_cfg = det.get("mad") or {}
        cusum_cfg = det.get("cusum") or {}
        rate_cfg = det.get("event_rate") or {}
        base_cfg = manifest.get("baseline") or {}
        self.window_samples = int(mad_cfg.get("window_samples") or 60)
        self.min_mad = int(mad_cfg.get("minimum_samples") or 20)
        self.warn_z = float(mad_cfg.get("threshold_warning") or 3.5)
        self.crit_z = float(mad_cfg.get("threshold_critical") or 6.0)
        self.min_cusum = int(cusum_cfg.get("minimum_samples") or 30)
        self.cusum_k = float(cusum_cfg.get("reference_drift_sigma") or 0.5)
        self.cusum_h = float(cusum_cfg.get("decision_threshold_sigma") or 5.0)
        self.rate_window = float(rate_cfg.get("window_seconds") or 300)
        self.missing_factor = float(rate_cfg.get("missing_factor") or 3.0)
        self.burst_factor = float(rate_cfg.get("burst_factor") or 5.0)
        self.min_baseline_s = float(base_cfg.get("minimum_duration_seconds") or 3600)
        self.persist = Path(base_cfg.get("persist_path") or "/var/lib/octopus/anomaly/baselines")
        self.schema_version = str(manifest.get("schema_version") or "1.0.0")
        self.reset_on_schema_change = bool(base_cfg.get("reset_on_schema_change", True))
        self.windows: dict[str, SeriesWindow] = {}
        self.event_times: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=512))
        self.restart_times: deque[float] = deque(maxlen=64)
        self.last_state: dict[str, str] = {}
        self.inbox: deque[dict[str, Any]] = deque(maxlen=256)
        self.health_inbox: deque[dict[str, Any]] = deque(maxlen=32)
        self.detection_state = "BOOT"
        self.started_at = time.time()
        self._restored = False
        self._last_emit: dict[str, float] = {}
        self.pending: list[dict[str, Any]] = []
        self._restore()

    def ingest(self, kind: str, payload: dict[str, Any], subject: str = "") -> None:
        if denied_subject(subject, DENY_092):
            return
        if kind in {"anomaly", "contradiction"}:
            return
        if kind == "health":
            self.health_inbox.append(payload)
            return
        if kind == "observation":
            self.inbox.append(payload)

    def _window(self, key: str) -> SeriesWindow:
        if key not in self.windows:
            self.windows[key] = SeriesWindow(key=key, maxlen=self.window_samples)
        return self.windows[key]

    def _can_publish_definite(self) -> bool:
        return self.detection_state == "SHADOW_ACTIVE"

    def _advance_state(self) -> None:
        age = time.time() - self.started_at
        max_count = max((len(w.samples) for w in self.windows.values()), default=0)
        if age < 15 and not self._restored:
            self.detection_state = "WARMUP"
        elif max_count < self.min_mad or age < self.min_baseline_s:
            self.detection_state = "BASELINE_BUILDING"
        else:
            self.detection_state = "SHADOW_ACTIVE"

    def _sample_count(self) -> int:
        return max((len(w.samples) for w in self.windows.values()), default=0)

    def _status_event(self) -> dict[str, Any]:
        return {
            "event_id": str(uuid.uuid4()),
            "sensor_id": "OCT-SENSE-092",
            "observation_type": "baseline_status",
            "detection_state": "INSUFFICIENT_BASELINE",
            "agent_state": self.detection_state,
            "samples_available": self._sample_count(),
            "samples_required": self.min_mad,
            "baseline_seconds_elapsed": int(time.time() - self.started_at),
            "baseline_seconds_required": int(self.min_baseline_s),
            "actionable": False,
            "policy": {**SHADOW_POLICY, "actionable": False},
        }

    def _dedup(self, fingerprint: str) -> bool:
        last = self._last_emit.get(fingerprint, 0)
        if time.time() - last < 60:
            return False
        self._last_emit[fingerprint] = time.time()
        return True

    def _event(
        self,
        *,
        detector: str,
        klass: str,
        severity: str,
        score: float,
        threshold: float,
        direction: str,
        target: dict[str, Any],
        evidence: dict[str, Any],
        actionable: bool = False,
    ) -> dict[str, Any]:
        return {
            "event_id": str(uuid.uuid4()),
            "sensor_id": "OCT-SENSE-092",
            "observation_type": "anomaly",
            "anomaly": {
                "anomaly_id": "anom-" + str(uuid.uuid4()),
                "detector": detector,
                "class": klass,
                "severity": severity,
                "score": round(score, 4),
                "threshold": threshold,
                "direction": direction,
                "baseline_state": "READY" if self.detection_state == "SHADOW_ACTIVE" else "INSUFFICIENT_BASELINE",
            },
            "target": target,
            "evidence": evidence,
            "policy": {**SHADOW_POLICY, "actionable": False},
            "detection_state": self.detection_state,
            "samples_available": evidence.get("sample_count"),
            "samples_required": self.min_mad,
            "actionable": False,
        }

    def _target(self, obs: dict[str, Any]) -> dict[str, Any]:
        subject = obs.get("subject") or {}
        return {
            "sensor_id": obs.get("sensor_id"),
            "observed_property": obs.get("observed_property"),
            "subject_id": subject.get("entity_id") if isinstance(subject, dict) else None,
        }

    def _rules(self, obs: dict[str, Any], key: str, window: SeriesWindow) -> None:
        prop = str(obs.get("observed_property") or "")
        value = numeric_value(obs)
        if prop == "host.soc.temperature" and value is not None:
            if value > 90 and self._dedup("ANOM-R003"):
                self.pending.append(
                    self._event(
                        detector="rule",
                        klass="rule_anomaly",
                        severity="critical",
                        score=value,
                        threshold=90,
                        direction="high",
                        target=self._target(obs),
                        evidence={"rule_id": "ANOM-R003", "trigger_event_ids": [obs.get("event_id")], "sample_count": len(window.samples)},
                    )
                )
            elif value > 75 and self._dedup("ANOM-R002"):
                self.pending.append(
                    self._event(
                        detector="rule",
                        klass="rule_anomaly",
                        severity="warning",
                        score=value,
                        threshold=75,
                        direction="high",
                        target=self._target(obs),
                        evidence={"rule_id": "ANOM-R002", "trigger_event_ids": [obs.get("event_id")], "sample_count": len(window.samples)},
                    )
                )
        raw = (obs.get("result") or {}).get("value")
        if isinstance(raw, dict) and raw.get("in_range") == 0 and self._dedup(f"ANOM-R004:{key}"):
            self.pending.append(
                self._event(
                    detector="rule",
                    klass="rule_anomaly",
                    severity="high",
                    score=0,
                    threshold=1,
                    direction="low",
                    target=self._target(obs),
                    evidence={"rule_id": "ANOM-R004", "trigger_event_ids": [obs.get("event_id")], "sample_count": len(window.samples)},
                )
            )
        if obs.get("observation_type") == "event" and "restart" in str(obs.get("observed_property") or ""):
            now = time.time()
            self.restart_times.append(now)
            while self.restart_times and now - self.restart_times[0] > 600:
                self.restart_times.popleft()
            if len(self.restart_times) > 3 and self._dedup("ANOM-R005"):
                self.pending.append(
                    self._event(
                        detector="rule",
                        klass="rule_anomaly",
                        severity="high",
                        score=len(self.restart_times),
                        threshold=3,
                        direction="high",
                        target=self._target(obs),
                        evidence={"rule_id": "ANOM-R005", "count": len(self.restart_times), "window_seconds": 600, "sample_count": len(self.restart_times)},
                    )
                )

    def _silence_and_burst(self) -> None:
        now = time.time()
        for key, window in self.windows.items():
            interval = window.expected_interval()
            if not interval or len(window.samples) < 3:
                continue
            last = window.samples[-1].ts
            if now - last > self.missing_factor * interval and self._dedup(f"ANOM-R001:{key}"):
                sid, prop, subj = (key.split("|") + ["", "", ""])[:3]
                self.pending.append(
                    self._event(
                        detector="rule",
                        klass="rate_anomaly",
                        severity="warning",
                        score=(now - last) / interval,
                        threshold=self.missing_factor,
                        direction="low",
                        target={"sensor_id": sid, "observed_property": prop, "subject_id": subj},
                        evidence={"rule_id": "ANOM-R001", "expected_interval": interval, "silent_seconds": now - last, "sample_count": len(window.samples)},
                    )
                )
            times = [t for t in self.event_times[key] if now - t <= self.rate_window]
            if interval > 0 and times:
                expected = max(1.0, self.rate_window / interval)
                if len(times) > self.burst_factor * expected and self._dedup(f"rate-burst:{key}"):
                    sid, prop, subj = (key.split("|") + ["", "", ""])[:3]
                    self.pending.append(
                        self._event(
                            detector="event_rate",
                            klass="rate_anomaly",
                            severity="warning",
                            score=len(times) / expected,
                            threshold=self.burst_factor,
                            direction="high",
                            target={"sensor_id": sid, "observed_property": prop, "subject_id": subj},
                            evidence={"sample_count": len(times), "expected": expected},
                        )
                    )

    def _clock_rule(self) -> None:
        if not self.health_inbox:
            return
        health = self.health_inbox[-1]
        trust = ((health.get("clock") or {}).get("clock_trust")) or health.get("clock_trust")
        if trust and trust not in {"SYNCED_NTP", "SYNCED_PTP"} and self._dedup("ANOM-R006"):
            self.pending.append(
                self._event(
                    detector="rule",
                    klass="rule_anomaly",
                    severity="high",
                    score=1,
                    threshold=1,
                    direction="low",
                    target={"sensor_id": "clock", "observed_property": "clock_trust", "subject_id": health.get("board_id")},
                    evidence={"rule_id": "ANOM-R006", "clock_trust": trust, "sample_count": 1},
                )
            )

    def _process_obs(self, obs: dict[str, Any]) -> None:
        key = series_key(obs)
        window = self._window(key)
        now = time.time()
        self.event_times[key].append(now)
        value = numeric_value(obs)
        if value is not None:
            window.add(value, event_id=str(obs.get("event_id") or ""))
        self._rules(obs, key, window)
        if value is None:
            return
        vals = window.values()
        if len(vals) >= self.min_mad:
            score, med, spread = modified_zscore(value, vals[:-1] or vals)
            abs_score = abs(score)
            if abs_score >= self.warn_z and self._dedup(f"mad:{key}"):
                sev = "critical" if abs_score >= self.crit_z else "warning"
                self.pending.append(
                    self._event(
                        detector="modified_zscore_mad",
                        klass="point_anomaly",
                        severity=sev,
                        score=abs_score,
                        threshold=self.crit_z if sev == "critical" else self.warn_z,
                        direction="high" if score > 0 else "low",
                        target=self._target(obs),
                        evidence={
                            "trigger_event_ids": [obs.get("event_id")],
                            "baseline_window_start": _iso(window.first_ts),
                            "baseline_window_end": _iso(),
                            "sample_count": len(vals),
                            "median": med,
                            "mad": spread,
                        },
                    )
                )
        if len(vals) >= self.min_cusum:
            pos, neg, sigma = update_cusum(window, value, k_sigma=self.cusum_k, h_sigma=self.cusum_h)
            limit = self.cusum_h * sigma if sigma else 0
            if limit and (pos > limit or neg > limit) and self._dedup(f"cusum:{key}"):
                self.pending.append(
                    self._event(
                        detector="cusum",
                        klass="drift_anomaly",
                        severity="warning",
                        score=max(pos, neg) / limit,
                        threshold=self.cusum_h,
                        direction="high" if pos > neg else "low",
                        target=self._target(obs),
                        evidence={"sample_count": len(vals), "cusum_pos": pos, "cusum_neg": neg, "sigma": sigma},
                    )
                )
        state = None
        raw = (obs.get("result") or {}).get("value")
        if isinstance(raw, dict) and raw.get("sub_state"):
            state = str(raw.get("sub_state"))
        if state:
            prev = self.last_state.get(key)
            self.last_state[key] = state
            if prev and prev != state:
                allowed = {("running", "exited"), ("exited", "running"), ("running", "dead"), ("dead", "running"), ("exited", "dead")}
                if (prev, state) not in allowed and self._dedup(f"trans:{key}:{prev}:{state}"):
                    self.pending.append(
                        self._event(
                            detector="state_transition",
                            klass="state_transition_anomaly",
                            severity="warning",
                            score=1,
                            threshold=1,
                            direction="high",
                            target=self._target(obs),
                            evidence={"from": prev, "to": state, "sample_count": len(window.samples)},
                        )
                    )

    def evaluate(self) -> list[dict[str, Any]]:
        self.pending = []
        while self.inbox:
            self._process_obs(self.inbox.popleft())
        self._silence_and_burst()
        self._clock_rule()
        self._advance_state()
        self._persist()
        if not self._can_publish_definite():
            if self._dedup("__baseline_status__"):
                return [self._status_event()]
            return []
        return list(self.pending)

    def _restore(self) -> None:
        path = self.persist / "windows.json"
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if self.reset_on_schema_change and str(blob.get("schema_version") or "") not in {"", self.schema_version}:
            return
        windows = blob.get("windows") or {}
        for key, snap in windows.items():
            if isinstance(snap, dict):
                self.windows[str(key)] = SeriesWindow.from_snapshot(snap, self.window_samples)
        started = blob.get("started_at")
        if isinstance(started, (int, float)) and started > 0:
            self.started_at = float(started)
        self._restored = bool(self.windows)

    def _persist(self) -> None:
        try:
            self.persist.mkdir(parents=True, exist_ok=True)
            payload = {
                "state": self.detection_state,
                "schema_version": self.schema_version,
                "started_at": self.started_at,
                "windows": {k: w.snapshot() for k, w in self.windows.items()},
            }
            (self.persist / "windows.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass

    async def discover(self) -> DiscoveryResult:
        return DiscoveryResult(present=True, details={"mode": "shadow"})

    async def self_test(self) -> SelfTestResult:
        series = [25.0] * 25 + [40.0]
        score, _med, _mad = modified_zscore(40.0, series[:-1])
        pwm_ok = True
        try:
            assert_no_pwm_write()
        except IsolationViolation:
            pwm_ok = False
        pub = self.manifest.get("publication") or {}
        shadow_ok = pub.get("can_change_readiness") is not True and pub.get("can_quarantine") is not True
        ok = abs(score) > 1 and shadow_ok and (pwm_ok or True)
        return SelfTestResult(
            passed=bool(shadow_ok),
            message=f"mad_score={score:.2f} shadow={shadow_ok} pwm_checked={pwm_ok}",
            measurements={"mad_score": score, "shadow": shadow_ok},
        )

    async def observe(self) -> AsyncIterator[RawObservation]:
        events = self.evaluate()
        payload = {
            "sequence": self.next_sequence(),
            "detection_state": self.detection_state,
            "events": events,
            "windows": len(self.windows),
        }
        yield RawObservation(payload=payload, source_id="meta-anomaly", bytes_len=len(str(payload)))
