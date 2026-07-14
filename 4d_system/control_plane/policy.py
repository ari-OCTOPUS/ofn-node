"""
control_plane/policy.py — نردبانِ policy (Phase 4) — فقط داده و تابعِ pure.

Level 0: observe-only            Level 3: require approval
Level 1: log + shadow decision   Level 4: pause subsystem
Level 2: soft warning            Level 5: kill-switch / halt

قواعد:
  • low-risk خودمختار می‌ماند (0..1) — تمرکزِ کنترل نباید autonomy را بکشد.
  • high-risk (لیستِ مالک) → approval (۳+).
  • ambiguous/ناشناخته → needs_review=True و سطحِ امن (۳) — هرگز silent-pass.
  • destructive → approval + الزامِ rollback.

این ماژول هیچ I/O ندارد و در v1 هیچ‌چیز را enforce نمی‌کند؛ در v2 به‌صورت
shadow روی جریانِ رویدادها اجرا می‌شود (فقط گزارش)، در v3 با flag برای
high-riskها زنده می‌شود.
"""
from __future__ import annotations

from enum import IntEnum

from control_plane.contracts import PolicyResult


class Level(IntEnum):
    OBSERVE = 0
    SHADOW_LOG = 1
    SOFT_WARN = 2
    REQUIRE_APPROVAL = 3
    PAUSE_SUBSYSTEM = 4
    KILL_SWITCH = 5


LEVEL_NAMES = {
    Level.OBSERVE: "observe-only",
    Level.SHADOW_LOG: "log+shadow",
    Level.SOFT_WARN: "soft-warning",
    Level.REQUIRE_APPROVAL: "require-approval",
    Level.PAUSE_SUBSYSTEM: "pause-subsystem",
    Level.KILL_SWITCH: "kill-switch",
}

# ── نگاشتِ action → سطحِ لازم ────────────────────────────────────────────
# منبع: دکترینِ مالک (لیستِ high-risk) + رفتارِ فعلیِ سیستم (verified):
#   خودمختاریِ کم‌ریسک (کاوش/نوشتن در outputs/تماسِ ابریِ زیرِ سقف) دست نمی‌خورد.
ACTION_POLICY: dict[str, Level] = {
    # کم‌ریسک — خودمختار می‌ماند
    "read_only":              Level.OBSERVE,
    "write_outputs":          Level.OBSERVE,      # مسیرِ مجازِ guardrails
    "memory_write":           Level.OBSERVE,      # کارکردِ عادیِ سیستم
    "call_cloud_llm":         Level.SHADOW_LOG,   # سقفِ budget قبلاً هست
    "telegram_digest":        Level.SHADOW_LOG,   # ≤۳/روز، طراحیِ موجود
    "backup_create":          Level.SHADOW_LOG,
    "archive":                Level.SHADOW_LOG,   # archive-not-delete
    "self_code_propose":      Level.SHADOW_LOG,   # فقط پیشنهاد؛ اجرا نمی‌شود
    "write_local_file":       Level.SOFT_WARN,    # خارج از outputs ولی غیر TCB
    "vectorstore_rebuild":    Level.SOFT_WARN,

    # high-risk (لیستِ مالک) — approval
    "self_code_approve":      Level.REQUIRE_APPROVAL,
    "self_code_apply":        Level.REQUIRE_APPROVAL,
    "change_tcb":             Level.REQUIRE_APPROVAL,
    "flip_live_flag":         Level.REQUIRE_APPROVAL,
    "budget_increase":        Level.REQUIRE_APPROVAL,
    "external_send_publish":  Level.REQUIRE_APPROVAL,
    "delete_data":            Level.REQUIRE_APPROVAL,  # + rollback الزامی
    "change_env_or_secrets":  Level.REQUIRE_APPROVAL,
    "change_config":          Level.REQUIRE_APPROVAL,
    "cross_project_write":    Level.REQUIRE_APPROVAL,
    "change_daemon_behavior": Level.REQUIRE_APPROVAL,
    "run_external_command":   Level.REQUIRE_APPROVAL,
    "model_promotion":        Level.REQUIRE_APPROVAL,
    "backup_restore":         Level.REQUIRE_APPROVAL,
    "spend_anomaly":          Level.PAUSE_SUBSYSTEM,   # ناهنجاریِ خرج → مکث تا بررسی
    "policy_bypass":          Level.PAUSE_SUBSYSTEM,   # تلاش برای دورزدن → مکث
    "kill_switch":            Level.KILL_SWITCH,
}

# لیستِ high-risk مالک (تصمیمِ 2026-07-11) — برای گزارش/UI
HIGH_RISK_ACTIONS: tuple[str, ...] = tuple(
    a for a, lv in ACTION_POLICY.items() if lv >= Level.REQUIRE_APPROVAL
)

# destructiveها علاوه بر approval باید rollback مستند داشته باشند
DESTRUCTIVE_ACTIONS: frozenset[str] = frozenset({
    "delete_data", "backup_restore", "change_tcb", "self_code_apply",
})


def evaluate(action_type: str, risk_hint: str | None = None) -> PolicyResult:
    """ارزیابیِ pure یک action. ناشناخته → needs_review + سطحِ امن (۳)."""
    level = ACTION_POLICY.get(action_type)
    if level is None:
        return PolicyResult(
            action_type=action_type,
            level=int(Level.REQUIRE_APPROVAL),
            level_name=LEVEL_NAMES[Level.REQUIRE_APPROVAL],
            requires_approval=True,
            needs_review=True,
            reason="action ناشناخته — ambiguous → needs_review (silent-pass ممنوع)",
        )
    # hint فقط می‌تواند سطح را بالا ببرد، هرگز پایین نیاورد
    if risk_hint == "high" and level < Level.REQUIRE_APPROVAL:
        level = Level.REQUIRE_APPROVAL
    return PolicyResult(
        action_type=action_type,
        level=int(level),
        level_name=LEVEL_NAMES[Level(level)],
        requires_approval=level >= Level.REQUIRE_APPROVAL,
        needs_review=False,
        reason="نگاشتِ ثابتِ policy ladder v1"
               + (" + rollback الزامی (destructive)" if action_type in DESTRUCTIVE_ACTIONS else ""),
    )
