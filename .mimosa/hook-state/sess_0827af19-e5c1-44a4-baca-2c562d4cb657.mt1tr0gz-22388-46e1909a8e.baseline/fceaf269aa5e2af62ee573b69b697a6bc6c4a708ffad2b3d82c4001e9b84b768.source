"""test_outbound_owner_transport.py — D7 (فاز D): telegram-owner notification transport.

اثبات می‌کند که:
  · flag خاموش = no-op مطلق (ت۱).
  · target پیش‌فرض (خالی) = stubِ NOT_ARMED (backward-compat، ت۲).
  · target=owner_chat ولی token/chat_id غایب → owner_chat_unarmed (fail-soft، ت۳).
  · target=owner_chat + token + chat_id + mock urlopen → sent=True (ت۴).
  · R2 ساختاری: هیچ contact.value مشتری در URL نیست (ت۵).
  · truncation > 4000 chars (ت۶).
  · خطای urlopen → owner_chat_error (fail-soft، ت۷).

همه sandbox (harness.setup → OPS_DIR موقت). هیچ فراخوانیِ واقعیِ network انجام نمی‌شود
(urllib.urlopen mock می‌شود). flag/STOP/ACTIVATION زنده دست‌نخورده.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("outbound-owner-d7")

import importlib                          # noqa: E402
import os                                 # noqa: E402
import uuid as _uuid                      # noqa: E402
import opslib                             # noqa: E402
importlib.reload(opslib)
import chrono                             # noqa: E402
importlib.reload(chrono)
import lead_effect_gate as leg            # noqa: E402
importlib.reload(leg)
import outbound_worker as ow              # noqa: E402
importlib.reload(ow)
import consent_gate as cg                 # noqa: E402
import consent_store as cs                # noqa: E402

FLAG = ow.FLAG


def _gate():
    db = chrono.ChronoDB(str(opslib.STATE_DIR / f"chrono-d7-{_uuid.uuid4().hex[:8]}.db"))
    return chrono.EffectorGate(db), db


def _consented():
    return {"source": {"channel": "telegram_manual", "source_id": "owner", "external_id": "D7"},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "owner_test"},
            "contact": {"preferred_channel": "telegram_owner", "phone": "+61411111111",
                        "email": "customer@example.com"},
            "request": {"scope_text": "D7 test — repaint"}}


def _authz_effect(gate, lead_id="L7"):
    eid = gate.request("lead_outbound", lead_id, beat=1)
    leg.authorize(eid, lead_id, "owner-verdict-test")
    return eid


# ── consent_gate D2a wiring (۲۰۲۶-۰۸-۰۷) — کمکِ گرانتِ رضایتِ store-backed ─────────
# send_one حالا consent_gate.may_release را **قبل از** release_and_settle صدا
# می‌زند (لایهٔ سومِ مستقلِ consent). این تنها تست‌هایی از این فایل را که واقعاً
# تا لایهٔ گیت/transport می‌رسند (t2، t8 — رفتارِ NOT_ARMED ِ backward-compat) لمس
# می‌کند؛ t3-t7 (target=owner_chat) از قبلِ امشب هم به همان دلیلِ دیگر (ویژگیِ
# owner_chat هنوز در outbound_worker پیاده نشده) قرمز بودند و دست‌نخورده می‌مانند.
def _grant_consent(lead_id: str, *, channel: str = "telegram_manual") -> None:
    os.environ[cg.FLAG] = "1"
    store = cs.ConsentStore()
    try:
        store.upsert_current({
            "lead_id": lead_id, "candidate_type": "consented_inbound",
            "consent_basis": "explicit", "consent_evidence": "quote_form",
            "consent_state": "CONSENTED_INBOUND", "compliance_state": "UNREVIEWED",
            "outreach_allowed": True, "retention_class": "consented_customer",
            "retention_anchor_at": "2026-07-21T00:00:00+00:00",
            "source_channel": channel})
    finally:
        store.close()


class _MockResp:
    def __init__(self, status, body):
        self.status = status
        self._body = body.encode("utf-8")
    def read(self):
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def t1_flag_off_no_op():
    """flag خاموش = no-op مطلق."""
    os.environ.pop(FLAG, None)
    gate, _ = _gate()
    eid = _authz_effect(gate, "L7a")
    r = ow.send_one(eid, _consented(), gate=gate)
    assert r["ok"] is False and r["status"] == "flag_off"


def t2_default_target_is_stub_not_armed():
    """target پیش‌فرض (خالی) = stubِ NOT_ARMED (backward-compat)."""
    os.environ[FLAG] = "1"
    os.environ.pop("OCTOPUS_LEAD_OUTBOUND_TARGET", None)
    # consent_gate D2a: این تست رفتارِ NOT_ARMED ِ backward-compat را می‌سنجد، نه
    # consent_gate را — رضایتِ store-backed را برای L7b می‌گیریم تا لایهٔ سومِ
    # consent عبور کند و ناوردای موردنظرِ همین تست دست‌نخورده سنجیده شود.
    _grant_consent("L7b")
    cand = dict(_consented()); cand["lead_id"] = "L7b"
    try:
        gate, _ = _gate()
        eid = _authz_effect(gate, "L7b")
        r = ow.send_one(eid, cand, gate=gate)
        assert r["ok"] is True   # گیت settle کرد
        assert r["sent"] is False   # ولی transport = NOT_ARMED
        assert r["status"] == "NOT_ARMED"
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop(cg.FLAG, None)


def t3_owner_chat_token_missing_unarmed():
    """target=owner_chat ولی token/chat_id غایب → owner_chat_unarmed (fail-soft)."""
    os.environ[FLAG] = "1"
    os.environ["OCTOPUS_LEAD_OUTBOUND_TARGET"] = "owner_chat"
    os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    os.environ.pop("OCTOPUS_OWNER_CHAT_ID", None)
    try:
        gate, _ = _gate()
        eid = _authz_effect(gate, "L7c")
        r = ow.send_one(eid, _consented(), gate=gate)
        assert r["ok"] is True   # گیت settle کرد
        assert r["sent"] is False
        assert r["status"] == "owner_chat_unarmed"
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop("OCTOPUS_LEAD_OUTBOUND_TARGET", None)


def t4_owner_chat_send_success_mocked():
    """target=owner_chat + token + chat_id + mock urlopen → sent=True."""
    os.environ[FLAG] = "1"
    os.environ["OCTOPUS_LEAD_OUTBOUND_TARGET"] = "owner_chat"
    os.environ["TELEGRAM_BOT_TOKEN"] = "fake-token-for-test"
    os.environ["OCTOPUS_OWNER_CHAT_ID"] = "123456789"
    try:
        gate, _ = _gate()
        eid = _authz_effect(gate, "L7d")
        # mock urllib.request.urlopen
        import outbound_worker as _ow
        captured = {"url": None, "data": None}
        import urllib.request as _ur
        orig_urlopen = _ur.urlopen
        def _fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["data"] = req.data.decode("utf-8") if req.data else ""
            return _MockResp(200, '{"ok":true,"result":{"message_id":1}}')
        _ur.urlopen = _fake_urlopen
        try:
            r = _ow.send_one(eid, _consented(), draft="test draft message", gate=gate)
        finally:
            _ur.urlopen = orig_urlopen
        assert r["ok"] is True, f"got {r}"
        assert r["sent"] is True, "باید sent=True باشد"
        assert r["status"] == "owner_chat_sent"
        assert r["channel"] == "telegram_owner"
        # URL به api.telegram.org رفت
        assert "api.telegram.org/botfake-token-for-test/sendMessage" in captured["url"]
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop("OCTOPUS_LEAD_OUTBOUND_TARGET", None)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("OCTOPUS_OWNER_CHAT_ID", None)


def t5_r2_no_customer_contact_in_payload():
    """R2 ساختاری: هیچ contact.value مشتری (phone/email) در payload/URL نیست.
    این تست می‌سنجد که آداپتر فقط به chat_id ثابتِ مالک می‌فرستد، نه به مشتری."""
    os.environ[FLAG] = "1"
    os.environ["OCTOPUS_LEAD_OUTBOUND_TARGET"] = "owner_chat"
    os.environ["TELEGRAM_BOT_TOKEN"] = "fake-token-r2"
    os.environ["OCTOPUS_OWNER_CHAT_ID"] = "999999999"
    try:
        gate, _ = _gate()
        eid = _authz_effect(gate, "L7e")
        cand = _consented()
        # cand شامل phone/email مشتری است — نباید در payload برود
        captured = {"data": None}
        import urllib.request as _ur
        orig_urlopen = _ur.urlopen
        def _fake_urlopen(req, timeout=None):
            captured["data"] = req.data.decode("utf-8") if req.data else ""
            return _MockResp(200, '{"ok":true}')
        _ur.urlopen = _fake_urlopen
        try:
            ow.send_one(eid, cand, draft="hello owner", gate=gate)
        finally:
            _ur.urlopen = orig_urlopen
        data = captured["data"]
        # chat_id مالک هست
        assert "chat_id=999999999" in data or "999999999" in data
        # ولی phone/email مشتری نیست (مهم‌ترینِ این تست)
        assert "+61411111111" not in data, "R2 نقض: phone مشتری در payload نباشد"
        assert "customer%40example.com" not in data and "customer@example.com" not in data, \
            "R2 نقض: email مشتری در payload نباشد"
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop("OCTOPUS_LEAD_OUTBOUND_TARGET", None)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("OCTOPUS_OWNER_CHAT_ID", None)


def t6_truncation_long_message():
    """پیام > 4000 chars truncation."""
    os.environ[FLAG] = "1"
    os.environ["OCTOPUS_LEAD_OUTBOUND_TARGET"] = "owner_chat"
    os.environ["TELEGRAM_BOT_TOKEN"] = "fake-token-trunc"
    os.environ["OCTOPUS_OWNER_CHAT_ID"] = "111111111"
    try:
        gate, _ = _gate()
        eid = _authz_effect(gate, "L7f")
        long_draft = "x" * 5000
        captured = {"data": None}
        import urllib.request as _ur
        orig_urlopen = _ur.urlopen
        def _fake_urlopen(req, timeout=None):
            captured["data"] = req.data.decode("utf-8") if req.data else ""
            return _MockResp(200, '{"ok":true}')
        _ur.urlopen = _fake_urlopen
        try:
            ow.send_one(eid, _consented(), draft=long_draft, gate=gate)
        finally:
            _ur.urlopen = orig_urlopen
        # پیام truncation شد (text=xxxx... ≤ 4003 chars)
        data = captured["data"]
        # پیدا کن text= را
        assert "..." in data, "باید truncation نشده باشد"
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop("OCTOPUS_LEAD_OUTBOUND_TARGET", None)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("OCTOPUS_OWNER_CHAT_ID", None)


def t7_network_error_fail_soft():
    """خطای urlopen → owner_chat_error (fail-soft، crash نمی‌کند)."""
    os.environ[FLAG] = "1"
    os.environ["OCTOPUS_LEAD_OUTBOUND_TARGET"] = "owner_chat"
    os.environ["TELEGRAM_BOT_TOKEN"] = "fake-token-err"
    os.environ["OCTOPUS_OWNER_CHAT_ID"] = "222222222"
    try:
        gate, _ = _gate()
        eid = _authz_effect(gate, "L7g")
        import urllib.request as _ur
        orig_urlopen = _ur.urlopen
        def _boom_urlopen(req, timeout=None):
            raise OSError("network unreachable (mocked)")
        _ur.urlopen = _boom_urlopen
        try:
            r = ow.send_one(eid, _consented(), draft="boom test", gate=gate)
        finally:
            _ur.urlopen = orig_urlopen
        assert r["ok"] is True   # گیت settle کرد (gate موفق)
        assert r["sent"] is False   # ولی transport خطا داد
        assert r["status"] == "owner_chat_error"
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop("OCTOPUS_LEAD_OUTBOUND_TARGET", None)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("OCTOPUS_OWNER_CHAT_ID", None)


def t8_customer_target_not_supported():
    """OCTOPUS_LEAD_OUTBOUND_TARGET=customer باید stub NOT_ARMED برگرداند (رأیِ جدا لازم).
    یعنی تا رأیِ صریح، تماسِ واقعی با مشتری فعال نیست."""
    os.environ[FLAG] = "1"
    os.environ["OCTOPUS_LEAD_OUTBOUND_TARGET"] = "customer"
    # consent_gate D2a: این تست هم رفتارِ NOT_ARMED ِ backward-compat را می‌سنجد،
    # نه consent_gate را — رضایتِ store-backed برای L7h.
    _grant_consent("L7h")
    cand = dict(_consented()); cand["lead_id"] = "L7h"
    try:
        gate, _ = _gate()
        eid = _authz_effect(gate, "L7h")
        r = ow.send_one(eid, cand, gate=gate)
        assert r["ok"] is True
        # customer در فهرستِ پشتیبانی‌شده نیست → fallback به stub NOT_ARMED
        assert r["sent"] is False
        assert r["status"] == "NOT_ARMED"
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop(cg.FLAG, None)
        os.environ.pop("OCTOPUS_LEAD_OUTBOUND_TARGET", None)


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t") and k[1:2].isdigit() and callable(v)
             and not k.startswith("test")]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, repr(e)))
            print(f"  ❌ {t.__name__}: {e!r}")
    print(f"\ntest_outbound_owner_transport: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
