"""Tiny stdlib discrete Active Inference. Not pymdp. Not executable control.

Expected free energy here is risk + ambiguity for a POMDP with |S| ≤ 4.
This module never issues motor commands, HTTP, or systemd actions.
"""

from __future__ import annotations

from typing import Any

MAX_STATES = 4
EXECUTABLE = False


def _validate_simplex(vector: list[float], name: str) -> list[float]:
    if not vector:
        raise ValueError(f"{name}_empty")
    if any(x < 0 for x in vector):
        raise ValueError(f"{name}_negative")
    total = sum(vector)
    if total <= 0:
        raise ValueError(f"{name}_zero")
    return [x / total for x in vector]


def expected_free_energy(
    *,
    A: list[list[float]],
    B_policy: list[list[float]],
    C: list[float],
    qs: list[float],
) -> dict[str, Any]:
    """EFE = risk + ambiguity. Information gain is not subtracted here.

    A[o][s] = P(o|s), columns should be observation likelihoods per state.
    B_policy[s'][s] = P(s'|s, π) for one policy.
    C[o] = preferred observation log-prob (already a preference vector).
    qs[s] = current state belief.
    """
    if len(qs) > MAX_STATES:
        raise ValueError("state_dim_exceeds_4")
    qs_n = _validate_simplex(list(qs), "qs")
    n_s = len(qs_n)
    n_o = len(A)
    if n_o == 0 or any(len(row) != n_s for row in A):
        raise ValueError("A_shape")
    if len(B_policy) != n_s or any(len(row) != n_s for row in B_policy):
        raise ValueError("B_shape")
    if len(C) != n_o:
        raise ValueError("C_shape")

    # Predicted next-state belief q(s') = B q(s)
    qsp = [0.0] * n_s
    for sp in range(n_s):
        qsp[sp] = sum(B_policy[sp][s] * qs_n[s] for s in range(n_s))
    qsp = _validate_simplex(qsp, "qsp")

    # Predicted observations qo = A q(s')
    qo = [sum(A[o][s] * qsp[s] for s in range(n_s)) for o in range(n_o)]
    qo = _validate_simplex(qo, "qo")

    # Risk: KL[q(o)||P(o)] with P(o) ∝ exp(C) then normalized
    import math

    pref_raw = [math.exp(c) for c in C]
    pref = _validate_simplex(pref_raw, "pref")
    risk = 0.0
    for o in range(n_o):
        if qo[o] > 0 and pref[o] > 0:
            risk += qo[o] * math.log(qo[o] / pref[o])

    # Ambiguity: E_{q(s')} H[P(o|s')]
    ambiguity = 0.0
    for s in range(n_s):
        col = [max(A[o][s], 0.0) for o in range(n_o)]
        col_n = _validate_simplex(col, f"A_col_{s}")
        entropy = 0.0
        for p in col_n:
            if p > 0:
                entropy -= p * math.log(p)
        ambiguity += qsp[s] * entropy

    efe = risk + ambiguity
    return {
        "efe": efe,
        "risk": risk,
        "ambiguity": ambiguity,
        "information_gain_subtracted": False,
        "state_dim": n_s,
        "obs_dim": n_o,
        "executable": EXECUTABLE,
        "engine": "stdlib-discrete-pomdp",
        "pymdp": False,
        "jax": False,
    }


def plan_shadow(
    A: list[list[float]],
    policies: list[list[list[float]]],
    C: list[float],
    qs: list[float],
) -> dict[str, Any]:
    scored = []
    for index, B in enumerate(policies):
        scored.append({"policy_index": index, **expected_free_energy(A=A, B_policy=B, C=C, qs=qs)})
    ranked = sorted(scored, key=lambda item: item["efe"])
    return {
        "ranked": ranked,
        "selected_policy_index": ranked[0]["policy_index"] if ranked else None,
        "executable": EXECUTABLE,
        "note": "shadow ranking only; no actuator dispatch",
    }
