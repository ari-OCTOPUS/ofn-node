"""test_initiative_worth_it.py — WS-5: ابتکارِ بی‌سقف ولی حساب‌پس‌ده.

رأیِ مالک ۲۰۲۶-۰۸-۰۱: «هر وقت چیزِ واقعی برای گفتن دارد» — سقفِ ۲/روز برداشته
شود. ولی شرطی که به رأیش چسباند خودِ نکته است: بی‌سقفِ **بی‌حساب** همان چیزی
است که گروه را به لولهٔ نویز تبدیل کرد.

پس این فایل سه چیز را می‌سنجد و یک چیز را نمی‌گذارد بلغزد:
  ۱. عدد جای خود را به **آستانهٔ ارزش** داد: بی‌دلیل = سکوت، و دلیل ثبت می‌شود.
  ۲. ساعتِ سکوت **دست‌نخورده** ماند (رأی دربارهٔ سقف بود، نه نیمه‌شب).
  ۳. هر ابتکار با سرنوشتش جفت می‌شود، و نرخ **سه‌حالتی** گزارش می‌شود.
  ۴. با فلگِ خاموش، رفتار **دقیقاً** رفتارِ امروز است — همان کلیدها، همان کارت.

دندان (teeth)
─────────────
همین فایل با ماژولِ **قبل از تغییر** هم اجرا می‌شود:
    set IV_TEETH_MODULE_DIR=<پوشه‌ای که initiative.py ِ HEAD در آن است>
آن‌وقت هر تستی که رفتارِ تازه را ادعا می‌کند باید بیفتد. اگر همه سبز بمانند،
یعنی تست چیزی را نمی‌سنجد که تغییر کرده باشد.
"""
import datetime as _dt
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("initiative-worth-it")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── سوئیچِ دندان: ماژولِ پیش-از-تغییر را مقدم کن ─────────────────────────────
_TEETH = os.environ.get("IV_TEETH_MODULE_DIR", "").strip()
if _TEETH:
    sys.path.insert(0, _TEETH)

import opslib             # noqa: E402,F401
import initiative as iv   # noqa: E402

# زمان‌ها از **ساعتِ محلیِ صریح** ساخته می‌شوند، نه از offsetِ epoch. ساعتِ سکوت
# پیش‌فرض ۰..۷ محلی است؛ اگر پایه را کور انتخاب کنیم، سوییت شب‌ها قرمز و روزها
# سبز می‌شود — دقیقاً همان دامی که یک‌بار در این ماژول افتاد.
_NOON = _dt.datetime(2026, 8, 1, 12, 0, 0).timestamp()
_QUIET_HOUR = _dt.datetime(2026, 8, 1, 3, 0, 0).timestamp()

_WHY = "چون سقفِ ماهانهٔ خرج امشب رد می‌شود و فقط تو می‌توانی تصمیم بگیری"
_BODY = "ا" * 90


def _reply(why=_WHY, kind="سوال", decline=False, body=_BODY):
    d = {"نوع": kind, "متن": body, "ارزشش_را_ندارد": decline}
    if why is not None:
        d["چرا_حالا"] = why
    return json.dumps(d, ensure_ascii=False)


def _fn(text=None):
    payload = _reply() if text is None else text

    def ask(*a, **k):
        return {"ok": True, "text": payload, "model": "test-brain",
                "tier": "primary"}
    return ask


def _reset(*, uncapped=None):
    for p in (iv.STATE, iv.LEDGER, getattr(iv, "ASK_LEDGER", iv.LEDGER)):
        try:
            p.unlink()
        except OSError:
            pass
    os.environ[iv.FLAG] = "1"
    ucf = getattr(iv, "UNCAPPED_FLAG", "OCTOPUS_INITIATIVE_UNCAPPED")
    if uncapped:
        os.environ[ucf] = "1"
    else:
        os.environ.pop(ucf, None)


def _ledger_rows():
    try:
        return [json.loads(l) for l in iv.LEDGER.read_text("utf-8").splitlines()
                if l.strip()]
    except OSError:
        return []


def _write_ask(epoch):
    """یک ردیف در دفترِ زندهٔ ask_brain — همان شکلی که تولید می‌نویسد."""
    p = iv.ASK_LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _dt.datetime.fromtimestamp(epoch).isoformat(
            timespec="seconds"), "schema": "tg-ask-brain.v1", "ok": True,
            "topic": "x"}, ensure_ascii=False) + "\n")


# ══ ۱. فلگِ خاموش = امروز، بی‌کم‌وکاست ═══════════════════════════════════════
def t_flag_off_still_caps_at_two_a_day():
    """پیش-از-تغییر: سومین پیامِ روز `daily-cap` می‌گیرد. این نصفهٔ بازسازیِ
    رفتارِ قدیم است — اگر روزی بیفتد یعنی فلگِ خاموش دیگر خاموش نیست."""
    _reset(uncapped=False)
    r1 = iv.speak(ask_fn=_fn(), now=_NOON)
    r2 = iv.speak(ask_fn=_fn(), now=_NOON + 4 * 3600 + 10)
    r3 = iv.speak(ask_fn=_fn(), now=_NOON + 8 * 3600 + 20)
    assert r1.get("ok") is True, r1
    assert r2.get("ok") is True, r2
    assert r3.get("ok") is False and r3.get("reason") == "daily-cap", r3


def t_flag_off_record_keys_are_byte_identical():
    _reset(uncapped=False)
    r = iv.speak(ask_fn=_fn(), now=_NOON)
    assert r.get("ok") is True, r
    rows = [x for x in _ledger_rows() if x.get("ok")]
    assert len(rows) == 1, rows
    assert set(rows[0]) == {"ts", "schema", "ok", "kind", "text", "why",
                            "model"}, sorted(rows[0])


def t_flag_off_delivers_even_without_a_reason():
    """امروز `چرا_حالا` **اختیاری** است — و همین چیزی است که تغییر می‌کند."""
    _reset(uncapped=False)
    r = iv.speak(ask_fn=_fn(_reply(why=None)), now=_NOON)
    assert r.get("ok") is True, r
    assert r.get("why") == "", r


def t_flag_off_card_has_no_account_line():
    _reset(uncapped=False)
    body, _ = iv.card({"kind": "سوال", "text": "م" * 70, "why": _WHY,
                       "worth_it": {"delivered": 9, "engaged": 0,
                                    "quieted": 1, "ignored": 8,
                                    "worth_it_rate": 0.0}})
    assert "حسابِ من" not in body, body[-200:]


# ══ ۲. بی‌سقف ═══════════════════════════════════════════════════════════════
def t_uncapped_passes_the_old_ceiling():
    """پنج پیام در یک روز — با سقفِ قدیم سومی می‌افتاد."""
    _reset(uncapped=True)
    gap = iv.UNCAPPED_MIN_GAP_S + 1
    oks = [iv.speak(ask_fn=_fn(), now=_NOON + i * gap) for i in range(5)]
    assert all(o.get("ok") for o in oks), [o.get("reason") for o in oks]
    st = json.loads(iv.STATE.read_text("utf-8"))
    assert int(st.get("used", 0)) == 5, st
    assert int(st.get("cap", 0)) <= 2, st   # سقف هنوز در state هست ولی دیگر نمی‌بندد


def t_uncapped_still_has_a_spend_brake():
    """بی‌سقف یعنی بی‌سقفِ **پیام**، نه تماسِ پولی در هر بیت."""
    _reset(uncapped=True)
    a = iv.speak(ask_fn=_fn(), now=_NOON)
    b = iv.speak(ask_fn=_fn(), now=_NOON + 60)
    assert a.get("ok") is True, a
    assert b.get("ok") is False and b.get("reason") == "too-soon", b
    # …ولی ترمز باید **ترمز** باشد نه سقفِ ۴ ساعتهٔ قبلی: نیم‌ساعت بعد باز است.
    c = iv.speak(ask_fn=_fn(), now=_NOON + iv.UNCAPPED_MIN_GAP_S + 1)
    assert c.get("ok") is True, c


# ══ ۳. ساعتِ سکوت دست‌نخورده ═════════════════════════════════════════════════
def t_quiet_hours_survive_the_uncapping():
    """رأیِ مالک دربارهٔ سقف بود، نه دربارهٔ نیمه‌شب."""
    _reset(uncapped=True)
    r = iv.speak(ask_fn=_fn(), now=_QUIET_HOUR)
    assert r.get("ok") is False and r.get("reason") == "quiet-hours", r
    assert not [x for x in _ledger_rows() if x.get("ok")], _ledger_rows()


# ══ ۴. آستانهٔ ارزش ═════════════════════════════════════════════════════════
def t_no_reason_no_message():
    _reset(uncapped=True)
    r = iv.speak(ask_fn=_fn(_reply(why=None)), now=_NOON)
    assert r.get("ok") is False and r.get("reason") == "no-justification", r
    assert not [x for x in _ledger_rows() if x.get("ok")], _ledger_rows()


def t_a_tick_is_not_a_reason():
    _reset(uncapped=True)
    r = iv.speak(ask_fn=_fn(_reply(why="مهم")), now=_NOON)
    assert r.get("ok") is False and r.get("reason") == "no-justification", r


def t_the_refusal_is_recorded_not_silent():
    """«نپرسید» باید از «پرسید و رد شد» جدا بماند — وگرنه دو سکوت یکی می‌شوند."""
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(_reply(why=None)), now=_NOON)
    rows = [x for x in _ledger_rows() if x.get("reason") == "no-justification"]
    assert len(rows) == 1, _ledger_rows()


def t_the_reason_is_persisted_with_the_message():
    _reset(uncapped=True)
    r = iv.speak(ask_fn=_fn(), now=_NOON)
    assert r.get("ok") is True, r
    row = [x for x in _ledger_rows() if x.get("ok")][0]
    assert row.get("why") == _WHY[:200], row.get("why")
    assert row.get("id") and row.get("outcome") == "open", row
    assert abs(float(row.get("ts_epoch")) - _NOON) < 0.001, row.get("ts_epoch")


# ══ ۵. جفت‌شدن با سرنوشت ════════════════════════════════════════════════════
def t_engagement_closes_the_loop():
    """مالک بعد از قطع‌شدن با اختاپوس حرف زد → `engaged`، از دفترِ زندهٔ ask_brain."""
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    _write_ask(_NOON + 900)
    out = iv.resolve_outcomes(now=_NOON + 1000)
    assert out.get("resolved") == 1, out
    st = iv.stats()
    assert st["engaged"] == 1 and st["ignored"] == 0, st
    assert st["worth_it_rate"] == 1.0, st
    oc = [x for x in _ledger_rows() if x.get("schema") == iv.OUTCOME_SCHEMA]
    assert oc and oc[0].get("wait_s") == 900.0, oc


def t_silence_past_the_window_is_ignored():
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    out = iv.resolve_outcomes(now=_NOON + iv.OUTCOME_WINDOW_S + 60)
    assert out.get("resolved") == 1, out
    st = iv.stats()
    assert st["ignored"] == 1 and st["engaged"] == 0, st
    assert st["worth_it_rate"] == 0.0, st


def t_an_ask_outside_the_window_does_not_count():
    """سیگنال باید **بعد** از ابتکار و **داخل** پنجره باشد."""
    _reset(uncapped=True)
    _write_ask(_NOON - 600)                      # قبلش
    _write_ask(_NOON + iv.OUTCOME_WINDOW_S + 60)  # بعد از پنجره
    iv.speak(ask_fn=_fn(), now=_NOON)
    iv.resolve_outcomes(now=_NOON + iv.OUTCOME_WINDOW_S + 120)
    st = iv.stats()
    assert st["engaged"] == 0 and st["ignored"] == 1, st


def t_still_open_inside_the_window():
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    iv.resolve_outcomes(now=_NOON + 600)
    st = iv.stats()
    assert st["open"] == 1 and st["resolved"] == 0, st


def t_unknown_is_not_zero():
    """سه‌حالتی: هنوز-نمی‌دانم ≠ به‌کارش-نیامد."""
    _reset(uncapped=True)
    st0 = iv.stats()
    assert st0["worth_it_rate"] is None, st0
    iv.speak(ask_fn=_fn(), now=_NOON)
    st1 = iv.stats()
    assert st1["delivered"] == 1 and st1["resolved"] == 0, st1
    assert st1["worth_it_rate"] is None, st1


def t_outcomes_are_appended_never_rewritten():
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    before = _ledger_rows()
    iv.resolve_outcomes(now=_NOON + iv.OUTCOME_WINDOW_S + 60)
    after = _ledger_rows()
    assert after[:len(before)] == before, "دفتر بازنویسی شد"
    assert len(after) == len(before) + 1, (len(before), len(after))


def t_resolution_is_idempotent():
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    iv.resolve_outcomes(now=_NOON + iv.OUTCOME_WINDOW_S + 60)
    n1 = len(_ledger_rows())
    iv.resolve_outcomes(now=_NOON + iv.OUTCOME_WINDOW_S + 999)
    assert len(_ledger_rows()) == n1, "سرنوشت دوباره ثبت شد"
    assert iv.stats()["ignored"] == 1, iv.stats()


def t_speak_resolves_without_a_new_caller():
    """سنجه روی سیمِ موجود سوار است: `organism.py → speak()` کافی است."""
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    r2 = iv.speak(ask_fn=_fn(), now=_NOON + iv.OUTCOME_WINDOW_S + 60)
    assert r2.get("ok") is True, r2
    st = iv.stats()
    assert st["ignored"] == 1, st
    # عکسِ حساب در لحظهٔ تصمیمِ دوم، **قبل** از خودش
    assert r2["worth_it"]["delivered"] == 1, r2["worth_it"]
    assert r2["worth_it"]["worth_it_rate"] == 0.0, r2["worth_it"]


# ══ ۶. دکمهٔ «کمتر حرف بزن» زنده می‌ماند ═══════════════════════════════════
def t_quieter_is_not_a_dead_button_when_uncapped():
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    r = iv.quieter()
    assert r.get("ok") is True, r
    assert r.get("gap_floor_h") == round(iv.UNCAPPED_MIN_GAP_S * 2 / 3600.0, 2), r
    assert r.get("outcome_recorded") is True, r
    st = iv.stats()
    assert st["quieted"] == 1, st
    assert st["worth_it_rate"] == 0.0, st


def t_quieter_actually_widens_the_brake():
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    iv.quieter()
    r = iv.speak(ask_fn=_fn(), now=_NOON + iv.UNCAPPED_MIN_GAP_S + 60)
    assert r.get("ok") is False and r.get("reason") == "too-soon", r


def t_the_brake_survives_midnight():
    """تپِ مالک نباید هر نیمه‌شب بی‌صدا باطل شود."""
    _reset(uncapped=True)
    iv.speak(ask_fn=_fn(), now=_NOON)
    iv.quieter()
    d = json.loads(iv.STATE.read_text("utf-8"))
    floor = float(d["gap_floor"])
    d["date"] = "1999-01-01"
    iv.STATE.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
    iv._take(_NOON + 10 * 3600)
    d2 = json.loads(iv.STATE.read_text("utf-8"))
    assert float(d2.get("gap_floor", 0)) == floor, d2


def t_quieter_flag_off_is_unchanged():
    _reset(uncapped=False)
    r = iv.quieter()
    assert set(r) == {"ok", "cap"}, r
    assert r["cap"] == 1, r
    assert not [x for x in _ledger_rows()
                if x.get("schema") == iv.OUTCOME_SCHEMA], _ledger_rows()


# ══ ۷. مالک عدد را می‌بیند ═════════════════════════════════════════════════
def t_the_card_shows_the_bill():
    _reset(uncapped=True)
    body, kb = iv.card({"kind": "سوال", "text": "م" * 70, "why": _WHY,
                        "worth_it": {"delivered": 9, "engaged": 0,
                                     "quieted": 1, "ignored": 8,
                                     "worth_it_rate": 0.0}})
    assert "حسابِ من" in body, body[-200:]
    assert "۹" in body and "۰" in body, body[-200:]
    verbs = {b["callback_data"].split(":")[0] for row in kb for b in row}
    assert "iv" in verbs, kb   # دکمهٔ مرده اضافه نشده، دکمهٔ زنده حذف نشده


def t_the_card_stays_silent_while_unknown():
    _reset(uncapped=True)
    body, _ = iv.card({"kind": "خبر", "text": "م" * 70, "why": _WHY,
                       "worth_it": {"delivered": 1, "engaged": 0, "quieted": 0,
                                    "ignored": 0, "worth_it_rate": None}})
    assert "حسابِ من" not in body, body[-200:]


# ══ ۸. سیم‌کشی: چیزی که صداکننده ندارد مرده است ═════════════════════════════
def t_the_new_measures_are_actually_called():
    """AST: `speak` هم `resolve_outcomes` و هم `stats` را صدا می‌زند."""
    import ast
    src = Path(iv.__file__).read_text("utf-8")
    fn = [n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == "speak"][0]
    called = {n.func.id for n in ast.walk(fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "resolve_outcomes" in called, sorted(called)
    assert "stats" in called, sorted(called)


def t_speak_still_has_a_production_caller():
    """`organism.py` هنوز `initiative.speak()` را صدا می‌زند."""
    import ast
    src = (_OPS / "organism.py").read_text("utf-8")
    hits = 0
    for n in ast.walk(ast.parse(src)):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "speak"
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id.endswith("iv")):
            hits += 1
    assert hits >= 1, hits


def t_no_send_no_secret_no_subprocess():
    """مرزِ ماژول نلغزید: فقط متن، هیچ اجرا، هیچ شبکه."""
    import ast
    tree = ast.parse(Path(iv.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "smtplib", "http"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)


TESTS = [
    ("(1a) فلگ خاموش: سقفِ ۲/روز سرِ جایش", t_flag_off_still_caps_at_two_a_day),
    ("(1b) فلگ خاموش: کلیدهای رکورد عوض نشده",
     t_flag_off_record_keys_are_byte_identical),
    ("(1c) فلگ خاموش: بی‌دلیل هم می‌فرستد",
     t_flag_off_delivers_even_without_a_reason),
    ("(1d) فلگ خاموش: کارت خطِ حساب ندارد", t_flag_off_card_has_no_account_line),
    ("(2a) بی‌سقف: از سقفِ قدیم رد می‌شود", t_uncapped_passes_the_old_ceiling),
    ("(2b) بی‌سقف ولی ترمزِ خرج دارد", t_uncapped_still_has_a_spend_brake),
    ("(3)  ساعتِ سکوت دست‌نخورده", t_quiet_hours_survive_the_uncapping),
    ("(4a) بی‌دلیل = سکوت", t_no_reason_no_message),
    ("(4b) تیک دلیل نیست", t_a_tick_is_not_a_reason),
    ("(4c) ردّ ِ بی‌دلیل ثبت می‌شود", t_the_refusal_is_recorded_not_silent),
    ("(4d) دلیل با پیام ثبت می‌شود", t_the_reason_is_persisted_with_the_message),
    ("(5a) جواب داد → engaged", t_engagement_closes_the_loop),
    ("(5b) سکوتِ بعد از پنجره → ignored", t_silence_past_the_window_is_ignored),
    ("(5c) سؤالِ بیرونِ پنجره نمی‌شمارد", t_an_ask_outside_the_window_does_not_count),
    ("(5d) داخلِ پنجره هنوز باز است", t_still_open_inside_the_window),
    ("(5e) نمی‌دانم ≠ صفر", t_unknown_is_not_zero),
    ("(5f) دفتر append-only ماند", t_outcomes_are_appended_never_rewritten),
    ("(5g) بستنِ سرنوشت idempotent است", t_resolution_is_idempotent),
    ("(5h) speak بدونِ صداکنندهٔ تازه می‌بندد", t_speak_resolves_without_a_new_caller),
    ("(6a) «کمتر حرف بزن» مرده نشد",
     t_quieter_is_not_a_dead_button_when_uncapped),
    ("(6b) تپ واقعاً ترمز را پهن می‌کند", t_quieter_actually_widens_the_brake),
    ("(6c) ترمز از نیمه‌شب جان سالم می‌برد", t_the_brake_survives_midnight),
    ("(6d) فلگ خاموش: quieter عوض نشده", t_quieter_flag_off_is_unchanged),
    ("(7a) کارت حساب را نشان می‌دهد", t_the_card_shows_the_bill),
    ("(7b) کارت تا نامعلوم است ساکت می‌ماند", t_the_card_stays_silent_while_unknown),
    ("(8a) سنجه‌ها واقعاً صدا زده می‌شوند", t_the_new_measures_are_actually_called),
    ("(8b) speak صداکنندهٔ تولیدی دارد", t_speak_still_has_a_production_caller),
    ("(8c) مرزِ ماژول نلغزید", t_no_send_no_secret_no_subprocess),
]


def main() -> int:
    passed, failed = 0, []
    for name, fn in TESTS:
        try:
            fn()
            passed += 1
            print(f"  ✅ {name}")
        except Exception as e:  # noqa: BLE001
            failed.append((name, f"{type(e).__name__}: {e}"))
            print(f"  ❌ {name} — {type(e).__name__}: {e}")
    print(f"\n{'✅' if not failed else '❌'} test_initiative_worth_it: "
          f"{passed}/{len(TESTS)} passed, {len(failed)} failed"
          + (f"  [TEETH MODE: {_TEETH}]" if _TEETH else ""))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
