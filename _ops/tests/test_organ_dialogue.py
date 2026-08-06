#!/usr/bin/env python3
"""test_organ_dialogue.py — Task 3 (2026-07-24): دیالوگِ دوطرفهٔ owner↔organ.

پوشش:
  3a Doctor: digest render/hash · steering «focus» (tie-breaker، هرگز بحران‌شکن نیست) ·
     بازنگریِ RFC (صف → ادغامِ دکتر) · دکمهٔ ✍️ + free-text در کانال
  3b Brains: digest از state-file (بدونِ هیچ poller) · parse ِ boundedِ guidance ·
     append/effective (last-wins) · cortex هرگز channel نمی‌گیرد (structural)
  3c Hearts: digest/alerts · stall-detector (frozen-beat) · setpoint فقط از راهِ
     HeartParams.validate (σ≤1، سقف‌های مطلق، ADR-001: هیچ period) · جریانِ کاملِ
     تلگرام: /heart set → کارتِ confirmِ توکن‌دار → act:heartset → epochِ نو + audit
  wiring beats: ارسال + hash-throttle + flag-off = no-op
ایزوله: tempdir mini-vault؛ صفر شبکه (http تزریقی)؛ صفر state واقعی.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("organ-dialogue")
os.environ["OCTOPUS_CB_SECRET"] = "unit-test-organ-dialogue-secret"

import opslib  # noqa: E402
import organ_dialogue as od  # noqa: E402
import wiring  # noqa: E402
from approval_channel import TelegramApprovalChannel  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cortex"))
import owner_guidance as og  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "doctor"))
from doctor import Doctor  # noqa: E402

SD = Path(ENV["ops"]) / "state"
OWNER = 777


class _FakeChannel:
    wired = True

    def __init__(self):
        self.sent: list[tuple[str, dict | None]] = []

    def send_text(self, text, reply_markup=None, chat_id=None):
        self.sent.append((text, reply_markup))
        return True


def _seed_doctor_state():
    (SD / "doctor").mkdir(parents=True, exist_ok=True)
    (SD / "doctor" / "self-knowledge-latest.json").write_text(json.dumps({
        "ts": opslib.now_iso(), "version": 3, "snapshot_hash": "abc123",
        "focus": "تستِ تمرکز",
        "understanding": {"pathology": [
            {"symptom": "نبضِ یخ‌زده", "root_cause": "pacemaker مرده", "severity": 3}]},
    }, ensure_ascii=False), "utf-8")
    (SD / "doctor" / "rfcs.json").write_text(json.dumps({
        "ts": opslib.now_iso(), "schema": "doctor-rfcs.v1",
        "rfcs": [{"rfc_id": "RFC-t1", "bottleneck": "b1", "fix": "f1",
                  "expected_lift": "l1", "status": "submitted",
                  "change_level": "tune", "knob": "K"}]}, ensure_ascii=False), "utf-8")


def _seed_heart_state(spent=288, cap=288):
    (SD / "pulse").mkdir(parents=True, exist_ok=True)
    (SD / "pulse" / "heartstate-latest.json").write_text(json.dumps({
        "shadow": {"velocity": 1.2, "sigma": 0.0, "period_s": 900.0,
                   "band": [0.05, 4.5]},
        "stress": {"organism": 1.0, "level": "🔴 ترس", "in_fear": ["legs"]},
        "innervation": {"coverage_pct": 100.0, "dead_spots": []}},
        ensure_ascii=False), "utf-8")
    (SD / "pulse" / "heart-shadow-latest.json").write_text(json.dumps({
        "beat": 9890, "signal": {"beat_seq": 9890, "period_s": 900.0,
                                 "sigma_now": 0.0, "baro_factor": 0.85},
        "telemetry": {"velocity_per_hr": 1.28, "band_lo": 0.05, "band_hi": 4.58}},
        ensure_ascii=False), "utf-8")
    (SD / "cardiac-budget.json").write_text(
        json.dumps({"date": "2026-07-24", "spent": spent, "resting": 0}), "utf-8")
    (SD / "pulse" / "heart-setpoint-latest.json").write_text(json.dumps({
        "ts": opslib.now_iso(), "schema": "HeartParams.v1", "target_sigma": 1.0,
        "viable_band_lo": 0.05, "viable_band_hi": 4.27, "epoch_seq": 28,
        "target_mass_scale": 1.0, "daily_beat_cap": cap, "baroreflex_gain": 0.0},
        ensure_ascii=False), "utf-8")


def _seed_brain_state():
    (SD / "cortex").mkdir(parents=True, exist_ok=True)
    (SD / "cortex" / "cortex-state.json").write_text(json.dumps({
        "ts": opslib.now_iso(), "cycle": 35, "coherence": 0.876,
        "stale_members": ["heart"]}, ensure_ascii=False), "utf-8")
    (SD / "cortex" / "stress-latest.json").write_text(
        json.dumps({"level": "🟡 هشدار"}, ensure_ascii=False), "utf-8")
    with open(SD / "cortex" / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": opslib.now_iso(), "cycle": 35,
                            "thought": "[local] تمرکز روی پول"}, ensure_ascii=False) + "\n")
    dq = Path(ENV["ops"]) / "debate" / "SURVIVORS-QUEUE.md"
    dq.parent.mkdir(parents=True, exist_ok=True)
    dq.write_text("# صف\n\n- — top-1 · بازمانده ۱\n- — top-2 · بازمانده ۲\n", "utf-8")


def _stub_get(url, timeout):
    return {"ok": True, "result": []}


class _PostCapture:
    def __init__(self):
        self.bodies = []

    def __call__(self, url, body, timeout_s=10.0):
        self.bodies.append(body)
        return {"ok": True, "result": {}}


def _mk_channel(post=None):
    return TelegramApprovalChannel(token="123:tok", owner_chat_id=OWNER,
                                   http_get=_stub_get,
                                   http_post=post or _PostCapture(),
                                   state_dir=str(SD))


# ─── 3a · Doctor ────────────────────────────────────────────────────────────────
def t_doctor_digest_renders_and_hashes():
    _seed_doctor_state()
    d = od.doctor_digest(SD)
    assert "RFC-t1" in d["text"] and d["rfc_open"] == 1
    assert "نبضِ یخ‌زده" in d["text"]
    h1 = d["hash"]
    od.save_owner_focus("پول", SD)
    assert od.doctor_digest(SD)["hash"] != h1     # steering دیدنی → hash عوض


def t_doctor_focus_is_tiebreaker_not_override():
    od.save_owner_focus("error", SD)
    doc = Doctor(state_dir=SD, approval_channel=None)
    # دو کاندیدِ high: بدونِ focus «effects-stuck» (score بدتر) اول بود؛ focus=error جابه‌جا می‌کند
    b = doc.mine(trace={"errors_24h": 3, "effects_pending": 9})
    assert b["evidence"]["key"] == "error-rate-high", b
    # ولی critical (frozen) هرگز با focus کنار نمی‌رود
    b2 = doc.mine(trace={"errors_24h": 3, "frozen": True})
    assert b2["evidence"]["key"] == "frozen-conflict", b2


def t_rfc_revision_queue_and_doctor_merge():
    ch = _FakeChannel()
    doc = Doctor(state_dir=SD, approval_channel=ch)
    rfc = doc.propose_rfc({"bottleneck": "کندیِ تست"}, fix="فیکسِ اولیه",
                          expected_lift="ل", rollback="r")
    r = od.save_rfc_revision(rfc.rfc_id, "سخت‌گیرتر باش", SD)
    assert r["ok"]
    n = doc._consume_owner_revisions()
    assert n == 1
    assert "بازنگریِ مالک" in doc._rfcs[rfc.rfc_id].fix
    assert "سخت‌گیرتر باش" in doc._rfcs[rfc.rfc_id].fix
    assert any(rfc.rfc_id in t for t, _ in ch.sent)      # اطلاع به مالک
    assert od.pop_rfc_revisions(SD) == {}                 # صف atomic خالی شد


def t_rfc_edit_button_then_freetext():
    post = _PostCapture()
    ch = _mk_channel(post)
    assert ch.rfc_card("RFC-ed1", "خلاصهٔ تست")
    kb = post.bodies[-1]["reply_markup"]["inline_keyboard"]
    edit_btns = [b for row in kb for b in row if b["callback_data"].startswith("rfc:edit:")]
    assert edit_btns, kb
    token = edit_btns[0]["callback_data"].split(":")[3]
    reply = ch.dispatch_callback(f"rfc:edit:RFC-ed1:{token}", from_id=OWNER, external=True)
    assert "✍️" in str(reply)
    assert ch._awaiting_rfc_edit == "RFC-ed1"
    r2 = ch.handle_command("متنِ بازنگریِ من", from_id=OWNER)
    assert "ثبت شد" in str(r2)
    assert ch._awaiting_rfc_edit is None
    assert "RFC-ed1" in od.pop_rfc_revisions(SD)
    # tokenِ edit مصرف نشده — merge هنوز معتبر است (decision همچنان SUBMITTED)
    r3 = ch.dispatch_callback(f"rfc:merge:RFC-ed1:{token}", from_id=OWNER, external=True)
    assert "ثبت شد" in str(r3), r3


def t_doctor_commands_owner_gated():
    ch = _mk_channel()
    deny = ch.handle_command("/doctor focus پول", from_id=999)
    assert "⛔" in str(deny)
    ok = ch.handle_command("/doctor focus پول", from_id=OWNER)
    assert "steering ثبت شد" in str(ok)
    assert od.load_owner_focus(SD) == "پول"
    ok2 = ch.handle_command(f"/doctor edit RFC-x متنِ ادیت", from_id=OWNER)
    assert "صف شد" in str(ok2)


# ─── 3b · Brains ────────────────────────────────────────────────────────────────
def t_guidance_parse_bounded():
    d, e = og.parse("focus: روی پول تمرکز کن")
    assert e is None and d["focus"].startswith("روی پول")
    d, e = og.parse("think_every_n: 5")
    assert e is None and d["think_every_n"] == 5
    for bad in ("think_every_n: 0", "think_every_n: 1000", "think_every_n: abc",
                "pause: paid", "period: 30", "rate: 10", ""):
        d, e = og.parse(bad)
        assert d is None and e, (bad, d, e)
    d, e = og.parse("pause: think")
    assert e is None and d["paused"] is True
    d, e = og.parse("resume: think")
    assert e is None and d["paused"] is False
    d, e = og.parse("متنِ آزاد بدونِ کلید")
    assert e is None and d["focus"] == "متنِ آزاد بدونِ کلید"


def t_guidance_append_effective_lastwins():
    assert og.append("focus: اول", state_dir=SD)["ok"]
    assert og.append("focus: دوم\nthink_every_n: 7", state_dir=SD)["ok"]
    eff = og.effective(SD)
    assert eff["focus"] == "دوم" and eff["think_every_n"] == 7
    bad = og.append("period: 30", state_dir=SD)
    assert not bad["ok"]
    assert og.effective(SD)["focus"] == "دوم"     # ردشده هیچ اثری نگذاشت


def t_brain_digest_reads_state_files():
    _seed_brain_state()
    d = od.brain_digest(SD)
    assert "0.876" in d["text"] and "cycle" in d["text"].lower() or "35" in d["text"]
    assert d["debate_pending"] == 2
    assert "بازمانده" in d["text"]
    h1 = d["hash"]
    (SD / "cortex" / "stress-latest.json").write_text(
        json.dumps({"level": "🔴 ترس"}, ensure_ascii=False), "utf-8")
    assert od.brain_digest(SD)["hash"] != h1


def t_brain_guide_channel_command():
    ch = _mk_channel()
    deny = ch.handle_command("/brain guide focus: پول", from_id=999)
    assert "⛔" in str(deny)
    ok = ch.handle_command("/brain guide focus: پول", from_id=OWNER)
    assert "ثبت شد" in str(ok)
    assert og.effective(SD)["focus"] == "پول"
    bad = ch.handle_command("/brain guide rate: 10", from_id=OWNER)
    assert "⛔" in str(bad)


def t_cortex_never_owns_a_channel():
    """ساختاری (ضدِ 409): در سورسِ cortex هیچ ساختِ TelegramApprovalChannel/getUpdates نیست."""
    root = Path(__file__).resolve().parents[1] / "cortex"
    for p in root.glob("*.py"):
        src = p.read_text("utf-8", errors="replace")
        assert "TelegramApprovalChannel(" not in src, p.name
        assert "getUpdates" not in src, p.name


# ─── 3c · Hearts ────────────────────────────────────────────────────────────────
def t_heart_stall_detector():
    (SD / "pulse" / "heart-card-state.json").unlink(missing_ok=True)
    r1 = od.heart_stall_check(beat=100, state_dir=SD, now=1000.0)
    assert r1["stalled"] is False
    r2 = od.heart_stall_check(beat=100, state_dir=SD, now=1000.0 + 2000)
    assert r2["stalled"] is True and r2.get("already_alerted") is False
    r3 = od.heart_stall_check(beat=100, state_dir=SD, now=1000.0 + 3000)
    assert r3["stalled"] is True and r3.get("already_alerted") is True
    r4 = od.heart_stall_check(beat=101, state_dir=SD, now=1000.0 + 3100)
    assert r4["stalled"] is False                     # beat جلو رفت → سالم


def t_heart_digest_alerts():
    _seed_heart_state(spent=288, cap=288)
    (SD / "pulse" / "heart-card-state.json").unlink(missing_ok=True)
    d = od.heart_digest(SD, beat=9890)
    assert "بودجهٔ ضربانِ امروز" in d["text"]
    assert d["depleted"] is True
    assert any("بودجهٔ ضربان" in a for a in d["alerts"])
    assert any("🔴" in a for a in d["alerts"])         # تنشِ قرمزِ seed شده
    assert "period" not in json.dumps(od.HEART_PARAM_ALIASES)   # ADR-001 ساختاری


def t_heart_set_validation_walls():
    _seed_heart_state()
    assert od.heart_set_preview("sigma", "0.8", SD)["ok"]
    assert not od.heart_set_preview("sigma", "1.5", SD)["ok"]          # σ≤1 قانونِ اساسی
    assert not od.heart_set_preview("hi", "9999", SD)["ok"]            # ABS_BAND_MAX 500
    assert not od.heart_set_preview("cap", "5000", SD)["ok"]           # ABS_BEAT_CAP 2000
    assert not od.heart_set_preview("period", "30", SD)["ok"]          # ADR-001
    assert not od.heart_set_preview("rate", "10", SD)["ok"]
    assert not od.heart_set_preview("ناشناخته", "1", SD)["ok"]
    assert od.heart_set_preview("cap", "300", SD)["ok"]


def t_heart_set_apply_epoch_and_audit():
    _seed_heart_state()
    r = od.heart_set_apply("sigma", "0.8", SD, by="test")
    assert r["ok"] and r["epoch_seq"] == 29, r
    cur = od.heart_params_current(SD)
    assert abs(cur.target_sigma - 0.8) < 1e-9 and cur.epoch_seq == 29
    audit = (SD / "pulse" / "heart-setpoint-audit.jsonl").read_text("utf-8")
    assert '"param": "target_sigma"' in audit
    bad = od.heart_set_apply("hi", "9999", SD)
    assert not bad["ok"]
    assert od.heart_params_current(SD).epoch_seq == 29   # ردشده هیچ epochی ننوشت


def t_heartset_full_telegram_flow():
    _seed_heart_state()
    ch = _mk_channel()
    deny = ch.handle_command("/heart set sigma 0.7", from_id=999)
    assert "⛔" in str(deny)
    card = ch.handle_command("/heart set sigma 0.7", from_id=OWNER)
    assert isinstance(card, dict), card
    btn = card["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    assert btn.startswith("act:heartset:target_sigma:")
    reply = ch.dispatch_callback(btn, from_id=OWNER, external=True)
    assert "✅ setpoint نوشته شد" in str(reply), reply
    assert abs(od.heart_params_current(SD).target_sigma - 0.7) < 1e-9
    # ضدِ replay: همان توکن دوباره → رد
    again = ch.dispatch_callback(btn, from_id=OWNER, external=True)
    assert "✅" not in str(again)
    # /heart فقط‌خواندنی برای عضوِ گروه هم مجاز است
    view = ch.handle_command("/heart", from_id=999)
    assert isinstance(view, dict) and "قلب" in view["text"]


# ─── wiring beats ───────────────────────────────────────────────────────────────
def t_beats_flag_off_noop():
    for f in ("OCTOPUS_WIRE_DOCTOR_DIGEST", "OCTOPUS_WIRE_BRAIN_DIGEST",
              "OCTOPUS_WIRE_HEART_CARD"):
        os.environ.pop(f, None)
    assert wiring.doctor_digest_beat(_FakeChannel(), beat=10) is None
    assert wiring.brain_digest_beat(_FakeChannel(), beat=10) is None
    assert wiring.heart_card_beat(_FakeChannel(), beat=10) is None


def t_beats_send_then_hash_throttle():
    _seed_doctor_state()
    _seed_brain_state()
    _seed_heart_state()
    os.environ.update({"OCTOPUS_WIRE_DOCTOR_DIGEST": "1",
                       "OCTOPUS_WIRE_BRAIN_DIGEST": "1",
                       "OCTOPUS_WIRE_HEART_CARD": "1",
                       "OCTOPUS_WIRE_PULSE": "1",
                       "CHRONO_DOCTOR_DIGEST_MIN_S": "0",
                       "CHRONO_BRAIN_DIGEST_MIN_S": "0",
                       "CHRONO_HEART_CARD_MIN_S": "0"})
    try:
        ch = _FakeChannel()
        r1 = wiring.doctor_digest_beat(ch, beat=100)
        assert r1 and r1["sent"] is True, r1
        r2 = wiring.doctor_digest_beat(ch, beat=101)
        assert r2 and r2["sent"] is False            # hash همان → اسپم نه
        b1 = wiring.brain_digest_beat(ch, beat=100)
        assert b1 and b1["sent"] is True, b1
        h1 = wiring.heart_card_beat(ch, beat=9890)
        assert h1 and h1["sent"] is True, h1
        assert len(ch.sent) == 3
        assert any("دکتر" in t for t, _ in ch.sent)
        assert any("مغز" in t for t, _ in ch.sent)
        assert any("قلب" in t for t, _ in ch.sent)
    finally:
        for f in ("OCTOPUS_WIRE_DOCTOR_DIGEST", "OCTOPUS_WIRE_BRAIN_DIGEST",
                  "OCTOPUS_WIRE_HEART_CARD"):
            os.environ.pop(f, None)


# ─── ۲۰۲۶-۰۷-۲۸: کارتی که نرسید هم باید مهر بخورد ────────────────────────
# اندازه‌گیریِ زنده: سه کارتِ قلب با فاصلهٔ ۴۵ ثانیه، دوتایشان با **همان ضربان**
# (۱۵۸۷۵)، و `pulse/heart-card-nudge.json` از ۰۶:۴۰ یخ‌زده. علت: `_dialogue_mark`
# فقط پشتِ `if sent:` صدا زده می‌شد، و چون سیاستِ سطحِ نسخهٔ ۲ جریانِ `heart` را
# نگه می‌دارد، `sent` همیشه False بود ⇒ حالت هرگز جلو نمی‌رفت ⇒ گیت هر تیک
# عبور می‌داد. هر سه دایجست (دکتر/مغز/قلب) همین را داشتند — یک هلپر، سه قربانی.

def t_brain_digest_beat_keyboard_links_to_the_working_approval_queue():
    """رگرسیونِ باگِ گزارش‌شده (۲۰۲۶-۰۸-۰۶): مالک ۱۴ ایدهٔ مناظره را در همین کارتِ
    پوش‌شده می‌بیند، ولی تنها دکمه‌اش («🧠 تبِ مغز» → menu:brain) به یک نمای
    وضعیت می‌رود، نه به صفِ رأیِ واقعی («📮 صف تأیید» → mn:ap). نتیجه: مالک
    هرگز روی دکمهٔ رأیِ کارکننده نمی‌رسد و فکر می‌کند «کلیک ثبت نمی‌شود» — درحالی
    که اصلاً به آن دکمه نرسیده. این تست کیبوردِ همان پیامی را که برای مالک پوش
    می‌شود می‌سنجد، نه صفِ تأییدِ داخلی (که در test_debate_card_roundtrip.py
    جداگانه سبز است)."""
    _seed_brain_state()
    (opslib.STATE_DIR / "cortex" / "brain-digest-nudge.json").unlink(missing_ok=True)
    os.environ["OCTOPUS_WIRE_BRAIN_DIGEST"] = "1"
    os.environ["CHRONO_BRAIN_DIGEST_MIN_S"] = "0"
    try:
        ch = _FakeChannel()
        r = wiring.brain_digest_beat(ch, beat=100)
        assert r and r["sent"] is True, r
        assert ch.sent, "کارتِ مغز اصلاً ارسال نشد"
        _text, kb = ch.sent[-1]
        assert kb and kb.get("inline_keyboard"), f"کیبورد خالی است: {kb}"
        buttons = [b.get("callback_data", "")
                   for row in kb["inline_keyboard"] for b in row]
        assert "mn:ap" in buttons, (
            "کارتِ پوش‌شدهٔ مغز به صفِ کارکننده (mn:ap) لینک نمی‌دهد — "
            f"فقط {buttons}. مالک از این کارت هرگز به دکمهٔ رأیِ واقعی نمی‌رسد "
            "(همان علتِ ریشه‌ایِ ۱۴ ایدهٔ رأی‌نخورده)."
        )
    finally:
        os.environ.pop("OCTOPUS_WIRE_BRAIN_DIGEST", None)
        os.environ.pop("CHRONO_BRAIN_DIGEST_MIN_S", None)


def t_no_monotonic_counter_sits_in_a_dedup_key():
    """⚠️ سومین نمونهٔ یک الگو در یک روز — و گران‌ترینش.

    گاردِ `_dialogue_gate` را درست کردم و **هیچ اثری نداشت**: نرخِ کارتِ قلب
    ۱.۴۵ در دقیقه ماند. علت این بود که hash خودش هر دقیقه عوض می‌شد:

        قلب : `spent` — بودجهٔ ضربانِ مصرف‌شده، هر ۶۰ثانیه +۱
        مغز : `cycle` — شمارندهٔ چرخهٔ کورتکس، هر چرخه +۱

    گاردی که روی تطبیقِ hash کار می‌کند، با hashی که با **گذشتِ زمان** عوض
    می‌شود هرگز تطبیق نمی‌دهد. «تغییر» و «گذشتِ زمان» یکی گرفته شده بودند.

    هر دو از کلید بیرون رفتند و در **متنِ کارت** ماندند — مالک عدد را می‌بیند،
    ولی عدد تصمیمِ فرستادن را نمی‌گیرد. (همان الگوی `stable_hash` در کارتِ
    نیازها، که آن‌جا شمارندهٔ هشدار بود.)
    """
    src = Path(od.__file__).read_text("utf-8")
    for fn_marker, banned in (('"mode": mode', "spent"),
                              ('"stress_level": stress_level', "cycle")):
        i = src.index(fn_marker)
        j = src.rfind("hsh = _h(", 0, i)
        assert j != -1, fn_marker
        key = src[j:src.index(")\n", j)]
        assert banned not in key, f"شمارندهٔ «{banned}» دوباره در کلیدِ dedup است"


def t_the_heart_hash_survives_the_passage_of_beats():
    """رفتارِ واقعی، نه ساختار: چهار beat مختلف باید یک hash بدهند."""
    hs = {od.heart_digest(beat=b)["hash"] for b in (15900, 15901, 15960, 16200)}
    assert len(hs) == 1, f"hash با گذشتِ ضربان عوض می‌شود: {hs}"


def t_the_brain_and_doctor_hashes_are_stable_too():
    for fn in (od.brain_digest, od.doctor_digest):
        hs = {fn()["hash"] for _ in range(3)}
        assert len(hs) == 1, (fn.__name__, hs)


def _probe_state():
    import opslib
    p = opslib.STATE_DIR / "probe-dialogue-nudge.json"
    p.unlink(missing_ok=True)
    return "probe-dialogue-nudge.json", p


def t_an_undelivered_card_is_still_throttled():
    """پنج تلاش با ارسالِ همیشه‌ناموفق → فقط یکی باید عبور کند."""
    name, _ = _probe_state()
    passes = 0
    for _ in range(5):
        if wiring._dialogue_gate(name, "H1", 21600.0):
            passes += 1
            wiring._dialogue_mark(name, "H1", sent=False)
    assert passes == 1, f"{passes} تلاش عبور کرد — گارد بی‌اثر است"


def t_an_undelivered_card_can_retry_later():
    """نرسیده نباید `last_hash` را جلو ببرد، وگرنه وقتی نگه‌داشتن برداشته شد
    آن کارت برای همیشه گم می‌شود."""
    import json
    name, p = _probe_state()
    assert wiring._dialogue_gate(name, "H2", 21600.0) is True
    wiring._dialogue_mark(name, "H2", sent=False)
    st = json.loads(p.read_text("utf-8"))
    assert st.get("last_hash") is None, st
    assert st.get("last_attempt_hash") == "H2", st


def t_the_three_digests_share_one_gate():
    """اگر هرکدام گیتِ خودش را بنویسد، فیکس باید سه بار تکرار شود."""
    src = (harness.SELF_OPS / "wiring.py").read_text("utf-8")
    assert src.count("def _dialogue_gate(") == 1
    assert src.count("def _dialogue_mark(") == 1


def t_no_caller_marks_only_on_success():
    """⚠️ گاردِ بازگشت: اگر کسی دوباره `if sent:` بنویسد، سه دایجست بی‌صدا
    به همان حلقهٔ تکرار برمی‌گردند."""
    import re
    src = (harness.SELF_OPS / "wiring.py").read_text("utf-8").splitlines()
    bad = []
    for n, line in enumerate(src, 1):
        if "_dialogue_mark(" in line and "def " not in line:
            prev = [src[k - 1].strip() for k in range(max(1, n - 3), n)]
            if any(re.match(r"^if\s+sent\b", x) for x in prev):
                bad.append(n)
    assert not bad, f"صداکنندهٔ پشتِ if-sent در خطوط {bad}"


if __name__ == "__main__":
    sys.exit(harness.run([
        ("3a: digest دکتر render+hash", t_doctor_digest_renders_and_hashes),
        ("3a: focus فقط tie-breaker (بحران‌شکن نیست)", t_doctor_focus_is_tiebreaker_not_override),
        ("3a: صفِ بازنگری → ادغامِ دکتر + اطلاعِ مالک", t_rfc_revision_queue_and_doctor_merge),
        ("3a: دکمهٔ ✍️ + free-text (token مصرف نمی‌شود)", t_rfc_edit_button_then_freetext),
        ("3a: /doctor focus|edit owner-gated", t_doctor_commands_owner_gated),
        ("3b: parse ِ bounded (کران‌ها + کلیدهای ممنوع)", t_guidance_parse_bounded),
        ("3b: append/effective last-wins", t_guidance_append_effective_lastwins),
        ("3b: digest مغز از state-file", t_brain_digest_reads_state_files),
        ("3b: /brain guide owner-gated + bounded", t_brain_guide_channel_command),
        ("3b: cortex هرگز کانال نمی‌سازد (ضدِ 409، ساختاری)", t_cortex_never_owns_a_channel),
        ("3c: stall-detector ِ frozen-beat", t_heart_stall_detector),
        ("3c: digest قلب + alertها", t_heart_digest_alerts),
        ("3c: دیوارهای validate (σ≤1، سقف‌ها، ADR-001)", t_heart_set_validation_walls),
        ("3c: apply → epochِ نو + audit (ردشده نمی‌نویسد)", t_heart_set_apply_epoch_and_audit),
        ("3c: جریانِ کاملِ تلگرام + ضدِ replay + owner-gate", t_heartset_full_telegram_flow),
        ("wiring: flag-off = no-op", t_beats_flag_off_noop),
        ("wiring: سه دایجست یک هلپرِ مشترک دارند", t_the_three_digests_share_one_gate),
        ("wiring: ارسال + hash-throttle (ضدِ اسپم)", t_beats_send_then_hash_throttle),
        ("وایرینگ: کارتِ پوش‌شدهٔ مغز به mn:ap لینک می‌دهد (نه فقط menu:brain)",
         t_brain_digest_beat_keyboard_links_to_the_working_approval_queue),
        ("hash: شمارندهٔ یک‌طرفه در کلیدِ dedup نباشد", t_no_monotonic_counter_sits_in_a_dedup_key),
        ("hash: قلب با گذشتِ ضربان عوض نشود", t_the_heart_hash_survives_the_passage_of_beats),
        ("hash: مغز و دکتر هم پایدار", t_the_brain_and_doctor_hashes_are_stable_too),
        ("wiring: ارسالِ نرسیده هم مهر می‌خورد", t_an_undelivered_card_is_still_throttled),
        ("wiring: نرسیده last_hash را جلو نمی‌برد", t_an_undelivered_card_can_retry_later),
        ("wiring: هیچ صداکننده‌ای پشتِ if-sent نماند", t_no_caller_marks_only_on_success),
    ]))
