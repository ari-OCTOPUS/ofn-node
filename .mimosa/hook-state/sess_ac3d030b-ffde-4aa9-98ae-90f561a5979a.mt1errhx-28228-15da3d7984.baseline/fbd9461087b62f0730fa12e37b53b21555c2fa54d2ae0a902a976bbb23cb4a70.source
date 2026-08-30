#!/usr/bin/env python3
"""vault_updater_gate.py — validatorِ stdlib که PATCH PROPOSAL را **پیش از commit** می‌سنجد.

رأی مالک (α): «نسخهٔ JSON-Schema رسمیِ خروجی + یک validatorِ stdlib که gate قبل از commit
اجرا کند (هم‌سبکِ ۱۸ تستِ credential panel).» این دومین گاردِ مستقلِ ریل‌های سخت است:
حتی اگر proposer باگ داشته باشد، gate proposalِ ناامن را رد می‌کند (defense-in-depth).

قرارداد (JSON-Schema سبک، stdlib): کلیدها، enumها، و ریل‌های سخت.
fail-closed: هر تخطی → (False, [errors]). فقط proposalِ (True) اجازهٔ رفتن به writer دارد.
"""
from __future__ import annotations

import json
import re

STATUS = {"OK", "HOLD"}
MODES = {"AUTO", "GATE", "HOLD"}
RISKS = {"LOW", "REVIEW", "CRITICAL"}
KINDS = {"fact", "decision", "task", "reference", "insight"}
OPS = {"create", "append", "supersede"}          # هرگز delete/overwrite

REQUIRED = ("status", "classification", "target_path", "commit_mode", "risk",
            "dedup", "patch", "ledger_entry", "rationale")
_PROJECTF_RE = re.compile(r"اونلی|onlyfans|Project-F", re.I)


def validate(obj: dict) -> tuple[bool, list[str]]:
    """(ok, errors). فقط ok=True اجازهٔ commit می‌دهد."""
    e: list[str] = []
    if not isinstance(obj, dict):
        return False, ["proposal یک dict نیست"]
    for k in REQUIRED:
        if k not in obj:
            e.append(f"کلیدِ لازم غایب: {k}")
    if e:
        return False, e

    if obj["status"] not in STATUS:
        e.append(f"status نامعتبر: {obj['status']}")
    if obj["commit_mode"] not in MODES:
        e.append(f"commit_mode نامعتبر: {obj['commit_mode']}")
    if obj["risk"] not in RISKS:
        e.append(f"risk نامعتبر: {obj['risk']}")
    cls = obj.get("classification") or {}
    if cls.get("kind") not in KINDS:
        e.append(f"classification.kind نامعتبر: {cls.get('kind')}")
    ring = cls.get("target_ring")
    if not isinstance(ring, int) or not (0 <= ring <= 4):
        e.append(f"target_ring نامعتبر: {ring}")

    # ── ریل‌های سختِ تخطی‌ناپذیر ──────────────────────────────────────────────
    mode, risk = obj["commit_mode"], obj["risk"]
    # ۱) Ring 0/1 هرگز AUTO
    if isinstance(ring, int) and ring in (0, 1) and mode == "AUTO":
        e.append(f"ریلِ سخت: Ring{ring} هرگز AUTO نمی‌شود")
    # ۲) CRITICAL هرگز AUTO (هرگز downgrade/suppress)
    if risk == "CRITICAL" and mode == "AUTO":
        e.append("ریلِ سخت: CRITICAL هرگز AUTO نمی‌شود")
    # ۳) Project-F همیشه HOLD
    if _PROJECTF_RE.search(str(obj.get("target_path", ""))) and mode != "HOLD":
        e.append("ریلِ سخت: Project-F باید HOLD باشد")
    # ۴) OK باید patch + ledger معتبر داشته باشد؛ HOLD باید human_prompt داشته باشد
    if obj["status"] == "OK":
        try:
            patch = json.loads(obj["patch"]) if isinstance(obj["patch"], str) else obj["patch"]
            if patch.get("op") not in OPS:
                e.append(f"ریلِ سخت: opِ نامعتبر/مخرب: {patch.get('op')} (فقط {OPS})")
        except (ValueError, TypeError, AttributeError):
            e.append("patch قابلِ‌پارس نیست")
        led = obj.get("ledger_entry") or {}
        if not led.get("provenance"):
            e.append("ریلِ سخت: ledger بدونِ provenance (جعلِ منبع ممنوع)")
        if not led.get("after_hash"):
            e.append("ledger بدونِ after_hash")
    if mode in ("GATE", "HOLD") and not str(obj.get("human_prompt", "")).strip():
        e.append(f"{mode} باید human_prompt داشته باشد")
    # ۵) delete/overwrite در متنِ patch مطلقاً ممنوع (حتی اگر op درست بود)
    if re.search(r"\"op\"\s*:\s*\"(delete|overwrite|replace|remove)\"",
                 str(obj.get("patch", "")), re.I):
        e.append("ریلِ سخت: delete/overwrite در patch")

    return (not e), e


if __name__ == "__main__":
    import sys
    obj = json.loads(sys.stdin.read())
    ok, errs = validate(obj)
    print(json.dumps({"ok": ok, "errors": errs}, ensure_ascii=False, indent=2))
