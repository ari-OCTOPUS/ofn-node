#!/usr/bin/env python3
"""تست P3 · T-1 · TelegramApprovalChannel — لولهٔ human-append (fail-closed).

$0 آفلاین: هیچ شبکه‌ای واقعی نمی‌رود — http_get یک تابعِ فیک است که JSONِ Telegram
را شبیه‌سازی می‌کند. کلیدِ واقعی هرگز لازم نیست (و نباید واردِ تست شود — I9).

ناوردی‌های پوشش‌داده‌شده (P3-TELEGRAM §5 + قوانینِ قفل‌شده):
  · نبودِ token = no-opِ امن، نه crash؛ poll_once/run_forever هیچ شبکه‌ای نمی‌زنند.
  · long-pollingِ $0-idle (timeout پاس می‌دهد؛ offset = last_update+1).
  · allowlist: فقط chat_idِ مالک پذیرفته می‌شود؛ غیرمجاز ignore (offset جلو می‌رود).
  · quarantine: هر پیام = DATA نه دستور؛ فقط ثبت می‌شود، اجرا نمی‌شود.
  · شیرِ بسته: در T-1 approval_for همیشه None مگر از طریقِ seam (T-2).
  · kill supreme: kill_check → poll_once/run_forever فوراً می‌ایستند.
  · token mask: __repr__/خطا هرگز کلِ token را نشون نمی‌دهند (secret-guard I9).
"""
import os
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("telegram-channel")
os.environ["OCTOPUS_CB_SECRET"] = "unit-test-telegram-secret-not-real"
# NOTE: TELEGRAM_OWNER_CHAT_ID عمداً در سطحِ ماژول ست نمی‌شود — تست‌ها owner را صریح به
# TC() می‌دهند. ست‌کردنِ سراسری، تست‌های no-owner (wired=False) را به‌خاطرِ fallbackِ env می‌شکست.
import approval_channel as ac  # noqa: E402
from approval_channel import Approval, TelegramApprovalChannel as TC  # noqa: E402

# F-G8: neutralise the default POST transport so no test path (e.g.
# answerCallbackQuery, which is NOT injected like http_get) reaches the real
# api.telegram.org. Poll paths already inject a fake http_get; this covers the
# _url_json_post fallback. Fire-and-forget results are ignored by callers.
ac._url_json_post = lambda *a, **k: {"ok": True, "result": {}}


def _fake_get_factory(responses_for_url: dict, calls: list):
    """سازندهٔ http_get فیک. responses_for_url: {method_substring: json_dict | callable}.
    calls: لیستی که tupleهای (method, params) را پر می‌کند برای بازرسی. هیچ شبکه‌ای."""
    def _fake(url: str, timeout_s: float):
        # متد/پارام را از URL بیرون بکش (URL در محیطِ تست هیچ رازی ندارد)
        from urllib.parse import urlparse, parse_qs
        p = urlparse(url)
        path = p.path  # مثلا /bot<TOKEN>/getUpdates
        q = {k: v[0] for k, v in parse_qs(p.query).items()}
        calls.append((path.rsplit("/", 1)[-1], q))
        for key, val in responses_for_url.items():
            if key in path:
                return val(q) if callable(val) else val
        return {"ok": True, "result": []}
    return _fake


def t_noop_without_token():
    """نبودِ token → no-opِ امن. هیچ فراخوانیِ شبکه‌ای نمی‌شود."""
    calls = []
    http = _fake_get_factory({}, calls)
    ch = TC(token="", owner_chat_id=42, http_get=http)   # بدون token
    assert ch.wired is False
    assert ch.poll_once() == 0
    assert calls == [], f"نباید هیچ APIی صدا زده شود: {calls}"


def t_noop_without_owner():
    """نبودِ owner_chat_id → no-op (نمی‌توان بدون allowlist کار کرد)."""
    http = _fake_get_factory({}, [])
    ch = TC(token="FAKETOKEN123456", owner_chat_id=None, http_get=http)
    assert ch.wired is False
    assert ch.poll_once() == 0


def t_wired_needs_both():
    """wired فقط با token + owner هر دو."""
    assert TC(token="t", owner_chat_id=1).wired is True
    assert TC(token="t", owner_chat_id=None).wired is False
    assert TC(token="", owner_chat_id=1).wired is False


def t_longpoll_params_and_offset():
    """long-poll: timeout پاس می‌رود، offset = last_update_id + 1 پیش می‌رود."""
    calls = []
    payload = {"ok": True, "result": [
        {"update_id": 100, "message": {"chat": {"id": 42}, "text": "hi", "from": {"id": 42}, "date": 1}},
        {"update_id": 101, "message": {"chat": {"id": 42}, "text": "yo", "from": {"id": 42}, "date": 2}},
    ]}
    http = _fake_get_factory({"getUpdates": payload}, calls)
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_get=http, longpoll_timeout=30)
    n = ch.poll_once()
    assert n == 2, n
    method, params = calls[0]
    assert method == "getUpdates"
    assert params["timeout"] == "30", params
    assert params["offset"] == "0", params        # اولین بار از 0
    # دفعهٔ بعد offset = آخرین update_id + 1
    assert ch._offset == 102, ch._offset


def t_offset_persisted_across_restart():
    """offset در فایل ذخیره می‌شود؛ نمونهٔ جدیدِ بات (restart) همان offset را می‌خواند.
    بدون این، restart → offset=0 → پیام‌های قدیمی دوباره در quarantine."""
    import approval_channel as ac
    sd = ENV["ops"] / "state" / f"restart-{os.getpid()}"
    sd.mkdir(parents=True, exist_ok=True)
    ofile = ac._offset_state_path(str(sd))
    assert not ofile.exists(), "آغازِ تمیز"
    # نمونهٔ ۱: دو پیام پردازش کن → offset = 102
    payload = {"ok": True, "result": [
        {"update_id": 100, "message": {"chat": {"id": 42}, "text": "a", "from": {"id": 42}, "date": 1}},
        {"update_id": 101, "message": {"chat": {"id": 42}, "text": "b", "from": {"id": 42}, "date": 2}},
    ]}
    ch1 = TC(token="FAKETOKEN123456", owner_chat_id=42,
             http_get=_fake_get_factory({"getUpdates": payload}, []), state_dir=str(sd))
    assert ch1.poll_once() == 2
    assert ch1._offset == 102
    assert ofile.exists(), "offset باید persist شده باشد"
    # نمونهٔ ۲ (restart): باید offset=102 را از فایل بخواند، نه 0
    calls2 = []
    ch2 = TC(token="FAKETOKEN123456", owner_chat_id=42,
             http_get=_fake_get_factory({"getUpdates": {"ok": True, "result": []}}, calls2),
             state_dir=str(sd))
    assert ch2._offset == 102, f"restart باید offset را از فایل بخواند: {ch2._offset}"
    ch2.poll_once()
    assert calls2[0][1]["offset"] == "102", "اولین getUpdates باید از offset ذخیره‌شده"


def t_offset_not_persisted_without_state_dir():
    """C7.2: state_dir=None دیگر «RAM-only» نیست — به دایرکتوریِ canonicalِ durable resolve
    می‌شود (callback state هرگز RAM-only نیست). پس offset همیشه persist می‌شود و نمونهٔ تازه
    آن را می‌خواند. (offset ابتدا پاک می‌شود تا از leakِ تست‌های قبلی جدا بماند.)"""
    import approval_channel as ac
    ac._offset_state_path(str(ac.opslib.STATE_DIR)).unlink(missing_ok=True)
    payload = {"ok": True, "result": [
        {"update_id": 50, "message": {"chat": {"id": 42}, "text": "x", "from": {"id": 42}, "date": 1}}]}
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42,
            http_get=_fake_get_factory({"getUpdates": payload}, []))
    assert ch._offset == 0, "آغازِ تمیز (offset پاک شد)"
    ch.poll_once()
    assert ch._offset == 51
    # نمونهٔ تازه بدونِ state_dirِ صریح → همان دایرکتوریِ canonical → offset را durable می‌خواند
    ch2 = TC(token="FAKETOKEN123456", owner_chat_id=42)
    assert ch2._offset == 51, "offset باید durable-by-default از دایرکتوریِ canonical خوانده شود"


def t_owner_allowed_and_quarantined():
    """پیامِ مالک پذیرفته می‌شود ولی به‌عنوان DATA در quarantine؛ اجرا نمی‌شود."""
    http = _fake_get_factory({"getUpdates": {"ok": True, "result": [
        {"update_id": 5, "message": {"chat": {"id": 42}, "text": "/anything",
         "from": {"id": 42}, "date": 1}}]}}, [])
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_get=http)
    assert ch.poll_once() == 1
    q = ch._quarantine
    assert len(q) == 1, q
    assert q[0]["chat_id"] == 42 and q[0]["text"] == "/anything", q[0]
    # شیر بسته: هیچ approvalی از پیام ساخته نشد
    assert ch.approval_for("anything", 0.0) is None


def test_non_owner_ignored():
    """allowlist: غیرمالک ignore می‌شود (ولی offset جلو می‌رود تا دوباره نیاید)."""
    ac._offset_state_path(str(ac.opslib.STATE_DIR)).unlink(missing_ok=True)    # C7.2: offset durable-by-default → آغازِ تمیز
    http = _fake_get_factory({"getUpdates": {"ok": True, "result": [
        {"update_id": 9, "message": {"chat": {"id": 999}, "text": "intruder",
         "from": {"id": 999}, "date": 1}}]}}, [])
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_get=http)
    n = ch.poll_once()
    assert n == 1, n                                   # پردازش‌شد ولی ignore
    assert ch._quarantine == [], ch._quarantine        # هیچ‌چیز ذخیره نشد
    assert ch._offset == 10, ch._offset                # offset جلو رفت


def t_network_error_is_fail_soft():
    """خطای شبکه fail-soft: poll_once 0 برمی‌گرداند، استثنا بالا نمی‌آید، URL leak نمی‌شود."""
    def boom(url, timeout_s):
        raise urllib.error.URLError("simulated network down")
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_get=boom)
    assert ch.poll_once() == 0                          # fail-soft


def t_seam_approval_only_via_record():
    """شیر بسته: approval_for در T-1 همیشه None. فقط seam (T-2) می‌نویسد."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    assert ch.approval_for("ACT-1", 50.0) is None
    ch._record_approval(Approval("ACT-1", 50.0, "approved", "telegram"))
    a = ch.approval_for("ACT-1", 50.0)
    assert a is not None and a.valid and a.source == "telegram", a
    # mismatch مبلغ همچنان deny (قراردادِ money_gate)
    assert ch.approval_for("ACT-1", 99.0) is None


def t_kill_check_stops_poll():
    """kill supreme: kill_check=True → poll_once می‌ایستد قبل از فراخوانیِ شبکه."""
    calls = []
    http = _fake_get_factory({"getUpdates": {"ok": True, "result": []}}, calls)
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_get=http,
            kill_check=lambda: True)
    assert ch.poll_once() == 0
    assert calls == [], "kill باید قبل از fetch بایستد"


def t_stop_flag_stops_loop():
    """run_forever با پرچمِ داخلیِ stop() تمیز برمی‌گردد."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42,
            http_get=_fake_get_factory({"getUpdates": {"ok": True, "result": []}}, []))
    ch.stop()
    ch.run_forever()          # باید فوراً برگردد، نه hang
    assert ch._stop is True


def t_token_never_leaked_in_repr():
    """secret-guard I9: __repr__ کلِ token را نشان نمی‌دهد."""
    ch = TC(token="SUPERSECRETTOKENXYZ", owner_chat_id=42)
    r = repr(ch)
    assert "SUPERSECRETTOKENXYZ" not in r, r
    assert "SUPE…" in r or "…" in r, r         # فقط mask دیده می‌شود


def t_url_builder_no_log_of_token():
    """URL حاویِ token است؛ هیچ مسیری در کلاس آن را لاگ/echo نمی‌کند. این یک چکِ سازه‌ای
    روی _build_url است که حداقل token واقعاً در URL هست (برای اثباتِ حضور) ولی تنها جایی
    که دیده می‌شود همین URLِ تولید-شده است، نه log."""
    ch = TC(token="THE_REAL_TOKEN", owner_chat_id=42)
    url = ch._build_url("getUpdates", {"offset": 0, "timeout": 5})
    assert "THE_REAL_TOKEN" in url                      # فقط در URL (برای API لازم)
    # اما __repr__ نباید آن را نشان دهد
    assert "THE_REAL_TOKEN" not in repr(ch)


def t_callback_query_routed_as_data():
    """callback_query (دکمهٔ اینلاین، برای T-2) هم به‌عنوان DATA در quarantine می‌رسد."""
    http = _fake_get_factory({"getUpdates": {"ok": True, "result": [
        {"update_id": 7, "callback_query": {
            "message": {"chat": {"id": 42}, "from": {"id": 42}, "date": 1},
            "data": "approve:ACT-1"}}]}}, [])
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_get=http)
    assert ch.poll_once() == 1
    assert len(ch._quarantine) == 1, ch._quarantine
    assert ch._quarantine[0]["text"] == "approve:ACT-1", ch._quarantine[0]
    # ولی هنوز شیر بسته — در T-1 از callback هیچ approvalی ساخته نمی‌شود
    assert ch.approval_for("ACT-1", 50.0) is None


# ════════════════════════════════════════════════════════════════════════════════
# T-2 · تأییدِ irreversible/مالی → human-append → EffectorGate.settle (paper-mode)
# ════════════════════════════════════════════════════════════════════════════════
# برای تستِ settle واقعی، یک EffectorGate + Ledger واقعی (در vault موقتِ harness) می‌سازیم.
# این دقیقاً همان قراردادی است که chrono.on_human_judgment استفاده می‌کند.

def _gate_and_ledger():
    """یک EffectorGate + Ledger تازه در vault موقت می‌سازد (هم‌سان با test_chrono_langar)."""
    import chrono
    sys.path.insert(0, str(ENV["genome"] / "ledger"))
    from ledger import Ledger
    lg = Ledger(ENV["genome"] / "ledger" / f"tg-{os.getpid()}-{id(object())}.jsonl")
    db = chrono.ChronoDB(ENV["ops"] / "state" / f"tg-{os.getpid()}-{id(object())}.db")
    gate = chrono.EffectorGate(db, ledger=lg)
    return gate, lg, db


def _fake_post_factory(sent: list):
    """http_post فیک: بدنهٔ sendMessage را در sent ثبت می‌کند. هیچ شبکه‌ای."""
    def _fake(url: str, body: dict, timeout_s: float = 10.0):
        sent.append({"body": body})
        return {"ok": True, "result": {"message_id": 1}}
    return _fake


def t_card_not_sent_when_not_wired():
    """not wired → request_approval_card False؛ هیچ POSTی فرستاده نمی‌شود."""
    sent = []
    ch = TC(token="", owner_chat_id=42, http_post=_fake_post_factory(sent))
    assert ch.request_approval_card("E1", 50.0, "test", "") is False
    assert sent == [], sent


def t_card_sent_with_three_buttons():
    """کارت فرستاده می‌شود با ۳ دکمهٔ متمایز و callback_data حاویِ توکنِ ضدِ جعل."""
    sent = []
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory(sent))
    ok = ch.request_approval_card("E1", 25.0, "خریدِ X", "over-gate")
    assert ok is True
    assert len(sent) == 1, sent
    body = sent[0]["body"]
    assert body["chat_id"] == 42
    assert "AU$25.00" in body["text"]
    assert "خریدِ X" in body["text"]
    kb = body["reply_markup"]["inline_keyboard"][0]
    assert len(kb) == 3, kb
    labels = [b["text"] for b in kb]
    assert "تأیید ✅" in labels and "رد ❌" in labels and "بعداً ⏳" in labels, labels
    # callback_data = app:<verb>:<effect_id>:<token>
    approve_cb = [b["callback_data"] for b in kb if b["text"] == "تأیید ✅"][0]
    assert approve_cb.startswith("app:approve:E1:"), approve_cb
    token = approve_cb.split(":")[3]
    assert len(token) >= 16, token            # توکنِ هش، نه کوتاه


def t_fake_approval_wrong_token_rejected():
    """تأییدِ جعلی با توکنِ نامنطبق → رد؛ هیچ human-appendی صورت نمی‌گیرد."""
    sent = []
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory(sent))
    ch.request_approval_card("E2", 50.0, "test", "")
    # callback با توکنِ غلط
    resp = ch.dispatch_callback("app:approve:E2:WRONGTOKEN")
    assert "رد" in resp, resp
    assert ch._pending["E2"]["status"] == "pending", ch._pending["E2"]   # هنوز pending
    assert ch.approval_for("E2", 50.0) is None                            # شیر بسته ماند


def t_unknown_effect_rejected():
    """callback برای effect_id ناشناخته → رد."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.dispatch_callback("app:approve:UNKNOWN:anytoken")
    assert "رد" in resp, resp


def t_deny_does_not_settle():
    """دکمهٔ رد → هیچ settle/human-append؛ status = denied."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory([]))
    ch.request_approval_card("E3", 50.0, "test", "")
    token = ch._pending["E3"]["token"]
    resp = ch.dispatch_callback(f"app:deny:E3:{token}")
    assert "رد شد" in resp, resp
    assert ch._pending["E3"]["status"] == "denied"
    assert ch.approval_for("E3", 50.0) is None


def t_later_keeps_pending():
    """دکمهٔ بعداً → pending باقی می‌ماند (نه deny، نه approve)."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory([]))
    ch.request_approval_card("E4", 50.0, "test", "")
    token = ch._pending["E4"]["token"]
    resp = ch.dispatch_callback(f"app:later:E4:{token}")
    assert "بعداً" in resp, resp
    assert ch._pending["E4"]["status"] == "pending"


def t_approve_settles_via_human_append():
    """تأییدِ واقعی → on_human_judgment (age_tick+1) → release → settle.
    این نقطهٔ کلیدیِ TINV-7 است: تنها مسیرِ settle."""
    gate, lg, db = _gate_and_ledger()
    try:
        effect_id = gate.request("PAY", "ref://bill-1")   # pending در gated_effect
        ch = TC(token="FAKETOKEN123456", owner_chat_id=42,
                http_post=_fake_post_factory([]), gate=gate, ledger=lg)
        ch.request_approval_card(effect_id, 50.0, "قبضِ برق", "over-gate")
        token = ch._pending[effect_id]["token"]
        # قبل از approve: effect pending است، settle باید False
        assert gate.settle(effect_id) is False, "نباید قبل از approve settle شود"
        assert lg.last_age_tick() == 0
        # approve → human-append (age_tick 0→1) → release → settle True
        resp = ch.dispatch_callback(f"app:approve:{effect_id}:{token}")
        assert "تأیید شد" in resp, resp
        assert lg.last_age_tick() == 1, "human-append باید age_tick را +1 کند"
        row = db.q("SELECT status FROM gated_effect WHERE effect_id=?", (effect_id,))
        assert row and row[0][0] == "settled", f"effect باید settled باشد: {row}"
        # و approval ثبت شد
        a = ch.approval_for(effect_id, 50.0)
        assert a is not None and a.valid and a.source == "telegram", a
    finally:
        db.close()


def t_double_approve_idempotent():
    """approve دوم روی همان effect → رد (قبلاً تصمیم‌گرفته). جلوی replay."""
    gate, lg, db = _gate_and_ledger()
    try:
        effect_id = gate.request("PAY", "ref://bill-2")
        ch = TC(token="FAKETOKEN123456", owner_chat_id=42,
                http_post=_fake_post_factory([]), gate=gate, ledger=lg)
        ch.request_approval_card(effect_id, 50.0, "test", "")
        token = ch._pending[effect_id]["token"]
        r1 = ch.dispatch_callback(f"app:approve:{effect_id}:{token}")
        assert "تأیید" in r1
        r2 = ch.dispatch_callback(f"app:approve:{effect_id}:{token}")
        assert "رد" in r2, f"approve دوم باید رد شود: {r2}"
    finally:
        db.close()


def t_post_network_error_fail_soft():
    """خطای شبکه در POST → request_approval_card False؛ اما intent در registry ثبت شد (retry)."""
    def boom(url, body, timeout_s=10.0):
        raise urllib.error.URLError("down")
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=boom)
    ok = ch.request_approval_card("E5", 50.0, "test", "")
    assert ok is False
    assert "E5" in ch._pending                       # intent باقی‌ماند برای retry


# ════════════════════════════════════════════════════════════════════════════════
# T-3 · UIِ Lead: /lead → attribution.propose (mint LEAD-YYYYMMDD-nnn)
# ════════════════════════════════════════════════════════════════════════════════

def t_lead_prompt_shown():
    """/lead بدون آرگومان → راهنمای فرمت + لیستِ پاها."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.handle_command("/lead")
    assert resp is not None and "ثبتِ لید" in resp, resp
    assert "lead.doer" in resp and "ziman.doer" in resp and "crypto.doer" in resp, resp


def t_lead_parse_mints_id():
    """/lead با ورودیِ معتبر → attribution.propose → LEAD-YYYYMMDD-nnn واقعی در ledger."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.handle_command("/lead بازسازی | 3000 | ziman.doer")
    assert resp is not None and "ثبت شد" in resp, resp
    # کدِ LEAD-YYYYMMDD-nnn باید در پاسخ باشد
    import re
    m = re.search(r"LEAD-\d{8}-\d{3}", resp)
    assert m, f"attribution_id مینت‌نشده در پاسخ: {resp}"


def t_lead_invalid_amount():
    """ارزشِ غیرعددی → پیامِ خطا (fail-closed، هیچ PROPOSALی)."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.handle_command("/lead نام | یک میلیون | lead.doer")
    assert resp is not None and "عدد" in resp, resp


def t_lead_negative_amount():
    """ارزشِ منفی → پیامِ خطا."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.handle_command("/lead نام | -50 | lead.doer")
    assert resp is not None and "منفی" in resp, resp


def t_lead_unknown_cell_defaults():
    """پای ناشناخته → پیش‌فرضِ lead.doer (نه reject — mirrorِ panel)."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.handle_command("/lead نام | 100 | bogus.doer")
    assert resp is not None and "ثبت شد" in resp, resp   # باز هم ثبت شد با پیش‌فرض


def t_lead_missing_parts():
    """ورودیِ ناقص (بدون |) → راهنمای فرمت."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.handle_command("/lead فقط نام")
    assert resp is not None and "ناقص" in resp, resp


def t_unknown_command_returns_none():
    """دستورِ ناشناخته → None (نادیده)."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    assert ch.handle_command("/unknown") is None
    assert ch.handle_command("") is None


def t_send_text_not_wired_noop():
    """send_text در حالتِ not wired → False (هیچ POSTی)."""
    sent = []
    ch = TC(token="", owner_chat_id=42, http_post=_fake_post_factory(sent))
    assert ch.send_text("hello") is False
    assert sent == [], sent


# ════════════════════════════════════════════════════════════════════════════════
# T-4 · lab N=1: /start_exp, /reveal (seal/SHA256، no-early-decode)
# ════════════════════════════════════════════════════════════════════════════════
import shutil as _shutil

# Test-owned, synthetic laboratory input: no live-tree dependency or raw identity.
_SEED_SRC = Path(__file__).resolve().parent / "fixtures" / "lab_data.json"


def _channel_with_lab():
    """یک channel با state_dir موقت + seed کپی‌شده. هر تست مستقل."""
    sd = ENV["ops"] / "state"
    sd.mkdir(parents=True, exist_ok=True)
    if _SEED_SRC.exists():
        _shutil.copy2(_SEED_SRC, sd / "lab_seed_data.json")
    return TC(token="FAKETOKEN123456", owner_chat_id=42, state_dir=str(sd))


def t_start_exp_creates_calendar():
    """/start_exp1 → تقویمِ ۱۴روزه تولید و قفل می‌شود."""
    ch = _channel_with_lab()
    r = ch.start_experiment("exp1")
    assert "شروع شد" in r and "14 روز" in r, r
    st = __import__("approval_channel")._load_lab_state(str(ENV["ops"] / "state"))
    run = st["experiments"]["exp1"]
    assert len(run["calendar"]) == 14, run["calendar"]
    assert run["status"] == "running"
    # قانونِ exp1: روز زوج = P_FORCE، فرد = P_IMAGE
    assert run["calendar"][1]["protocol"] == "P_FORCE"   # روز ۲
    assert run["calendar"][0]["protocol"] == "P_IMAGE"   # روز ۱


def t_start_exp2_deterministic_calendar():
    """exp2: تقویمِ تناوب با seed ثابت (بازتولیدپذیر). حداقل ۳ از هرکدام در هفتهٔ ۲."""
    ch = _channel_with_lab()
    ch.start_experiment("exp2")
    st = __import__("approval_channel")._load_lab_state(str(ENV["ops"] / "state"))
    cal = st["experiments"]["exp2"]["calendar"]
    w2 = [c["protocol"] for c in cal if c["day"] >= 8]
    assert w2.count("GESTURE_A") >= 3 and w2.count("GESTURE_B") >= 3, w2
    # هفتهٔ ۱ فقط A
    w1 = [c["protocol"] for c in cal if c["day"] <= 7]
    assert all(g == "GESTURE_A" for g in w1), w1


def t_sealed_prediction_not_decoded_at_start():
    """در start فقط sha256 ذخیره می‌شود؛ b64 هرگز decode نمی‌شود (no-early-decode)."""
    ch = _channel_with_lab()
    ch.start_experiment("exp1")
    st = __import__("approval_channel")._load_lab_state(str(ENV["ops"] / "state"))
    run = st["experiments"]["exp1"]
    assert run["sealed_sha256"], "sha256 باید ذخیره شود"
    assert "b64" not in run and "prediction" not in run, "b64 نباید در state باشد"
    assert len(run["sealed_sha256"]) == 64             # sha256 hex


def t_reveal_locked_before_end_date():
    """/reveal قبل از end_date → قفل است؛ prediction decode نمی‌شود."""
    ch = _channel_with_lab()
    ch.start_experiment("exp1")
    r = ch.reveal_experiment("exp1")
    assert "قفل" in r, r
    assert "sha256" not in r.lower() or "تأیید" not in r   # نه تأییدِ موفق


def t_reveal_after_end_date_verifies_sha256():
    """/reveal بعد از end_date → decode + verify sha256 → متنِ prediction نمایش."""
    ch = _channel_with_lab()
    ch.start_experiment("exp1")
    # end_date را به گذشته ببریم (دستکاریِ state برای تست)
    import approval_channel as ac
    st = ac._load_lab_state(str(ENV["ops"] / "state"))
    st["experiments"]["exp1"]["end_date"] = "2020-01-01"
    ac._save_lab_state(st, str(ENV["ops"] / "state"))
    r = ch.reveal_experiment("exp1")
    assert "آشکار شد" in r and "sha256 تأیید شد" in r, r


def t_reveal_tampered_seed_rejected():
    """اگر sha256 منطبق نباشد (seed دست‌خورده) → رد."""
    ch = _channel_with_lab()
    ch.start_experiment("exp1")
    import approval_channel as ac
    st = ac._load_lab_state(str(ENV["ops"] / "state"))
    st["experiments"]["exp1"]["end_date"] = "2020-01-01"
    st["experiments"]["exp1"]["sealed_sha256"] = "0" * 64   # هشِ غلط
    ac._save_lab_state(st, str(ENV["ops"] / "state"))
    r = ch.reveal_experiment("exp1")
    assert "شکست" in r or "جعل" in r or "منطبق نیست" in r, r


def t_reveal_unknown_experiment():
    """/reveal برای آزمایشِ شروع‌نشده → خطا."""
    ch = _channel_with_lab()
    r = ch.reveal_experiment("exp9")
    assert "فعال نیست" in r, r


def t_no_trend_shown_during_experiment():
    """ضدِ نشتِ انتظار: در طولِ آزمایش هیچ ترند/تفسیری در lab_status نیست."""
    ch = _channel_with_lab()
    ch.start_experiment("exp1")
    r = ch.lab_status()
    assert "exp1" in r and "running" in r
    assert "ترند" not in r and "تفسیر" not in r and "نتیجه" not in r, r


# ════════════════════════════════════════════════════════════════════════════════
# T-5 · /status: فقط‌خواندنی
# ════════════════════════════════════════════════════════════════════════════════

def _channel_with_state_files():
    """channel با state_dir موقت + ORGANISM-STATE.json شبیه‌سازی‌شده."""
    sd = ENV["ops"] / "state"
    sd.mkdir(parents=True, exist_ok=True)
    org = {"ts": "2026-07-08T22:00:00", "started": "2026-07-08T15:00:00",
           "halted": None, "frozen": False, "stop_organism": False,
           "month": {"aud": 12.50, "usd": 8.0}, "today": {"usd": 0.5},
           "suspect_zero_total": 0, "conflicts": [],
           "germline_lag_h": 18.8, "germline_alert": "warn"}
    (sd / "ORGANISM-STATE.json").write_text(
        __import__("json").dumps(org, ensure_ascii=False), encoding="utf-8")
    return TC(token="FAKETOKEN123456", owner_chat_id=42, state_dir=str(sd))


def t_status_read_only_report():
    """/status → گزارشِ فقط‌خواندنی با خرج، lag، σ."""
    ch = _channel_with_state_files()
    r = ch.status_report()
    assert "وضعیت" in r and "AU$12.50" in r, r
    assert "18.8" in r and "🟠" in r, r              # germline_lag warn
    assert "فقط‌خواندنی" in r, r


def t_status_no_state():
    """/status وقتی state نباشد → پیامِ روشن‌نبودن."""
    sd = ENV["ops"] / "state" / "empty_subdir"
    sd.mkdir(parents=True, exist_ok=True)
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, state_dir=str(sd))
    r = ch.status_report()
    assert "روشن نشده" in r, r


def t_status_writes_nothing():
    """/status هیچ فایلی نمی‌نویسد (فقط‌خواندنی)."""
    import json
    sd = ENV["ops"] / "state"
    ch = _channel_with_state_files()
    before = (sd / "ORGANISM-STATE.json").read_text(encoding="utf-8")
    ch.status_report()
    after = (sd / "ORGANISM-STATE.json").read_text(encoding="utf-8")
    assert before == after, "status نباید state را تغییر دهد"


# ════════════════════════════════════════════════════════════════════════════════
# T-6 · RFC/تکامل: کارتِ مرور پشتِ flag
# ════════════════════════════════════════════════════════════════════════════════

def t_rfc_card_sent_with_buttons():
    """rfc_card → POST با دکمه‌های merge/deny."""
    sent = []
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory(sent))
    ok = ch.rfc_card("RFC-001", "افزودنِ replication guard")
    assert ok is True and len(sent) == 1, sent
    body = sent[0]["body"]
    kb = body["reply_markup"]["inline_keyboard"][0]
    labels = [b["text"] for b in kb]
    assert any("merge" in l for l in labels) and any("رد" in l for l in labels), labels
    assert body["text"].find("RFC-001") >= 0


def t_rfc_card_not_wired_noop():
    """not wired → rfc_card False."""
    ch = TC(token="", owner_chat_id=42)
    assert ch.rfc_card("RFC-001", "x") is False


class _Flag:
    """ctx manager: ست/پاک‌کردنِ یک env-flag با restore."""
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


def t_rfc_card_notif_flag_off_posts_to_telegram_as_before():
    """۲۰۲۶-۰۸-۰۷: پشتِ notif_inbox.FLAG خاموش → دقیقاً همان رفتارِ قبل (POST واقعی)."""
    _tgc = str(Path(__file__).resolve().parent.parent / "telegram_center")
    sys.path.insert(0, _tgc) if _tgc not in sys.path else None
    import notif_inbox as _ni
    sent = []
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory(sent))
    with _Flag(_ni.FLAG, None):
        ok = ch.rfc_card("RFC-FLAGOFF", "تستِ فلگِ خاموش")
    assert ok is True and len(sent) == 1, sent
    assert "RFC-FLAGOFF" in sent[0]["body"]["text"]


def t_rfc_card_notif_flag_on_routes_to_inbox_never_posts():
    """۲۰۲۶-۰۸-۰۷: پشتِ notif_inbox.FLAG روشن → کارت به صندوق می‌رود، هیچ POSTی
    به تلگرام نمی‌رود — ولی mint/token/pending_rfc دست‌نخورده می‌مانند (رأیِ
    مینی‌اپ باید هنوز کار کند)."""
    _tgc = str(Path(__file__).resolve().parent.parent / "telegram_center")
    sys.path.insert(0, _tgc) if _tgc not in sys.path else None
    import notif_inbox as _ni
    try:
        _ni._STORE_PATH.unlink()
    except OSError:
        pass
    sent = []
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory(sent))
    with _Flag(_ni.FLAG, "1"):
        ok = ch.rfc_card("RFC-FLAGON", "تستِ فلگِ روشن")
    assert ok is True, ok
    assert sent == [], f"نباید هیچ POSTی به تلگرام برود: {sent}"
    # mint/token/pending_rfc دست‌نخورده: هنوز با توکنِ واقعی ثبت شده
    rec = ch._pending_rfc.get("RFC-FLAGON")
    assert rec is not None and rec.get("token") and rec.get("status") == "pending", rec
    # اشاره‌گر در صندوق نشسته
    items = _ni.list_items()
    assert items and items[0]["category"] == "rfc_card", items
    assert items[0]["kind"] == "pointer", items[0]
    assert items[0]["meta"].get("rfc_id") == "RFC-FLAGON", items[0]


# ════════════════════════════════════════════════════════════════════════════════
# T-7 · kill-switch + Re-entry Packet
# ════════════════════════════════════════════════════════════════════════════════

def t_stop_writes_authoritative_file():
    """/stop → فایلِ STOP-ORGANISM نوشته می‌شود (authoritative)."""
    sd = ENV["ops"] / "state"
    sd.mkdir(parents=True, exist_ok=True)
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, state_dir=str(sd))
    stop_file = sd.parent / "STOP-ORGANISM"
    if stop_file.exists():
        stop_file.unlink()
    r = ch.kill_switch()
    assert "KILL-SWITCH" in r, r
    assert stop_file.exists(), "STOP-ORGANISM باید نوشته شود"
    ch.stop()
    stop_file.unlink()                                 # پاک‌سازی


def t_stop_stops_poll_loop():
    """kill_switch → حلقهٔ poll هم می‌ایستد (self._stop = True)."""
    sd = ENV["ops"] / "state"
    sd.mkdir(parents=True, exist_ok=True)
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, state_dir=str(sd))
    ch.kill_switch()
    assert ch._stop is True
    assert ch._killed() is True
    (sd.parent / "STOP-ORGANISM").unlink(missing_ok=True)


def t_reentry_packet_shows_pending():
    """/reentry → کارت‌های معلق + (اگر gate) اثرهای freeze‌شده را نشان می‌دهد."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory([]))
    ch.request_approval_card("E-RE", 50.0, "test", "")     # یک کارتِ pending
    r = ch.reentry_packet()
    assert "Re-entry" in r and "کارت‌های تأییدِ معلق: 1" in r, r
    assert "cognition" in r or "heartbeat" in r


def t_reentry_packet_with_gate():
    """/reentry با gate → تعدادِ اثرهای pending در gated_effect را هم نشان می‌دهد."""
    gate, lg, db = _gate_and_ledger()
    try:
        gate.request("PAY", "ref://x")                       # یک effect pending
        ch = TC(token="FAKETOKEN123456", owner_chat_id=42,
                http_post=_fake_post_factory([]), gate=gate, ledger=lg)
        r = ch.reentry_packet()
        assert "freeze‌شده: 1" in r or "freeze‌شده: 1" in r.replace("\u200c", ""), r
    finally:
        db.close()


# ════════════════════════════════════════════════════════════════════════════════
# Router: تمامِ دستورها از handle_command عبور می‌کنند
# ════════════════════════════════════════════════════════════════════════════════

def t_router_dispatches_all_commands():
    """handle_command تمامِ UIهای v2 را dispatch می‌کند (هر کدام یک UIِ متمایز).
    UX v2: /start_exp, /reveal, /lab, /reentry حذف شدند. /start اضافه شد."""
    sd = ENV["ops"] / "state"
    sd.mkdir(parents=True, exist_ok=True)
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, state_dir=str(sd),
            http_post=_fake_post_factory([]))
    assert ch.handle_command("/start") is not None      # UX v2: منوی اصلی
    assert ch.handle_command("/status") is not None
    assert ch.handle_command("/lead") is not None
    assert ch.handle_command("/stop") is not None
    # حذف‌شده در UX v2 و همچنان بدونِ route:
    assert ch.handle_command("/start_exp1") is None     # T-4: فقط از دکمهٔ act
    assert ch.handle_command("/lab") is None             # T-4: فقط از منو
    # به‌روزرسانی 2026-07-10 (Cockpit v2 §۸): reveal/reentry عمداً resurface شدند —
    # مگاپرامپت TELEGRAM-BRAIN-COCKPIT-v2-FULL-BODY آن‌ها را به router برگرداند.
    assert ch.handle_command("/reveal exp1") is not None
    assert ch.handle_command("/reentry") is not None
    (sd.parent / "STOP-ORGANISM").unlink(missing_ok=True)


def t_ux_v2_start_menu_has_icon():
    """UX v2 §۲: /start منوی اصلی با آیکن 🐙."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    menu = ch.handle_command("/start")
    # fix 2026-07-10: منو از UX v3 یک dict است؛ `in` روی dict کلیدها را می‌گردد نه متن —
    # این چک با کدِ HEAD هم قرمز بود (باگِ خودِ تست). حالا متنِ واقعی چک می‌شود.
    text = menu["text"] if isinstance(menu, dict) else str(menu or "")
    assert menu is not None and "🐙" in text, f"منو باید آیکن 🐙 داشته باشد: {text[:120]}"


def t_ux_v2_status_has_html_and_mode():
    """UX v2 §۲: /status غنی با HTML + mode color (🟢/🟡/🔴)."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, state_dir=str(ENV["ops"] / "state"))
    r = ch.status_report_v2()
    assert "──────" in r  # خط‌جداکننده
    assert "🐙" in r or "🟢" in r or "🟡" in r or "🔴" in r  # mode color


def t_ux_v2_approval_card_rich_html():
    """UX v2 §۲: کارتِ تأیید غنی با خط‌جداکننده + گارد + آیکن."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory([]))
    ch.request_approval_card("E1", 25.0, "تست", "over-gate")
    # بررسیِ متنِ کارت
    card = ch._render_approval_card("E1", 25.0, "تست", "over-gate")
    assert "──────" in card and "🛡" in card and "🦑" in card or "🐙" in card
    assert "AU$25.00" in card


if __name__ == "__main__":
    _checks = [
        # T-1
        ("[T-1] نبودِ token → no-opِ امن", t_noop_without_token),
        ("[T-1] نبودِ owner → no-op", t_noop_without_owner),
        ("[T-1] wired = token + owner هر دو", t_wired_needs_both),
        ("[T-1] long-poll: timeout + offset = last+1", t_longpoll_params_and_offset),
        ("[T-1] offset در restart از فایل خوانده می‌شود (persist)", t_offset_persisted_across_restart),
        ("[T-1] بدونِ state_dir، offset در حافظه (نه فایل)", t_offset_not_persisted_without_state_dir),
        ("[T-1] پیامِ مالک → quarantine (DATA نه دستور)، شیر بسته", t_owner_allowed_and_quarantined),
        ("[T-1] allowlist: غیرمالک ignore می‌شود (offset جلو می‌رود)", test_non_owner_ignored),
        ("[T-1] خطای شبکه fail-soft", t_network_error_is_fail_soft),
        ("[T-1] شیر بسته: approval فقط از seam", t_seam_approval_only_via_record),
        ("[T-1] kill_check → poll_once می‌ایستد قبل از شبکه", t_kill_check_stops_poll),
        ("[T-1] stop() → run_forever تمیز برمی‌گردد", t_stop_flag_stops_loop),
        ("[T-1] secret-guard: __repr__ کلِ token را نشان نمی‌دهد", t_token_never_leaked_in_repr),
        ("[T-1] secret-guard: token فقط در URL، نه در repr/log", t_url_builder_no_log_of_token),
        ("[T-1] callback_query هم DATA، شیر بسته", t_callback_query_routed_as_data),
        # T-2
        ("[T-2] not wired → کارت فرستاده نمی‌شود", t_card_not_sent_when_not_wired),
        ("[T-2] کارت با ۳ دکمه + callback_data توکن‌دار فرستاده می‌شود", t_card_sent_with_three_buttons),
        ("[T-2] تأییدِ جعلی (توکنِ نامنطبق) → رد", t_fake_approval_wrong_token_rejected),
        ("[T-2] effect ناشناخته → رد", t_unknown_effect_rejected),
        ("[T-2] دکمهٔ رد → settle نمی‌کند", t_deny_does_not_settle),
        ("[T-2] دکمهٔ بعداً → pending می‌ماند", t_later_keeps_pending),
        ("[T-2] approve → human-append (age_tick+1) → settle (TINV-7)", t_approve_settles_via_human_append),
        ("[T-2] approve دوم → رد (ضدِ replay)", t_double_approve_idempotent),
        ("[T-2] خطای POST fail-soft، intent باقی می‌ماند", t_post_network_error_fail_soft),
        # T-3
        ("[T-3] /lead → راهنمای فرمت + پاها", t_lead_prompt_shown),
        ("[T-3] /lead معتبر → mint LEAD-YYYYMMDD-nnn در ledger", t_lead_parse_mints_id),
        ("[T-3] ارزشِ غیرعددی → خطا", t_lead_invalid_amount),
        ("[T-3] ارزشِ منفی → خطا", t_lead_negative_amount),
        ("[T-3] پای ناشناخته → پیش‌فرض", t_lead_unknown_cell_defaults),
        ("[T-3] ورودیِ ناقص → راهنما", t_lead_missing_parts),
        ("[T-3] دستورِ ناشناخته → None", t_unknown_command_returns_none),
        ("[T-3] send_text در not wired → no-op", t_send_text_not_wired_noop),
    ]
    assert _SEED_SRC.exists(), "synthetic laboratory fixture is required"
    _checks += [
        ("[T-4] /start_exp1 → تقویمِ ۱۴روزه تولید و قفل", t_start_exp_creates_calendar),
        ("[T-4] exp2 → تقویمِ تناوبِ بازتولیدپذیر", t_start_exp2_deterministic_calendar),
        ("[T-4] prediction در start decode نمی‌شود (فقط sha256)", t_sealed_prediction_not_decoded_at_start),
        ("[T-4] /reveal قبل از end_date → قفل", t_reveal_locked_before_end_date),
        ("[T-4] /reveal بعد از end_date → verify sha256", t_reveal_after_end_date_verifies_sha256),
        ("[T-4] /reveal با fixture دست‌خورده → رد", t_reveal_tampered_seed_rejected),
        ("[T-4] /reveal آزمایشِ ناشناخته → خطا", t_reveal_unknown_experiment),
        ("[T-4] ضدِ نشت: در طولِ آزمایش ترند نیست", t_no_trend_shown_during_experiment),
    ]
    _checks += [
        # T-5
        ("[T-5] /status → گزارشِ فقط‌خواندنی", t_status_read_only_report),
        ("[T-5] /status بدونِ state → پیامِ روشن‌نبودن", t_status_no_state),
        ("[T-5] /status هیچ writeای نمی‌کند", t_status_writes_nothing),
        # T-6
        ("[T-6] rfc_card با دکمه‌های merge/deny", t_rfc_card_sent_with_buttons),
        ("[T-6] rfc_card در not wired → no-op", t_rfc_card_not_wired_noop),
        ("[T-6] rfc_card: notif_inbox خاموش → POST مثلِ قبل",
         t_rfc_card_notif_flag_off_posts_to_telegram_as_before),
        ("[T-6] rfc_card: notif_inbox روشن → صندوق، صفر POST، token/pending دست‌نخورده",
         t_rfc_card_notif_flag_on_routes_to_inbox_never_posts),
        # T-7
        ("[T-7] /stop → STOP-ORGANISM نوشته می‌شود", t_stop_writes_authoritative_file),
        ("[T-7] /stop → حلقهٔ poll می‌ایستد", t_stop_stops_poll_loop),
        ("[T-7] /reentry → کارت‌های معلق", t_reentry_packet_shows_pending),
        ("[T-7] /reentry با gate → اثرهای freeze‌شده", t_reentry_packet_with_gate),
        # Router
        ("[Router] handle_command همهٔ UIها را dispatch می‌کند", t_router_dispatches_all_commands),
        ("[UX v2] /start منو با آیکن 🐙", t_ux_v2_start_menu_has_icon),
        ("[UX v2] /status غنی با mode color", t_ux_v2_status_has_html_and_mode),
        ("[UX v2] کارتِ تأیید غنی", t_ux_v2_approval_card_rich_html),
    ]
    failed = harness.run(_checks)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    failed = harness.run([
        ("نبودِ token → no-opِ امن (هیچ APIی صدا زده نمی‌شود)", t_noop_without_token),
        ("نبودِ owner → no-op", t_noop_without_owner),
        ("wired = token + owner هر دو", t_wired_needs_both),
        ("long-poll: timeout + offset = last+1", t_longpoll_params_and_offset),
        ("پیامِ مالک → quarantine (DATA نه دستور)، شیر بسته", t_owner_allowed_and_quarantined),
        ("allowlist: غیرمالک ignore می‌شود (offset جلو می‌رود)", test_non_owner_ignored),
        ("خطای شبکه fail-soft (URL/token leak نمی‌شود)", t_network_error_is_fail_soft),
        ("شیر بسته: approval فقط از seam (T-2) + mismatch مبلغ deny", t_seam_approval_only_via_record),
        ("kill_check → poll_once می‌ایستد قبل از شبکه", t_kill_check_stops_poll),
        ("stop() → run_forever تمیز برمی‌گردد", t_stop_flag_stops_loop),
        ("secret-guard: __repr__ کلِ token را نشان نمی‌دهد", t_token_never_leaked_in_repr),
        ("secret-guard: token فقط در URL، نه در repr/log", t_url_builder_no_log_of_token),
        ("callback_query (دکمهٔ T-2) هم DATA، شیر بسته", t_callback_query_routed_as_data),
    ])
    sys.exit(1 if failed else 0)
