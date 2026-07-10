"""test_p0_security_fixes.py — جلسه ۴۶: دو رفعِ P0 که ممیزیِ ۱۲-ایجنتی پیدا کرد.

۱) human-append enforced: توکنِ معتبرِ تلگرام → is_human می‌ماند؛ بی‌توکن/جعلی → downgrade
   (age_tickِ جعلی جلو نمی‌رود)؛ مسیرِ settle دست‌نخورده؛ flag خاموش = رفتارِ قبلی.
۲) apply_merge wired: verdictِ merged → apply_merge (lesson + NOTE، status=merged).
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("p0-security")

import human_append_guard as hag   # noqa: E402
import opslib                      # noqa: E402


# ─── ۱) human-append گارد ────────────────────────────────────────────────────────
def _fake_ledger():
    """ledgerِ تزریقی که فقط is_human/actorِ آخرین append را ضبط می‌کند."""
    class _L:
        def __init__(self):
            self.last = None

        def append(self, event_type, judgment, actor="system", is_human=False, **kw):
            self.last = {"event_type": event_type, "actor": actor,
                         "is_human": is_human}
            return {"hash": "h", "is_human": is_human}
    return _L()


def t_a_valid_token_keeps_human():
    """گاردِ enabled + توکنِ mintِ کانال → is_human می‌ماند True."""
    os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "1"
    import chrono  # noqa: E402
    try:
        hag.configure(b"boot-secret-32-bytes-xxxxxxxxxxxx")
        tok = hag.default_guard().mint("eff-123", "APPROVAL")
        lg = _fake_ledger()
        chrono.on_human_judgment({"effect_id": "eff-123", "verdict": "approve"},
                                 gate=None, ledger=lg, ha_token=tok)
        assert lg.last["is_human"] is True, lg.last
        assert lg.last["actor"] == "human"
    finally:
        os.environ.pop("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", None)


def t_b_forged_no_token_downgraded():
    """گاردِ enabled + بدونِ توکن (جعلِ کد) → is_human به False downgrade می‌شود."""
    os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "1"
    import chrono  # noqa: E402
    try:
        hag.configure(b"boot-secret-32-bytes-xxxxxxxxxxxx")
        lg = _fake_ledger()
        chrono.on_human_judgment({"effect_id": "eff-999", "verdict": "approve"},
                                 gate=None, ledger=lg, ha_token=None)
        assert lg.last["is_human"] is False, lg.last   # جعل مسدود شد
        assert lg.last["actor"] == "system"
    finally:
        os.environ.pop("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", None)


def t_c_bad_token_downgraded():
    """توکنِ دست‌کاری‌شده/بیگانه → downgrade (امضای HMAC نامعتبر)."""
    os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "1"
    import chrono  # noqa: E402
    try:
        hag.configure(b"boot-secret-32-bytes-xxxxxxxxxxxx")
        lg = _fake_ledger()
        chrono.on_human_judgment({"effect_id": "eff-1"}, gate=None, ledger=lg,
                                 ha_token="v1.eff-1.9999999999.deadbeef")
        assert lg.last["is_human"] is False
    finally:
        os.environ.pop("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", None)


def t_d_replay_downgraded():
    """توکنِ یک‌بارمصرف: استفادهٔ دوم → downgrade (ضدِ replay)."""
    os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "1"
    import chrono  # noqa: E402
    try:
        hag.configure(b"boot-secret-32-bytes-xxxxxxxxxxxx")
        tok = hag.default_guard().mint("eff-r", "APPROVAL")
        lg1, lg2 = _fake_ledger(), _fake_ledger()
        chrono.on_human_judgment({"effect_id": "eff-r"}, ledger=lg1, ha_token=tok)
        chrono.on_human_judgment({"effect_id": "eff-r"}, ledger=lg2, ha_token=tok)
        assert lg1.last["is_human"] is True and lg2.last["is_human"] is False
    finally:
        os.environ.pop("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", None)


def t_e_flag_off_is_legacy_behavior():
    """پرچمِ خاموش → گارد اصلاً اجرا نمی‌شود؛ is_human=True (بایت‌به‌بایت رفتارِ قبلی)."""
    os.environ.pop("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", None)
    import chrono  # noqa: E402
    lg = _fake_ledger()
    chrono.on_human_judgment({"effect_id": "eff-x"}, ledger=lg, ha_token=None)
    assert lg.last["is_human"] is True


def t_f_guard_disabled_passthrough():
    """گاردِ پیکربندی‌نشده (بدونِ راز) + flag روشن → passthrough (رفتارِ قبلی، بی‌کرش)."""
    os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "1"
    import chrono  # noqa: E402
    try:
        hag.configure.__globals__["_default_guard"] = hag.HumanAppendGuard(None)  # disabled
        lg = _fake_ledger()
        chrono.on_human_judgment({"effect_id": "eff-y"}, ledger=lg, ha_token=None)
        assert lg.last["is_human"] is True   # disabled → passthrough، نه downgrade
    finally:
        os.environ.pop("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", None)


def t_g_mint_helper_sanitizes_and_gates():
    """_mint_ha_token: گاردِ خاموش → None؛ روشن → توکنِ معتبر با idِ sanitize‌شده."""
    import approval_channel as ac
    hag.configure.__globals__["_default_guard"] = hag.HumanAppendGuard(None)
    assert ac._mint_ha_token("eff.1") is None           # disabled → None
    hag.configure(b"boot-secret-32-bytes-xxxxxxxxxxxx")
    tok = ac._mint_ha_token("eff.1.2")                  # نقطه‌دار
    assert tok and tok.split(".")[1] == "eff-1-2"       # sanitize شد


# ─── ۲) apply_merge wired ────────────────────────────────────────────────────────
def t_h_apply_merge_effect_on_merged_verdict():
    """verdictِ merged در run_cycle → apply_merge (status=merged + فایلِ lesson)."""
    sys.path.insert(0, str(_HERE.parent / "doctor"))
    import importlib
    import doctor as _docmod
    importlib.reload(_docmod)

    class _Chan:
        def __init__(self):
            self._v = [("rfc-abc", "merge-approved")]

        def pop_rfc_verdicts(self):
            v, self._v = self._v, []
            return v

    d = _docmod.Doctor(state_dir=str(Path(ENV["ops"]) / "state"),
                       approval_channel=_Chan())
    # یک RFCِ submitted در رجیستری بگذار
    rfc = _docmod.RFC(rfc_id="rfc-abc", bottleneck="b", fix="f",
                      expected_lift=0.1, status="submitted")
    d._rfcs["rfc-abc"] = rfc
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert d._rfcs["rfc-abc"].status == "merged", d._rfcs["rfc-abc"].status
    lesson = d._knowledge_dir / "rfc-abc-lesson.md"
    assert lesson.exists(), "apply_merge باید فایلِ lesson بنویسد"


def t_i_apply_merge_flag_off_no_effect():
    """flag خاموش → apply_merge صدا زده نمی‌شود؛ status فقط برچسبِ human-merged."""
    sys.path.insert(0, str(_HERE.parent / "doctor"))
    import doctor as _docmod

    class _Chan:
        def pop_rfc_verdicts(self):
            return [("rfc-off", "merge-approved")]

    d = _docmod.Doctor(state_dir=str(Path(ENV["ops"]) / "state"), approval_channel=_Chan())
    d._rfcs["rfc-off"] = _docmod.RFC(rfc_id="rfc-off", bottleneck="b", fix="f",
                                     expected_lift=0.1, status="submitted")
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "0"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert d._rfcs["rfc-off"].status == "human-merged"   # فقط برچسب، نه merged
    assert not (d._knowledge_dir / "rfc-off-lesson.md").exists()


def t_j_rfc_registry_persists_across_restart():
    """جلسه ۴۶: RFCها روی دیسک persist و در بوتِ Doctorِ نو بارگذاری می‌شوند."""
    sys.path.insert(0, str(_HERE.parent / "doctor"))
    import importlib
    import doctor as _docmod
    importlib.reload(_docmod)
    sd = str(Path(ENV["ops"]) / "state")
    os.environ["OCTOPUS_WIRE_DOCTOR_PERSIST"] = "1"
    try:
        d1 = _docmod.Doctor(state_dir=sd)
        d1._rfcs["rfc-persist"] = _docmod.RFC(rfc_id="rfc-persist", bottleneck="b",
                                              fix="f", expected_lift=0.2, status="submitted")
        d1._persist_rfcs()
        assert d1._rfc_store.exists()
        # «restart»: Doctorِ نو باید RFC را از دیسک بخواند
        d2 = _docmod.Doctor(state_dir=sd)
        assert "rfc-persist" in d2._rfcs, "RFC باید بعد از restart بارگذاری شود"
        assert d2._rfcs["rfc-persist"].status == "submitted"
        on_disk = json.loads(d1._rfc_store.read_text("utf-8"))
        assert on_disk["schema"] == "doctor-rfcs.v1"
        # terminal RFC نباید بعد از restart بارگذاری شود (ضدِ باد‌کردنِ pending)
        d2._rfcs["rfc-done"] = _docmod.RFC(rfc_id="rfc-done", bottleneck="b", fix="f",
                                           expected_lift=0.1, status="merged")
        d2._persist_rfcs()
        d3 = _docmod.Doctor(state_dir=sd)
        assert "rfc-done" not in d3._rfcs and "rfc-persist" in d3._rfcs
        # flag خاموش → هیچ load (backward-compat)
        os.environ.pop("OCTOPUS_WIRE_DOCTOR_PERSIST", None)
        d4 = _docmod.Doctor(state_dir=sd)
        assert d4._rfcs == {}
    finally:
        os.environ.pop("OCTOPUS_WIRE_DOCTOR_PERSIST", None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_p0_security_fixes: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
