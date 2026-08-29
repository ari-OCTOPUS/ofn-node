"""Optional unwired FastAPI observe app. Not a systemd unit. Do not bind on the Pi."""

from __future__ import annotations

from typing import Any

from octopus_shadow.observe import ObserveError, parse_synthetic_observation


def create_app() -> Any:
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, ConfigDict
    except ImportError as exc:  # pragma: no cover - optional on Sensorium
        raise RuntimeError("fastapi_not_installed") from exc

    class SyntheticBody(BaseModel):
        model_config = ConfigDict(extra="forbid")
        synthetic: bool
        scenario: str
        index: int = 0
        energy_ratio: float = 0.0
        error_rate: float = 0.0
        skill: float = 0.0
        source: str | None = "shadow-chaos"
        namespace: str | None = "chaos"

    app = FastAPI(title="OCTOPUS WAVE0 observe (unwired)", docs_url=None, redoc_url=None)

    @app.post("/v1/observe/synthetic")
    def observe_synthetic(body: SyntheticBody) -> dict[str, Any]:
        try:
            return parse_synthetic_observation(body.model_dump())
        except ObserveError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return app
