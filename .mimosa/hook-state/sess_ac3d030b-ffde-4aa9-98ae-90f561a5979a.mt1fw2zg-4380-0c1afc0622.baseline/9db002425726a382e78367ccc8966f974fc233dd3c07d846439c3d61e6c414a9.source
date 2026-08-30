#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blackbox_map.py — نقشهٔ جعبه‌سیاه‌ها: چه کمکی می‌کنند، از چه بهتر/بدترند.

فقط‌خواندنی. هیچ فایلِ ممنوعه‌ای را باز نمی‌کند (Partner/PII/Identity/.env/secret).
برای مسیرهای خارج از F:\\backup فقط metadataِ اعلامی (SAYS) گزارش می‌شود مگر
مالک ROMAJAN_LAB_PATH / BLACKBOX_ROOT را بدهد و دسترسی موجود باشد.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

FLAG = "OCTOPUS_WIRE_BLACKBOX_MAP"
_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state"
VAULT = _HERE.parent

# مسیرهایی که هرگز نباید باز/لیست/هش شوند
_FORBIDDEN_SUBSTR = (
    "partner", "pii", "identity", ".env", "secret", "credential",
    "wallet", "seed", "id_rsa", ".pem", ".key", "owner-profile",
)


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _forbidden(p: str | Path) -> bool:
    s = str(p).lower().replace("\\", "/")
    return any(x in s for x in _FORBIDDEN_SUBSTR)


# ─── کاتالوگِ اعلامی (SAYS از اسنادِ vault؛ VERIFY جدا) ───────────────────────
CATALOG: list[dict] = [
    {
        "id": "nbb_black_box",
        "path_declared": r"F:\_______Black Box",
        "also_known_as": [r"F:\Black Box"],
        "what": "NBB Control Plane / Second Brain Super-Governor (relocated 2026-07-11)",
        "helps": [
            "12 invariantِ قانون‌اساسی برای spawn/replication",
            "ledgerِ hash-chained",
            "لایه‌های l0_kernel / l1_adapters / l2_replay",
            "تاریخچهٔ bundle (اگر verify شود)",
        ],
        "better_than": ["ad-hoc agent without constitution", "prompt-only governor"],
        "worse_than": ["live F:\\backup\\_ops with git + tests + telemetry"],
        "risks": [
            "NO GIT در root اعلام شده — تاریخچه ممکن است فقط در bundle باشد",
            "2.8GB / 599 files → احتمالاً venv/weights/logs نه سورس",
            "doc drift: 171 vs 207 tests",
            "path rename Black Box → _______Black Box = dangling refs",
        ],
        "irreplaceable_if": "bundle + unique NBB tests not copied into backup\\4d_system\\src\\nbb_cp",
        "verify_in_vault": [
            r"F:\backup\4d_system\BLACK-BOX.md",
            r"F:\backup\4d_system\src\nbb_cp",
            r"F:\backup\NBB-Project-Scan-2026-07-11\SCAN.txt",
        ],
        "status_default": "DORMANT_EXTERNAL",
    },
    {
        "id": "4d_system_in_vault",
        "path_declared": r"F:\backup\4d_system",
        "what": "مغزِ پژوهشیِ SOG + Brain-OS + کپیِ nbb_cp (DEPRECATED 2026-07-18)",
        "helps": [
            "اتحادِ E_shadow + Δ_self",
            "چرخهٔ meditate: explore→introspect→conclude→guard",
            "کدِ nbb_cp قابلِ پیوند به _ops",
        ],
        "better_than": ["lost USB notes", "chat history without files"],
        "worse_than": ["_ops/cortex/cortex.py (canonical live brain)"],
        "risks": ["DEPRECATED — وصل به ارگانیسمِ زنده نیست", "دو درخت 4d_system روی F:"],
        "irreplaceable_if": "unique math in core\\ not ported to _ops",
        "verify_in_vault": [
            r"F:\backup\4d_system\DEPRECATED.md",
            r"F:\backup\4d_system\PROJECT_STATE.md",
        ],
        "status_default": "ARCHIVED_IN_VAULT",
    },
    {
        "id": "romajan_lab",
        "path_declared": r"F:\romajan",
        "what": "آزمایشگاهِ propagation: PSLQ + SINDy + evalharness + evolution_lab",
        "helps": [
            "فرضیهٔ ریاضیِ ابطال‌پذیر برای C6",
            "ground-truthِ partition/Ramanujan",
            "NO-GOِ صادقانهٔ evolution_lab",
        ],
        "better_than": ["LLM-invented formulas without holdout"],
        "worse_than": ["peer-reviewed CAS library with CI"],
        "risks": ["خارج از gitِ backup تا genesis", "schema drift در claims_ledger"],
        "irreplaceable_if": "unique claims not exported",
        "verify_in_vault": [],
        "status_default": "EXTERNAL_LAB",
    },
    {
        "id": "c6_live_loop",
        "path_declared": r"F:\backup\_ops\c6_trigger.py",
        "what": "حلقهٔ خودبهبودیِ propose-only روی فرضیه‌های mechanism_count",
        "helps": ["آزمایشِ روزانه", "ضد green-lie", "writeback به thesis ledger"],
        "better_than": ["ungoverned self-modifying agents"],
        "worse_than": ["DGM open archive with human review at scale"],
        "risks": ["بدون PRODUCER flag = یک seedِ جعلی", "بدون ACTIVATION flag = dark"],
        "irreplaceable_if": "queue + ledger history",
        "verify_in_vault": [
            r"F:\backup\_ops\c6_trigger.py",
            r"F:\backup\_ops\c6_producer.py",
            r"F:\backup\_ops\c6_probes.py",
        ],
        "status_default": "LIVE_GATED",
    },
    {
        "id": "coherence_organ",
        "path_declared": r"F:\backup\_ops\coherence.py",
        "what": "پروبِ انسجام: شکارِ ادعاهایی که نمی‌توانند غلط باشند",
        "helps": ["ضد تئاترِ متریک", "زبانِ مشترک با thesis ledger"],
        "better_than": ["dashboard vanity metrics"],
        "worse_than": ["formal proof of observability"],
        "risks": ["flag-off = unused organ"],
        "irreplaceable_if": "unique verdict taxonomy",
        "verify_in_vault": [r"F:\backup\_ops\coherence.py"],
        "status_default": "LIVE_GATED",
    },
]


def _exists_safe(p: str | Path) -> str:
    if _forbidden(p):
        return "forbidden"
    try:
        path = Path(p)
        if path.exists():
            return "exists"
        return "missing"
    except Exception:  # noqa: BLE001
        return "unreadable"


def survey() -> dict:
    """وضعیتِ هر جعبه‌سیاه نسبت به vaultِ در دسترس."""
    out = []
    for item in CATALOG:
        rec = dict(item)
        root = item["path_declared"]
        if item["id"] == "romajan_lab":
            root = os.environ.get("ROMAJAN_LAB_PATH", root)
        if item["id"] == "nbb_black_box":
            root = os.environ.get("BLACKBOX_ROOT", root)
        rec["path_resolved"] = root
        rec["root_status"] = _exists_safe(root)
        vstatus = []
        for vp in item.get("verify_in_vault") or []:
            vstatus.append({"path": vp, "status": _exists_safe(vp)})
        rec["vault_evidence"] = vstatus
        # verdict
        if rec["root_status"] == "exists":
            rec["live"] = True
        elif any(v["status"] == "exists" for v in vstatus):
            rec["live"] = "partial-in-vault"
        else:
            rec["live"] = False
        out.append(rec)
    return {
        "n": len(out),
        "items": out,
        "rule": "helps/better/worse are design claims; live=filesystem presence only",
    }


def card() -> str:
    rep = survey()
    lines = ["📦 نقشهٔ جعبه‌سیاه‌ها", f"n={rep['n']}"]
    for it in rep["items"]:
        live = it.get("live")
        mark = "✅" if live is True else ("🟡" if live == "partial-in-vault" else "⚪")
        lines.append(f"{mark} {it['id']}: {it['what'][:70]}")
        lines.append(f"   path={it.get('path_resolved')} ({it.get('root_status')})")
        helps = it.get("helps") or []
        if helps:
            lines.append("   + " + helps[0][:80])
        risks = it.get("risks") or []
        if risks:
            lines.append("   ! " + risks[0][:80])
    lines.append("جزئیات: /box <id>  |  مقایسه: better_than/worse_than در detail")
    return "\n".join(lines)


def detail_card(box_id: str) -> str:
    bid = str(box_id or "").strip().lower().replace(" ", "_")
    rep = survey()
    it = next((x for x in rep["items"] if x["id"] == bid or bid in x["id"]), None)
    if not it:
        return "جعبهٔ ناشناخته. idها: " + ", ".join(x["id"] for x in rep["items"])
    lines = [
        f"📦 {it['id']}",
        it["what"],
        f"path: {it.get('path_resolved')} ({it.get('root_status')})",
        f"live: {it.get('live')}",
        "کمک:",
    ]
    for h in it.get("helps") or []:
        lines.append(f"  + {h}")
    lines.append("بهتر از: " + "; ".join(it.get("better_than") or []))
    lines.append("بدتر از: " + "; ".join(it.get("worse_than") or []))
    lines.append("ریسک:")
    for r in it.get("risks") or []:
        lines.append(f"  ! {r}")
    lines.append(f"irreplaceable_if: {it.get('irreplaceable_if')}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(card())
