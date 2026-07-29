#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cb_token_legmiss.py — گسترشِ توکنِ HMACِ callback (OCTOPUS_WIRE_CB_TOKEN) به verbهای
legacy (ok/no/later — کارتِ تصمیم) و mission (ms:approve/ms:reject) — D4، ITEM 1.

قرارداد (center.py + callback_token.py، همان طرحِ ap: — «طرحِ دوم» اختراع نمی‌شود):
- فلگ خاموش (پیش‌فرض) → ok/no/later و ms:approve/reject بایت‌به‌بایتِ امروز (بدونِ رد یا توکن).
- فلگ روشن → این verbها باید توکنِ HMACِ معتبر (<...>:<token>) داشته باشند؛ tokenlessِ قدیمی/
  جعلی/منقضی = رد (fail-closed، دقیقاً مثلِ ap:). راز از OCTOPUS_CB_SECRET؛ نبودِ راز = fail-closed.
- is_owner از handle_update *اول* است: غیرمالک هرگز به این handlerها نمی‌رسد (سکوتِ کامل).
- mint↔verify roundtrip: کارتِ رندرشده (پشتِ فلگ) توکن‌دار است و از درِ handler عبور می‌کند.
- 64-بایتِ callback_data؛ secret هرگز echo نمی‌شود.
$0 آفلاین؛ FakeClient؛ approval_store به sandbox پین می‌شود؛ صفر شبکه/تلگرام.
"""
import os
import sys
import time
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("cb-token-legmiss")
_OPS = harness.SELF_OPS         # کدِ زیرِ تست = درختِ خودِ تست (نه REAL_VAULT) — pin به worktree
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "outcomes"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import center                    # noqa: E402
import approval_store as aps     # noqa: E402
import callback_token as cbtok   # noqa: E402
import mission as mission_mod    # noqa: E402

# approval_store به sandbox — تستِ صف هرگز کنارِ repo نمی‌نویسد
_APS_TMP = Path(ENV["OPS_DIR"]) / "aps-sandbox"
_APS_TMP.mkdir(parents=True, exist_ok=True)
aps._APPROVALS_JSON = _APS_TMP / "approvals.json"
aps._AUDIT_PATH = _APS_TMP / "audit.log"
aps._LEGACY_DIR = _APS_TMP / "legacy-approvals"

_OWNER = 777
_SECRET_ENV = "OCTOPUS_CB_SECRET"
_TEST_SECRET = "unit-test-secret-not-real"     # مقدارِ مصنوعیِ تست — راز واقعی نیست


class FakeClient:
    def __init__(self, owner_id=_OWNER):
        self.owner_id = owner_id
        self.owner_chat_id = owner_id
        self.center_chat_id = None
        self.calls = []

    def wired(self):
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self.calls.append(("send", {"text": text, "keyboard": keyboard}))
        return 1

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"text": text, "keyboard": keyboard}))
        return True

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"text": text}))
        return True

    def texts(self):
        return [str(p.get("text", "")) for _k, p in self.calls]


def _center():
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0,
                      render_mod=types.SimpleNamespace(collect_feeds=lambda: {},
                                                       render_status=lambda f: "st",
                                                       scrub=lambda t: t))
    return c, fc


def _cb(data, uid=_OWNER, chat=_OWNER):
    return {"callback_query": {"id": "cb1", "from": {"id": uid},
                               "message": {"message_id": 100, "chat": {"id": chat}},
                               "data": data}}


def _flag_on(secret=_TEST_SECRET):
    os.environ[cbtok.FLAG] = "1"
    if secret is None:
        os.environ.pop(_SECRET_ENV, None)
    else:
        os.environ[_SECRET_ENV] = secret


def _clear():
    for k in (cbtok.FLAG, _SECRET_ENV):
        os.environ.pop(k, None)


# ── legacy ok/no/later ───────────────────────────────────────────────────────
def t_legacy_flag_off_parity():
    """فلگ خاموش → ok/no/later بدونِ توکن کار می‌کنند (verdict ثبت، صفر رد)."""
    _clear()
    for verb in ("ok", "no", "later"):
        c, fc = _center()
        r = c.handle_update(_cb(f"{verb}:dec-off-{verb}"))
        assert r and r.get("verdict") == verb and "rejected" not in r, r


def t_legacy_flag_on_missing_token_rejected():
    _flag_on()
    try:
        c, fc = _center()
        r = c.handle_update(_cb("ok:dec-mt"))          # tokenless
        assert r and r.get("rejected") == "bad-token" and r.get("verdict") is None, r
    finally:
        _clear()


def t_legacy_flag_on_forged_token_rejected():
    _flag_on()
    try:
        c, fc = _center()
        r = c.handle_update(_cb("ok:dec-forge:deadbeefdeadbeef0000"))
        assert r and r.get("rejected") == "bad-token", r
    finally:
        _clear()


def t_legacy_flag_on_valid_token_passes():
    _flag_on()
    try:
        c, fc = _center()
        tok = cbtok.mint("dec-ok", "ok", _OWNER, "", "")   # همان طرحِ _cb_mint (action_hash/expires="")
        assert tok, "با راز باید توکن ساخته شود"
        r = c.handle_update(_cb(f"ok:dec-ok:{tok}"))
        assert r and r.get("verdict") == "ok" and "rejected" not in r, r
        for t in fc.texts():
            assert _TEST_SECRET not in t, "secret هرگز echo نمی‌شود"
    finally:
        _clear()


def t_legacy_missing_secret_fail_closed():
    _flag_on(secret=None)
    try:
        c, fc = _center()
        r = c.handle_update(_cb("ok:dec-ns:anytokenatall"))
        assert r and r.get("rejected") == "bad-token", r
        assert cbtok.mint("dec-ns", "ok", _OWNER, "", "") == "", "بی‌راز نباید توکن ساخته شود"
        for t in fc.texts():
            assert _TEST_SECRET not in t
    finally:
        _clear()


# ── mission ms:approve / ms:reject ───────────────────────────────────────────
def _mk_mission():
    m = mission_mod.create_mission("تستِ توکنِ mission", source="telegram", mission_type="general")
    return m["id"]


def t_mission_flag_off_parity():
    """فلگ خاموش → ms:approve/reject بدونِ توکن کار می‌کنند."""
    _clear()
    for verb in ("approve", "reject"):
        mid = _mk_mission()
        c, fc = _center()
        r = c.handle_update(_cb(f"ms:{verb}:{mid}"))
        assert r and r.get("action") == verb and r.get("ok") and "rejected" not in r, r


def t_mission_flag_on_missing_token_rejected():
    _flag_on()
    try:
        mid = _mk_mission()
        c, fc = _center()
        r = c.handle_update(_cb(f"ms:approve:{mid}"))       # tokenless
        assert r and r.get("rejected") == "bad-token", r
        assert mission_mod.get(mid).get("owner_verdict") in (None, ), "رد نباید رأی ثبت کند"
    finally:
        _clear()


def t_mission_flag_on_forged_rejected():
    _flag_on()
    try:
        mid = _mk_mission()
        c, fc = _center()
        r = c.handle_update(_cb(f"ms:approve:{mid}:deadbeefdeadbeef0000"))
        assert r and r.get("rejected") == "bad-token", r
    finally:
        _clear()


def t_mission_flag_on_valid_passes():
    _flag_on()
    try:
        mid = _mk_mission()
        c, fc = _center()
        exp = str((mission_mod.get(mid) or {}).get("expires_epoch", ""))   # عملاً "" (missionِ نو)
        tok = cbtok.mint(mid, "approve", _OWNER, "", exp)
        assert tok
        r = c.handle_update(_cb(f"ms:approve:{mid}:{tok}"))
        assert r and r.get("action") == "approve" and r.get("ok") and "rejected" not in r, r
        for t in fc.texts():
            assert _TEST_SECRET not in t
    finally:
        _clear()


def t_mission_flag_on_expired_rejected():
    """missionِ دارای expires_epochِ گذشته → توکنِ HMACِ معتبر ولی منقضی → رد (مثلِ ap: t_k)."""
    _flag_on()
    _prev_get = mission_mod.get
    try:
        past = int(time.time()) - 10
        mission_mod.get = lambda _mid: {"id": _mid, "expires_epoch": past,
                                        "state": "created", "risk": "read"}
        mid = "M-EXPIRED-TEST-0001"
        c, fc = _center()
        tok = cbtok.mint(mid, "approve", _OWNER, "", str(past))   # HMAC معتبر روی expiresِ گذشته
        r = c.handle_update(_cb(f"ms:approve:{mid}:{tok}"))
        assert r and r.get("rejected") == "expired", r
    finally:
        mission_mod.get = _prev_get
        _clear()


def t_mission_missing_secret_fail_closed():
    _flag_on(secret=None)
    try:
        mid = _mk_mission()
        c, fc = _center()
        r = c.handle_update(_cb(f"ms:approve:{mid}:anytoken"))
        assert r and r.get("rejected") == "bad-token", r
    finally:
        _clear()


# ── is_owner *اول* است (defense-in-depth؛ گیتِ اصلی از from.id) ────────────────
def t_is_owner_gate_is_first():
    """غیرمالک با فلگِ روشن و توکنِ هرچقدر معتبر → handle_update = None (سکوتِ کامل، صفر اثر)."""
    _flag_on()
    try:
        mid = _mk_mission()
        c, fc = _center()
        tok = cbtok.mint(mid, "approve", _OWNER, "", "")     # حتی توکنِ درست
        assert c.handle_update(_cb(f"ms:approve:{mid}:{tok}", uid=666, chat=666)) is None
        assert fc.calls == [], f"غیرمالک = سکوتِ کامل: {fc.calls}"
        assert mission_mod.get(mid).get("owner_verdict") in (None, ), "غیرمالک نباید رأی بدهد"
    finally:
        _clear()


# ── mint↔verify roundtrip از مسیرِ رندر (کارتِ توکن‌دار از درِ handler عبور می‌کند) ──
def t_render_roundtrip_mission():
    """کارتِ mission پشتِ فلگ توکن می‌گیرد (_tok_kb) و همان callback_data از handler عبور می‌کند."""
    _flag_on()
    try:
        mid = _mk_mission()
        c, fc = _center()
        _txt, kb = mission_mod.mission_card(mid)
        kb = c._tok_kb(kb)                                   # همان چیزی که center قبل از send/edit می‌زند
        approve_cd = None
        for row in kb:
            for btn in row:
                cd = btn.get("callback_data", "")
                if cd.startswith(f"ms:approve:{mid}"):
                    approve_cd = cd
        assert approve_cd and approve_cd != f"ms:approve:{mid}", "کارت باید توکن‌دار شود"
        assert len(approve_cd.encode("utf-8")) <= 64, f"callback_data > 64B: {len(approve_cd)}"
        r = c.handle_update(_cb(approve_cd))
        assert r and r.get("action") == "approve" and r.get("ok") and "rejected" not in r, r
    finally:
        _clear()


def t_render_roundtrip_legacy():
    """کارتِ تصمیمِ legacy پشتِ فلگ توکن می‌گیرد و از درِ handler عبور می‌کند."""
    _flag_on()
    try:
        c, fc = _center()
        import render
        _txt, kb = render.render_decision({"id": "dec-roundtrip", "q": "تصمیم؟", "source": "sys"})
        kb = c._tok_kb(kb)
        ok_cd = None
        for row in kb:
            for btn in row:
                if btn.get("callback_data", "").startswith("ok:dec-roundtrip"):
                    ok_cd = btn["callback_data"]
        assert ok_cd and ok_cd != "ok:dec-roundtrip", "کارتِ legacy باید توکن‌دار شود"
        assert len(ok_cd.encode("utf-8")) <= 64
        r = c.handle_update(_cb(ok_cd))
        assert r and r.get("verdict") == "ok" and "rejected" not in r, r
    finally:
        _clear()


# ── flag_off render = بایت‌به‌بایت (بدونِ توکن) ────────────────────────────────
def t_flag_off_render_tokenless():
    _clear()
    c, fc = _center()
    mid = _mk_mission()
    _txt, kb = mission_mod.mission_card(mid)
    kb2 = c._tok_kb(kb)
    assert kb2 == kb, "فلگ خاموش → _tok_kb باید kb را بدونِ تغییر برگرداند"
    for row in kb2:
        for btn in row:
            cd = btn.get("callback_data", "")
            if cd.startswith("ms:approve") or cd.startswith("ms:reject"):
                assert cd.count(":") == 2, f"فلگ خاموش نباید توکن بچسباند: {cd}"


def t_a9_2_worst_case_callback_fits_64_bytes():
    """A9-2: بدترین حالتِ callback_data — jidِ ۴۸-کاراکتری (سقفِ render.py) + token —
    باید ≤۶۴B بماند. تست‌های roundtripِ بالا idِ کوتاه دارند و این سقف را لمس نمی‌کنند؛
    با _TOKEN_LEN=20 این ۷۵B می‌شد و تلگرام کلِ کارت را رد می‌کرد."""
    _flag_on()
    try:
        jid = "j" * 48                       # سقفِ jid در render (jid[:48])
        tok = cbtok.mint(jid, "ok", _OWNER, "", "")
        assert tok, "با راز باید توکن ساخته شود"
        worst = f"ap:ok:{jid}:{tok}"          # ap:ok:(۶)+jid(۴۸)+:(۱)+token
        assert len(worst.encode("utf-8")) <= 64, f"callback_data {len(worst)}B > 64B"
    finally:
        _clear()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} cb_token_legmiss: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
