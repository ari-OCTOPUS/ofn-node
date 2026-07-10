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

    def fake(url):
        if "opensearch" in url:
            return json.dumps(["q", ["Neural network"], [""], ["u"]])
        if "rest_v1/page/summary" in url:
            return json.dumps({"title": "Neural network", "extract": "a model"})
        return ""
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


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_discoveries: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
