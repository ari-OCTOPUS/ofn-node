from __future__ import annotations

import json
from typing import Any

from octopus_sensorium.natsbus import publish_json


async def publish_payload(nc, subject: str, payload: dict[str, Any]) -> None:  # noqa: ANN001
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    await publish_json(nc, subject, blob)
