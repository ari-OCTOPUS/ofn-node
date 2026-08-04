"""test_vault_updater_apply.py — «EffectorGate» applier (جلسه ۴۶، رأی مالک «کامل کن»).

قفل‌های چندلایه: خاموش پیش‌فرض؛ فقط AUTOِ gate-passed؛ Ring0/1/Project-F هرگز؛
create فقط inbox؛ append-only + idempotent؛ ضدِ traversal؛ kill-switch اول.
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("vault-apply")

import vault_updater as vu          # noqa: E402
import vault_updater_apply as ap    # noqa: E402
import opslib                       # noqa: E402

ENV_OK = ["00 - Inbox/", "07 - Knowledge/"]
_VROOT = Path(ENV["ops"]).parent    # ریشهٔ mini-vault (ORG_ROOT در تست)


def _auto_proposal():
    return vu.propose("یادداشتِ تستیِ inbox — qwen خوب بود", provenance="telegram",
                      target_path="00 - Inbox/2026-07-11 test.md",
                      candidates=[{"path": "00 - Inbox/other.md", "summary": "نامرتبط"}],
                      autonomy_envelope=ENV_OK)


def _enable():
    os.environ["ORG_ROOT"] = str(_VROOT)
    os.environ[ap.FLAG_ENV] = "1"
    ap.ACT_AUTO.parent.mkdir(parents=True, exist_ok=True)
    ap.ACT_AUTO.write_text("owner", "utf-8")


def _disable():
    os.environ.pop(ap.FLAG_ENV, None)
    if ap.ACT_AUTO.exists():
        ap.ACT_AUTO.unlink()


def t_a_off_by_default_refuses():
    _disable()
    p = _auto_proposal()
    r = ap.apply(p)
    assert r["applied"] is False and "غیرفعال" in r["reason"]


def t_b_auto_inbox_write_and_idempotent():
    _enable()
    try:
        p = _auto_proposal()
        assert p["commit_mode"] == "AUTO"
        r = ap.apply(p)
        assert r["ok"] and r["applied"] and r["path"] == "00 - Inbox/2026-07-11 test.md"
        dest = _VROOT / r["path"]
        assert dest.exists() and "qwen خوب بود" in dest.read_text("utf-8")
        # idempotent: دوباره → no-op (بدونِ تکرار)
        r2 = ap.apply(p)
        assert r2["applied"] is False and r2["reason"] == "idempotent-noop"
        assert dest.read_text("utf-8").count("qwen خوب بود") == 1
    finally:
        _disable()


def t_c_gate_hold_never_applied():
    _enable()
    try:
        pf = vu.propose("چیزی دربارهٔ اونلی فنز", provenance="chat",
                        target_path="00 - Inbox/x.md", candidates=[], autonomy_envelope=ENV_OK)
        assert ap.apply(pf)["applied"] is False       # HOLD → هرگز
        # یک proposalِ GATE (Ring1) هم هرگز
        g = vu.propose("لینک به ایندکس", provenance="chat",
                       target_path="07 - Knowledge/_Index - Knowledge.md",
                       candidates=[{"path": "07 - Knowledge/_Index - Knowledge.md", "summary": "ایندکس"}],
                       autonomy_envelope=ENV_OK)
        assert g["commit_mode"] == "GATE"
        assert ap.apply(g)["applied"] is False
    finally:
        _disable()


def t_d_ring01_and_projectf_double_blocked():
    _enable()
    try:
        # حتی اگر یک proposalِ AUTOِ جعلی برای Ring1 دست‌ساز بدهیم، applier رد می‌کند
        fake = _auto_proposal()
        fake["classification"]["target_ring"] = 1
        assert ap.apply(fake)["applied"] is False   # gate یا ring-check می‌گیرد
        fake2 = _auto_proposal()
        fake2["target_path"] = "03 - Projects/اونلی فنز/x.md"
        assert ap.apply(fake2)["applied"] is False
    finally:
        _disable()


def t_e_traversal_and_nonmd_blocked():
    _enable()
    try:
        p = _auto_proposal()
        p["patch"] = json.dumps({"op": "create", "path": "../../etc/passwd", "content": "x"})
        assert ap.apply(p)["applied"] is False
        p2 = _auto_proposal()
        p2["patch"] = json.dumps({"op": "create", "path": "00 - Inbox/x.txt", "content": "x"})
        assert ap.apply(p2)["applied"] is False    # فقط .md
    finally:
        _disable()


def t_f_killswitch_first():
    _enable()
    opslib.STOP_ORGANISM.parent.mkdir(parents=True, exist_ok=True)
    opslib.STOP_ORGANISM.write_text("stop", "utf-8")
    try:
        assert ap.apply(_auto_proposal())["reason"] == "kill-switch/FREEZE"
    finally:
        opslib.STOP_ORGANISM.unlink()
        _disable()


def t_g_domain_create_without_match_refused():
    """نوتِ دامنهٔ نو (Ring3) بدونِ dedup-match نباید ساخته شود (فقط inbox create مجاز)."""
    _enable()
    try:
        p = vu.propose("نکتهٔ دانشیِ کاملاً نو", provenance="chat",
                       target_path="07 - Knowledge/brand-new.md",
                       candidates=[{"path": "07 - Knowledge/z.md", "summary": "کاملاً نامرتبط xyz"}],
                       autonomy_envelope=ENV_OK)
        # Ring3 + AUTO ولی create در دامنه → applier رد می‌کند
        r = ap.apply(p)
        if p["commit_mode"] == "AUTO":
            assert r["applied"] is False and "create فقط" in r["reason"]
    finally:
        _disable()


# ═══ arm_gate wiring (۲۰۲۶-۰۸-۰۴، DR-001) — گیتِ هشتم داخلِ apply()، بعدِ idempotent ═══
# این مسیر امروز orphan است (هیچ صداکنندهٔ تولیدی ندارد — رجوع ۳۲-گزارش)، ولی
# capability=self_improve_auto را با arm_gate.DANGEROUS به‌اشتراک می‌گذارد؛
# سیم‌کشی defense-in-depth است برای وقتی این مسیر روزی wired شود.


def _arm_env(on):
    if on:
        os.environ["OCTOPUS_ARM_SENSITIVE_DEFAULT"] = "1"
    else:
        os.environ.pop("OCTOPUS_ARM_SENSITIVE_DEFAULT", None)
    os.environ.pop("OCTOPUS_REQUIRE_ARM", None)


def _write_arm_token(cap, suffix):
    d = opslib.STATE_DIR / "arm"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{cap}.{suffix}.json").write_text(
        json.dumps({"capability": cap, "armed_at": time.time()}), encoding="utf-8")


def _clear_arm_tokens():
    import shutil
    shutil.rmtree(opslib.STATE_DIR / "arm", ignore_errors=True)


def _unique_proposal(tag):
    """proposalِ inbox با پیام و مسیرِ یکتا — _auto_proposal() مسیرِ ثابتِ
    2026-07-11 را استفاده می‌کند که تستِ t_b قبلاً نوشته، پس هر تستِ arm_gate
    باید مسیر/محتوای خودش را داشته باشد وگرنه idempotent-noop زودتر برمی‌گردد."""
    return vu.propose(f"یادداشتِ تستیِ arm-gate-{tag} — محتوایِ یکتا", provenance="telegram",
                      target_path=f"00 - Inbox/arm-gate-{tag}.md",
                      candidates=[{"path": "00 - Inbox/other.md", "summary": "نامرتبط"}],
                      autonomy_envelope=ENV_OK)


def t_h_arm_gate_default_off_is_byte_identical():
    """هر دو knobِ arm_gate خاموش (پیش‌فرضِ امروز) → apply() دقیقاً مثلِ قبل از
    سیم‌کشی می‌نویسد (رگرسیونِ t_b)."""
    _arm_env(False)
    _clear_arm_tokens()
    _enable()
    try:
        p = _unique_proposal("h")
        r = ap.apply(p)
        assert r["ok"] and r["applied"], r
        assert not str(r.get("reason", "")).startswith("arm-gate-denied"), r
    finally:
        _disable()
        _arm_env(False)
        _clear_arm_tokens()


def t_i_arm_gate_sensitive_default_denies_without_a_fresh_token():
    """OCTOPUS_ARM_SENSITIVE_DEFAULT=1 + بدونِ arm-token → نوشته نمی‌شود، دلیل
    arm-gate-denied؛ فایل روی دیسک ساخته نمی‌شود."""
    _arm_env(True)
    _clear_arm_tokens()
    _enable()
    try:
        p = _unique_proposal("i")
        dest = _VROOT / p["target_path"]
        r = ap.apply(p)
        assert r["ok"] is False and r["applied"] is False, r
        assert str(r.get("reason", "")).startswith("arm-gate-denied"), r
        assert not dest.exists(), "گیت رد کرد ولی فایل نوشته شد"
    finally:
        _disable()
        _arm_env(False)
        _clear_arm_tokens()


def t_j_arm_gate_sensitive_default_allows_with_a_fresh_two_key_token():
    """همان + هر دو arm-token تازه → مثلِ قبل می‌نویسد."""
    _arm_env(True)
    _clear_arm_tokens()
    _enable()
    _write_arm_token("self_improve_auto", "arm")
    _write_arm_token("self_improve_auto", "arm2")
    try:
        p = _unique_proposal("j")
        r = ap.apply(p)
        assert r["ok"] and r["applied"], r
    finally:
        _disable()
        _arm_env(False)
        _clear_arm_tokens()


def t_k_arm_gate_does_not_block_the_idempotent_noop():
    """no-opِ idempotent (چیزی تغییر نمی‌کند) نباید نیازِ arm-token داشته باشد —
    گیت بعدِ چکِ idempotent است، نه قبلش."""
    _arm_env(True)
    _clear_arm_tokens()
    _enable()
    _write_arm_token("self_improve_auto", "arm")
    _write_arm_token("self_improve_auto", "arm2")
    try:
        p = _unique_proposal("k")
        r1 = ap.apply(p)
        assert r1["ok"] and r1["applied"], r1
        _clear_arm_tokens()   # توکن‌ها را پاک کن — نوشتنِ واقعیِ دوم باید رد شود
        r2 = ap.apply(p)      # همان محتوا → باید idempotent-noop بماند، نه arm-gate-denied
        assert r2["ok"] is True and r2["applied"] is False, r2
        assert r2["reason"] == "idempotent-noop", r2
    finally:
        _disable()
        _arm_env(False)
        _clear_arm_tokens()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_vault_updater_apply: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
