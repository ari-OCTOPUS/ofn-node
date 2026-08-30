"""test_merge_applies_knob.py — 2026-07-18: تپِ merge مالک روی یک RFCِ نوعِ 'tune'
واقعاً یک knobِ whitelist را (محدود/برگشت‌پذیر) اعمال می‌کند — پایانِ apply_mergeِ نمادین.

قفل می‌کند، به‌ویژه مرزِ سخت:
  · فقط change_level=='tune' + knobِ AUTO_KNOBS واقعاً اعمال می‌شود؛
  · هر چیزِ دیگر (پیش‌فرضِ 'code') فقط درس می‌نویسد (بایت‌به‌بایتِ رفتارِ قدیمی)؛
  · flag خاموش → حتی RFCِ tune هم اعمال نمی‌شود؛
  · minting فقط knobهای *unset* را پیشنهاد می‌دهد (مقدارِ صریحِ مالک را نمی‌جنباند)؛
  · خطِ قرمزِ AST: branchِ apply_merge هرگز settle/pay/post_journal/git صدا نمی‌زند.
$0 · بدونِ شبکه · state موقت (harness).
"""
import ast
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "doctor"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness                       # noqa: E402
ENV = harness.setup("merge-applies-knob")

import doctor as _docmod             # noqa: E402
import improve as _improve           # noqa: E402
import opslib                        # noqa: E402


class _VerdictChan:
    """کانالِ تزریقی (C7.2 claim/ack): یک verdictِ merge-approved با revision یک‌بار می‌دهد؛
    begin_rfc_apply/ack موفق تا مسیرِ apply (نه صرفاً برچسبِ legacy) طی شود."""
    def __init__(self, rfc_id):
        self._v = [(rfc_id, "merge-approved", 1)]

    def claim_rfc_verdicts(self, worker_id, lease_s=300):
        v, self._v = self._v, []
        return v

    def begin_rfc_apply(self, rfc_id, revision, operation_key):
        return True

    def ack_rfc_verdict(self, rfc_id, revision, *, applied, receipt_id=""):
        return True


class _CardChan:
    """کانالِ تزریقی برای mint: rfc_card=True (کارت فرستاده شد)، بدونِ verdict."""
    def __init__(self):
        self.cards = []

    def rfc_card(self, rfc_id, summary):
        self.cards.append(rfc_id)
        return True

    def pop_rfc_verdicts(self):
        return []


def _doctor(chan=None):
    return _docmod.Doctor(state_dir=str(Path(ENV["ops"]) / "state"),
                          approval_channel=chan)


def _knobs_path():
    return Path(opslib.STATE_DIR) / "cortex" / "auto-knobs.json"


def t_a_tune_knob_merge_applies_real_knob():
    """RFCِ tune + knobِ whitelist + هر دو flag روشن → merge واقعاً apply_knob می‌زند:
    auto-knobs.json نوشته می‌شود و مقدار در کرانِ امن است."""
    knob = "CORTEX_THINK_EVERY_N"
    lo, hi = _improve.AUTO_KNOBS[knob]
    d = _doctor(_VerdictChan("rfc-tune"))
    d._rfcs["rfc-tune"] = _docmod.RFC(rfc_id="rfc-tune", bottleneck="b",
                                      fix="tune the think cadence", expected_lift="x",
                                      status="submitted", change_level="tune", knob=knob)
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    os.environ["OCTOPUS_WIRE_MERGE_APPLIES_KNOB"] = "1"
    os.environ.pop(knob, None)
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
        os.environ.pop("OCTOPUS_WIRE_MERGE_APPLIES_KNOB", None)
    assert d._rfcs["rfc-tune"].status == "merged", d._rfcs["rfc-tune"].status
    kp = _knobs_path()
    assert kp.exists(), "apply_knob باید auto-knobs.json بنویسد"
    m = json.loads(kp.read_text("utf-8"))
    assert knob in m, m
    assert lo <= float(m[knob]) <= hi, (m[knob], lo, hi)   # در کرانِ امن (clamp)


def t_b_code_rfc_merge_is_lesson_only():
    """RFCِ پیش‌فرض (change_level='code') + merge → هیچ knob اعمال نمی‌شود؛
    فقط درس (مرزِ سخت: کد هرگز خودکار اعمال نمی‌شود)."""
    kp = _knobs_path()
    before = kp.read_text("utf-8") if kp.exists() else None
    d = _doctor(_VerdictChan("rfc-code"))
    d._rfcs["rfc-code"] = _docmod.RFC(rfc_id="rfc-code", bottleneck="b",
                                      fix="rewrite the scheduler core in place",
                                      expected_lift="x", status="submitted")  # پیش‌فرض code
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    os.environ["OCTOPUS_WIRE_MERGE_APPLIES_KNOB"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
        os.environ.pop("OCTOPUS_WIRE_MERGE_APPLIES_KNOB", None)
    assert d._rfcs["rfc-code"].status == "merged"
    assert (d._knowledge_dir / "rfc-code-lesson.md").exists(), "باید درس بنویسد"
    after = kp.read_text("utf-8") if kp.exists() else None
    assert after == before, "RFCِ code نباید هیچ knob اعمال کند (مرزِ سخت)"


def t_c_flag_off_no_knob_apply():
    """flagِ MERGE_APPLIES_KNOB خاموش → حتی RFCِ tune هم فقط درس می‌شود (هیچ knob)."""
    knob = "CHRONO_NUDGE_EVERY_N_BEATS"
    kp = _knobs_path()
    before = kp.read_text("utf-8") if kp.exists() else None
    d = _doctor(_VerdictChan("rfc-off"))
    d._rfcs["rfc-off"] = _docmod.RFC(rfc_id="rfc-off", bottleneck="b", fix="f",
                                     expected_lift="x", status="submitted",
                                     change_level="tune", knob=knob)
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    os.environ.pop("OCTOPUS_WIRE_MERGE_APPLIES_KNOB", None)   # خاموش
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert d._rfcs["rfc-off"].status == "merged"
    after = kp.read_text("utf-8") if kp.exists() else None
    assert after == before, "flag خاموش نباید knob اعمال کند"


def t_d_mint_only_unset_whitelisted_knobs():
    """_mine_knob_rfcs: فقط برای knobِ whitelistِ unset، RFCِ tune می‌سازد؛
    knobِ setِ صریحِ مالک را دست نمی‌زند."""
    d = _doctor(_CardChan())
    set_knob = "HEART_SAMPLE_INTERVAL_S"
    for k in _improve.AUTO_KNOBS:
        os.environ.pop(k, None)
    os.environ[set_knob] = "900"   # مقدارِ صریحِ مالک (خارج از باند)
    try:
        drafted = d._mine_knob_rfcs()
    finally:
        os.environ.pop(set_knob, None)
    minted = {d._rfcs[rid].knob for rid in drafted}
    assert set_knob not in minted, "knobِ setِ صریحِ مالک نباید mint شود"
    assert minted, "برای knobهای unset باید حداقل یکی mint شود"
    for rid in drafted:
        assert d._rfcs[rid].change_level == "tune"
        assert d._rfcs[rid].knob in _improve.AUTO_KNOBS


def t_e_mint_dedup_no_double():
    """dedup: knobی که RFCِ باز دارد بارِ دوم mint نمی‌شود."""
    d = _doctor(_CardChan())
    for k in _improve.AUTO_KNOBS:
        os.environ.pop(k, None)
    first = d._mine_knob_rfcs()
    second = d._mine_knob_rfcs()
    assert first, "بارِ اول باید mint کند"
    assert not second, ("بارِ دوم باید خالی باشد (dedup)", second)


def t_f_apply_merge_knob_branch_never_settles():
    """خطِ قرمزِ AST: متدِ apply_merge هرگز settle/pay/post_journal/transfer/git صدا
    نمی‌زند — تنها اعمالِ مجاز apply_knob است."""
    src = (_HERE.parent / "doctor" / "doctor.py").read_text("utf-8")
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "apply_merge")
    called = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            name = getattr(f, "attr", None) or getattr(f, "id", None)
            if name:
                called.add(name)
    banned = {"settle", "pay", "post_journal", "spend", "transfer",
              "push", "checkout", "commit", "run", "Popen", "call",
              "_write_env", "write_env", "set_flag", "rmtree", "unlink",
              "remove", "on_human_judgment", "raise_halt_all", "settle_effect"}
    hit = called & banned
    assert not hit, f"apply_merge نباید این‌ها را صدا بزند (مرزِ پول/git/gate): {hit}"
    assert "apply_knob" in called, "apply_merge باید apply_knob را (تنها اعمالِ مجاز) داشته باشد"


def t_g_denied_knob_not_reminted():
    """احترام به «نه»: knobی که RFCش رد شده دوباره mint نمی‌شود (درسِ later-is-not-a-verdict)."""
    d = _doctor(_CardChan())
    for k in _improve.AUTO_KNOBS:
        os.environ.pop(k, None)
    first = d._mine_knob_rfcs()
    assert first, "بارِ اول باید mint کند"
    for rid in first:                 # شبیه‌سازیِ ردِ مالک
        d._rfcs[rid].status = "human-rejected"
    second = d._mine_knob_rfcs()
    assert not second, ("knobِ ردشده نباید دوباره mint شود", second)


def t_h_owner_set_between_mint_and_merge_not_overwritten():
    """اگر مالک بینِ mint و merge مقدارِ knob را set کند، تپِ merge آن را بازنویسی نمی‌کند
    (فقط merge/درس؛ هیچ apply — caveat راستی‌آزمایی بسته شد)."""
    knob = "CHRONO_NUDGE_EVERY_N_BEATS"
    kp = _knobs_path()
    before = kp.read_text("utf-8") if kp.exists() else None
    d = _doctor(_VerdictChan("rfc-race"))
    d._rfcs["rfc-race"] = _docmod.RFC(rfc_id="rfc-race", bottleneck="b", fix="f",
                                      expected_lift="x", status="submitted",
                                      change_level="tune", knob=knob)
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    os.environ["OCTOPUS_WIRE_MERGE_APPLIES_KNOB"] = "1"
    os.environ[knob] = "500"          # مالک بینِ mint و merge مقدار گذاشت
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
        os.environ.pop("OCTOPUS_WIRE_MERGE_APPLIES_KNOB", None)
        os.environ.pop(knob, None)
    assert d._rfcs["rfc-race"].status == "merged"
    after = kp.read_text("utf-8") if kp.exists() else None
    assert after == before, "مقدارِ صریحِ مالک نباید سرِ merge بازنویسی/اعمال شود"


def t_i_applied_value_is_integer_string():
    """رفعِ blocker: مقدارِ اعمال‌شده باید صحیح باشد (نه '780.0') تا int(os.environ) نشکند."""
    knob = "CHRONO_NUDGE_EVERY_N_BEATS"
    d = _doctor(_VerdictChan("rfc-int"))
    d._rfcs["rfc-int"] = _docmod.RFC(rfc_id="rfc-int", bottleneck="b", fix="f",
                                     expected_lift="x", status="submitted",
                                     change_level="tune", knob=knob)
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    os.environ["OCTOPUS_WIRE_MERGE_APPLIES_KNOB"] = "1"
    os.environ.pop(knob, None)
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
        os.environ.pop("OCTOPUS_WIRE_MERGE_APPLIES_KNOB", None)
    m = json.loads(_knobs_path().read_text("utf-8"))
    assert float(m[knob]) == int(float(m[knob])), (m[knob], "باید صحیح باشد")
    # مصرف‌کننده int(str(value)) نباید ValueError بگیرد
    int(str(m[knob]))


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_merge_applies_knob: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
