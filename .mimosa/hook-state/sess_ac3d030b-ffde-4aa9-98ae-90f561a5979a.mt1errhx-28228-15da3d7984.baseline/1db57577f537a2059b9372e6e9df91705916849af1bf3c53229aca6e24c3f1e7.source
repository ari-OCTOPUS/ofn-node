#!/usr/bin/env python3
"""action_graph.py — ژنومِ حرکتیِ مرکز تلگرام (Action Graph).

این ماژول یک رجیستریِ خالص و stdlib-only از actionهای قابل‌کنترل از تلگرام است.
هدفش این است که هر دکمه/نیت به جای handler پراکنده، یک رکورد ژنتیکی داشته باشد:

    action_id → risk → requires_approval → handler → audit → rollback → tests

قواعد:
  - import-time کاملاً خالص: هیچ I/O، هیچ شبکه، هیچ نوشتن.
  - fail-closed: action ناشناس high-risk و نیازمند approval فرض می‌شود.
  - content-free: فقط id/handler/risk، بدون echo محتوای مالک.

مصرف‌کنندهٔ اصلی: mission.py و center.py.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ActionSpec:
    """یک action در نخاع حرکتی اختاپوس."""

    action_id: str
    label: str
    organ: str
    risk: str = "read"                 # read|low|medium|high
    requires_approval: bool = False
    handler: str = ""                   # dotted-path قراردادی/مستند؛ الزاماً callable نیست
    audit: bool = True
    rollback: bool = False
    autonomy_level: int = 0             # سطح پیشنهادی ۰..۵
    tests: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tests"] = list(self.tests)
        return d


# قرارداد ژنوم حرکتی — additive و محافظه‌کار.
_ACTIONS: dict[str, ActionSpec] = {
    # observe / cockpit
    "status.refresh": ActionSpec(
        "status.refresh", "تازه‌سازی وضعیت", "telegram_center", "read", False,
        "center._page:st", autonomy_level=0, tests=("test_tg_render", "test_tg_center")),
    "approval.view": ActionSpec(
        "approval.view", "دیدن صف تأیید", "telegram_center", "read", False,
        "center._page:ap", autonomy_level=0, tests=("test_tg_approval_store",)),
    "mission.view": ActionSpec(
        "mission.view", "دیدن مأموریت‌ها", "telegram_center", "read", False,
        "center._page:ms", autonomy_level=0, tests=("test_tg_mission",)),

    # reversible runtime operations
    "leg.pause": ActionSpec(
        "leg.pause", "مکث پا", "telegram_center", "low", False,
        "power.pause_leg", rollback=True, autonomy_level=1, tests=("test_tg_power",)),
    "leg.resume": ActionSpec(
        "leg.resume", "ادامه پا", "telegram_center", "low", False,
        "power.resume_leg", rollback=True, autonomy_level=1, tests=("test_tg_power",)),
    "map.scan": ActionSpec(
        "map.scan", "اسکن metadata", "telegram_center", "read", False,
        "metadata_scan.scan_metadata", autonomy_level=1, tests=("test_tg_metadata_scan",)),

    # Mission Genome / self-coding pipeline (propose-only until owner approval)
    "mission.next": ActionSpec(
        "mission.next", "قدم بعدی مأموریت", "telegram_center", "read", False,
        "mission.advance", autonomy_level=1, tests=("test_tg_mission",)),
    "code.plan": ActionSpec(
        "code.plan", "ساخت طرح کدنویسی", "cortex", "medium", False,
        "cortex.code_autonomy:propose-only", rollback=False, autonomy_level=2,
        tests=("test_tg_mission", "test_code_autonomy"),
        notes="طرح/patch پیشنهادی است؛ اعمال زنده ندارد."),
    "code.patch": ActionSpec(
        "code.patch", "ساخت patch پیشنهادی", "cortex", "medium", False,
        "cortex.code_autonomy.shadow_test", rollback=False, autonomy_level=2,
        tests=("test_code_autonomy", "test_tg_center"),
        notes="فقط تولید diff و shadow-test؛ apply جدا و gated است."),
    "code.test": ActionSpec(
        "code.test", "اجرای تست/fitness", "cortex", "low", False,
        "tests.run_all / targeted-suite", autonomy_level=2,
        tests=("test_tg_mission",), notes="در این لایه فقط در mission ثبت می‌شود؛ runner واقعی جداست."),
    "doctor.review": ActionSpec(
        "doctor.review", "نقد دکتر/ایمنی", "doctor", "low", False,
        "doctor.review_bus", autonomy_level=2, tests=("test_doctor", "test_tg_mission")),
    "epistemics.review": ActionSpec(
        "epistemics.review", "نقد شواهد", "epistemics", "low", False,
        "epistemics.guard_review", autonomy_level=2, tests=("test_phase4_epistemics",)),
    "code.diff": ActionSpec(
        "code.diff", "دیدن diff", "cortex", "read", False,
        "code_autonomy.diff", autonomy_level=2, tests=("test_code_autonomy",)),
    "code.apply": ActionSpec(
        "code.apply", "اعمال patch", "cortex", "high", True,
        "code_autonomy.apply_approved", rollback=True, autonomy_level=3,
        tests=("test_code_autonomy", "test_tg_approval_store"),
        notes="همیشه owner approval + shadow-green + rollback لازم دارد."),
    "code.rollback": ActionSpec(
        "code.rollback", "rollback patch", "cortex", "high", True,
        "code_autonomy.rollback", rollback=True, autonomy_level=3,
        tests=("test_code_autonomy",)),
    "evolution.propose": ActionSpec(
        "evolution.propose", "پیشنهاد جهش", "doctor", "medium", False,
        "doctor.evolution:propose", rollback=False, autonomy_level=5,
        tests=("test_evolution", "test_held_out_evaluator"),
        notes="tournament/fitness قبل از owner approval برای apply."),
    "evolution.select": ActionSpec(
        "evolution.select", "انتخاب جهش برنده", "doctor", "high", True,
        "doctor.evolution:select", rollback=True, autonomy_level=5,
        tests=("test_evolution", "test_held_out_evaluator", "test_code_autonomy")),
}

# نگاشت intent مرکز تلگرام به action اصلی.
_INTENT_TO_ACTION = {
    "status": "status.refresh",
    "approvals": "approval.view",
    "scan_metadata": "map.scan",
    "pause_leg": "leg.pause",
    "resume_leg": "leg.resume",
    "code_plan": "code.plan",
    "code_patch": "code.patch",
    "code_test": "code.test",
    "code_apply": "code.apply",
    "evolution_propose": "evolution.propose",
    "mission": "mission.next",
    "learn_preference": "mission.next",
}

_RISK_RANK = {"read": 0, "low": 1, "medium": 2, "high": 3}


def all_actions() -> dict[str, dict]:
    """کپیِ serializable از کل action graph."""
    return {k: v.to_dict() for k, v in sorted(_ACTIONS.items())}


def get(action_id: str) -> dict:
    """یک action را برگردان. ناشناس = high-risk/approval-required (fail-closed)."""
    key = str(action_id or "")
    spec = _ACTIONS.get(key)
    if spec is None:
        return ActionSpec(
            key or "unknown", "اکشن ناشناخته", "unknown", "high", True,
            "unknown", audit=True, rollback=False, autonomy_level=0,
            notes="fail-closed: action ناشناس بدون approval مجاز نیست.",
        ).to_dict()
    return spec.to_dict()


def action_for_intent(intent_name: str) -> dict:
    """intent مرکز تلگرام → action spec اصلی."""
    return get(_INTENT_TO_ACTION.get(str(intent_name or ""), "mission.next"))


def requires_owner_approval(action_id: str) -> bool:
    return bool(get(action_id).get("requires_approval"))


def risk_rank(risk: str) -> int:
    return _RISK_RANK.get(str(risk or "high"), 3)


def max_risk(action_ids: list[str] | tuple[str, ...]) -> str:
    """بالاترین risk در چند action."""
    best = "read"
    for aid in action_ids or []:
        r = str(get(aid).get("risk", "high"))
        if risk_rank(r) > risk_rank(best):
            best = r
    return best


def allowed_at_level(action_id: str, level: int) -> bool:
    """آیا action در سطح خودمختاری داده‌شده مجاز است؟ high/apply همچنان approval می‌خواهد."""
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        lvl = 0
    spec = get(action_id)
    if bool(spec.get("requires_approval")):
        return False
    try:
        return int(spec.get("autonomy_level", 99)) <= lvl
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    import json
    print(json.dumps(all_actions(), ensure_ascii=False, indent=2))
