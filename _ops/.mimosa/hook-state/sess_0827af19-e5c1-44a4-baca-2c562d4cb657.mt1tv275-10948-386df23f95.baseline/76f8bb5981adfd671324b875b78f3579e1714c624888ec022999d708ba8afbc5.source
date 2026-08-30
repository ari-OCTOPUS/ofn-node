"""policy.py — بارگذارِ fail-closedِ policy.yaml (ADR-039 C1).

stdlib-only — هیچ Pydantic. PyYAML 6.x موجود است (هم‌الگو با budget/opslib.load_budgets).

سیاستِ fail-closed (ADR-039 §7):
  - فایلِ غایب یا غیرقابل‌parse  ⇒ RuntimeError (FREEZE / STOP).
  - کلیدِ الزامیِ غایب            ⇒ RuntimeError.
  - sandbox_profile != no_network ⇒ RuntimeError.
  - max_authority != propose      ⇒ RuntimeError.
  - ceiling مطلق (defense-in-depth) فارغ از محتوای فایل enforcing می‌شود.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_POLICY_PATH = HERE / "policy.yaml"

# ceilingهای مطلق: فایل policy.yaml نمی‌تواند از این بالاتر برود، حتی اگر بنویسد.
_HARD_MAX_RUNS = 1000
_HARD_MAX_WALL_S = 14400      # 4 ساعت
_HARD_MAX_COST = 10.0


@dataclass(frozen=True)
class Caps:
    max_runs: int
    max_wall_seconds: int
    max_cost_aud: float


@dataclass(frozen=True)
class BeliefUpdate:
    clip_log_odds: float
    lambda_disagreement: float


@dataclass(frozen=True)
class Independence:
    min_clusters: int
    clustering_keys: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PolicyConfig:
    schema_version: int
    default_off: bool
    env_flag: str
    sandbox_profile: str        # همیشه "no_network"
    max_authority: str          # همیشه "propose"
    caps: Caps
    belief_update: BeliefUpdate
    independence: Independence
    authorized_producers: List[str] = field(default_factory=list)
    maturity_ladder: Dict[str, Dict[str, object]] = field(default_factory=dict)


def _require(data: dict, key: str, ctx: str):
    """کلیدِ الزامی — غایب ⇒ RuntimeError (fail-closed)."""
    if not isinstance(data, dict) or key not in data:
        raise RuntimeError(
            f"policy.yaml: missing required key '{key}' in {ctx} — FREEZE (ADR-039 §7)"
        )
    return data[key]


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> PolicyConfig:
    """بارگذاری + اعتبارسنجیِ fail-closed. هر نقص ⇒ RuntimeError."""
    if not Path(path).exists():
        raise RuntimeError(f"policy.yaml not found at {path} — FREEZE (ADR-039 §7)")
    try:
        data = yaml.safe_load(Path(path).read_text("utf-8"))
    except yaml.YAMLError as exc:
        raise RuntimeError(f"policy.yaml unparseable: {exc} — FREEZE") from exc
    if not isinstance(data, dict):
        raise RuntimeError("policy.yaml root must be a mapping — FREEZE")

    # --- سخت‌مرزها (non-negotiable) ---
    if int(_require(data, "schema_version", "root")) != 1:
        raise RuntimeError("policy.yaml: schema_version must be 1 — FREEZE")

    sandbox = _require(data, "sandbox_profile", "root")
    if sandbox != "no_network":
        raise RuntimeError(
            "policy.yaml: sandbox_profile must be 'no_network' (ADR-039 §7.3) — FREEZE"
        )

    authority = _require(data, "max_authority", "root")
    if authority != "propose":
        raise RuntimeError(
            "policy.yaml: max_authority must be 'propose' (execute forbidden) — FREEZE"
        )

    # --- سقف‌ها + ceiling مطلق ---
    caps_d = _require(data, "caps", "root")
    max_runs = int(_require(caps_d, "max_runs", "caps"))
    max_wall = int(_require(caps_d, "max_wall_seconds", "caps"))
    max_cost = float(_require(caps_d, "max_cost_aud", "caps"))
    if max_runs > _HARD_MAX_RUNS:
        raise RuntimeError(f"caps.max_runs {max_runs} > hard ceiling {_HARD_MAX_RUNS} — FREEZE")
    if max_wall > _HARD_MAX_WALL_S:
        raise RuntimeError(
            f"caps.max_wall_seconds {max_wall} > hard ceiling {_HARD_MAX_WALL_S} — FREEZE"
        )
    if max_cost > _HARD_MAX_COST:
        raise RuntimeError(f"caps.max_cost_aud {max_cost} > hard ceiling {_HARD_MAX_COST} — FREEZE")

    # --- بخش‌های phụ ---
    bu_d = _require(data, "belief_update", "root")
    ind_d = _require(data, "independence", "root")
    producers_d = _require(data, "producers", "root")

    return PolicyConfig(
        schema_version=1,
        default_off=bool(_require(data, "default_off", "root")),
        env_flag=str(_require(data, "env_flag", "root")),
        sandbox_profile="no_network",
        max_authority="propose",
        caps=Caps(max_runs=max_runs, max_wall_seconds=max_wall, max_cost_aud=max_cost),
        belief_update=BeliefUpdate(
            clip_log_odds=float(_require(bu_d, "clip_log_odds", "belief_update")),
            lambda_disagreement=float(_require(bu_d, "lambda_disagreement", "belief_update")),
        ),
        independence=Independence(
            min_clusters=int(_require(ind_d, "min_clusters", "independence")),
            clustering_keys=list(_require(ind_d, "clustering_keys", "independence")),
        ),
        authorized_producers=list(_require(producers_d, "authorized", "producers")),
        maturity_ladder=dict(data.get("maturity_ladder", {})),
    )
