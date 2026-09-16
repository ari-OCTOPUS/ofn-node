#!/usr/bin/env python3
"""executor — تنها جایی که واقعاً کاری می‌کند. و عمداً کمترین کارِ ممکن.

در این دور فقط دو کلاس اجرا می‌شوند:

    A0  خواندنِ فایلِ محلیِ داخلِ sandbox / مشاهدهٔ سنجه
    A1  نوشتنِ artifact داخلِ sandbox

هر چیز دیگری — A2 تا A6 — بدونِ استثنا به رسیدِ `BLOCKED`/`REJECTED` می‌رسد و
**هیچ تابعی برای انجامش وجود ندارد**. این تفاوت مهم است: «فلگش خاموش است» یعنی
کد هست و منتظر؛ «تابعش نوشته نشده» یعنی مسیر ساختاراً غایب است. برای A4/A5
دومی را انتخاب کردم.

سه ناوردی که در هر مسیر برقرارند و تست‌شان می‌کند:
    external_effects == []      همیشه، در همهٔ مسیرها
    cost == 0                   همیشه
    artifact ⊂ sandbox          هر فایلِ نوشته‌شده داخلِ ریشه

استثنای اجراکننده = `FAILED`، نه `EXECUTED`. و رسیدِ ننشسته وضعیت را پایین
می‌آورد (`receipt.finalize`).

$0 · stdlib · صفر شبکه · صفر پول · صفر اثرِ بیرونی.
"""
from __future__ import annotations

import json
from pathlib import Path

import contracts
import receipt as receipt_mod
import rollback as rollback_mod
import scope_guard

# نامِ کلاس‌هایی که این اجراکننده **می‌تواند** انجام دهد. بقیه مسیر ندارند.
EXECUTABLE = frozenset({"A0", "A1"})

_BLOCK_STATUS = {"BLOCK": "BLOCKED", "REJECT": "REJECTED",
                 "OWNER_GATE": "BLOCKED"}


def execute(req: dict, plan: dict, *, sandbox_root, receipts_dir,
            ledger_path, now_iso: str = "", dry_run: bool = True) -> dict:
    """اجرا طبقِ نقشه. خروجی: {receipt, ok}.

    `dry_run=True` پیش‌فرض است: در این حالت حتی A1 هم فایل نمی‌نویسد و فقط
    مسیرِ مقصد را در `artifacts` گزارش می‌کند. صداکننده باید **صریح** خلافش را
    بخواهد — پیش‌فرضِ امن، نه پیش‌فرضِ راحت."""
    started = now_iso
    aid = str((req or {}).get("action_id") or "unknown")
    cls = str((plan or {}).get("classification") or "A6")
    decision = str((plan or {}).get("decision") or "REJECT")
    key = str((plan or {}).get("idempotency_key") or "")

    def _fin(status, **kw):
        rec = contracts.new_receipt(
            action_id=aid, idempotency_key=key, status=status,
            classification=cls, started_at=started, finished_at=now_iso,
            external_effects=[], cost=0, **kw)
        return receipt_mod.finalize(rec, receipts_dir=receipts_dir,
                                    ledger_path=ledger_path)

    # نقشهٔ بدشکل = هیچ اجرایی
    pv = contracts.validate_plan(plan)
    if not pv["ok"]:
        return _fin("REJECTED", errors=["invalid-plan"] + pv["errors"][:4])

    if decision != "ALLOW":
        # NOOP ِ تکراری از BLOCK ِ واقعی جدا می‌ماند — وگرنه کارتِ نمره
        # «جلوگیری شد» و «قبلاً شده بود» را یکی می‌شمارد.
        if str(plan.get("reason") or "").startswith("duplicate-noop"):
            return _fin("NOOP", errors=[], evidence=[{"why": "idempotent-replay"}])
        return _fin(_BLOCK_STATUS.get(decision, "BLOCKED"),
                    errors=[str(plan.get("reason") or "")[:200]])

    if cls not in EXECUTABLE:
        # ALLOW روی کلاسی که مسیرِ اجرا ندارد = نقصِ سیاست، نه اجازه
        return _fin("BLOCKED",
                    errors=[f"no-executor-path-for:{cls}"])

    try:
        if cls == "A0":
            out = _observe(req, sandbox_root=sandbox_root)
        else:
            out = _write_artifact(req, sandbox_root=sandbox_root,
                                  dry_run=dry_run)
    except Exception as e:  # noqa: BLE001 — استثنا = FAILED، هرگز EXECUTED
        return _fin("FAILED", errors=[f"executor-exception:{type(e).__name__}: {e}"[:300]])

    if not out.get("ok"):
        return _fin("FAILED", errors=[str(out.get("reason"))[:200]],
                    steps_completed=out.get("steps", []))

    arts = out.get("artifacts", [])
    rb = rollback_mod.plan_for(arts, sandbox_root=sandbox_root)
    return _fin("EXECUTED", steps_completed=out.get("steps", []),
                artifacts=arts, before=out.get("before", {}),
                after=out.get("after", {}),
                rollback_available=bool(rb["available"]),
                evidence=out.get("evidence", []))


def _observe(req: dict, *, sandbox_root) -> dict:
    """A0 — خواندن. هیچ نوشتنی، حتی لاگ."""
    target = str(req.get("target") or "")
    sc = scope_guard.check(target, sandbox_root=sandbox_root,
                           allowed_scope=req.get("allowed_scope"))
    if not sc["ok"]:
        return {"ok": False, "reason": f"scope:{sc['reason']}"}
    p = Path(sc["resolved"])
    if not p.exists():
        # غیاب یک **مشاهدهٔ معتبر** است، نه شکست — و صریح ثبت می‌شود تا
        # «نبود» با «نخواندم» یکی نشود.
        return {"ok": True, "steps": [{"op": "observe", "result": "absent"}],
                "evidence": [{"path": sc["rel"], "exists": False}],
                "artifacts": []}
    try:
        raw = p.read_text("utf-8")
    except OSError as e:
        return {"ok": False, "reason": f"read-failed:{type(e).__name__}"}
    return {"ok": True,
            "steps": [{"op": "observe", "result": "read"}],
            "evidence": [{"path": sc["rel"], "exists": True,
                          "bytes": len(raw.encode("utf-8"))}],
            "artifacts": []}


def _write_artifact(req: dict, *, sandbox_root, dry_run: bool) -> dict:
    """A1 — ساختِ artifact. فقط داخلِ sandbox، فقط با محتوای اعلام‌شده."""
    target = str(req.get("target") or "")
    sc = scope_guard.check(target, sandbox_root=sandbox_root,
                           allowed_scope=req.get("allowed_scope"))
    if not sc["ok"]:
        return {"ok": False, "reason": f"scope:{sc['reason']}"}
    body = req.get("payload")
    if body is None:
        return {"ok": False, "reason": "no-payload"}
    text = body if isinstance(body, str) else json.dumps(
        body, ensure_ascii=False, indent=1)
    p = Path(sc["resolved"])
    if dry_run:
        return {"ok": True,
                "steps": [{"op": "write_artifact", "result": "dry-run"}],
                "artifacts": [{"path": str(p), "bytes": len(text.encode("utf-8")),
                               "written": False}],
                "evidence": [{"path": sc["rel"], "dry_run": True}]}
    w = receipt_mod._atomic_write(p, text)
    if not w["ok"]:
        return {"ok": False, "reason": f"write-failed:{w.get('error')}"}
    return {"ok": True,
            "steps": [{"op": "write_artifact", "result": "written"}],
            "artifacts": [{"path": str(p), "bytes": len(text.encode("utf-8")),
                           "written": True}],
            "evidence": [{"path": sc["rel"], "dry_run": False}]}
