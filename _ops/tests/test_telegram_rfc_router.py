#!/usr/bin/env python3
"""تست W-3 · routerِ RFCِ تلگرام + رفعِ باگ‌های نهفته در approval_channel.

پوشش:
  · rfc_card: token واقعی + registry (self._pending_rfc) + callback_dataی ۴-تکه.
  · _dispatch_rfc: merge/deny → ثبتِ verdict؛ توکنِ غلط/replay/کارتِ قدیمیِ ۳-تکه → رد
    (graceful، بدونِ crash). هیچ settle/gate در شاخهٔ rfc.
  · pop_rfc_verdicts: هر verdict دقیقاً یک‌بار، ترتیبِ قطعی (sorted by rfc_id).
  · poll_once (T-8): callbackِ مالک → dispatch؛ غریبه → ignore (allowlist)، dispatch نمی‌شود.
  · باگِ نهفتهٔ NameError: 'opslib' حالا import شده — مسیرهای خطای poll_once و
    _answer_callback_query دیگر run_forever را نمی‌کشند (structural + behavioral).
  · /lead با leg تزریقی → leg.intake؛ leg=None یا legِ خراب → مسیرِ موجودِ attribution.
  · رگرسیون: جریانِ پولِ "app:*" (TINV-7 human-append→settle) دست‌نخورده.

$0 آفلاین: هیچ شبکه‌ای — http_get/http_post فیک (همان الگوی test_telegram_channel).
"""
import os
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("telegram-rfc-router")
os.environ["OCTOPUS_CB_SECRET"] = "unit-test-rfc-secret-not-real"
os.environ["TELEGRAM_OWNER_CHAT_ID"] = "42"
import approval_channel as ac  # noqa: E402
from approval_channel import TelegramApprovalChannel as TC  # noqa: E402


# ─── فیک‌های HTTP (کپیِ دقیقِ الگوی test_telegram_channel — هیچ شبکه‌ای) ─────────

def _fake_get_factory(responses_for_url: dict, calls: list):
    """http_get فیک. responses_for_url: {method_substring: json_dict | callable}."""
    def _fake(url: str, timeout_s: float):
        from urllib.parse import urlparse, parse_qs
        p = urlparse(url)
        q = {k: v[0] for k, v in parse_qs(p.query).items()}
        calls.append((p.path.rsplit("/", 1)[-1], q))
        for key, val in responses_for_url.items():
            if key in p.path:
                return val(q) if callable(val) else val
        return {"ok": True, "result": []}
    return _fake


def _fake_post_factory(sent: list):
    """http_post فیک: بدنهٔ sendMessage/answerCallbackQuery را ثبت می‌کند."""
    def _fake(url: str, body: dict, timeout_s: float = 10.0):
        sent.append({"body": body})
        return {"ok": True, "result": {"message_id": 1}}
    return _fake


_SD_SEQ = {"n": 0}


def _new_state_dir():
    _SD_SEQ["n"] += 1
    p = Path(ENV["ops"]) / "state" / f"rfc-router-{_SD_SEQ['n']}"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def _rfc_channel(sent=None):
    """channel آماده با http_post فیک + یک کارتِ RFCِ ثبت‌شده. خروجی: (ch, sent)."""
    sent = [] if sent is None else sent
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory(sent),
            state_dir=_new_state_dir())
    assert ch.rfc_card("RFC-001", "افزودنِ replication guard") is True
    return ch, sent


# ═══ rfc_card: registry + token ═══════════════════════════════════════════════

def t_rfc_card_registers_and_embeds_token():
    """rfc_card → ثبت در _pending_rfc + callback_dataی ۴-تکه با توکنِ ≥۱۶ نویسه."""
    ch, sent = _rfc_channel()
    assert "RFC-001" in ch._pending_rfc
    meta = ch._pending_rfc["RFC-001"]
    assert meta["status"] == "pending" and len(meta["token"]) >= 16, meta
    assert len(sent) == 1, sent
    body = sent[0]["body"]
    assert "RFC-001" in body["text"]                     # متنِ کارت دست‌نخورده
    kb = body["reply_markup"]["inline_keyboard"][0]
    merge_cb = [b["callback_data"] for b in kb if "merge" in b["text"]][0]
    deny_cb = [b["callback_data"] for b in kb if "رد" in b["text"]][0]
    assert merge_cb == f"rfc:merge:RFC-001:{meta['token']}", merge_cb
    assert deny_cb == f"rfc:deny:RFC-001:{meta['token']}", deny_cb
    assert len(merge_cb.split(":")) == 4, merge_cb       # دقیقاً ۴-تکه


def t_rfc_card_post_failure_keeps_intent():
    """خطای POST → rfc_card False ولی intent در registry می‌ماند (retry — هم‌سان T-2)."""
    def boom(url, body, timeout_s=10.0):
        raise urllib.error.URLError("down")
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=boom,
            state_dir=_new_state_dir())
    assert ch.rfc_card("RFC-X", "s") is False
    assert ch._pending_rfc["RFC-X"]["status"] == "pending"


# ═══ _dispatch_rfc: merge/deny/جعل/replay/قدیمی ═══════════════════════════════

def t_rfc_merge_happy_path():
    """merge با توکنِ درست → status = merge-approved + پاسخِ موفق (بدونِ settle)."""
    ch, _ = _rfc_channel()
    token = ch._pending_rfc["RFC-001"]["token"]
    resp = ch.dispatch_callback(f"rfc:merge:RFC-001:{token}")
    assert "ثبت شد" in resp and "flag" in resp and "human-append" in resp, resp
    assert ch._pending_rfc["RFC-001"]["status"] == "merge-approved"


def t_rfc_wrong_token_rejected():
    """توکنِ غلط → رد؛ status هنوز pending (ضدِ جعل)."""
    ch, _ = _rfc_channel()
    resp = ch.dispatch_callback("rfc:merge:RFC-001:WRONGTOKEN")
    assert "رد" in resp and "توکن" in resp, resp
    assert ch._pending_rfc["RFC-001"]["status"] == "pending"


def t_rfc_replay_rejected():
    """merge دوم بعد از موفقیت → رد (قبلاً تصمیم‌گرفته = ضدِ replay)."""
    ch, _ = _rfc_channel()
    token = ch._pending_rfc["RFC-001"]["token"]
    r1 = ch.dispatch_callback(f"rfc:merge:RFC-001:{token}")
    assert "ثبت شد" in r1, r1
    r2 = ch.dispatch_callback(f"rfc:merge:RFC-001:{token}")
    assert "رد" in r2 and ("ناشناخته" in r2 or "قبلاً" in r2), r2
    assert ch._pending_rfc["RFC-001"]["status"] == "merge-approved"   # دست‌نخورده


def t_rfc_deny_path():
    """deny با توکنِ درست → status = denied + «رد شد»."""
    ch, _ = _rfc_channel()
    token = ch._pending_rfc["RFC-001"]["token"]
    resp = ch.dispatch_callback(f"rfc:deny:RFC-001:{token}")
    assert "رد شد" in resp, resp
    assert ch._pending_rfc["RFC-001"]["status"] == "denied"


def t_rfc_recard_never_clobbers_unconsumed_verdict():
    """گاردِ ضدِ clobber (بازبینیِ خصمانه 2026-07-10): کارتِ دوباره برای rfc_id ِ دارای
    verdictِ مصرف‌نشده → False و رأیِ مالک دست‌نخورده؛ بعد از مصرف → کارتِ نو مجاز."""
    ch, _ = _rfc_channel()
    token = ch._pending_rfc["RFC-001"]["token"]
    ch.dispatch_callback(f"rfc:merge:RFC-001:{token}")
    assert ch._pending_rfc["RFC-001"]["status"] == "merge-approved"
    # resubmit (مثل sweep ِ doctor) پیش از مصرف — نباید رأی را pending کند
    assert ch.rfc_card("RFC-001", "نسخهٔ دوم کارت") is False
    assert ch._pending_rfc["RFC-001"]["status"] == "merge-approved", "رأی مالک clobber شد!"
    # After APPLIED acknowledgment, the same RFC identity remains terminal; a new revision
    # must use a new RFC id rather than silently reopening the old decision.
    claimed = ch.claim_rfc_verdicts("doctor-test")
    hit = [x for x in claimed if x[0] == "RFC-001"][0]
    assert ch.begin_rfc_apply("RFC-001", hit[2], f"rfc:RFC-001:rev:{hit[2]}")
    assert ch.ack_rfc_verdict("RFC-001", hit[2], applied=True, receipt_id="ledger:test")
    assert ch.rfc_card("RFC-001", "نسخهٔ سوم کارت") is False


def t_rfc_legacy_3part_graceful():
    """کارتِ قدیمیِ ۳-تکه (rfc:merge:RFC-001) → پیامِ graceful، بدونِ exception."""
    ch, _ = _rfc_channel()
    resp = ch.dispatch_callback("rfc:merge:RFC-001")
    assert "قدیمی" in resp, resp
    assert ch._pending_rfc["RFC-001"]["status"] == "pending"          # دست‌نخورده


def t_rfc_unknown_verb_ignored():
    """فعلِ ناشناخته با توکنِ درست → «نادیده» (نه ثبت، نه crash)."""
    ch, _ = _rfc_channel()
    token = ch._pending_rfc["RFC-001"]["token"]
    resp = ch.dispatch_callback(f"rfc:explode:RFC-001:{token}")
    assert resp == "نادیده", resp
    assert ch._pending_rfc["RFC-001"]["status"] == "pending"


# ═══ pop_rfc_verdicts: exactly-once + ترتیبِ قطعی ═════════════════════════════

def t_pop_rfc_verdicts_exactly_once_sorted():
    """دو RFC با verdict → pop اول هر دو (sorted by rfc_id)؛ pop دوم خالی؛ pending تحویل نمی‌شود."""
    sent = []
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=_fake_post_factory(sent),
            state_dir=_new_state_dir())
    for rid in ("RFC-B", "RFC-A", "RFC-C"):
        assert ch.rfc_card(rid, f"summary {rid}") is True
    tok_a = ch._pending_rfc["RFC-A"]["token"]
    tok_b = ch._pending_rfc["RFC-B"]["token"]
    ch.dispatch_callback(f"rfc:merge:RFC-B:{tok_b}")
    ch.dispatch_callback(f"rfc:deny:RFC-A:{tok_a}")
    # Durable lease returns both sorted; a second claim is empty until lease expiry.
    got = ch.claim_rfc_verdicts("doctor-test")
    assert [(r, v) for r, v, _ in got] == [("RFC-A", "denied"), ("RFC-B", "merge-approved")], got
    assert ch.claim_rfc_verdicts("doctor-2") == []
    # Acknowledge deny; merge needs operation receipt.
    for rid, verdict, rev in got:
        if verdict == "denied":
            assert ch.ack_rfc_verdict(rid, rev, applied=False)
        else:
            assert ch.begin_rfc_apply(rid, rev, f"rfc:{rid}:rev:{rev}")
            assert ch.ack_rfc_verdict(rid, rev, applied=True, receipt_id="ledger:test")
    tok_c = ch._pending_rfc["RFC-C"]["token"]
    ch.dispatch_callback(f"rfc:merge:RFC-C:{tok_c}")
    got_c = ch.claim_rfc_verdicts("doctor-test")
    assert [(r, v) for r, v, _ in got_c] == [("RFC-C", "merge-approved")]


# ═══ poll_once (T-8): مسیرِ مالک vs غریبه ═════════════════════════════════════

def _cbq_update(update_id: int, chat_id: int, data: str, cbq_id: str = "cb1") -> dict:
    return {"update_id": update_id, "callback_query": {
        "id": cbq_id,
        "message": {"chat": {"id": chat_id}, "date": 1},
        "from": {"id": chat_id}, "data": data}}


def t_poll_once_owner_callback_dispatched():
    """callback_queryِ مالک از poll_once به dispatch می‌رسد (status عوض می‌شود) + answer می‌رود."""
    sent = []
    ch, _ = _rfc_channel(sent)
    token = ch._pending_rfc["RFC-001"]["token"]
    upd = {"ok": True, "result": [_cbq_update(10, 42, f"rfc:merge:RFC-001:{token}")]}
    ch._http_get = _fake_get_factory({"getUpdates": upd}, [])
    assert ch.poll_once() == 1
    assert ch._pending_rfc["RFC-001"]["status"] == "merge-approved", \
        "poll_once باید callback مالک را dispatch کند"
    # answerCallbackQuery فرستاده شد (بعد از کارتِ اولیه)
    answers = [s for s in sent if "callback_query_id" in s["body"]]
    assert len(answers) == 1 and "ثبت شد" in answers[0]["body"]["text"], answers
    # و در quarantine هم به‌عنوان DATA ثبت شد
    assert any(q["text"].startswith("rfc:merge:RFC-001:") for q in ch._quarantine)


def t_poll_once_stranger_callback_not_dispatched():
    """callback_queryِ غریبه (allowlist) → dispatch نمی‌شود؛ status پابرجا؛ answer نمی‌رود."""
    sent = []
    ch, _ = _rfc_channel(sent)
    token = ch._pending_rfc["RFC-001"]["token"]
    n_sent_before = len(sent)
    upd = {"ok": True, "result": [_cbq_update(11, 999, f"rfc:merge:RFC-001:{token}")]}
    ch._http_get = _fake_get_factory({"getUpdates": upd}, [])
    assert ch.poll_once() == 1                            # پردازش‌شد ولی ignore (offset جلو)
    assert ch._pending_rfc["RFC-001"]["status"] == "pending", \
        "callbackِ غریبه هرگز نباید dispatch شود"
    assert len(sent) == n_sent_before, "هیچ answer/پاسخی به غریبه نمی‌رود"
    assert ch._quarantine == [], "غریبه حتی وارد صفِ DATA نمی‌شود (allowlist ignore)"


# ═══ باگِ نهفتهٔ NameError (opslib import نشده بود) ═══════════════════════════

def t_opslib_imported_structural():
    """structural: سورسِ approval_channel حالا 'import opslib' دارد (رفعِ NameError نهفته)."""
    src = Path(ac.__file__).read_text(encoding="utf-8")
    assert "import opslib" in src, "opslib باید در سطحِ ماژول import شده باشد"


def t_poll_once_dispatch_error_no_nameerror():
    """behavioral: خطای داخلِ پردازشِ callback (answer که raise می‌کند) → poll_once زنده
    می‌ماند و alert می‌نویسد — قبلاً opslib.alert خودش NameError بود و run_forever را می‌کشت."""
    ch, _ = _rfc_channel()
    token = ch._pending_rfc["RFC-001"]["token"]
    upd = {"ok": True, "result": [_cbq_update(12, 42, f"rfc:merge:RFC-001:{token}")]}
    ch._http_get = _fake_get_factory({"getUpdates": upd}, [])

    def _boom_answer(cbq_id, text=""):
        raise RuntimeError("simulated answer failure")
    ch._answer_callback_query = _boom_answer              # صفتِ نمونه، متد را shadow می‌کند
    n = ch.poll_once()                                    # نباید exception بالا بیاید
    assert n == 1, n
    import opslib
    alerts = opslib.ALERTS_MD
    assert alerts.exists() and "T-8 dispatch error" in alerts.read_text(encoding="utf-8"), \
        "خطای dispatch باید alert بنویسد (نه NameError)"


def t_answer_callback_error_fail_soft():
    """behavioral: خطای POST در _answer_callback_query → False + alert (نه NameError)."""
    def boom(url, body, timeout_s=10.0):
        raise urllib.error.URLError("down")
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, http_post=boom)
    assert ch._answer_callback_query("cb9", "x") is False
    import opslib
    assert "answerCallbackQuery error" in opslib.ALERTS_MD.read_text(encoding="utf-8")


# ═══ /lead → legِ اختیاری (W-3) ═══════════════════════════════════════════════

def t_lead_with_injected_leg():
    """/lead با legِ تزریقی → leg.intake دقیقاً یک‌بار با آرگومان‌های پارس‌شده + پاسخِ تأیید."""
    from unittest.mock import MagicMock
    leg = MagicMock()
    leg.intake.return_value = {"ok": True, "attribution_id": "LEAD-20260710-001",
                               "cell": "ziman.doer", "expected_aud": 3000.0}
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, leg=leg)
    resp = ch.handle_command("/lead بازسازی | 3000 | ziman.doer")
    leg.intake.assert_called_once_with("بازسازی", 3000.0, cell="ziman.doer")
    assert resp is not None and "ثبت شد" in resp and "LEAD-20260710-001" in resp, resp


def t_lead_broken_leg_falls_back():
    """legِ خراب (exception) → fail-soft: alert + سقوط به مسیرِ موجودِ attribution (mint واقعی)."""
    from unittest.mock import MagicMock
    leg = MagicMock()
    leg.intake.side_effect = RuntimeError("leg broken")
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42, leg=leg)
    resp = ch.handle_command("/lead بازسازی | 500 | lead.doer")
    assert resp is not None and "ثبت شد" in resp, resp
    import re
    assert re.search(r"LEAD-\d{8}-\d{3}", resp), f"باید از مسیرِ attribution مینت شود: {resp}"
    import opslib
    assert "leg intake error" in opslib.ALERTS_MD.read_text(encoding="utf-8")


def t_lead_without_leg_unchanged():
    """leg=None → رفتارِ موجود byte-identical: mint از _attribution_propose."""
    ch = TC(token="FAKETOKEN123456", owner_chat_id=42)
    resp = ch.handle_command("/lead بازسازی | 700 | lead.doer")
    assert resp is not None and "ثبت شد" in resp, resp
    import re
    assert re.search(r"LEAD-\d{8}-\d{3}", resp), f"attribution_id مینت‌نشده: {resp}"


# ═══ رگرسیون: جریانِ پولِ app:* (SACRED — TINV-7) دست‌نخورده ═══════════════════

def t_money_app_flow_untouched():
    """approve واقعی → human-append (age_tick+1) → settle. عینِ الگویِ test_telegram_channel."""
    import chrono
    sys.path.insert(0, str(ENV["genome"] / "ledger"))
    from ledger import Ledger
    lg = Ledger(ENV["genome"] / "ledger" / f"rfc-{os.getpid()}-{id(object())}.jsonl")
    db = chrono.ChronoDB(ENV["ops"] / "state" / f"rfc-{os.getpid()}-{id(object())}.db")
    gate = chrono.EffectorGate(db, ledger=lg)
    try:
        effect_id = gate.request("PAY", "ref://bill-w3")
        ch = TC(token="FAKETOKEN123456", owner_chat_id=42,
                http_post=_fake_post_factory([]), gate=gate, ledger=lg,
                state_dir=str(ENV["ops"] / "state"))
        ch.request_approval_card(effect_id, 50.0, "قبضِ برق", "over-gate")
        token = ch._pending[effect_id]["token"]
        assert gate.settle(effect_id) is False, "نباید قبل از approve settle شود"
        assert lg.last_age_tick() == 0
        resp = ch.dispatch_callback(f"app:approve:{effect_id}:{token}")
        assert "تأیید شد" in resp, resp
        assert lg.last_age_tick() == 1, "human-append باید age_tick را +1 کند"
        row = db.q("SELECT status FROM gated_effect WHERE effect_id=?", (effect_id,))
        assert row and row[0][0] == "settled", f"effect باید settled باشد: {row}"
        a = ch.approval_for(effect_id, 50.0)
        assert a is not None and a.valid and a.source == "telegram", a
        # و replayِ پول همچنان رد
        r2 = ch.dispatch_callback(f"app:approve:{effect_id}:{token}")
        assert "رد" in r2, r2
    finally:
        db.close()


if __name__ == "__main__":
    failed = harness.run([
        ("[W-3] rfc_card → registry + callback_dataی ۴-تکهٔ توکن‌دار", t_rfc_card_registers_and_embeds_token),
        ("[W-3] خطای POST → False ولی intent می‌ماند", t_rfc_card_post_failure_keeps_intent),
        ("[W-3] merge happy-path → merge-approved + پاسخِ موفق", t_rfc_merge_happy_path),
        ("[W-3] توکنِ غلط → رد، status هنوز pending", t_rfc_wrong_token_rejected),
        ("[W-3] replay (merge دوم) → رد", t_rfc_replay_rejected),
        ("[W-3] deny → denied + «رد شد»", t_rfc_deny_path),
        ("[W-3] re-card هرگز verdictِ مصرف‌نشده را clobber نمی‌کند", t_rfc_recard_never_clobbers_unconsumed_verdict),
        ("[W-3] کارتِ قدیمیِ ۳-تکه → graceful، بدونِ crash", t_rfc_legacy_3part_graceful),
        ("[W-3] فعلِ ناشناخته → نادیده", t_rfc_unknown_verb_ignored),
        ("[W-3] pop_rfc_verdicts: exactly-once + sorted", t_pop_rfc_verdicts_exactly_once_sorted),
        ("[T-8] callbackِ مالک از poll_once به dispatch می‌رسد", t_poll_once_owner_callback_dispatched),
        ("[T-8] callbackِ غریبه dispatch نمی‌شود (allowlist)", t_poll_once_stranger_callback_not_dispatched),
        ("[Bug] structural: import opslib در سطحِ ماژول", t_opslib_imported_structural),
        ("[Bug] خطای dispatch در poll_once → alert، نه NameError", t_poll_once_dispatch_error_no_nameerror),
        ("[Bug] خطای answerCallbackQuery → False + alert", t_answer_callback_error_fail_soft),
        ("[W-3] /lead با legِ تزریقی → leg.intake + پاسخِ تأیید", t_lead_with_injected_leg),
        ("[W-3] legِ خراب → alert + سقوط به attribution", t_lead_broken_leg_falls_back),
        ("[W-3] leg=None → رفتارِ موجود دست‌نخورده", t_lead_without_leg_unchanged),
        ("[SACRED] جریانِ پولِ app:* دست‌نخورده (TINV-7)", t_money_app_flow_untouched),
    ])
    sys.exit(1 if failed else 0)
