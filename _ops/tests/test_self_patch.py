"""test_self_patch.py — پلِ «نقص پیدا کردم» → «پچ نوشتم و تستش کردم».

رأیِ مالک ۲۰۲۶-۰۷-۲۶: «خودشو بهتر کنه، نه الکی فقط نگاه». مرزِ الف: می‌نویسد و
ایزوله تست می‌کند؛ اعمال همیشه یک کلیکِ جداست.

سخت‌ترین قیدها این‌جا **آن‌هایی‌اند که نباید اتفاق بیفتند**:
  · هیچ پچی بدونِ سوییتِ سبز به کارت تبدیل نشود (`t_a_red_shadow_never_becomes_a_card`)
  · allowlist هرگز این‌جا بازتعریف نشود — از code_autonomy قرض گرفته می‌شود
  · هرگز چیزی به درختِ زنده نوشته نشود
اگر این سه سبز بمانند و بقیه بشکنند، هنوز ایمن است؛ برعکسش نه.

صفر شبکه: مغز و شادو-تستر هر دو تزریقی‌اند.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("self-patch")

sys.path.insert(0, str(_HERE.parent / "cortex"))
import self_patch as sp      # noqa: E402
import code_autonomy as ca   # noqa: E402

ALLOWED = "_ops/telegram_center/live_commands.py"
DENIED = "_ops/budget/approval_channel.py"


def _flag(on):
    if on:
        os.environ[sp.FLAG] = "1"
    else:
        os.environ.pop(sp.FLAG, None)


def _brain(text):
    def fn(task, prompt, system="", max_tokens=4000, tier=None):
        assert tier == "primary", "نوشتنِ کد باید به لایهٔ سنگین برود"
        return {"ok": True, "tier": "primary", "text": text}
    return fn


def _shadow(green, **extra):
    def fn(target, content):
        return {"ok": True, "green": green, "target": target,
                "diff": " 1 file changed, 2 insertions(+)", **extra}
    return fn


# ─── گیت‌ها ─────────────────────────────────────────────────────────────────
def t_flag_off_does_nothing():
    _flag(False)
    r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain("y"),
                   shadow_fn=_shadow(True))
    assert r == {"ok": False, "reason": "flag-off"}


def t_allowlist_is_borrowed_not_redefined():
    """این ماژول نباید allowlist خودش را بسازد — یک حقیقت، یک نگهبان."""
    import inspect
    src = inspect.getsource(sp)
    assert "allowed_target" in src, "باید از code_autonomy.allowed_target استفاده کند"
    for banned in ("_ALLOW_ROOTS", "_DENY = ", "allowlist = ["):
        assert banned not in src, f"allowlist این‌جا بازتعریف شده: {banned!r}"


def t_a_denied_target_is_refused_before_the_brain_is_asked():
    _flag(True)
    asked = []

    def spy(task, prompt, system="", max_tokens=4000, tier=None):
        asked.append(task)
        return {"ok": True, "text": "x"}
    try:
        r = sp.propose(target_rel=DENIED, defect="x", ask_fn=spy,
                       shadow_fn=_shadow(True))
        assert r["ok"] is False and r["reason"] == "target-not-allowed", r
        assert asked == [], "مغز نباید برای هدفِ ممنوع اصلاً صدا زده شود"
    finally:
        _flag(False)


def t_money_and_secret_paths_stay_denied():
    """گاردِ صریح روی مسیرهایی که هرگز نباید خودتغییر شوند."""
    for p in ("_ops/budget/budgets.yaml", "_ops/.env", "_ops/genome/x.py",
              "_ops/state/ledger.jsonl", "_ops/money_effector.py", ".git/config"):
        assert not ca.allowed_target(p), f"{p} نباید مجاز باشد"


# ─── قیدِ اصلی: قرمز هرگز کارت نمی‌شود ──────────────────────────────────────
def t_a_red_shadow_never_becomes_a_card():
    """قلبِ ایمنیِ مرزِ الف. پچی که سوییت را نمی‌گذراند نباید توجهِ مالک را بخورد."""
    _flag(True)
    try:
        r = sp.propose(target_rel=ALLOWED, defect="یک نقص",
                       ask_fn=_brain("# changed\nprint(1)\n"),
                       shadow_fn=_shadow(False))
        assert r["ok"] is False and r["reason"] == "shadow-red", r
        assert r["green"] is False
    finally:
        _flag(False)


def t_a_green_shadow_produces_a_proposal():
    _flag(True)
    try:
        r = sp.propose(target_rel=ALLOWED, defect="یک نقصِ واقعی", fix_hint="کوتاهش کن",
                       ask_fn=_brain("# fixed\nprint(1)\n"),
                       shadow_fn=_shadow(True))
        assert r["ok"] is True and r["green"] is True, r
        assert r["target"] == ALLOWED and r["id"].startswith("sp-")
        assert r["bytes_after"] > 0 and r["bytes_before"] > 0
    finally:
        _flag(False)


def t_an_unchanged_candidate_is_honesty_not_success():
    """سیستم‌پرامپت می‌گوید اگر مطمئن نیستی فایل را دست‌نخورده برگردان.
    آن حالت نباید به‌عنوان پچ جا زده شود."""
    _flag(True)
    src = (Path(sp._HERE).parent / ALLOWED).read_text("utf-8")
    try:
        r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain(src),
                       shadow_fn=_shadow(True))
        assert r["ok"] is False and r["reason"] == "no-change-proposed", r
    finally:
        _flag(False)


def t_brain_silence_is_not_a_patch():
    _flag(True)
    try:
        for empty in ("", "   ", "```\n```"):
            r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain(empty),
                           shadow_fn=_shadow(True))
            assert r["ok"] is False and r["reason"] == "brain-no-answer", r
    finally:
        _flag(False)


def t_code_fences_are_stripped():
    assert sp._strip_fences("```python\nprint(1)\n```") == "print(1)"
    assert sp._strip_fences("print(1)") == "print(1)"


# ─── سقفِ روزانه و بی‌اثری روی درختِ زنده ───────────────────────────────────
def t_daily_cap_protects_owner_attention():
    _flag(True)
    d = sp._dir()
    d.mkdir(parents=True, exist_ok=True)
    made = []
    try:
        for i in range(sp.DAILY_CAP):
            p = d / f"cap-{i}.json"
            p.write_text("{}", encoding="utf-8")
            made.append(p)
        r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain("print(1)"),
                       shadow_fn=_shadow(True))
        assert r["ok"] is False and r["reason"] == "daily-cap", r
    finally:
        for p in made:
            try:
                p.unlink()
            except OSError:
                pass
        _flag(False)


def t_it_never_writes_to_the_live_tree():
    """قیدِ سخت: تنها اثرِ جانبیِ مجاز، رکوردِ پیشنهاد در state است."""
    _flag(True)
    target = Path(sp._HERE).parent / ALLOWED
    before = target.read_bytes()
    try:
        sp.propose(target_rel=ALLOWED, defect="x",
                   ask_fn=_brain("# مهاجم\nprint('pwned')\n"),
                   shadow_fn=_shadow(True))
        assert target.read_bytes() == before, "فایلِ زنده عوض شد — نقضِ مرزِ الف"
    finally:
        _flag(False)


def t_the_card_says_what_happens_if_ignored():
    """طبق دکترین D1 — کارتِ بی‌پیامدِ بی‌عملی ساخته نمی‌شود."""
    txt = sp.card_text({"target": "x.py", "defect": "d", "diff": "1 file changed"})
    assert "نکنی" in txt, "کارت نمی‌گوید اگر کاری نکنی چه می‌شود"
    assert "x.py" in txt and "سبز" in txt


# ═══ حلقهٔ خودگردان (review→queue→drive→card) — تستِ متخاصم ۲۰۲۶-۰۷-۲۷ ═══════
# قصد: شکستنِ حلقهٔ تازه، نه تأییدش. سه چیز نباید ممکن باشد:
#   · مغزِ خراب هر تیک یک مرورِ گران بسوزاند (روز باید قبل از تماس بسوزد)
#   · یک نقصِ done دوباره driven شود (صف append-only است — آخرین وضع برنده)
#   · جوابِ خارج از قرارداد چیزی وارد صف کند


def _on():
    _flag(True)


def _off():
    _flag(False)


def _reset_loop_state():
    for p in (sp.QUEUE_PATH, sp.REVIEW_STATE):
        try:
            p.unlink()
        except OSError:
            pass
    # تست‌های propose ِ بالاتر تا سقفِ روزانه (۳) پیشنهاد ساخته‌اند؛ بدونِ پاک‌سازی،
    # drive در این بلوک به daily-cap می‌خورد و ask هرگز صدا نمی‌شود — شکستِ گمراه‌کننده.
    d = sp._dir()
    if d.exists():
        for f in d.glob("*.json"):
            try:
                f.unlink()
            except OSError:
                pass


def _mk_ask(answer, calls=None, boom=False):
    """ask_fn با امضای model_router.ask؛ فراخوان‌ها را ضبط می‌کند."""
    calls = calls if calls is not None else []

    def ask(task, prompt, system="", max_tokens=400, tier=None, **kw):
        calls.append({"task": task, "prompt": prompt, "system": system,
                      "max_tokens": max_tokens, "tier": tier})
        if boom:
            raise RuntimeError("مغز ترکید")
        return {"ok": True, "text": answer, "model": "fugu", "cost_usd": 0.0}

    ask._calls = calls
    return ask


class _Chan:
    def __init__(self, boom=False):
        self.sent, self.boom = [], boom

    def send_text(self, text, stream=None, **kw):
        if self.boom:
            raise RuntimeError("کانال ترکید")
        self.sent.append({"text": text, "stream": stream})
        return True


def t_loop_review_flag_off_is_a_pure_noop():
    _off()
    _reset_loop_state()
    r = sp.review_and_queue(ask_fn=_mk_ask("CLEAN"))
    assert r == {"ok": False, "reason": "flag-off"}, r
    assert not sp.QUEUE_PATH.exists() and not sp.REVIEW_STATE.exists()


def t_loop_review_burns_the_day_before_the_expensive_call():
    """مغزِ خراب → روز باید سوخته باشد؛ تلاشِ دوم در همان روز مرور نمی‌کند."""
    _on()
    _reset_loop_state()
    try:
        boom = _mk_ask("", boom=True)
        r = sp.review_and_queue(ask_fn=boom, targets=[ALLOWED])
        assert r.get("clean") or not r.get("queued"), r      # جوابِ خالی = بدونِ صف
        assert sp.REVIEW_STATE.exists(), "روز قبل از تماس نسوخت"
        again = _mk_ask("CLEAN")
        r2 = sp.review_and_queue(ask_fn=again, targets=[ALLOWED])
        assert r2["reason"] == "already-reviewed-today", r2
        assert not again._calls, "روزِ سوخته دوباره مغز را صدا زد"
    finally:
        _off()


def t_loop_clean_answer_queues_nothing():
    _on()
    _reset_loop_state()
    try:
        r = sp.review_and_queue(ask_fn=_mk_ask("CLEAN"), targets=[ALLOWED])
        assert r.get("clean") is True, r
        assert not sp.QUEUE_PATH.exists(), "CLEAN ولی صف ساخته شد"
    finally:
        _off()


def t_loop_garbage_review_output_queues_nothing():
    for bad in ("خب به نظرم این فایل مشکل دارد.", '{"no_defect_key": 1}', "{broken json"):
        _on()
        _reset_loop_state()
        try:
            r = sp.review_and_queue(ask_fn=_mk_ask(bad), targets=[ALLOWED])
            assert not r.get("queued"), (bad[:30], r)
            assert not sp.QUEUE_PATH.exists(), f"جوابِ خارج از قرارداد وارد صف شد: {bad[:30]}"
        finally:
            _off()


def t_loop_a_real_defect_is_queued_exactly_once():
    _on()
    _reset_loop_state()
    try:
        ans = json.dumps({"defect": "تابعِ X روی ورودیِ خالی KeyError می‌دهد", "hint": "گاردِ .get"},
                         ensure_ascii=False)
        r = sp.review_and_queue(ask_fn=_mk_ask(ans), targets=[ALLOWED])
        assert r.get("queued"), r
        rows = sp._queue_rows()
        assert len(rows) == 1 and rows[0]["status"] == "open" and rows[0]["target"] == ALLOWED
        # فردا همان نقص دوباره پیدا شود → duplicate، نه ردیفِ دوم
        sp.REVIEW_STATE.unlink()
        r2 = sp.review_and_queue(ask_fn=_mk_ask(ans), targets=[ALLOWED])
        assert r2.get("duplicate") is True, r2
        assert len(sp._queue_rows()) == 1
    finally:
        _off()


def t_loop_review_rotates_files_across_days():
    _on()
    _reset_loop_state()
    try:
        seen = []
        files = [ALLOWED, "_ops/telegram_center/tg_api.py", "_ops/cortex/improve.py"]
        for _ in range(3):
            r = sp.review_and_queue(ask_fn=_mk_ask("CLEAN"), targets=files)
            seen.append(r["target"])
            sp.REVIEW_STATE.write_text(json.dumps(
                {**json.loads(sp.REVIEW_STATE.read_text("utf-8")), "date": "2000-01-01"}),
                "utf-8")   # روزِ کهنه → فردا
        assert seen == files, f"چرخش شکسته: {seen}"
    finally:
        _off()


def t_loop_review_is_pinned_to_the_expensive_tier():
    """بدونِ پین، CORTEX_LOCAL_FIRST مرور را به مدلِ رایگان می‌بَرد و حلقه نمایش می‌شود."""
    _on()
    _reset_loop_state()
    try:
        ask = _mk_ask("CLEAN")
        sp.review_and_queue(ask_fn=ask, targets=[ALLOWED])
        c = ask._calls[0]
        assert c["tier"] == "primary", c["tier"]
        assert "CLEAN" in c["system"], "قراردادِ مرور در system نیست — قراردادِ پچ رفته"
        assert ALLOWED in c["prompt"] and "BEGIN FILE" in c["prompt"]
    finally:
        _off()


def t_loop_drive_respects_effective_state_not_raw_rows():
    """صف append-only است: ردیفِ done نباید دوباره driven شود."""
    _on()
    _reset_loop_state()
    try:
        row = {"id": "sp-t1", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
               "defect": "d", "hint": "", "status": "open"}
        sp._queue_append(row)
        sp._queue_append({**row, "status": "done"})
        r = sp.drive(channel=_Chan(), ask_fn=_mk_ask("x"), shadow_fn=lambda t, c: {"green": True})
        assert r["reason"] == "queue-empty", f"ردیفِ done دوباره driven شد: {r}"
    finally:
        _off()


def t_loop_drive_locks_the_row_before_the_brain_call():
    _on()
    _reset_loop_state()
    try:
        sp._queue_append({"id": "sp-t2", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                          "defect": "d", "hint": "", "status": "open"})
        state_at_call = {}

        def ask(task, prompt, **kw):
            eff = sp._queue_effective()
            state_at_call["status"] = eff["sp-t2"]["status"]
            return {"ok": True, "text": "new content", "model": "fugu"}

        sp.drive(channel=None, ask_fn=ask, shadow_fn=lambda t, c: {"green": True})
        assert state_at_call["status"] == "taken", state_at_call
        assert sp._queue_effective()["sp-t2"]["status"] == "done"
    finally:
        _off()


def t_loop_red_shadow_drive_sends_no_card():
    _on()
    _reset_loop_state()
    try:
        sp._queue_append({"id": "sp-t3", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                          "defect": "d", "hint": "", "status": "open"})
        ch = _Chan()
        r = sp.drive(channel=ch, ask_fn=_mk_ask("candidate"),
                     shadow_fn=lambda t, c: {"green": False, "reason": "suite-red"})
        assert not r.get("ok") and not ch.sent, (r, ch.sent)
        assert sp._queue_effective()["sp-t3"]["status"] == "failed"
    finally:
        _off()


def t_loop_green_drive_delivers_a_card_and_survives_a_dead_channel():
    _on()
    _reset_loop_state()
    try:
        sp._queue_append({"id": "sp-t4", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                          "defect": "نقصِ واقعی", "hint": "", "status": "open"})
        ch = _Chan()
        r = sp.drive(channel=ch, ask_fn=_mk_ask("fixed content"),
                     shadow_fn=lambda t, c: {"green": True, "diff": "1 file changed"})
        assert r.get("ok") and len(ch.sent) == 1, (r, ch.sent)
        assert ch.sent[0]["stream"] == "c6" and "نکنی" in ch.sent[0]["text"]
        # کانالِ مرده حلقه را نمی‌کشد
        sp._queue_append({"id": "sp-t5", "ts": "2026-01-01T00:00:01Z", "target": ALLOWED,
                          "defect": "نقصِ دوم", "hint": "", "status": "open"})
        r2 = sp.drive(channel=_Chan(boom=True), ask_fn=_mk_ask("fixed2"),
                      shadow_fn=lambda t, c: {"green": True})
        assert r2.get("ok"), r2
    finally:
        _off()


def t_loop_beat_async_never_blocks_and_never_doubles():
    import threading
    import time as _t
    _on()
    _reset_loop_state()
    try:
        # هیچ‌کاری نیست → spawn نمی‌کند
        sp.REVIEW_STATE.parent.mkdir(parents=True, exist_ok=True)
        sp.REVIEW_STATE.write_text(json.dumps(
            {"date": _t.strftime("%Y-%m-%d"), "idx": 0, "target": ALLOWED}), "utf-8")
        r = sp.beat_async(channel=None)
        assert r == {"spawned": False, "reason": "nothing-to-do"}, r
        # قفل گرفته → busy، نه threadِ دوم
        assert sp._BEAT_LOCK.acquire(blocking=False)
        try:
            sp._queue_append({"id": "sp-t6", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                              "defect": "d", "hint": "", "status": "open"})
            r2 = sp.beat_async(channel=None)
            assert r2 == {"spawned": False, "reason": "busy"}, r2
        finally:
            sp._BEAT_LOCK.release()
    finally:
        _off()
        _reset_loop_state()


def t_loop_beat_async_flag_off_spawns_nothing():
    _off()
    r = sp.beat_async(channel=None)
    assert r == {"spawned": False, "reason": "flag-off"}, r


def t_loop_review_targets_all_pass_the_borrowed_allowlist():
    """هرچه review_targets می‌دهد باید از allowlistِ قرضی رد شود — وگرنه مرور فایلی
    را می‌خواند که پچش هرگز مجاز نیست (اتلافِ تماسِ گران)."""
    files = sp.review_targets()
    assert files, "هیچ هدفِ مروری نیست"
    for f in files:
        assert ca.allowed_target(f), f
        assert f.endswith(".py"), f


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_self_patch: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
