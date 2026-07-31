"""test_discoveries.py — لایهٔ «کشف و یادگیریِ دیدنی» (جلسه ۴۶).

رأی مالک: «الان یادگیری نداره ... کشف و نوتیف به من نداره.»
- discoveries: record/recent/unseen/mark_seen، بی‌محتوا، $0.
- web_research: fallback topics (یادگیری حتی بدونِ گپِ مدرسه) + ثبتِ کشف.
- خانهٔ ساده: خطِ «چی یاد گرفتم» + دکمه؛ menu:learned لیست را می‌دهد و seen می‌کند.
- discovery_nudge_beat: نوتیفِ ملایم فقط وقتی کشفِ تازه باشد، پشتِ پرچم + kill-switch.
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("discoveries")

import discoveries as disc   # noqa: E402
import web_research as wr    # noqa: E402


def t_a_record_recent_unseen_seen():
    disc.record("research", "دربارهٔ X تحقیق کردم — ۳ نتیجه")
    disc.record("idea", "یه ایده برای بهترشدن: کمترکردنِ خطا")
    assert disc.unseen_count() == 2
    r = disc.recent(5)
    assert len(r) == 2 and r[0]["kind"] == "idea"   # جدیدترین اول
    ls = disc.lines(5)
    assert any("🔍" in x for x in ls) and any("💡" in x for x in ls)
    disc.mark_seen()
    assert disc.unseen_count() == 0
    disc.record("learn", "یه چیزِ نو")
    assert disc.unseen_count() == 1


def t_b_web_research_fallback_topics_always_learn():
    """گپِ خالی → موضوع‌های پیش‌فرض؛ یادگیری هیچ‌وقت نمی‌ایستد."""
    tp = wr.fallback_topics(beat=0, k=3)
    assert len(tp) == 3 and all(isinstance(t, str) for t in tp)
    assert wr.fallback_topics(beat=1)[0] != wr.fallback_topics(beat=0)[0]  # چرخش


def t_c_web_research_records_discovery():
    os.environ[wr.FLAG_ENV] = "1"

    # ۲۰۲۶-۰۷-۲۸ — stub حالا عنوانی می‌دهد که به **همان کوئری** ربط دارد.
    #
    # نسخهٔ قبلی برای هر موضوعی «Neural network» برمی‌گرداند. از وقتی
    # `web_research._relevant()` نتیجهٔ بی‌ربط را دور می‌ریزد (گاردِ همان روز:
    # کوئری «perception bias» → «Perceptual hashing» فقط هم‌پیشوند بود و
    # «چیزی که یاد گرفتم» نامیده می‌شد)، این stub صفر نتیجه می‌داد و هیچ کشفی
    # ثبت نمی‌شد. موضوع‌های fallback «reinforcement learning» و
    # «vector memory databases»‌اند — هیچ واژهٔ مشترکی با «Neural network».
    #
    # این تست **سیم‌کشی** را می‌سنجد نه ربط را، پس stub باید مثلِ یک موتورِ
    # واقعی رفتار کند: عنوانی هم‌واژه با پرسش. ضعیف‌کردنِ گارد برای سبزکردنِ
    # تست، همان کاری است که قاعدهٔ این مخزن ممنوع کرده.
    def _q(url):
        import urllib.parse as _up
        qs = _up.parse_qs(_up.urlparse(url).query)
        raw = (qs.get("search") or qs.get("q") or [""])[0]
        return _up.unquote_plus(raw) or "reinforcement learning"

    def fake(url):
        if "opensearch" in url:
            t = _q(url).title()
            return json.dumps(["q", [t], [""], ["u"]])
        if "rest_v1/page/summary" in url:
            title = _up_title(url)
            return json.dumps({"title": title, "extract": "a model"})
        return ""

    def _up_title(url):
        import urllib.parse as _up
        return _up.unquote(url.rsplit("/", 1)[-1]).replace("_", " ")
    try:
        before = disc.unseen_count()
        r = wr.run_and_persist([], opener=fake, beat=2)   # خالی → fallback
        assert r["ok"] is True
        assert disc.unseen_count() > before   # یک کشفِ تازه ثبت شد
        assert any("تحقیق کردم" in x for x in disc.lines(3))
    finally:
        os.environ.pop(wr.FLAG_ENV, None)


def t_d_home_shows_learning_and_view():
    import approval_channel as ac
    ch = ac.TelegramApprovalChannel(token="1:x", owner_chat_id=1,
                                    http_get=lambda *a, **k: {"ok": True, "result": []},
                                    http_post=lambda *a, **k: {"ok": True})
    disc.mark_seen()
    disc.record("learn", "یه چیزِ تازه یاد گرفتم")
    home = ch._main_menu()
    assert "یاد گرفتم" in home["text"]
    kb = json.dumps(home["reply_markup"], ensure_ascii=False)
    assert "menu:learned" in kb
    # دیدن → seen صفر می‌شود
    view = ch.dispatch_callback("menu:learned")
    assert isinstance(view, dict) and "چی یاد گرفتم" in view["text"]
    assert disc.unseen_count() == 0


def t_e_discovery_nudge_only_on_new_and_gated():
    import wiring
    sent_box = {}

    class _Chan:
        wired = True
        def send_text(self, text, kb=None):
            sent_box["text"] = text
            return True
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    try:
        disc.mark_seen()   # هیچ کشفِ تازه → نباید بفرستد
        r0 = wiring.discovery_nudge_beat(_Chan(), beat=480)
        assert r0["sent"] is False
        disc.record("research", "یه کشفِ تازه")
        wiring._DISCOVERY_STATE["last_epoch"] = -1   # ریست epoch برای تست
        r1 = wiring.discovery_nudge_beat(_Chan(), beat=960)
        assert r1["sent"] is True and "یاد گرفتم" in sent_box["text"]
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)


def t_f_discovery_nudge_respects_killswitch():
    import wiring
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    import opslib
    opslib.STOP_ORGANISM.parent.mkdir(parents=True, exist_ok=True)
    opslib.STOP_ORGANISM.write_text("stop", "utf-8")
    try:
        assert wiring.discovery_nudge_beat(None, beat=480) is None
    finally:
        opslib.STOP_ORGANISM.unlink()
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)


def _iso_discovery_files():
    """snapshot/restore سه فایلِ کشف — تستِ من نباید حالتِ تستِ دیگر را بشوید.

    اولین نسخهٔ این تست‌ها فایل‌ها را پاک می‌کرد و چون الفبایی جلوتر بود،
    `t_a_record_recent_unseen_seen` را می‌شکست. تستِ وابسته به ترتیب همان
    بیماریِ «نتیجه‌ای که به چیزی نگفته وابسته است» در لباسِ کندتر است."""
    import discoveries as d
    saved = {}
    for f in (d.LOG, d.SEEN, d.NUDGED):
        saved[f] = f.read_bytes() if f.exists() else None
        if f.exists():
            f.unlink()
    return saved


def _restore_discovery_files(saved, epoch=None):
    """فایل‌ها **و** حالتِ ماژول را برگردان.

    نسخهٔ دوم هم ناقص بود: فایل‌ها را برمی‌گرداند ولی
    `wiring._DISCOVERY_STATE["last_epoch"]` را نه — و همان باعث شد
    `t_e_discovery_nudge_only_on_new_and_gated` با beatِ یکسان زودتر برگردد و
    None بدهد. حالتِ ماژول هم حالتِ مشترک است."""
    if epoch is not None:
        try:
            import wiring as _w
            _w._DISCOVERY_STATE["last_epoch"] = epoch
        except Exception:  # noqa: BLE001
            pass
    for f, blob in saved.items():
        if blob is None:
            if f.exists():
                f.unlink()
        else:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(blob)


# ─── «به تو گفتم» ≠ «تو نگاه کردی» (2026-07-26) ─────────────────────────────
def t_nudge_marker_is_separate_from_the_seen_marker():
    """`mark_seen` تنها از کلیکِ دکمه صدا زده می‌شود (تنها فراخوانش در
    approval_channel است). پس بدونِ کلیک، `unseen_count` بی‌نهایت رشد می‌کند و
    همان انبار دوباره اعلام می‌شود. اندازه‌گیریِ زنده ۲۰۲۶-۰۷-۲۶: نشانگر از
    ۲۰۲۶-۰۷-۱۹ تکان نخورده بود و شمارنده روی ۱۰ بود."""
    import discoveries as d
    saved = _iso_discovery_files()
    try:
        d.record("learn", "الف")
        d.record("learn", "ب")
        assert d.unseen_count() == 2 and d.unseen_since_nudge() == 2
        d.mark_nudged()
        assert d.unseen_since_nudge() == 0, "بعد از خبر دادن باید صفر شود"
        assert d.unseen_count() == 2, "کلیکِ مالک نیامده — SEEN نباید تکان بخورد"
        d.record("learn", "ج")
        assert d.unseen_since_nudge() == 1, "فقط کشفِ تازه باید شمرده شود"
        assert d.unseen_count() == 3
        d.mark_seen()
        assert d.unseen_count() == 0, "کلیک باید SEEN را جلو ببرد"
    finally:
        _restore_discovery_files(saved)


def t_delta_flag_off_keeps_todays_behaviour():
    import discoveries as d
    import wiring
    saved = _iso_discovery_files()
    _epoch0 = wiring._DISCOVERY_STATE["last_epoch"]
    d.record("learn", "الف")
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    os.environ.pop("OCTOPUS_DISCOVERY_NUDGE_DELTA", None)
    try:
        wiring._DISCOVERY_STATE["last_epoch"] = 0
        r = wiring.discovery_nudge_beat(None, beat=480)
        assert r and r["delta_mode"] is False and r["n"] == 1, r
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)
        _restore_discovery_files(saved, epoch=_epoch0)


def t_a_failed_nudge_does_not_bury_the_backlog():
    """علامتِ «خبر دادم» فقط بعد از ارسالِ موفق — وگرنه یک نوتیفِ نرسیده برای
    همیشه دفن می‌شود، همان الگویی که کارتِ C6 را یک شبانه‌روز پنهان کرد."""
    import discoveries as d
    import wiring

    class Dead:
        wired = True

        def send_text(self, text, reply_markup=None, chat_id=None, stream=None):
            return False

    saved = _iso_discovery_files()
    _epoch0 = wiring._DISCOVERY_STATE["last_epoch"]
    d.record("learn", "الف")
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    os.environ["OCTOPUS_DISCOVERY_NUDGE_DELTA"] = "1"
    try:
        wiring._DISCOVERY_STATE["last_epoch"] = 0
        r = wiring.discovery_nudge_beat(Dead(), beat=480)
        assert r and r["sent"] is False, r
        assert not d.NUDGED.exists(), "ارسالِ ناموفق نباید نشانگر را جلو ببرد"
        assert d.unseen_since_nudge() == 1, "بک‌لاگ باید سرِ جایش بماند"
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)
        os.environ.pop("OCTOPUS_DISCOVERY_NUDGE_DELTA", None)
        _restore_discovery_files(saved, epoch=_epoch0)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_discoveries: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
