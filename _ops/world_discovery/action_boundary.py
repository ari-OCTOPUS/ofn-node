"""action_boundary.py — مرز عمل بیرونی و Owner Gate تلگرام.

بند ۱۳: هر اقدام بیرونی پیش از رأی در وضعیت BLOCKED_BY_OWNER است.
این ماژول:
- L0..L4 تعریف می‌کند.
- Owner Action Card می‌سازد.
- یک OwnerGate interface تعریف می‌کند که پیاده‌سازی تلگرامش در
  INTEGRATION-MANIFEST به approval_channel.send_text وصل می‌شود —
  ولی داخل کد فعال نیست تا پذیرش ایجنت ارشد.

هیچ فایل مشترکی ویرایش نمی‌شود. ارسال واقعی فقط با runner مستقل + رأی.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Protocol

from .contracts import OwnerActionCard, make_action_id

# سطوح عمل
L0 = "L0"  # فقط تحقیق و گزارش
L1 = "L1"  # تحقیق + ساخت artifact، بدون ارسال بیرونی
L2 = "L2"  # اجرای فقط روی داده/صفحات عمومی، بدون تماس
L3 = "L3"  # ساخت draft پیام/پیشنهاد، ارسال با رأی مالک
L4 = "L4"  # تماس یا ارسال خودکار

ALL_LEVELS = {L0, L1, L2, L3, L4}

# اقداماتی که بدون رأی تازه همیشه ممنوع‌اند
ALWAYS_FORBIDDEN = {
    "send-telegram", "send-email", "call-customer", "register-form",
    "create-account", "login-account", "buy-api", "spend", "advertise",
    "publish-public", "place-order", "sign-contract", "deploy", "merge",
    "push", "change-secret", "read-sensitive-personal", "scrape-tos-violation",
    "bypass-paywall", "bypass-captcha", "forge-identity", "fake-review",
    "fake-lead", "fake-revenue", "fake-claim", "metric-gaming",
    "edit-runtime-state",
}

# اقداماتی که در این مأموریت (L3) با رأی مالک مجازند
ALLOWED_WITH_VOTE = {"send-telegram"}


class PermissionDenied(Exception):
    """اقدام بیرونی بدون رأی انجام شد."""


# ──────────────────────────────────────────────────────
# Owner Action Card
# ──────────────────────────────────────────────────────
def make_owner_action_card(
    *,
    discovery_id: str,
    exact_action: str,
    why_needed: str,
    expected_information_gain: str = "",
    risk: str = "low",
    cost: str = "0 AUD",
    channel: str = "telegram",
    target_recipient: str = "owner",
    draft_message: str = "",
    ttl_hours: int = 48,
    now: Optional[datetime] = None,
) -> OwnerActionCard:
    """ساخت یک Owner Action Card با TTL و default do-not-execute."""
    now = now or datetime.now(timezone.utc)
    expires = (now + timedelta(hours=ttl_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    external = "send" in exact_action.lower() or channel != "none"

    return OwnerActionCard(
        action_id=make_action_id(discovery_id, exact_action),
        discovery_id=discovery_id,
        exact_action=exact_action,
        why_needed=why_needed,
        expected_information_gain=expected_information_gain,
        risk=risk,
        cost=cost,
        external_effect=external,
        channel=channel,
        target_recipient=target_recipient,
        draft_message=draft_message,
        expires_at=expires,
        default_without_approval="do-not-execute",
        status="BLOCKED_BY_OWNER",
    )


def card_expired(card: OwnerActionCard, *, now: Optional[datetime] = None) -> bool:
    """آیا Owner Action Card منقضی شده؟"""
    if not card.expires_at:
        return True
    now = now or datetime.now(timezone.utc)
    try:
        exp = datetime.strptime(card.expires_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    return now > exp


# ──────────────────────────────────────────────────────
# Level check
# ──────────────────────────────────────────────────────
def action_allowed(action: str, level: str, *, owner_voted: bool = False) -> bool:
    """آیا این action در این level مجاز است؟

    - ALWAYS_FORBIDDEN همیشه نیاز به رأی دارند (حتی در L4).
    - در L0..L2: هیچ send مجاز نیست.
    - در L3: send-telegram با رأی مالک مجاز است.
    - در L4: ارسال خودکار (ولی باز هم هزینه/حساب ممنوع).
    """
    if level not in ALL_LEVELS:
        return False

    # cost/spend/account همیشه ممنوع (طبق رأی مالک: خرج ممنوع)
    if action in {"spend", "buy-api", "create-account", "register-form",
                  "call-customer", "deploy", "merge", "push"}:
        return False

    if action == "send-telegram":
        if level in (L3, L4) and owner_voted:
            return True
        return False

    # actions سبک (read, compute, build-artifact)
    if action in {"read-public-data", "compute-metric", "build-artifact",
                  "build-draft", "write-local-report"}:
        # در همهٔ سطوح از L1 به بالا مجازند
        if level == L0 and action in {"build-artifact", "build-draft"}:
            return False
        return True

    # هر چیز دیگر → ممنوع مگر رأی صریح
    return False


def assert_action(action: str, level: str, *, owner_voted: bool = False) -> None:
    """raise اگر action مجاز نیست."""
    if not action_allowed(action, level, owner_voted=owner_voted):
        raise PermissionDenied(
            f"action '{action}' not allowed at level {level} "
            f"(owner_voted={owner_voted}). status=BLOCKED_BY_OWNER"
        )


# ──────────────────────────────────────────────────────
# OwnerGate interface (تلگرام در manifest وصل می‌شود)
# ──────────────────────────────────────────────────────
class OwnerGate(Protocol):
    """پروتکل owner gate.

    پیاده‌سازی واقعی (TelegramOwnerGate) در runtime ایجنت ارشد ساخته می‌شود
    و به approval_channel.send_text وصل می‌شود. تا آن زمان، یک
    NoOpOwnerGate همه را BLOCKED برمی‌گرداند.
    """

    def request(self, card: OwnerActionCard) -> dict:
        """ارسال Owner Action Card به مالک و بازگرداندان نتیجه.

        Returns: {approved: bool, vote_id: str, reason: str}
        default (بدون پیاده‌سازی): approved=False → BLOCKED_BY_OWNER.
        """
        ...


class NoOpOwnerGate:
    """پیاده‌سازی پیش‌فرض: همه را BLOCKED برمی‌گرداند (safe default).

    هیچ ارسالی انجام نمی‌دهد. این تضمین می‌کند که تا پیاده‌سازی واقعی،
    هیچ send واقعی اتفاق نمی‌افتد.
    """

    def request(self, card: OwnerActionCard) -> dict:
        return {
            "approved": False,
            "vote_id": "",
            "reason": (
                "NoOpOwnerGate active — no live telegram channel wired. "
                "Action remains BLOCKED_BY_OWNER until senior agent integrates."
            ),
            "status": "BLOCKED_BY_OWNER",
        }


# ──────────────────────────────────────────────────────
# Telegram message composer (L3 draft) — only builds text, never sends
# ──────────────────────────────────────────────────────
def compose_telegram_brief(
    *,
    discovery: dict,
    opportunity: dict,
    experiment: dict,
    metrics: dict,
    max_chars: int = 3500,
) -> str:
    """ساخت متن draft پیام تلگرام برای Owner Action Card.

    این فقط text می‌سازد. هیچ ارسالی انجام نمی‌شود.
    قالب مرتب طبق نظم تلگرام اختاپوس (brief، نه هرزنامه).
    """
    claim = (discovery.get("claim") or "")[:160]
    why = (discovery.get("why_it_matters") or "")[:200]
    opp_type = opportunity.get("type", "")
    opp_claim = (opportunity.get("claim") or "")[:160]
    conf = opportunity.get("confidence", 0.0)
    exp_level = experiment.get("level", "E0")
    exp_metric = (experiment.get("observable_metric") or "")[:140]

    # تجمیع‌های سنجه‌ای
    ext = metrics.get("external_effect_count", 0)
    spend = metrics.get("spend_amount", 0.0)
    privacy = metrics.get("privacy_violation_count", 0)

    lines = [
        "📡 WORLD-DISCOVERY — کاندیدای کشف",
        "",
        f"🔹 ادعا: {claim}",
        f"🔹 چرا مهم: {why}",
        "",
        f"💡 فرصت [{opp_type}] — confidence {conf:.0%}",
        f"   {opp_claim}",
        "",
        f"🧪 آزمایش پیشنهادی [{exp_level}]",
        f"   سنجه: {exp_metric}",
        "",
        "🔒 سنجه‌های سخت:",
        f"   external_effect={ext}  spend={spend}  privacy={privacy}",
        "",
        "⏸ وضعیت: BLOCKED_BY_OWNER — ارسال فقط با رأی تازهٔ تو.",
        "اگر تأیید می‌کنی، رأی بده؛ وگرنه nothing happens.",
    ]
    text = "\n".join(lines)
    return text[:max_chars]
