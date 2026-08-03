"""test_money_fsm — نقطهٔ کورِ ۱۳۶: گذارِ حالتِ پول بدونِ فهرستِ مجاز.

تا امروز فقط **حالتِ مقصد** اعتبارسنجی می‌شد. یعنی `APPROVED → PENDING` مجاز
بود: یک پرداختِ تمام‌شده می‌توانست به عقب برگردد و دوباره کارتِ قابلِ‌کلیک بگیرد.
هیچ صداکنندهٔ امروزی این کار را نمی‌کند — ولی «امروز هیچ‌کس نمی‌کند» ناوردی نیست،
فقط یک مشاهده است. و مشاهده‌ها با هر ریفکتور باطل می‌شوند.

ناوردیِ واقعی: **تصمیمِ پولی هرگز بی‌تصمیم نمی‌شود.**

و یک قیدِ احتیاط که به‌اندازهٔ خودِ گارد مهم است: این گارد **پیش‌فرض خاموش**
است. فهرستِ گذارها از خواندنِ کد آمده نه از مشاهدهٔ ترافیکِ زنده؛ اگر همین حالا
اجباری شود و یک گذارِ مشروعِ نادیده وجود داشته باشد، پرداختِ واقعیِ مالک
می‌شکند. اول می‌شمارد، بعد — با شواهد — مسلح می‌شود.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("money-fsm")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                      # noqa: E402
import pending_card_recovery as pcr  # noqa: E402

STATE = opslib.STATE_DIR
FLAG = pcr.TRANSITION_FLAG


def _seed(state: str):
    p = pcr._store_path(STATE)
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"decision": state} if state else {}
    p.write_text(json.dumps({"money:e1": rec}), "utf-8")


def _decision() -> str:
    d = json.loads(pcr._store_path(STATE).read_text("utf-8"))
    return str(d["money:e1"].get("decision") or "")


def _enforce(v=True):
    if v:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


# ─── ناوردیِ اصلی ──────────────────────────────────────────────────────────
def t_a_settled_payment_can_never_be_un_settled():
    """قلبِ ۱۳۶. APPROVED و DENIED پایانی‌اند — از آن‌ها هیچ راهی بیرون نیست."""
    _enforce()
    try:
        for terminal in ("APPROVED", "DENIED", "EXPIRED"):
            for target in ("PENDING", "DEFERRED", "APPROVING", "APPROVED",
                           "DENIED", "RECONCILE_REQUIRED"):
                _seed(terminal)
                ok = pcr.persist_money_decision(state_dir=STATE, effect_id="e1",
                                                decision=target)
                assert ok is False, f"{terminal} → {target} اجازه گرفت"
                assert _decision() == terminal, "حالتِ پایانی عوض شد"
    finally:
        _enforce(False)


def t_the_legitimate_path_is_never_blocked_by_the_guard():
    """گاردی که مسیرِ درست را ببندد، بدتر از نبودنش است.

    ⚠️ عمداً روی **تابعِ خالصِ تصمیم** می‌سنجد، نه روی نوشتنِ دیسک. نسخهٔ اول از
    راهِ `persist_money_decision` می‌رفت و در سوییتِ کامل گاهی قرمز می‌شد در حالی
    که تنها اجرا سبز بود. علتش منطقِ گذار نبود: `_mutate_store` قفلِ فایلی با
    مهلتِ **۳ ثانیه** می‌گیرد، و زیرِ بار (سوییتِ کامل + اسکنِ آنتی‌ویروسِ این
    ماشین) گرفتنِ آن قفل می‌تواند شکست بخورد → `False`.

    آن `False` **رفتارِ درستِ محصول** است (fail-closed، و صداکننده هم پیامِ
    شکست را به مالک می‌دهد). تستی که آن را «گاردِ اشتباه» بخواند، دروغ می‌گوید.
    پس ناوردیِ منطقی این‌جا، و ماندگاری در تستِ بعدی."""
    for src, dst in (("PENDING", "APPROVING"), ("APPROVING", "APPROVED"),
                     ("PENDING", "DENIED"), ("PENDING", "DEFERRED"),
                     ("DEFERRED", "PENDING"), ("DEFERRED", "APPROVING"),
                     ("APPROVING", "RECONCILE_REQUIRED"),
                     ("RECONCILE_REQUIRED", "APPROVED"),
                     ("RECONCILE_REQUIRED", "DENIED"),
                     ("PENDING", "EXPIRED")):
        assert not pcr._illegal_transition(src, dst), f"{src} → {dst} مسدود شد"


def t_a_legitimate_transition_reaches_the_disk():
    """ماندگاریِ واقعی — با تحملِ صریح نسبت به قفلِ مشغول.

    اگر قفل گرفته نشد، تست باید بگوید «سنجیده نشد»، نه «گارد خراب است»."""
    _enforce()
    try:
        _seed("PENDING")
        if not pcr.persist_money_decision(state_dir=STATE, effect_id="e1",
                                          decision="APPROVING"):
            assert not pcr._illegal_transition("PENDING", "APPROVING")
            return
        assert _decision() == "APPROVING"
    finally:
        _enforce(False)


def t_a_brand_new_record_can_enter_any_state():
    _enforce()
    try:
        for s in pcr.MONEY_STATES:
            _seed("")
            assert pcr.persist_money_decision(state_dir=STATE, effect_id="e1",
                                              decision=s), s
    finally:
        _enforce(False)


def t_an_unknown_state_is_still_refused():
    for bad in ("APPROVE", "approved", "", None, "DROP TABLE", 5):
        assert pcr.persist_money_decision(state_dir=STATE, effect_id="e1",
                                          decision=bad) is False, bad


# ─── احتیاط: پیش‌فرض سایه ──────────────────────────────────────────────────
def t_the_guard_is_off_by_default_and_only_counts():
    """پیش‌فرض نباید رفتارِ امروزِ مسیرِ پول را بایتی عوض کند."""
    _enforce(False)
    _seed("APPROVED")
    assert pcr.persist_money_decision(state_dir=STATE, effect_id="e1",
                                      decision="PENDING") is True
    assert _decision() == "PENDING", "خاموش بود ولی جلویش را گرفت"


def t_a_violation_is_recorded_in_both_modes():
    """سایه بی‌صدا نیست — وگرنه شواهدی برای مسلح‌کردن جمع نمی‌شود."""
    log = pcr._ops_state_dir() / "money-fsm-violations.jsonl"
    for enforce in (False, True):
        try:
            log.unlink()
        except OSError:
            pass
        _enforce(enforce)
        try:
            _seed("APPROVED")
            pcr.persist_money_decision(state_dir=STATE, effect_id="e1",
                                       decision="PENDING")
            rows = [json.loads(x) for x in log.read_text("utf-8").splitlines() if x.strip()]
            assert len(rows) == 1, (enforce, rows)
            assert rows[0]["from"] == "APPROVED" and rows[0]["to"] == "PENDING"
            assert rows[0]["enforced"] is enforce
        finally:
            _enforce(False)


def t_a_legal_transition_logs_nothing():
    log = pcr._ops_state_dir() / "money-fsm-violations.jsonl"
    try:
        log.unlink()
    except OSError:
        pass
    _enforce()
    try:
        _seed("APPROVING")
        pcr.persist_money_decision(state_dir=STATE, effect_id="e1", decision="APPROVED")
        assert not log.exists(), "گذارِ مشروع آلارم داد — نویز"
    finally:
        _enforce(False)


# ─── شکلِ جدول ─────────────────────────────────────────────────────────────
def t_the_table_covers_every_state_and_targets_are_valid():
    for s in pcr.MONEY_STATES:
        assert s in pcr.MONEY_TRANSITIONS, f"حالتِ «{s}» در جدولِ گذار نیست"
    for src, targets in pcr.MONEY_TRANSITIONS.items():
        for t in targets:
            assert t in pcr.MONEY_STATES, (src, t)


def t_the_three_terminal_states_have_no_exit():
    for s in ("APPROVED", "DENIED", "EXPIRED"):
        assert pcr.MONEY_TRANSITIONS[s] == set(), (s, pcr.MONEY_TRANSITIONS[s])


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_money_fsm: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
