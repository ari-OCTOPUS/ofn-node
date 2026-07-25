#!/usr/bin/env python3
"""test_live_debug_fixes_2026_07_25.py — فیکس‌هایی که از دیباگِ **زندهٔ** ارگانیسم درآمد.
(۱۰ بخش، ~۴۵ چک. بخش‌های ۸–۱۰ بعد از بازسنجیِ نردبانِ AGI اضافه شدند.)

هر ادعا با شاهدِ زندهٔ ۲۰۲۶-۰۷-۲۵ (پس از ریستارتِ ۱۴:۱۴:۲۵) پشتیبانی می‌شود:

۱) spectral: یال در build_event_graph فقط از «خطا» ساخته می‌شود، پس ارگانیسمِ بی‌خطا
   گرافِ بی‌یال می‌دهد → L(G)=۰ → gap=0.000 و σ=1.00 → سنسور **سلامت را «critical»**
   اعلام می‌کرد. گواه: ۸ RFCِ یکسان در صفِ زنده، در حالی که phi_tِ Box در همان دقیقه
   sigma=0.0/gap=0.7321 داد. اکنون: بی‌ساختارِ خطا → سکوت؛ با ساختارِ خطا → همان حرفِ قبلی.

۲) RFC.created_ts persist نمی‌شد و __post_init__ در هر لود آن را now می‌کرد → همهٔ RFCها
   بعد از هر restart «نوزاد» می‌شدند و sweepِ سن‌محور هیچ‌وقت expire نمی‌کرد.

۳) PhiAccrual: با ۲ ack یک فاصله داریم → var=0 → std به کفِ 0.1×mean می‌افتد → یک سکونِ
   ~۲×mean کافی بود تا phi=300 (که *دقیقاً* سقفِ p_later=1e-300 است، نه عددی واقعی) و لِگ
   «مرده» اعلام شود. گواه: ۶۶ ری‌استارتِ self-heal، ۱۰۰٪ روی lead-naghshi، همه با phi=300.0.
   پنجرهٔ ۲-نمونه‌ای در هر بوت از نو ساخته می‌شود، پس هر بوت تکرار می‌شود و بعد خودش
   می‌خوابد (۱۵:۰۵:۴۹ همان لِگ بی‌هیچ فیکسی alive شد). ← نسخهٔ اولِ این توضیح «حلقهٔ
   بیرونی ۹.۵ دقیقه» می‌گفت که **غلط بود**؛ اندازه‌گیریِ تمیز ۶۰.۹s/beat داد.

۴) legs_diag: چرا یک لِگ failed است هرگز در state دیده نمی‌شد — فقط برچسبِ حالت.

۵) shadow.production_wire_open شرطِ Gate-0 را فقط با `authoritative` می‌سنجید، و آن با
   Δ *منفی* هم True است → «خودشناسیِ منفی» درِ ورودِ قلب به تولید را باز می‌کرد.

۶) wire_summary سه فلگِ مغزِ پولی را نداشت → «مسلح بودنِ مسیرِ پولی» فقط از فایلِ
   رازدارِ flags.cmd قابلِ فهم بود، نه از state/کاکپیت. (+ arm_gate_enforcing: قفلِ دومِ
   مسیرِ پولی تا ست‌نشدنِ OCTOPUS_REQUIRE_ARM تزئینی است — VQ-ARM-001.)

۷) متنِ آلارمِ router «fallback local» می‌گفت در حالی که caller اول tierهای پولیِ بعدی
   را امتحان می‌کند (در شاهدِ زنده primary افتاد و secondaryِ پولی جواب داد).

۸) شمارندهٔ شکستِ Fugu سراسری بود، پس بریکرِ auto-STOP-FUGU در الگوی «primary می‌افتد →
   secondary جواب می‌دهد» هرگز شلیک نمی‌کرد (۳ تایم‌اوتِ پیاپی، consecutive_failures=0).

۹) خودشناسی فقط لایهٔ بیرونیِ business_legs را می‌خواند، پس یک شبه-لِگ با live=False
   می‌دید که **ساختاراً مستقل از واقعیت** بود — منبعِ گزارشِ غلطِ «۱ لِگِ تجاری در وضعیتِ
   مرگ» در v10، در حالی که ۴ لِگ وجود دارد.

۱۰) opslib.alert() هیچ throttle نداشت و تنها اقدامِ context_fence همان alert است که به
   تلگرامِ مالک می‌رود → روشن‌کردنِ R5 می‌توانست اعلانِ واقعیِ halt را زیر سیلِ آلارم ببرد.

همه $0 و آفلاین. صفر نوشتن در درختِ زنده (harness sandbox).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("livefix")
OPS = Path(__file__).resolve().parent.parent
for _p in (OPS / "doctor", OPS / "heart", OPS / "cortex"):
    sys.path.insert(0, str(_p))

import opslib  # noqa: E402,F401
import chrono  # noqa: E402

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


class FakeClock:
    def __init__(self, t_ms: int = 1_000_000):
        self.t = t_ms

    def __call__(self) -> int:
        return self.t

    def advance(self, ms: int) -> int:
        self.t += ms
        return self.t


# ═══ ۱) گاردِ گرافِ دژنرهٔ spectral ════════════════════════════════════════════
def s1_spectral():
    from spectral import spectral_mine, build_event_graph
    healthy = {"organs": {"A": {}, "B": {}, "C": {}}, "errors": []}
    edges, n = build_event_graph(healthy)
    check(n == 3 and not edges,
          f"ارگانیسمِ بی‌خطا گرافِ بی‌یال می‌دهد (n={n}, edges={len(edges)}) — ریشهٔ باگ")
    check(spectral_mine(healthy) is None,
          "بی‌خطا → سکوت (قبلاً «σ≈1 … critical» می‌داد)")
    check(spectral_mine({"organs": {"A": {}}, "errors": [{"organ": "A"}]}) is None,
          "تک‌گره → سکوت (n<2)")
    real = {"organs": {"A": {}, "B": {}, "C": {}},
            "errors": [{"organ": "A"}, {"organ": "B"}]}
    e2, _ = build_event_graph(real)
    bn = spectral_mine(real)
    check(bool(e2) and bn is not None and bn.get("severity") in ("high", "critical"),
          f"با ساختارِ خطای واقعی همچنان حرف می‌زند (edges={len(e2)}, "
          f"severity={None if bn is None else bn.get('severity')}) — گارد over-block نکرد")
    check(spectral_mine({}) is None, "traceِ خالی → None (رفتارِ قبلی)")


# ═══ ۲) persistِ created_ts ════════════════════════════════════════════════════
def s2_created_ts():
    import doctor as doc
    r = doc.RFC(rfc_id="RFC-test01", bottleneck="b", fix="f",
                expected_lift="l", rollback="r")
    d = r.to_dict()
    check("created_ts" in d and float(d["created_ts"]) > 0,
          f"to_dict حالا created_ts دارد ({'created_ts' in d})")
    # round-tripِ دقیقاً همان فیلترِ _load_rfcs
    fields = {k: d[k] for k in doc.RFC.__dataclass_fields__ if k in d}
    r2 = doc.RFC(**fields)
    check(abs(r2.created_ts - r.created_ts) < 1e-6,
          "سن پس از لود حفظ می‌شود (نه ریست به now) → sweep می‌تواند expire کند")
    # سازگاریِ عقب: رکوردِ قدیمیِ بدونِ created_ts هنوز لود می‌شود
    old = {k: v for k, v in d.items() if k != "created_ts"}
    of = {k: old[k] for k in doc.RFC.__dataclass_fields__ if k in old}
    r3 = doc.RFC(**of)
    check(r3.created_ts > 0,
          "رکوردِ قدیمیِ بی‌created_ts هنوز لود می‌شود (__post_init__ پرش می‌کند)")


# ═══ ۳) تحمّلِ صادقِ phi ═══════════════════════════════════════════════════════
def s3_phi():
    GAP = 60_000
    os.environ.pop("OCTOPUS_CHRONO_PHI_HONEST", None)
    acc = chrono.PhiAccrual()
    acc.heard(0)
    acc.heard(GAP)
    check(acc.phi(GAP) < chrono.PHI_SUSPECT,
          f"فلگ خاموش: لحظهٔ ack → زنده (phi={acc.phi(GAP):.2f})")
    _old = acc.phi(GAP + 2 * GAP)
    check(_old >= chrono.PHI_DEAD,
          f"فلگ خاموش: یک سکونِ ۲×mean → «مرده» — رفتارِ قدیم حفظ شد (phi={_old:.1f})")

    os.environ["OCTOPUS_CHRONO_PHI_HONEST"] = "1"
    thin = chrono.PhiAccrual()
    thin.heard(0)
    thin.heard(GAP)
    _new = thin.phi(GAP + 10 * GAP)
    check(_new < chrono.PHI_DEAD,
          f"فلگ روشن: با ۱ فاصله هرگز «مرده» نمی‌شود (phi={_new:.2f} < {chrono.PHI_DEAD})")
    check(_new >= chrono.PHI_SUSPECT,
          f"فلگ روشن: ولی «مشکوک» می‌شود — سیگنال خفه نشد (phi={_new:.2f})")

    rich = chrono.PhiAccrual()
    for i in range(6):
        rich.heard(i * GAP)
    t = 5 * GAP + 2 * GAP
    os.environ["OCTOPUS_CHRONO_PHI_HONEST"] = "1"
    _h = rich.phi(t)
    os.environ["OCTOPUS_CHRONO_PHI_HONEST"] = "0"
    _o = rich.phi(t)
    check(_h < chrono.PHI_DEAD <= _o,
          f"با ۵ فاصله، سکونِ ۲×mean: روشن={_h:.2f} زنده · خاموش={_o:.1f} مرده "
          f"(کفِ std از 0.1 به {chrono.PHI_STD_FLOOR_FRAC} رفت)")
    os.environ.pop("OCTOPUS_CHRONO_PHI_HONEST", None)
    check(chrono.MIN_PHI_GAPS >= 2 and 0.0 < chrono.PHI_STD_FLOOR_FRAC <= 1.0,
          f"knobها کران‌دارند (MIN_PHI_GAPS={chrono.MIN_PHI_GAPS}, "
          f"STD_FLOOR_FRAC={chrono.PHI_STD_FLOOR_FRAC})")


# ═══ ۴) legs_diag در snapshot ══════════════════════════════════════════════════
def s4_legs_diag():
    clock = FakeClock()
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-livefix.db")
    bus = chrono.ChronoBus(clock)
    pm = chrono.Pacemaker(db=db, bus=bus, clock=clock)
    h = bus.register_leg("leg-probe")
    h.event()
    clock.advance(60_000)
    pm.beat_once()
    st = pm.status()
    check("legs_diag" in st, "status حالا legs_diag دارد")
    d = (st.get("legs_diag") or {}).get("leg-probe") or {}
    need = ("state", "phi", "phi_dead", "ack_samples", "silence_ms",
            "mean_gap_ms", "honest_tolerance")
    check(all(k in d for k in need),
          f"legs_diag همهٔ فیلدهای تشخیصی را دارد ({sorted(d)})")
    check(isinstance(d.get("ack_samples"), int) and d["ack_samples"] >= 2,
          f"ack_samples شمارشِ واقعی است ({d.get('ack_samples')})")
    check(d.get("phi") is not None and d.get("phi_dead") == chrono.PHI_DEAD,
          f"phi و آستانهٔ مرگ هر دو دیده می‌شوند (phi={d.get('phi')}, dead={d.get('phi_dead')})")
    check(st.get("legs", {}).get("leg-probe") == d.get("state"),
          "برچسبِ legs و legs_diag.state یک حقیقت‌اند (دو نامِ متناقض ممنوع)")


# ═══ ۵) Gate-0 در shadow: Δ منفی گیت را باز نکند ═══════════════════════════════
def s5_wire_gate():
    import shadow
    orig = shadow.producers.read_signals
    NEG = {"delta_self": {"authoritative": True, "delta_self_live": -0.027143},
           "gate0_live_producer": False}
    POS = {"delta_self": {"authoritative": True, "delta_self_live": 0.31},
           "gate0_live_producer": True}
    try:
        shadow.producers.read_signals = lambda: NEG
        ok, reasons = shadow.production_wire_open()
        blob = " | ".join(reasons)
        check(ok is False, "Δ منفی: گیت بسته است")
        check("Δ_selfِ زنده مثبت نیست" in blob or "delta_self_live=-0.027143" in blob,
              "Δ منفی: دلیلِ صریحِ Δ در فهرست هست (نه سکوت)")
        shadow.producers.read_signals = lambda: POS
        _ok2, reasons2 = shadow.production_wire_open()
        blob2 = " | ".join(reasons2)
        check("Δ_selfِ زنده مثبت نیست" not in blob2,
              "Δ مثبت: دلیلِ Δ حذف می‌شود (گیت بی‌جهت مسدود نمی‌کند)")
        check("Gate-0" not in blob2,
              "Δ مثبت + authoritative: شرطِ Gate-0 کاملاً پاس می‌شود")
        # فایلِ سیگنالِ قدیمی (بدونِ gate0_live_producer) → سقوط به قاعدهٔ قبلی
        shadow.producers.read_signals = lambda: {"delta_self": {"authoritative": True,
                                                                "delta_self_live": 0.5}}
        _ok3, reasons3 = shadow.production_wire_open()
        check("Gate-0" not in " | ".join(reasons3),
              "سیگنالِ قدیمیِ بی‌gate0 → سقوطِ سازگار به authoritative (بدونِ رگرسیون)")
    finally:
        shadow.producers.read_signals = orig


# ═══ ۶) wire_summary سه فلگِ پولی را نشان دهد ══════════════════════════════════
def s6_wire_summary():
    import wiring
    keys = ("paid_governor_router", "paid_heart_doctor_router", "paid_doctor_selfknow")
    s = wiring.wire_summary()
    check(all(k in s for k in keys),
          f"wire_summary هر سه فلگِ پولی را دارد ({[k for k in keys if k in s]})")
    _saved = {k: os.environ.get(k) for k in
              ("OCTOPUS_GOVERNOR_USE_ROUTER", "OCTOPUS_HEART_DOCTOR_USE_ROUTER",
               "OCTOPUS_DOCTOR_SELFKNOW_PAID")}
    try:
        for k in _saved:
            os.environ[k] = "1"
        on = wiring.wire_summary()
        check(all(on[k] for k in keys), "فلگ روشن → True در خلاصه")
        for k in _saved:
            os.environ[k] = "0"
        off = wiring.wire_summary()
        check(not any(off[k] for k in keys), "فلگ خاموش → False در خلاصه")
    finally:
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ═══ ۷) صداقتِ متنِ آلارمِ router (ساختاری) ════════════════════════════════════
def s7_alert_honesty():
    src = (OPS / "cortex" / "model_router.py").read_text("utf-8")
    # فقط *کد* سنجیده می‌شود، نه کامنت: کامنتِ توضیحیِ فیکس خودش عبارتِ قدیمی را
    # نقل می‌کند و آن مستندسازی است نه رفتار.
    src = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    check("fallback local" not in src,
          "متنِ «fallback local» حذف شد — در شاهدِ زنده primary افتاد ولی secondaryِ "
          "*پولی* جواب داد، پس آن متن دروغ بود")
    check("انتخابِ" in src and "caller" in src,
          "متنِ نو می‌گوید انتخابِ tierِ بعدی دستِ caller است")


# ═══ ۸) شمارندهٔ شکستِ per-tierِ Fugu (صداقتِ گزارش، بدونِ تغییرِ رفتار) ═════════
def s8_fugu_per_tier():
    import tempfile
    import fugu_quota as fq
    _saved = {k: os.environ.get(k) for k in ("FUGU_QUOTA_BASE", "FUGU_FAIL_CEILING",
                                             "OCTOPUS_FUGU_KILL")}
    try:
        tmp = Path(tempfile.mkdtemp(prefix="fq-livefix-"))
        (tmp / "state").mkdir(parents=True, exist_ok=True)
        os.environ["FUGU_QUOTA_BASE"] = str(tmp)
        os.environ["FUGU_FAIL_CEILING"] = "99"      # قطعیت: در این بخش STOP نوشته نشود
        os.environ.pop("OCTOPUS_FUGU_KILL", None)
        for _ in range(2):
            r = fq.reserve("primary")
            if not r.get("allow"):
                check(False, f"reserve باید allow بدهد ({r.get('reason')})")
                return
            fq.fail("primary")
        s = fq.status()
        check(s.get("consecutive_failures") == 2,
              f"سراسری بعد از ۲ شکستِ primary = ۲ ({s.get('consecutive_failures')})")
        check((s.get("consecutive_failures_by_tier") or {}).get("primary") == 2,
              f"per-tier[primary] = ۲ ({(s.get('consecutive_failures_by_tier') or {})})")
        # الگوی زندهٔ باگ: موفقیتِ tierِ دیگر شمارندهٔ سراسری را صفر می‌کند
        fq.reserve("secondary")
        fq.ok("secondary")
        s2 = fq.status()
        bt = s2.get("consecutive_failures_by_tier") or {}
        check(s2.get("consecutive_failures") == 0,
              "موفقیتِ secondary شمارندهٔ سراسری را صفر کرد — رفتارِ تاریخی دست‌نخورده")
        check(bt.get("primary") == 2,
              f"ولی per-tier[primary] همچنان ۲ است → tierِ مرده دیگر نامرئی نیست ({bt})")
        check(bt.get("secondary") == 0, f"per-tier[secondary] صفر شد ({bt})")
        # حکمِ سقف عمداً روی شمارندهٔ سراسری مانده (بدونِ تغییرِ رفتار)
        tmp2 = Path(tempfile.mkdtemp(prefix="fq-ceil-"))
        (tmp2 / "state").mkdir(parents=True, exist_ok=True)
        os.environ["FUGU_QUOTA_BASE"] = str(tmp2)
        os.environ["FUGU_FAIL_CEILING"] = "2"
        for _ in range(2):
            fq.reserve("primary")
            fq.fail("primary")
        check((tmp2 / "STOP-FUGU").exists(),
              "سقف همچنان از شمارندهٔ سراسری شلیک می‌کند (STOP-FUGU نوشته شد)")
        check(not (Path(os.sep) / "STOP-FUGU").exists(),
              "sandbox ایزوله بود — هیچ STOP-FUGU خارج از temp نوشته نشد")
        # سازگاریِ عقب: فایلِ قدیمیِ بدونِ کلیدِ نو
        old = fq.Core.roll({"day": fq._today(), "used_total": 5,
                            "consecutive_failures": 1, "used": {}, "denied": {}},
                           fq._today())
        check(old.get("consecutive_failures_by_tier") == {},
              "فایلِ قدیمیِ بی‌کلید → roll آن را می‌سازد (بدونِ KeyError)")
    finally:
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ═══ ۹) C3: خودشناسی اندام‌های خودش را می‌شمارد (پیش‌بینیِ پیش‌ثبت‌شده) ══════════
# پیش‌بینی *قبل* از اجرا (ابطال‌پذیر): با فلگِ خاموش، snobshot()['legs'] فقط کلیدِ
# 'business_legs' را دارد و **با تغییرِ واقعیتِ لِگ‌ها عوض نمی‌شود**؛ با فلگ روشن، همان
# چهار لِگِ واقعی با live/signalِ خودشان ظاهر می‌شوند. اگر خاموش هم لِگ‌ها را ببیند،
# ادعای «کوریِ ساختاری» ابطال شده است.
def s9_selfknow_legs():
    import importlib
    import opslib as _ol
    sk = importlib.import_module("self_knowledge")
    _saved_flag = os.environ.get("OCTOPUS_SELFKNOW_LEGS_UNWRAP")
    _saved_state = _ol.STATE_DIR
    try:
        sb = Path(ENV["ops"]) / "state-c3probe"
        sb.mkdir(parents=True, exist_ok=True)
        _ol.STATE_DIR = sb

        def _write(mining_live, crypto_live):
            (sb / "ORGANISM-STATE.json").write_text(json.dumps({
                "chrono": {"beat": 7},
                "business_legs": {"business_legs": {
                    "mining": {"leg": "mining", "live": mining_live, "signal": "s1"},
                    "crypto": {"leg": "crypto", "live": crypto_live, "signal": "s2"},
                }, "beat": 7},
                "wiring": {}, "month": {}, "cardiac": {},
            }, ensure_ascii=False), "utf-8")

        os.environ.pop("OCTOPUS_SELFKNOW_LEGS_UNWRAP", None)
        _write(False, False)
        off_a = sk.snapshot().get("legs")
        _write(True, True)                      # واقعیت را برگردان
        off_b = sk.snapshot().get("legs")
        check(list(off_a or {}) == ["business_legs"],
              f"فلگ خاموش: legs یک شبه-لِگ است ({list(off_a or {})}) — عددِ beat هم "
              "به‌خاطرِ گاردِ isinstance(v, dict) خطِ ۱۵۵ می‌افتد")
        check((off_a or {}).get("business_legs", {}).get("live") is False,
              "فلگ خاموش: liveِ آن شبه-لِگ همیشه False است (bool(None)) — منبعِ گزارشِ "
              "غلطِ «۱ لِگِ تجاری در وضعیتِ مرگ» در خودشناسیِ v10")
        check(off_a == off_b,
              "فلگ خاموش: خروجی با برگشتنِ واقعیتِ لِگ‌ها **عوض نمی‌شود** — کوریِ ساختاری")

        os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = "1"
        on_b = sk.snapshot().get("legs") or {}
        check(sorted(on_b) == ["crypto", "mining"],
              f"فلگ روشن: لِگ‌های واقعی دیده می‌شوند ({sorted(on_b)})")
        check(len(on_b) == 2 and len(off_b or {}) == 1,
              f"شمارشِ اندام درست شد: خاموش={len(off_b or {})} ← روشن={len(on_b)} "
              "(همان «۱» در برابرِ واقعیت)")
        check(on_b.get("mining", {}).get("live") is True
              and on_b.get("crypto", {}).get("live") is True,
              "فلگ روشن: liveِ هر لِگ از واقعیت می‌آید")
        _write(False, True)
        on_c = sk.snapshot().get("legs") or {}
        check(on_c.get("mining", {}).get("live") is False
              and on_c.get("crypto", {}).get("live") is True,
              "فلگ روشن: خروجی با واقعیت **تغییر می‌کند** (شرطِ لازمِ سنجهٔ C3)")
        # سازگاری: اگر روزی business_legs تک‌لایه شد، unwrap دست نمی‌زند
        (sb / "ORGANISM-STATE.json").write_text(json.dumps({
            "chrono": {"beat": 7},
            "business_legs": {"mining": {"leg": "mining", "live": True}},
            "wiring": {}, "month": {}, "cardiac": {},
        }, ensure_ascii=False), "utf-8")
        flat = sk.snapshot().get("legs") or {}
        check(sorted(flat) == ["mining"],
              f"شکلِ تک‌لایه دست‌نخورده می‌ماند (بدونِ unwrapِ کور) ({sorted(flat)})")
    finally:
        _ol.STATE_DIR = _saved_state
        if _saved_flag is None:
            os.environ.pop("OCTOPUS_SELFKNOW_LEGS_UNWRAP", None)
        else:
            os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = _saved_flag


# ═══ ۱۰) throttleِ آلارمِ fence — پیش‌شرطِ ایمنِ روشن‌کردنِ R5 ═══════════════════
def s10_alert_throttle():
    import opslib as _ol
    _saved_state, _saved_alerts = _ol.STATE_DIR, _ol.ALERTS_MD
    try:
        sb = Path(ENV["ops"]) / "state-throttle"
        sb.mkdir(parents=True, exist_ok=True)
        _ol.STATE_DIR = sb
        _ol.ALERTS_MD = sb / "alerts.md"

        def _n():
            try:
                return _ol.ALERTS_MD.read_text("utf-8").count("- ⚠️")
            except OSError:
                return 0

        check(_ol.alert_throttled(["X"], key="k1") is True, "اولین آلارم نوشته می‌شود")
        check(_n() == 1, f"یک خط ({_n()})")
        check(_ol.alert_throttled(["X"], key="k1") is False,
              "تکرارِ عینِ همان پیام در پنجره سرکوب می‌شود")
        check(_n() == 1, f"هنوز یک خط ({_n()})")
        check(_ol.alert_throttled(["Y — متنِ نو"], key="k1") is True,
              "متنِ **نو** فوراً عبور می‌کند (throttle فقط روی تکرارِ عین است)")
        check(_ol.alert_throttled(["X"], key="k2") is True,
              "کلیدِ دیگر مستقل است (یک task نو خفه نمی‌شود)")
        # بستنِ پنجره **قطعی** (بدونِ sleep و بدونِ وابستگی به ساعتِ دیواری):
        # سه سرکوب، بعد ts ذخیره‌شده را به گذشته می‌بریم تا پنجره منقضی شود.
        _ol.alert_throttled(["Z"], key="k3")
        _ol.alert_throttled(["Z"], key="k3")
        _ol.alert_throttled(["Z"], key="k3")
        _tp = _ol.STATE_DIR / "alert-throttle.json"
        _st = json.loads(_tp.read_text("utf-8"))
        check(int(_st["k3"]["suppressed"]) == 2,
              f"شمارندهٔ سرکوب پیش از انقضا = ۲ ({_st['k3']['suppressed']})")
        _st["k3"]["ts"] = 0.0                      # پنجره منقضی شد
        _tp.write_text(json.dumps(_st, ensure_ascii=False), "utf-8")
        check(_ol.alert_throttled(["Z"], key="k3") is True,
              "پس از انقضای پنجره، همان پیام دوباره نوشته می‌شود")
        blob = _ol.ALERTS_MD.read_text("utf-8")
        check("تکرارِ سرکوب‌شده" in blob and "k3" in blob,
              "بعد از بسته‌شدنِ پنجره، شمارِ سرکوب‌شده‌ها صریح گزارش می‌شود")
        # fail-open: مسیرِ state غیرقابل‌نوشتن → آلارم از دست نمی‌رود
        _ol.STATE_DIR = sb / "nonexistent" / "deep" / "\0bad"
        before = _n()
        try:
            _ol.alert_throttled(["W"], key="k4")
        except Exception as e:  # noqa: BLE001
            check(False, f"fail-open نقض شد — استثنا پرت شد: {type(e).__name__}")
        check(_n() > before, "fail-open: با stateِ خراب هم آلارم نوشته شد")
        # ساختاری: سایتِ fence از throttle استفاده می‌کند نه alertِ خام
        src = (OPS / "cortex" / "model_router.py").read_text("utf-8")
        code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
        i = code.find("context_fence: ورودیِ مشکوک")
        check(i > 0 and "alert_throttled" in code[max(0, i - 900):i + 600],
              "سایتِ آلارمِ fence throttled است (پیش‌شرطِ VQ-ALERT-001 برای R5)")
    finally:
        _ol.STATE_DIR, _ol.ALERTS_MD = _saved_state, _saved_alerts


for name, fn in (("۱ گاردِ گرافِ دژنرهٔ spectral", s1_spectral),
                 ("۲ persistِ created_ts", s2_created_ts),
                 ("۳ تحمّلِ صادقِ phi", s3_phi),
                 ("۴ legs_diag در snapshot", s4_legs_diag),
                 ("۵ Gate-0 با Δ منفی", s5_wire_gate),
                 ("۶ فلگ‌های پولی در wire_summary", s6_wire_summary),
                 ("۷ صداقتِ متنِ آلارم", s7_alert_honesty),
                 ("۸ شمارندهٔ per-tierِ Fugu", s8_fugu_per_tier),
                 ("۹ C3: شمردنِ اندام‌های خود", s9_selfknow_legs),
                 ("۱۰ throttleِ آلارمِ fence", s10_alert_throttle)):
    print(f"\n── {name} " + "─" * max(0, 50 - len(name)))
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        fails.append(f"{name}: {type(e).__name__}: {e}")
        print(f"  💥 {name}: {type(e).__name__}: {e}")

print(f"\n{'PASS' if not fails else 'FAIL'} — test_live_debug_fixes_2026_07_25 "
      f"({len(fails)} failure(s))")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
