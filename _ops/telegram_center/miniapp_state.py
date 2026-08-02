#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""miniapp_state.py — read-only state helpers for the MiniApp cockpit.

قرارداد (PHASE 4 megaprompt):
  · read-only — هیچ mutate، هیچ side-effect.
  · secret-scrubbed — هرگز token/chat_id/PII در خروجی.
  · fail-closed — اگه فایل غایب/خراب است، status=unknown نه صفرِ جعلی.
  · JSON-safe — خروجی همیشه JSON-serializable.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import opslib  # noqa: E402
    STATE_DIR = opslib.STATE_DIR
    ORGAN_STATE = opslib.ORGAN_STATE
    BUDGET_STATE = opslib.BUDGET_STATE
    ORGAN_LOG = opslib.ORGAN_LOG
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore
    STATE_DIR = _OPS / "state"
    ORGAN_STATE = _OPS / "budget" / "organ-state.json"
    BUDGET_STATE = _OPS / "budget" / "budget-state.json"
    ORGAN_LOG = _OPS / "budget" / "organ-gate-log.jsonl"

_ROOT = _OPS.parent
_RUNTIME = _OPS / "agi2027_runtime"
_TRUTH = _ROOT / "OCTOPUS-CURRENT-TRUTH-2026-08-02.md"

# ── منابعِ واقعیِ چهار بخشِ تازهٔ /api/ops (۲۰۲۶-۰۸-۰۳) ────────────────────────
# هر مسیر این‌جا **اعلام** می‌شود ولی هیچ‌جا **فرض** نمی‌شود: هر خواننده اول
# وجودش را می‌سنجد و اگر نبود، مقدار null با «دلیل» می‌دهد — نه عددِ ساختگی.
# ماژول‌سطح‌اند تا تست بتواند بدونِ دست‌زدن به درختِ زنده جایشان را عوض کند.
_4D_ROOT = _ROOT / "4d_system"
_4D_OUTPUTS = _4D_ROOT / "outputs"            # daemon_state.json + self_evolved/
_4D_CONSOLIDATION_PY = _4D_ROOT / "brain" / "consolidation.py"
_NEURAL_CONSOLIDATION = _OPS / "neural" / "consolidation.json"
_BUDGETS_YAML = _OPS / "budget" / "budgets.yaml"

# مسیرهای نسبی (نه مطلق) — چون هم در پیام و هم در سنجشِ وجود به‌کار می‌روند.
_FUGU_POLICY_REL = "docs/fugu_usage_policy.md"
_CANONICAL_PROVIDER_REL = "_ops/cortex/model_router.py"
_CANONICAL_CHOKE_POINT = "ask()"

# ریشه‌هایی که یک مسیرِ کوتاه‌نویسیِ سند ممکن است نسبت به آن‌ها نوشته شده باشد.
# بدونِ این، «brain/budget.py» ِ سند به‌غلط «گم‌شده» گزارش می‌شد — یعنی خودِ
# سطحِ حقیقت یک drift ِ دروغین می‌ساخت.
_PATH_ROOTS = ("", "_ops", "4d_system")

# اسنادِ ابسیدین که این سطح ادعای وجودشان را می‌کند. هر کدام **سنجیده** می‌شود.
_OBSIDIAN_DOCS = (
    "_PROJECT_INSTRUCTIONS.md",
    "CLAUDE.md",
    ".agentignore",
    "01 - Dashboard/HANDOFF.md",
    "01 - Dashboard/Home.md",
    "06 - Architecture Maps/ECOSYSTEM.md",
    "06 - Architecture Maps/Property Schema.md",
    "10 - Telegram processing/SOP.md",
    "10 - Telegram processing/ROUTING.md",
    _FUGU_POLICY_REL,
)

# الگوی scrub — عبارت‌های حساس را پاک می‌کند
_SECRET_RE = re.compile(
    r"(?i)(bot_token|api[_-]?key|secret|password|passwd|chat_id|bearer|sk-|fish_|xoxb-)"
    r"\s*[:=]\s*[^\s,;\"']+")
_TOKEN_RE = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def _scrub(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = _TOKEN_RE.sub("<TOKEN_REDACTED>", text)
    text = _SECRET_RE.sub(r"\1=<REDACTED>", text)
    text = _EMAIL_RE.sub("<EMAIL_REDACTED>", text)
    return text


def _scrub_dict(d: Any) -> Any:
    """بازگشتی secretها را از dict/list/str پاک می‌کند."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            if isinstance(k, str) and re.search(
                    r"(?i)token|secret|password|passwd|api[_-]?key|chat_id|cookie|session",
                    k):
                out[k] = "<REDACTED>"
            else:
                out[k] = _scrub_dict(v)
        return out
    if isinstance(d, list):
        return [_scrub_dict(x) for x in d]
    if isinstance(d, str):
        return _scrub(_scrub(d))
    return d


def _read_json_safe(path: Path) -> "dict | None":
    try:
        if not path.exists():
            return None
        d = json.loads(path.read_text("utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _read_json_any(path: Path):
    """مثلِ `_read_json_safe` ولی list را هم می‌پذیرد (فایل‌های append-only ِ چرخه)."""
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def _as_int(v):
    """int یا None — هرگز صفرِ جعلی به‌جای «نمی‌دانم»."""
    if isinstance(v, bool) or v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _iso(ts):
    """timestamp عددی → ISO ِ محلی؛ هر چیزِ دیگر → None (نه رشتهٔ ساختگی)."""
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(float(ts)))
    except (TypeError, ValueError, OSError):
        return None


def _exists(p: Path) -> bool:
    try:
        return p.exists()
    except OSError:
        return False


def _miniapp_url_configured() -> bool:
    """Best-effort config check without exposing the URL.
    The gateway may be started before the User env is inherited by the process,
    while run-miniapp-tunnel.ps1 always writes state/telegram/miniapp-url.json.
    Treat either source as configured so the cockpit does not show a false
    CONFIG_NEEDED warning.
    """
    if str(os.environ.get("OCTOPUS_MINIAPP_URL", "") or "").strip():
        return True
    try:
        import subprocess
        code = "[Environment]::GetEnvironmentVariable('OCTOPUS_MINIAPP_URL','User')"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", code],
                           capture_output=True, text=True, timeout=2)
        if (r.stdout or "").strip():
            return True
    except Exception:
        pass
    try:
        d = _read_json_safe(STATE_DIR / "telegram" / "miniapp-url.json")
        return bool(isinstance(d, dict) and str(d.get("url") or "").strip())
    except Exception:
        return False


def get_miniapp_state(root: "Path | None" = None) -> dict:
    """Home/Cockpit: system status، flags، pending، risk، Project-F، auth."""
    st = _read_json_safe(STATE_DIR / "ORGANISM-STATE.json")
    if st is None:
        return {"status": "unknown", "reason": "ORGANISM-STATE missing/unreadable"}
    flags = {
        "OCTOPUS_WIRE_TG_CONTROL": os.environ.get("OCTOPUS_WIRE_TG_CONTROL", "0") == "1",
        "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": os.environ.get("OCTOPUS_WIRE_LEAD_OUTBOUND_WAL", "0") == "1",
        "OCTOPUS_WIRE_VALUE_LEDGER": os.environ.get("OCTOPUS_WIRE_VALUE_LEDGER", "0") == "1",
    }
    # managed_flags.json را هم بخوان
    mf = _read_json_safe(_RUNTIME / "managed_flags.json")
    if isinstance(mf, dict):
        for k, v in mf.items():
            flags[k] = (str(v) == "1")
    # auth status: آیا bot_token + owner_id موجود است؟
    auth_configured = bool(os.environ.get("TG_CENTER_BOT_TOKEN")) and bool(os.environ.get("TELEGRAM_OWNER_CHAT_ID"))
    out = {
        "status": "ok",
        "halted": bool(st.get("halted") or st.get("stop_organism")),
        "frozen": bool(st.get("frozen")),
        "beat": st.get("beat"),
        "epoch_mode": st.get("epoch_mode"),
        "ts": st.get("ts"),
        "month": st.get("month"),
        "today": st.get("today"),
        "conflicts": st.get("conflicts"),
        "suspect_zero_total": st.get("suspect_zero_total"),
        "active_flags": flags,
        "auth_status": "configured" if auth_configured else "CONFIG_NEEDED",
        "projectf_status": "BLOCKED_NEEDS_CREDENTIALS",
        "miniapp_url_configured": _miniapp_url_configured(),
        "commit": _git_head_short(root),
    }
    return _scrub_dict(out)


def get_outbound_state(root: "Path | None" = None) -> dict:
    """Outbound/G-03: sent/failed/sending/needs_owner/cancelled counts."""
    db = _RUNTIME / "outbound-effects.sqlite3"
    if not db.exists():
        return {"status": "no_wal_db", "counts": {}, "note": "no outbound effects yet"}
    try:
        conn = sqlite3.connect(str(db))
        rows = conn.execute(
            "SELECT state, COUNT(*) FROM outbound_effects GROUP BY state").fetchall()
        conn.close()
        counts = {r[0]: r[1] for r in rows}
        return {"status": "ok", "counts": counts, "total": sum(counts.values())}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_approvals_state(root: "Path | None" = None) -> dict:
    """Approvals: pending proposal cards از outcomes."""
    db = STATE_DIR / "outcomes" / "outcomes.db"
    if not db.exists():
        return {"status": "no_outcomes_db", "pending": []}
    try:
        conn = sqlite3.connect(str(db))
        # best-effort: count deliveries not resolved
        try:
            rows = conn.execute(
                "SELECT proposal_id, kind, amount_aud FROM deliveries WHERE resolved=0 LIMIT 50"
            ).fetchall()
            pending = [{"proposal_id": r[0], "kind": r[1], "amount_aud": r[2]} for r in rows]
        except Exception:  # noqa: BLE001 — schema ممکن است متفاوت باشد
            pending = []
            conn.close()
            return {"status": "unknown_schema", "pending": []}
        conn.close()
        return {"status": "ok", "pending": _scrub_dict(pending), "count": len(pending)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_legs_state(root: "Path | None" = None) -> dict:
    """Legs/Agents: از business_legs در ORGANISM-STATE."""
    st = _read_json_safe(STATE_DIR / "ORGANISM-STATE.json")
    biz = st.get("business_legs") if isinstance(st, dict) else None
    # unwrap double-layer
    if isinstance(biz, dict) and "business_legs" in biz:
        biz = biz.get("business_legs")
    if not isinstance(biz, dict):
        return {"status": "unknown", "reason": "business_legs missing", "legs": {}}
    return {"status": "ok", "legs": _scrub_dict(biz)}


def get_value_state(root: "Path | None" = None) -> dict:
    """Value Ledger: خلاصه از value-ledger.jsonl (اگر هست)."""
    ledger = _RUNTIME / "value-ledger.jsonl"
    if not ledger.exists():
        return {"status": "no_value_ledger", "note": "value ledger not yet populated"}
    try:
        counts = {}
        for raw in ledger.read_text("utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                r = json.loads(raw)
            except ValueError:
                continue
            leg = r.get("leg", "?")
            counts[leg] = counts.get(leg, 0) + 1
        return {"status": "ok", "events_per_leg": counts, "total": sum(counts.values()),
                "auto_delete": False}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_ui_registry(root: "Path | None" = None) -> dict:
    """UI Registry: از ui-registry.json."""
    reg = _read_json_safe(_RUNTIME / "ui-registry.json")
    if reg is None:
        return {"status": "missing", "reason": "ui-registry.json not found"}
    return reg



# ══ brain ═══════════════════════════════════════════════════════════════════
def _brain_daemon() -> dict:
    """پاهای daemon ِ مغزِ 4D — منبع: همان فایلی که خودش می‌نویسد.

    `4d_system/brain/daemon.py:_save_state` → `<OUTPUT_DIR>/daemon_state.json`.
    عمداً `config.settings` را import نمی‌کنیم: آن ماژول در import ِ خودش
    `OUTPUT_DIR.mkdir()` می‌زند و یک سطحِ **فقط‌خواندنی** حق ندارد پوشه بسازد."""
    p = _4D_OUTPUTS / "daemon_state.json"
    src = "4d_system/outputs/daemon_state.json"
    d = _read_json_safe(p)
    if d is None:
        return {"reachable": False, "ticks": None, "errors": None,
                "last_tick": None, "generation": None,
                "reason": f"unreadable or absent: {src}", "source": src}
    fields = {"ticks": _as_int(d.get("total_ticks")),
              "errors": _as_int(d.get("errors_this_run")),
              "last_tick": d.get("last_tick_at") or None,
              "generation": _as_int(d.get("generation"))}
    missing = sorted(k for k, v in fields.items() if v is None)
    return {"reachable": True, "reason": None, "source": src,
            "missing_fields": missing, **fields}


def _brain_consolidation() -> dict:
    """تثبیتِ (consolidation) مغزِ 4D — هر عدد از یک فایلِ نام‌برده می‌آید.

    شمارش‌ها **مشتق**اند نه اعلامی: conclusions از طولِ `conclusions_fa`،
    frontier از تعدادِ سلول‌های آرشیو، و آخرین تأیید از آخرین چرخهٔ
    `self_evolved/consolidation.json`. هر منبعِ نخوانده = null + دلیل."""
    sd = _4D_OUTPUTS / "self_evolved"
    src_c = "4d_system/outputs/self_evolved/conclusions.json"
    src_f = "4d_system/outputs/self_evolved/frontier.json"
    src_y = "4d_system/outputs/self_evolved/consolidation.json"
    src_n = "_ops/neural/consolidation.json"
    engine_present = _exists(_4D_CONSOLIDATION_PY)
    concl = _read_json_safe(sd / "conclusions.json")
    front = _read_json_safe(sd / "frontier.json")
    cycles = _read_json_any(sd / "consolidation.json")
    neural = _read_json_any(_NEURAL_CONSOLIDATION)

    reasons = []
    n_concl = None
    if isinstance(concl, dict) and isinstance(concl.get("conclusions_fa"), list):
        n_concl = len(concl["conclusions_fa"])
    else:
        reasons.append(f"no conclusions_fa list in {src_c}")
    n_front = None
    if isinstance(front, dict):
        n_front = len(front)
    else:
        reasons.append(f"no cell archive in {src_f}")
    last_verified, last_sources = None, None
    if isinstance(cycles, list) and cycles and isinstance(cycles[-1], dict):
        last_verified = _iso(cycles[-1].get("timestamp"))
        vs = cycles[-1].get("verified_sources")
        last_sources = vs if isinstance(vs, list) else None
    else:
        reasons.append(f"no cycle history in {src_y}")
    neural_cycles = len(neural) if isinstance(neural, list) else None
    if neural_cycles is None:
        reasons.append(f"no cycle list in {src_n}")
    if not engine_present:
        reasons.append("4d_system/brain/consolidation.py absent")

    available = bool(engine_present and (n_concl is not None or n_front is not None
                                         or last_verified is not None))
    return {
        "available": available,
        "conclusions_count": n_concl,
        "frontier_count": n_front,
        "last_verified": last_verified,
        "last_verified_sources": last_sources,
        "neural_cycles": neural_cycles,
        "reason": None if available and not reasons else ("; ".join(reasons) or None),
        "sources": {"conclusions": src_c, "frontier": src_f,
                    "cycles": src_y, "neural_cycles": src_n,
                    "engine": "4d_system/brain/consolidation.py"},
    }


def get_brain_state(root: "Path | None" = None) -> dict:
    """بخشِ brain ِ /api/ops — fail-soft: نخواندن هرگز پاسخ را نمی‌کشد."""
    daemon = _brain_daemon()
    cons = _brain_consolidation()
    available = bool(daemon.get("reachable") or cons.get("available"))
    reason = None
    if not available:
        reason = "; ".join(x for x in (daemon.get("reason"), cons.get("reason")) if x) \
            or "brain sources unreadable"
    return {"available": available, "reason": reason,
            "daemon": daemon, "consolidation": cons}


# ══ governor ════════════════════════════════════════════════════════════════
def _resolve_declared(rel: str, r: Path) -> "str | None":
    """مسیرِ کوتاه‌نویسیِ سند را زیرِ ریشه‌های ممکن پیدا کن؛ نبود = None."""
    rel = rel.rstrip("/")
    for base in _PATH_ROOTS:
        cand = (r / base / rel) if base else (r / rel)
        try:
            if cand.exists():
                return (f"{base}/{rel}" if base else rel)
        except OSError:
            continue
    return None


def _policy_declared_paths(doc: Path, r: Path) -> list:
    """مسیرهایی که خودِ سندِ سیاست نام می‌برد + سنجشِ وجودِ هرکدام."""
    try:
        text = doc.read_text("utf-8", errors="replace")
    except OSError:
        return []
    out, seen = [], set()
    for m in re.finditer(r"`([^`\n]{3,120})`", text):
        s = m.group(1).strip()
        if "/" not in s or s.startswith("http"):
            continue
        if not (s.endswith(".py") or s.endswith(".ts") or s.endswith(".js")
                or s.endswith("/")):
            continue
        if s in seen:
            continue
        seen.add(s)
        found = _resolve_declared(s, r)
        out.append({"declared": s, "exists": found is not None, "resolved": found})
    return out


def _governor_drift(r: Path, policy: "Path | None", canonical_ok: bool) -> dict:
    """drift **مشتق** است نه اعلامی: سند را می‌خوانیم و مسیرهایش را می‌سنجیم."""
    if policy is None:
        return {"status": "unknown", "reason": f"policy doc absent: {_FUGU_POLICY_REL}",
                "declared_paths": [], "missing": [], "notes": []}
    declared = _policy_declared_paths(policy, r)
    if not declared:
        return {"status": "unknown", "reason": "no provider paths parsed from policy doc",
                "declared_paths": [], "missing": [], "notes": []}
    missing = [d["declared"] for d in declared if not d["exists"]]
    notes = [f"policy names `{m}` but it does not exist in this tree" for m in missing]
    try:
        text = policy.read_text("utf-8", errors="replace")
    except OSError:
        text = ""
    for line in text.splitlines():
        if _CANONICAL_PROVIDER_REL in line and "migrate" in line.lower():
            notes.append(f"policy marks the measured choke point "
                         f"`{_CANONICAL_PROVIDER_REL}` as pending migration")
            break
    if not canonical_ok:
        notes.append(f"canonical provider absent: {_CANONICAL_PROVIDER_REL}")
    return {"status": "drift" if (missing or not canonical_ok) else "aligned",
            "reason": None, "declared_paths": declared,
            "missing": missing, "notes": notes}


def _router_tier_roles(r: Path) -> "dict | None":
    """نگاشتِ tier→role ِ `model_router._TIER_ROLE` با خواندنِ **متنِ** خودِ فایل.

    عمداً import نمی‌کنیم: model_router به opslib/circuit_breaker/local_llm
    وصل است و این ماژول قراردادِ «صفر side-effect» دارد."""
    try:
        src = (r / _CANONICAL_PROVIDER_REL).read_text("utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"_TIER_ROLE\s*=\s*\{([^}]*)\}", src)
    if not m:
        return None
    return dict(re.findall(r"[\"'](\w+)[\"']\s*:\s*[\"'](\w+)[\"']", m.group(1)))


def _budget_role_models(path: Path) -> dict:
    """role → model از `budgets.yaml` (بدونِ وابستگی به pyyaml)."""
    try:
        text = path.read_text("utf-8", errors="replace")
    except OSError:
        return {}
    out, role, in_routing = {}, None, False
    for line in text.splitlines():
        if re.match(r"^routing:\s*(#.*)?$", line):
            in_routing = True
            continue
        if in_routing and line and not line.startswith(" "):
            break
        if not in_routing:
            continue
        m = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):\s*(#.*)?$", line)
        if m:
            role = m.group(1)
            continue
        m2 = re.match(r"^\s{3,}model:\s*\"?([^\"#\s]+)\"?", line)
        if m2 and role:
            out.setdefault(role, m2.group(1))
    return out


# نامِ مسیر → (role ِ budgets.yaml, برچسبِ انسانی). ترتیب = ترتیبِ نمایش.
_ROUTE_SPEC = (("local", "local"), ("fugu", "orchestr"),
               ("fugu_ultra", "premium"), ("fugu_cyber", None))


def _governor_routes(r: Path) -> dict:
    """چهار مسیرِ اعلام‌شده + این‌که آیا واقعاً از `ask()` دست‌یافتنی‌اند.

    «دست‌یافتنی» یعنی role اش در `_TIER_ROLE` باشد (یا local که fallback ِ
    ساختاریِ مسیریاب است). هر ادعای دیگری بدونِ شاهد = null با دلیل."""
    roles = _router_tier_roles(r)
    models = _budget_role_models(_BUDGETS_YAML)
    role_to_tier = {v: k for k, v in (roles or {}).items()}
    out = {}
    for name, role in _ROUTE_SPEC:
        model = models.get(role) if role else None
        if roles is None:
            out[name] = {"role": role, "model": model, "tier": None,
                         "reachable_from_ask": None,
                         "reason": f"could not parse _TIER_ROLE from {_CANONICAL_PROVIDER_REL}"}
            continue
        if role == "local":
            out[name] = {"role": "local", "model": model, "tier": "local",
                         "reachable_from_ask": True, "reason": None}
            continue
        tier = role_to_tier.get(role) if role else None
        reach = tier is not None
        reason = None
        if role is None:
            reason = ("no 'cyber' role in budgets.yaml routing and no cyber tier in "
                      f"{_CANONICAL_PROVIDER_REL}:_TIER_ROLE")
        elif not reach:
            reason = (f"role '{role}' is not mapped by "
                      f"{_CANONICAL_PROVIDER_REL}:_TIER_ROLE — unreachable from ask()")
        out[name] = {"role": role, "model": model, "tier": tier,
                     "reachable_from_ask": reach, "reason": reason}
    return out


def get_governor_state(root: "Path | None" = None) -> dict:
    """بخشِ governor — هیچ مسیری بدونِ سنجشِ وجود ادعا نمی‌شود."""
    r = Path(root) if root is not None else _ROOT
    policy = r / _FUGU_POLICY_REL
    canon = r / _CANONICAL_PROVIDER_REL
    policy_ok = _exists(policy)
    canon_ok = _exists(canon)
    return {
        "policy_doc": _FUGU_POLICY_REL if policy_ok else None,
        "policy_doc_reason": None if policy_ok else f"not found: {_FUGU_POLICY_REL}",
        "canonical_provider": _CANONICAL_PROVIDER_REL if canon_ok else None,
        "canonical_provider_reason": None if canon_ok else
            f"not found: {_CANONICAL_PROVIDER_REL}",
        "canonical_choke_point": _CANONICAL_CHOKE_POINT if canon_ok else None,
        "drift_status": _governor_drift(r, policy if policy_ok else None, canon_ok),
        "routes": _governor_routes(r),
    }


# ══ obsidian ════════════════════════════════════════════════════════════════
def get_obsidian_state(root: "Path | None" = None) -> dict:
    """بخشِ obsidian — **هر** مسیر سنجیده می‌شود.

    سطحِ حقیقتی که فایلِ غایب را «هست» اعلام کند، دقیقاً همان drift ای است که
    برای جلوگیری‌اش ساخته شده. مقدارِ خامِ REFERENCE_DIR بیرون نمی‌رود؛ فقط
    «پیکربندی شده یا نه»."""
    r = Path(root) if root is not None else _ROOT
    raw = str(os.environ.get("REFERENCE_DIR", "") or "").strip()
    ref_ok = False
    if raw:
        try:
            rp = Path(raw)
            rp = rp if rp.is_absolute() else (r / raw)
            ref_ok = rp.is_dir()
        except (OSError, ValueError):
            ref_ok = False
    docs = {}
    for rel in _OBSIDIAN_DOCS + (_TRUTH.name,):
        docs[rel] = {"exists": _exists(r / rel)}
    missing = sorted(k for k, v in docs.items() if not v["exists"])
    return {
        "reference_dir_configured": bool(raw and ref_ok),
        "reference_dir_reason": None if (raw and ref_ok) else (
            "REFERENCE_DIR env not set" if not raw
            else "REFERENCE_DIR set but the directory does not exist"),
        "vault_config_dir": _exists(r / ".obsidian"),
        "docs": docs,
        "missing": missing,
        "missing_count": len(missing),
        "checked": len(docs),
    }


# ══ next_steps ══════════════════════════════════════════════════════════════
def _ui_has(name: str, needles: tuple, need_all: bool = False) -> "bool | None":
    """آیا فایلِ UI ِ کاکپیت این نشانه‌ها را دارد؟ نخواندن = None (نه False).

    `need_all=True` وقتی نشانه‌ها **فهرستِ لازم**اند (چهار تب)، نه املاهای جایگزین."""
    try:
        text = (_HERE / "miniapp" / name).read_text("utf-8", errors="replace")
    except OSError:
        return None
    hits = [n in text for n in needles]
    return all(hits) if need_all else any(hits)


def _step(sid: str, title: str, status: str, evidence: str) -> dict:
    return {"id": sid, "title": title, "status": status, "evidence": evidence}


def get_next_steps(root: "Path | None" = None) -> list:
    """ترتیبِ ساختِ فعلی — وضعیتِ هر قدم **سنجیده** می‌شود نه اعلام.

    قدم‌های UI با خواندنِ خودِ `miniapp/index.html` و `miniapp/app.js` سنجیده
    می‌شوند (لِینِ دیگری مالکِ آن‌هاست؛ این‌جا فقط خوانده می‌شود)."""
    r = Path(root) if root is not None else _ROOT
    tabs = _ui_has("index.html", ('data-tab="brain"', 'data-tab="governor"',
                                  'data-tab="obsidian"', 'data-tab="next"'),
                   need_all=True)
    palette = _ui_has("app.js", ("palette", "Palette"))
    nba = _ui_has("app.js", ("nextBest", "next_best", "next-best"))
    policy = r / _FUGU_POLICY_REL
    drift = _governor_drift(r, policy if _exists(policy) else None,
                            _exists(r / _CANONICAL_PROVIDER_REL))

    def tri(v: "bool | None") -> str:
        return "unknown" if v is None else ("done" if v else "open")

    return [
        _step("ops-read-model",
              "/api/ops = تنها سطحِ صادقِ خواندنی (brain/governor/obsidian/next_steps)",
              "done", "miniapp_state.get_ops_state"),
        _step("ops-subendpoints",
              "زیرمسیرهای /api/ops/brain · /api/ops/leads · /api/ops/tasks",
              "done", "miniapp_state.dispatch_api handlers"),
        _step("ops-snapshot-cache", "کشِ ۲–۵ ثانیه‌ایِ اسنپ‌شات (خطا هرگز کش نمی‌شود)",
              "done", f"miniapp_state cache ttl={_cache_ttl():g}s"),
        _step("miniapp-tabs", "تب‌های Brain/Governor/Obsidian/Next در کاکپیت",
              tri(tabs), "miniapp/index.html data-tab"),
        _step("command-palette", "پالتِ فرمان در کاکپیت", tri(palette), "miniapp/app.js"),
        _step("next-best-action", "کارتِ «بهترین اقدامِ بعدی»", tri(nba), "miniapp/app.js"),
        _step("fugu-policy-drift",
              "بستنِ drift ِ سندِ سیاستِ Fugu (مسیرهای اعلام‌شدهٔ ناموجود)",
              "open" if drift.get("status") == "drift" else
              ("unknown" if drift.get("status") == "unknown" else "done"),
              f"governor.drift_status={drift.get('status')}"),
    ]


# ══ Ops Studio ══════════════════════════════════════════════════════════════
def _engine_summary(root: "Path | None" = None) -> dict:
    """خلاصهٔ خامِ موتورِ Ops — تنها نقطهٔ تماس با SQLite ِ محلی.

    جدا شد تا `/api/ops/leads` و `/api/ops/tasks` بتوانند **بدونِ** ساختنِ
    بخش‌های سنگینِ brain/governor/obsidian جواب بدهند."""
    try:
        import sys as _sys
        ops_path = str(_OPS)
        if ops_path not in _sys.path:
            _sys.path.insert(0, ops_path)
        from agi2027_control.ops_actions import OpsActionEngine  # noqa: WPS433
        eng = OpsActionEngine(Path(root) if root is not None else _ROOT)
        try:
            return dict(eng.summary())
        finally:
            eng.close()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def _section(fn, root, name: str, empty):
    """هر بخش در قرنطینهٔ خودش — یک بخشِ خراب هرگز کلِ /api/ops را نمی‌کشد."""
    try:
        return fn(root)
    except Exception as exc:  # noqa: BLE001
        if isinstance(empty, list):
            return []
        out = dict(empty)
        out["reason"] = f"{name}_read_failed: {type(exc).__name__}"
        return out


def get_ops_state(root: "Path | None" = None) -> dict:
    """Ops Studio local summary: leads/tasks/value + owner-auth + action registry
    + چهار بخشِ سطحِ حقیقت (brain / governor / obsidian / next_steps).

    قرارداد: **هیچ کلیدِ موجودی نه نام عوض می‌کند نه معنا.** `owner_auth` و
    `actions.registry`/`actions.blocked_prefixes` مستقیم از خودِ موتور خوانده
    می‌شوند (نه کپیِ دستی) و نام‌های قدیمی‌ترِ همان‌ها (`safe_local_actions`،
    `blocked_external_automation`) هم عمداً می‌مانند — چون دو لِینِ موازی هرکدام
    یکی را نوشته‌اند و حذفِ هرکدام یک breaking change با لباسِ «تمیزکاری» است."""
    out = _engine_summary(root)
    if out.get("status") == "ok":
        try:
            from agi2027_control.ops_actions import (  # noqa: WPS433
                ALLOWED_ACTIONS,
                BLOCKED_PREFIXES,
            )
            has_bot = bool(os.environ.get("TG_CENTER_BOT_TOKEN"))
            has_owner = bool(os.environ.get("TELEGRAM_OWNER_CHAT_ID"))
            out["owner_auth"] = {
                "configured": has_bot and has_owner,
                "bot_token": "set" if has_bot else "missing",
                "owner_id": "set" if has_owner else "missing",
            }
            out["actions"] = {
                "enabled_when": "owner-auth configured + Telegram initData valid",
                "registry": sorted(ALLOWED_ACTIONS),
                "blocked_prefixes": list(BLOCKED_PREFIXES),
                "safe_local_actions": sorted(ALLOWED_ACTIONS),
                "blocked_external_automation": list(BLOCKED_PREFIXES),
            }
        except Exception as exc:  # noqa: BLE001
            out["actions"] = {"status": "error", "reason": f"{type(exc).__name__}"}
    out["brain"] = _section(get_brain_state, root, "brain",
                            {"available": False, "daemon": {}, "consolidation": {}})
    out["governor"] = _section(get_governor_state, root, "governor",
                               {"policy_doc": None, "canonical_provider": None,
                                "drift_status": {"status": "unknown"}, "routes": {}})
    out["obsidian"] = _section(get_obsidian_state, root, "obsidian",
                               {"reference_dir_configured": False, "docs": {}})
    out["next_steps"] = _section(get_next_steps, root, "next_steps", [])
    return _scrub_dict(out)


def get_ops_brain(root: "Path | None" = None) -> dict:
    """`/api/ops/brain` — دقیقاً همان بخشِ brain ِ /api/ops، بدونِ بقیه."""
    return _scrub_dict({"status": "ok", "section": "brain",
                        "brain": _section(get_brain_state, root, "brain",
                                          {"available": False, "daemon": {},
                                           "consolidation": {}})})


def get_ops_leads(root: "Path | None" = None) -> dict:
    """`/api/ops/leads` — برشِ لیدها با همان نام‌کلیدهای /api/ops."""
    s = _engine_summary(root)
    if s.get("status") != "ok":
        return _scrub_dict({"status": s.get("status") or "error", "section": "leads",
                            "reason": s.get("reason"),
                            "leads_total": None, "lead_stages": None})
    return _scrub_dict({"status": "ok", "section": "leads",
                        "leads_total": s.get("leads_total"),
                        "lead_stages": s.get("lead_stages")})


def get_ops_tasks(root: "Path | None" = None) -> dict:
    """`/api/ops/tasks` — برشِ کارها با همان نام‌کلیدهای /api/ops."""
    s = _engine_summary(root)
    if s.get("status") != "ok":
        return _scrub_dict({"status": s.get("status") or "error", "section": "tasks",
                            "reason": s.get("reason"),
                            "tasks_total": None, "task_status": None})
    return _scrub_dict({"status": "ok", "section": "tasks",
                        "tasks_total": s.get("tasks_total"),
                        "task_status": s.get("task_status")})


def get_current_truth(root: "Path | None" = None) -> dict:
    """Current Truth: خلاصهٔ OCTOPUS-CURRENT-TRUTH markdown."""
    if not _TRUTH.exists():
        return {"status": "missing", "reason": "OCTOPUS-CURRENT-TRUTH file not found"}
    try:
        text = _TRUTH.read_text("utf-8", errors="replace")
        # اولین ~۲۰ خطِ غیر-frontmatter را بگیر
        lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("---")][:25]
        return {"status": "ok", "preview": _scrub("\n".join(lines)), "path": str(_TRUTH.name)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def _git_head_short(root: "Path | None" = None) -> str:
    """short commit hash، fail-soft."""
    import subprocess
    r = root if root is not None else _ROOT
    try:
        out = subprocess.run(["git", "-C", str(r), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


# ══ کشِ اسنپ‌شات ═════════════════════════════════════════════════════════════
# ۲–۵ ثانیه: به‌اندازهٔ کافی کوتاه که «کهنه» نشود، به‌اندازهٔ کافی بلند که یک
# رفرشِ کاکپیت (چند fetch پشتِ‌سرِ هم) دوباره کلِ درخت را نخواند.
# قانونِ سخت: **فقط پاسخِ سالم کش می‌شود.** یک خطا هرگز به‌جای موفقیت سرو نمی‌شود
# و یک ورودیِ سالمِ قدیمی هم نباید جای پاسخِ خرابِ امروز را بگیرد — پس هر پاسخِ
# ناسالم ورودیِ قبلی را هم باطل می‌کند.
_CACHE_TTL_DEFAULT = 3.0
_CACHE: dict = {}


def _cache_ttl() -> float:
    try:
        v = float(os.environ.get("OCTOPUS_MINIAPP_CACHE_TTL_S", _CACHE_TTL_DEFAULT))
    except (TypeError, ValueError):
        v = _CACHE_TTL_DEFAULT
    return max(0.0, min(5.0, v))


def _mono() -> float:
    """ساعتِ کش — تک‌نقطه تا تست بتواند زمان را جلو ببرد."""
    return time.monotonic()


def cache_clear() -> None:
    _CACHE.clear()


def _cached(key: str, fn, root) -> dict:
    ttl = _cache_ttl()
    now = _mono()
    hit = _CACHE.get(key)
    if hit is not None and ttl > 0 and (now - hit[0]) < ttl:
        return hit[1]
    data = fn(root)                    # استثنا اصلاً به این‌جا نمی‌رسد ⇒ کش نمی‌شود
    if isinstance(data, dict) and data.get("status") == "ok":
        _CACHE[key] = (now, data)
    else:
        _CACHE.pop(key, None)
    return data


# dispatcher برای gateway
def dispatch_api(path: str, root: "Path | None" = None) -> "tuple[int, bytes, str]":
    """GET /api/* dispatcher. خروجی: (status, body_bytes, content_type)."""
    p = str(path or "").split("?", 1)[0]
    handlers = {
        "/api/state": get_miniapp_state,
        "/api/outbound": get_outbound_state,
        "/api/approvals": get_approvals_state,
        "/api/legs": get_legs_state,
        "/api/value": get_value_state,
        "/api/ui-registry": get_ui_registry,
        "/api/current-truth": get_current_truth,
        "/api/ops": get_ops_state,
        # زیرمسیرها (رأیِ مالک): یک بخشِ سنگین نباید بقیه را کند کند.
        "/api/ops/brain": get_ops_brain,
        "/api/ops/leads": get_ops_leads,
        "/api/ops/tasks": get_ops_tasks,
    }
    fn = handlers.get(p)
    if fn is None:
        return 404, b'{"status":"not_found"}', "application/json; charset=utf-8"
    try:
        data = _cached(p, fn, root)
        return 200, json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"), \
            "application/json; charset=utf-8"
    except Exception as exc:  # noqa: BLE001 — fail-closed، هرگز crash
        return 500, json.dumps({"status": "error", "reason": f"{type(exc).__name__}"}).encode("utf-8"), \
            "application/json; charset=utf-8"


if __name__ == "__main__":
    # self-test: همه‌ی helpers را فراخوانی کن و خروجی JSON چاپ کن
    for name, fn in [("miniapp", get_miniapp_state), ("outbound", get_outbound_state),
                     ("approvals", get_approvals_state), ("legs", get_legs_state),
                     ("value", get_value_state), ("ops", get_ops_state), ("ui-registry", get_ui_registry),
                     ("current-truth", get_current_truth), ("ops/brain", get_ops_brain),
                     ("ops/leads", get_ops_leads), ("ops/tasks", get_ops_tasks),
                     ("brain", get_brain_state), ("governor", get_governor_state),
                     ("obsidian", get_obsidian_state)]:
        print(f"=== {name} ===")
        print(json.dumps(fn(), ensure_ascii=False, indent=2)[:600])
        print()
