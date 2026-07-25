#!/usr/bin/env python3
"""
_ops/synapse/egress_policy.py — P1: سیاستِ egress به‌صورتِ deny-by-default.

درسِ ExploitGym: sandbox باید egress به اینترنت را «قابلیتِ محیطیِ پیش‌فرض»
نداشته باشد. این ماژول فقط **داده + توابعِ خالص** است؛ هیچ wiringای به رانتایم
در این جلسه انجام نشده (wiring = wrap کردنِ clientهای LLM/HTTP = tapِ مالک؛
پلن در _program-deliverables/AGI-CAPABILITY-GAP-ROADMAP-2026-07-24.md §P1).

قواعد:
  * پیش‌فرض: **deny** برای همه‌ی hostها به‌جز localhost (Ollama محلی).
  * DECLARED_ENDPOINTS: فهرستِ endpointهای مجازِ ابری per-purpose — [EST] است و
    باید با تأییدِ مالک از روی کانفیگ‌های واقعی پر شود، نه حدسِ ما. تا وقتی
    خالی است، هیچ egressِ ابری مجاز نیست (fail-closed).
  * OCTOPUS_EGRESS_ENFORCE=1 → تصمیم‌ها «enforced» علامت می‌خورند؛ ولی enforce
    واقعی نیازمند wiring است (این فایل به‌تنهایی هیچ ترافیکی را بلاک نمی‌کند).
  * OCTOPUS_EGRESS_AUDIT=1 → هر تصمیم در out/egress-audit.jsonl لاگ می‌شود.

مصرفِ LLM: صفر. بدونِ I/O شبکه‌ای.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

FLAG_ENFORCE = "OCTOPUS_EGRESS_ENFORCE"
FLAG_AUDIT = "OCTOPUS_EGRESS_AUDIT"

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

# [EST — نیازمند تأییدِ مالک] endpointهای اعلام‌شده‌ی LLM per-purpose.
# منابعِ کاندید برای پرکردن (owner-verified): _ops/OCTOPUS.env (بدونِ خواندنِ
# secrets)، 4d_system/llm/{ollama_client,fugu_client}.py، router.py.
# تا پر نشود: هیچ egressِ ابری مجاز نیست.
DECLARED_ENDPOINTS: dict[str, frozenset[str]] = {
    # "ollama": frozenset({"localhost:11434"}),
    # "deepseek": frozenset({"api.deepseek.com"}),
    # "glm": frozenset({"...مالک تأیید کند..."}),
    # "fugu": frozenset({"...مالک تأیید کند..."}),
}

_HERE = Path(__file__).resolve()
DEFAULT_AUDIT = _HERE.parent / "out" / "egress-audit.jsonl"


def _flag(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "yes", "on")


def enforce_on() -> bool:
    return _flag(FLAG_ENFORCE)


def normalize_host(host: object) -> str:
    """host را نرمال می‌کند: حذفِ scheme، حذفِ path، حروفِ کوچک، بدونِ پورت
    (پورت فقط برای localhost حفظ می‌شود تا 11434 قابلِ تشخیص بماند)."""
    h = str(host or "").strip().lower()
    for scheme in ("https://", "http://"):
        if h.startswith(scheme):
            h = h[len(scheme):]
            break
    h = h.split("/", 1)[0]
    return h


def is_allowed(host: object, purpose: str = "unknown") -> bool:
    """تصمیمِ خالص — deny-by-default:
    localhost همیشه مجاز؛ ابری فقط اگر در DECLARED_ENDPOINTSِ همان purpose باشد."""
    h = normalize_host(host)
    if not h:
        return False
    bare = h.split(":", 1)[0]
    if bare in LOCAL_HOSTS:
        return True
    allowed = DECLARED_ENDPOINTS.get(purpose, frozenset())
    return h in allowed or bare in {a.split(":", 1)[0] for a in allowed}


def decide(host: object, purpose: str = "unknown", audit_path: Path | None = None) -> dict:
    """تصمیم + متادیتا؛ با فلگِ AUDIT در out/egress-audit.jsonl لاگ می‌کند.
    هرگز raise نمی‌کند؛ fail-closed: ورودیِ بد → deny."""
    try:
        allowed = is_allowed(host, purpose)
    except Exception:
        allowed = False
    rec = {
        "schema": "egress.decision.v1",
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "host": normalize_host(host),
        "purpose": str(purpose or "unknown"),
        "allowed": bool(allowed),
        "enforced": enforce_on(),
    }
    if _flag(FLAG_AUDIT):
        try:
            ap = Path(audit_path) if audit_path else DEFAULT_AUDIT
            ap.parent.mkdir(parents=True, exist_ok=True)
            with ap.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return rec


def self_test() -> dict:
    checks: dict[str, bool] = {}
    checks["localhost_allowed"] = is_allowed("http://localhost:11434/api", "ollama") is True
    checks["loopback_allowed"] = is_allowed("127.0.0.1", "anything") is True
    checks["cloud_denied_by_default"] = is_allowed("api.deepseek.com", "deepseek") is False
    checks["unknown_purpose_denied"] = is_allowed("example.com", "unknown") is False
    checks["empty_host_denied"] = is_allowed("", "x") is False
    checks["garbage_denied"] = is_allowed(None, "x") is False
    # fail-closed روی purposeهای اعلام‌نشده حتی با hostِ معروف
    checks["declared_only"] = is_allowed("api.openai.com", "fugu") is False
    d = decide("https://example.com/x", "test")
    checks["decide_shape"] = set(d.keys()) == {"schema", "ts_utc", "host", "purpose", "allowed", "enforced"}
    checks["decide_denies"] = d["allowed"] is False
    checks["ALL"] = all(checks.values())
    return checks


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, indent=2))
