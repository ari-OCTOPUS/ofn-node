#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_orphans_wired — «ساخته شده ولی در تولید غیرقابلِ رسیدن» (اسکنِ ۹۲-شکاف).

چهار یتیمِ لِین، هر کدام با اثباتِ **رسیدن** نه اثباتِ وجود:
  ۱. `owner_menu.handle_panel_choice` → گزینهٔ ② واقعاً به `handle_new_mission`
     می‌رسد و `looks_like_lead` تنها گیتِ مسیرِ ثبتِ لید است (outer-bot-6).
  ۲. `decision_gate.pending_cards` → کارتی که هندلر داشت و امیتر نداشت حالا
     منبعِ انتخاب دارد؛ فقط از دفترِ واقعی، read-only (outer-bot-7).
  ۳. `leg_activation.guard_send` → قاعدهٔ «صفر template» ِ منشور §۵ به شکلی که
     مسیرِ ارسال بتواند مصرف کند.
  ۴. `surface-routing.json` → هر جریان یا producer دارد یا `_note` ِ صریح؛
     و `validate_contract.py` هنوز پاس می‌شود (در run_all ثبت است).

هیچ تستی چیزی نمی‌فرستد، به درختِ زنده نمی‌نویسد و توکن لمس نمی‌کند.
"""
import ast
import io
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-orphans-wired")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "telegram_contract"),
           str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mission_contract as mc      # noqa: E402
import owner_menu as om            # noqa: E402
import menu_integration as mi      # noqa: E402
import decision_gate as dg         # noqa: E402
import leg_activation as la        # noqa: E402
import surface_router as sr        # noqa: E402
import validate_contract as vc     # noqa: E402

ROUTING = _OPS / "telegram_center" / "surface-routing.json"
CENTER_SRC = (_OPS / "telegram_center" / "center.py").read_text("utf-8")

NOW = 1_785_460_000.0

# مدخل‌های بی‌producer که امروز **می‌دانیم** بی‌producer اند. این فهرست فقط حق
# دارد کوچک شود (وقتی کسی واقعاً وصل کرد) — بزرگ‌شدنش یعنی یک ادعای تازهٔ
# پوشش که پشتش کد نیست. گاردِ رگرسیون، نه سبزِ مطلق.
RESERVED_STREAMS = {
    "chat", "intuition", "doctor-daily", "critical-alerts", "organ-digest",
    "money-pulse", "approvals-organism", "legs-all", "center-status",
}


# ── ابزارِ اسکنِ producer (AST، نه grep) ─────────────────────────────────────
_SKIP_PARTS = {"tests", "__pycache__", "_Archive", "_Duplicates", "state", "manifests"}


def _literal_or_prefix(node):
    """(value, is_exact) برای Constant و JoinedStr؛ وگرنه (None, None)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, True
    if isinstance(node, ast.JoinedStr):
        pre = ""
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                pre += v.value
            else:
                break
        if pre:
            return pre, False
    return None, None


def _producers() -> tuple:
    """(exact, prefixed, where) از کلِ درختِ _ops بجز تست‌ها.

    صداکنندهٔ معتبر: `*._route_send(<stream>, …)` یا `resolve(<stream>, clients=…)`.
    نامِ متغیر یک پله دنبال می‌شود (doctor_link ِ زنده دقیقاً همین شکل است).
    f-string فقط تا جایی producer شمرده می‌شود که **پسوندش هم در همان فایل
    رشتهٔ ثابت باشد** — وگرنه «doctor-» به‌غلط `doctor-daily` را هم پوشیده
    نشان می‌داد، یعنی همان دروغِ نقشه‌ای که این فایل برای بستنش نوشته شد."""
    exact, prefixed, where = set(), [], {}
    for p in _OPS.rglob("*.py"):
        if any(part in _SKIP_PARTS for part in p.parts):
            continue
        try:
            tree = ast.parse(p.read_text("utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        names, consts = {}, set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                consts.add(n.value)
            if isinstance(n, ast.Assign):
                v, ex = _literal_or_prefix(n.value)
                if v:
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            names[t.id] = (v, ex)
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            fname = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
            if fname != "_route_send" and not (
                    fname == "resolve" and any(k.arg == "clients" for k in n.keywords)):
                continue
            args = list(n.args) + [k.value for k in n.keywords if k.arg == "stream"]
            if not args:
                continue
            v, ex = _literal_or_prefix(args[0])
            if v is None and isinstance(args[0], ast.Name):
                v, ex = names.get(args[0].id, (None, None))
            if v is None:
                continue                      # آرگومانِ پویا (خودِ _route_send) — نادیده
            site = f"{p.relative_to(_OPS)}:{n.lineno}"
            if ex:
                exact.add(v)
                where.setdefault(v, []).append(site)
            else:
                prefixed.append((v, frozenset(consts), site))
    return exact, prefixed, where


def _has_producer(stream: str, exact, prefixed) -> bool:
    if stream in exact:
        return True
    for pre, consts, _site in prefixed:
        if stream.startswith(pre) and stream[len(pre):] in consts:
            return True
    return False


def _routing() -> dict:
    return json.loads(ROUTING.read_text("utf-8"))


def _cbs(kb) -> list:
    return [b.get("callback_data") for row in (kb or []) for b in row
            if isinstance(b, dict)]


# ── ۱. پنل: گزینهٔ ② واقعاً به هندلر می‌رسد ─────────────────────────────────
class _Spy:
    def __init__(self, rec=None):
        self.calls, self.rec = [], rec or {"ok": True, "lead_id": "LD-spy-1"}

    def __call__(self, intent):
        self.calls.append(intent)
        return dict(self.rec)


def _free_deps(spy):
    """مالکِ اجازه‌داده: is_important=False تا مسیرِ ثبت واقعاً طی شود."""
    return {"register_lead": spy, "is_important": lambda _i: (False, "تستِ آزاد")}


def t_a_panel_option_two_reaches_the_real_mission_handler():
    """اثباتِ **رسیدن**: ورودیِ مالک → envelope معتبر + ثبتِ واقعیِ لید.
    تا ۰۷-۳۱ گزینهٔ ② فقط نثر برمی‌گرداند و این مسیر هرگز اجرا نمی‌شد."""
    spy = _Spy()
    text = "نقاشیِ داخلیِ خانهٔ مشتری در موزمن، قیمت می‌خوام"
    out = om.handle_panel_choice("m:mission", text, _free_deps(spy))
    assert out["kind"] == "mission", out
    env = out["mission"]
    assert env and mc.validate(env) == [], (env, mc.validate(env or {}))
    assert env["target_leg"] == "lead", env["target_leg"]
    assert spy.calls == [text], spy.calls               # هندلرِ واقعی صدا خورد
    assert env["status"] == "running" and env["output_refs"] == ["lead://LD-spy-1"], env
    assert "LD-spy-1" in out["text"]


def t_a_looks_like_lead_is_the_only_gate_of_capture():
    """`looks_like_lead` تا امروز صفر ارجاع داشت. حالا متنِ غیرِ لید ⇒ هیچ ثبتی."""
    spy = _Spy()
    out = om.handle_panel_choice("mission", "گزارشِ مصرفِ دیسکِ سرور را بده",
                                 _free_deps(spy))
    assert out["kind"] == "mission" and out["lead_gated"] is False, out
    assert spy.calls == [], spy.calls                   # مسیرِ لید اصلاً باز نشد
    assert out["mission"]["target_leg"] == om.NON_LEAD_LEG
    assert "لیدی ثبت نشد" in out["text"]


def t_a_mission_without_text_asks_and_fabricates_nothing():
    out = om.handle_panel_choice("m:mission", "", _free_deps(_Spy()))
    assert out["kind"] == "prompt" and out["mission"] is None, out
    assert "بنویس" in out["text"]


def t_a_important_request_is_gated_before_anything_runs():
    """مهم ⇒ needs_approval و **قبل از** هر ثبتی برمی‌گردد (فلسفهٔ مالک ۰۷-۱۸)."""
    spy = _Spy()
    out = om.handle_panel_choice("m:mission", "به مشتری پیش‌فاکتور بفرست و پول بگیر",
                                 {"register_lead": spy,
                                  "is_important": lambda _i: (True, "پول")})
    env = out["mission"]
    assert env["status"] == "needs_approval" and env["requires_approval"] is True, env
    assert spy.calls == [], spy.calls
    assert "منتظرِ رأیِ توست" in out["text"]


def t_a_panel_emits_only_callbacks_the_emitting_bot_handles():
    """درسِ «۳۵ کارتِ مرده»: هر دکمه‌ای که این ماژول می‌سازد باید در همان باتِ
    فرستنده هندلر داشته باشد. تنها فعلِ استفاده‌شده `m:` است و مرکز آن را
    مسیریابی می‌کند؛ و `m:home` واقعاً به خانهٔ پنل می‌رسد."""
    kbs = []
    for choice in ("m:mission", "m:bogus"):
        kbs += _cbs(om.handle_panel_choice(choice, "", None)["keyboard"])
    kbs += _cbs(om.handle_panel_choice("m:mission", "نقاشی", _free_deps(_Spy()))["keyboard"])
    assert kbs and set(kbs) == {"m:home"}, kbs
    assert 'if verb == "m":' in CENTER_SRC                 # مرکز فعلِ m را می‌شناسد
    txt, kb = mi.dispatch("m:home")                        # و مقصدِ دکمه واقعی است
    assert "پنل" in txt and _cbs(kb), (txt[:60], kb)


def t_a_other_options_stay_with_menu_integration():
    """پنل دو پیاده‌سازیِ موازی نمی‌سازد: بقیهٔ گزینه‌ها delegate اند."""
    for key in ("status", "mytasks", "legs", "report", "stop"):
        out = om.handle_panel_choice(key, "", None)
        assert out["kind"] == "delegate" and out["mission"] is None, (key, out)
    assert om.handle_panel_choice("m:nope", "", None)["kind"] == "unknown"


# ── ۲. decision_gate: کارتی که امیتر نداشت ─────────────────────────────────
def _clear_ledger():
    try:
        dg.LEDGER.unlink()
    except OSError:
        pass


def _put(action, *, trace, executor_owner=True, ts=None, evidence=None):
    """یک ردیفِ واقعی از راهِ خودِ decide/record — نه fixture ِ دست‌ساز."""
    rec = dg.decide(action=action, evidence=evidence or {}, risk_class=1, trace_id=trace)
    if not executor_owner:
        rec["executor"] = "ai"
    if ts is not None:
        import datetime as _dt
        rec["ts"] = _dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds")
    assert dg.record(rec)
    return rec


def t_b_pending_cards_surfaces_what_waits_for_the_owner():
    """`card()` هندلرِ dg:e: داشت و هیچ امیتری نداشت. حالا انتخاب واقعی است."""
    _clear_ledger()
    _put("بازآراییِ لاگ", trace="tr-owner-1", ts=NOW - 60)
    cards = dg.pending_cards(now=NOW)
    assert len(cards) == 1, (cards, dg.last_scan())
    c = cards[0]
    assert c["trace_id"] == "tr-owner-1" and "بازآراییِ لاگ" in c["text"]
    verbs = {str(cb).split(":")[0] for cb in _cbs(c["keyboard"])}
    assert verbs == {"ok", "no", "later", "dg"}, verbs
    # هر فعلِ این کارت در همان باتِ فرستنده (مرکز) هندلر دارد — وگرنه کارتِ مرده
    assert '_VERDICTS = ("ok", "no", "later")' in CENTER_SRC
    assert 'if verb == "dg"' in CENTER_SRC


def t_b_pending_cards_skips_ai_traceless_and_stale():
    _clear_ledger()
    _put("کارِ AI", trace="tr-ai", executor_owner=False, ts=NOW - 60)
    _put("بی‌ردپا", trace="", ts=NOW - 60)
    _put("کهنه", trace="tr-old", ts=NOW - dg.MAX_CARD_AGE_S - 10)
    _put("تازه", trace="tr-new", ts=NOW - 30)
    cards = dg.pending_cards(now=NOW)
    st = dg.last_scan()
    assert [c["trace_id"] for c in cards] == ["tr-new"], (cards, st)
    assert st["skipped_ai"] == 1 and st["skipped_no_trace"] == 1, st
    assert st["skipped_stale"] == 1, st


def t_b_pending_cards_dedupes_a_trace_and_honours_since_and_limit():
    _clear_ledger()
    _put("نسخهٔ اول", trace="tr-dup", ts=NOW - 500)
    _put("نسخهٔ دوم", trace="tr-dup", ts=NOW - 100)
    for i in range(4):
        _put(f"کارِ {i}", trace=f"tr-{i}", ts=NOW - 200 - i)
    cards = dg.pending_cards(now=NOW, limit=3)
    assert len(cards) == 3, cards
    dup = [c for c in dg.pending_cards(now=NOW, limit=99) if c["trace_id"] == "tr-dup"]
    assert len(dup) == 1 and "نسخهٔ دوم" in dup[0]["text"], dup
    # since = cursorِ صداکننده ⇒ idempotency بدونِ نویسندهٔ دوم روی state
    assert dg.pending_cards(now=NOW, limit=99, since=NOW - 50) == []
    assert [c["trace_id"] for c in dg.pending_cards(now=NOW, limit=99, since=NOW - 150)] \
        == ["tr-dup"]


def t_b_pending_cards_is_read_only_and_never_raises():
    _clear_ledger()
    _put("کاری", trace="tr-ro", ts=NOW - 10)
    before = dg.LEDGER.read_bytes()
    dg.pending_cards(now=NOW)
    assert dg.LEDGER.read_bytes() == before
    _clear_ledger()
    assert dg.pending_cards(now=NOW) == []               # دفترِ نبود → خالی، نه crash
    dg.LEDGER.parent.mkdir(parents=True, exist_ok=True)
    dg.LEDGER.write_text("{not json\n\n{\"schema\": \"other\"}\n", "utf-8")
    assert dg.pending_cards(now=NOW) == []
    assert dg.last_scan()["error"] == "", dg.last_scan()


# ── ۳. گاردِ صفر-template در فرمِ مسیرِ ارسال ───────────────────────────────
def t_c_guard_blocks_a_template_and_passes_a_real_event():
    blocked = la.guard_send("هیچ فعالیتی ثبت نشده است — گزارش خودکار", leg="mining")
    assert blocked["send"] is False and "template" in blocked["reason"], blocked
    ok = la.guard_send("۲ رگ در ۱۴:۰۲ ری‌استارت شد؛ هش‌ریت به ۹۲MH/s برگشت", leg="mining")
    assert ok["send"] is True, ok
    assert la.guard_send("", leg="mining")["send"] is False
    assert la.guard_send("گزارشِ {{leg_name}}", leg="mining")["send"] is False


def t_c_guard_allows_short_but_factual_and_names_its_reason():
    """allow-list: رخدادِ واقعی حق دارد کوتاه باشد اگر عدد/پول/زمان دارد."""
    assert la.guard_send("۳ لید نو", leg="lead")["send"] is True
    assert la.guard_send("AU$120", leg="accounting")["send"] is True
    thin = la.guard_send("سلام", leg="lead")
    assert thin["send"] is False and str(la.MIN_REAL_CHARS) in thin["reason"], thin
    named = la.guard_send("todo: بعداً پرش کن", leg="crypto")
    assert "todo:" in named["reason"], named          # **کدام** امضا، نه فقط «امضا»
    assert named["reason"].startswith("[crypto]")


def t_c_bool_guard_and_send_guard_never_disagree():
    """یک منبعِ حقیقت: هر متنی که گاردِ قدیمی template بداند، مسیرِ ارسال هم رد کند."""
    corpus = ["", "  ", "placeholder", "TBD", "گزارش خودکار", "{{x}}",
              "۳ لید نو", "AU$120", "این یک پیام تستی است",
              "۲ رگ در ۱۴:۰۲ ری‌استارت شد؛ هش‌ریت به ۹۲MH/s برگشت"]
    for t in corpus:
        if la.zero_template_guard(t):
            assert la.guard_send(t)["send"] is False, t


# ── ۴. surface-routing.json: نقشه = قلمرو ──────────────────────────────────
def t_d_every_stream_has_a_producer_or_an_explicit_note():
    exact, prefixed, _where = _producers()
    streams = _routing()["streams"]
    liars = [s for s, e in streams.items()
             if not _has_producer(s, exact, prefixed)
             and not str((e or {}).get("_note") or "").strip()]
    assert not liars, f"مدخلِ بی‌producer و بی‌_note (ادعای پوششِ بی‌پشتوانه): {liars}"


def t_d_producerless_set_only_shrinks():
    """رچت: وصل‌کردن مجاز است (فهرست کوچک شود)، اضافه‌کردنِ ادعای تازه نه."""
    exact, prefixed, _ = _producers()
    orphans = {s for s in _routing()["streams"]
               if not _has_producer(s, exact, prefixed)}
    assert orphans <= RESERVED_STREAMS, \
        f"مدخلِ بی‌producer ِ تازه: {orphans - RESERVED_STREAMS}"


def t_d_the_scanner_actually_finds_the_live_producers():
    """گاردِ بی‌دندان نباشد: اسکنر باید صداکننده‌های واقعیِ امروز را ببیند."""
    exact, prefixed, where = _producers()
    for s in ("center-digest", "center-decision", "center-urgent",
              "center-health-digest", "center-pulse", "center-alert", "code-card"):
        assert s in exact and where.get(s), (s, where.get(s))
    for s in ("doctor-intent", "doctor-diff"):           # f-string ِ doctor_link
        assert _has_producer(s, exact, prefixed), s
    assert not _has_producer("doctor-daily", exact, prefixed), \
        "پیشوندِ doctor- نباید daily را پوشیده نشان دهد"


def t_d_legs_all_note_is_true_not_decorative():
    """ادعای `_note` را با خودِ روتر بسنج: legs-all واقعاً تاپیک پیدا نمی‌کند."""
    entry = _routing()["streams"]["legs-all"]
    cfg = {"chat_id": -100123, "topics": {"lead": 22, "mining": 24}}
    assert sr._topic_id_for("legs-all", entry["target"], cfg) is None
    assert sr._topic_id_for("lead", {"surface": "group", "topic": "per-leg"}, cfg) == 22


def t_d_validate_contract_still_passes():
    """این validator در run_all ثبت است؛ ویرایشِ غلطِ فایل = سوییتِ قرمز."""
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = vc.main()
    assert code == 0, buf.getvalue()


def t_d_routing_file_is_still_parseable_by_the_live_router():
    """خودِ روتر (نه فقط json.loads) باید فایل را بخواند — fail-soft ِ روتر
    یک فایلِ خراب را بی‌صدا به {} تبدیل می‌کند، و آن سکوت باید دیده شود."""
    streams = sr._load_streams()
    assert set(streams) == set(_routing()["streams"]), (len(streams),)


def t_d_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(dg.LEDGER).lower().startswith(live), dg.LEDGER


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_orphans_wired: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
