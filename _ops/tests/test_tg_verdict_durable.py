#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_verdict_durable.py — رأیِ احرازشدهٔ مالک از handlerِ واقعیِ تلگرام → OutcomeStoreِ
پایدار (Wave1-A، Part2). همهٔ سناریوها از درِ واقعی: center.handle_update با updateهای مصنوعی.

پوشش (لیستِ اجباریِ brief):
  (a) flag-off parity: بدونِ OCTOPUS_WIRE_VERDICT_OUTCOME صفر نوشتِ durable — رفتارِ امروز.
  (b) غیرمالک: سکوتِ کامل — صفر state-change، صفر durable، صفر پاسخ.
  (c) مالک ok → accepted-measurement پایدار (linkage: proposal/mission/corr/source).
  (d) رد و تعویق: no → rejected؛ later (کارتِ تصمیم) → deferred — هر دو پایدار.
  (e) دو-تپ/duplicate: transitionِ single-use + idempotency → فقط یک رویداد.
  (f) کارتِ نامعتبر/legacy (tokenless یا توکنِ جعلی) با فلگِ توکن روشن → رد.
  (g) secret ِ غایب با فلگِ توکن روشن → fail-closed، بدونِ افشای هیچ مقدار.
  (h) توکنِ معتبر → کلِ مسیر (mint→callback→durable)؛ secret هرگز echo نمی‌شود.
  (i) restart/reopen replay: رأی می‌ماند؛ replay بعد از «restart» رویدادِ نو نمی‌سازد.
  (j) هیچ استنتاجی: نه approval-رسمی، نه delivered/settled/failed/verified، نه revenue.
  (k) شکستِ تحویلِ fake: نه delivered، نه seen — کارت برای ضربانِ بعد زنده می‌ماند.
  (l) رأیِ کارتِ mission (ms:approve/reject) هم پایدار می‌شود.
  (m) ساختاری: مسیرِ durable در center صفر settle/effector/شبکه.
$0 آفلاین؛ FakeClient؛ approval_store به temp پین می‌شود؛ صفر شبکه/تلگرام.
"""
import ast
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("tg-verdict-durable")
_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "outcomes"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                    # noqa: E402
import center                    # noqa: E402
import approval_store as aps     # noqa: E402  (همان module object ِ داخلِ center)
import callback_token as cbtok   # noqa: E402
import mission as mission_mod    # noqa: E402
import outcome_store as osx      # noqa: E402
import verdict_recorder as vr    # noqa: E402

# approval_store به sandbox پین می‌شود — تستِ صف هرگز کنارِ repo نمی‌نویسد
_APS_TMP = Path(ENV["OPS_DIR"]) / "aps-sandbox"
_APS_TMP.mkdir(parents=True, exist_ok=True)
aps._APPROVALS_JSON = _APS_TMP / "approvals.json"
aps._AUDIT_PATH = _APS_TMP / "audit.log"
aps._LEGACY_DIR = _APS_TMP / "legacy-approvals"

_DB = opslib.STATE_DIR / "outcomes" / "outcomes.db"
_OWNER = 777
_SECRET_ENV = "OCTOPUS_CB_SECRET"
_TEST_SECRET = "unit-test-secret-not-real"   # مقدارِ مصنوعیِ تست — secret واقعی نیست


class FakeClient:
    """کلاینتِ fake با قراردادِ TgClient — صفر شبکه. شکستِ send قابلِ تزریق."""

    def __init__(self, owner_id=_OWNER, fail_send=False):
        self.owner_id = owner_id
        self.owner_chat_id = owner_id
        self.center_chat_id = None
        self.fail_send = fail_send
        self.calls = []
        self._mid = 100

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self.calls.append(("send", {"text": text, "keyboard": keyboard}))
        if self.fail_send:
            return None                      # تحویلِ شکست‌خورده (fake)
        self._mid += 1
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def texts(self):
        return [str(p.get("text", "")) for _k, p in self.calls]


def _center(fail_send=False):
    fc = FakeClient(fail_send=fail_send)
    c = center.Center(client=fc, clock=lambda: 1000.0,
                      render_mod=types.SimpleNamespace(collect_feeds=lambda: {},
                                                       render_status=lambda f: "st",
                                                       scrub=lambda t: t))
    return c, fc


def _cb(data, uid=_OWNER, chat=_OWNER):
    return {"callback_query": {"id": "cb1", "from": {"id": uid},
                               "message": {"message_id": 100, "chat": {"id": chat}},
                               "data": data}}


def _rows(pid):
    if not _DB.exists():
        return []
    o = osx.OutcomeStore(path=_DB)
    try:
        return o.events(proposal_id=pid)
    finally:
        o.close()


def _all_rows():
    if not _DB.exists():
        return []
    o = osx.OutcomeStore(path=_DB)
    try:
        return o.events()
    finally:
        o.close()


def _clear_flags():
    for k in (vr.FLAG, cbtok.FLAG, _SECRET_ENV, "OCTOPUS_WIRE_MENU_V2"):
        os.environ.pop(k, None)


# ── (a) اول از همه: flag-off parity (قبل از این‌که هیچ تستی db بسازد) ──────────────
def t_a_flag_off_parity_no_durable_write():
    _clear_flags()
    jid = aps.add_pending({"id": "job-off", "type": "task", "title": "t", "risk": "read"})
    c, fc = _center()
    r = c.handle_update(_cb(f"ap:ok:{jid}"))
    assert r and r.get("ok") is True and r.get("verdict") == "ok", r
    assert not _DB.exists(), "flag خاموش نباید outcomes.db بسازد (parity بایت‌به‌بایت)"
    # مسیرِ قدیمی همانِ امروز: verdict فایل legacy دارد
    assert (aps._LEGACY_DIR / f"{jid}.json").exists(), "legacy verdict باید مثل امروز ثبت شود"
    # کارتِ تصمیمِ legacy هم با flag خاموش durable نمی‌نویسد
    c.handle_update(_cb("ok:dec-off"))
    assert not _DB.exists(), "verdictِ کارتِ تصمیم هم با flag خاموش نباید durable بنویسد"


# ── (b) غیرمالک: سکوت + صفر اثر ─────────────────────────────────────────────────
def t_b_nonowner_rejected_zero_effect():
    os.environ[vr.FLAG] = "1"
    try:
        jid = aps.add_pending({"id": "job-stranger", "type": "task", "title": "t", "risk": "read"})
        c, fc = _center()
        assert c.handle_update(_cb(f"ap:ok:{jid}", uid=666, chat=666)) is None
        assert fc.calls == [], f"غیرمالک = سکوتِ کامل: {fc.calls}"
        job = aps.get(jid)
        assert job and job.get("status") == "pending", "غیرمالک نباید state را عوض کند"
        assert _rows(jid) == [], "غیرمالک نباید رویدادِ durable بسازد"
    finally:
        _clear_flags()


# ── (c) مالک ok → accepted-measurement + linkage ─────────────────────────────────
def t_c_owner_ok_accepted_measurement_linkage():
    os.environ[vr.FLAG] = "1"
    try:
        jid = aps.add_pending({"id": "job-acc", "type": "mission", "title": "t", "risk": "medium"})
        c, fc = _center()
        r = c.handle_update(_cb(f"ap:ok:{jid}"))
        assert r and r.get("ok") is True, r
        rows = _rows(jid)
        assert len(rows) == 1, rows
        ev = rows[0]
        assert ev["event_type"] == "accepted-measurement", ev
        assert ev["verdict"] == "measurement", ev            # هرگز approval/settled
        assert ev["proposal_id"] == jid, ev
        assert ev["mission_id"] == jid, "type=mission → mission_id حفظ می‌شود"
        assert ev["correlation_id"] == f"prop_{jid}", ev
        assert float(ev["value_aud_claimed"] or 0.0) == 0.0, "صفِ تأیید مبلغ ندارد — صفر CLAIM"
        assert '"source": "tg-center"' in ev["payload_json"] or '"tg-center"' in ev["payload_json"], ev
    finally:
        _clear_flags()


# ── (d) rejected و deferred پایدار می‌شوند ────────────────────────────────────────
def t_d_rejected_and_deferred_persist():
    os.environ[vr.FLAG] = "1"
    try:
        jid = aps.add_pending({"id": "job-rej", "type": "task", "title": "t", "risk": "read"})
        c, fc = _center()
        r = c.handle_update(_cb(f"ap:no:{jid}"))
        assert r and r.get("ok") is True, r
        rows = _rows(jid)
        assert len(rows) == 1 and rows[0]["event_type"] == "rejected", rows
        # کارتِ تصمیمِ legacy: «بعداً» = تعویق — must persist as deferred
        r2 = c.handle_update(_cb("later:dec-defer"))
        assert r2 and r2.get("verdict") == "later", r2
        rows2 = _rows("dec-defer")
        assert len(rows2) == 1 and rows2[0]["event_type"] == "deferred", rows2
    finally:
        _clear_flags()


# ── (e) duplicate/دو-تپ suppressed ──────────────────────────────────────────────
def t_e_duplicate_callback_suppressed():
    os.environ[vr.FLAG] = "1"
    try:
        jid = aps.add_pending({"id": "job-dup", "type": "task", "title": "t", "risk": "read"})
        c, fc = _center()
        r1 = c.handle_update(_cb(f"ap:ok:{jid}"))
        r2 = c.handle_update(_cb(f"ap:ok:{jid}"))          # replay/دو-تپ
        assert r1.get("ok") is True and r2.get("ok") is False, (r1, r2)
        assert len(_rows(jid)) == 1, "single-use + idempotency → دقیقاً یک رویداد"
        # کارتِ تصمیمِ legacy هم: همان رأی دوبار → یک رویداد (idempotency ِ store)
        c.handle_update(_cb("ok:dec-dup"))
        c.handle_update(_cb("ok:dec-dup"))
        accs = [e for e in _rows("dec-dup") if e["event_type"] == "accepted-measurement"]
        assert len(accs) == 1, accs
    finally:
        _clear_flags()


# ── (f) کارتِ نامعتبر/legacy با فلگِ توکن روشن → رد ──────────────────────────────
def t_f_invalid_or_legacy_card_rejected():
    os.environ[vr.FLAG] = "1"
    os.environ[cbtok.FLAG] = "1"
    os.environ[_SECRET_ENV] = _TEST_SECRET
    try:
        jid = aps.add_pending({"id": "job-tok", "type": "task", "title": "t", "risk": "read"})
        c, fc = _center()
        # کارتِ legacy ِ tokenless
        r1 = c.handle_update(_cb(f"ap:ok:{jid}"))
        assert r1 and r1.get("rejected") == "bad-token", r1
        # توکنِ جعلی/دستکاری‌شده
        r2 = c.handle_update(_cb(f"ap:ok:{jid}:deadbeefdeadbeef"))
        assert r2 and r2.get("rejected") == "bad-token", r2
        job = aps.get(jid)
        assert job and job.get("status") == "pending", "کارتِ نامعتبر نباید state عوض کند"
        assert _rows(jid) == [], "کارتِ نامعتبر نباید رویدادِ durable بسازد"
        for t in fc.texts():
            assert _TEST_SECRET not in t, "secret هرگز echo نمی‌شود"
    finally:
        _clear_flags()


# ── (g) secret ِ غایب → fail-closed بدونِ افشا ────────────────────────────────────
def t_g_missing_secret_fail_closed():
    os.environ[vr.FLAG] = "1"
    os.environ[cbtok.FLAG] = "1"
    os.environ.pop(_SECRET_ENV, None)                      # secret عمداً غایب
    try:
        jid = aps.add_pending({"id": "job-nosecret", "type": "task", "title": "t", "risk": "read"})
        c, fc = _center()
        r = c.handle_update(_cb(f"ap:ok:{jid}:anytokenatall"))
        assert r and r.get("rejected") == "bad-token", r   # هیچ توکنی بی‌secret معتبر نیست
        job = aps.get(jid)
        assert job and job.get("status") == "pending", "fail-closed: صفر state-change"
        assert _rows(jid) == [], "fail-closed: صفر durable"
        # کارت‌های صفِ تأیید هم بی‌secret توکن نمی‌گیرند (mint="")
        assert cbtok.mint(jid, "ok", _OWNER, "h", "e") == "", "بی‌secret نباید توکن ساخته شود"
    finally:
        _clear_flags()


# ── (h) توکنِ معتبر → کلِ مسیر؛ صفر echo ِ secret ─────────────────────────────────
def t_h_valid_token_full_path():
    os.environ[vr.FLAG] = "1"
    os.environ[cbtok.FLAG] = "1"
    os.environ[_SECRET_ENV] = _TEST_SECRET
    try:
        jid = aps.add_pending({"id": "job-sec", "type": "mission", "title": "t", "risk": "medium"})
        job = aps.get(jid)
        c, fc = _center()
        ah = c._ap_action_hash("ok", jid, job)
        tok = cbtok.mint(jid, "ok", _OWNER, ah, str(job.get("expires_epoch", "")))
        assert tok, "با secret باید توکن mint شود"
        r = c.handle_update(_cb(f"ap:ok:{jid}:{tok}"))
        assert r and r.get("ok") is True, r
        rows = _rows(jid)
        assert len(rows) == 1 and rows[0]["event_type"] == "accepted-measurement", rows
        for t in fc.texts():
            assert _TEST_SECRET not in t, "secret هرگز echo نمی‌شود"
    finally:
        _clear_flags()


# ── (i) restart/reopen replay ───────────────────────────────────────────────────
def t_i_restart_reopen_replay():
    os.environ[vr.FLAG] = "1"
    try:
        jid = aps.add_pending({"id": "job-restart", "type": "task", "title": "t", "risk": "read"})
        c1, _ = _center()
        assert c1.handle_update(_cb(f"ap:ok:{jid}")).get("ok") is True
        assert len(_rows(jid)) == 1
        # «restart»: instanceِ نو (state روی دیسک) + replay ِ همان callback
        c2, _ = _center()
        r2 = c2.handle_update(_cb(f"ap:ok:{jid}"))
        assert r2.get("ok") is False, "بعد از restart هم replay نباید دوباره تصمیم بگیرد"
        rows = _rows(jid)                                   # reopen ِ store = restart ِ سوم
        assert len(rows) == 1 and rows[0]["event_type"] == "accepted-measurement", rows
        # کارتِ تصمیمِ legacy هم پس از restart replay-safe است (idempotency ِ کلید)
        c1.handle_update(_cb("ok:dec-restart"))
        c2.handle_update(_cb("ok:dec-restart"))
        accs = [e for e in _rows("dec-restart") if e["event_type"] == "accepted-measurement"]
        assert len(accs) == 1, accs
    finally:
        _clear_flags()


# ── (j) صفر استنتاج: نه delivery، نه settle، نه revenue ──────────────────────────
def t_j_no_approval_delivery_revenue_inference():
    rows = _all_rows()
    assert rows, "تا این‌جا باید رویدادِ durable ثبت شده باشد"
    allowed = {"accepted-measurement", "rejected", "deferred"}
    for ev in rows:
        assert ev["event_type"] in allowed, f"استنتاجِ ممنوع: {ev}"
        assert ev["verdict"] == "measurement", ev
        assert "settled" not in str(ev["payload_json"]), ev
    o = osx.OutcomeStore(path=_DB)
    try:
        m = o.metrics()
    finally:
        o.close()
    assert m["delivered"] == 0 and m["failed"] == 0, m
    assert m["confirmed_revenue_aud"] == 0.0, "رأی هرگز درآمد نمی‌سازد"
    assert m["value_aud_claimed"] == 0.0, "مسیرِ center مبلغ ندارد — صفر CLAIM"


# ── (k) شکستِ تحویلِ fake → نه delivered، نه seen ────────────────────────────────
def t_k_failed_fake_delivery_never_delivered_or_seen():
    os.environ[vr.FLAG] = "1"
    try:
        n_before = len(_all_rows())
        rmod = types.SimpleNamespace(
            collect_feeds=lambda: {"guidance": {"items": [
                {"id": "dec-fail", "q": "تصمیم؟", "source": "sys"}]}},
            render_status=lambda f: "",
            render_decision=lambda it: ("کارت", [[{"text": "آره",
                                                   "callback_data": f"ok:{it['id']}"}]]),
        )
        fc = FakeClient(fail_send=True)                     # تحویل شکست می‌خورد
        c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=rmod)
        out = c.beat()
        assert out["decisions"] == 0, f"تحویلِ شکست‌خورده نباید decision بشمارد: {out}"
        cfg = center._load_config()
        assert "dec-fail" not in (cfg.get("seen") or []), \
            "تحویلِ شکست‌خورده نباید seen شود — کارت باید در ضربانِ بعد دوباره برود"
        assert len(_all_rows()) == n_before, "شکستِ تحویل نباید هیچ رویدادِ durable بسازد"
        assert _rows("dec-fail") == [], "نه delivered، نه هیچ رویدادی برای کارتِ نرفته"
    finally:
        _clear_flags()


# ── (l) رأیِ کارتِ mission هم پایدار می‌شود ──────────────────────────────────────
def t_l_mission_card_verdict_durable():
    os.environ[vr.FLAG] = "1"
    try:
        m = mission_mod.create_mission("تستِ ثبتِ رأی", source="telegram", mission_type="code")
        mid = m["id"]
        c, fc = _center()
        r = c.handle_update(_cb(f"ms:approve:{mid}"))
        assert r and r.get("action") == "approve" and r.get("ok"), r
        rows = _rows(mid)
        assert len(rows) == 1 and rows[0]["event_type"] == "accepted-measurement", rows
        assert rows[0]["mission_id"] == mid, "mission_id باید حفظ شود"
    finally:
        _clear_flags()


# ── (m) ساختاری: صفر settle/effector/شبکه در مسیرِ durable ِ center ───────────────
def t_m_structural_no_effector_no_network():
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_durable_verdict_outcome"), None)
    assert fn is not None, "مسیرِ durable باید وجود داشته باشد"
    called, imported = set(), set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            called.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
    forbidden = {"settle", "approve", "_do_approve", "pay", "mark_paid", "post_journal",
                 "send", "send_message", "sendMessage", "EffectorGate"}
    assert not (called & forbidden), f"مسیرِ durable صدا می‌زند: {called & forbidden}"
    assert "record_owner_verdict" in called, "باید واقعاً به verdict_recorder وصل باشد"
    assert not (imported & {"urllib", "http", "socket", "requests"}), imported
    # فراخوانی‌ها فقط بعد از گیتِ مالک‌اند: handle_update بدونِ is_owner به handler نمی‌رسد
    assert "self._is_owner(u)" in src and "return None" in src


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_tg_verdict_durable: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
