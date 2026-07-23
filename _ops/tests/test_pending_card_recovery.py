#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pending_card_recovery.py — C7.1: بازسازیِ درستِ کارت‌های معلق بعد از restart.

این نسخه false-greenهای بازبینیِ مستقل (B1..B7) را می‌کشد و قراردادِ درست را اثبات می‌کند:
  * projection در **هر** بوت بازسازی می‌شود (نه فقط بوتِ اول) — B1.
  * کارتِ بازسازی‌شده دکمهٔ واقعیِ approve/deny/later دارد (رندرِ canonical) — B2.
  * مدلِ توکن صریح است: **B (stateless-valid)** — توکنِ پیش از restart همچنان کار می‌کند؛
    ضدِ replay در لایهٔ پول (approval_id تک‌مصرفه) — B3.
  * زیرِ HALT صفر ارسال/mark؛ بعد از resume ارسال می‌شود — B4.
  * markerِ SENT فقط پس از موفقیتِ ارسال؛ ارسالِ شکست‌خورده retryable — B5.
  * مبلغ از ردیفِ durableِ لحظهٔ ساخت (واقعی)؛ نامعلوم/tamper → fail-closed، صفر کارت — B6.
  * RFC: رأی پیش از restart durable می‌شود؛ مصرفِ durable (exactly-once) — B7.
$0 آفلاین؛ صفر شبکه/پول/settle واقعی؛ sandbox (http_post تزریق‌شده، gate=None).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("pending-card-recovery")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import pending_card_recovery as pcr  # noqa: E402
import approval_channel as ac  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))
_OWNER = 777
_SECRET = "unit-test-secret-not-real"


def _env():
    os.environ["OCTOPUS_WIRE_PROPOSAL_BUTTONS"] = "1"
    os.environ[pcr.SECRET_ENV] = _SECRET
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)


def _reset_store():
    for p in (pcr._store_path(_STATE), pcr._rfc_verdict_path(_STATE)):
        try:
            p.unlink()
        except OSError:
            pass
    import shutil
    try:
        shutil.rmtree(_STATE / "pulse" / "card-lease")
    except OSError:
        pass


class _Chan(ac.TelegramApprovalChannel):
    """کانالِ واقعی با http تزریق‌شده (صفر شبکه). ارسال‌ها ضبط می‌شوند؛ gate=None (صفر پول)."""

    def __init__(self, fail_send=False):
        self.sent = []
        self._fail = fail_send

        def _post(url, body, timeout_s=10.0):
            if self._fail:
                raise OSError("simulated telegram send failure")
            self.sent.append(body)
            return {"ok": True}

        super().__init__(token="unit-token", owner_chat_id=_OWNER, http_get=lambda *a, **k: {"ok": True},
                         http_post=_post, state_dir=str(_STATE))


def _last_keyboard(chan):
    for body in reversed(chan.sent):
        rm = body.get("reply_markup")
        if rm and rm.get("inline_keyboard"):
            return rm["inline_keyboard"]
    return None


def _status_pending(_eid):
    return "pending"


# ── ۱: projection در هر دو بوت بازسازی می‌شود (B1) + دکمهٔ واقعی (B2) ─────────────
def t_projection_every_boot_with_buttons():
    _env(); _reset_store()
    boot0 = _Chan()
    assert boot0.request_approval_card("fx-1", 12.5, "خریدِ X") is True
    # کارتِ اول ۳ دکمه دارد
    kb = _last_keyboard(boot0)
    verbs = [b["callback_data"].split(":")[1] for row in kb for b in row]
    assert verbs == ["approve", "deny", "later"], kb

    # restart 1: کانالِ تازه (RAM خالی) → بازسازی
    boot1 = _Chan()
    assert boot1._pending == {}
    r1 = pcr.rebuild_money_cards(channel=boot1, owner=_OWNER, state_dir=_STATE,
                                 status_fn=_status_pending, boot_id="b1")
    assert r1["rebuilt"] == 1, r1
    assert "fx-1" in boot1._pending, boot1._pending

    # restart 2: باز هم projection حاضر است (نه صفر!) — این همان false-greenِ B1 بود
    boot2 = _Chan()
    r2 = pcr.rebuild_money_cards(channel=boot2, owner=_OWNER, state_dir=_STATE,
                                 status_fn=_status_pending, boot_id="b2")
    assert r2["rebuilt"] == 1, f"projection باید در هر بوت بازسازی شود، نه فقط اولی: {r2}"
    assert "fx-1" in boot2._pending, boot2._pending


# ── ۲: بوتِ دوم spam نمی‌فرستد (delivery=SENT) ولی projection حاضر است ────────────
def t_no_duplicate_send_when_already_sent():
    _env(); _reset_store()
    boot0 = _Chan()
    boot0.request_approval_card("fx-2", 7.0, "قبض")
    # ثبتِ اولیه delivery=SENT است → بازسازی نباید دوباره بفرستد
    boot1 = _Chan()
    r1 = pcr.rebuild_money_cards(channel=boot1, owner=_OWNER, state_dir=_STATE,
                                 status_fn=_status_pending, boot_id="b1")
    assert r1["rebuilt"] == 1 and r1["sent"] == 0, f"delivery=SENT → صفر ارسالِ دوباره: {r1}"
    assert boot1.sent == [], "نباید کارتِ تکراری فرستاده شود (no-spam)"


# ── ۳: ارسالِ شکست‌خورده → delivery=PENDING → بوتِ بعدی retry ─────────────────────
def t_failed_send_retried_next_boot():
    _env(); _reset_store()
    # کارت را دستی با delivery=PENDING ثبت کن (شبیهِ ارسالِ ناموفقِ اولیه)
    pcr.record_money_card(state_dir=_STATE, effect_id="fx-3", amount_aud=9.0, content_hash="c",
                          action_kind="pay", target_ref="t", summary="s", owner=_OWNER,
                          token="tok-3", delivery="PENDING")
    boot1 = _Chan(fail_send=True)   # ارسال دوباره شکست می‌خورد
    r1 = pcr.rebuild_money_cards(channel=boot1, owner=_OWNER, state_dir=_STATE,
                                 status_fn=_status_pending, boot_id="b1")
    assert r1["rebuilt"] == 1 and r1["sent"] == 0, r1
    st = pcr._load_store(_STATE)[pcr._key("money", "fx-3")]["delivery"]
    assert st == "PENDING", f"ارسالِ شکست‌خورده باید PENDING (retryable) بماند: {st}"
    # بوتِ بعدی که ارسالش موفق است → SENT
    boot2 = _Chan(fail_send=False)
    r2 = pcr.rebuild_money_cards(channel=boot2, owner=_OWNER, state_dir=_STATE,
                                 status_fn=_status_pending, boot_id="b2")
    assert r2["sent"] == 1, r2
    assert pcr._load_store(_STATE)[pcr._key("money", "fx-3")]["delivery"] == "SENT"


# ── ۴: HALT → projection بله، ارسال نه، mark نه؛ resume → ارسال ───────────────────
def t_halt_reconstructs_but_never_sends_then_resume():
    _env(); _reset_store()
    pcr.record_money_card(state_dir=_STATE, effect_id="fx-4", amount_aud=4.0, content_hash="c",
                          action_kind="pay", target_ref="t", summary="s", owner=_OWNER,
                          token="tok-4", delivery="PENDING")
    halt_boot = _Chan()
    r = pcr.rebuild_money_cards(channel=halt_boot, owner=_OWNER, state_dir=_STATE,
                               status_fn=_status_pending, boot_id="bh", halted=True)
    assert r["rebuilt"] == 1 and r["sent"] == 0 and r["halted"] is True, r
    assert "fx-4" in halt_boot._pending, "زیرِ HALT projection باید بازسازی شود"
    assert halt_boot.sent == [], "زیرِ HALT هیچ کارتی ارسال نشود"
    assert pcr._load_store(_STATE)[pcr._key("money", "fx-4")]["delivery"] == "PENDING", \
        "HALT نباید دلیوری را SENT کند (فرصتِ دلیوری نباید سوخته شود — B4)"
    # resume (بدونِ HALT) → حالا ارسال می‌شود
    resume_boot = _Chan()
    r2 = pcr.rebuild_money_cards(channel=resume_boot, owner=_OWNER, state_dir=_STATE,
                                status_fn=_status_pending, boot_id="br")
    assert r2["sent"] == 1, f"بعد از resume باید ارسال شود: {r2}"


# ── ۵: مبلغِ نامعلوم/tamper → fail-closed (هیچ کارت) — B6 ─────────────────────────
def t_unknown_amount_and_tamper_fail_closed():
    _env(); _reset_store()
    # (الف) مبلغِ نامعلوم: ردیفِ دستی بدونِ integrity معتبر و amount=0
    store = pcr._load_store(_STATE)
    store[pcr._key("money", "fx-bad")] = {"kind": "money", "effect_id": "fx-bad", "owner": _OWNER,
                                          "amount_aud": 0.0, "token": "t", "delivery": "PENDING",
                                          "expires_at": pcr._now() + 1000, "integrity": None}
    pcr._save_store(_STATE, store)
    boot = _Chan()
    r = pcr.rebuild_money_cards(channel=boot, owner=_OWNER, state_dir=_STATE,
                               status_fn=_status_pending, boot_id="b")
    assert r["rebuilt"] == 0 and r["skipped_unknown_amount"] == 1, r
    assert "fx-bad" not in boot._pending, "کارتِ بی‌مبلغ هرگز قابلِ‌کلیک ساخته نشود"

    # (ب) tamper: مبلغِ ردیف را بعد از ثبتِ integrity عوض کن → تگ نمی‌خواند → fail-closed
    _reset_store()
    pcr.record_money_card(state_dir=_STATE, effect_id="fx-tam", amount_aud=5.0, content_hash="c",
                          action_kind="pay", target_ref="t", summary="s", owner=_OWNER,
                          token="tk", delivery="PENDING")
    st = pcr._load_store(_STATE)
    st[pcr._key("money", "fx-tam")]["amount_aud"] = 5000.0   # دستکاریِ مبلغ
    pcr._save_store(_STATE, st)
    boot2 = _Chan()
    r2 = pcr.rebuild_money_cards(channel=boot2, owner=_OWNER, state_dir=_STATE,
                                status_fn=_status_pending, boot_id="b2")
    assert r2["rebuilt"] == 0 and r2["skipped_unknown_amount"] == 1, f"tamper باید fail-closed: {r2}"


# ── ۶: مدل B — توکنِ پیش از restart بازگردانده می‌شود و دکمهٔ مالک هنوز کار می‌کند ─
def t_model_b_pre_restart_token_still_valid():
    _env(); _reset_store()
    boot0 = _Chan()
    boot0.request_approval_card("fx-6", 6.0, "s")
    pre_token = boot0._pending["fx-6"]["token"]
    # restart
    boot1 = _Chan()
    pcr.rebuild_money_cards(channel=boot1, owner=_OWNER, state_dir=_STATE,
                            status_fn=_status_pending, boot_id="b1")
    assert boot1._pending["fx-6"]["token"] == pre_token, "مدل B: همان توکن باید بازگردد"
    # توکنِ جعلی رد می‌شود (در حالِ pending — پیش از هر تصمیم)
    assert "نامنطبق" in boot1.dispatch_callback("app:approve:fx-6:WRONGTOKEN")
    # دکمهٔ پیش از restart (همان توکن) هنوز پذیرفته می‌شود (status=pending، token منطبق)
    reply = boot1.dispatch_callback(f"app:deny:fx-6:{pre_token}")
    assert "رد شد" in reply, f"توکنِ پیش از restart باید معتبر بماند: {reply}"


# ── ۷: integrity tag — card-swap/wrong-owner/expired رد ─────────────────────────
def t_integrity_tag_binding_checks():
    _env()
    exp = pcr._now() + 100000
    tag = pcr.mint_money_token(effect_id="fx-1", content_hash="ch1", action_kind="pay",
                               target_ref="tgt1", amount=12.5, owner=_OWNER, exp=exp)
    assert pcr.verify_money_token(tag, effect_id="fx-1", content_hash="ch1", action_kind="pay",
                                  target_ref="tgt1", amount=12.5, owner=_OWNER)[0]
    # effect دیگر / مبلغِ دیگر / binding دیگر / owner دیگر → reject
    for kw in ({"effect_id": "fx-2"}, {"amount": 99.9}, {"content_hash": "EVIL"}, {"owner": 999}):
        base = dict(effect_id="fx-1", content_hash="ch1", action_kind="pay",
                    target_ref="tgt1", amount=12.5, owner=_OWNER)
        base.update(kw)
        assert not pcr.verify_money_token(tag, **base)[0], f"باید reject شود: {kw}"
    # expired
    old = pcr.mint_money_token(effect_id="fx-1", content_hash="ch1", action_kind="pay",
                               target_ref="tgt1", amount=12.5, owner=_OWNER, exp=pcr._now() - 10)
    assert pcr.verify_money_token(old, effect_id="fx-1", content_hash="ch1", action_kind="pay",
                                  target_ref="tgt1", amount=12.5, owner=_OWNER)[1] == "expired"


# ── ۸: terminal/EXECUTING/RECONCILE هرگز re-present نمی‌شوند (cross-check) ─────────
def t_terminal_and_inflight_skipped():
    _env(); _reset_store()
    for eid, st in (("s", "settled"), ("x", "EXECUTING"), ("r", "RECONCILE_REQUIRED"),
                    ("f", "refused")):
        pcr.record_money_card(state_dir=_STATE, effect_id=eid, amount_aud=1.0, content_hash="c",
                              action_kind="pay", target_ref="t", summary="s", owner=_OWNER,
                              token=f"tok-{eid}", delivery="PENDING")
    statuses = {"s": "settled", "x": "EXECUTING", "r": "RECONCILE_REQUIRED", "f": "refused"}
    boot = _Chan()
    r = pcr.rebuild_money_cards(channel=boot, owner=_OWNER, state_dir=_STATE,
                               status_fn=lambda e: statuses.get(e), boot_id="b")
    assert r["rebuilt"] == 0 and boot._pending == {}, f"terminal/in-flight هرگز re-present: {r}"
    assert r["skipped_terminal"] == 4, r


# ── ۹: concurrent recovery lease — فقط یک بوت می‌فرستد ───────────────────────────
def t_concurrent_send_lease():
    _env(); _reset_store()
    assert pcr._acquire_send_lease(_STATE, "money", "fx-9", "bootA") is True
    assert pcr._acquire_send_lease(_STATE, "money", "fx-9", "bootB") is False, \
        "بوتِ دوم نباید lease بگیرد (ضدِ ارسالِ دوگانه)"
    pcr.release_send_lease(_STATE, "money", "fx-9")
    assert pcr._acquire_send_lease(_STATE, "money", "fx-9", "bootB") is True, \
        "بعد از release باید دوباره claim شود"


# ── ۱۰: RFC submitted ربیلد؛ decided/consumed نه ─────────────────────────────────
def t_rfc_submitted_rebuilt_decided_not():
    _env(); _reset_store()
    rf = _STATE / "rfcs-a.json"
    rf.write_text(json.dumps({"rfcs": [{"rfc_id": "RFC-S", "status": "submitted",
                                        "bottleneck": "slow"},
                                       {"rfc_id": "RFC-M", "status": "human-merge"}]}), "utf-8")
    boot = _Chan()
    r = pcr.rebuild_rfc_cards(channel=boot, rfcs_path=rf, state_dir=_STATE)
    assert r["rebuilt"] == 1 and "RFC-S" in boot._pending_rfc, (r, list(boot._pending_rfc))
    assert "RFC-M" not in boot._pending_rfc, "decided نباید rebuild شود"


# ── ۱۱: RFC click → crash قبل از مصرفِ doctor → رأی زنده می‌ماند (reinject، exactly-once) ─
def t_rfc_verdict_survives_crash_before_consume():
    _env(); _reset_store()
    rf = _STATE / "rfcs-b.json"
    rf.write_text(json.dumps({"rfcs": [{"rfc_id": "RFC-1", "status": "submitted",
                                        "bottleneck": "x"}]}), "utf-8")
    boot0 = _Chan()
    boot0.rfc_card("RFC-1", "x")
    tok = boot0._pending_rfc["RFC-1"]["token"]
    # مالک کلیک می‌کند (merge) → رأی durable می‌شود
    boot0.dispatch_callback(f"rfc:merge:RFC-1:{tok}")
    assert pcr.load_rfc_verdicts(_STATE)["RFC-1"]["verdict"] == "merge-approved"
    # crash قبل از مصرف. restart: رأیِ مصرف‌نشده باید reinject شود تا doctor یک‌بار بگیرد
    boot1 = _Chan()
    r = pcr.rebuild_rfc_cards(channel=boot1, rfcs_path=rf, state_dir=_STATE)
    assert r["reinjected_verdicts"] == 1, r
    popped = boot1.pop_rfc_verdicts()
    assert popped == [("RFC-1", "merge-approved")], f"رأی باید دقیقاً یک‌بار تحویل شود: {popped}"
    # doctor مصرف کرد → durable consumed. restart دوباره → دیگر تحویل نمی‌شود
    boot2 = _Chan()
    r2 = pcr.rebuild_rfc_cards(channel=boot2, rfcs_path=rf, state_dir=_STATE)
    assert r2["reinjected_verdicts"] == 0, f"رأیِ مصرف‌شده نباید دوباره reinject شود: {r2}"
    assert boot2.pop_rfc_verdicts() == [], "مصرفِ durable → صفر تحویلِ دوباره (exactly-once)"


# ── ۱۲: doctor consume → crash → durable consumed → no duplicate ─────────────────
def t_rfc_consume_then_crash_no_duplicate():
    _env(); _reset_store()
    pcr.persist_rfc_verdict(state_dir=_STATE, rfc_id="RFC-2", verdict="denied")
    pcr.mark_rfc_consumed(state_dir=_STATE, rfc_id="RFC-2")
    v = pcr.load_rfc_verdicts(_STATE)["RFC-2"]
    assert v["verdict"] == "denied" and v["consumed"] is True
    rf = _STATE / "rfcs-c.json"
    rf.write_text(json.dumps({"rfcs": [{"rfc_id": "RFC-2", "status": "submitted"}]}), "utf-8")
    boot = _Chan()
    r = pcr.rebuild_rfc_cards(channel=boot, rfcs_path=rf, state_dir=_STATE)
    assert r["reinjected_verdicts"] == 0 and r["rebuilt"] == 0, \
        f"RFCِ رأی‌خورده+مصرف‌شده نه reinject نه rebuild: {r}"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱] projection هر بوت + دکمهٔ واقعی (B1/B2)", t_projection_every_boot_with_buttons),
        ("[۲] no-spam وقتی SENT (B1)", t_no_duplicate_send_when_already_sent),
        ("[۳] ارسالِ شکست‌خورده retry (B5)", t_failed_send_retried_next_boot),
        ("[۴] HALT بازسازی-نه-ارسال، resume ارسال (B4)", t_halt_reconstructs_but_never_sends_then_resume),
        ("[۵] مبلغِ نامعلوم/tamper fail-closed (B6)", t_unknown_amount_and_tamper_fail_closed),
        ("[۶] مدل B — توکنِ پیش از restart معتبر (B3)", t_model_b_pre_restart_token_still_valid),
        ("[۷] integrity tag binding checks", t_integrity_tag_binding_checks),
        ("[۸] terminal/in-flight cross-check skip", t_terminal_and_inflight_skipped),
        ("[۹] concurrent send lease", t_concurrent_send_lease),
        ("[۱۰] RFC submitted rebuild، decided نه", t_rfc_submitted_rebuilt_decided_not),
        ("[۱۱] RFC رأی زنده می‌ماند + exactly-once (B7)", t_rfc_verdict_survives_crash_before_consume),
        ("[۱۲] RFC consume→crash→no-dup (B7)", t_rfc_consume_then_crash_no_duplicate),
    ])
    sys.exit(1 if failed else 0)
