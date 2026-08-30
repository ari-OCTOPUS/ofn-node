#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
owner_debug — the ⑤ گزارش و دیباگ surface: a cheap, read-only, live "doctor scan lite".

Surfaces the four things the owner asked to see: خطاها · اتصالِ قطع · کارِ تکراری · UIِ زائد.
It runs quick on-disk checks against the REAL vault and returns compact, content-free findings.
It is NOT the full Doctor (doctor/); it is the always-cheap owner-facing snapshot that the menu
shows instantly. Reuses owner_views.legs_status for the legs signal (no duplication).

Read-only. Never mutates. Graceful: missing files simply produce fewer findings, never a crash.
Signal paths verified by live probe 2026-07-18 (dlq.jsonl 1 entry; telegram.log 0 bytes; etc.).
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import owner_views as ov  # reuse legs_status

DEFAULT_VAULT_ROOT = os.environ.get("OCTOPUS_VAULT_ROOT", r"F:\backup")


def _exists(p: str) -> bool:
    return os.path.exists(p)


def _size(p: str) -> int:
    try:
        return os.path.getsize(p)
    except Exception:
        return -1


def _count_lines(p: str) -> int:
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for ln in f if ln.strip())
    except Exception:
        return 0


def _flag_present(flags_path: str, name: str) -> bool:
    try:
        with open(flags_path, "r", encoding="utf-8", errors="ignore") as f:
            return name in f.read()
    except Exception:
        return False


def scan(vault_root: str = DEFAULT_VAULT_ROOT) -> Dict[str, List[Dict[str, str]]]:
    """Return findings grouped as errors / broken / duplicates / dead_ui. Content-free."""
    j = lambda *a: os.path.join(vault_root, *a)
    errors: List[Dict[str, str]] = []
    broken: List[Dict[str, str]] = []
    duplicates: List[Dict[str, str]] = []
    dead_ui: List[Dict[str, str]] = []

    # ── errors ──
    dlq = j("_ops", "state", "dlq.jsonl")
    n_dlq = _count_lines(dlq)
    if n_dlq:
        errors.append({"sev": "red", "msg": f"{n_dlq} رکورد در صفِ مرده (dlq)"})
    if _size(j("_octopus", "logs", "errors.log")) > 0:
        errors.append({"sev": "red", "msg": "errors.log خالی نیست"})

    # ── broken / dry pipes ──
    if _size(j("_octopus", "logs", "telegram.log")) == 0:
        broken.append({"sev": "orange", "msg": "باتِ تلگرام poll نمی‌کند (RUN-TG-CENTER.bat اجرا شود)"})
    if not _exists(j("_ops", "state", "legs", "lead-inbox")):
        broken.append({"sev": "orange", "msg": "صندوقِ لید (lead-inbox) نیست → مسیرِ درآمد بسته"})
    if not _flag_present(j("_ops", "OCTOPUS-flags.cmd"), "OCTOPUS_WIRE_MISSION_RUNNER"):
        broken.append({"sev": "yellow", "msg": "دکمهٔ 🧪 غیرواقعی (فلگِ mission_runner خاموش)"})
    try:
        reds = [l["label"] for l in ov.legs_status(j("_ops", "state")) if l["rag"] == "red"]
        for lbl in reds:
            broken.append({"sev": "orange", "msg": f"پای قرمز: {lbl}"})
    except Exception:
        pass

    # ── duplicates / competing ──
    if _exists(j("octopus_core")):
        duplicates.append({"sev": "yellow", "msg": "octopus_core (پیاده‌سازیِ رقیب، صفر import) → ARCHIVE"})
    if _exists(j("07 - Knowledge", "genome-system")):
        duplicates.append({"sev": "yellow", "msg": "genome-system (.git مستقل) → DECIDE"})

    # ── dead UI ──
    if _exists(j("_ops", "telegram_center", "actions.py")):
        dead_ui.append({"sev": "grey", "msg": "actions.py یتیم (جایگزین: owner_menu) → MERGE/DELETE"})

    return {"errors": errors, "broken": broken, "duplicates": duplicates, "dead_ui": dead_ui}


def total_findings(f: Dict[str, List[Dict[str, str]]]) -> int:
    return sum(len(v) for v in f.values())


_SEV = {"red": "🔴", "orange": "🟠", "yellow": "🟡", "grey": "⚪"}


def render_debug(f: Dict[str, List[Dict[str, str]]]) -> str:
    if total_findings(f) == 0:
        return "⑤ گزارش و دیباگ: همه‌چیز تمیز است ✅"
    titles = {"errors": "خطاها", "broken": "اتصالِ قطع", "duplicates": "کارِ تکراری", "dead_ui": "UIِ زائد"}
    lines = [f"⑤ گزارش و دیباگ — {total_findings(f)} یافته:"]
    for cat in ("errors", "broken", "duplicates", "dead_ui"):
        for it in f[cat]:
            lines.append(f"{_SEV.get(it['sev'], '•')} [{titles[cat]}] {it['msg']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_debug(scan()))
