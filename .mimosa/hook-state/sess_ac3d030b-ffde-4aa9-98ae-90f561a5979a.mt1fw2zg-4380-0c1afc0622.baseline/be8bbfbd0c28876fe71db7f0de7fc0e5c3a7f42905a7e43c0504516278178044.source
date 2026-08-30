#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_crypto_data.py — CH-08: Crypto/Wallet Connector for OCTOPUS.

منبع: 03 - Projects/Crypto - etoro/ (lunarcrush, cryptoquant, manifest, registry)
سینک: nervous-system/crypto-data.js  →  window.CRYPTO_DATA

قوانین سخت:
  • alert-only — هیچ BUY/SELL خودکار
  • دادهٔ stale (June 2026) → هشدار کهنه
  • registry خالی → blocker
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── paths ────────────────────────────────────────────────────────────────────
CRYPTO_DIR = Path("F:/backup/03 - Projects/Crypto - etoro")
NS_DIR = Path("F:/backup/nervous-system")

# ─── helpers ──────────────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def _find_latest_json(prefix: str) -> Path | None:
    """جدیدترین فایل با prefix (مثلاً lunarcrush_analysis_*.json)."""
    candidates = sorted(
        CRYPTO_DIR.glob(f"{prefix}_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return candidates[0] if candidates else None


def _parse_yaml_frontmatter(text: str) -> dict[str, Any]:
    """استخراج YAML frontmatter از markdown (ساده)."""
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm = text[3:end].strip()
    out: dict[str, Any] = {}
    for line in fm.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            out[k] = v
    return out


def _read_md_section(path: Path, heading: str) -> str:
    """خواندن بخش زیر یک heading markdown."""
    if not path.exists():
        return ""
    text = path.read_text("utf-8", errors="replace")
    pat = re.compile(rf"^##\s+{re.escape(heading)}.*$", re.MULTILINE | re.IGNORECASE)
    m = pat.search(text)
    if not m:
        return ""
    start = m.end()
    next_h = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_h.start() if next_h else len(text)
    return text[start:end].strip()


def _read_yaml_block(path: Path) -> dict[str, Any]:
    """خواندن بلوک YAML در یک فایل markdown."""
    if not path.exists():
        return {}
    text = path.read_text("utf-8", errors="replace")
    m = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if not m:
        return {}
    out: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            out[k] = v
    return out


def _stale_hours(path: Path | None) -> float | None:
    if not path or not path.exists():
        return None
    mtime = path.stat().st_mtime
    return (datetime.now().timestamp() - mtime) / 3600


def _status_from_stale(hours: float | None) -> dict[str, Any]:
    if hours is None:
        return {"label": "غایب", "emoji": "🔴", "color": "#ef4444", "hours": None}
    if hours > 24 * 30:
        return {"label": "کهنهٔ شدید", "emoji": "🔴", "color": "#ef4444", "hours": round(hours, 1)}
    if hours > 24 * 7:
        return {"label": "کهنه", "emoji": "🟡", "color": "#fcd34d", "hours": round(hours, 1)}
    if hours > 24:
        return {"label": "نیمه‌کهنه", "emoji": "🟡", "color": "#fcd34d", "hours": round(hours, 1)}
    return {"label": "تازه", "emoji": "🟢", "color": "#34d399", "hours": round(hours, 1)}


# ─── extractors ───────────────────────────────────────────────────────────────
def extract_manifest() -> dict[str, Any]:
    path = CRYPTO_DIR / "MANIFEST.yaml"
    if not path.exists():
        return {"found": False}
    text = path.read_text("utf-8", errors="replace")
    out: dict[str, Any] = {"found": True}
    # خطوط کلیدی
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("execution_state:"):
            out["execution_state"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("primary_blocker:"):
            out["primary_blocker"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("security_gate:"):
            out["security_gate"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("phase:"):
            out["phase"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("status_snapshot:"):
            continue
    return out


def extract_lunarcrush() -> dict[str, Any]:
    path = _find_latest_json("lunarcrush_analysis")
    data = _load_json(path, default={}) if path else {}
    summary = data.get("summary", {})
    top_buy = data.get("top_buy_candidates", [])[:5]
    top_sell = data.get("top_sell_candidates", [])[:5]
    stale = _status_from_stale(_stale_hours(path))
    return {
        "source": str(path) if path else None,
        "stale": stale,
        "summary": {
            "total_coins": summary.get("total_coins", 0),
            "buy_signals": summary.get("buy_signals", 0),
            "sell_signals": summary.get("sell_signals", 0),
            "hold_signals": summary.get("hold_signals", 0),
        },
        "top_buy": [{"symbol": c.get("symbol"), "name": c.get("name"), "price": c.get("price"),
                     "change_24h": c.get("change_24h"), "galaxy_score": c.get("galaxy_score")} for c in top_buy],
        "top_sell": [{"symbol": c.get("symbol"), "name": c.get("name"), "price": c.get("price"),
                      "change_24h": c.get("change_24h"), "galaxy_score": c.get("galaxy_score")} for c in top_sell],
        "errors_count": len(data.get("errors", [])),
    }


def extract_cryptoquant() -> dict[str, Any]:
    path = _find_latest_json("cryptoquant_analysis")
    data = _load_json(path, default={}) if path else {}
    stale = _status_from_stale(_stale_hours(path))
    per_asset = data.get("per_asset", [])
    # فقط assetهای با verdict غیر از NEUTRAL یا Low confidence
    signals = []
    for pa in per_asset:
        verdict = pa.get("verdict", "NEUTRAL")
        if verdict != "NEUTRAL":
            signals.append({
                "asset": pa.get("asset"),
                "verdict": verdict,
                "score": pa.get("normalized_score"),
                "confidence": pa.get("confidence"),
                "confidence_pct": pa.get("confidence_pct"),
            })
    agg = data.get("aggregate", {})
    return {
        "source": str(path) if path else None,
        "stale": stale,
        "aggregate": {
            "score": agg.get("score"),
            "verdict": agg.get("verdict"),
            "verdictClass": agg.get("verdictClass"),
            "emoji": agg.get("emoji"),
        },
        "completeness": data.get("completeness", {}),
        "signals": signals,
        "errors_count": len(data.get("errors", [])),
        "unavailable_count": len(data.get("unavailable", [])),
    }


def extract_registry() -> dict[str, Any]:
    path = CRYPTO_DIR / "Portfolio Registry.md"
    if not path.exists():
        return {"found": False, "positions_active": [], "positions_closed": []}
    text = path.read_text("utf-8", errors="replace")
    # شمردن پوزیشن‌ها (ساده: دنبال خطوطی با position: می‌گردد)
    active_section = _read_md_section(path, "پوزیشن‌های فعال")
    closed_section = _read_md_section(path, "پوزیشن‌های بسته")
    active_count = len(re.findall(r"^position:\s*\S", active_section, re.MULTILINE))
    closed_count = len(re.findall(r"^position:\s*\S", closed_section, re.MULTILINE))
    # بررسی خالی بودن
    active_empty = "*(خالی" in active_section or active_count == 0
    return {
        "found": True,
        "positions_active_count": active_count,
        "positions_closed_count": closed_count,
        "registry_empty": active_empty,
    }


def extract_runbook_rules() -> dict[str, Any]:
    path = CRYPTO_DIR / "Standing Rules.md"
    if not path.exists():
        return {"found": False, "rules_count": 0}
    text = path.read_text("utf-8", errors="replace")
    # شمردن قواعد شماره‌دار
    rules = re.findall(r"^\d+\.\s+\*\*", text, re.MULTILINE)
    return {
        "found": True,
        "rules_count": len(rules),
        "rules_summary": [r.strip() for r in rules[:6]],
    }


def extract_adapter() -> dict[str, Any]:
    path = CRYPTO_DIR / "contracts" / "adapter.yaml"
    if not path.exists():
        return {"found": False}
    text = path.read_text("utf-8", errors="replace")
    out: dict[str, Any] = {"found": True}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("autonomy_floor:"):
            out["autonomy_floor"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("tenant:"):
            out["tenant"] = line.split(":", 1)[1].strip().strip('"').strip("'")
    return out


# ─── composite score ──────────────────────────────────────────────────────────
def compute_crypto_score(manifest: dict, registry: dict, lc: dict, cq: dict) -> dict[str, Any]:
    """امتیاز کلی ۰..۱۰۰ برای پنل OCTOPUS."""
    score = 100
    details: dict[str, Any] = {}

    # registry خالی → -۳۰
    if registry.get("registry_empty", True):
        score -= 30
        details["registry_empty_penalty"] = 30
    else:
        details["registry_empty_penalty"] = 0

    # دادهٔ lunarcrush کهنه
    lc_hours = (lc.get("stale") or {}).get("hours")
    if lc_hours is not None and lc_hours > 24 * 7:
        score -= 15
        details["lunarcrush_stale_penalty"] = 15
    else:
        details["lunarcrush_stale_penalty"] = 0

    # دادهٔ cryptoquant کهنه
    cq_hours = (cq.get("stale") or {}).get("hours")
    if cq_hours is not None and cq_hours > 24 * 7:
        score -= 15
        details["cryptoquant_stale_penalty"] = 15
    else:
        details["cryptoquant_stale_penalty"] = 0

    # security gate بسته
    gate = manifest.get("security_gate", "").lower()
    if "closed" in gate:
        score -= 10
        details["gate_closed_penalty"] = 10
    else:
        details["gate_closed_penalty"] = 0

    # edge classifier broken
    state = manifest.get("execution_state", "").lower()
    if "broken" in state or "unwired" in state:
        score -= 15
        details["edge_broken_penalty"] = 15
    else:
        details["edge_broken_penalty"] = 0

    score = max(0, min(100, score))
    status = "سالم" if score >= 80 else "هشدار" if score >= 50 else "بحرانی"
    emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
    return {
        "score": score,
        "status": status,
        "emoji": emoji,
        "details": details,
    }


# ─── main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = _now_iso()

    manifest = extract_manifest()
    registry = extract_registry()
    lc = extract_lunarcrush()
    cq = extract_cryptoquant()
    rules = extract_runbook_rules()
    adapter = extract_adapter()
    composite = compute_crypto_score(manifest, registry, lc, cq)

    crypto_data = {
        "generated": generated,
        "project": {
            "name": "Crypto - eToro",
            "phase": manifest.get("phase", "unknown"),
            "execution_state": manifest.get("execution_state", "unknown"),
            "security_gate": manifest.get("security_gate", "unknown"),
            "primary_blocker": manifest.get("primary_blocker", "unknown"),
            "autonomy_floor": adapter.get("autonomy_floor", "unknown"),
            "risk_level": "critical",
            "action_mode": "alert-only",
        },
        "registry": registry,
        "standing_rules": rules,
        "lunarcrush": lc,
        "cryptoquant": cq,
        "composite": composite,
        "blockers": [
            {"id": "b1", "label": "Portfolio Registry خالی", "active": registry.get("registry_empty", True)},
            {"id": "b2", "label": "Security Gate بسته", "active": "closed" in (manifest.get("security_gate", "")).lower()},
            {"id": "b3", "label": "EdgeClassifier unwired", "active": "broken" in (manifest.get("execution_state", "")).lower() or "unwired" in (manifest.get("execution_state", "")).lower()},
            {"id": "b4", "label": "دادهٔ LunarCrush کهنه", "active": (lc.get("stale") or {}).get("hours", 0) > 24 * 7},
            {"id": "b5", "label": "دادهٔ CryptoQuant کهنه", "active": (cq.get("stale") or {}).get("hours", 0) > 24 * 7},
        ],
        "hard_rules": [
            "BUY همیشه انسانی — بدون استثنا",
            "SELL خودکار فقط از مسیر exit_rules ثبت‌شده و تأییدشده",
            "کلیدهای exchange: off-box، صفر دسترسی LLM",
            "cross-model check پیش از ارائه به انسان",
        ],
        "meta": {
            "schema_version": "crypto.v1",
            "source_dir": str(CRYPTO_DIR),
            "extractor": "extract_crypto_data.py",
        },
    }

    out_path = NS_DIR / "crypto-data.js"
    js = "window.CRYPTO_DATA = " + json.dumps(crypto_data, ensure_ascii=False, default=str) + ";\n"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(js)
    print("crypto-data.js refreshed", len(js), "chars ->", out_path)
    return 0


if __name__ == "__main__":
    exit(main())
