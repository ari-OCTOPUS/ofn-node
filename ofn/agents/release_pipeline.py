"""release_pipeline — پلِ OwnerRelease → ارسال واقعی (M5، Round 31؛ P03 بازنویسی).

قبل از این ماژول: OwnerRelease در kernel بود (کامل، ۱۱ گیت fail-closed)
ولی هیچ تولیدکننده/مصرف‌کننده‌ای نداشت — همان الگوی «بساز و فراموش کن».

نسخهٔ ۲۰۲۶-۰۹-۰۴ (P03 / A08): هر هفت نقص نسخهٔ قبلی بسته شد —
  ۱. bool(step_token) تأیید نبود → توکن‌ها approval_id:code واقعی از
     owner_approvals هستند؛ two-step، bound به payload، expiry ۲۴ساعت.
  ۲-۳. consent/platform/rate/idempotency/ledger ثابت True نبودند → همه از
     منبع واقعی خوانده می‌شوند (consent_store/سقف کارگر/گیتِ اثر).
  ۴. secret_rotation/partner_precondition پیش‌فرض True نبودند → از
     config.load() (closed_gates واقعی، همان الگوی node.py).
  ۵. gate=None به send_one داده نمی‌شود → EffectGate واقعی.
  ۶. effect_id مبتنی بر زمان نبود → hash پایدار lead+draft (retry-stable).
  ۷. ok=True مستقل از sent برنمی‌گردد → نتیجه چهاروضعیتی
     passed/rejected/failed/unknown + dry_run برچسب‌دار.

قواعد آهنان:
  · هرگز بدون دو مرحله تأیید مالک ارسال نمی‌کند (OwnerRelease + approval store)
  · هرگز بدون conservation-بودن ارسال نمی‌کند (outbound_worker بلوک می‌کند)
  · هرگز بدون سقف روزانه ارسال نمی‌کند
  · هر رسید append-only است (state/legs/release-pipeline.jsonl)
  · هر خطا fail-closed است با رسیدِ دقیق چرایی
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parents[1]))
import opslib  # noqa: E402

SCHEMA = "octopus.release-pipeline.v2"
RECEIPTS = opslib.STATE_DIR / "legs" / "release-pipeline.jsonl"


def _append_receipt(entry: dict) -> None:
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    entry.setdefault("at", opslib.now_iso())
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def stable_effect_id(lead_id: str, draft_text: str) -> str:
    """Retry-stable effect identity: the same lead+draft is the SAME effect,
    no matter which second it is minted in. The lead_effect_gate makes the
    second use a hard duplicate."""
    h = hashlib.sha256(
        f"{lead_id}\n{draft_text}".encode("utf-8")).hexdigest()[:16]
    return f"release-{lead_id}-{h}"


def build_release_context(
    *,
    owner_confirmed_step1: bool,
    owner_confirmed_step2: bool,
    kill_switch_active: bool = False,
    secret_rotation_open: bool = False,       # fail-closed default (was True)
    partner_precondition_open: bool = False,  # fail-closed default (was True)
    sensitivity: str = "general",
    consent_ok: bool = False,                 # fail-closed default
    platform_ok: bool = False,
    rate_limit_ok: bool = False,
    idempotency_unused: bool = False,
    ledger_ready: bool = False,
) -> dict[str, Any]:
    """ساخت ReleaseContext — همهٔ فیلدها صریح؛ پیش‌فرض‌ها fail-closed."""
    from ofn.kernel.release_switch import ReleaseContext
    return ReleaseContext(
        kill_switch_active=kill_switch_active,
        owner_confirmed_step1=owner_confirmed_step1,
        owner_confirmed_step2=owner_confirmed_step2,
        secret_rotation_open=secret_rotation_open,
        partner_precondition_open=partner_precondition_open,
        sensitivity=sensitivity,
        consent_ok=consent_ok,
        platform_ok=platform_ok,
        rate_limit_ok=rate_limit_ok,
        idempotency_unused=idempotency_unused,
        ledger_ready=ledger_ready,
    )


class EffectGate:
    """Real per-effect gate for send_one (replaces gate=None).

    Fourth independent policy layer after the worker belt (halt/flag/
    conservation/cap) and consent layer 3. It re-derives, from live state:
    master halt, suppression on the recipient, and payload sanity. It owns
    no approval semantics — the two-step lives in the kernel context.
    """

    def release(self, effect_id: str, candidate: dict) -> tuple[bool, str]:
        lead_id = str((candidate or {}).get("lead_id") or "")
        if not lead_id:
            return False, "gate:no-lead"
        if not str((candidate or {}).get("draft_sha256") or ""):
            return False, "gate:no-payload-hash"
        halted = opslib.master_halted()
        if halted:
            return False, f"gate:halted:{halted}"
        try:
            import consent_gate as _cg  # noqa: WPS433
            import consent_store as _cs  # noqa: WPS433
            store = _cs.ConsentStore()
            try:
                ok, why = _cg.may_release(lead_id, "lead_outbound",
                                          store=store)
            finally:
                store.close()
            if not ok:
                return False, f"gate:{why}"
        except Exception as e:  # noqa: BLE001 — fail-closed
            return False, f"gate:consent-unavailable:{type(e).__name__}"
        return True, "gate:ok"


def _config_gates_open() -> tuple[bool, bool]:
    """secret_rotation / partner_precondition from the REAL closed-gates
    config (same source as node.py) — never a hardcoded True."""
    from ofn.config import load
    closed = set(getattr(load(), "base_closed_gates", ()) or ())
    return ("secret_rotation" not in closed,
            "partner_precondition" not in closed)


def _consent_ok(lead_id: str) -> tuple[bool, str]:
    import consent_gate as _cg  # noqa: WPS433
    return _cg.may_release(lead_id, "lead_outbound")


def _platform_ok(platform: str) -> bool:
    """The only wired lead channel is email; its screen is a real resolved
    transport credential plus the (un)suppressed recipient. Social/content
    platforms are a different path (platform_matrix), not this pipeline."""
    if str(platform).casefold() != "email":
        return False
    try:
        import mail_credentials as _mc  # noqa: WPS433
        cr = _mc.resolve()
        return bool(cr and cr.get("ok"))
    except Exception:  # noqa: BLE001
        return False


def _rate_limit_ok(now_s: float | None) -> bool:
    import outbound_worker as _ow  # noqa: WPS433
    return _ow.sends_today(now=now_s) < _ow.LEAD_DAILY_SEND_CAP


def _ledger_ready() -> bool:
    import lead_effect_gate as _leg  # noqa: WPS433
    return _leg.ledger_ready()


def _idempotency_unused(effect_id: str) -> bool:
    import lead_effect_gate as _leg  # noqa: WPS433
    return _leg.status(effect_id) is None


def _parse_token(token: str) -> tuple[str, str]:
    """token format: '<approval_id>:<step_code>' — anything else is invalid."""
    parts = str(token or "").split(":", 1)
    if len(parts) != 2 or not all(parts):
        return "", ""
    return parts[0], parts[1]


def _policy_context(lead_id: str, draft_text: str, platform: str,
                    effect_id: str, *, owner1: bool, owner2: bool,
                    kill: bool | None = None, now_s: float | None = None):
    """Real-source context. Owner flags and kill switch are injectable for
    the two verification shapes (pre-card / release)."""
    rot_open, partner_open = _config_gates_open()
    c_ok, _c_why = _consent_ok(lead_id)
    if kill is None:
        kill = bool(opslib.master_halted())
    return build_release_context(
        owner_confirmed_step1=owner1,
        owner_confirmed_step2=owner2,
        kill_switch_active=kill,
        secret_rotation_open=rot_open,
        partner_precondition_open=partner_open,
        sensitivity="general",
        consent_ok=c_ok,
        platform_ok=_platform_ok(platform),
        rate_limit_ok=_rate_limit_ok(now_s),
        idempotency_unused=_idempotency_unused(effect_id),
        ledger_ready=_ledger_ready(),
    )


def _policy_blocker(lead_id: str, draft_text: str, platform: str,
                    effect_id: str, *, owner1: bool, owner2: bool,
                    kill: bool | None = None,
                    now_s: float | None = None) -> str | None:
    """Run the kernel verdict; return the blocking rule or None.

    Ordering note: the kernel checks owner two-step BEFORE the per-item
    policy screens, so a pre-card pre-flight passes owner flags=True
    (presumed) to expose any POLICY refusal; the release-time call runs the
    full verdict with the genuinely-validated approval."""
    from ofn.kernel.release_switch import OwnerRelease
    ctx = _policy_context(lead_id, draft_text, platform, effect_id,
                          owner1=owner1, owner2=owner2, kill=kill,
                          now_s=now_s)
    verdict = OwnerRelease().may_publish(ctx)
    if verdict.ok:
        return None
    return verdict.rule


def pipeline(
    draft_text: str,
    *,
    step1_token: str = "",
    step2_token: str = "",
    lead_id: str,
    platform: str = "email",
    subject: str = "",
    dry_run: bool = True,
    now_s: float | None = None,
) -> dict:
    """چهار مرحله‌ای: draft → verify(policy) → card → (optional) release.

    step1_token/step2_token = '<approval_id>:<confirm_code>' — the codes the
    owner received on the card. Garbage strings validate to nothing.
    Result carries 'result': passed|rejected|failed|unknown|dry_run.
    """
    _append_receipt({"phase": "start", "lead_id": lead_id,
                     "dry_run": dry_run, "platform": platform})

    # ۱ — DRAFT
    if not draft_text or len(draft_text) < 10:
        _append_receipt({"phase": "draft", "ok": False,
                         "error": "draft-too-short"})
        return {"ok": False, "stage": "draft", "result": "rejected",
                "error": "draft_text must be ≥10 chars"}

    effect_id = stable_effect_id(lead_id, draft_text)

    # ۲ — VERIFY: policy pre-flight. Owner flags presumed True here ONLY to
    # expose policy refusals past the kernel's two-step ordering; nothing is
    # released on this basis — the real two-step is validated at RELEASE.
    try:
        blocking = _policy_blocker(lead_id, draft_text, platform, effect_id,
                                   owner1=True, owner2=True, kill=False,
                                   now_s=now_s)
    except Exception as e:  # noqa: BLE001
        _append_receipt({"phase": "verify", "ok": False,
                         "error": type(e).__name__})
        return {"ok": False, "stage": "verify", "result": "failed",
                "error": str(e)}
    _append_receipt({"phase": "verify", "effect_id": effect_id,
                     "policy_blocker": blocking})
    if blocking is not None:
        return {"ok": False, "stage": "verify", "result": "rejected",
                "rule": blocking,
                "error": f"OwnerRelease policy refused: {blocking}"}

    # ۳ — CARD (dry_run stops here, labeled; nothing is sent, ever).
    card = {
        "to": lead_id, "platform": platform,
        "text": draft_text[:500], "hold_external": True,
        "may_authorize": False, "needs": "owner APPROVE_ONCE",
        "effect_id": effect_id,
    }
    _append_receipt({"phase": "card",
                     "card": {**card, "text": card["text"][:80]}})
    if dry_run:
        return {"ok": True, "stage": "dry-run", "result": "dry_run",
                "message": "verified + card prepared; NOT sent (dry_run)",
                "effect_id": effect_id, "card": card}

    # ۳ب — APPROVAL: real two-step tokens bound to this exact payload.
    try:
        import owner_approvals as _oa  # noqa: WPS433
        aid1, code1 = _parse_token(step1_token)
        aid2, code2 = _parse_token(step2_token)
        if not aid1 or aid1 != aid2:
            _append_receipt({"phase": "approval", "ok": False,
                             "error": "approval-token-shape"})
            return {"ok": False, "stage": "release", "result": "rejected",
                    "error": "approval tokens must be '<approval_id>:<code>' pairs"}
        ok_appr, why_appr = _oa.validate(
            aid1, code1, code2, lead_id=lead_id, draft_text=draft_text,
            platform=platform, effect_id=effect_id, now=now_s)
        _append_receipt({"phase": "approval", "ok": ok_appr,
                         "approval_id": aid1, "reason": why_appr})
        if not ok_appr:
            return {"ok": False, "stage": "release", "result": "rejected",
                    "rule": why_appr,
                    "error": f"owner approval invalid: {why_appr}"}
    except Exception as e:  # noqa: BLE001
        _append_receipt({"phase": "approval", "ok": False,
                         "error": type(e).__name__})
        return {"ok": False, "stage": "release", "result": "failed",
                "error": str(e)}

    # ۴ — RELEASE: full kernel verdict with real owner confirmation, then
    # send_one through the REAL effect gate (never None).
    try:
        blocking = _policy_blocker(lead_id, draft_text, platform, effect_id,
                                   owner1=True, owner2=True, now_s=now_s)
    except Exception as e:  # noqa: BLE001
        _append_receipt({"phase": "verify", "ok": False,
                         "error": type(e).__name__})
        return {"ok": False, "stage": "verify", "result": "failed",
                "error": str(e)}
    if blocking is not None:
        return {"ok": False, "stage": "verify", "result": "rejected",
                "rule": blocking,
                "error": f"OwnerRelease refused: {blocking}"}

    import outbound_worker
    candidate = {"lead_id": lead_id,
                 "contact": {"preferred_channel": platform},
                 "effect_id": effect_id,
                 "draft_sha256": hashlib.sha256(
                     draft_text.encode("utf-8")).hexdigest(),
                 "subject": subject}
    res = outbound_worker.send_one(
        effect_id=effect_id,
        candidate=candidate,
        draft=draft_text,
        gate=EffectGate(),
    )
    sent = bool(res.get("sent"))
    status = str(res.get("status") or "")
    gate_reason = res.get("gate_reason")
    if sent:
        result, ok = "passed", True
    elif status == "worker_error":
        result, ok = "failed", False
    elif gate_reason == "idempotency:duplicate":
        result, ok = "rejected", False  # already settled once — never resend
    else:
        # cleared nothing / transport did not send (NOT_ARMED, SUPPRESSED,
        # CAP_REACHED, consent-denied, SEND_FAILED) — honest no-send.
        result, ok = "rejected", False
    _append_receipt({"phase": "release", "effect_id": effect_id,
                     "sent": sent, "status": status, "result": result})
    return {"ok": ok, "stage": "released", "result": result,
            "sent": sent, "status": status, "effect_id": effect_id,
            "gate_reason": gate_reason}


def issue_approval(draft_text: str, *, lead_id: str, platform: str = "email",
                   subject: str = "", now_s: float | None = None) -> dict:
    """CARD-stage helper: mint the approval record and return the owner-held
    confirm codes once (they travel to the owner channel only)."""
    import owner_approvals as _oa  # noqa: WPS433
    effect_id = stable_effect_id(lead_id, draft_text)
    appr = _oa.issue(lead_id=lead_id, draft_text=draft_text,
                     platform=platform, effect_id=effect_id)
    _append_receipt({"phase": "approval-issued", "approval_id": appr["approval_id"],
                     "effect_id": effect_id, "lead_id": lead_id})
    return {"approval_id": appr["approval_id"],
            "step1_code": appr["step1_code"],
            "step2_code": appr["step2_code"],
            "effect_id": effect_id}


def main() -> int:
    print(json.dumps({"schema": SCHEMA,
                      "note": "import as module; call pipeline()"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
