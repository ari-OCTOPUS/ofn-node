#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_mining_data.py — CH-09 Mining Monitor for OCTOPUS.

Sources:
  • _ops/state/ORGANISM-STATE.json  → mining leg runtime state
  • 03 - Projects/Mining/MANIFEST.yaml  → manifest snapshot
  • 03 - Projects/Mining/PROJECT.md  → blockers, next actions, KPIs
  • 03 - Projects/Mining/Hardware Registry & Runbook.md  → node table
  • 03 - Projects/Mining/DecisionLog.md  → decision timeline
  • 03 - Projects/Mining/VERDICT_QUEUE.md  → pending owner verdicts
  • 03 - Projects/Mining/OpenQuestions.md  → open questions
  • 03 - Projects/Mining/02 - Code/Ai bots/QuantumAlphaBot/data/coin_hunter_cache.json  → coin scout cache

Sink:
  • nervous-system/mining-data.js  (window.MINING_DATA = ...)

Rules: stdlib-only, read-only, honest about missing data.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# ─── paths ────────────────────────────────────────────────────────────────────
NS_DIR = Path("F:/backup/nervous-system")
MINING_DIR = Path("F:/backup/03 - Projects/Mining")
OPS_STATE = Path("F:/backup/_ops/state")
COIN_CACHE = (
    MINING_DIR
    / "02 - Code"
    / "Ai bots"
    / "QuantumAlphaBot"
    / "data"
    / "coin_hunter_cache.json"
)

# ─── helpers ──────────────────────────────────────────────────────────────────
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_json(path: Path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def _parse_manifest(text: str) -> dict:
    """Extract key fields from MANIFEST.yaml via regex (no yaml lib)."""
    data: dict[str, str] = {}

    def grab(key: str) -> str | None:
        pat = rf'^[ ]*{re.escape(key)}:\s*["\']?(.*?)["\']?\s*$'
        m = re.search(pat, text, re.MULTILINE)
        if m:
            return m.group(1).strip().strip('"').strip("'")
        return None

    for k in ("code", "domain", "phase", "execution_state", "primary_blocker",
              "security_gate", "hardware", "role_in_ecosystem"):
        v = grab(k)
        if v:
            data[k] = v
    return data


def _extract_md_section(text: str, heading: str) -> str:
    """Extract content under a markdown heading until next ## heading."""
    pattern = re.compile(rf"^{re.escape(heading)}\s*$.*?(?=^## |\Z)", re.M | re.S | re.I)
    m = pattern.search(text)
    return m.group(0) if m else ""


def _parse_md_table(text: str) -> list[dict]:
    """Parse a simple markdown table into list of dicts."""
    lines = [l.rstrip() for l in text.splitlines() if "|" in l]
    if len(lines) < 2:
        return []
    header_line = lines[0]
    headers = [h.strip() for h in header_line.split("|") if h.strip()]
    rows = []
    for line in lines[2:]:
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c or c == ""]
        if not cells or all(c.replace("-", "").strip() == "" for c in cells):
            continue
        if len(cells) >= len(headers):
            row = {headers[i]: cells[i] for i in range(len(headers))}
            rows.append(row)
    return rows


def _parse_hardware_registry(text: str) -> list[dict]:
    """Extract hardware registry table."""
    section = _extract_md_section(text, "## رجیستری ناوگان")
    return _parse_md_table(section)


def _parse_verdict_queue(text: str) -> list[dict]:
    """Extract verdict queue table."""
    section = _extract_md_section(text, "# ✅ Mining VERDICT_QUEUE")
    return _parse_md_table(section)


def _parse_decisions(text: str) -> list[dict]:
    """Extract dated decisions from DecisionLog."""
    decisions = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("**"):
            continue
        m = re.match(r"\*\*(\d{4}-\d{2}-\d{2})\s*[-—]\s*(.+?)\*\*(.*)", line)
        if m:
            decisions.append({
                "date": m.group(1),
                "title": m.group(2).strip(),
                "detail": m.group(3).strip(" .")
            })
        else:
            decisions.append({
                "date": None,
                "title": line.strip("*").strip(),
                "detail": ""
            })
    return decisions


def _parse_open_blockers(text: str) -> list[str]:
    """Extract bullet list from ## Open blockers section."""
    section = _extract_md_section(text, "## Open blockers")
    blockers = []
    for line in section.splitlines():
        s = line.strip()
        if s.startswith("- "):
            blockers.append(s[2:].strip())
    return blockers


def _parse_open_questions(text: str) -> list[str]:
    """Extract numbered questions."""
    questions = []
    for line in text.splitlines():
        m = re.match(r"^\d+\.\s+(.+)", line.strip())
        if m:
            questions.append(m.group(1).strip())
    return questions


def _parse_coin_cache(path: Path) -> dict:
    data = _load_json(path, default={})
    if not data:
        return {
            "scanned_total": 0,
            "records_count": 0,
            "rejections": {},
            "candidates_count": 0,
            "top_candidates": [],
            "note": "coin_hunter_cache.json not found",
        }
    records = data.get("records", [])
    rejections = data.get("rejections", {})
    scanned = data.get("scanned", 0)

    candidates = []
    for r in records:
        try:
            age = float(r.get("age_days", 999))
            mcap = float(r.get("market_cap", 0) or 0)
            vol = float(r.get("volume_24h", 0) or 0)
            survival = int(r.get("survival_score", 0) or 0)
            symbol = r.get("symbol", "?")
            name = r.get("name", "?")
            score = 0
            if 0 <= age <= 90:
                score += 25
            elif age <= 180:
                score += 10
            if mcap > 0 and mcap < 100_000_000:
                score += 15
            if vol > 100_000:
                score += 15
            score += min(survival, 30)
            candidates.append({
                "symbol": symbol,
                "name": name,
                "age_days": age,
                "market_cap": mcap,
                "volume_24h": vol,
                "survival_score": survival,
                "score": min(score, 100),
            })
        except (ValueError, TypeError):
            continue

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return {
        "scanned_total": scanned,
        "records_count": len(records),
        "rejections": rejections,
        "candidates_count": len(candidates),
        "top_candidates": candidates[:12],
    }


# ─── core logic ───────────────────────────────────────────────────────────────
def compute_mining_data() -> dict:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    org = _load_json(OPS_STATE / "ORGANISM-STATE.json", default={})
    mining_org = org.get("mining", {})

    manifest_text = _read_text(MINING_DIR / "MANIFEST.yaml")
    manifest = _parse_manifest(manifest_text)

    proj_text = _read_text(MINING_DIR / "PROJECT.md")
    blockers = _parse_open_blockers(proj_text)

    hw_text = _read_text(MINING_DIR / "Hardware Registry & Runbook.md")
    nodes = _parse_hardware_registry(hw_text)

    dec_text = _read_text(MINING_DIR / "DecisionLog.md")
    decisions = _parse_decisions(dec_text)

    vq_text = _read_text(MINING_DIR / "VERDICT_QUEUE.md")
    verdicts = _parse_verdict_queue(vq_text)

    oq_text = _read_text(MINING_DIR / "OpenQuestions.md")
    questions = _parse_open_questions(oq_text)

    coins = _parse_coin_cache(COIN_CACHE)

    total = len(nodes)
    running = sum(1 for n in nodes if n.get("وضعیت", "").lower() == "running")
    broken = sum(1 for n in nodes if n.get("وضعیت", "").lower() == "broken")
    unknown = total - running - broken
    if total == 0:
        total = mining_org.get("nodes_total", 0)
        running = mining_org.get("nodes_running", 0)
        unknown = total - running
        broken = 0

    electricity_mood = mining_org.get("electricity_mood", "🟡")
    electricity_safe = mining_org.get("electricity_safe", False)
    hashrate_measured = mining_org.get("hashrate_measured", False)

    readiness = 0
    readiness_reasons = []
    if total > 0:
        readiness += 20
        readiness_reasons.append("رجیستری سخت‌افزار موجود")
    else:
        readiness_reasons.append("رجیستری سخت‌افزار خالی")
    if running > 0:
        readiness += 25
        readiness_reasons.append("حداقل یک نود running")
    else:
        readiness_reasons.append("هیچ نود running نیست")
    if electricity_safe:
        readiness += 25
        readiness_reasons.append("گیت برق عبور کرد")
    else:
        readiness_reasons.append("گیت برق نامشخص/ناامن")
    if not blockers:
        readiness += 15
        readiness_reasons.append("بلاکر باز ندارد")
    else:
        readiness_reasons.append(f"{len(blockers)} بلاکر باز")
    if coins["candidates_count"] > 0:
        readiness += 15
        readiness_reasons.append("کاندید کوین یافت شد")
    else:
        readiness_reasons.append("کاندید کوین ندارد")

    readiness = min(100, readiness)
    readiness_mood = "🟢" if readiness >= 70 else "🟡" if readiness >= 40 else "🟠"

    gates = {
        "wallet_zero_access": {
            "pass": True,
            "mood": "🟢",
            "note": "D-11: هیچ ایجنت به wallet/seed دسترسی ندارد",
        },
        "electricity_verified": {
            "pass": electricity_safe,
            "mood": "🟢" if electricity_safe else "🟡",
            "note": "<$0.05/kWh یا solar" if electricity_safe else "هزینه/منبع برق تأیید نشده",
        },
        "registry_filled": {
            "pass": total > 0 and any(n.get("وضعیت") not in ("", "[To measure]") for n in nodes),
            "mood": "🟢" if total > 0 else "🟡",
            "note": "رجیستری تکمیل" if total > 0 else "رجیستری خالی — نودها [To measure]",
        },
        "verdict_queue_clear": {
            "pass": len(verdicts) == 0,
            "mood": "🟢" if len(verdicts) == 0 else "🟡",
            "note": f"{len(verdicts)} verdict باز" if verdicts else "صف verdict خالی",
        },
        "no_active_mining": {
            "pass": running == 0,
            "mood": "🟢" if running == 0 else "🟡",
            "note": "ZERO mining active (safe state)" if running == 0 else f"{running} نود فعال — نیاز به پایش",
        },
    }

    data = {
        "generated": generated,
        "project": {
            "code": manifest.get("code", "Mining"),
            "domain": manifest.get("domain", "CPU/ARM cryptocurrency mining"),
            "phase": manifest.get("phase", "unknown"),
            "status": manifest.get("execution_state", "unknown"),
            "risk_level": "medium",
            "autonomy": "read-only / propose-only",
            "primary_blocker": manifest.get("primary_blocker", "unknown"),
            "open_blockers": blockers,
            "open_questions": questions,
        },
        "fleet": {
            "nodes_total": total,
            "nodes_running": running,
            "nodes_broken": broken,
            "nodes_unknown": unknown,
            "electricity_mood": electricity_mood,
            "electricity_safe": electricity_safe,
            "hashrate_measured": hashrate_measured,
            "thermal_warn": mining_org.get("thermal_warn", []),
            "nodes_detail": nodes if nodes else [],
        },
        "coins": coins,
        "decisions": {
            "count": len(decisions),
            "recent": decisions[-8:] if decisions else [],
        },
        "verdicts": {
            "pending_count": len(verdicts),
            "items": verdicts,
        },
        "readiness": {
            "score": readiness,
            "mood": readiness_mood,
            "reasons": readiness_reasons,
        },
        "security": {
            "gates": gates,
            "hard_rules": [
                "D2: survival-based death-watch تنها معیار قطع",
                "D-10: execution مالی HARD_STOP",
                "D-20: NO direct SSH",
                "D-11: NO wallet access",
                "برق: HALT اگر >$0.05/kWh و نه solar",
            ],
        },
        "runtime": {
            "beat": mining_org.get("beat", 0),
            "money_link": mining_org.get("money_link", "?"),
            "proposals_total": mining_org.get("proposals_total", 0),
            "brains": mining_org.get("brains", []),
        },
        "source_files": [
            str(OPS_STATE / "ORGANISM-STATE.json"),
            str(MINING_DIR / "MANIFEST.yaml"),
            str(MINING_DIR / "PROJECT.md"),
            str(MINING_DIR / "Hardware Registry & Runbook.md"),
            str(MINING_DIR / "DecisionLog.md"),
            str(MINING_DIR / "VERDICT_QUEUE.md"),
            str(MINING_DIR / "OpenQuestions.md"),
            str(COIN_CACHE),
        ],
    }
    return data


def emit_js(data: dict, out_dir: Path = NS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "mining-data.js"
    js = "window.MINING_DATA = " + json.dumps(data, ensure_ascii=False, default=str) + ";\n"
    out_path.write_text(js, encoding="utf-8")
    print("mining-data.js refreshed:", len(js), "chars")
    return out_path


def main() -> int:
    data = compute_mining_data()
    emit_js(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
