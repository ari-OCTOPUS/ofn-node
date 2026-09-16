#!/usr/bin/env python3
"""test_tg_power.py — مرکزِ فرماندهیِ تلگرام: ردهٔ A (مکث/ادامهٔ تک‌پا) + ردهٔ B (قدرت).

قراردادها (رأی مالک 2026-07-17):
- ردهٔ A: pause/resume فایلِ state/leg-<key>-paused.flag را می‌سازد/برمی‌دارد؛
  wiring.leg_paused هر ضربان می‌بیند؛ studio_pf به projectf-paused.flag نگاشت.
- ردهٔ B: بدونِ OCTOPUS_TG_POWER=1 هیچ اکشنی اجرا نمی‌شود (fail-closed)؛ با فلگ،
  فقط بعد از تأییدِ دوکلیکِ تازه (arm→confirm ≤180s) اجرا می‌شود.
- set_flag فقط whitelist/0-1؛ apply_budget اعتبارسنجی قبل از جایگزینی + backup.
- غیرمالک = سکوتِ مطلق. audit content-free نوشته می‌شود.
صفر شبکه (FakeClient) و صفر نوشتن خارج از temp harness.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-power")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib     # noqa: E402
import center     # noqa: E402
import power      # noqa: E402
import wiring     # noqa: E402


class FakeClient:
    """صفر شبکه — فقط ضبطِ send/edit/answer (قراردادِ tg_api)."""
    def __init__(self, owner_id=777):
        self.owner_id = owner_id
        self.calls: list = []
        self._mid = 100

    def wired(self):
        return True

    def is_owner(self, u):
        frm = ((u.get("message") or {}).get("from")
               or (u.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def send(self, text, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self._mid += 1
        self.calls.append(("send", text, keyboard))
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", message_id, text, keyboard))
        return True

    def answer_callback(self, cid, text=""):
        self.calls.append(("answer", cid, text))
        return True

    def set_commands(self, commands):
        self.calls.append(("set_commands", list(commands)))
        return True


def _cb(data, owner=True, mid=555):
    return {"callback_query": {"id": "cb1", "data": data,
                               "from": {"id": 777 if owner else 666},
                               "message": {"message_id": mid,
                                           "chat": {"id": -100123}}}}


def _msg(text, owner=True):
    return {"message": {"text": text, "from": {"id": 777 if owner else 666},
                        "chat": {"id": -100123}}}


def _mk():
    return center.Center(client=FakeClient(), clock=lambda: 1000.0)


def _clean():
    for k in power.PAUSABLE_LEGS:
        try:
            power._pause_path(k).unlink(missing_ok=True)
        except OSError:
            pass
    for p in (opslib.STOP_ORGANISM, opslib.HALT_ALL,
              opslib.OPS / "RESTART-REQUESTED"):
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
    os.environ.pop(power.POWER_FLAG, None)


# ─── ردهٔ A: مکث/ادامهٔ تک‌پا ─────────────────────────────────────────────────────
def t_a_menu_command_sends_keyboard():
    _clean()
    c = _mk()
    r = c.handle_update(_msg("/menu"))
    assert r and r["sent"] is True
    kind, text, kb = c._client.calls[-1]
    assert kind == "send" and "فرماندهی" in text and kb, "منو باید کیبورد داشته باشد"


def t_b_nonowner_total_silence():
    _clean()
    c = _mk()
    assert c.handle_update(_msg("/menu", owner=False)) is None
    assert c.handle_update(_cb("lg:lead:p", owner=False)) is None
    assert not power.leg_paused("lead"), "غیرمالک نباید هیچ اثری بگذارد"
    assert c._client.calls == [], "غیرمالک = سکوتِ مطلق (نه حتی answer)"


def t_c_pause_resume_leg_runtime():
    _clean()
    c = _mk()
    r = c.handle_update(_cb("lg:lead:p"))
    assert r["ok"] is True and power.leg_paused("lead")
    assert wiring.leg_paused("lead") is True, "wiring باید همان فایل را ببیند"
    r2 = c.handle_update(_cb("lg:lead:r"))
    assert r2["ok"] is True and not power.leg_paused("lead")


def t_d_studio_pf_maps_to_existing_flag():
    _clean()
    ok, _ = power.pause_leg("studio_pf")
    assert ok and (opslib.STATE_DIR / "projectf-paused.flag").exists(), \
        "studio_pf باید به فایلِ موجودِ projectf-paused.flag نگاشت شود"
    power.resume_leg("studio_pf")


def t_e_wiring_beats_skip_paused():
    _clean()
    os.environ["OCTOPUS_WIRE_ZIMAN"] = "1"
    try:
        power.pause_leg("ziman")
        assert wiring.ziman_beat(leg=object()) is None, \
            "پای مکث‌شده نباید بتپد (حتی با فلگِ روشن)"
    finally:
        os.environ.pop("OCTOPUS_WIRE_ZIMAN", None)
        power.resume_leg("ziman")


# ─── ردهٔ B: fail-closed بدونِ فلگ + دوکلیک ─────────────────────────────────────────
def t_f_power_off_locks_risky_frees_emergency():
    """قراردادِ ترکیب (2026-07-17): بدونِ فلگ، ریسک‌دارها (restart/فلگ/بودجه) قفل؛
    ترمزِ اضطراری (پنیک/توقف/ادامه) آزاد — چون بعد از HALT تنها کانالِ زنده همین است."""
    _clean()
    for fn in (power.restart_organism, power.apply_budget):
        ok, msg = fn()
        assert ok is False and power.POWER_FLAG in msg, f"{fn.__name__} باید قفل باشد"
    ok, _ = power.set_flag("OCTOPUS_OBS_ALERT", True)
    assert ok is False, "فلگ‌ها باید قفل باشند"
    assert not opslib.STOP_ORGANISM.exists()
    # اضطراری‌ها بدونِ فلگ کار می‌کنند (فقط-مالک + دوکلیک در center)
    ok, _ = power.panic()
    assert ok is True and opslib.HALT_ALL.exists(), "پنیک نباید پشتِ قفل باشد"
    ok, _ = power.resume_all()
    assert ok is True and not opslib.HALT_ALL.exists(), "ادامه از پنیک هم اضطراری است"
    ok, _ = power.stop_organism()
    assert ok is True and opslib.STOP_ORGANISM.exists(), "توقف نباید پشتِ قفل باشد"
    _clean()


def t_g_two_tap_restart_executes():
    _clean()
    os.environ[power.POWER_FLAG] = "1"
    try:
        c = _mk()
        c.handle_update(_cb("pw:rs"))                       # قدمِ ۱: مسلح
        assert not opslib.STOP_ORGANISM.exists(), "arm نباید اجرا کند"
        r = c.handle_update(_cb("pwc:rs"))                  # قدمِ ۲: تأیید
        assert r["ok"] is True
        assert opslib.STOP_ORGANISM.exists()
        assert (opslib.OPS / "RESTART-REQUESTED").exists(), \
            "ری‌استارتِ روتین = هر دو سنتینل (قراردادِ RUN-ORGANISM.bat)"
    finally:
        _clean()


def t_h_confirm_without_arm_or_stale_refused():
    _clean()
    os.environ[power.POWER_FLAG] = "1"
    try:
        c = _mk()
        r = c.handle_update(_cb("pwc:st"))                  # بدونِ arm
        assert "expired" in r and not opslib.STOP_ORGANISM.exists()
        # arm با clockِ 1000 → confirm با clockِ 2000 (کهنه‌تر از ARM_FRESH_S)
        c2 = center.Center(client=FakeClient(), clock=lambda: 1000.0)
        c2.handle_update(_cb("pw:st"))
        c3 = center.Center(client=c2._client, clock=lambda: 2000.0)
        r3 = c3.handle_update(_cb("pwc:st"))
        assert "expired" in r3 and not opslib.STOP_ORGANISM.exists(), \
            "تأییدِ کهنه باید باطل باشد"
    finally:
        _clean()


def t_i_flag_whitelist_and_file_write():
    _clean()
    os.environ[power.POWER_FLAG] = "1"
    fc = power._flags_cmd_path()
    try:
        fc.write_text("@echo off\nset OCTOPUS_OBS_ALERT=0\n", "utf-8")
        ok, msg = power.set_flag("OCTOPUS_OBS_ALERT", True)
        assert ok and "بوتِ بعدی" in msg, "پیام باید صادقانه بگوید اثر در بوتِ بعد"
        assert "set OCTOPUS_OBS_ALERT=1" in fc.read_text("utf-8")
        ok2, _ = power.set_flag("TOTALLY_FAKE_FLAG", True)
        assert ok2 is False, "خارج از whitelist ممنوع"
        ok3, _ = power.toggle_flag("OCTOPUS_OBS_ALERT")
        assert ok3 and "set OCTOPUS_OBS_ALERT=0" in fc.read_text("utf-8")
    finally:
        fc.unlink(missing_ok=True)
        _clean()


def t_j_apply_budget_surgical_and_validated():
    _clean()
    os.environ[power.POWER_FLAG] = "1"
    epochs = opslib.BUDGET_DIR / "epochs"
    epochs.mkdir(parents=True, exist_ok=True)
    yp = opslib.BUDGETS_YAML
    orig = yp.read_text("utf-8") if yp.exists() else None
    try:
        (epochs / "epoch-99999999T000000.json").write_text(json.dumps(
            {"allocation_dry": {"grants": {
                "ZIMAN": {"total_month_aud": 7.5},
                "GHOST_ORGAN": {"total_month_aud": 3.0}}}}), "utf-8")
        yp.parent.mkdir(parents=True, exist_ok=True)
        yp.write_text("# کامنتِ مهم\nglobal:\n  cap_monthly: 30\nprojects:\n"
                      "  ZIMAN: {floor: 1, human_priority: 0.5}\n", "utf-8")
        ok, msg = power.apply_budget()
        assert ok, msg
        txt = yp.read_text("utf-8")
        assert "cap_monthly: 7.5" in txt and "# کامنتِ مهم" in txt, \
            "ویرایش جراحی: cap نوشته + کامنت سالم"
        import yaml
        parsed = yaml.safe_load(txt)
        assert parsed["projects"]["ZIMAN"]["cap_monthly"] == 7.5
        assert parsed["global"]["cap_monthly"] == 30, "global دست‌نخورده"
        assert list(yp.parent.glob("budgets.yaml.bak-*")), "backup باید باشد"
    finally:
        for b in yp.parent.glob("budgets.yaml.bak-*"):
            b.unlink(missing_ok=True)
        for e in epochs.glob("epoch-99999999*"):
            e.unlink(missing_ok=True)
        if orig is not None:
            yp.write_text(orig, "utf-8")
        try:
            opslib.load_budgets(force=True)
        except Exception:  # noqa: BLE001
            pass
        _clean()


def t_k_audit_trail_written():
    _clean()
    power.pause_leg("mining")
    power.resume_leg("mining")
    p = opslib.STATE_DIR / "telegram" / "power-audit.jsonl"
    assert p.exists()
    rows = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]
    acts = [r["action"] for r in rows[-2:]]
    assert acts == ["pause:mining", "resume:mining"], acts
    _clean()


def t_l_menu_navigation_edits_in_place():
    _clean()
    c = _mk()
    r = c.handle_update(_cb("mn:sy", mid=42))
    assert r["page"] == "sy"
    edits = [x for x in c._client.calls if x[0] == "edit"]
    assert edits and edits[-1][1] == 42, "ناوبری باید همان پیام را edit کند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_power: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
