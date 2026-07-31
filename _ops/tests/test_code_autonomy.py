"""test_code_autonomy.py — P1: تسترِ سایه‌ایِ patch زیرِ فرمانِ قلب (code_autonomy).

قانونِ قلب: حسِ قلب (فیوزِ استرس) رییسِ اجازه است؛ deny-list سخت؛ شادو-تست هرگز درختِ زنده
را لمس نمی‌کند؛ flag-off = بدونِ نوشتنِ state. همه با run_fn/monkeypatch فیک — صفر git، صفر سوییت.
"""
import io
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("code-autonomy")

from cortex import code_autonomy as CA  # noqa: E402

# رفرنسِ تابعِ واقعی، پیش از این‌که تست‌ها CA.heart_mood را با fake جایگزین کنند
_REAL_HEART_MOOD = CA.heart_mood


class _C:
    failed = 0


def check(name, cond):
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


# ── قانونِ قلب §۱ — mood verdict روی استرسِ فیوز‌شده ──────────────────────────────
def _mood_with(arousal, in_fear=False, sigma=None):
    CA.heart_mood.__wrapped__ = None
    orig = CA.heart_mood
    def fake():
        m = "🔥جریان"
        if in_fear or arousal >= CA.FEAR or (sigma is not None and sigma >= 1.0):
            m = "فروپاشی"
        elif arousal > CA.STRESS_FLOW_HI:
            m = "تنش"
        elif arousal < CA.STRESS_STAGNANT:
            m = "رکود"
        return {"mood": m, "verdict": CA._MOOD_VERDICT[m], "arousal": arousal,
                "in_fear": in_fear, "sigma": sigma, "note": ""}
    return fake


# real heart_mood must return a well-formed dict on the empty test vault (fail-soft)
def t_a_heart_mood_fail_soft_shape():
    m = CA.heart_mood()
    assert isinstance(m, dict)
    assert m["verdict"] in ("freeze", "throttle", "push", "act")
    assert "mood" in m and "arousal" in m


def t_b_edge_of_chaos_band():
    # استرسِ صفر = رکود (push)، وسط = جریان (act)، بالا = تنش (throttle)، ترس = فروپاشی (freeze)
    CA.heart_mood = _mood_with(0.0)
    assert CA.heart_mood()["verdict"] == "push" and CA.heart_mood()["mood"] == "رکود"
    CA.heart_mood = _mood_with(0.35)
    assert CA.heart_mood()["verdict"] == "act" and CA.heart_mood()["mood"] == "🔥جریان"
    CA.heart_mood = _mood_with(0.68)
    assert CA.heart_mood()["verdict"] == "throttle"
    CA.heart_mood = _mood_with(0.80)
    assert CA.heart_mood()["verdict"] == "freeze"
    CA.heart_mood = _mood_with(0.30, in_fear=True)
    assert CA.heart_mood()["verdict"] == "freeze", "ترس باید freeze کند حتی با استرسِ کم"
    CA.heart_mood = _mood_with(0.30, sigma=1.0)
    assert CA.heart_mood()["verdict"] == "freeze", "σ=۱ (محورِ فروپاشی) باید freeze کند"


# ── قانونِ قلب §۳ — deny/allowlist ────────────────────────────────────────────────
def t_c_allowlist_and_denylist():
    # ۰۷-۳۱: با رأیِ ثبت‌شدهٔ مالک (VQ-SELFGOAL-005، ۰۷-۳۰) `telegram_center`
    # از allowlist ِ خودپچی **برداشته شد** (دامنه = دقیقاً `_ops/cortex` +
    # `_ops/state`)؛ انتظارِ قدیمیِ این بند از قبل از آن رأی مانده بود و
    # `test_self_patch.t_the_narrowed_scope_is_locked_not_just_unused` هم
    # همین قفل را از سمتِ دیگر می‌سنجد.
    assert CA.allowed_target("_ops/cortex/stress.py")
    assert not CA.allowed_target("_ops/telegram_center/render.py"), \
        "دامنهٔ باریک‌شده باز شده — تضاد با VQ-SELFGOAL-005"
    # deny-list سخت — هرگز
    for bad in ("_ops/budget/money_gate.py", "_ops/cortex/auto_approve.py",
                "_ops/cortex/goal_directed.py", ".git/config", "_ops/germline.py",
                "OCTOPUS.env", "_ops/registry_scan.py", ".claude/settings.json",
                "_ops/cortex/code_autonomy.py".replace("code_autonomy", "capability_gate")):
        assert not CA.allowed_target(bad), f"deny نشد: {bad}"
    # خارج از allowlist
    assert not CA.allowed_target("_ops/live/server.py")
    assert not CA.allowed_target("") and not CA.allowed_target(None)


# ── شادو-تست — با run_fn فیک، هرگز git/سوییت/درختِ زنده ──────────────────────────
def t_d_shadow_test_injected_runner():
    calls = {}
    def fake_run(target, content):
        calls["target"] = target
        return {"ok": True, "green": True, "target": target, "diff": "1 file"}
    r = CA.shadow_test("_ops/cortex/stress.py", "# patch\n", run_fn=fake_run)
    assert r["ok"] and r["green"] and calls["target"] == "_ops/cortex/stress.py"
    # هدفِ deny → run_fn اصلاً صدا نمی‌شود (fail-closed پیش از تست)
    calls.clear()
    r2 = CA.shadow_test("_ops/budget/money_gate.py", "x", run_fn=fake_run)
    assert (not r2["ok"]) and "not-allowed" in r2["reason"] and "target" not in calls
    # محتوای خالی رد
    assert not CA.shadow_test("_ops/cortex/stress.py", "   ", run_fn=fake_run)["ok"]


# ── tick — قانونِ قلب end-to-end (freeze/act/red)، flag-off بدونِ نوشتن ────────────
def t_e_tick_heart_freeze_blocks_everything():
    CA.heart_mood = _mood_with(0.9, in_fear=True)   # فروپاشی
    ran = {"called": False}
    def fake_run(t, c):
        ran["called"] = True
        return {"ok": True, "green": True}
    out = CA.tick({"target": "_ops/cortex/stress.py", "content": "x\n"}, run_fn=fake_run)
    assert out["mood"]["verdict"] == "freeze" and not out["acted"]
    assert "heart-freeze" in out["decision"] and not ran["called"], "قلبِ فروپاشیده = صفر شادو-تست"


def t_f_tick_act_green_proposes():
    CA.heart_mood = _mood_with(0.35)                # جریان
    out = CA.tick({"target": "_ops/cortex/stress.py", "content": "# ok\n"},
                  run_fn=lambda t, c: {"ok": True, "green": True, "diff": "1"})
    assert out["acted"] and "آمادهٔ پیشنهاد" in out["decision"]
    # سوییتِ قرمز در سایه → رد، درختِ زنده امن
    out2 = CA.tick({"target": "_ops/cortex/stress.py", "content": "# bad\n"},
                   run_fn=lambda t, c: {"ok": True, "green": False})
    assert "قرمز" in out2["decision"]


def t_g_flag_off_writes_nothing():
    import os
    os.environ.pop(CA.FLAG, None)
    before = CA.SHADOW_LOG.exists()
    CA.heart_mood = _mood_with(0.35)
    CA.tick({"target": "_ops/cortex/stress.py", "content": "# x\n"},
            run_fn=lambda t, c: {"ok": True, "green": True})
    assert CA.SHADOW_LOG.exists() == before, "flag-off نباید لاگِ shadow بنویسد"


def t_h_never_touches_live_tree_guarantee():
    # قرارداد: بدونِ run_fn، shadow_test از git worktree استفاده می‌کند (اینجا صدا نمی‌زنیم)؛
    # هدفِ deny حتی مسیرِ واقعی را هم نمی‌رسد (fail-closed قبل از هر subprocess).
    r = CA.shadow_test(".git/hooks/pre-commit", "evil")
    assert not r["ok"] and "not-allowed" in r["reason"]


# ── سطح A actuator: هفت گیتِ apply_approved ───────────────────────────────────────
def _activate():
    CA.ACTIVATION.parent.mkdir(parents=True, exist_ok=True)
    CA.ACTIVATION.write_text("owner", "utf-8")
    if CA.KILL.exists():
        CA.KILL.unlink()


def _approve(aid):
    CA.APPROVALS_DIR.mkdir(parents=True, exist_ok=True)
    (CA.APPROVALS_DIR / f"{aid}.json").write_text(
        json.dumps({"verdict": "ok", "id": aid}), "utf-8")


def _fresh_log():
    if CA.APPLIED_LOG.exists():
        CA.APPLIED_LOG.unlink()


def t_i_actuator_seven_gates():
    patch = {"target": "_ops/cortex/stress.py", "content": "# x\n",
             "shadow_green": True, "id": "code-1"}
    calls = {"n": 0}
    def fake(t, c):
        calls["n"] += 1
        return {"applied": True, "green": True}
    _fresh_log()
    # ۱ بدونِ فعال‌سازی → رد
    if CA.ACTIVATION.exists():
        CA.ACTIVATION.unlink()
    CA.heart_mood = _mood_with(0.35)
    r = CA.apply_approved(patch, "code-1", apply_fn=fake)
    check("gate: not-activated blocks", (not r["ok"]) and "not-activated" in r["reason"] and calls["n"] == 0)
    _activate()
    # ۲ قلبِ freeze → رد
    CA.heart_mood = _mood_with(0.9, in_fear=True)
    r = CA.apply_approved(patch, "code-1", apply_fn=fake)
    check("gate: heart-freeze blocks", (not r["ok"]) and r["reason"] == "heart-freeze" and calls["n"] == 0)
    CA.heart_mood = _mood_with(0.35)
    # ۳ بدونِ تأییدِ مالک → رد
    r = CA.apply_approved(patch, "code-1", apply_fn=fake)
    check("gate: no-owner-approval blocks", (not r["ok"]) and r["reason"] == "no-owner-approval" and calls["n"] == 0)
    _approve("code-1")
    # ۴ هدفِ deny → رد
    r = CA.apply_approved({**patch, "target": "_ops/budget/money_gate.py"}, "code-1", apply_fn=fake)
    check("gate: deny target blocks", (not r["ok"]) and "not-allowed" in r["reason"])
    # ۵ بدونِ سبزِ سایه → رد
    r = CA.apply_approved({**patch, "shadow_green": False}, "code-1", apply_fn=fake)
    check("gate: shadow-not-green blocks", (not r["ok"]) and "shadow-not-green" in r["reason"])
    # ۷ همه پاس → اعمال
    r = CA.apply_approved(patch, "code-1", apply_fn=fake)
    check("all gates pass -> applied once", r["ok"] and r.get("applied") and calls["n"] == 1)
    # ۶ refractory: بلافاصله دوباره → رد
    r = CA.apply_approved({**patch, "id": "code-1b"}, "code-1", apply_fn=fake)
    check("gate: refractory blocks 2nd", (not r["ok"]) and "refractory" in r["reason"] and calls["n"] == 1)


def t_j_canary_red_auto_freezes():
    _activate(); _approve("code-2"); _fresh_log()
    CA.heart_mood = _mood_with(0.35)
    if CA.KILL.exists():
        CA.KILL.unlink()
    patch = {"target": "_ops/cortex/stress.py", "content": "# x\n",
             "shadow_green": True, "id": "code-2"}
    CA.apply_approved(patch, "code-2", apply_fn=lambda t, c: {"applied": True, "green": False})
    check("canary red -> auto-freeze (KILL created)", CA.KILL.exists())
    # و بعدِ freeze، active() = False → هیچ اعمالِ دیگری
    check("after freeze active() is False", CA.active() is False)
    CA.KILL.unlink()


def t_k_consume_approvals_applies_approved():
    _activate(); _fresh_log()
    CA.heart_mood = _mood_with(0.35)
    pend = CA.opslib.STATE_DIR / "cortex" / "pending-patches"
    pend.mkdir(parents=True, exist_ok=True)
    (pend / "code-9.json").write_text(json.dumps(
        {"id": "code-9", "target": "_ops/cortex/stress.py", "content": "# x\n",
         "shadow_green": True}), "utf-8")
    _approve("code-9")
    out = CA.consume_approvals(apply_fn=lambda t, c: {"applied": True, "green": True})
    check("consume applies approved code patch", out["applied"] == 1)
    # patchِ بی‌تأیید مصرف نمی‌شود
    (pend / "code-10.json").write_text(json.dumps(
        {"id": "code-10", "target": "_ops/cortex/stress.py", "content": "# y\n",
         "shadow_green": True}), "utf-8")
    _fresh_log()
    out2 = CA.consume_approvals(apply_fn=lambda t, c: {"applied": True, "green": True})
    check("unapproved patch is skipped", out2["applied"] == 0 and out2["skipped"] >= 1)


def t_l_propose_to_owner_stores_pending_fail_soft():
    # سایهٔ سبز + هدفِ مجاز → pending ذخیره، id=code-*، بی‌تلگرام fail-soft (posted=None)
    r = CA.propose_to_owner({"target": "_ops/cortex/stress.py", "content": "# p\n",
                             "shadow_green": True, "intent": "تست"})
    check("propose stores pending + returns code-id",
          r["ok"] and str(r["id"]).startswith("code-") and r["posted"] is None)
    pend = CA.opslib.STATE_DIR / "cortex" / "pending-patches" / f"{r['id']}.json"
    check("pending patch file written", pend.exists())
    # بدونِ سبزِ سایه یا هدفِ deny → رد، صفر pending
    assert not CA.propose_to_owner({"target": "_ops/cortex/stress.py", "content": "x"})["ok"]
    assert not CA.propose_to_owner({"target": "_ops/budget/money_gate.py", "content": "x",
                                    "shadow_green": True})["ok"]


# ── HEART-02: فیوزِ σ≥۱ روی heart_mood ِ *واقعی* (نه fake) ─────────────────────────
# رگرسیون‌گیر: باگِ قبلی σ را از hs['heart']/hs['sigma'] می‌خواند (همیشه None) پس فیوز مرده بود؛
# t_b آن را می‌پوشاند چون یک heart_mood ِ fake با منطقِ درستِ σ می‌سازد. اینجا heart_mood ِ
# واقعی را با یک heartstate ِ ساختگی (ساختارِ واقعی: shadow.sigma) اجرا می‌کنیم.
def _install_fake_heart(sigma, *, arousal=0.0, in_fear=False):
    import types
    hs = types.ModuleType("heartstate")
    hs.build = lambda: {"shadow": {"sigma": sigma}}
    st = types.ModuleType("stress")
    st.assess = lambda: {"organism_stress": arousal, "in_fear": in_fear, "level": ""}
    sys.modules["heartstate"] = hs
    sys.modules["stress"] = st


def t_m_real_sigma_fuse_fires():
    saved = {k: sys.modules.get(k) for k in ("heartstate", "stress")}
    try:
        # assert (نه check ِ نرم که harness نمی‌بیند) — این تستِ رگرسیونِ فیوزِ ایمنی
        # باید واقعاً بتواند شکست بخورد؛ وگرنه سبزِ دروغین است (یافتهٔ verifier).
        # σ=۱ → sig باید از shadow.sigma خوانده شود و فیوز شلیک کند (freeze)
        _install_fake_heart(1.0)
        m = _REAL_HEART_MOOD()
        assert m["verdict"] == "freeze" and m["mood"] == "فروپاشی" and m.get("sigma") == 1.0, \
            f"shadow.sigma>=1 باید freeze کند (sig درست خوانده شود): {m}"
        # σ=۰٫۵ (< ۱) و استرسِ صفر → freeze نباید شلیک کند
        _install_fake_heart(0.5)
        m2 = _REAL_HEART_MOOD()
        assert m2["verdict"] != "freeze" and m2.get("sigma") == 0.5, \
            f"shadow.sigma<1 نباید freeze کند: {m2}"
        # غیابِ σ (حالتِ عادیِ سایه، shadow خالی) → freeze نباید شلیک کند (اندام بی‌جهت freeze نشود)
        import types
        hs = types.ModuleType("heartstate"); hs.build = lambda: {"shadow": {}}
        sys.modules["heartstate"] = hs
        m3 = _REAL_HEART_MOOD()
        assert m3["verdict"] != "freeze", f"غیابِ sigma نباید freeze کند (اندام بی‌جهت neutered): {m3}"
        # مقدارِ حاضرِ خرابِ σ → محافظه‌کارانه freeze (fail-soft bad)
        _install_fake_heart("nan-ish-garbage")
        m4 = _REAL_HEART_MOOD()
        assert m4["verdict"] == "freeze", f"sigmaِ خراب باید محافظه‌کارانه freeze کند: {m4}"
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


# ═══ ممیزیِ متخاصمِ ۲۰۲۶-۰۷-۲۷ — دو بحرانیِ تأییدشده ═════════════════════════
ALLOWED_TARGET = "_ops/telegram_center/live_commands.py"

def t_n_shadow_env_cannot_spend_money():
    """بحرانی: `dict(os.environ)` کلیدهای پروایدر را به فرزند می‌داد، پس یک سوییتِ
    سایه می‌توانست تماسِ پولیِ واقعی بزند و سهمیه بسوزاند. تست باید **نتواند** خرج
    کند — این ایزولاسیون ساختاری است، نه قراردادی."""
    import os as _os
    from pathlib import Path as _P
    saved = dict(_os.environ)
    for k, v in {"FUGU_API_KEY": "x", "SAKANA_API_KEY": "x", "GLM_API_KEY": "x",
                 "ZAI_API_KEY": "x", "TELEGRAM_BOT_TOKEN": "x",
                 "TG_CENTER_BOT_TOKEN": "x", "LITELLM_MASTER_KEY": "x",
                 "SOME_SECRET": "x", "DB_PASSWORD": "x"}.items():
        _os.environ[k] = v
    try:
        env = CA._shadow_env(_P("/tmp/wt"))
        leaked = [k for k in env if any(
            s in k.upper() for s in ("API_KEY", "TOKEN", "SECRET", "PASSWORD"))]
        check("هیچ اعتبارنامه‌ای به سوییتِ سایه نشت نمی‌کند", not leaked)
        check("مسیرها به worktree پین‌اند",
              env.get("ORG_ROOT") == str(_P("/tmp/wt"))
              and env.get("REAL_VAULT") == str(_P("/tmp/wt")))
        check("OPS_DIR/BUDGET_STATE پاک شده‌اند",
              "OPS_DIR" not in env and "BUDGET_STATE" not in env)
        check("سوییت می‌داند در سایه است", env.get("OCTOPUS_SHADOW_SUITE") == "1")
        check("PATH حفظ شده (سوییت باید بدود)", bool(env.get("PATH") or env.get("Path")))
    finally:
        _os.environ.clear()
        _os.environ.update(saved)


def t_o_green_is_measured_against_a_baseline_not_absolute():
    """بحرانی: worktree از HEAD ساخته می‌شود و `_ops/OCTOPUS-flags.cmd` عمداً
    gitignored است، پس `test_paid_router_dark_config` در هر worktree قرمز است —
    مستقل از پچ. «سبزِ مطلق» ساختاراً دست‌نیافتنی بود، پس هیچ پچی هرگز کارت نمی‌شد
    و هر تلاش یک نقص را می‌سوزاند. معیارِ درست: هیچ شکستِ **تازه**."""
    calls = {"n": 0}

    def fake_suite(wt, env, timeout=600):
        calls["n"] += 1
        # مبنا: دو قرمزِ محیطی. کاندید: همان دو، بدونِ قرمزِ تازه.
        return {"code": 1, "fails": {"test_paid_router_dark_config",
                                     "test_llm_call_inventory"}, "tail": "t"}

    real_suite, real_env = CA._run_suite, CA._shadow_env
    CA._run_suite = fake_suite
    CA._shadow_env = lambda wt: {}
    try:
        import subprocess as _sp
        from pathlib import Path as _P
        real_run = _sp.run

        def fake_run(cmd, **kw):
            class R:
                returncode = 0
                stdout = " 1 file changed"
                stderr = ""
            if "worktree" in cmd and "add" in cmd:
                wt = _P(cmd[cmd.index("add") + 2])
                (wt / "_ops" / "telegram_center").mkdir(parents=True, exist_ok=True)
                (wt / "_ops" / "telegram_center" / "live_commands.py").write_text("old", "utf-8")
            return R()

        _sp.run = fake_run
        try:
            r = CA._git_shadow_test(ALLOWED_TARGET, "new content")
        finally:
            _sp.run = real_run
        check("مبنا و کاندید هر دو دویدند", calls["n"] == 2)
        check("قرمزِ محیطی سبز را نمی‌کشد", r.get("green") is True)
        check("قرمزهای مبنا گزارش می‌شوند", len(r.get("baseline_fails") or []) == 2)
        check("هیچ شکستِ تازه‌ای نیست", r.get("new_fails") == [])
    finally:
        CA._run_suite, CA._shadow_env = real_suite, real_env


def t_p_a_patch_that_breaks_a_test_is_still_red():
    """گاردِ معکوس: مبنا نباید به بهانه‌ای برای قبولِ پچِ خراب تبدیل شود."""
    seq = [{"code": 1, "fails": {"test_env_red"}, "tail": "base"},
           {"code": 1, "fails": {"test_env_red", "test_broken_by_patch"}, "tail": "cand"}]
    real_suite, real_env = CA._run_suite, CA._shadow_env
    CA._run_suite = lambda wt, env, timeout=600: seq.pop(0)
    CA._shadow_env = lambda wt: {}
    try:
        import subprocess as _sp
        from pathlib import Path as _P
        real_run = _sp.run

        def fake_run(cmd, **kw):
            class R:
                returncode = 0
                stdout = ""
                stderr = ""
            if "worktree" in cmd and "add" in cmd:
                wt = _P(cmd[cmd.index("add") + 2])
                (wt / "_ops" / "telegram_center").mkdir(parents=True, exist_ok=True)
                (wt / "_ops" / "telegram_center" / "live_commands.py").write_text("old", "utf-8")
            return R()

        _sp.run = fake_run
        try:
            r = CA._git_shadow_test(ALLOWED_TARGET, "new")
        finally:
            _sp.run = real_run
        check("شکستِ تازه سبز نمی‌شود", r.get("green") is False)
        check("شکستِ تازه نام‌برده می‌شود", r.get("new_fails") == ["test_broken_by_patch"])
    finally:
        CA._run_suite, CA._shadow_env = real_suite, real_env


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(checks)
    # رفعِ green-lie: check()های نرم فقط _C.failed را بالا می‌برند و raise نمی‌کنند،
    # پس harness.run آن‌ها را نمی‌بیند. exit باید به هر دو نگاه کند وگرنه شکستِ
    # درون‌تابعیِ check() بی‌صدا سبز می‌شود.
    total_failed = failed + _C.failed
    print(f"\n{'✅' if not total_failed else '❌'} test_code_autonomy: "
          f"{len(checks) - failed}/{len(checks)}"
          + (f" · +{_C.failed} soft-check failure(s)" if _C.failed else ""))
    sys.exit(1 if total_failed else 0)
