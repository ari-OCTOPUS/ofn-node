"""App configuration from environment. The kernel never sees this module."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from ..kernel.domain import Mode


def _load_dotenv(path: str = ".env") -> dict[str, str]:
    """Read a local, gitignored `.env` into a dict (empty if absent). No dependency,
    no global mutation. Secrets stay in `.env` (never committed); values are never logged."""
    out: dict[str, str] = {}
    p = Path(path)
    if p.exists():
        # utf-8-sig strips a leading BOM if present (a no-op otherwise). Windows
        # editors / PowerShell write a UTF-8 BOM by default; without this the first
        # key parses as "﻿FUGU_API_KEY" and the key is silently dropped.
        for raw in p.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if key:
                out[key] = value.strip().strip('"').strip("'")
    return out


@dataclass(frozen=True)
class AppConfig:
    global_cap_cents: int = 3000
    mode: Mode = Mode.SHADOW
    llm_mode: str = "mock"                      # mock | cassette | live
    cassette_path: str = "cassettes/demo_epoch.jsonl"
    db_path: str = "outputs/nbb.db"
    kill_switch_file: str = "outputs/KILL"
    sigma_window_epochs: int = 5
    fugu_api_key: str | None = None   # loaded from env/.env; used by the Phase-3 LLM adapter
    fugu_api_host: str = "https://api.sakana.ai/v1"
    fugu_api_path: str = "/chat/completions"
    fugu_model: str = "fugu"          # standard tier, not ultra (spec §11)
    organs: tuple[tuple[str, str], ...] = field(
        default_factory=lambda: (
            ("accounting", "Accounting"),
            ("painting-leads", "Lead-Painting"),
            ("ziman", "Ziman Gallery"),
        )
    )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AppConfig":
        if env is None:
            merged = _load_dotenv()          # gitignored .env fills gaps...
            merged.update(os.environ)        # ...but a real environment variable always wins
            env = merged
        else:
            env = dict(env)
        mode_raw = env.get("NBB_MODE", "shadow").strip().lower()
        if mode_raw not in (m.value for m in Mode):
            # Fail closed: an unknown mode must not silently become live.
            mode_raw = Mode.SHADOW.value
        # SPEC §6: `live` is unreachable until the Phase-6 shadow-to-live gate. Fail
        # closed to shadow unless the operator sets NBB_ALLOW_LIVE=1 explicitly
        # (INV-12 / CLAUDE.md rule 4: unknown/ungated state -> shadow, never guess).
        if mode_raw == Mode.LIVE.value and env.get("NBB_ALLOW_LIVE", "").strip() != "1":
            mode_raw = Mode.SHADOW.value
        return cls(
            global_cap_cents=int(env.get("NBB_GLOBAL_CAP_CENTS", "3000")),
            mode=Mode(mode_raw),
            llm_mode=env.get("NBB_LLM_MODE", "mock").strip().lower(),
            cassette_path=env.get("NBB_CASSETTE_PATH", "cassettes/demo_epoch.jsonl"),
            db_path=env.get("NBB_DB_PATH", "outputs/nbb.db"),
            kill_switch_file=env.get("NBB_KILL_SWITCH_FILE", "outputs/KILL"),
            fugu_api_key=(env.get("FUGU_API_KEY") or None),
            fugu_api_host=env.get("NBB_FUGU_HOST", "https://api.sakana.ai/v1"),
            fugu_api_path=env.get("NBB_FUGU_PATH", "/chat/completions"),
            fugu_model=env.get("NBB_FUGU_MODEL", "fugu"),
        )
