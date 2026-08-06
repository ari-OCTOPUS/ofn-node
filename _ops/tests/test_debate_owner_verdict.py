#!/usr/bin/env python3
"""WS-E — رأیِ مالک روی مناظره: پایدار، عواقب‌دار، و قابلِ لمس.

سه چیز را می‌سنجد و هر سه قبلاً غایب بودند:
  ۱. ایدهٔ **ردشده** دوباره صف نمی‌شود (تا امروز می‌شد — تنها حافظه، فایلِ md بود).
  ۲. هر callback_data ِ روی کارت به یک handlerِ **واقعی** می‌رسد و شناسه‌اش همان
     شناسه‌ای است که آن handler رویش approve/reject می‌زند.
  ۳. فلگ خاموش = رفتارِ بایت‌به‌بایتِ امروز.

«دندانِ» تست: نسخهٔ پیش‌از‌فیکسِ debate_loop از روی همین فایل بازسازی می‌شود
(string-replace) و نشان داده می‌شود که تستِ ۱ رویش می‌افتد.
"""
import ast
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("debate-owner-verdict")
import opslib        # noqa: E402
import debate_loop   # noqa: E402

os.environ.pop("OCTOPUS_WIRE_DEBATE_LOCAL", None)

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS / "telegram_center"))
import actions as act        # noqa: E402
import approval_store as aps  # noqa: E402
import render                # noqa: E402
import organ_dialogue as od   # noqa: E402

# ── ایزولهٔ approval_store ─────────────────────────────────────────────────────
# مسیرهای این ماژول از __file__ ساخته می‌شوند نه از env، پس harness ایزوله‌شان
# نمی‌کند. بدونِ این چند خط، تست به approvals.json ِ **زنده** می‌نوشت.
_LIVE_APPROVALS = aps._APPROVALS_JSON
_LIVE_STAMP = (_LIVE_APPROVALS.exists(),
               _LIVE_APPROVALS.stat().st_size if _LIVE_APPROVALS.exists() else -1,
               _LIVE_APPROVALS.stat().st_mtime_ns if _LIVE_APPROVALS.exists() else -1)
_SANDBOX = Path(ENV["root"]) / "_octopus"
aps._APPROVALS_JSON = _SANDBOX / "state" / "approvals.json"
aps._AUDIT_PATH = _SANDBOX / "logs" / "audit.log"
# همان مسیری که debate_loop._verdict_dir() می‌خواند — پلِ واقعیِ بینِ دو پروسه
aps._LEGACY_DIR = opslib.STATE_DIR / "telegram" / "approvals"
assert str(aps._APPROVALS_JSON).startswith(str(ENV["root"])), "صفِ تأیید ایزوله نشد"
assert aps._LEGACY_DIR == debate_loop._verdict_dir(), "پلِ verdict بینِ دو پروسه نمی‌خواند"

TOPIC = {"id": "seed-2", "source": "SEED_TOPICS", "text": "موضوعِ آزمایشی"}
MUSE = {"idea": "پروکسیِ ارزشِ per-organ از APPROVALهای sent", "why_genius": "g",
        "why_insane": "i", "est_tokens": 10, "quality_bar": "normal",
        "epistemic_tag": "SPEC"}
ARCH = {"verdict": "pass", "kill_condition": "k", "cheapest_test": "c",
        "epistemic_tag": "SPEC"}
SIG = debate_loop.survivor_sig(TOPIC["id"], MUSE["idea"])
JID = debate_loop.survivor_job_id(SIG)


def _reset_queue() -> None:
    """فایلِ md را پاک می‌کند تا گاردِ `sig:` هرگز **دلیلِ** رد شدن نباشد."""
    if debate_loop.QUEUE_MD.exists():
        debate_loop.QUEUE_MD.unlink()


def _reset_store() -> None:
    if aps._APPROVALS_JSON.exists():
        aps._APPROVALS_JSON.unlink()
    if debate_loop.PENDING_JSONL.exists():
        debate_loop.PENDING_JSONL.unlink()
    vdir = debate_loop._verdict_dir()
    if vdir.exists():
        for f in vdir.glob("dbt-*.json"):
            f.unlink()


def _owner_taps(jid: str, verb: str) -> None:
    """دقیقاً کاری که `center._handle_approval_callback` بعد از تپِ مالک می‌کند:
    انتقال در صف + نوشتنِ فایلِ per-decision. حلقهٔ مناظره دومی را می‌خواند."""
    moved = aps.approve(jid) if verb == "ok" else aps.reject(jid)
    assert moved is True, f"jobِ {jid} در صفِ pending نبود"
    assert aps.record_legacy_verdict(jid, verb) is True


def _q_rows() -> int:
    if not debate_loop.QUEUE_MD.exists():
        return 0
    return len(re.findall(r"^## .+ · sig:", debate_loop.QUEUE_MD.read_text("utf-8"), re.M))


def _prefix_module():
    """نسخهٔ پیش‌از‌فیکس: دو بلوکِ WS-E از منبع حذف و ماژول جدا لود می‌شود."""
    src = Path(debate_loop.__file__).read_text("utf-8")
    a = ("    if _verdict_on() and owner_verdict_for(_sig) in _DECIDED:\n"
         "        return False                      # مالک رأی داده — دوباره نپرس\n")
    b = ("    if _verdict_on():\n"
         "        _publish_survivor(_sig, topic, muse, status)\n")
    assert a in src and b in src, "منبع عوض شده — بازسازیِ پیش‌از‌فیکس نامعتبر است"
    old = src.replace(a, "").replace(b, "")
    p = Path(ENV["root"]) / "_prefix_debate_loop.py"
    p.write_text(old, "utf-8")
    spec = importlib.util.spec_from_file_location("prefix_debate_loop", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ═══ ۱. رأیِ «نه» عواقب دارد ══════════════════════════════════════════════════
def t_rejected_idea_is_not_requeued():
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    _reset_store()
    _reset_queue()
    # دورِ اول: ایده صف می‌شود و پروژکشن برای مرکز منتشر می‌شود
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is True
    assert _q_rows() == 1, _q_rows()
    assert debate_loop.PENDING_JSONL.exists(), "پروژکشنی برای مرکز منتشر نشد"
    # سمتِ مرکز (پروسهٔ دوم): پروژکشن → jobِ واقعیِ دکمه‌دار
    rows = render.ingest_debate_survivors()
    job = aps.get(JID)
    assert isinstance(job, dict) and job["status"] == "pending", job
    assert job["type"] == "debate" and job["title"] == MUSE["idea"], job
    assert [r["id"] for r in rows] == [JID], rows
    assert debate_loop.owner_verdict_for(SIG) == "", "هنوز رأیی نیامده"

    # مالک ❌ می‌زند — دقیقاً همان چیزی که center._handle_approval_callback می‌کند
    _owner_taps(JID, "no")
    assert debate_loop.owner_verdict_for(SIG) == "rejected"

    # دورِ بعد: فایلِ md پاک است، پس تنها دلیلِ ممکنِ رد شدن، خودِ رأی است
    _reset_queue()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is False, \
        "ایدهٔ ردشده دوباره صف شد — رأیِ مالک بی‌اثر است"
    assert _q_rows() == 0, "ردیفِ md نوشته شد با اینکه ایده رد شده بود"
    assert aps.get(JID)["status"] == "rejected", "رأی بازنویسی شد"


def t_approved_idea_is_not_requeued_either():
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    _reset_store()
    _reset_queue()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is True
    render.ingest_debate_survivors()
    _owner_taps(JID, "ok")
    _reset_queue()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is False, \
        "ایدهٔ تأییدشده دوباره پرسیده شد"


def t_a_different_idea_is_still_queued():
    """گاردِ ضدِ over-fitting: رأی به **محتوا** بایند است نه به موضوع."""
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    _reset_store()
    _reset_queue()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is True
    render.ingest_debate_survivors()
    _owner_taps(JID, "no")
    other = dict(MUSE, idea="ایدهٔ کاملاً متفاوت روی همان موضوع")
    os.environ["OCTOPUS_DEBATE_QUEUE_COOLDOWN_H"] = "0"   # کفِ زمانی موضوعِ این تست نیست
    try:
        assert debate_loop._queue_survivor(TOPIC, other, ARCH, "pending-human") is True, \
            "ایدهٔ تازه روی موضوعِ قدیمی نباید با رأیِ قبلی خفه شود"
    finally:
        os.environ.pop("OCTOPUS_DEBATE_QUEUE_COOLDOWN_H", None)


def t_teeth_prefix_code_requeues_a_rejected_idea():
    """دندان: همین سناریو روی کدِ پیش‌از‌فیکس **می‌افتد**."""
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    pre = _prefix_module()
    _reset_store()
    _reset_queue()
    aps.add_pending({"id": JID, "type": "debate", "title": MUSE["idea"], "risk": "medium"})
    _owner_taps(JID, "no")
    assert debate_loop.owner_verdict_for(SIG) == "rejected", "سناریو درست برپا نشد"
    _reset_queue()
    got = pre._queue_survivor(TOPIC, MUSE, ARCH, "pending-human")
    assert got is True, ("کدِ پیش‌از‌فیکس هم رد کرد → تست دندان ندارد "
                         f"(got={got!r})")
    assert _q_rows() == 1, "کدِ پیش‌از‌فیکس باید ردیفِ md را دوباره بنویسد"


# ═══ ۲. هر دکمه به handlerِ واقعی می‌رسد ═════════════════════════════════════
_CENTER_SRC = (_OPS / "telegram_center" / "center.py").read_text("utf-8", errors="replace")
_HANDLED_ACTIONS = ("ok", "no", "detail")


def _card_rows():
    return [{"id": JID, "type": "debate", "title": MUSE["idea"], "risk": "medium",
             "status": "pending"},
            {"id": "dbt-aaaaaaaaaaaa", "type": "debate", "title": "ایدهٔ دوم",
             "risk": "medium", "status": "pending"}]


def t_every_callback_on_the_card_resolves_to_a_real_handler():
    text, kb = render.render_debate_survivors(_card_rows())
    assert text and kb, "کارت خالی درآمد"
    datas = [b["callback_data"] for row in kb for b in row]
    assert len(datas) == 6, datas
    # (الف) فعل به handler مسیر دارد (جدولِ dispatch ِ center، از منبع)
    assert re.search(r'if verb == "ap":\s*\n\s*return self\._handle_approval_callback',
                     _CENTER_SRC), "فعلِ ap در جدولِ dispatch نیست"
    body = _CENTER_SRC.split("def _handle_approval_callback", 1)[1].split("\n    def ", 1)[0]
    for a in _HANDLED_ACTIONS:
        assert f'action == "{a}"' in body, f"اکشنِ {a} در handler اجرا نمی‌شود"
    ids = set()
    for d in datas:
        seg = d.split(":")
        assert seg[0] == "ap", d
        assert seg[1] in _HANDLED_ACTIONS, f"اکشنِ بی‌handler: {d}"
        # (ب) شناسه باید از sanitize ِ خودِ handler دست‌نخورده رد شود، وگرنه
        # aps.get(jid) چیزی پیدا نمی‌کند و دکمه «یافت نشد» می‌دهد.
        assert aps._sanitize_id(seg[2]) == seg[2], f"شناسه بعد از sanitize عوض می‌شود: {d}"
        assert len(d.encode("utf-8")) <= 64, f"از سقفِ ۶۴ بایتِ تلگرام رد شد: {d}"
        ids.add(seg[2])
    assert ids == {JID, "dbt-aaaaaaaaaaaa"}, ids


def t_callback_comes_from_the_registry_not_a_string_literal():
    text, kb = render.render_debate_survivors(_card_rows()[:1])
    ok_cb, no_cb = kb[0][0]["callback_data"], kb[0][1]["callback_data"]
    assert ok_cb == act.callback_for("approval.approve", id=JID), ok_cb
    assert no_cb == act.callback_for("approval.reject", id=JID), no_cb
    assert act.get("approval.approve") and act.get("approval.reject")


def t_the_id_on_the_button_is_the_id_the_handler_acts_on():
    """امروز `leg_rooms_beat` ۱۶ صداکننده داشت و هر ۱۶ در تست بودند. اینجا
    شناسهٔ روی دکمه واقعاً به approve/reject داده می‌شود و نتیجه سنجیده."""
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    _reset_store()
    _reset_queue()
    debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human")
    _t, kb = render.render_debate_survivors(render.ingest_debate_survivors())
    jid_from_button = kb[0][1]["callback_data"].split(":")[2]
    assert aps.reject(jid_from_button) is True, "شناسهٔ روی دکمه در صف پیدا نشد"
    assert aps.get(JID)["status"] == "rejected"
    # و همان شناسه، رأی را به حلقهٔ مناظره برمی‌گرداند
    assert aps.record_legacy_verdict(jid_from_button, "no") is True
    assert debate_loop.owner_verdict_for(SIG) == "rejected"


def t_token_mode_matches_what_the_handler_parses():
    """با OCTOPUS_WIRE_CB_TOKEN روشن، handler توکن را از seg[3] می‌خواند."""
    text, kb = render.render_debate_survivors(_card_rows()[:1],
                                              mint=lambda jid, a: f"t{a}")
    ok_cb = kb[0][0]["callback_data"]
    seg = ok_cb.split(":")
    assert len(seg) == 4 and seg[3] == "tok", ok_cb
    assert seg[:3] == ["ap", "ok", JID], ok_cb


# ═══ ۳. فلگ خاموش = امروز ═════════════════════════════════════════════════════
def t_flag_off_is_byte_identical():
    os.environ.pop("OCTOPUS_WIRE_DEBATE_VERDICT", None)
    pend = [{"id": JID, "type": "debate", "title": MUSE["idea"], "risk": "medium"},
            {"id": "job-x", "type": "mission", "title": "کارِ دیگر", "risk": "high"}]
    counts = {"pending": 2, "approved": 0, "rejected": 0, "done": 0}
    t_off, kb_off = render.render_approvals_queue(pend, counts, [])
    # همان ورودی، ولی نوعِ debate عوض شده: اگر فلگ خاموش باشد باید **بایت‌به‌بایت**
    # یکی باشند، یعنی نوعِ debate هیچ اثری ندارد.
    neutral = [dict(pend[0], type="task"), pend[1]]
    t_neutral, kb_neutral = render.render_approvals_queue(neutral, counts, [])
    assert t_off == t_neutral, "فلگ خاموش ولی نوعِ debate خروجی را عوض کرد"
    assert kb_off == kb_neutral, "فلگ خاموش ولی کیبورد عوض شد"
    assert "مناظره" not in t_off, "بخشِ مناظره با فلگِ خاموش رندر شد"
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    t_on, kb_on = render.render_approvals_queue(pend, counts, [])
    assert "مناظره" in t_on, t_on
    # ایدهٔ مناظره از فهرستِ صفحه‌بندی‌شده **بیرون کشیده** می‌شود و به بالا می‌رود:
    # ردیفِ اول کارت. با فلگِ خاموش همان ایده ردیفِ دوم بود (زیرِ jobِ risk=high).
    assert kb_on[0][0]["callback_data"] == f"ap:ok:{JID}", kb_on[0]
    assert kb_on[0][0]["text"].startswith("✅ آره"), kb_on[0]
    assert kb_off[0][0]["callback_data"] == "ap:ok:job-x", kb_off[0]
    assert len(kb_on) == len(kb_off), (len(kb_on), len(kb_off))
    # و دیگر در فهرستِ عادی تکرار نمی‌شود (یک ایده = یک جفت دکمه)
    assert sum(1 for r in kb_on for b in r
               if b.get("callback_data") == f"ap:ok:{JID}") == 1, kb_on


def t_flag_off_never_publishes_anything():
    os.environ.pop("OCTOPUS_WIRE_DEBATE_VERDICT", None)
    _reset_store()
    _reset_queue()
    assert debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human") is True
    assert not debate_loop.PENDING_JSONL.exists(), "با فلگِ خاموش پروژکشن نوشته شد"
    assert not aps._APPROVALS_JSON.exists(), "صفِ تأیید با فلگِ خاموش ساخته شد"


def t_the_organism_process_never_imports_the_approval_store():
    """ناوردیِ تک‌نویسنده (S1-05 t_o): قفلِ approval_store درون‌پروسه‌ای است، پس
    فقط مرکز اجازهٔ نوشتنِ approvals.json را دارد. نسخهٔ اولِ همین کار این را نقض
    کرد و آن گارد گرفتش؛ این چک همان مرز را از سمتِ WS-E هم قفل می‌کند."""
    pat = re.compile(r"^\s*(?:import\s+approval_store\b|from\s+approval_store\b)", re.M)
    for rel in ("debate/debate_loop.py", "organ_dialogue.py"):
        src = (_OPS / rel).read_text("utf-8")
        assert not pat.search(src), f"{rel} در پروسهٔ ارگانیسم approval_store را import کرد"
    # و در عوض، نویسنده باید داخلِ telegram_center باشد
    assert pat.search((_OPS / "telegram_center" / "render.py").read_text("utf-8")), \
        "نویسندهٔ صف از render حذف شده — مسیرِ دکمه قطع است"


def t_brain_digest_flag_off_is_unchanged():
    os.environ.pop("OCTOPUS_WIRE_DEBATE_VERDICT", None)
    d = od.brain_digest(state_dir=Path(ENV["ops"]) / "state")
    assert d.get("kb") == [], d.get("kb")
    assert d.get("debate_open") == 0, d.get("debate_open")
    assert "⚖️ <b>مناظره</b>" not in d["text"], d["text"]


def t_brain_digest_flag_on_shows_the_real_ideas():
    os.environ["OCTOPUS_WIRE_DEBATE_VERDICT"] = "1"
    _reset_store()
    _reset_queue()
    debate_loop._queue_survivor(TOPIC, MUSE, ARCH, "pending-human")
    sd = Path(ENV["ops"]) / "state"
    d = od.brain_digest(state_dir=sd)
    assert d["debate_open"] == 1, d
    assert MUSE["idea"][:25] in d["text"], "متنِ ایده هنوز به ۱۲۰ کاراکتر بریده می‌شود"
    # این کارت از باتِ ارگانیسم می‌رود (wiring.brain_digest_beat →
    # make_telegram_channel روی TELEGRAM_BOT_TOKEN)، ولی صفِ رأیِ واقعی فقط در
    # باتِ مرکز است. متن باید صریح بگوید کدام بات — چون یک callback_data روی
    # این کارت هرگز نمی‌تواند به آن بات برسد (تلهٔ دو-باتی، رگرسیونِ ۲۰۲۶-۰۸-۰۶).
    assert "@intergrade2725_Bot" in d["text"], (
        "کارتِ مغز نمی‌گوید رأی را در کدام بات بزن — مالک دوباره روی همین "
        f"بات دنبالِ دکمهٔ کار می‌گردد: {d['text']!r}"
    )
    h_before = d["hash"]
    # رأیِ مالک باید ایده را از کارتِ مغز هم بردارد (و hash را عوض کند)
    render.ingest_debate_survivors()
    _owner_taps(JID, "no")
    d2 = od.brain_digest(state_dir=sd)
    assert d2["debate_open"] == 0, d2
    assert MUSE["idea"][:25] not in d2["text"], "ایدهٔ ردشده هنوز در کارتِ مغز است"
    assert d2["hash"] != h_before, "hash عوض نشد → کارتِ تازه هرگز ارسال نمی‌شود"


# ═══ ۴. صداکنندهٔ تولیدی وجود دارد (AST، بیرونِ tests) ═════════════════════════
_NEW_FUNCS = ("render_debate_survivors", "ingest_debate_survivors", "owner_verdict_for",
              "_publish_survivor", "debate_survivor_card", "_ap_callback",
              "_debate_pending_path")


def _ast_call_counts() -> dict:
    counts = {f: 0 for f in _NEW_FUNCS}
    for p in _OPS.rglob("*.py"):
        parts = set(p.parts)
        if "tests" in parts or "__pycache__" in parts:
            continue
        try:
            tree = ast.parse(p.read_text("utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            name = (f.id if isinstance(f, ast.Name)
                    else f.attr if isinstance(f, ast.Attribute) else None)
            if name in counts:
                counts[name] += 1
    return counts


def t_every_new_function_has_a_production_caller():
    counts = _ast_call_counts()
    print("     صداکننده‌های تولیدی (بیرونِ tests):", json.dumps(counts))
    dead = [k for k, v in counts.items() if v == 0]
    assert not dead, f"تابعِ مرده (صفر صداکنندهٔ تولیدی): {dead}"


def t_live_approval_queue_was_never_touched():
    now = (_LIVE_APPROVALS.exists(),
           _LIVE_APPROVALS.stat().st_size if _LIVE_APPROVALS.exists() else -1,
           _LIVE_APPROVALS.stat().st_mtime_ns if _LIVE_APPROVALS.exists() else -1)
    assert now == _LIVE_STAMP, f"صفِ زندهٔ تأیید عوض شد! {_LIVE_STAMP} → {now}"


CHECKS = [
    ("رأیِ «نه» ایده را برای همیشه از صف بیرون می‌برد", t_rejected_idea_is_not_requeued),
    ("رأیِ «آره» هم دوباره پرسیده نمی‌شود", t_approved_idea_is_not_requeued_either),
    ("ایدهٔ متفاوت روی همان موضوع هنوز صف می‌شود", t_a_different_idea_is_still_queued),
    ("دندان: کدِ پیش‌از‌فیکس ایدهٔ ردشده را دوباره صف می‌کند",
     t_teeth_prefix_code_requeues_a_rejected_idea),
    ("هر callback_data به handlerِ واقعی می‌رسد",
     t_every_callback_on_the_card_resolves_to_a_real_handler),
    ("callback از رجیستری می‌آید نه از رشتهٔ hardcode",
     t_callback_comes_from_the_registry_not_a_string_literal),
    ("شناسهٔ روی دکمه همان است که handler رویش عمل می‌کند",
     t_the_id_on_the_button_is_the_id_the_handler_acts_on),
    ("حالتِ توکن با آنچه handler پارس می‌کند می‌خواند",
     t_token_mode_matches_what_the_handler_parses),
    ("فلگ خاموش → خروجیِ بایت‌به‌بایتِ امروز", t_flag_off_is_byte_identical),
    ("فلگ خاموش → هیچ چیز منتشر نمی‌شود", t_flag_off_never_publishes_anything),
    ("پروسهٔ ارگانیسم approval_store را import نمی‌کند",
     t_the_organism_process_never_imports_the_approval_store),
    ("کارتِ مغز با فلگِ خاموش دست‌نخورده", t_brain_digest_flag_off_is_unchanged),
    ("کارتِ مغز با فلگِ روشن خودِ ایده‌ها را نشان می‌دهد",
     t_brain_digest_flag_on_shows_the_real_ideas),
    ("هر تابعِ تازه صداکنندهٔ تولیدی دارد", t_every_new_function_has_a_production_caller),
    ("صفِ زندهٔ تأیید دست‌نخورده ماند", t_live_approval_queue_was_never_touched),
]

if __name__ == "__main__":
    print(f"WS-E — رأیِ مالک روی مناظره ({len(CHECKS)} چک)")
    assert len(CHECKS) >= 15, "فهرستِ چک‌ها خالی/ناقص است — تستِ بی‌صدا"
    failed = harness.run(CHECKS)
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} پاس")
    sys.exit(1 if failed else 0)
