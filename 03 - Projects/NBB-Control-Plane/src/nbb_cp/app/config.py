"""App configuration from environment. The kernel never sees this module."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping

from ..kernel.domain import Mode


@dataclass(frozen=True)
class AppConfig:
    global_cap_cents: int = 3000
    mode: Mode = Mode.SHADOW
    llm_mode: str = "mock"                      # mock | cassette | live
    cassette_path: str = "cassettes/demo_epoch.jsonl"
    db_path: str = "outputs/nbb.db"
    kill_switch_file: str = "outputs/KILL"
    sigma_window_epochs: int = 5
    organs: tuple[tuple[str, str], ...] = field(
        default_factory=lambda: (
            ("accounting", "Accounting"),
            ("painting-leads", "Lead-Painting"),
            ("ziman", "Ziman Gallery"),
        )
    )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AppConfig":
        env = dict(os.environ if env is None else env)
        mode_raw = env.get("NBB_MODE", "shadow").strip().lower()
        if mode_raw not in (m.value for m in Mode):
            # Fail closed: an unknown mode must not silently become live.
            mode_raw = Mode.SHADOW.value
        return cls(
            global_cap_cents=int(env.get("NBB_GLOBAL_CAP_CENTS", "3000")),
            mode=Mode(mode_raw),
            llm_mode=env.get("NBB_LLM_MODE", "mock").strip().lower(),
            cassette_path=env.get("NBB_CASSETTE_PATH", "cassettes/demo_epoch.jsonl"),
            db_path=env.get("NBB_DB_PATH", "outputs/nbb.db"),
            kill_switch_file=env.get("NBB_KILL_SWITCH_FILE", "outputs/KILL"),
        )
