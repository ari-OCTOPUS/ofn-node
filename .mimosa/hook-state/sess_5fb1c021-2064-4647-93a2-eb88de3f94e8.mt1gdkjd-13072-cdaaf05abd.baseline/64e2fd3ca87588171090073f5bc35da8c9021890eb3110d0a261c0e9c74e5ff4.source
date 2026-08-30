"""test_heart_loop.py — HH-P2/P3/P5/P6: interface + کوپلِ Governor + shadow-wiring + دکترِ w-slow.

flag خاموش = no-regression اثبات‌شده؛ predicateِ ۸شرطی امروز ساختاراً بسته؛
Doctor فقط setpoint (هرگز نرخ)؛ کوپل فقط cadence (هرگز پول).
"""
import datetime as _dt
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("heart-loop")

import heart.interface as hi          # noqa: E402
import heart.producers as producers   # noqa: E402
import heart.shadow as shadow         # noqa: E402
import heart.doctor_setpoint as ds    # noqa: E402
import heart.autoregulation as ar     # noqa: E402
import governor_epoch                 # noqa: E402
import wiring                         # noqa: E402
import opslib                         # noqa: E402


def _write_signals(v=None, v_auth=True, cpi=None, delta=None):
    sig = {"ts": opslib.now_iso(), "schema": "heart-signals.v1",
           "velocity": {"velocity_per_hr": v, "authoritative": v_auth,
                        "components": {}, "sample_size": 10},
           "cpi": {"cpi_0_1": cpi, "authoritative": cpi is not None},
           "delta_self": delta or {"authoritative": False},
           "gate0_live_producer": bool((delta or {}).get("authoritative"))}
    producers.PULSE_DIR.mkdir(parents=True, exist_ok=True)
    with opslib.LockedJson(producers.SIGNALS_PATH) as lj:
        lj.write(sig)
    return sig


# ── P2: interface ────────────────────────────────────────────────────────────────
def t_a_interface_validate_and_roundtrip():
    ok = hi.HeartParams(viable_band_lo=1.0, viable_band_hi=4.0, epoch_seq=3)
    assert ok.validate() == []
    assert ok.viable_band == (1.0, 4.0)
    bad = hi.HeartParams(target_sigma=1.5)               # σ-cap قانونِ اساسی
    assert any("target_sigma" in e for e in bad.validate())
    inv = hi.HeartParams(viable_band_lo=5.0, viable_band_hi=1.0)
    assert any("وارونه" in e for e in inv.validate())
    rt = hi.HeartParams.from_json(ok.to_json())
    assert rt == ok
    assert hi.read_setpoint() is None                    # غایب → None (fail-soft)
    assert hi.write_setpoint(bad) is False               # نامعتبر نوشته نمی‌شود
    assert hi.write_setpoint(ok) is True
    assert hi.read_setpoint() == ok


# ── P3: کوپلِ Governor (additive، پشتِ flag) ─────────────────────────────────────
def t_b_governor_flag_off_no_heart_keys():
    os.environ.pop("OCTOPUS_WIRE_HEART", None)
    rec = governor_epoch.run_epoch()
    assert "heart_autoreg" not in rec
    assert "next_epoch_minutes_raw" not in rec


def t_c_governor_flag_on_cpi_tightens_epoch():
    """CPI بالا (velocity داخل باند) → epoch کش می‌آید (سفت‌تر)، هرگز کوتاه‌تر."""
    _write_signals(v=3.0, cpi=0.9)
    hi.write_setpoint(hi.HeartParams(epoch_seq=1))
    os.environ["OCTOPUS_WIRE_HEART"] = "1"
    try:
        rec = governor_epoch.run_epoch()
        assert rec.get("heart_autoreg", {}).get("available") is True
        assert rec["heart_autoreg"]["epoch_damping"] > 1.5
        assert rec["next_epoch_minutes"] >= rec["next_epoch_minutes_raw"]
        assert rec["next_epoch_minutes"] <= 120.0        # هرگز بالای base×2
        # ناوردیِ پول: تخصیص دست‌نخورده — هیچ کلیدِ heart داخلِ allocation
        assert "heart" not in json.dumps(rec.get("allocation_dry", {}))
    finally:
        os.environ.pop("OCTOPUS_WIRE_HEART", None)


def t_d_velocity_pressure_bounded():
    """استالِ کامل → فشار دقیقاً سقفِ 0.5 (ضربان Governor را تسخیر نمی‌کند)."""
    sp = hi.HeartParams()
    p = ar.velocity_pressure({"velocity_per_hr": 0.0, "authoritative": True}, sp)
    assert p["pressure"] == 0.5
    p2 = ar.velocity_pressure({"velocity_per_hr": 3.0, "authoritative": True}, sp)
    assert p2["pressure"] == 0.0
    p3 = ar.velocity_pressure({"velocity_per_hr": None}, sp)
    assert p3["pressure"] == 0.0                          # fail-neutral
    ct = ar.cpi_tightening({"cpi_0_1": 1.0})
    assert 1.0 <= ct["epoch_damping"] <= 2.0


# ── P5: wiring + shadow + predicate ─────────────────────────────────────────────
def t_e_heart_beat_flag_off_is_noop():
    os.environ.pop("OCTOPUS_WIRE_HEART", None)
    assert wiring.heart_beat(beat=100) is None
    assert not shadow.SHADOW_SINK.exists()               # هیچ سایه‌ای نوشته نشده


def t_f_heart_beat_shadow_writes_sink_never_period():
    os.environ["OCTOPUS_WIRE_HEART"] = "1"
    try:
        wiring._HEART_STATE["last_epoch"] = 0
        out = wiring.heart_beat(beat=10)
        assert out is not None
        assert shadow.SHADOW_SINK.exists()
        assert shadow.SHADOW_LATEST.exists()
        latest = shadow.read_shadow_latest()
        assert latest["mode"] == "shadow"
        assert latest["production_wire"]["open"] is False
        # σ در mini-vault غایب → fail-closed به MAX (استراحت) — نه کرش
        assert latest["period_s"] == 900.0
        assert out["wire_open"] is False
        # ضدِ aliasing: همان پنجره دوباره fire نمی‌شود
        assert wiring.heart_beat(beat=10) is None
        # kill-switch: STOP → None حتی با flag روشن
        opslib.STOP_ORGANISM.write_text("stop", "utf-8")
        try:
            wiring._HEART_STATE["last_epoch"] = 0
            assert wiring.heart_beat(beat=20) is None
        finally:
            opslib.STOP_ORGANISM.unlink()
    finally:
        os.environ.pop("OCTOPUS_WIRE_HEART", None)


def t_g_production_wire_closed_today_and_unforgeable():
    # rollover 2026-07-21: تقویم به LIVE_GATE_DATE رسید و سپرِ تاریخِ واقعی باز شد؛ این تست
    # «قراردادِ پیش از تاریخ» را می‌سنجد → تاریخ را قطعی می‌بندیم (الگوی test_cockpit_golive_honesty).
    _real_gate = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2099, 1, 1)
    try:
        ok, reasons = shadow.production_wire_open()
        assert ok is False
        assert len(reasons) >= 4, reasons
        assert any("live locked until" in r or "activation" in r for r in reasons)
        # جعلِ تک‌شرط: ساختنِ ACTIVATION-PULSE.flag به‌تنهایی هیچ دری باز نمی‌کند
        shadow.ACT_PULSE.parent.mkdir(parents=True, exist_ok=True)
        shadow.ACT_PULSE.write_text("forged", "utf-8")
        try:
            ok2, reasons2 = shadow.production_wire_open()
            assert ok2 is False
            assert any("live locked until" in r for r in reasons2)   # سپرِ تاریخ حاکم
        finally:
            shadow.ACT_PULSE.unlink()
    finally:
        opslib.LIVE_GATE_DATE = _real_gate


def t_h_organism_seam_is_conditional_and_guarded():
    """ساختاری: seam ارگانیسم فقط پشتِ نتیجهٔ heart_beat + کلیدِ شرطی + init پیش از try
    + کفِ زندهٔ ۶۰s (HH-P8 رأی ۳)."""
    src = (Path(__file__).resolve().parent.parent / "organism.py").read_text("utf-8")
    assert '_heart_status = None       # HH-P5' in src          # init پیش از try
    assert '**({"heart": _heart_status} if _heart_status else {})' in src
    assert '_heart_status.get("wire_open")' in src              # زنده فقط با predicate
    assert 'production_wire_open()' not in src                  # هیچ I/O predicate در tick
    assert 'HEART_LIVE_FLOOR_S", "60"' in src                   # کفِ زندهٔ مصوب (HH-P8)
    assert 'max(30.0, min(900.0' not in src                     # کفِ ۳۰ از seam حذف شد


def t_h2_setpoint_seeds_from_first_observation():
    """HH-P8 رأی ۱: بدونِ setpointِ قبلی + مشاهدهٔ v → باندِ seedشده حولِ واقعیت؛
    بدونِ مشاهده → نوشتن به تعویق."""
    import heart.doctor_setpoint as ds2
    if hi.SETPOINT_PATH.exists():
        hi.SETPOINT_PATH.unlink()                       # بدونِ prev
    _write_signals(v=None, cpi=None)
    out0 = ds2.run_epoch_setpoint(write=True)
    assert out0["written"] is False
    assert out0["reason"] == "awaiting-first-velocity"
    assert hi.read_setpoint() is None
    _write_signals(v=0.08, cpi=None)
    out1 = ds2.run_epoch_setpoint(write=True)
    assert out1["written"] is True, out1
    assert out1.get("rationale", "").startswith("seeded")
    sp = hi.read_setpoint()
    assert sp is not None and sp.epoch_seq == 1
    assert sp.viable_band_lo <= 0.08 <= sp.viable_band_hi
    assert sp.viable_band_hi < 0.5                      # نه پیش‌فرضِ 0.5..6 (کالیبره)


def t_h3_setpoint_cadence_survives_restart():
    """w-slow واقعاً کند بماند: last_setpoint_epoch در حافظه است، پس هر restartِ واچ‌داگ
    قبلاً یک epochِ اضافه می‌نوشت و hysteresis ±۲۰٪ در یک روز چندبار اعمال می‌شد
    (شاهد: ledger ‏07-23/24). بازیابیِ stateless: setpointِ تازهٔ روی دیسک = این پنجره served."""
    os.environ["OCTOPUS_WIRE_HEART"] = "1"
    os.environ["CHRONO_HEART_SETPOINT_EVERY_N_BEATS"] = "1440"
    try:
        _write_signals(v=2.0, cpi=0.1)
        hi.write_setpoint(hi.HeartParams(epoch_seq=5))
        wiring._HEART_STATE["last_epoch"] = 0
        wiring._HEART_STATE["last_setpoint_epoch"] = 0
        out1 = wiring.heart_beat(beat=1450)               # اولین ضربانِ بعد از restart
        seq1 = hi.read_setpoint().epoch_seq
        assert out1 is not None
        assert seq1 == 5, f"setpointِ تازه نباید دوباره نوشته شود (seq={seq1})"
        assert "setpoint_epoch_seq" not in out1, out1
        # همان پنجره، restartِ دوم → باز هم بدونِ نوشتن (idempotent)
        wiring._HEART_STATE["last_epoch"] = 0
        wiring._HEART_STATE["last_setpoint_epoch"] = 0
        wiring.heart_beat(beat=1460)
        assert hi.read_setpoint().epoch_seq == 5
        # setpointِ کهنه (بیرونِ پنجره) → cadence مشروع دوباره می‌نویسد
        p = hi.SETPOINT_PATH
        d = json.loads(p.read_text("utf-8"))
        d["ts"] = (_dt.datetime.now() - _dt.timedelta(days=3)).isoformat(timespec="seconds")
        p.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        wiring._HEART_STATE["last_epoch"] = 0
        wiring._HEART_STATE["last_setpoint_epoch"] = 0
        out2 = wiring.heart_beat(beat=1470)
        assert out2.get("setpoint_epoch_seq") == 6, out2
        assert hi.read_setpoint().epoch_seq == 6
    finally:
        os.environ.pop("OCTOPUS_WIRE_HEART", None)
        os.environ.pop("CHRONO_HEART_SETPOINT_EVERY_N_BEATS", None)


# ── P6: دکترِ w-slow ─────────────────────────────────────────────────────────────
def t_i_setpoint_hysteresis_and_monotonic_seq():
    prev = hi.HeartParams(viable_band_lo=0.5, viable_band_hi=6.0, epoch_seq=7)
    jump = _write_signals(v=60.0, cpi=0.0)   # جهشِ بزرگ
    p = ds.propose_setpoint(prev, jump)
    mid_prev, mid_new = 3.25, (p.viable_band_lo + p.viable_band_hi) / 2
    assert mid_new <= mid_prev * 1.2 * 1.5 + 1e-6   # hysteresis ±۲۰٪ (+گشایشِ سقف)
    assert p.epoch_seq == 8
    assert p.validate() == []
    # CPI بالا → باند جمع می‌شود (میانه پایین می‌آید)
    shrink = ds.propose_setpoint(prev, _write_signals(v=None, cpi=0.95))
    assert (shrink.viable_band_lo + shrink.viable_band_hi) / 2 < mid_prev
    # خروجی هرگز فیلدِ نرخ ندارد (ساختاری، ADR)
    assert "period" not in json.dumps(p.to_json())


def t_j_setpoint_epoch_writes_and_llm_gated():
    # rollover 2026-07-21: سپرِ تاریخ را قطعی ببند تا قراردادِ «llm گیت‌خورده، $0» سنجیده شود.
    _real_gate = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2099, 1, 1)
    try:
        _write_signals(v=2.0, cpi=0.2)
        out = ds.run_epoch_setpoint(write=True)
        assert out["written"] is True
        sp = hi.read_setpoint()
        assert sp is not None and sp.epoch_seq == out["epoch_seq"]
        assert out["llm"] is None                 # live-gate (تاریخ) → قطعی، $0
        ok, why = opslib.live_gate_open(ds.ACT_HEART_DOCTOR)
        assert ok is False and "live locked" in why
    finally:
        opslib.LIVE_GATE_DATE = _real_gate


def t_k_structural_doctor_no_toplevel_money():
    """I2: مسیرِ LLM موظف به organ_gate است ولی فقط lazy — هیچ importِ top-level پول."""
    src = Path(ds.__file__).read_text("utf-8")
    head = src.split("def propose_setpoint")[0]
    assert "organ_gate" not in head               # top-level پاک
    assert "organ_gate.reserve" in src            # مسیرِ گیت‌خورده در تنِ live-gated
    assert "organ_gate.settle" in src
    assert "live_gate_open" in src


# ── P7: کارتِ قلب در کابین ───────────────────────────────────────────────────────
class _FakeHTTP:
    def __init__(self):
        self.posts = []

    def get(self, url, timeout):
        return {"ok": True, "result": []}

    def post(self, url, body, timeout_s=10.0):
        self.posts.append((url, body))
        return {"ok": True}


def t_l_cockpit_heart_card_renders_shadow():
    """کارتِ ضربان: بخشِ قلبِ ترکیبی با state واقعیِ همین تست‌ها (سایه/سیگنال/setpoint)؛
    سیمِ زنده بسته؛ هیچ نشتِ توکن؛ fail-soft بدونِ فایل."""
    import approval_channel as ac
    import cockpit_readmodel as crm
    state = Path(ENV["ops"]) / "state"
    fh = _FakeHTTP()
    ch = ac.TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                    state_dir=str(state),
                                    http_get=fh.get, http_post=fh.post)
    txt = ch._render_card("overview", "heart")
    assert "قلبِ ترکیبی" in txt
    assert "سیمِ زنده: 🔴" in txt              # امروز ساختاراً بسته
    assert "123:abc" not in txt                # هیچ secret در کارت
    assert "Gate-0" in txt
    # readmodel: read_heart از زیرشاخه‌های pulse/sim می‌خواند (یافتهٔ ریویو)
    rm = crm.CockpitReadModel(state_dir=str(state))
    hh = rm.read_heart()
    assert hh["shadow"].get("mode") == "shadow"
    assert hh["setpoint"].get("schema") == "HeartParams.v1"
    # fail-soft: state خالی → پیامِ 🟡، نه کرش
    empty = Path(ENV["root"]) / "empty-state"
    empty.mkdir(exist_ok=True)
    ch2 = ac.TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                     state_dir=str(empty),
                                     http_get=fh.get, http_post=fh.post)
    txt2 = ch2._render_card("overview", "heart")
    assert "هنوز سایه‌ای ثبت نشده" in txt2


# ── P6b: تفکیکِ آلارمِ مسیرِ bespokeِ دکتر (۲۰۲۶-۰۸-۰۶) ───────────────────────────
# مسیرِ زندهٔ دکتر (OCTOPUS_HEART_DOCTOR_USE_ROUTER خاموش، پیش‌فرض) با organ_gate/AUD
# و DeepSeekClient مستقیم کار می‌کند، پس فیکسِ model_router به آن نرسید. سه شرطِ
# «طراحی‌شده» باید از «خرابیِ واقعی» جدا شوند: قیمتِ قفل‌نشده (PriceNotLocked)، سقفِ
# بودجهٔ گیت، و سقفِ نرخِ provider (HTTP 429/402) → لحنِ آرامِ ℹ️؛ هر خطای دیگر →
# آلارمِ «heart doctor llm failed». صفر شبکه (client/organ_gate تزریقی).

def _doctor_client(ctor_exc=None, complete_exc=None):
    class _C:
        def __init__(self, role="econ", **kw):
            if ctor_exc is not None:
                raise ctor_exc

        def est_worst_case(self, chars, max_tokens=400):
            return 0.001

        def complete(self, system, user, max_tokens=400):
            if complete_exc is not None:
                raise complete_exc
            return {"text": '{"lo": 1.0, "hi": 4.0}', "cost_usd": 0.0, "model": "fugu"}
    return _C


def _drive_bespoke_doctor(reserve, client_cls):
    """ds.llm_refine را روی مسیرِ bespoke با گیتِ باز می‌راند؛ (out, alerts) را برمی‌گرداند."""
    import client as C
    import organ_gate as og
    sent = []
    saved = (opslib.alert, opslib.live_gate_open, og.reserve, og.settle,
             og.release, C.DeepSeekClient)
    opslib.alert = lambda msgs, **k: sent.extend(list(msgs))
    opslib.live_gate_open = lambda *a, **k: (True, "test-open")
    og.reserve = reserve
    og.settle = lambda *a, **k: {"ok": True}
    og.release = lambda *a, **k: {"ok": True}
    C.DeepSeekClient = client_cls
    os.environ.pop("OCTOPUS_HEART_DOCTOR_USE_ROUTER", None)
    ds._DOCTOR_LLM_ALERTED = False
    ds._DOCTOR_CAP_ALERTED = False
    sp = hi.HeartParams(viable_band_lo=1.0, viable_band_hi=4.0, epoch_seq=2)
    try:
        out = ds.llm_refine(sp, {})
    finally:
        (opslib.alert, opslib.live_gate_open, og.reserve, og.settle,
         og.release, C.DeepSeekClient) = saved
        ds._DOCTOR_LLM_ALERTED = False
        ds._DOCTOR_CAP_ALERTED = False
    return out, sent


def t_m_doctor_price_not_locked_is_dormant_not_broken():
    """قیمتِ قفل‌نشده = شرطِ طراحی‌شده (client قبل از شبکه امتناع می‌کند). باید ℹ️/
    «خفته» بدهد، نه آلارمِ «heart doctor llm failed» — همان کلاسِ باگِ model_router."""
    import client as C
    out, sent = _drive_bespoke_doctor(
        reserve=lambda *a, **k: {"allow": True, "reserved": 0.001},
        client_cls=_doctor_client(ctor_exc=C.PriceNotLocked("no price")))
    assert out is None
    blob = " ".join(sent)
    assert blob and blob.startswith("ℹ️"), blob
    assert ("خفته" in blob or "قفل نشده" in blob), blob
    assert "heart doctor llm failed" not in blob, blob


def t_n_doctor_budget_cap_gate_denial_is_calm_info():
    """گیتِ باز + سقفِ بودجهٔ AUD پر → یک خطِ آرامِ ℹ️. قبلاً کاملاً بی‌صدا بود، پس
    مالک نمی‌توانست «سکوت به‌خاطرِ سقف» را از «اصلاً اجرا نشد» تشخیص دهد."""
    out, sent = _drive_bespoke_doctor(
        reserve=lambda *a, **k: {"allow": False,
                                 "reason": "organ-monthly: AU$3.0000 > cap AU$2.00"},
        client_cls=_doctor_client())
    assert out is None
    blob = " ".join(sent)
    assert blob and "ℹ️" in blob and "طراحی‌شده" in blob, blob


def t_o_doctor_non_cap_gate_denial_stays_silent():
    """ردِ گیت که سقفِ بودجه *نیست* (state ناخوانا و…) همان‌طور بی‌صدا می‌ماند —
    organ_gate خودش آن مسیر را با FREEZE/آلارمِ خودش پوشش می‌دهد."""
    out, sent = _drive_bespoke_doctor(
        reserve=lambda *a, **k: {"allow": False, "reason": "organ-state-unreadable:x"},
        client_cls=_doctor_client())
    assert out is None
    assert sent == [], sent


def t_p_doctor_genuine_failure_stays_alarming():
    """complete() خطای واقعیِ transport/provider → لحنِ هشداری حفظ شود."""
    out, sent = _drive_bespoke_doctor(
        reserve=lambda *a, **k: {"allow": True, "reserved": 0.001},
        client_cls=_doctor_client(complete_exc=RuntimeError("network down")))
    assert out is None
    blob = " ".join(sent)
    assert "heart doctor llm failed" in blob, blob
    assert "ℹ️" not in blob, blob


def t_q_doctor_provider_rate_limit_reads_as_designed():
    """HTTP 429 provider (urllib.error.HTTPError، `.code` واقعی) = سقفِ نرخِ طراحی‌شده."""
    import urllib.error
    err = urllib.error.HTTPError("https://api.deepseek.com", 429, "rate", {}, None)
    out, sent = _drive_bespoke_doctor(
        reserve=lambda *a, **k: {"allow": True, "reserved": 0.001},
        client_cls=_doctor_client(complete_exc=err))
    assert out is None
    blob = " ".join(sent)
    assert "ℹ️" in blob and "429" in blob, blob
    assert "heart doctor llm failed" not in blob, blob


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_loop: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
