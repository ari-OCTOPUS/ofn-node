#!/usr/bin/env python3
"""drawdown_guard.py — SHADOW, alert-only drawdown guard (D3, owner-preapproved safe default).

WHAT THIS IS
  A pure, stdlib-only observer. It computes a "drawdown" status — how much of the
  daily budget has been burned — and, on breach, produces an ADVISORY alert dict.
  It has ZERO money effect: it never reserves, settles, releases, halts, blocks,
  or calls any effector. It is imported by budget_gate.py and invoked ONLY on a
  fail-soft, money-neutral shadow path (see budget_gate._drawdown_shadow_observe).

WHAT THIS IS NOT (owner-gated future work — DO NOT build here)
  ENFORCEMENT — actually blocking / halting spending on a drawdown breach — is
  explicitly owner-gated and NOT implemented. The HH_DRAWDOWN_ENFORCE flag is read
  only to record intent in the status; the enforcement branch is a documented
  no-op placeholder (see enforce_action()). Turning the flag on in THIS build only
  enables shadow observation + advisory alerts; it never blocks money.

THRESHOLD (owner-tunable, PLACEHOLDER)
  Single source of truth: budgets.yaml -> global.spike_pct (an existing, owner-tunable
  key; see budgets.yaml ~line 16). budget_gate._caps() surfaces it raw as caps["spike_pct"].
  When that key is absent/unreadable the guard falls back to
  DEFAULT_DRAWDOWN_PCT_PLACEHOLDER. That number is a PLACEHOLDER, NOT an
  owner-decided drawdown policy — the real drawdown policy (and its enforcement)
  is owner-gated future work.

STRUCTURAL INVARIANT
  This module imports only the Python standard library (os/json/pathlib, lazily).
  It never imports a network client, an effector, or any money-moving module, and
  never calls reserve()/settle()/release()/halt(). The alert path is observe-only.
"""
from __future__ import annotations

# ── flag (default OFF). Enforcement is NOT built here; see module docstring. ──────
FLAG_ENFORCE = "HH_DRAWDOWN_ENFORCE"

# ── threshold placeholder (owner-tunable via budgets.yaml global.spike_pct) ───────
#   PLACEHOLDER — deliberately NOT presented as an owner-decided drawdown policy.
DEFAULT_DRAWDOWN_PCT_PLACEHOLDER = 25.0
#   The single owner-tunable source key, as surfaced by budget_gate._caps().
THRESHOLD_SOURCE_KEY = "spike_pct"

_SRC_YAML = "budgets.yaml:global.spike_pct"
_SRC_PLACEHOLDER = "placeholder-constant:DEFAULT_DRAWDOWN_PCT_PLACEHOLDER"


def enforce_enabled(env=None) -> bool:
    """True only if the owner has explicitly set HH_DRAWDOWN_ENFORCE truthy.
    NOTE: even when True, THIS build does not block/halt — see enforce_action()."""
    import os
    e = os.environ if env is None else env
    return str(e.get(FLAG_ENFORCE, "")).strip().lower() in {"1", "true", "yes", "on"}


def threshold_pct(caps) -> tuple[float, str]:
    """Resolve the drawdown threshold from the SINGLE owner-tunable source.

    Returns (pct, source_tag). Reads caps["spike_pct"] (raw budgets.yaml value);
    on absence/garbage falls back to the documented placeholder constant. The tag
    lets callers prove which source produced the number (value alone is ambiguous
    because the placeholder happens to equal the current yaml default)."""
    v = None
    try:
        v = caps.get(THRESHOLD_SOURCE_KEY)
    except AttributeError:
        v = None
    if v is not None:
        try:
            return float(v), _SRC_YAML
        except (TypeError, ValueError):
            pass
    return DEFAULT_DRAWDOWN_PCT_PLACEHOLDER, _SRC_PLACEHOLDER


def evaluate(window_spend_aud, day_cap_aud, caps, *, enforce_flag_on=False) -> dict:
    """PURE shadow drawdown evaluation — no I/O, no money, deterministic.

    breach = (window_spend_aud / day_cap_aud) * 100 >= threshold_pct.
    Same inputs always yield the same status dict."""
    thr, src = threshold_pct(caps)
    try:
        spent = max(0.0, float(window_spend_aud))
        cap = float(day_cap_aud)
    except (TypeError, ValueError):
        spent, cap = 0.0, 0.0
    pct = (spent / cap * 100.0) if cap > 0 else 0.0
    return {
        "breach": pct >= thr,
        "window_pct": round(pct, 6),
        "threshold_pct": thr,
        "threshold_source": src,
        "enforce_requested": bool(enforce_flag_on),
        "enforced": False,   # ALWAYS False (this build): enforcement is owner-gated, not built
        "mode": "shadow",
    }


def build_alert(status, *, agent=None, now_iso=None) -> dict | None:
    """Return an ADVISORY alert dict on breach, else None.
    Observe-only: this NEVER moves money or calls an effector."""
    if not status.get("breach"):
        return None
    return {
        "kind": "drawdown-advisory",
        "severity": "advisory",   # advisory ONLY — never a halt/block in this build
        "agent": agent,
        "window_pct": status.get("window_pct"),
        "threshold_pct": status.get("threshold_pct"),
        "threshold_source": status.get("threshold_source"),
        "enforce_requested": status.get("enforce_requested"),
        "enforced": False,
        "ts": now_iso,
        "note": "SHADOW advisory — zero money effect; enforcement owner-gated (not built).",
    }


def enforce_action(status) -> dict:
    """OWNER-GATED FUTURE WORK — intentionally a no-op placeholder.

    Real enforcement (blocking / halting spending on a drawdown breach) is NOT
    implemented here. Kept as an explicit, named seam so the future owner-gated
    work is obvious and reviewable. It must never move money."""
    return {"enforced": False, "reason": "enforcement-owner-gated-not-built"}


def observe(window_spend_aud, day_cap_aud, caps, *, agent=None, now_iso=None,
            sink=None, log_path=None, enforce_flag_on=False) -> dict:
    """Full shadow observation: evaluate -> (on breach) advisory alert.

    Returns {"status": ..., "alert": ...}. ZERO money effect; fail-soft on all I/O.
    An error in the sink or the append-only log MUST NOT propagate — the shadow
    guard can never affect the money path."""
    status = evaluate(window_spend_aud, day_cap_aud, caps, enforce_flag_on=enforce_flag_on)
    alert = build_alert(status, agent=agent, now_iso=now_iso)
    if alert is not None:
        if sink is not None:
            try:
                sink(alert)
            except Exception:
                pass   # fail-soft
        if log_path is not None:
            try:
                import json
                import pathlib
                p = pathlib.Path(log_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "a", encoding="utf-8") as f:   # append-only observability log
                    f.write(json.dumps(alert, ensure_ascii=False) + "\n")
            except Exception:
                pass   # fail-soft
    return {"status": status, "alert": alert}
