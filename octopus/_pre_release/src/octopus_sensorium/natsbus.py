"""NATS connection for the Sensorium runtime. Stream create/delete is not a runtime API."""

from __future__ import annotations

import asyncio
import os

import nats
from nats.js.api import DiscardPolicy, RetentionPolicy, StorageType, StreamConfig

STREAMS = (
    StreamConfig(
        name="SENSORIUM",
        subjects=["octopus.sensorium.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=64 * 1024 * 1024,
        max_age=7 * 24 * 3600,
    ),
    StreamConfig(
        name="OBSERVATION",
        subjects=["octopus.sensor.observation.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=512 * 1024 * 1024,
        max_age=2 * 24 * 3600,
    ),
    StreamConfig(
        name="FEATURE",
        subjects=["octopus.sensor.feature.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=256 * 1024 * 1024,
        max_age=2 * 24 * 3600,
    ),
    StreamConfig(
        name="SENSOR_HEALTH",
        subjects=["octopus.sensor.health.>", "octopus.sensor.anomaly.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=64 * 1024 * 1024,
        max_age=7 * 24 * 3600,
    ),
    StreamConfig(
        name="WORLD",
        subjects=["octopus.world.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=256 * 1024 * 1024,
        max_age=7 * 24 * 3600,
    ),
    StreamConfig(
        name="AUDIT",
        subjects=["octopus.audit.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=128 * 1024 * 1024,
        max_age=30 * 24 * 3600,
    ),
    StreamConfig(
        name="COMMAND",
        subjects=["octopus.command.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=32 * 1024 * 1024,
        max_age=2 * 24 * 3600,
    ),
    StreamConfig(
        name="LEG",
        subjects=["octopus.leg.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        discard=DiscardPolicy.OLD,
        max_bytes=64 * 1024 * 1024,
        max_age=2 * 24 * 3600,
    ),
)


def load_nats_url() -> tuple[str, str, str]:
    env_path = os.environ.get("OCTOPUS_NATS_ENV", "/etc/octopus/secrets/nats-sensorium.env")
    user = os.environ.get("NATS_USER", "")
    password = os.environ.get("NATS_PASSWORD", "")
    url = os.environ.get("NATS_URL", "nats://192.168.0.182:4222")
    try:
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    if key == "NATS_USER":
                        user = value
                    elif key == "NATS_PASSWORD":
                        password = value
                    elif key == "NATS_URL":
                        url = value
    except OSError:
        pass
    return url, user, password


async def connect(*, disconnected_cb=None, reconnected_cb=None) -> nats.NATS:
    url, user, password = load_nats_url()
    return await nats.connect(
        url,
        user=user,
        password=password,
        name="sensorium-agent",
        allow_reconnect=True,
        max_reconnect_attempts=-1,
        connect_timeout=3,
        reconnect_time_wait=1,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
    )


async def list_streams(nc: nats.NATS) -> list[str]:
    js = nc.jetstream()
    names: list[str] = []
    for cfg in STREAMS:
        try:
            info = await asyncio.wait_for(js.stream_info(cfg.name), timeout=2)
            names.append(info.config.name)
        except Exception:
            continue
    return names


async def ensure_streams(nc: nats.NATS) -> list[str]:
    """Forbidden on the live agent. Provisioning lives in tools/provision_streams.py only."""
    raise RuntimeError(
        "allow_nats_provisioning=false: runtime must not create or update JetStream streams"
    )


async def publish_json(nc: nats.NATS, subject: str, payload: bytes) -> None:
    await nc.publish(subject, payload)
    await nc.flush(timeout=2)
