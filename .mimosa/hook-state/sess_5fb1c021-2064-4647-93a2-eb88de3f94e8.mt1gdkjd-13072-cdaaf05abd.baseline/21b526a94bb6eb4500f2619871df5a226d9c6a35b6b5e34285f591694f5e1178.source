"""hardware_brain.py — 🛠 خلاصهٔ فقط‌خواندنیِ ناوگان از state (بدونِ تماس با نود)."""
from __future__ import annotations

# ۲۰۲۶-۰۸-۰۱ — «unknown» عمداً بیرون است. اگر جزوِ «وضعیتِ معلوم» بماند، رجیستری‌ای
# پر از نودِ اندازه‌گیری‌نشده `status_known=True` می‌دهد و `core.py` همان را مبنای
# `live` می‌گیرد — یعنی سیستم بدونِ یک اندازه‌گیریِ واقعی خودش را زنده اعلام می‌کند.
# خطِ قرمزِ ولت: scorerِ زنده جعل نمی‌شود.
_KNOWN = {"running", "broken"}
_THERMAL_C = 82  # آستانهٔ هشدارِ حرارتیِ RK3588


def summarize_fleet(fleet: dict) -> dict:
    nodes = fleet.get("nodes", []) if isinstance(fleet, dict) else []
    if not isinstance(nodes, list):
        nodes = []
    total = len(nodes)
    running = sum(1 for n in nodes if str(n.get("status", "")).lower() == "running")
    broken = sum(1 for n in nodes if str(n.get("status", "")).lower() == "broken")
    known = any(str(n.get("status", "")).lower() in _KNOWN for n in nodes)
    thermal = [n.get("id") for n in nodes
               if isinstance(n.get("temp_c"), (int, float)) and n["temp_c"] >= _THERMAL_C]
    return {
        "nodes_total": total,
        "running": running,
        "broken": broken,
        "unknown": total - running - broken,
        "status_known": known,
        "thermal_warn": thermal,
    }
