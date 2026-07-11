#!/usr/bin/env python3
"""registry_scan.py — URCP Phase-0 (پیشنهاد #۱۰، رأی مالک «کاملاً موافقم» ۲۰۲۶-۰۷-۱۱).

«You cannot govern what you cannot see» — این ماژول فقط *می‌بیند*:
registry ِ runtime ِ read-only از موجودیت‌های اکوسیستم (پروژه‌ها، ایجنت‌ها، اندام‌ها)
با پیش‌فرضِ `unknown` (اصلِ A5 ِ URCP: unknown امن‌تر از null/حدس است).

طراحی (سند: [[06 - Architecture Maps/URCP Reconciliation - control-plane on OCTOPUS]]):
  - **کشف (scan):** پوشه‌های `03 - Projects` (فرانت‌مترِ PROJECT.md اگر بود) و
    داک‌های `05 - Agents`. فقط خواندن؛ هرگز چیزی داخلِ پوشه‌های پروژه نوشته نمی‌شود.
  - **seed (manifest):** فایل‌های JSON ِ curated در `_ops/registry/entities/` —
    مقادیرِ manifest بر کشف مقدم‌اند (منبعِ حقیقتِ مالک).
  - **containment ِ Project-F:** تطبیق فقط با sha256 ِ نامِ پوشه (`folder_sha256`)؛
    برای موجودیتِ `content_free: true` اسکنر **پوشه را اصلاً نمی‌خواند** و هویت/پلتفرم
    هرگز echo نمی‌شود؛ + scrub ِ دفاعی روی کلِ snapshot.
  - **risk:** اسکنر حداکثر R3 می‌دهد (نگاشتِ low/medium/high→R1/R2/R3)؛
    R4/R5 فقط از manifest ِ دست‌نوشتهٔ مالک می‌آید — هرگز خودکار.
  - خروجی: `state/registry/registry-latest.json` (schema: registry.v0) +
    اختیاری یک رویدادِ خلاصه در events (فقط CLI با --emit؛ داشبورد لمس نمی‌شود).

$0 · stdlib (+yaml ِ موجودِ opslib فقط برای فرانت‌متر، fail-soft) · read-only · additive.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402

SCHEMA = "registry.v0"
UNKNOWN = "unknown"
ENTITIES_DIR = _HERE / "registry" / "entities"
SNAPSHOT_DIR = opslib.STATE_DIR / "registry"

# فیلدهای لازم برای conformance (نسبتِ known/required — صادقانه و ساده)
REQUIRED = ("owner", "risk_tier", "live_state", "approval_state", "physical_path")
# نگاشت‌های محافظه‌کار از فرانت‌مترِ PROJECT.md
RISK_MAP = {"low": "R1", "medium": "R2", "high": "R3"}         # R4/R5 هرگز خودکار
STATUS_MAP = {"active": "live", "paused": "paused", "done": "retired",
              "archived": "retired", "superseded": "retired"}
# scrub ِ دفاعیِ containment (تستِ سخت هم دارد)
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")


def _sha(name: str) -> str:
    return hashlib.sha256(str(name).encode("utf-8")).hexdigest()


def _slug(name: str) -> str:
    return str(name).strip().lower().replace(" ", "-")


def _blank(entity_type: str, logical_id: str, display: str) -> dict:
    return {"logical_id": logical_id, "entity_type": entity_type,
            "display_name": display, "physical_path": UNKNOWN,
            "owner": UNKNOWN, "risk_tier": UNKNOWN, "autonomy_level": UNKNOWN,
            "live_state": UNKNOWN, "approval_state": UNKNOWN,
            "capabilities": [], "content_free": False,
            "source": "scan", "notes": ""}


def _read_frontmatter(p: Path) -> dict:
    """فرانت‌مترِ ساده — fail-soft: هر خطا = {} (اسکنر هرگز نمی‌میرد)."""
    try:
        txt = p.read_text("utf-8", errors="ignore")
    except OSError:
        return {}
    if not txt.startswith("---"):
        return {}
    end = txt.find("\n---", 3)
    if end < 0:
        return {}
    block = txt[3:end]
    try:
        import yaml  # موجود در مسیرِ زنده (opslib) — ولی وابستگیِ سخت نیست
        d = yaml.safe_load(block)
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001 — fallback ِ خطی
        out = {}
        for line in block.splitlines():
            if ":" in line and not line.strip().startswith("#"):
                k, _, v = line.partition(":")
                out[k.strip()] = v.strip().strip('"')
        return out


def load_manifests(entities_dir: "Path | None" = None) -> list[dict]:
    d = entities_dir or ENTITIES_DIR
    out: list[dict] = []
    if not d.exists():
        return out
    for f in sorted(d.glob("*.json")):
        try:
            m = json.loads(f.read_text("utf-8"))
            if isinstance(m, dict) and m.get("logical_id"):
                m.setdefault("source", "manifest")
                out.append(m)
        except (OSError, ValueError):
            continue                                    # fail-soft: یک manifest ِ خراب بقیه را نمی‌کشد
    return out


def discover_projects(root: Path, manifests: list[dict]) -> list[dict]:
    base = root / "03 - Projects"
    ents: list[dict] = []
    if not base.exists():
        return ents
    by_sha = {m.get("folder_sha256"): m for m in manifests if m.get("folder_sha256")}
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name.startswith(("_", ".")):
            continue
        mf = by_sha.get(_sha(d.name))
        if mf is not None and mf.get("content_free"):
            continue                                    # containment: پوشه اصلاً خوانده نمی‌شود؛ manifest-only
        e = _blank("Project", f"urn:octopus:project:{_slug(d.name)}", d.name)
        e["physical_path"] = f"03 - Projects/{d.name}"
        fm = _read_frontmatter(d / "PROJECT.md")
        if fm:
            if fm.get("owner"):
                e["owner"] = str(fm["owner"])
            rl = str(fm.get("risk_level", "")).lower()
            if rl in RISK_MAP:
                e["risk_tier"] = RISK_MAP[rl]           # سقفِ خودکار: R3
            st = str(fm.get("status", "")).lower()
            if st in STATUS_MAP:
                e["live_state"] = STATUS_MAP[st]
            al = str(fm.get("autonomy_level", "")).strip()
            if al.upper() in ("L0", "L1", "L2", "L3"):
                e["autonomy_level"] = al.upper()
            elif al:
                e["notes"] = f"autonomy_note: {al[:40]}"
        ents.append(e)
    return ents


def discover_agents(root: Path) -> list[dict]:
    base = root / "05 - Agents"
    ents: list[dict] = []
    if not base.exists():
        return ents
    skip = {"AGENT_REGISTRY", "RATIFIED-TASKS"}
    for f in sorted(base.glob("*.md")):
        stem = f.stem
        if stem.startswith("_") or stem in skip:
            continue
        e = _blank("Agent", f"urn:octopus:agent:{_slug(stem)}", stem)
        e["physical_path"] = f"05 - Agents/{f.name}"
        fm = _read_frontmatter(f)
        if fm.get("owner"):
            e["owner"] = str(fm["owner"])
        ents.append(e)
    return ents


def merge(discovered: list[dict], manifests: list[dict]) -> list[dict]:
    """manifest بر کشف مقدم است (فیلد-به-فیلد، فقط مقادیرِ معنادار). dedup روی logical_id."""
    by_id: dict[str, dict] = {}
    for e in discovered:
        by_id[e["logical_id"]] = dict(e)
    for m in manifests:
        lid = m["logical_id"]
        base = by_id.get(lid) or _blank(m.get("entity_type", "Subsystem"), lid,
                                        m.get("display_name", lid))
        for k, v in m.items():
            if k in ("folder_sha256",):
                continue                                # هرگز واردِ snapshot نمی‌شود
            if v not in (None, "", UNKNOWN):
                base[k] = v
        base["source"] = "manifest+scan" if lid in by_id else "manifest"
        by_id[lid] = base
    return [by_id[k] for k in sorted(by_id)]


def conformance(e: dict) -> float:
    known = sum(1 for k in REQUIRED if e.get(k) and e.get(k) != UNKNOWN)
    return round(known / len(REQUIRED), 3)


def scrub(snapshot: dict) -> dict:
    """دفاعِ عمقی containment: هیچ رشتهٔ ممنوع هرگز از این ماژول بیرون نمی‌رود."""
    def _clean(x):
        if isinstance(x, str):
            low = x.lower()
            if any(b in low or b in x for b in _BANNED_ECHO):
                return "(redacted:containment)"
            return x
        if isinstance(x, list):
            return [_clean(i) for i in x]
        if isinstance(x, dict):
            return {k: _clean(v) for k, v in x.items()}
        return x
    return _clean(snapshot)


def build_snapshot(root: "Path | None" = None,
                   entities_dir: "Path | None" = None) -> dict:
    """خالص و read-only: هیچ نوشتنی. root پیش‌فرض = ORG_ROOT ِ opslib."""
    r = root or opslib.ORG_ROOT
    manifests = load_manifests(entities_dir)
    ents = merge(discover_projects(r, manifests) + discover_agents(r), manifests)
    for e in ents:
        e["conformance_score"] = conformance(e)
    counts = {
        "total": len(ents),
        "projects": sum(1 for e in ents if e["entity_type"] == "Project"),
        "agents": sum(1 for e in ents if e["entity_type"] == "Agent"),
        "organs": sum(1 for e in ents if e["entity_type"] == "Organ"),
        "unknown_owner": sum(1 for e in ents if e.get("owner") == UNKNOWN),
        "unknown_risk": sum(1 for e in ents if e.get("risk_tier") == UNKNOWN),
        "avg_conformance": round(sum(e["conformance_score"] for e in ents)
                                 / max(1, len(ents)), 3),
    }
    snap = {"ts": opslib.now_iso(), "schema": SCHEMA,
            "epistemic": "access-only — registry ِ read-only، نه ادعای کنترل",
            "counts": counts, "entities": ents}
    return scrub(snap)


def summary(snap: "dict | None" = None) -> str:
    s = snap or build_snapshot()
    c = s["counts"]
    return (f"🗂 registry: {c['projects']} پروژه · {c['agents']} ایجنت · "
            f"{c['organs']} اندام · مالکِ نامعلوم {c['unknown_owner']} · "
            f"conformance {c['avg_conformance']}")


def main(out_dir: "Path | None" = None, emit_event: bool = False) -> dict:
    snap = build_snapshot()
    out = out_dir or SNAPSHOT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "registry-latest.json").write_text(
        json.dumps(snap, ensure_ascii=False, indent=1), "utf-8")
    if emit_event:
        try:
            if str(_HERE) not in sys.path:
                sys.path.insert(0, str(_HERE))
            import events
            events.emit("task.completed", "registry", summary=summary(snap),
                        next_action="unknownها را در registry تعیین کن")
        except Exception:  # noqa: BLE001 — رویداد هرگز اسکنر را نمی‌کشد
            pass
    return snap


if __name__ == "__main__":
    s = main(emit_event=("--emit" in sys.argv))
    print(json.dumps({"counts": s["counts"], "summary": summary(s)},
                     ensure_ascii=False, indent=1))
