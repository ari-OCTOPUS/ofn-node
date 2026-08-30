#!/usr/bin/env python3
"""vault_updater_apply.py — «EffectorGate» که PATCH PROPOSALِ gate-passed را commit می‌کند.

رأی مالک: «EffectorGate تنها نویسنده.» این تنها نقطه‌ای است که proposalِ vault-updater را
واقعاً روی دیسکِ vault می‌نویسد — و فقط با گاردهای چندلایه، append-only، idempotent، ledger‌دار.

قفل‌های چندلایه (هر تخطی → refuse):
  ۱) `vault_updater_gate.validate` باید پاس شود (validatorِ مستقل).
  ۲) commit_mode باید AUTO باشد (GATE/HOLD → رأیِ مالک، هرگز اینجا).
  ۳) پرچمِ مالک `ACTIVATION-SELF-IMPROVE-AUTO` + `OCTOPUS_WIRE_VAULT_AUTO_WRITE=1`.
  ۴) Ring باید ∈ {3,4} باشد (Ring0/1 هرگز؛ gate هم می‌گیرد، این دومین چک است).
  ۵) create فقط در Ring 4 (inbox — capture ماشینیِ مجازِ قانون اساسی §۵)؛ append فقط به
     نوتِ dedup-matchedِ موجود. نوتِ دامنهٔ نو بدونِ match ساخته نمی‌شود.
  ۶) kill-switch/FREEZE اول.
  ۷) idempotent: اگر متن از قبل در نوت باشد → no-op (بدونِ تکرار).
  ۸) arm_gate.guard('self_improve_auto') (۲۰۲۶-۰۸-۰۴، DR-001) — اگر مالک
     OCTOPUS_ARM_SENSITIVE_DEFAULT=1 کرد، یک arm-token تازهٔ دوکلیدی لازم است؛
     پیش‌فرض بدونِ اثر.
هرگز delete/overwrite. پیش‌فرض **خاموش** (پرچم نباشد → آماده ولی ساکت). $0 · stdlib.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib               # noqa: E402
import vault_updater_gate as gate  # noqa: E402
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import arm_gate              # noqa: E402

ACT_AUTO = opslib.OPS / "ACTIVATION-SELF-IMPROVE-AUTO.flag"
FLAG_ENV = "OCTOPUS_WIRE_VAULT_AUTO_WRITE"
_PROJECTF_RE = re.compile(r"اونلی|onlyfans|Project-F", re.I)


def _vault_root() -> Path:
    return Path(os.environ.get("ORG_ROOT", str(opslib.ORG_ROOT)))


def enabled() -> bool:
    return ACT_AUTO.exists() and os.environ.get(FLAG_ENV) == "1"


def _refuse(reason: str) -> dict:
    return {"ok": False, "applied": False, "reason": reason}


def apply(proposal: dict) -> dict:
    """proposalِ AUTOِ gate-passed را commit کن. هر شکست/شرطِ نامحقق → refuse (بی‌خطر)."""
    # ۶) kill-switch اول
    if opslib.STOP_ORGANISM.exists() or opslib.halted() or opslib.frozen():
        return _refuse("kill-switch/FREEZE")
    # ۳) مجوز
    if not enabled():
        return _refuse(f"غیرفعال — نیازِ {FLAG_ENV}=1 + ACTIVATION-SELF-IMPROVE-AUTO")
    # ۱) validatorِ مستقل
    ok, errs = gate.validate(proposal)
    if not ok:
        return _refuse(f"gate رد کرد: {errs[:3]}")
    # ۲) فقط AUTO
    if proposal.get("commit_mode") != "AUTO" or proposal.get("status") != "OK":
        return _refuse("فقط commit_mode=AUTO اینجا commit می‌شود (بقیه رأیِ مالک)")
    ring = (proposal.get("classification") or {}).get("target_ring")
    tgt = str(proposal.get("target_path", ""))
    # ۴) Ring 0/1 هرگز + Project-F هرگز
    if ring not in (3, 4):
        return _refuse(f"Ring {ring} خارج از دامنهٔ AUTO (فقط ۳/۴)")
    if _PROJECTF_RE.search(tgt):
        return _refuse("Project-F → containment")
    # ضدِ traversal + فقط .md درونِ vault
    try:
        patch = json.loads(proposal["patch"]) if isinstance(proposal["patch"], str) else proposal["patch"]
    except (ValueError, TypeError):
        return _refuse("patch ناخوانا")
    op = patch.get("op")
    rel = str(patch.get("path", tgt)).replace("\\", "/")
    if ".." in rel or rel.startswith("/") or not rel.endswith(".md"):
        return _refuse("مسیرِ نامعتبر/غیرِ.md")
    dest = (_vault_root() / rel).resolve()
    if not str(dest).startswith(str(_vault_root().resolve())):
        return _refuse("خارج از vault (traversal)")
    # ۵) create فقط Ring4؛ append فقط به موجود
    content = str(patch.get("content", "")).strip()
    if not content:
        return _refuse("محتوای خالی")
    exists = dest.exists()
    if op == "create":
        if ring != 4:
            return _refuse("create فقط در inbox (Ring4)؛ دامنه نیازِ dedup-match")
        if exists:
            op = "append"   # از قبل هست → append (نه overwrite)
    if op == "append" and not exists and ring != 4:
        return _refuse("append به نوتِ ناموجودِ دامنه ممنوع")
    if op not in ("create", "append"):
        return _refuse(f"opِ غیرمجازِ applier: {op}")
    # ۷) idempotent + append-only write
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        prev = dest.read_text("utf-8") if dest.exists() else ""
        if content in prev:
            return {"ok": True, "applied": False, "reason": "idempotent-noop",
                    "path": rel}
        # گیتِ اضافیِ arm_gate (۲۰۲۶-۰۸-۰۴، DR-001): defense-in-depth روی همین
        # capabilityِ self_improve_auto که arm_gate.DANGEROUS از قبل تعریف کرده
        # بود — فقط سخت‌تر می‌کند، هرگز شل‌تر؛ پیش‌فرض بدونِ اثر. بعدِ چکِ
        # idempotent عمداً است: یک no-op که چیزی عوض نمی‌کند نیازِ arm-token ندارد.
        _arm_ok, _arm_why = arm_gate.guard("self_improve_auto")
        if not _arm_ok:
            return _refuse(f"arm-gate-denied:{_arm_why}")
        block = (prev + ("\n\n" if prev.strip() else "")
                 + f"<!-- auto {opslib.now_iso()} (vault-updater) -->\n" + content + "\n")
        tmp = dest.with_suffix(".md.tmp")
        tmp.write_text(block, "utf-8")
        os.replace(tmp, dest)
        opslib.ledger_note("VAULT_AUTO_WRITE",
                           {"path": rel, "op": op,
                            "after_hash": (proposal.get("ledger_entry") or {}).get("after_hash"),
                            "provenance": (proposal.get("ledger_entry") or {}).get("provenance")},
                           actor="vault-updater-effector")
    except OSError as e:
        return _refuse(f"write failed: {type(e).__name__}")
    return {"ok": True, "applied": True, "path": rel, "op": op}


if __name__ == "__main__":
    print(json.dumps({"enabled": enabled(), "vault_root": str(_vault_root())},
                     ensure_ascii=False, indent=2))
