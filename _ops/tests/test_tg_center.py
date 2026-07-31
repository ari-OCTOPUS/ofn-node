"""test_tg_center.py — مرکزِ فرماندهیِ تلگرام (telegram_center/center.py).

پوشش: setup دوباره = idempotent؛ beat فقط status را edit می‌کند (هرگز sendِ دوباره)؛
cadence دایجست با clockِ تزریقی؛ callbackِ غیرمالک = سکوتِ کامل؛ okِ مالک = فایلِ
approval + توکنِ HumanAppendGuard (فقط با راز) + answer؛ فایلِ STOP حلقه را می‌ایستاند؛
و not-wired = صفر اثر. صفر شبکه (client/render ِ fake) و صفر نوشتن خارج از temp harness.
"""
import json
import os
import pathlib
import shutil
import sys
import tempfile
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-center")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402
import approval_store as aps   # noqa: E402 — فاز E
import metadata_scan as ms     # noqa: E402 — فاز D
import mission as mission_mod  # noqa: E402 — Mission Genome

# sandbox برای مسیرهای خروجیِ اختاپوس (تا تست روی F:\backup\_octopus ننویسد)
_E2E_SANDBOX = Path(tempfile.mkdtemp(prefix="octopus-center-e2e-"))


def _redirect_octopus_paths():
    """هدایتِ مسیرهای approval_store/metadata_scan/mission به sandboxِ تازه."""
    shutil.rmtree(_E2E_SANDBOX / "_octopus", ignore_errors=True)
    shutil.rmtree(_E2E_SANDBOX / "_ops" / "state" / "telegram" / "missions", ignore_errors=True)
    shutil.rmtree(_E2E_SANDBOX / "_ops" / "state" / "telegram" / "approvals", ignore_errors=True)
    aps._OCTOPUS_STATE = _E2E_SANDBOX / "_octopus" / "state"
    aps._APPROVALS_JSON = aps._OCTOPUS_STATE / "approvals.json"
    aps._AUDIT_PATH = _E2E_SANDBOX / "_octopus" / "logs" / "audit.log"
    aps._LEGACY_DIR = _E2E_SANDBOX / "_ops" / "state" / "telegram" / "approvals"
    aps._ROOT = _E2E_SANDBOX
    mission_mod._STATE_DIR = _E2E_SANDBOX / "_ops" / "state" / "telegram" / "missions"
    mission_mod._MISSIONS_JSON = mission_mod._STATE_DIR / "missions.json"
    mission_mod._AUDIT_JSONL = mission_mod._STATE_DIR / "mission-audit.jsonl"
    ms._OCTOPUS = _E2E_SANDBOX / "_octopus"
    ms._MANIFEST_DIR = ms._OCTOPUS / "manifests"
    ms._HISTORY_DIR = ms._MANIFEST_DIR / "history"
    ms._REPORTS_DIR = ms._OCTOPUS / "reports" / "daily"
    ms._STATE_PATH = ms._OCTOPUS / "state" / "metadata_scan.json"
    ms._AUDIT_PATH = ms._OCTOPUS / "logs" / "audit.log"
    ms._ROOT = _E2E_SANDBOX

CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"
APPROVALS = opslib.STATE_DIR / "telegram" / "approvals"
ALL_LEGS = ("lead", "ziman", "mining", "crypto", "accounting",
            "studio_pf", "system", "knowledge")

# ثابت‌های تستِ دو-باتیِ TG-P2 (center chat_id منفی = سوپرگروهِ forum)
CENTER = -1009999


# ─── fakeها (صفر شبکه، فقط ثبتِ فراخوان‌ها) ─────────────────────────────────────
class FakeClient:
    def __init__(self, wired=True, owner_id=777):
        self._is_wired = wired
        self.owner_id = owner_id
        self.calls: list = []
        self._next_mid = 100
        self._next_topic = 10
        self.updates: list = []

    def wired(self):
        return self._is_wired

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self.calls.append(("send", {"text": text, "topic_id": topic_id,
                                    "keyboard": keyboard, "chat_id": chat_id,
                                    "pin": pin}))
        self._next_mid += 1
        return self._next_mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def pin_message(self, message_id, chat_id=None):
        self.calls.append(("pin", {"message_id": message_id}))
        return True

    def create_topic(self, name, chat_id=None):
        self.calls.append(("create_topic", {"name": name}))
        self._next_topic += 1
        return self._next_topic

    def set_commands(self, commands, scope=None):
        self.calls.append(("set_commands", {"commands": list(commands),
                                            "scope": scope}))
        return True

    def delete_commands(self, scope=None):
        self.calls.append(("delete_commands", {"scope": scope}))
        return True

    def poll_updates(self, offset=0, timeout_s=25):
        self.calls.append(("poll", {"offset": offset}))
        ups, self.updates = self.updates, []
        return ups

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"id": callback_id, "text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def fake_render(guidance_items=None):
    """renderِ قراردادی (پاک، بدونِ شبکه) برای تزریق به Center."""
    legs = {k: {} for k in ALL_LEGS}

    def collect_feeds():
        return {"guidance": {"items": list(guidance_items or [])}}

    def render_status(feeds):
        return "STATUS-LINE"

    def render_leg_digest(leg_key, leg):
        return f"digest:{leg_key}"

    def render_decision(item):
        did = item.get("id", "x")
        kb = [[{"text": "✅", "callback_data": f"ok:{did}"},
               {"text": "❌", "callback_data": f"no:{did}"},
               {"text": "⏳", "callback_data": f"later:{did}"}]]
        return (f"decision:{did}", kb)

    def render_menu(power=False, feeds=None, paused=None):
        return "MENU-LIVE", [[{"text": "📊", "callback_data": "mn:st"}],
                             [{"text": "🧬", "callback_data": "mn:ms"}]]

    def render_organs(paused, config=None):
        return "ORGANS", [[{"text": "x", "callback_data": "mn:menu"}]]

    def render_power(power, sentinels=None):
        return "POWER", [[{"text": "x", "callback_data": "mn:menu"}]]

    def scrub(t):
        return t

    return types.SimpleNamespace(LEGS=legs, collect_feeds=collect_feeds,
                                 render_status=render_status,
                                 render_leg_digest=render_leg_digest,
                                 render_decision=render_decision,
                                 render_menu=render_menu,
                                 render_organs=render_organs,
                                 render_power=render_power,
                                 scrub=scrub)


def fake_render_with_map(guidance_items=None):
    """مثلِ fake_render ولی با render_map_page و render_approvals_queue (فاز D/E)."""
    base = fake_render(guidance_items)

    def render_map_page(scan_state=None):
        return "MAP-PAGE", [[{"text": "🗺 شروع", "callback_data": "map:start"}],
                            [{"text": "🔙", "callback_data": "mn:menu"}]]

    def render_approvals_queue(pending=None, summary_counts=None, legacy_recent=None):
        pend = pending or []
        kb = []
        for job in pend[:3]:
            jid = job.get("id", "?")
            kb.append([{"text": "✅", "callback_data": f"ap:ok:{jid}"},
                       {"text": "❌", "callback_data": f"ap:no:{jid}"}])
        kb.append([{"text": "🔙", "callback_data": "mn:menu"}])
        return f"AP-QUEUE ({len(pend)} pending)", kb

    base.render_map_page = render_map_page
    base.render_approvals_queue = render_approvals_queue
    return base


class Clock:
    def __init__(self, t=1000.0):
        self.t = float(t)

    def __call__(self):
        return self.t


def _reset():
    """state تلگرامِ temp را بینِ تست‌ها پاک کن (config حافظهٔ idempotency است)."""
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)
    if center.STOP_TG_CENTER.exists():
        center.STOP_TG_CENTER.unlink()


# ─── تست‌ها ──────────────────────────────────────────────────────────────────────
def t_a_double_ensure_setup_idempotent():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    assert c.ensure_setup() is True
    assert len(fc.named("create_topic")) == 8          # هر ۸ پا یک تاپیک
    assert len(fc.named("set_commands")) == 1
    # ۲۰۲۶-۰۷-۳۰: setup از امروز **دو** پیامِ یک‌بارهٔ پین‌شده می‌سازد —
    # statusِ زنده و دستورالعملِ استفاده (مالک: «گروه هیچی نداره که
    # دستورالعمل»). ناوردیِ این تست عدد نیست، «هیچ‌چیز دوبار ساخته نمی‌شود»
    # است؛ پس شمارشِ خام جایش را به سنجهٔ دقیق‌تر می‌دهد: هر دو پین‌شده‌اند،
    # و دورِ دوم صفر sendِ تازه.
    sends = fc.named("send")
    assert len(sends) == 2, [s["text"][:24] for s in sends]
    assert all(s["pin"] is True for s in sends)         # هر دو پین
    assert sum("این گروه چطور کار می‌کند" in s["text"] for s in sends) == 1
    assert c.ensure_setup() is True                     # دور دوم
    assert len(fc.named("create_topic")) == 8           # هیچ تاپیکِ تکراری
    assert len(fc.named("set_commands")) == 1
    assert len(fc.named("send")) == 2                   # هیچ‌کدام دوباره نساخت
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert isinstance(cfg.get("status_message_id"), int)
    assert sorted(cfg.get("topics", {}).keys()) == sorted(ALL_LEGS)


def t_b_beat_edits_status_never_resends():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    c.ensure_setup()
    status_mid = json.loads(CFG_PATH.read_text("utf-8"))["status_message_id"]
    fc.calls.clear()
    out1 = c.beat()                                     # اولین beat: همهٔ دایجست‌ها سررسیده
    assert out1["edited"] is True and out1["digests"] == 8
    edits = fc.named("edit")
    assert len(edits) == 1 and edits[0]["message_id"] == status_mid
    assert all(s["pin"] is False for s in fc.named("send"))   # هیچ sendِ پین‌شده (status) دوباره
    fc.calls.clear()
    out2 = c.beat()                                     # بلافاصله: هیچ دایجستی سررسید نیست
    assert out2["edited"] is True and out2["digests"] == 0
    assert len(fc.named("send")) == 0                   # فقط edit، صفر send
    assert len(fc.named("edit")) == 1


def t_c_digest_cadence_respects_injected_clock():
    _reset()
    fc = FakeClient()
    clk = Clock(50_000.0)
    c = center.Center(client=fc, clock=clk, render_mod=fake_render())
    c.ensure_setup()
    fc.calls.clear()
    assert c.beat()["digests"] == 8                     # صفر سابقه → همه due
    clk.t += 3600.0
    assert c.beat()["digests"] == 0                     # هنوز ۲۴h نشده
    clk.t += 86400.0
    assert c.beat()["digests"] == 8                     # سررسیدِ دوباره
    # override per-leg از config: فقط lead هر ۶۰ ثانیه
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    cfg["cadence_s"] = {"lead": 60, "default": 86400}
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")
    clk.t += 61.0
    out = c.beat()
    assert out["digests"] == 1                          # فقط lead due شد
    assert fc.named("send")[-1]["text"] == "digest:lead"


def t_c2_leg_cards_walk_every_leg_and_the_cursor_survives_on_disk():
    """کارتِ زندهٔ پاها باید **دور** بزند، نه روی پای اول گیر کند.

    ⚠️ این تست از یک شکستِ واقعی زاده شد: مالک گفت «گروه تلگرام هیچی نداره».
    نسخهٔ اولِ کد شمارنده را روی `cfg` ِ محلیِ beat می‌نوشت و `dirty=True`
    می‌زد — ولی `_save_config` ِ آن مسیر داخلِ شرطِ ساعتیِ پالس بود و
    `_refresh_leg_card` هم خودش config را از دیسک تازه می‌خواند. پس شمارنده
    روی صفر ماند، هر ضربان همان پای اول را گرفت، روی هش زود برگشت ⇒ در کلِ
    عمرِ پروسه دقیقاً **یک** کارت. و گاردِ نحویِ من (که فقط وجودِ فراخوان و
    رشتهٔ `leg_card_cursor` را می‌دید) سبز بود — پایهٔ زیرِ سطحِ هدف.

    سنجهٔ درست فقط رفتار است: بعد از دو نوبتِ سررسیده، **دو تاپیکِ متفاوت**
    کارت گرفته باشند و شمارنده روی دیسک جلو رفته باشد."""
    _reset()
    fc = FakeClient()
    clk = Clock(50_000.0)
    c = center.Center(client=fc, clock=clk, render_mod=fake_render())
    c.ensure_setup()
    topics = json.loads(CFG_PATH.read_text("utf-8"))["topics"]
    fc.calls.clear()
    c.beat()                                            # نوبتِ اول
    cfg1 = json.loads(CFG_PATH.read_text("utf-8"))
    ids1 = dict(cfg1.get("leg_card_ids") or {})
    assert len(ids1) == 1, f"نوبتِ اول باید دقیقاً یک کارت بسازد، شد {ids1}"
    assert cfg1.get("leg_card_cursor") == 1, \
        f"شمارنده روی دیسک جلو نرفت: {cfg1.get('leg_card_cursor')!r}"
    # ناوردیِ ضدِ رگبار: نوبتِ بلافاصله (ساعتِ یکسان) هیچ کارتِ تازه‌ای نمی‌سازد
    c.beat()
    assert dict(json.loads(CFG_PATH.read_text("utf-8"))
                .get("leg_card_ids") or {}) == ids1, "کادنس رعایت نشد"
    clk.t += center.LEG_CARD_EVERY_S + 1.0
    c.beat()                                            # نوبتِ دوم، سررسیده
    cfg2 = json.loads(CFG_PATH.read_text("utf-8"))
    ids2 = dict(cfg2.get("leg_card_ids") or {})
    assert len(ids2) == 2, f"دور نزد — هنوز روی همان پا: {ids2}"
    assert cfg2.get("leg_card_cursor") == 2
    # و کارت‌ها واقعاً به **تاپیکِ خودِ همان پا** رفتند، نه یک تاپیکِ مشترک
    tids = {topics[leg] for leg in ids2}
    assert len(tids) == 2, f"دو کارت در یک تاپیک: {tids}"


def t_c3_a_bogus_message_id_is_never_trusted_forever():
    """شناسهٔ جعلی + هشِ منطبق نباید کارت را برای همیشه قفل کند.

    این هم یک شکستِ واقعی بود، نه فرضی: پروبِ e2e ِ خودم با کلاینتِ جاسوس
    (که 9000+n برمی‌گرداند) روی center-config.json ِ **زنده** نوشت، `lead`
    شناسهٔ ۹۰۱۰ گرفت، و کارتش دیگر هرگز ساخته نشد."""
    _reset()
    fc = FakeClient()
    clk = Clock(50_000.0)
    c = center.Center(client=fc, clock=clk, render_mod=fake_render())
    c.ensure_setup()
    c.beat()
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    leg = next(iter(cfg["leg_card_ids"]))
    cfg["leg_card_ids"][leg] = 9010                     # آلودگیِ پروب
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")
    c._refresh_leg_card(leg)
    got = json.loads(CFG_PATH.read_text("utf-8"))["leg_card_ids"].get(leg)
    assert isinstance(got, int) and not (9000 <= got < 9100), \
        f"شناسهٔ جعلی باور شد و کارت قفل ماند: {got!r}"


def t_c4_an_unknown_callback_bridges_to_the_organism_router():
    """⚠️ یافتهٔ اسکنِ عمیقِ ۰۷-۳۱: پلِ فرمان‌ها جواب را با کیبورد روی باتِ
    بیرونی می‌فرستاد ولی تپِ همان کیبورد «نادیده» می‌گرفت — ~۳۵ فرمانِ bridged
    همگی کارتِ مرده بودند، از جمله app:approve/deny (پول). حالا تپ هم همان پل
    را طی می‌کند و ناشناختهٔ هر دو، «نادیده»ی امروز می‌مانَد."""
    import sys as _sys
    import types as _types
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    c.ensure_setup()
    calls = {}

    class _FakeCh:
        def dispatch_callback(self, data, from_id=None, external=False,
                              trusted_internal=False):
            calls["data"], calls["from_id"], calls["external"] = \
                data, from_id, external
            if data.startswith("app:"):
                return "✅ ثبت شد"
            if data.startswith("menu:"):
                return {"text": "MENU-PAGE", "reply_markup": [[{"text": "x",
                        "callback_data": "menu:2"}]]}
            return "نادیده"

    fake_mod = _types.ModuleType("approval_channel")
    fake_mod.TelegramApprovalChannel = _FakeCh
    old = _sys.modules.get("approval_channel")
    _sys.modules["approval_channel"] = fake_mod
    try:
        fc.calls.clear()
        # (الف) verb ِ ارگانیسمی با پاسخِ متنی → toast ِ همان پاسخ
        r = c.handle_update({"update_id": 9, "callback_query": {
            "id": "cb9", "from": {"id": 777}, "data": "app:ok:e1:tok",
            "message": {"chat": {"id": 777}}}})
        assert r and r.get("kind") == "bridged-callback", r
        assert calls["data"] == "app:ok:e1:tok" and calls["external"] is True
        assert calls["from_id"] == 777, "هویتِ واقعی به dispatch نرسید"
        assert any("ثبت شد" in a["text"] for a in fc.named("answer"))
        # (ب) پاسخِ dict ِ کیبورددار → پیامِ جدا با همان کیبورد
        fc.calls.clear()
        r2 = c.handle_update({"update_id": 10, "callback_query": {
            "id": "cb10", "from": {"id": 777}, "data": "menu:1",
            "message": {"chat": {"id": 777}}}})
        assert r2 and r2.get("kind") == "bridged-callback"
        sends = [s for s in fc.named("send") if s["text"] == "MENU-PAGE"]
        assert sends and sends[0]["keyboard"], "کیبوردِ پاسخ دوباره دور ریخته شد"
        # (ج) ناشناخته برای هر دو → «نادیده»ی امروز (parity)
        fc.calls.clear()
        r3 = c.handle_update({"update_id": 11, "callback_query": {
            "id": "cb11", "from": {"id": 777}, "data": "zz:1",
            "message": {"chat": {"id": 777}}}})
        assert r3 == {"kind": "callback", "verdict": None}
        assert any(a["text"] == "نادیده" for a in fc.named("answer"))
    finally:
        if old is not None:
            _sys.modules["approval_channel"] = old
        else:
            _sys.modules.pop("approval_channel", None)


def t_c5_the_home_message_is_edited_not_resent_and_dm_guide_is_pinned():
    """⚠️ دو یافتهٔ اسکن: (۱) «خانه» یک‌بار پین می‌شد و دیگر هرگز ویرایش نه —
    هر پالس پیامِ نو، پس خانهٔ بالای چت عکسِ کهنه بود. (۲) guide.dm_text صفر
    صداکننده داشت — سطحِ اصلیِ مالک بی‌دستورالعمل."""
    _reset()
    fc = FakeClient()
    fc.owner_chat_id = 777          # زنده: از env می‌آید؛ fake باید صریح بدهد
    clk = Clock(50_000.0)
    c = center.Center(client=fc, clock=clk, render_mod=fake_render())
    c.ensure_setup()
    # center-pulse با فلگِ خاموش عمداً هیچ‌جا نمی‌رود (current=none) — این تست
    # رفتارِ «فلگ روشن» را می‌سنجد، همان چیزی که روی درختِ زنده مسلح است.
    os.environ["OCTOPUS_TG_SPLIT_V1"] = "1"
    try:
        c.beat()                                        # پالسِ اول: ساخت+پین
        cfg = json.loads(CFG_PATH.read_text("utf-8"))
        hid = cfg.get("home_message_id")
        assert isinstance(hid, int), "خانه ساخته نشد"
        dmid = cfg.get("dm_guide_message_id")
        assert isinstance(dmid, int), "راهنمای DM فرستاده نشد — صداکننده هنوز صفر"
        # ⚠️ شمارشِ خامِ send این‌جا دروغ می‌گوید: ضربانِ دوم کارتِ پا هم
        # می‌فرستد (round-robin ِ مشروع). سنجه فقط خودِ پالس است.
        def _pulses():
            return [s for s in fc.named("send") if "نبضِ اختاپوس" in s["text"]]
        n_pulse = len(_pulses())
        clk.t += 3601.0
        c.beat()                                        # پالسِ دوم: فقط ویرایش
        assert len(_pulses()) == n_pulse, \
            "پالسِ دوم پیامِ نو فرستاد — خانه باید همان پیام ویرایش شود"
        assert any(e["message_id"] == hid for e in fc.named("edit")), \
            "خانهٔ پین‌شده ویرایش نشد"
        # راهنمای DM هم دوباره فرستاده نمی‌شود (هش بی‌تغییر)
        assert (json.loads(CFG_PATH.read_text("utf-8"))
                ["dm_guide_message_id"] == dmid)
    finally:
        os.environ.pop("OCTOPUS_TG_SPLIT_V1", None)


def t_c6_a_watchdog_revival_is_reported_to_the_owner_once():
    """⚠️ یافتهٔ منتقدِ اسکن: بات ۳ ساعت و ۵۳ دقیقه مرده بود («centre down
    (silent 14006s)») و مالک هرگز نفهمید — اعلانِ واچ‌داگ به event_bridge ِ
    تاریک می‌رود. حالا خودِ مرکز در بوت لاگ را می‌خوانَد و یک‌بار می‌گوید."""
    _reset()
    wl = opslib.STATE_DIR / "tg-center-watchdog-log.txt"
    wl.parent.mkdir(parents=True, exist_ok=True)
    wl.write_text(
        "2026-07-31T08:00:00 STOP-TG-CENTER present - not reviving centre\n"
        "2026-07-31T08:37:14 centre down (silent 14006s) - launching "
        "RUN-TG-CENTER.bat\n", "utf-8")
    try:
        fc = FakeClient()
        fc.owner_chat_id = 777
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
        c.ensure_setup()
        rec = [s for s in fc.named("send") if "واچ‌داگ" in s["text"]]
        assert rec, "رسیدِ بازگشت فرستاده نشد"
        assert "۲۳۳" in rec[0]["text"], \
            f"مدتِ سکوت (۱۴۰۰۶s≈۲۳۳ دقیقه، رقمِ فارسی) در رسید نیست: {rec[0]['text']!r}"
        # بوتِ دوم بدونِ خطِ launching ِ تازه → صفر رسید (dedupe با cursor)
        fc2 = FakeClient()
        fc2.owner_chat_id = 777
        c2 = center.Center(client=fc2, clock=Clock(), render_mod=fake_render())
        c2.ensure_setup()
        assert not [s for s in fc2.named("send") if "واچ‌داگ" in s["text"]], \
            "هر ری‌استارتِ عادی هم رسید می‌فرستد ⇒ رگبار"
    finally:
        wl.unlink(missing_ok=True)


def t_c7_unpausable_leg_cards_carry_no_pause_resume_buttons():
    """گروه ۵ِ اسکنِ ۰۷-۳۱: کارتِ system/mirror دکمهٔ ⏸/▶️ داشت که همیشه
    «پای ناشناخته» می‌داد (power.PAUSABLE_LEGS شاملشان نیست). منشور رأی ۴:
    «دکمه‌ای که کاری نمی‌کند وجود ندارد.»"""
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    c.ensure_setup()
    fc.calls.clear()
    c._refresh_leg_card("system")
    sends = [s for s in fc.named("send") if s["keyboard"]]
    assert sends, "کارتِ system ساخته نشد"
    cds = [b["callback_data"] for row in sends[-1]["keyboard"] for b in row]
    assert not any(cd.startswith(("tk:c:", "tk:p:")) for cd in cds), \
        f"کارتِ بی-pause هنوز ⏸/▶️ دارد: {cds}"
    assert any(cd.startswith("tk:q:") for cd in cds), cds
    # و پای قابلِ‌مکث چهار دکمه‌اش را نگه می‌دارد (ضدِ بیش‌بست)
    fc.calls.clear()
    c._refresh_leg_card("lead")
    sends = [s for s in fc.named("send") if s["keyboard"]]
    cds = [b["callback_data"] for row in sends[-1]["keyboard"] for b in row]
    assert any(cd.startswith("tk:c:") for cd in cds) \
        and any(cd.startswith("tk:p:") for cd in cds), cds


def t_c8_menu_and_start_are_never_swallowed_by_the_owner_console():
    """outer-bot-4: مامور /menu و /start را قبل از جدولِ فرمان می‌بلعید —
    فرمانِ #۱ ِ تبلیغ‌شده هرگز به _page('menu') نمی‌رسید. حتی مامورِ
    همه‌چیزخوار هم نباید فرمانِ جدولِ مرکز را بگیرد."""
    import types as _types
    _reset()
    fake_pkg = _types.ModuleType("owner_console")
    fake_ad = _types.ModuleType("owner_console.telegram_adapter")
    fake_ad.handle_callback = lambda data, surface_decision=None: {"handled": False}
    fake_ad.handle_message = lambda text, surface_decision=None: {
        "handled": True, "reply": {"kind": "answer", "text": "CONSOLE-ATE-IT"}}
    fake_pkg.telegram_adapter = fake_ad
    old_pkg = sys.modules.get("owner_console")
    old_ad = sys.modules.get("owner_console.telegram_adapter")
    sys.modules["owner_console"] = fake_pkg
    sys.modules["owner_console.telegram_adapter"] = fake_ad
    try:
        fc = FakeClient(owner_id=777)
        fc.owner_chat_id = 777
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
        for cmd in ("/menu", "/start"):
            fc.calls.clear()
            res = c.handle_update({"update_id": 30, "message": {
                "from": {"id": 777}, "text": cmd,
                "chat": {"id": 777, "type": "private"}}})
            assert res and res.get("kind") != "owner-console", (cmd, res)
            sent = fc.named("send")
            assert sent and "CONSOLE-ATE-IT" not in sent[-1]["text"], \
                f"{cmd} را مامور بلعید — به جدولِ فرمان نرسید"
        # و متنِ آزادِ غیرفرمان همچنان به مامور می‌رسد (ضدِ بیش‌بست)
        fc.calls.clear()
        res = c.handle_update({"update_id": 31, "message": {
            "from": {"id": 777}, "text": "یک متنِ آزادِ ماموری",
            "chat": {"id": 777, "type": "private"}}})
        assert res and res.get("kind") == "owner-console", res
    finally:
        for name, old in (("owner_console", old_pkg),
                          ("owner_console.telegram_adapter", old_ad)):
            if old is not None:
                sys.modules[name] = old
            else:
                sys.modules.pop(name, None)


def t_c9_home_taps_edit_the_same_message_instead_of_sending_new_ones():
    """منشور §۶.۲/§۶.۳: hm: زنجیرهٔ پیامِ نو نمی‌سازد — همان پیام ویرایش
    می‌شود و راهِ برگشت hm:home است (عمق ≤۲). زنجیرهٔ سه‌پیامیِ
    st→build→bq مُرد."""
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    c.ensure_setup()
    for verb in ("hm:st", "hm:legs", "hm:held", "hm:home"):
        fc.calls.clear()
        res = c.handle_update({"update_id": 32, "callback_query": {
            "id": f"cb-{verb}", "from": {"id": 777}, "data": verb,
            "message": {"message_id": 444,
                        "chat": {"id": 777, "type": "private"}}}})
        assert res and res.get("kind") == "home", (verb, res)
        edits = fc.named("edit")
        assert edits and edits[-1]["message_id"] == 444, \
            f"{verb} پیامِ خانه را ویرایش نکرد"
        assert fc.named("send") == [], \
            f"{verb} هنوز پیامِ نو می‌فرستد — منوی تو در تو برگشت"
        assert fc.named("answer"), f"{verb} بدونِ answer"


def t_d_decisions_posted_once_with_keyboard_dedupe_seen():
    _reset()
    items = [{"q": "یک تصمیم؟", "why": "w", "source": "approval", "priority": "high"}]
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render(items))
    c.ensure_setup()
    fc.calls.clear()
    assert c.beat()["decisions"] == 1
    # ۲۰۲۶-۰۷-۳۰: فیلترِ قبلی «هر sendِ کیبورددار» بود و «یک‌بار پست شد» را با
    # همان پروکسی می‌سنجید. از امروز beat کارتِ زندهٔ پا را هم می‌فرستد (که
    # کیبوردِ tk: دارد)، پس پروکسی بی‌دقت شد — نه ناوردیْ نقض. فیلتر دقیق شد و
    # در عوض بندِ تازه‌ای اضافه شد که **قوی‌تر** است: هر sendِ کیبورددارِ دیگر
    # باید اثباتاً کارتِ پا باشد، پس یک sendِ ناخواستهٔ سوم هم قرمز می‌کند.
    def _cb(s):
        return str((s["keyboard"] or [[{}]])[0][0].get("callback_data", ""))
    kbd = [s for s in fc.named("send") if s["keyboard"]]
    dec = [s for s in kbd if _cb(s).startswith("ok:")]
    assert len(dec) == 1
    assert dec[0]["keyboard"][0][0]["callback_data"].startswith("ok:")
    assert all(_cb(s).startswith("tk:") for s in kbd if s not in dec), \
        [_cb(s) for s in kbd if s not in dec]
    assert c.beat()["decisions"] == 0                   # dedupe با seen در config
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert len(cfg.get("seen", [])) == 1


def t_e_callback_from_non_owner_ignored():
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 5,
         "callback_query": {"id": "cb1", "from": {"id": 666}, "data": "ok:dec-1"}}
    assert c.handle_update(u) is None                   # سکوتِ کامل
    assert len(fc.named("answer")) == 0
    assert not (APPROVALS / "dec-1.json").exists()


def t_f_ok_callback_records_file_mints_token_and_answers():
    _reset()
    os.environ["HH_HUMAN_GUARD_SECRET"] = "test-secret-123"
    try:
        fc = FakeClient(owner_id=777)
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
        u = {"update_id": 6,
             "callback_query": {"id": "cb2", "from": {"id": 777}, "data": "ok:dec-2"}}
        res = c.handle_update(u)
        assert res and res["verdict"] == "ok" and res["recorded"] is True
        rec = json.loads((APPROVALS / "dec-2.json").read_text("utf-8"))
        assert rec["verdict"] == "ok" and rec.get("ha_token")
        # توکن واقعاً با همان راز معتبر است (mint → authorize)
        from human_append_guard import HumanAppendGuard
        g = HumanAppendGuard(b"test-secret-123")
        ok, reason = g.authorize("APPROVAL", True, token=rec["ha_token"])
        assert ok is True, reason
        answers = fc.named("answer")
        assert len(answers) == 1 and answers[0]["id"] == "cb2"
    finally:
        os.environ.pop("HH_HUMAN_GUARD_SECRET", None)


def t_g_ok_without_secret_records_without_token_no_crash():
    _reset()
    os.environ.pop("HH_HUMAN_GUARD_SECRET", None)
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 7,
         "callback_query": {"id": "cb3", "from": {"id": 777}, "data": "no:dec-3"}}
    res = c.handle_update(u)
    assert res and res["verdict"] == "no" and res["recorded"] is True
    rec = json.loads((APPROVALS / "dec-3.json").read_text("utf-8"))
    assert rec["verdict"] == "no" and "ha_token" not in rec
    assert len(fc.named("answer")) == 1


def t_h_now_command_sends_status():
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 8,
         "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "/now"}}
    res = c.handle_update(u)
    assert res and res["kind"] == "now" and res["sent"] is True
    assert fc.named("send")[-1]["text"] == "STATUS-LINE"


def t_i_run_once_dispatches_and_advances_offset():
    _reset()
    fc = FakeClient(owner_id=777)
    fc.updates = [
        {"update_id": 41,
         "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "/now"}},
        {"update_id": 42,
         "callback_query": {"id": "c9", "from": {"id": 777}, "data": "later:dec-9"}},
    ]
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    assert c.run_once() == 2
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert cfg["last_offset"] == 43                     # restart-safe
    assert len(fc.named("answer")) == 1                 # callback جواب گرفت
    rec = json.loads((APPROVALS / "dec-9.json").read_text("utf-8"))
    assert rec["verdict"] == "later"


def t_j_stop_file_halts_run_loop():
    _reset()
    center.STOP_TG_CENTER.parent.mkdir(parents=True, exist_ok=True)
    center.STOP_TG_CENTER.write_text("halt", "utf-8")
    try:
        fc = FakeClient(owner_id=777)
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
        c.run_forever()                                 # باید فوراً برگردد
        assert fc.calls == []                           # حتی ensure_setup هم اجرا نشد
        assert c.run_once() == 0                        # run_once هم تسلیمِ STOP است
        assert len(fc.named("poll")) == 0
    finally:
        center.STOP_TG_CENTER.unlink()


def t_k_zero_effect_when_not_wired():
    _reset()
    fc = FakeClient(wired=False)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    assert c.ensure_setup() is False
    assert c.beat() == {"edited": False, "digests": 0, "decisions": 0}
    assert c.run_once() == 0
    u = {"update_id": 9,
         "callback_query": {"id": "cb", "from": {"id": 777}, "data": "ok:z"}}
    assert c.handle_update(u) is None
    c.run_forever()
    assert fc.calls == []                               # صفر فراخوانِ client
    assert not (opslib.STATE_DIR / "telegram").exists()  # صفر نوشتنِ state


def t_l_missing_client_module_is_safe_noop():
    """client=None و tg_api غایب → Center بدونِ crash می‌سازد و همه‌چیز no-op است."""
    _reset()
    c = center.Center(clock=Clock(), render_mod=fake_render())
    assert c.wired() is False
    assert c.ensure_setup() is False
    assert c.beat()["digests"] == 0
    assert c.run_once() == 0


def t_m_free_text_status_routes_to_live_page_with_keyboard():
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 10,
         "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "وضعیت الان چطوره؟"}}
    res = c.handle_update(u)
    assert res and res["kind"] == "ask_status" and res["sent"] is True
    sent = fc.named("send")[-1]
    assert sent["text"] == "STATUS-LINE"
    assert sent["keyboard"] and sent["keyboard"][0][0]["callback_data"] == "mn:st"


def t_n_free_text_pause_builds_action_button_not_direct_execute():
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 11,
         "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "لید رو مکث کن"}}
    res = c.handle_update(u)
    assert res and res["kind"] == "ask_pause" and res["sent"] is True
    sent = fc.named("send")[-1]
    cds = [b["callback_data"] for row in sent["keyboard"] for b in row]
    assert "lg:lead:p" in cds
    # هنوز callback زده نشده؛ پس فقط پیشنهاد/دکمه بوده، نه اجرای مستقیم.
    assert not (opslib.STATE_DIR / "leg-lead-paused.flag").exists()


def t_o_free_text_scan_routes_to_map_page():
    """فاز C/D: «نقشه بکش» → صفحهٔ نقشه‌برداری با دکمهٔ map:start (نه اجرای مستقیم)."""
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 12,
         "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "نقشه بکش"}}
    res = c.handle_update(u)
    assert res and res["kind"] == "ask_scan_metadata" and res["sent"] is True


def t_p_menu_has_map_and_approvals_buttons():
    """فاز B/E + Mission: منوی اصلی دکمه‌های mn:map/mn:ap/mn:ms را دارد."""
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 13, "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "/menu"}}
    c.handle_update(u)
    sent = fc.named("send")[-1]
    flat = [b["callback_data"] for row in sent["keyboard"] for b in row]
    assert "mn:ms" in flat


def t_q_nonowner_map_and_ap_silenced():
    """فاز D/E/Mission: غیرمالک هیچ اثری روی map:* و ap:* و ms:* ندارد (allowlist)."""
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    # map:start از غیرمالک
    u = {"update_id": 14, "callback_query": {"id": "c1", "from": {"id": 666},
          "data": "map:start", "message": {"message_id": 1, "chat": {"id": -1}}}}
    assert c.handle_update(u) is None
    # ap:ok از غیرمالک
    u2 = {"update_id": 15, "callback_query": {"id": "c2", "from": {"id": 666},
          "data": "ap:ok:job-x", "message": {"message_id": 1, "chat": {"id": -1}}}}
    assert c.handle_update(u2) is None
    # ms:approve از غیرمالک
    u3 = {"update_id": 16, "callback_query": {"id": "c3", "from": {"id": 666},
          "data": "ms:approve:M-x", "message": {"message_id": 1, "chat": {"id": -1}}}}
    assert c.handle_update(u3) is None
    assert fc.calls == [], "غیرمالک = سکوتِ مطلق"


def t_r_map_start_runs_scan_and_writes_manifest_e2e():
    """فاز D (e2e): map:start از مالک → scan واقعی + manifest + state نوشته می‌شود.

    sandbox را به مسیرِ خالی هدایت می‌کنیم تا روی F:\backup ننویسد؛ آنجا چند فایل
    می‌سازیم تا scan چیزی برای شمردن داشته باشد."""
    _redirect_octopus_paths()
    # ساختِ چند فایلِ آزمایشی در sandbox
    (_E2E_SANDBOX / "sample.txt").write_text("hello", "utf-8")
    (_E2E_SANDBOX / "data").mkdir()
    (_E2E_SANDBOX / "data" / "x.json").write_text("{}", "utf-8")
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 16, "callback_query": {"id": "c1", "from": {"id": 777},
          "data": "map:start", "message": {"message_id": 1, "chat": {"id": -1}}}}
    res = c.handle_update(u)
    assert res and res["kind"] == "map" and res["action"] == "start"
    # manifest ساخته شده
    assert aps._APPROVALS_JSON.parent.exists()
    st = ms.load_state()
    assert st["status"] == "done" and st["files_seen"] >= 2
    # یک job هم در صف تأیید ثبت شده (برای بازبینی)
    assert len(aps.load_pending()) >= 1
    # paths را به sandboxِ پیش‌فرض برای تست‌های بعدی برگردان
    _redirect_octopus_paths()


def t_s_ap_ok_approves_job_and_writes_legacy_verdict_e2e():
    """فاز E (e2e): یک job اضافه، ap:ok از مالک → approve + legacy verdict."""
    _redirect_octopus_paths()
    jid = aps.add_pending({"type": "metadata_scan", "title": "test", "risk": "read"})
    assert len(aps.load_pending()) == 1
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 17, "callback_query": {"id": "c1", "from": {"id": 777},
          "data": f"ap:ok:{jid}", "message": {"message_id": 1, "chat": {"id": -1}}}}
    res = c.handle_update(u)
    assert res and res["kind"] == "approval" and res["action"] == "ok" and res["ok"] is True
    # job از pending به approved رفته
    assert len(aps.load_pending()) == 0
    assert aps.summary()["approved"] == 1
    # legacy verdict هم نوشته شده
    assert (aps._LEGACY_DIR / f"{jid}.json").exists()


def t_t_ap_detail_shows_content_free_card_e2e():
    """فاز E (e2e): ap:detail:id → کارتِ جزئیات بدونِ نشتِ محتوا."""
    _redirect_octopus_paths()
    jid = aps.add_pending({"type": "scan", "title": "test title", "risk": "high"})
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 18, "callback_query": {"id": "c1", "from": {"id": 777},
          "data": f"ap:detail:{jid}", "message": {"message_id": 1, "chat": {"id": -1}}}}
    res = c.handle_update(u)
    assert res and res["kind"] == "approval" and res["action"] == "detail"
    # edit صدا زده شده با متنِ جزئیات
    edits = fc.named("edit")
    assert edits and "جزئیات" in edits[-1]["text"]


def t_u_free_text_code_request_creates_mission_not_unknown():
    """Mission Genome: درخواست کدنویسی از متن آزاد → Mission + کارت action/approval، نه منوی unknown."""
    _redirect_octopus_paths()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 19,
         "message": {"from": {"id": 777}, "chat": {"id": 777},
                     "text": "اختاپوس، منوی تلگرامو بهتر کن و callbackها رو درست کن"}}
    res = c.handle_update(u)
    assert res and res["kind"] == "ask_mission" and res["sent"] is True
    mids = mission_mod.list_missions(limit=1)
    assert mids and mids[0]["mission_type"] == "self_coding"
    assert "code.apply" in mids[0]["actions"]
    assert aps.get(mids[0]["id"]) is not None, "mission approval-required باید در unified approval queue هم بیاید"
    sent = fc.named("send")[-1]
    assert "Mission" in sent["text"] and sent["keyboard"]


def t_v_mission_callback_approve_updates_state_e2e():
    """ms:approve فقط verdict mission را ثبت می‌کند و هیچ code.apply واقعی انجام نمی‌دهد."""
    _redirect_octopus_paths()
    m = mission_mod.create_mission("تلگرامو بهتر کن", source="telegram")
    aps.add_pending({"id": m["id"], "type": "mission", "title": "تلگرام", "risk": m["risk"]})
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 20,
         "callback_query": {"id": "c1", "from": {"id": 777},
                            "data": f"ms:approve:{m['id']}",
                            "message": {"message_id": 1, "chat": {"id": -1}}}}
    res = c.handle_update(u)
    assert res and res["kind"] == "mission" and res["action"] == "approve" and res["ok"] is True
    assert mission_mod.get(m["id"])["state"] == "approved"
    assert aps.summary()["approved"] == 1, "approval queue هم باید sync شود"
    assert fc.named("edit"), "کارت باید refresh/edit شود"
    _redirect_octopus_paths()


def t_w_mission_test_flag_off_is_request_only():
    """بدونِ OCTOPUS_WIRE_MISSION_RUNNER: ms:test فقط request ثبت می‌کند، runner اجرا نمی‌شود."""
    _redirect_octopus_paths()
    os.environ.pop("OCTOPUS_WIRE_MISSION_RUNNER", None)
    m = mission_mod.create_mission("تستا رو verify کن", source="telegram")
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
    u = {"update_id": 21,
         "callback_query": {"id": "c2", "from": {"id": 777},
                            "data": f"ms:test:{m['id']}",
                            "message": {"message_id": 1, "chat": {"id": -1}}}}
    res = c.handle_update(u)
    assert res and res["kind"] == "mission" and res["wired"] is False
    fresh = mission_mod.get(m["id"])
    assert fresh["state"] == "planned", "flag-off → فقط planned/awaiting-runner"
    assert fresh["tests"] == [], "هیچ تستِ واقعی نباید ثبت شده باشد"


def t_x_mission_test_flag_on_invokes_runner():
    """با OCTOPUS_WIRE_MISSION_RUNNER=1: ms:test runnerِ v0 را با hookِ تزریقی صدا می‌زند و شواهد ثبت می‌شود."""
    _redirect_octopus_paths()
    m = mission_mod.create_mission("تستا رو verify کن", source="telegram")
    called = {}

    def fake_run(mid, **kw):
        called["mid"] = mid
        mission_mod.record_test(mid, "test_tg_actions.py", True, detail="fake runner green")
        return {"ok": True, "run_id": "run-fake", "results": [], "skipped": []}

    orig = center.runner_mod
    try:
        center.runner_mod = types.SimpleNamespace(run_mission=fake_run)
        os.environ["OCTOPUS_WIRE_MISSION_RUNNER"] = "1"
        fc = FakeClient(owner_id=777)
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render_with_map())
        u = {"update_id": 22,
             "callback_query": {"id": "c3", "from": {"id": 777},
                                "data": f"ms:test:{m['id']}",
                                "message": {"message_id": 1, "chat": {"id": -1}}}}
        res = c.handle_update(u)
        assert res and res["wired"] is True
        assert called.get("mid") == m["id"], "runner باید با mid واقعی صدا زده شود"
        fresh = mission_mod.get(m["id"])
        assert fresh["tests"] and fresh["tests"][-1]["passed"] is True
    finally:
        center.runner_mod = orig
        os.environ.pop("OCTOPUS_WIRE_MISSION_RUNNER", None)
    _redirect_octopus_paths()


def t_center_pulses_every_loop_iteration():
    """نبضِ زنده‌بودنِ مرکز (۲۰۲۶-۰۷-۲۹، رأیِ مالک).

    چرا این گارد لازم است: مرکز تا آن روز هیچ سیگنالِ زنده‌بودنی نمی‌نوشت و
    عصرِ همان روز دو نمونهٔ هم‌زمانش روی یک توکن (pid 23892 + 10096) فقط
    به‌خاطرِ همین پالس دیده شد. اگر کسی فراخوانِ _pulse را از حلقه بردارد،
    آن کوری برمی‌گردد و هیچ تستِ رفتاری‌ای نمی‌گیردش — پس محلِ فراخوان در
    **متنِ منبع** سنجیده می‌شود، نه شکلِ ماژول."""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / 'telegram_center' / 'center.py').read_text(encoding='utf-8', errors='replace')
    body = src[src.index('def run_forever'):src.index('def _pulse')]
    assert 'self._pulse(' in body, 'run_forever دیگر پالس نمی‌زند — مرگِ مرکز نامرئی می‌شود'
    assert 'def _pulse' in src
    # پالس هرگز شناسه/راز ننویسد: فقط ts/pid/mono
    pulse = src[src.index('def _pulse'):]
    pulse = pulse[:pulse.index('os.replace')]
    for bad in ('CHAT_ID', 'TOKEN', 'chat_id', 'token'):
        assert bad not in pulse, f'پالس نباید {bad} بنویسد'


def t_center_has_a_real_singleton_lock():
    """قفلِ تک‌نمونه (۲۰۲۶-۰۷-۲۹، رأیِ مالک).

    شبِ همان روز دو مرکز هم‌زمان روی یک توکن زنده بودند (pid 23892 یتیم +
    10096) — چون بر خلافِ organism/cortex/live که bindِ پورت mutex مجانی
    می‌دهد، مرکز poller است و هیچ قفلی نداشت. این تست هم رفتار را می‌سنجد هم
    محلِ فراخوان را، چون هیچ‌کدام تنها کافی نیست."""
    P = 8901
    s1, w1 = center.acquire_singleton(P)
    assert s1 is not None and w1 is None, f'قفلِ اول باید بگیرد: {w1}'
    try:
        s2, w2 = center.acquire_singleton(P)
        assert s2 is None and w2 == 'in-use', f'نمونهٔ دوم باید رد شود: {w2}'
    finally:
        s1.close()
    s3, w3 = center.acquire_singleton(P)
    assert s3 is not None, f'بعد از آزادشدن باید دوباره قفل شود: {w3}'
    s3.close()
    # قفلِ تستی هرگز نباید ارجاعِ سراسری را بگیرد (وگرنه پروسهٔ واقعی گیر می‌کند)
    assert center._SINGLETON_SOCK is None

    src = (pathlib.Path(__file__).resolve().parents[1]
           / 'telegram_center' / 'center.py').read_text(encoding='utf-8', errors='replace')
    main = src[src.index('if __name__ == "__main__":'):]
    assert 'acquire_singleton()' in main, 'قفل در مسیرِ بوت صدا زده نمی‌شود'
    assert main.index('acquire_singleton()') < main.index('c.run_forever()'),         'قفل باید پیش از حلقه گرفته شود'
    # تلهٔ ویندوز: SO_REUSEADDR اجازهٔ double-bindِ ساکت می‌دهد و قفل را بی‌اثر می‌کند
    fn = src[src.index('def acquire_singleton'):]
    fn = fn[:fn.index('return s, None')]
    assert 'SO_REUSEADDR' not in fn, 'SO_REUSEADDR قفل را روی ویندوز بی‌اثر می‌کند'
    assert 'SO_EXCLUSIVEADDRUSE' in fn


def t_inner_client_built_from_telegram_bot_token():
    """آیتم ۲ِ TG-P2: کلاینتِ inner فقط-ارسال روی TELEGRAM_BOT_TOKEN ساخته می‌شود.

    قاعدهٔ ۲ِ TG-SPLIT: هیچ pollerِ نو. کلاینتِ inner هرگز getUpdates نمی‌زند — این
    تست فقط تأیید می‌کند که ساخته می‌شود و wired است، و post_fn/owner/center را از
    outer به ارث می‌برد."""
    _reset()
    os.environ["TELEGRAM_BOT_TOKEN"] = "inner-tok-987"
    try:
        fc = FakeClient()
        # outer fake باید خصیصه‌های واقعیِ TgClient را داشته باشد تا inner ازشان بخواند
        fc._owner = 777
        fc._center = CENTER
        fc._post = lambda u, b, timeout_s=10.0: {"ok": True, "result": {"message_id": 1}}
        fc._get = lambda u, t: {"ok": True, "result": []}
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
        inner = c._inner_client()
        assert inner is not None, "inner باید ساخته شود وقتی TELEGRAM_BOT_TOKEN هست"
        assert inner.wired() is True
        assert inner._owner == 777 and inner._center == CENTER
        cm = c._clients_map()
        assert cm["inner"] is inner and cm["outer"] is fc
    finally:
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)


def t_inner_missing_when_telegram_bot_token_absent():
    """نبودِ TELEGRAM_BOT_TOKEN → inner=None → surface_router به outer سقوط می‌کند."""
    _reset()
    os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    fc = FakeClient()
    fc._owner = 777
    fc._center = CENTER
    fc._post = lambda u, b, timeout_s=10.0: {"ok": True, "result": {}}
    fc._get = lambda u, t: {"ok": True, "result": []}
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    assert c._inner_client() is None
    assert c._clients_map()["inner"] is None
    assert c._clients_map()["outer"] is fc


def t_set_my_commands_single_writer_even_under_split():
    """W1 (outer-bot-12): مرکز **هرگز** منوی باتِ inner را نمی‌نویسد — حتی با
    فلگِ split روشن. تک-نویسندهٔ منوی inner = approval_channel در پروسهٔ
    organism؛ دو نویسنده با دو فهرست = race ِ بی‌صدا روی setMyCommands."""
    _reset()
    os.environ["OCTOPUS_TG_SPLIT_V1"] = "1"
    os.environ["TELEGRAM_BOT_TOKEN"] = "inner-tok"
    try:
        outer = FakeClient()
        outer._owner = 777
        outer._center = CENTER
        outer._post = lambda u, b, timeout_s=10.0: {"ok": True, "result": {"message_id": 1}}
        outer._get = lambda u, t: {"ok": True, "result": []}
        c = center.Center(client=outer, clock=Clock(), render_mod=fake_render())
        # inner تزریقی تا هر setMyCommands ِ ناخواسته رویش دیده شود
        inner_fc = FakeClient()
        inner_fc._owner = 777
        inner_fc._center = CENTER
        c._inner = inner_fc
        assert c.ensure_setup() is True
        outer_cmds = outer.named("set_commands")
        assert len(outer_cmds) == 1
        assert len(outer_cmds[0]["commands"]) == len(center.COMMANDS)
        assert inner_fc.named("set_commands") == [], \
            "مرکز منوی inner را نوشت — تک-نویسندگی نقض شد"
        assert inner_fc.named("delete_commands") == [], \
            "مرکز منوی inner را پاک کرد — آن بات مالِ approval_channel است"
    finally:
        os.environ.pop("OCTOPUS_TG_SPLIT_V1", None)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)


def t_flag_off_never_sets_inner_commands():
    """flag-off → inner اصلاً commands نمی‌گیرد (پاریتیِ تک-outerِ امروز بایت‌به‌بایت)."""
    _reset()
    os.environ.pop("OCTOPUS_TG_SPLIT_V1", None)
    outer = FakeClient()
    outer._owner = 777
    outer._center = CENTER
    outer._post = lambda u, b, timeout_s=10.0: {"ok": True, "result": {"message_id": 1}}
    outer._get = lambda u, t: {"ok": True, "result": []}
    c = center.Center(client=outer, clock=Clock(), render_mod=fake_render())
    inner_fc = FakeClient()
    c._inner = inner_fc
    assert c.ensure_setup() is True
    assert len(outer.named("set_commands")) == 1          # outer همان امروز
    assert len(inner_fc.named("set_commands")) == 0, "flag-off نباید inner را ثبت کند"

def t_c10_save_config_retries_transient_locks_and_is_loud_when_permanent():
    """W1 ِ دیباگِ ۰۷-۳۱: این فایل هر نشانگر/cursor/شناسهٔ کارت را نگه می‌دارد.
    قفلِ گذرای AV نباید بی‌صدا آن‌ها را ببلعد؛ شکستِ دائمی باید صدا کند."""
    import center as _c
    calls = {"n": 0}
    real_replace = _c.os.replace
    real_sleep = _c.time.sleep
    real_alert = _c.opslib.alert

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] <= 2:                      # دو قفلِ گذرا، بعد موفق
            raise PermissionError("[Errno 13] simulated AV lock")
        return real_replace(src, dst)

    slept = []
    _c.os.replace = flaky
    _c.time.sleep = lambda s: slept.append(s)
    try:
        assert _c._save_config({"probe": "transient"}) is True, "قفلِ گذرا جذب نشد"
        assert calls["n"] == 3 and slept, (calls, slept)
    finally:
        _c.os.replace = real_replace
        _c.time.sleep = real_sleep

    alerts = []

    def _boom(*_a, **_k):
        raise PermissionError("permanent")

    _c.os.replace = _boom
    _c.time.sleep = lambda s: None
    _c.opslib.alert = lambda lines: alerts.append(list(lines))
    try:
        assert _c._save_config({"probe": "permanent"}) is False, "شکستِ دائمی True داد"
        assert alerts and any("center-config" in " ".join(a) for a in alerts), alerts
    finally:
        _c.os.replace = real_replace
        _c.time.sleep = real_sleep
        _c.opslib.alert = real_alert



if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_center: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
