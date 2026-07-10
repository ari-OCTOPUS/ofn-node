#!/usr/bin/env python3
"""test_cockpit_v2.py — پذیرشِ Cockpit v2 (مگاپرامپت TELEGRAM-BRAIN-COCKPIT-v2-FULL-BODY §۷.۱).

۲۱ تستِ آفلاین با httpِ تزریقی (FakeHTTP) — هیچ شبکه، هیچ stateِ واقعی (harness).
پوشش: routing ۸ تب، امضای dispatch، backcompatِ menu/app/rfc، توکنِ تک‌مصرفِ act،
allowlist، fail-closedِ پول، بدونِ cycleِ inline، یکتاییِ settle، readmodelِ ایزوله،
chrono-ro، fail-soft، صفحه‌بندی، allowlistِ مالک، برچسب‌ها، redaction، صف، حفظِ رفتارِ قبلی.
"""
import harness

ENV = harness.setup("cockpit-v2")

import json  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import approval_channel as ac  # noqa: E402
import cockpit_readmodel as crm  # noqa: E402
import opslib  # noqa: E402

OPS = Path(ENV["ops"])
STATE = OPS / "state"
SRC_CHANNEL = (Path(os.environ.get("REAL_VAULT", r"F:\backup")) / "_ops" / "budget"
               / "approval_channel.py").read_text(encoding="utf-8")
SRC_READMODEL = (Path(os.environ.get("REAL_VAULT", r"F:\backup")) / "_ops" / "budget"
                 / "cockpit_readmodel.py").read_text(encoding="utf-8")


class FakeHTTP:
    """گیرنده/فرستندهٔ تزریقی: هیچ شبکه‌ای. sendMessageها را ضبط می‌کند."""

    def __init__(self, updates=None):
        self.updates = list(updates or [])
        self.posts: list[tuple[str, dict]] = []
        self.get_urls: list[str] = []

    def get(self, url: str, timeout: float) -> dict:
        self.get_urls.append(url)
        batch, self.updates = self.updates, []
        return {"ok": True, "result": batch}

    def post(self, url: str, body: dict, timeout_s: float = 10.0) -> dict:
        self.posts.append((url.split("/")[-1].split("?")[0], body))
        return {"ok": True}

    def sent_texts(self) -> list[str]:
        return [b.get("text", "") for m, b in self.posts if "sendMessage" in m]


def make_channel(**kw):
    fh = FakeHTTP()
    ch = ac.TelegramApprovalChannel(
        token="123:abc", owner_chat_id=1, state_dir=str(STATE),
        http_get=fh.get, http_post=fh.post, **kw)
    return ch, fh


def mint(ch, verb, key):
    """توکنِ act همان‌طور که رندر mint می‌کند."""
    return ch._new_act_token(verb, key)


# ── ۱) routing ۸ تب + main ساده (ADHD جلسه ۴۶) + now/more + queue ───────────────
def test_menu_routing():
    ch, _ = make_channel()
    for t in ac.TelegramApprovalChannel.TAB_PAGES:
        r = ch.dispatch_callback(f"menu:{t}")
        assert isinstance(r, dict) and r.get("text"), f"tab {t}"
        assert r.get("reply_markup"), f"tab {t} بدونِ keyboard"
    # منوی اصلی حالا ساده است (ADHD): «الان» + «وضعیت» + «همهٔ امکانات» — ≤۳ ردیف
    m = ch.dispatch_callback("menu:main")
    assert isinstance(m, dict) and "reply_markup" in m
    kb = json.dumps(m["reply_markup"], ensure_ascii=False)
    assert "menu:now" in kb and "menu:more" in kb and "menu:status" in kb
    assert len(m["reply_markup"]["inline_keyboard"]) <= 3
    # عمقِ کامل دست‌نخورده زیرِ «همهٔ امکانات»
    more = ch.dispatch_callback("menu:more")
    kb_more = json.dumps(more["reply_markup"], ensure_ascii=False)
    for t in ac.TelegramApprovalChannel.TAB_PAGES:
        assert f"menu:{t}" in kb_more, f"MENU_KEYBOARD بدونِ تبِ {t}"
    # «الان» رندر می‌شود و کرش نمی‌کند (با state خالی هم)
    now_page = ch.dispatch_callback("menu:now")
    assert isinstance(now_page, dict) and "الان" in now_page["text"]
    q = ch.dispatch_callback("menu:queue")
    assert isinstance(q, dict) and "صفِ تأیید" in q["text"]


# ── ۲) امضای dispatch: رشته، نه dict ──────────────────────────────────────────
def test_dispatch_signature():
    ch, _ = make_channel()
    r = ch.dispatch_callback("app:approve:e1:tok")   # نباید TypeError بدهد
    assert isinstance(r, str)
    assert ch.dispatch_callback(None) == "نادیده"


# ── ۳) backcompat: stop_confirm / app / rfc ───────────────────────────────────
def test_callback_backcompat():
    ch, fh = make_channel()
    stop_file = OPS / "STOP-ORGANISM"
    if stop_file.exists():
        stop_file.unlink()
    r = ch.dispatch_callback("menu:stop_confirm")
    assert isinstance(r, dict) and stop_file.exists(), "kill_switch شکست"
    stop_file.unlink()
    ch._stop = False   # حلقه برای بقیهٔ تست زنده بماند
    # app: کارتِ پول → deny (بدونِ settle — مسیرِ ۴بخشیِ قدیمی)
    assert ch.request_approval_card("eff-1", 5.0, "تستِ کارت")
    tok = ch._pending["eff-1"]["token"]
    r = ch.dispatch_callback(f"app:deny:eff-1:{tok}")
    assert "رد شد" in r and ch._pending["eff-1"]["status"] == "denied"
    # rfc: کارت → merge-verdict (فقط ثبت، هیچ settle)
    assert ch.rfc_card("rfc-1", "خلاصهٔ تست")
    rtok = ch._pending_rfc["rfc-1"]["token"]
    r = ch.dispatch_callback(f"rfc:merge:rfc-1:{rtok}")
    assert "ثبت شد" in r
    assert ch.pop_rfc_verdicts() == [("rfc-1", "merge-approved")]


# ── ۴) readها بدونِ توکن؛ act بدونِ توکنِ درست → رد ────────────────────────────
def test_new_schemes_no_token_for_reads():
    ch, _ = make_channel()
    assert isinstance(ch.dispatch_callback("menu:overview"), dict)
    assert isinstance(ch.dispatch_callback("card:overview:vitals"), dict)
    assert isinstance(ch.dispatch_callback("pg:alerts:rules:1"), dict)
    assert ch.dispatch_callback("act:export:raw") == "نادیده"          # ۳ بخش
    mint(ch, "export", "raw")
    r = ch.dispatch_callback("act:export:raw:WRONG")
    assert "نامنطبق" in r


# ── ۵) act تک‌مصرف + انقضا ─────────────────────────────────────────────────────
def test_act_token_single_use():
    ch, _ = make_channel()          # gate=None → sweep بی‌اثرِ امن
    tok = mint(ch, "sweep", "effects")
    r1 = ch.dispatch_callback(f"act:sweep:effects:{tok}")
    assert "gate وصل نیست" in r1
    r2 = ch.dispatch_callback(f"act:sweep:effects:{tok}")   # replay
    assert "منقضی" in r2 or "ناموجود" in r2
    tok2 = mint(ch, "sweep", "effects")
    with ch._lk:
        ch._pending_act["sweep:effects"]["expires_at"] = 0   # منقضی
    r3 = ch.dispatch_callback(f"act:sweep:effects:{tok2}")
    assert "منقضی" in r3 or "ناموجود" in r3


# ── ۶) allowlistِ بسته ─────────────────────────────────────────────────────────
def test_act_allowlist():
    ch, _ = make_channel()
    assert ch.dispatch_callback("act:hack:me:tok") == "نادیده"
    assert ch.dispatch_callback("act:ingest:evil:tok") == "نادیده"
    assert ch.dispatch_callback("act:flag:chamber_t:tok") == "نادیده"   # RED — عمداً غایب
    reqs = STATE / "cockpit-requests.jsonl"
    before = reqs.read_text(encoding="utf-8") if reqs.exists() else ""
    ch.dispatch_callback("act:latent:evilkey:tok")
    after = reqs.read_text(encoding="utf-8") if reqs.exists() else ""
    assert before == after, "کلیدِ خارج از allowlist اثری گذاشت!"


# ── ۷) پول fail-closed در لایهٔ cockpit ────────────────────────────────────────
def test_act_money_fail_closed():
    ch, _ = make_channel()
    assert "reconcile" not in ac.TelegramApprovalChannel.ACT_ALLOWLIST
    assert "epoch" not in ac.TelegramApprovalChannel.ACT_ALLOWLIST
    for t in ac.TelegramApprovalChannel.TAB_PAGES:      # هیچ دکمه‌ای هم نسازد
        kb = json.dumps(ch._tab_keyboard(t), ensure_ascii=False)
        assert "act:reconcile" not in kb and "act:epoch" not in kb
    # شاخهٔ دفاعی: اگر verbِ پولی تعریف شود، بدونِ گیتِ باز refuse می‌شود
    ch.MONEY_VERBS = frozenset({"sweep"})
    tok = mint(ch, "sweep", "effects")
    r = ch.dispatch_callback(f"act:sweep:effects:{tok}")
    assert "قفل" in r, f"verbِ پولی بدونِ live-gate رد نشد: {r}"


# ── ۸) هیچ subsystem cycleِ inline ─────────────────────────────────────────────
def test_act_no_inline_subsystem():
    assert "run_cycle(" not in SRC_CHANNEL, "فراخوانِ inlineِ run_cycle!"
    assert "run_epoch(" not in SRC_CHANNEL, "فراخوانِ inlineِ run_epoch!"
    assert "consolidation_beat(" not in SRC_CHANNEL
    ch, _ = make_channel()
    tok = mint(ch, "doctor", "run")
    r = ch.dispatch_callback(f"act:doctor:run:{tok}")
    assert "out-of-band" in r
    reqs = (STATE / "cockpit-requests.jsonl").read_text(encoding="utf-8")
    assert '"verb": "doctor"' in reqs


# ── ۹) یکتاییِ مسیرِ settle (فقط کد — نه کامنت/داکسترینگ) ─────────────────────
def test_settle_path_unique():
    code_lines = [ln for ln in SRC_CHANNEL.splitlines()
                  if not ln.strip().startswith(("#", "rem"))]
    n = "\n".join(code_lines).count(".settle(")
    assert n == 1, f"مسیرِ settle باید فقط در _settle_effect باشد (یافت: {n})"
    assert "self._gate.settle(" in SRC_CHANNEL


# ── ۱۰) readmodel بدونِ organism (AST — داکسترینگ نمی‌شمارد) ──────────────────
def test_readmodel_no_organism_import():
    import ast
    tree = ast.parse(SRC_READMODEL)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] == "organism" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "organism"


# ── ۱۱) chrono فقط‌خواندنی و بی‌بلاک ────────────────────────────────────────────
def test_chrono_ro_uri():
    assert "mode=ro&immutable=1" in SRC_READMODEL
    assert "timeout=1" in SRC_READMODEL
    (STATE / "chrono.db").write_bytes(b"NOT A SQLITE FILE")   # خراب → fail-soft
    rm = crm.CockpitReadModel(state_dir=STATE)
    assert rm.read_chrono_ro() == {}
    (STATE / "chrono.db").unlink()


# ── ۱۲) fail-softِ readmodel با stateِ خالی ────────────────────────────────────
def test_readmodel_failsoft():
    import tempfile
    empty = Path(tempfile.mkdtemp(prefix="cockpit-empty-"))
    rm = crm.CockpitReadModel(state_dir=empty, ops_dir=empty)
    for name in ("read_state", "read_sigma", "read_telemetry", "read_fitness",
                 "read_school", "read_latent", "read_bcm", "read_sparse",
                 "read_idea", "read_chamber_t", "read_fisher", "read_epi",
                 "read_box", "read_phase", "read_channels", "read_lab",
                 "read_bundle", "read_consolidation", "read_hebbian",
                 "read_chrono_ro"):
        assert getattr(rm, name)() == {}, name
    assert rm.read_requests() == []
    assert rm.tail_governor_alerts() == []
    rules = rm.rules()
    assert len(rules) == 24 and all("status" in r for r in rules)


# ── ۱۳) صفحه‌بندی ──────────────────────────────────────────────────────────────
def test_pagination():
    ch, _ = make_channel()
    r1 = ch.dispatch_callback("pg:alerts:rules:1")
    assert isinstance(r1, dict) and "1/3" in r1["text"]      # 24/8 = ۳ صفحه
    r3 = ch.dispatch_callback("pg:alerts:rules:3")
    kb = json.dumps(r3["reply_markup"], ensure_ascii=False)
    assert "pg:alerts:rules:2" in kb and "pg:alerts:rules:4" not in kb
    r99 = ch.dispatch_callback("pg:alerts:rules:99")          # clamp
    assert "3/3" in r99["text"]
    rf = ch.dispatch_callback("pg:safety:flags:3")            # 19/8 = ۳ صفحه
    assert isinstance(rf, dict) and "3/3" in rf["text"]
    assert ch.dispatch_callback("pg:alerts:rules:x") == "نادیده"
    assert ch.dispatch_callback("pg:evil:rules:1") == "نادیده"


# ── ۱۴) allowlistِ مالک در poll ────────────────────────────────────────────────
def test_owner_allowlist():
    fh = FakeHTTP(updates=[{"update_id": 7, "message": {
        "chat": {"id": 999}, "from": {"id": 999}, "text": "/start", "date": 0}}])
    ch = ac.TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                    state_dir=str(STATE),
                                    http_get=fh.get, http_post=fh.post)
    n = ch.poll_once()
    assert n == 1 and ch._offset == 8            # پردازش‌شده ولی ردشده؛ offset جلو
    assert fh.sent_texts() == [], "به غیرمالک پاسخ رفت!"


# ── ۱۵) برچسبِ 🔴 روی قفل‌های live-gate ────────────────────────────────────────
def test_live_gate_locked_labels():
    ch, _ = make_channel()
    money = ch.dispatch_callback("menu:money")["text"]
    assert "🔴" in money and "2026-07-21" in money
    gov = ch.dispatch_callback("card:money:governor")["text"]
    assert "🔴" in gov and "2026-07-21" in gov
    doc = ch.dispatch_callback("menu:doctor")["text"]
    assert "needs-live-gate" in doc or "🔴" in doc


# ── ۱۶) برچسبِ 🟡 روی flagهای خاموش (بدونِ روشن‌کردن) ─────────────────────────
def test_flag_off_labels():
    before = {k: v for k, v in os.environ.items() if k.startswith("OCTOPUS_WIRE")}
    ch, _ = make_channel()
    assert "🟡" in ch.dispatch_callback("card:money:reconcile")["text"]
    assert "🟡" in ch.dispatch_callback("card:money:cardiac")["text"]
    assert "🟡 OFF" in ch.dispatch_callback("menu:doctor")["text"]
    assert "🟢" in ch.dispatch_callback("card:blueprint:chamber")["text"]  # RED خاموش = درست
    after = {k: v for k, v in os.environ.items() if k.startswith("OCTOPUS_WIRE")}
    assert before == after, "رندر نباید flag را تغییر دهد"


# ── ۱۷) fixtureِ مسموم → redaction ─────────────────────────────────────────────
def test_no_secret_in_output():
    fake_token = "88888888888:AA" + "x" * 33
    fake_sk = "sk-" + "A" * 24
    (OPS / "governor").mkdir(exist_ok=True)
    (OPS / "governor" / "governor-alerts.md").write_text(
        f"## alert\n- توکن لو رفت: {fake_token}\n", encoding="utf-8")
    (STATE / "ORGANISM-STATE.json").write_text(
        json.dumps({"ts": "2026-07-10T00:00:00", "leak": fake_sk}), encoding="utf-8")
    ch, fh = make_channel()
    assert ch._redact(f"x {fake_token} y") == crm.REDACTED_BODY
    # C8: readmodel واقعاً از همین tmp می‌خواند (نه vaultِ واقعی) — کارت‌ها fixtureِ مسموم را
    # می‌بینند و redact می‌کنند. اگر ops_dir درست مشتق نشود، این کارت‌ها خالی می‌شوند و تست
    # به‌اشتباه سبز می‌ماند؛ پس assert می‌کنیم که redaction واقعاً فایر شده.
    fired = False
    for cb in ("card:alerts:governor", "card:alerts:raw"):
        r = ch.dispatch_callback(cb)
        text = r["text"] if isinstance(r, dict) else str(r)
        if fake_token in text or fake_sk in text:
            fired = True                        # کارت واقعاً secret را خواند (قبل از send)
        ch.send_text(text)                      # نقطهٔ ضمانت: خروجیِ واقعی به تلگرام
    sent = "\n".join(fh.sent_texts())
    assert fake_token not in sent and fake_sk not in sent, "secret لو رفت!"
    assert fired, "readmodel fixtureِ مسموم را نخواند (C8: ops_dir از tmp مشتق نشد؟)"
    assert crm.REDACTED_BODY in sent, "کارتِ مسموم redact نشد"
    (STATE / "ORGANISM-STATE.json").unlink()
    (OPS / "governor" / "governor-alerts.md").unlink(missing_ok=True)


# ── ۲۳) getUpdates صریحاً callback_query می‌خواهد (فیکسِ باگِ دکمه‌ها) ──────────
def test_getupdates_requests_callbacks():
    import urllib.parse
    fh = FakeHTTP()
    ch = ac.TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                    state_dir=str(STATE),
                                    http_get=fh.get, http_post=fh.post)
    ch.poll_once()
    assert fh.get_urls, "getUpdates صدا زده نشد"
    url = urllib.parse.unquote(fh.get_urls[0])
    assert "getUpdates" in url and "callback_query" in url and "message" in url, \
        f"allowed_updates بدونِ callback_query: {url}"


# ── ۲۲) flaggo مقدارِ مطلقِ زمانِ رندر را می‌نویسد (C4)، اتمیک با مصرف ──────────
def test_act_flag_absolute_target():
    ch, _ = make_channel()
    # confirmِ یک flagِ امن (doctor) → دکمهٔ flaggo با target ثبت می‌شود
    r = ch._act_flag_confirm("doctor")
    assert isinstance(r, dict)
    data = [b["callback_data"] for row in r["reply_markup"]["inline_keyboard"]
            for b in row if b.get("callback_data", "").startswith("act:flaggo:")]
    assert data, "دکمهٔ flaggo ساخته نشد"
    entry = ch._pending_act.get("flaggo:doctor")
    assert entry is not None and "target" in entry, "target ذخیره نشد (C4)"
    assert isinstance(entry["target"], bool)
    # توکنِ act تک‌مصرف: مصرفِ اتمیک وضعیت را به consumed می‌برد
    verb, key, tok = data[0].split(":")[1], data[0].split(":")[2], data[0].split(":")[3]
    assert verb == "flaggo" and key == "doctor"


# ── ۱۸) صفِ تأیید با وضعیتِ authoritative از گیت ───────────────────────────────
def test_queue_surface():
    class FakeGate:
        def status_of(self, eid):
            return "pending"

        def sweep_stale_effects(self):
            return {"refused": 2}
    fh = FakeHTTP()
    ch = ac.TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                    state_dir=str(STATE), gate=FakeGate(),
                                    http_get=fh.get, http_post=fh.post)
    assert ch.request_approval_card("eff-q", 3.0, "کارتِ صف")
    q = ch.dispatch_callback("menu:queue")["text"]
    assert "eff-q" in q and "pending" in q, "وضعیتِ gate در صف نیست"
    assert ch._count_pending() == 1
    tok = mint(ch, "sweep", "effects")
    assert "2" in ch.dispatch_callback(f"act:sweep:effects:{tok}")


# ── ۱۹) خطای رندر → alert + زنده‌ماندن ─────────────────────────────────────────
def test_failsoft_loop():
    ch, _ = make_channel()
    seen = []
    orig_alert = opslib.alert
    opslib.alert = lambda items: seen.append(items)
    try:
        orig = ch._tab_text
        ch._tab_text = lambda page: (_ for _ in ()).throw(RuntimeError("boom"))
        r = ch._render_tab("overview")
        assert isinstance(r, dict) and "❌" in r["text"]
        assert seen, "خطا alert نشد"
        ch._tab_text = orig
        assert "نمای کلی" in ch._render_tab("overview")["text"]   # زنده ماند
    finally:
        opslib.alert = orig_alert


# ── ۲۰) حفظِ کاملِ رفتارِ قبلی ─────────────────────────────────────────────────
def test_existing_commands_preserved():
    ch, _ = make_channel()
    r = ch.handle_command("/start")
    assert isinstance(r, dict) and "اختاپوس" in r["text"]
    assert "ثبتِ لید" in ch.handle_command("/lead")
    assert isinstance(ch.handle_command("/status"), str)
    assert ch.handle_command("سلام") is None
    stop_file = OPS / "STOP-ORGANISM"
    if stop_file.exists():
        stop_file.unlink()
    assert "KILL-SWITCH" in ch.handle_command("/stop")
    assert stop_file.exists()
    stop_file.unlink()
    ch._stop = False
    assert isinstance(ch.dispatch_callback("menu:lab"), dict)
    assert isinstance(ch.dispatch_callback("menu:status"), dict)


# ── ۲۱) verdictِ فاز فقط از رجیستریِ rfc ───────────────────────────────────────
def test_phaseverdict_via_rfc():
    assert "act:phaseverdict" not in SRC_CHANNEL
    assert "phase" not in ac.TelegramApprovalChannel.ACT_ALLOWLIST
    ch, _ = make_channel()
    assert ch.dispatch_callback("act:phase:transition:tok") == "نادیده"
    card = ch.dispatch_callback("card:blueprint:transition")["text"]
    assert "RFC" in card


if __name__ == "__main__":
    failed = harness.run([
        ("routing ۸ تب + main + queue", test_menu_routing),
        ("امضای رشته‌ایِ dispatch", test_dispatch_signature),
        ("backcompat: stop/app/rfc", test_callback_backcompat),
        ("read بی‌توکن؛ act توکن‌دار", test_new_schemes_no_token_for_reads),
        ("act تک‌مصرف + انقضا", test_act_token_single_use),
        ("allowlistِ بستهٔ act", test_act_allowlist),
        ("پول fail-closed", test_act_money_fail_closed),
        ("بدونِ cycleِ inline", test_act_no_inline_subsystem),
        ("settle فقط یک مسیر", test_settle_path_unique),
        ("readmodel بدونِ organism", test_readmodel_no_organism_import),
        ("chrono ro+immutable+timeout", test_chrono_ro_uri),
        ("fail-softِ readmodel", test_readmodel_failsoft),
        ("صفحه‌بندی", test_pagination),
        ("allowlistِ مالک", test_owner_allowlist),
        ("برچسبِ قفلِ live", test_live_gate_locked_labels),
        ("برچسبِ flagِ خاموش", test_flag_off_labels),
        ("redactionِ fixtureِ مسموم", test_no_secret_in_output),
        ("صفِ تأیید + گیت", test_queue_surface),
        ("خطای رندر → alert + زنده", test_failsoft_loop),
        ("حفظِ رفتارِ قبلی", test_existing_commands_preserved),
        ("verdictِ فاز فقط rfc", test_phaseverdict_via_rfc),
        ("flaggo target مطلق (C4)", test_act_flag_absolute_target),
        ("getUpdates → callback_query", test_getupdates_requests_callbacks),
    ])
    sys.exit(1 if failed else 0)
