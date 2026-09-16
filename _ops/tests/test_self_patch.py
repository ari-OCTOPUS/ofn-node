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
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("self-patch")

sys.path.insert(0, str(_HERE.parent / "cortex"))
import self_patch as sp      # noqa: E402
import code_autonomy as ca   # noqa: E402

# ۲۰۲۶-۰۷-۳۰ — فیکسچرِ ALLOWED از `telegram_center` به `cortex` رفت چون رأیِ صریحِ
# مالک (VQ-SELFGOAL-005) آن ریشه را از `code_autonomy._ALLOW_ROOTS` برداشت: دامنهٔ
# مصوبِ L3 فقط `_ops/cortex/**` + `_ops/state/**` بود، و `telegram_center` همان
# جایی است که کارتِ تأیید رندر می‌شود (ارگانیسم می‌توانست دکمهٔ رأیِ خودش را
# بازنویسی کند). این تغییرِ **فیکسچر** است نه تضعیفِ گارد — و برای اینکه دامنهٔ
# نو خودش قفل شود، `DENIED_TG` پایین اضافه شد.
ALLOWED = "_ops/cortex/local_llm.py"
DENIED = "_ops/budget/approval_channel.py"
DENIED_TG = "_ops/telegram_center/live_commands.py"   # رأیِ ۰۷-۳۰: دیگر مجاز نیست


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
        files = [ALLOWED, "_ops/cortex/synthesis.py", "_ops/cortex/improve.py"]
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


def t_the_narrowed_scope_is_locked_not_just_unused():
    """رأیِ مالک VQ-SELFGOAL-005 — دامنه **تنگ شد**، پس باید قفل شود.

    اگر فقط فیکسچر را عوض می‌کردم و این بند نبود، برگشتنِ `telegram_center` به
    `_ALLOW_ROOTS` هیچ تستی را قرمز نمی‌کرد — دقیقاً همان «گاردِ بی‌دندان».
    و مسیرِ فرارِ `..` هم این‌جا بسته می‌ماند (سوراخِ اثبات‌شدهٔ ۰۷-۳۰)."""
    assert ca.allowed_target(ALLOWED), ALLOWED
    for denied in (DENIED_TG, "_ops/telegram_center/power.py",
                   "_ops/cortex/../../PRE-0/governance.py",
                   "_ops/cortex/../tests/run_all.py"):
        assert not ca.allowed_target(denied), f"باید رد شود: {denied}"
    assert not any(f.startswith("_ops/telegram_center/")
                   for f in sp.review_targets()), sp.review_targets()


# ═══ یافته‌های ممیزیِ متخاصمِ ۲۰۲۶-۰۷-۲۷ (۱۸ تأییدشده) — قفلِ رگرسیون ═══════════
# هر تست زیر یک باگِ **واقعیِ همان روز** را می‌بندد، نه یک سناریوی فرضی.


def t_audit_a_corrupt_line_does_not_blank_the_whole_queue():
    """یافتهٔ major: `json.JSONDecodeError` زیرمجموعهٔ `ValueError` است و کلِ خواندن
    در یک try بود — یک خطِ نصفه (که appendِ غیراتمیک در قطعِ برق می‌سازد) صف را
    برای همیشه `[]` می‌کرد، بی‌صدا."""
    _on()
    _reset_loop_state()
    try:
        good = {"id": "sp-ok", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                "defect": "d", "hint": "", "status": "open"}
        sp._queue_append(good)
        with open(sp.QUEUE_PATH, "a", encoding="utf-8") as f:
            f.write('{"id": "sp-broken", "sta\n')          # خطِ بریده
        sp._queue_append({**good, "id": "sp-ok2"})
        rows = sp._queue_rows()
        ids = {r.get("id") for r in rows}
        assert ids == {"sp-ok", "sp-ok2"}, f"خطِ خراب صف را نابود کرد: {ids}"
        assert any(r.get("status") == "open" for r in sp._queue_effective().values())
    finally:
        _off()
        _reset_loop_state()


def t_audit_a_stale_taken_row_is_reopened_not_buried():
    """یافتهٔ major: threadِ daemon وسطِ کار با ری‌استارت می‌میرد؛ هیچ‌کس `taken` را
    نمی‌خواند و dedupِ id هم مانعِ صف‌شدنِ دوباره است ⇒ نقص برای همیشه دفن."""
    _on()
    _reset_loop_state()
    try:
        row = {"id": "sp-stale", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
               "defect": "d", "hint": "", "status": "open"}
        sp._queue_append(row)
        sp._queue_append({**row, "status": "taken", "taken_ts": "2020-01-01T00:00:00Z"})
        eff = sp._queue_effective()
        assert eff["sp-stale"]["status"] == "open", f"ردیفِ کهنه باز نشد: {eff}"
        assert eff["sp-stale"].get("reopened_from") == "taken-stale"
        # ولی یک `taken` ِ تازه نباید باز شود (وگرنه دو worker یک ردیف را می‌گیرند)
        import time as _t
        fresh = _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())
        sp._queue_append({**row, "status": "taken", "taken_ts": fresh})
        assert sp._queue_effective()["sp-stale"]["status"] == "taken", "ردیفِ تازه باز شد"
    finally:
        _off()
        _reset_loop_state()


def t_audit_a_transient_failure_does_not_burn_the_defect_forever():
    """یافتهٔ major: هر non-ok ردیف را نهایی می‌کرد — از جمله «سقفِ روزانه» و «مغز
    جواب نداد»، که هیچ‌کدام حرفی دربارهٔ خودِ نقص نمی‌زنند."""
    _on()
    _reset_loop_state()
    try:
        row = {"id": "sp-tr", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
               "defect": "d", "hint": "", "status": "open"}
        sp._queue_append(row)
        # مغز سکوت می‌کند → گذرا → باید دوباره باز شود
        sp.drive(channel=None, ask_fn=_mk_ask(""), shadow_fn=lambda t, c: {"green": True})
        eff = sp._queue_effective()["sp-tr"]
        assert eff["status"] == "open", f"شکستِ گذرا نهایی شد: {eff}"
        assert eff["attempts"] == 1
        # ولی قضاوتِ واقعی (سوییت قرمز) باید نهایی باشد
        sp.drive(channel=None, ask_fn=_mk_ask("cand"),
                 shadow_fn=lambda t, c: {"green": False, "reason": "suite-red"})
        assert sp._queue_effective()["sp-tr"]["status"] == "failed"
    finally:
        _off()
        _reset_loop_state()


def t_audit_transient_retries_are_bounded():
    """بی‌کران بودنِ retry یعنی یک نقصِ نفرین‌شده تا ابد تماسِ پولی می‌سوزاند."""
    _on()
    _reset_loop_state()
    try:
        sp._queue_append({"id": "sp-loop", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                          "defect": "d", "hint": "", "status": "open"})
        for _ in range(5):
            sp.drive(channel=None, ask_fn=_mk_ask(""),
                     shadow_fn=lambda t, c: {"green": True})
        eff = sp._queue_effective()["sp-loop"]
        assert eff["status"] == "failed", f"retry بی‌کران ماند: {eff}"
        assert eff["attempts"] <= 3, eff
    finally:
        _off()
        _reset_loop_state()


def t_audit_brain_silence_is_never_recorded_as_clean():
    """یافتهٔ major: مغزِ مرده هر روز یک فایل را «بازبینی‌شده و سالم» اعلام می‌کرد."""
    _on()
    _reset_loop_state()
    try:
        r = sp.review_and_queue(ask_fn=_mk_ask("", boom=True), targets=[ALLOWED])
        assert r.get("reason") == "brain-silent", r
        assert not r.get("clean"), "سکوتِ مغز «تمیز» ثبت شد"
        # ولی روز باید سوخته بماند وگرنه هر تیک یک مرورِ گران
        assert sp.REVIEW_STATE.exists(), "روز پس داده شد — مغزِ خراب هر تیک می‌سوزاند"
    finally:
        _off()
        _reset_loop_state()


def t_audit_a_silent_downgrade_never_writes_a_patch():
    """همان یافته در سمتِ پچ‌نویسی: یک پچِ پایتونی که مدلِ محلیِ ۱.۵B نوشته باشد
    نباید حتی وارد شادو-تست شود."""
    _on()
    _reset_loop_state()
    try:
        for extra in ({"fallback_from": "primary: paid-call-failed"},
                      {"tier": "local"}, {"tier": "secondary"}):
            shadow_called = {"n": 0}

            def ask(task, prompt, system="", max_tokens=4000, tier=None, **kw):
                return {"ok": True, "text": "patched content",
                        "tier": "primary", **extra}

            def shadow(t, c):
                shadow_called["n"] += 1
                return {"green": True}

            r = sp.propose(target_rel=ALLOWED, defect="d", ask_fn=ask, shadow_fn=shadow)
            assert not r.get("ok"), (extra, r)
            assert r.get("reason") == "brain-no-answer", (extra, r)
            assert shadow_called["n"] == 0, f"شادو-تستِ گران روی جوابِ رایگان دوید: {extra}"
    finally:
        _off()
        _reset_loop_state()


def t_audit_the_downgrade_alert_tells_the_daily_cap_from_a_real_failure():
    """۲۰۲۶-۰۸-۰۶ زنده (اسکنِ سراسری): همان کلاسِ آلارمِ گمراه‌کنندهٔ
    model_router/deep_think، سومین نمونهٔ فیکس‌نشده — self_patch's own
    «به مغزِ گران نرسید ... رها شد» تفکیک نمی‌کرد سقفِ روزانهٔ عادی از
    شکستِ واقعی. با سقف: باید ℹ️ و «سقفِ روزانه» بگوید. بدونِ سقف: متنِ
    قدیمی (بدونِ ℹ️) بماند."""
    import opslib
    _on()
    _reset_loop_state()
    sent, real_alert = [], opslib.alert
    opslib.alert = lambda msgs, **k: sent.extend(list(msgs))
    real_fq = sys.modules.get("fugu_quota")
    try:
        # self_patch's OWN daily-share counter (_self_patch_may_spend) never
        # gets cleared by _reset_loop_state() -- it accumulates across every
        # earlier propose()/_ask() call in this whole file's run, so it must
        # be zeroed here or this test silently gets denied before _ask() is
        # ever reached (exactly the failure mode that first caught this).
        try:
            sp.SELF_PATCH_CALLS.unlink()
        except OSError:
            pass
        import types

        def ask(task, prompt, system="", max_tokens=4000, tier=None, **kw):
            return {"ok": True, "text": "x", "tier": "local",
                    "fallback_from": "primary: paid-call-failed"}

        m = types.ModuleType("fugu_quota")
        m.status = lambda: {"remaining": 0, "used_total": 60, "cap": 60}
        m._cap = lambda: 60          # _self_patch_may_spend() reads this separately
        sys.modules["fugu_quota"] = m
        sp.propose(target_rel=ALLOWED, defect="d", ask_fn=ask,
                  shadow_fn=lambda t, c: {"green": True})
        assert sent, "آلارمی زده نشد"
        msg = sent[-1]
        assert msg.startswith("ℹ️"), msg
        assert "سقفِ روزانه" in msg and "60/60" in msg, msg

        sent.clear()
        m.status = lambda: {"remaining": 57, "used_total": 3, "cap": 60}
        sp.propose(target_rel=ALLOWED, defect="d", ask_fn=ask,
                  shadow_fn=lambda t, c: {"green": True})
        assert sent, "آلارمی زده نشد"
        msg2 = sent[-1]
        assert not msg2.startswith("ℹ️"), msg2
        assert "paid-call-failed" in msg2, msg2
    finally:
        opslib.alert = real_alert
        if real_fq is not None:
            sys.modules["fugu_quota"] = real_fq
        else:
            sys.modules.pop("fugu_quota", None)
        _off()
        _reset_loop_state()


def t_audit_the_input_cap_cannot_exceed_the_output_budget():
    """قرارداد «کلِ فایلِ اصلاح‌شده را برگردان» یعنی سقفِ ورودی نمی‌تواند از سقفِ
    خروجی بزرگ‌تر باشد. ۶۰KB پذیرفته می‌شد در حالی که ۴۰۰۰ توکن ~۱۲KB بیرون می‌دهد،
    پس هر فایلِ بزرگ‌تر ساختاراً نیمه‌کاره برمی‌گشت و سوییت را قرمز می‌کرد."""
    assert sp.MAX_FILE_BYTES <= sp.PATCH_MAX_TOKENS * 4, \
        f"سقفِ ورودی ({sp.MAX_FILE_BYTES}) از بودجهٔ خروجی بزرگ‌تر است"
    # و هر هدفی که برای مرور انتخاب می‌شود باید واقعاً پچ‌پذیر باشد
    root = Path(sp.__file__).resolve().parent.parent
    for rel in sp.review_targets():
        n = (root / rel).stat().st_size
        assert n <= sp.MAX_FILE_BYTES, f"{rel} ({n}B) مرور می‌شود ولی پچش جا نمی‌شود"


def t_audit_a_failed_defect_reaches_the_owner():
    """شکستِ نهایی باید دیده شود؛ وگرنه یافتهٔ یک مرورِ پولی بی‌صدا گم می‌شود."""
    import opslib
    _on()
    _reset_loop_state()
    sent, real = [], opslib.alert
    opslib.alert = lambda msgs, **k: sent.extend(msgs)
    try:
        sp._queue_append({"id": "sp-al", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                          "defect": "نقصِ واقعی", "hint": "", "status": "open"})
        sp.drive(channel=None, ask_fn=_mk_ask("cand"),
                 shadow_fn=lambda t, c: {"green": False, "reason": "suite-red",
                                         "new_fails": ["test_x"]})
        blob = " ".join(sent)
        assert "sp-al" in blob and ALLOWED in blob, f"شکست به مالک نرسید: {blob[:150]}"
    finally:
        opslib.alert = real
        _off()
        _reset_loop_state()


# ═══ arm_gate wiring (۲۰۲۶-۰۸-۰۴، DR-001) — گیتِ هشتم در _offer_patch_to_owner ═══
# سه چیز باید ثابت شود:
#   ۱. هر دو knobِ arm_gate خاموش (پیش‌فرضِ امروز) → رفتار بایت‌به‌بایت قبلی
#   ۲. OCTOPUS_ARM_SENSITIVE_DEFAULT=1 + بدونِ arm-token تازه → اینجا متوقف
#   ۳. OCTOPUS_ARM_SENSITIVE_DEFAULT=1 + arm-token دوکلیدیِ معتبر → رد می‌شود
# منطقِ داخلیِ arm_gate خودش قبلاً در test_arm_gate.py / test_arm_gate_p0.py
# تست شده — اینجا فقط سیم‌کشی (این تابع واقعاً guard() را صدا می‌زند و به
# نتیجه‌اش احترام می‌گذارد) تحتِ آزمون است، نه خودِ arm_gate.

import arm_gate as _ag  # noqa: E402

_ARM_DIR = sp.opslib.STATE_DIR / "arm"
_ACTIVATION_FLAG = sp.opslib.OPS / "ACTIVATION-CODE-AUTONOMY.flag"


def _arm_env(on):
    if on:
        os.environ["OCTOPUS_ARM_SENSITIVE_DEFAULT"] = "1"
    else:
        os.environ.pop("OCTOPUS_ARM_SENSITIVE_DEFAULT", None)
    os.environ.pop("OCTOPUS_REQUIRE_ARM", None)


def _write_arm_token(cap, suffix):
    _ARM_DIR.mkdir(parents=True, exist_ok=True)
    (_ARM_DIR / f"{cap}.{suffix}.json").write_text(
        json.dumps({"capability": cap, "armed_at": time.time()}), encoding="utf-8")


def _clear_arm_state():
    import shutil
    shutil.rmtree(_ARM_DIR, ignore_errors=True)
    try:
        _ACTIVATION_FLAG.unlink()
    except OSError:
        pass


def _offerable_patch(id_):
    return {"ok": True, "shadow_green": True, "content": "print(1)\n",
            "target": ALLOWED, "id": id_, "defect": "d"}


def t_arm_gate_default_off_is_byte_identical():
    """هر دو knob خاموش → گیتِ هشتم نباید هیچ چیزِ رفتاری را عوض کند
    (نتیجه باید همان چیزی باشد که قبل از سیم‌کشیِ arm_gate بود: not-offerable
    یا موفقیتِ pending-write، هرگز arm-gate-denied)."""
    _arm_env(False)
    _clear_arm_state()
    os.environ["OCTOPUS_WIRE_PATCH_CARD"] = "1"
    try:
        r = sp._offer_patch_to_owner(_offerable_patch("sp-arm0"))
        assert not str(r.get("reason", "")).startswith("arm-gate-denied"), r
        assert r.get("ok") is True, r  # پیشنهاد به مالک باید موفق شود (بدونِ arm_gate)
    finally:
        os.environ.pop("OCTOPUS_WIRE_PATCH_CARD", None)
        _arm_env(False)
        _clear_arm_state()


def t_arm_gate_sensitive_default_denies_without_a_fresh_token():
    """OCTOPUS_ARM_SENSITIVE_DEFAULT=1 + بدونِ arm-token → متوقف قبل از
    authorization_shadow و پیشنهادِ مالک (هیچ pending-patch نباید ساخته شود)
    و مالک باید یک opslib.alert ببیند — قبل از این فیکس این رد کاملاً بی‌صدا بود."""
    _arm_env(True)
    _clear_arm_state()
    os.environ["OCTOPUS_WIRE_PATCH_CARD"] = "1"
    pend = sp.opslib.STATE_DIR / "cortex" / "pending-patches"
    before = set(pend.glob("*.json")) if pend.exists() else set()
    sent, real_alert = [], sp.opslib.alert
    sp.opslib.alert = lambda msgs, **k: sent.extend(msgs)
    try:
        r = sp._offer_patch_to_owner(_offerable_patch("sp-arm1"))
        assert r.get("ok") is False, r
        assert str(r.get("reason", "")).startswith("arm-gate-denied"), r
        after = set(pend.glob("*.json")) if pend.exists() else set()
        assert after == before, "gate رد کرد ولی pending-patch نوشته شد"
        blob = " ".join(sent)
        assert "arm_gate" in blob and ALLOWED in blob, f"رد به مالک نرسید: {blob[:200]}"
    finally:
        sp.opslib.alert = real_alert
        os.environ.pop("OCTOPUS_WIRE_PATCH_CARD", None)
        _arm_env(False)
        _clear_arm_state()


def t_arm_gate_allow_does_not_spam_an_alert():
    """وقتی arm_gate عبور می‌دهد نباید هیچ آلارمی برای آن ساخته شود — آلارم فقط
    مالِ ردشدن است، نه هر عبورِ موفق."""
    _arm_env(True)
    _clear_arm_state()
    _ACTIVATION_FLAG.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVATION_FLAG.write_text("armed", encoding="utf-8")
    _write_arm_token("code_autonomy", "arm")
    _write_arm_token("code_autonomy", "arm2")
    os.environ["OCTOPUS_WIRE_PATCH_CARD"] = "1"
    sent, real_alert = [], sp.opslib.alert
    sp.opslib.alert = lambda msgs, **k: sent.extend(msgs)
    try:
        r = sp._offer_patch_to_owner(_offerable_patch("sp-arm4"))
        assert not str(r.get("reason", "")).startswith("arm-gate-denied"), r
        assert sent == [], f"عبورِ موفق آلارمِ اضافه ساخت: {sent}"
    finally:
        sp.opslib.alert = real_alert
        os.environ.pop("OCTOPUS_WIRE_PATCH_CARD", None)
        _arm_env(False)
        _clear_arm_state()


def t_arm_gate_sensitive_default_allows_with_a_fresh_two_key_token():
    """OCTOPUS_ARM_SENSITIVE_DEFAULT=1 + ACTIVATION flag + هر دو arm-token
    تازه → گیتِ هشتم رد می‌کند و جریان مثلِ قبل ادامه پیدا می‌کند."""
    _arm_env(True)
    _clear_arm_state()
    _ACTIVATION_FLAG.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVATION_FLAG.write_text("armed", encoding="utf-8")
    _write_arm_token("code_autonomy", "arm")
    _write_arm_token("code_autonomy", "arm2")
    os.environ["OCTOPUS_WIRE_PATCH_CARD"] = "1"
    try:
        r = sp._offer_patch_to_owner(_offerable_patch("sp-arm2"))
        assert not str(r.get("reason", "")).startswith("arm-gate-denied"), r
        assert r.get("ok") is True, r
    finally:
        os.environ.pop("OCTOPUS_WIRE_PATCH_CARD", None)
        _arm_env(False)
        _clear_arm_state()


def t_arm_gate_only_narrows_never_widens():
    """arm_gate نباید هیچ‌وقت چیزی را که هفت گیتِ قبلی رد کرده‌اند اجازه بدهد —
    حتی با arm-token معتبر، پچِ shadow_red همچنان not-offerable می‌ماند."""
    _arm_env(True)
    _clear_arm_state()
    _ACTIVATION_FLAG.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVATION_FLAG.write_text("armed", encoding="utf-8")
    _write_arm_token("code_autonomy", "arm")
    _write_arm_token("code_autonomy", "arm2")
    os.environ["OCTOPUS_WIRE_PATCH_CARD"] = "1"
    try:
        red = {"ok": False, "shadow_green": False, "content": "x",
               "target": ALLOWED, "id": "sp-arm3", "defect": "d"}
        r = sp._offer_patch_to_owner(red)
        assert r == {"ok": False, "reason": "not-offerable"}, r
    finally:
        os.environ.pop("OCTOPUS_WIRE_PATCH_CARD", None)
        _arm_env(False)
        _clear_arm_state()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_self_patch: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
