#!/usr/bin/env python3
"""export_status.py — بسته‌بندیِ فقط‌خواندنیِ وضعیتِ کاملِ اکتاپوس در یک JSON.

خروجی: _ops/state/export/octopus-status-bundle.json — برای آپلود در ابزارهای
بیرونی (Claude Design cockpit و غیره). هیچ write به state؛ فقط read.

امنیت (§۱۰):
  - OWNER-PROFILE*.json هرگز خوانده نمی‌شود (دادهٔ خصوصی مالک).
  - هیچ *.env/secret خوانده نمی‌شود.
  - پیش از نوشتن، کلِ خروجی با الگوهای secret (توکن تلگرام، sk-*) اسکن می‌شود؛
    اگر چیزی پیدا شد → abort (fail-closed).

اجرا:  python -X utf8 F:\\backup\\_ops\\export_status.py
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent
_STATE = _OPS / "state"
_VAULT = _OPS.parent
_OUT_DIR = _STATE / "export"
_OUT = _OUT_DIR / "octopus-status-bundle.json"

# فایل‌هایی که هرگز وارد بسته نمی‌شوند
_FORBIDDEN_NAMES = ("owner-profile", ".env", "secret", "wallet", "seed", "key", ".pem")
# الگوهای secret — پیدا شدن هر کدام در خروجی = abort
_SECRET_PATTERNS = [
    re.compile(r"\d{8,12}:AA[A-Za-z0-9_-]{30,}"),   # توکن بات تلگرام
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),            # کلیدهای sk-*
    re.compile(r"-----BEGIN [A-Z ]*KEY"),
]


def _read_json(path: Path):
    try:
        if any(b in path.name.lower() for b in _FORBIDDEN_NAMES):
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(path: Path) -> list:
    out = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append({"_unparseable_line": True, "head": line[:60]})
    except OSError:
        pass
    return out


def _tail_text(path: Path, n: int = 30) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except OSError:
        return []


def _chrono_summary() -> dict:
    """خلاصهٔ فقط‌خواندنی از chrono.db (URI mode=ro — قفل نمی‌گیرد)."""
    db = _STATE / "chrono.db"
    if not db.exists():
        return {"exists": False}
    out: dict = {"exists": True}
    try:
        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=3)
        cur = con.cursor()
        for table, key in (("heartbeat", "heartbeats"), ("gated_effect", "gated_effects"),
                           ("duration_marker", "duration_markers")):
            try:
                out[key] = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.Error:
                out[key] = None
        # verdictهای calibration (برای پنل Doctor)
        try:
            rows = cur.execute(
                "SELECT label FROM duration_marker WHERE event_id LIKE 'verdict-%'"
            ).fetchall()
            verdicts = []
            for (label,) in rows[-20:]:
                try:
                    verdicts.append(json.loads(label))
                except (json.JSONDecodeError, TypeError):
                    pass
            out["rfc_verdicts_tail"] = verdicts
            out["rfc_verdicts_total"] = len(rows)
        except sqlite3.Error:
            out["rfc_verdicts_tail"] = []
        # وضعیت اثرهای گیت‌شده به تفکیک status
        try:
            out["effects_by_status"] = dict(cur.execute(
                "SELECT status, COUNT(*) FROM gated_effect GROUP BY status").fetchall())
        except sqlite3.Error:
            out["effects_by_status"] = {}
        con.close()
    except sqlite3.Error as e:
        out["error"] = f"{type(e).__name__}"
    return out


def _genome_ledger_summary() -> dict:
    led_dir = _VAULT / "07 - Knowledge" / "genome-system" / "ledger"
    led = led_dir / "ledger.jsonl"
    out: dict = {"exists": led.exists()}
    if not led.exists():
        return out
    try:
        lines = [l for l in led.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        out["records"] = len(lines)
    except OSError:
        out["records"] = None
    # verify-scars (فقط‌خواندنی، subprocess با timeout)
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(led_dir / "ledger.py"),
                            str(led), "verify-scars"],
                           capture_output=True, text=True, timeout=30)
        out["verify_scars"] = (r.stdout or "").strip()[:200]
        out["verify_scars_ok"] = r.returncode == 0
    except Exception as e:  # noqa: BLE001 — گزارش صادقانه، نه crash
        out["verify_scars"] = f"error: {type(e).__name__}"
        out["verify_scars_ok"] = None
    return out


def _organ_table() -> dict:
    """نام و floor ارگان‌ها از budgets.yaml (فقط‌خواندنی — I6 دست‌نخورده)."""
    try:
        sys.path.insert(0, str(_OPS / "budget"))
        import opslib  # noqa: PLC0415
        table = opslib.organ_table()
        return {k: (v if isinstance(v, (int, float)) else v) for k, v in table.items()} \
            if isinstance(table, dict) else {"_raw": str(table)[:200]}
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}


def build_bundle() -> dict:
    bundle: dict = {
        "_meta": {
            "generator": "export_status.py v1 (read-only)",
            "bundle_version": 1,
            "note": "بستهٔ وضعیت اکتاپوس برای کابین بازرسی — هیچ secret؛ پروفایل خصوصی مالک عمداً غایب",
        },
        "organism_state": _read_json(_STATE / "ORGANISM-STATE.json"),
        "fitness": _read_json(_STATE / "fitness-latest.json"),
        "replication": _read_json(_STATE / "replication-latest.json"),
        "telemetry": _read_json(_STATE / "telemetry-latest.json"),
        "school_awareness": _read_json(_STATE / "school-awareness.json"),
        "channel_status": _read_json(_STATE / "channel-status.json"),
        "fisher": _read_json(_STATE / "fisher-latest.json"),
        "chamber_temperature": _read_json(_STATE / "chamber-temperature.json"),
        "bcm_weights_summary": None,
        "latent_summary": None,
        "phase_metrics": _read_jsonl(_STATE / "phase-metrics.jsonl"),
        "phase_reviews": [],
        "consolidation_summary": None,
        "governor_alerts_tail": _tail_text(_OPS / "governor" / "governor-alerts.md", 30),
        "chrono": _chrono_summary(),
        "genome_ledger": _genome_ledger_summary(),
        "organ_table": _organ_table(),
        "epochs": None,
    }
    # زمانِ تولید از خودِ ORGANISM-STATE (نه ساعت جدا) + fallback
    import datetime
    bundle["_meta"]["generated_at"] = datetime.datetime.now().isoformat(timespec="seconds")

    # BCM — فقط خلاصه (وزن‌ها ممکن است بزرگ شوند)
    bw = _read_json(_STATE / "bcm-weights.json")
    if bw and isinstance(bw.get("keys"), dict):
        ws = sorted(((k, r.get("w", 0)) for k, r in bw["keys"].items()),
                    key=lambda kv: -kv[1])
        bundle["bcm_weights_summary"] = {
            "step": bw.get("step"), "beta": bw.get("beta"),
            "count": len(bw["keys"]), "saturation_of_512": round(len(bw["keys"]) / 512, 4),
            "strongest_10": ws[:10], "weakest_10": ws[-10:],
        }
    # latent — فقط شمارش per-layer (وکتورها سنگین‌اند)
    lv = _read_json(_STATE / "latent-vectors.json")
    if isinstance(lv, list):
        by_layer: dict = {}
        for rec in lv:
            by_layer[rec.get("layer", "?")] = by_layer.get(rec.get("layer", "?"), 0) + 1
        bundle["latent_summary"] = {"total": len(lv), "by_layer": by_layer}
    # consolidation — شمارش + آخرین cycle
    cj = _read_json(_OPS / "neural" / "consolidation.json")
    if isinstance(cj, list) and cj:
        bundle["consolidation_summary"] = {"cycles": len(cj), "last": cj[-1]}
    # reviews
    rv_dir = _STATE / "reviews"
    if rv_dir.is_dir():
        for f in sorted(rv_dir.glob("*.json")):
            doc = _read_json(f)
            if doc is not None:
                doc["_file"] = f.name
                bundle["phase_reviews"].append(doc)
    # epochs — شمارش + آخرین
    ep_dir = _OPS / "budget" / "epochs"
    if ep_dir.is_dir():
        eps = sorted(ep_dir.glob("epoch-*.json"))
        bundle["epochs"] = {"count": len(eps),
                            "latest": _read_json(eps[-1]) if eps else None}
    # sparse predictor — خلاصه
    sp = _read_json(_STATE / "sparse-predictor.json")
    if sp:
        keys = sp.get("keys", sp) if isinstance(sp, dict) else {}
        bundle["sparse_summary"] = {"tracked_keys": len(keys) if isinstance(keys, dict) else None}
    return bundle


def main() -> int:
    bundle = build_bundle()
    # default=str: تاریخ‌های YAML (مثلاً deadline در budgets) → رشته
    text = json.dumps(bundle, ensure_ascii=False, indent=1, default=str)
    # اسکن امنیتی fail-closed — هیچ secret در خروجی
    for pat in _SECRET_PATTERNS:
        if pat.search(text):
            print("ABORT: الگوی secret در بسته پیدا شد — چیزی نوشته نشد.")
            return 1
    if "OWNER-PROFILE" in text.upper().replace("_", "-"):
        print("ABORT: ردپای OWNER-PROFILE — چیزی نوشته نشد.")
        return 1
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _OUT.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(_OUT)
    print(f"OK: {_OUT}  ({len(text)/1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
