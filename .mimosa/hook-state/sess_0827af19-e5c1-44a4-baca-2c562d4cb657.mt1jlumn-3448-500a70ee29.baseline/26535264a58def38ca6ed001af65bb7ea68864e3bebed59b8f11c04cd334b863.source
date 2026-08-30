#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_receive_probe.py — پروبِ «تلگرام چیزی نگه داشته؟» بدونِ لمسِ شبکه.

چه چیزی این‌جا قفل می‌شود
─────────────────────────
ابزارِ زیرِ تست (`_ops/tg_receive_probe.py`) قرار است دقیقاً همان نقطهٔ کوری را
روشن کند که صبحِ ۰۸-۰۱ دو ساعت خورد: **باتِ کر و صبحِ ساکت از بیرون یک شکل‌اند.**
ولی خودِ ابزار سه راهِ خراب‌شدن دارد که هر سه بی‌صدایند، پس هر سه تست دارند:

  ۱. **دزدیدنِ پیامِ مالک.** یک `getUpdates` ِ کنجکاوانه از این‌جا، آپدیت را از
     دهانِ تنها pollerِ مشروع بیرون می‌کشد و برای همیشه نابودش می‌کند. پس
     غیرمجاز بودنِ متد **ساختاری** است، نه یک قاعدهٔ نانوشته — و خودِ transport ِ
     ساختگی هم دیده‌بانی می‌کند.
  ۲. **نشتِ توکن.** ظریف‌ترین مسیر این نیست که ما چاپش کنیم؛ این است که
     **تلگرام** خودش پسش بدهد: الگوی متعارفِ webhook توکن را داخلِ مسیرِ URL
     می‌گذارد و `getWebhookInfo` همان را در `url`/`last_error_message` برمی‌گرداند.
  ۳. **سبزِ ناشی از غیاب.** پروسه‌ای که درست بعد از یک دورِ موفق مرده، فایلی با
     `last_ok_ts` ِ درخشان جا می‌گذارد. اگر فقط آن را بخوانیم، یک باتِ مرده
     «✅ سالم» گزارش می‌شود — یعنی همان باگ، با یک لایه رنگِ تازه.

هیچ تستی به شبکه نمی‌زند: transport تزریق می‌شود و هر توکنی ساختگی است.
"""
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import harness  # noqa: E402

ENV = harness.setup("tg-receive-probe")     # قبل از هر importی که state می‌خواند

import tg_receive_probe as probe            # noqa: E402
from telegram_center import tg_api          # noqa: E402

FAKE_MAIN = "1111111:AAAA-fake-main-token-never-real-xyz"
FAKE_CENTER = "2222222:BBBB-fake-center-token-never-real-abc"
BOTH = {"TELEGRAM_BOT_TOKEN": FAKE_MAIN, "TG_CENTER_BOT_TOKEN": FAKE_CENTER}
API = "https://api.telegram.org/bot"

# ── حسابرسیِ فایل: هر open در سطحِ مفسر ثبت می‌شود (audit hook، نه patch ِ
#    شکننده؛ os.open و io.open و pathlib همه از این‌جا رد می‌شوند). ──────────
_OPENS: list[str] = []
_RECORDING = [False]


def _audit(event, args):
    if event == "open" and _RECORDING[0]:
        try:
            _OPENS.append(str(args[0]))
        except Exception:  # noqa: BLE001
            pass


sys.addaudithook(_audit)


def _record_opens(fn, *a, **kw):
    _OPENS.clear()
    _RECORDING[0] = True
    try:
        return fn(*a, **kw)
    finally:
        _RECORDING[0] = False


# ── transport ِ ساختگی ───────────────────────────────────────────────────────
def _me(username="octo_bot"):
    return {"ok": True, "result": {"id": 111, "is_bot": True, "username": username}}


def _hook(pending=0, url="", last_error=""):
    return {"ok": True, "result": {"url": url, "pending_update_count": pending,
                                   "last_error_message": last_error,
                                   "last_error_date": 0}}


def _make_get(responses: dict, calls: list):
    """(url, timeout) → پاسخِ کنسروی. خودش هم دیده‌بانِ getUpdates است."""
    def get(url, timeout_s):
        assert url.startswith(API), f"میزبانِ غیرمجاز: {url[:40]}"
        token, _, method = url[len(API):].partition("/")
        method = method.split("?")[0]
        calls.append(method)
        assert method != "getUpdates", "پروب هرگز نباید getUpdates بزند"
        r = responses.get(token, {}).get(method)
        if r is None:
            raise OSError("no canned response")
        if isinstance(r, Exception):
            raise r
        return r
    return get


def _canned(pending_main=0, pending_center=0, user_main="octo_main",
            user_center="octo_center", hook_center="", err_center=""):
    return {FAKE_MAIN: {"getMe": _me(user_main), "getWebhookInfo": _hook(pending_main)},
            FAKE_CENTER: {"getMe": _me(user_center),
                          "getWebhookInfo": _hook(pending_center, hook_center,
                                                  err_center)}}


def _bot(report, env_var):
    return next(b for b in report["bots"] if b["env_var"] == env_var)


def _write_health(**kw):
    p = tg_api._poll_health_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(kw), "utf-8")
    return p


def _clear_health():
    p = tg_api._poll_health_path()
    if p.exists():
        p.unlink()
    return p


# ─────────────────────────────────────────────────────────────────────────────
def t_a_a_missing_token_is_answered_not_hunted_for():
    """توکن نیست ⇒ حرفِ صریح، نه crash و نه گشتن دنبالِ فایلِ secret.

    رأیِ مالک (سوالِ ۶، ۰۸-۰۱) مشخصاً برای مسیرِ **متغیرِ محیطی** بود. یک
    fallback ِ «شاید در .env باشد» هم قانونِ .agentignore را می‌شکند و هم
    ابزاری می‌سازد که توکن را از جایی می‌خواند که مالک انتظارش را ندارد.

    شاهد: audit hook ِ مفسر — هر open ِ واقعی ثبت می‌شود، نه ادعای ما."""
    _clear_health()
    calls = []
    probe.local_poll_health()                  # گرم‌کردنِ import ِ تنبل، بیرونِ ضبط
    rep = _record_opens(probe.build_report, get_fn=_make_get({}, calls),
                        environ={"PATH": "x"})
    assert calls == [], f"بدونِ توکن نباید هیچ تماسی رخ دهد: {calls}"
    for b in rep["bots"]:
        assert b["token_present"] is False, b
        assert b["verdict"] == "no_token", b

    forbidden = (".env", "secret", "wallet", "seed", ".pem", "flags.cmd")
    for path in _OPENS:
        low = path.lower()
        assert not any(f in low for f in forbidden), f"فایلِ ممنوع باز شد: {path}"
    names = {Path(p).name for p in _OPENS}
    assert names <= {"poll-health.json"}, f"فایلِ نامنتظر باز شد: {names}"

    text = probe.render(rep, environ={})
    assert "TELEGRAM_BOT_TOKEN" in text and "ست نیست" in text, text
    assert probe.exit_code(rep) == 2, "نامعلوم هرگز ۰ نیست"


def t_b_the_token_never_reaches_the_output_through_the_real_env_path():
    """مسیرِ تولیدی: توکن در os.environ، environ ِ پیش‌فرض، خروجیِ متن و JSON.

    نه خودِ توکن و نه نیمهٔ محرمانه‌اش نباید هیچ‌جا دیده شوند — mask هم نه."""
    import os
    _clear_health()
    saved = {k: os.environ.get(k) for k in BOTH}
    try:
        os.environ.update(BOTH)
        calls = []
        rep = probe.build_report(get_fn=_make_get(_canned(), calls))
        text = probe.render(rep)
        js = probe.render_json(rep)
        blob = text + "\n" + js + "\n" + json.dumps(rep, ensure_ascii=False)
        for tok in (FAKE_MAIN, FAKE_CENTER):
            assert tok not in blob, "توکنِ کامل در خروجی!"
            assert tok.split(":", 1)[1] not in blob, "نیمهٔ محرمانهٔ توکن در خروجی!"
        assert "octo_main" in text and "octo_center" in text, text
        assert json.loads(js)["schema"] == probe.SCHEMA
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def t_c_a_token_telegram_hands_back_is_redacted():
    """تلگرام خودش توکن را پس می‌دهد ⇒ باز هم نباید چاپ شود.

    سناریوی واقعی و نه فرضی: webhook را با الگوی متعارفِ `/bot<token>/hook` ست
    کرده‌اند؛ `getWebhookInfo` همان رشته را در `url` و در متنِ خطا برمی‌گرداند.
    ابزار عمداً `url` را برنمی‌گرداند (فقط host)، ولی `last_error_message` راهِ
    دومِ ورود است — و scrub ِ نهایی باید بگیردش."""
    _clear_health()
    hook_url = f"https://evil.example/bot{FAKE_CENTER}/hook"
    calls = []
    rep = probe.build_report(
        get_fn=_make_get(_canned(hook_center=hook_url,
                                 err_center=f"SSL error for {hook_url}"), calls),
        environ=dict(BOTH))
    c = _bot(rep, "TG_CENTER_BOT_TOKEN")
    assert c["webhook_host"] == "evil.example", c
    # scrub در سرچشمه: خودِ ساختارِ گزارش هم باید پاک باشد، نه فقط چاپش
    assert FAKE_CENTER not in json.dumps(c, ensure_ascii=False), \
        "توکن نباید حتی واردِ ساختارِ گزارش شود"
    assert probe._REDACTED in c["last_error_message"], c["last_error_message"]
    assert rep["secret_leaks_redacted"] >= 1, rep["secret_leaks_redacted"]

    text = probe.render(rep, environ=dict(BOTH))
    assert FAKE_CENTER not in text and FAKE_CENTER.split(":", 1)[1] not in text, text
    assert probe._REDACTED in text, "نشتی باید redact ِ دیده‌شدنی داشته باشد"
    assert "redact" in text, "نشتی باید صریح گزارش شود، نه بی‌صدا پاک"

    js = probe.render_json(rep, environ=dict(BOTH))
    assert FAKE_CENTER not in js, js[:200]
    assert json.loads(js).get("secret_leaks_redacted", 0) >= 1, "JSON باید معتبر بماند"

    # راهِ دومِ ورود: `description` ِ خودِ تلگرام روی یک getMe ِ شکست‌خورده.
    # (توکنِ باطل‌شده ⇒ ۴۰۱ ⇒ متنی که می‌تواند URL ِ درخواست را نقل کند.)
    rep2 = probe.build_report(
        get_fn=_make_get({FAKE_MAIN: {"getMe": {"ok": False, "error_code": 401,
                                                "description": f"Unauthorized: {API}"
                                                               f"{FAKE_MAIN}/getMe"}}},
                         []),
        environ={"TELEGRAM_BOT_TOKEN": FAKE_MAIN})
    m = _bot(rep2, "TELEGRAM_BOT_TOKEN")
    assert m["verdict"] == "auth_failed", m
    assert FAKE_MAIN not in json.dumps(m, ensure_ascii=False), \
        "description ِ تلگرام هم باید در سرچشمه scrub شود"
    assert probe._REDACTED in m["transport_error"], m["transport_error"]


def t_d_getupdates_is_structurally_impossible():
    """هیچ مسیرِ کدی نمی‌تواند به getUpdates برسد — حتی با آرگومانِ اشتباه."""
    for bad in ("getUpdates", "deleteWebhook", "sendMessage", "setWebhook"):
        try:
            probe._build_url(FAKE_MAIN, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"متدِ {bad} نباید URL بگیرد")
    assert probe._build_url(FAKE_MAIN, "getMe").startswith(API)

    _clear_health()
    calls = []
    probe.build_report(get_fn=_make_get(_canned(), calls), environ=dict(BOTH))
    assert calls, "باید واقعاً تماس گرفته باشد"
    assert set(calls) <= {"getMe", "getWebhookInfo"}, calls


def t_e_the_probe_writes_nothing_into_organism_state():
    """اجرا در هر لحظه‌ای بی‌خطر است ⇒ باید اثباتش کرد، نه ادعا.

    عکسِ کاملِ درختِ state قبل و بعد گرفته می‌شود (نام + اندازه + mtime_ns)."""
    tg_api._record_poll(True)                       # فایل باید از قبل باشد
    state_dir = Path(ENV["ops"]) / "state"

    def snap():
        return {str(p): (p.stat().st_size, p.stat().st_mtime_ns)
                for p in sorted(state_dir.rglob("*")) if p.is_file()}

    before = snap()
    assert before, "درختِ state نباید خالی باشد وگرنه تست هیچ نمی‌سنجد"
    calls = []
    probe.build_report(get_fn=_make_get(_canned(), calls), environ=dict(BOTH))
    probe.render(probe.build_report(get_fn=_make_get(_canned(), calls),
                                    environ=dict(BOTH)), environ=dict(BOTH))
    assert snap() == before, "پروب به state دست زد"


def t_f_the_local_view_reads_the_very_file_the_poller_writes():
    """نویسنده و خواننده با هم سنجیده می‌شوند، نه هرکدام با فیکسچرِ خودش.

    اگر مسیرِ فایل روزی در tg_api عوض شود و این‌جا کپیِ کهنه بماند، پروب برای
    همیشه «نامعلوم» می‌گوید و کسی نمی‌فهمد."""
    _clear_health()
    assert probe.local_poll_health()["status"] == "unknown"
    tg_api._record_poll(True)                       # همان نویسندهٔ واقعی
    h = probe.local_poll_health()
    assert h["file_present"] is True, h
    assert h["source"] == "tg_api", h
    assert h["status"] == "ok", h
    assert h["last_ok_age_s"] is not None and h["last_ok_age_s"] < 60, h


def t_g_a_writer_that_went_silent_is_never_reported_healthy():
    """قاتلِ «سبزِ ناشی از غیاب».

    فایل می‌گوید ۳۰ ثانیه پیش یک دورِ **موفق** داشتیم و صفر شکست — یعنی از هر
    زاویه‌ای درخشان. ولی آخرین دورِ ثبت‌شده ۱۵ دقیقه پیش است: پروسه درست بعد از
    آن موفقیت مرده. اگر فقط `last_ok_ts` خوانده شود، یک باتِ مرده «✅ سالم»
    گزارش می‌شود."""
    now = time.time()
    _write_health(last_ok_ts=now - 30, last_round_ts=now - 900,
                  consecutive_failures=0, last_reason="")
    h = probe.local_poll_health(now=now)
    assert h["status"] == "silent", f"نویسندهٔ ساکت باید دیده شود: {h}"
    assert h["last_ok_age_s"] < 60, h               # یعنی واقعاً «سالم به‌نظر» بود


def t_h_pending_plus_a_sick_poller_is_the_deaf_verdict():
    """قلبِ ماجرا: هیچ‌کدام از دو نما به‌تنهایی این را نمی‌گفت."""
    calls = []
    rep = probe.build_report(get_fn=_make_get(_canned(pending_center=7), calls),
                             environ=dict(BOTH), health={"status": "silent"})
    assert _bot(rep, "TG_CENTER_BOT_TOKEN")["verdict"] == "deaf", rep["bots"]
    assert probe.exit_code(rep) == 1

    rep2 = probe.build_report(get_fn=_make_get(_canned(pending_center=7), calls),
                              environ=dict(BOTH), health={"status": "ok"})
    assert _bot(rep2, "TG_CENTER_BOT_TOKEN")["verdict"] == "backlog", rep2["bots"]


def t_i_an_absent_or_never_successful_file_is_unknown_not_healthy():
    _clear_health()
    assert probe.local_poll_health()["status"] == "unknown"
    now = time.time()
    _write_health(last_ok_ts=0, last_round_ts=now - 5, consecutive_failures=1,
                  last_reason="URLError")
    h = probe.local_poll_health(now=now)
    assert h["file_present"] is True, h
    assert h["status"] == "unknown", f"بوتِ بی‌موفقیت = نمی‌دانم، نه سالم: {h}"


def t_j_the_local_view_is_pinned_to_the_bot_that_actually_writes_it():
    """فایلِ poll-health را فقط پولرِ مرکز می‌نویسد.

    چسباندنش به باتِ دیگر یعنی گزارشی که با شاهدِ **بات ب** دربارهٔ **بات الف**
    حکم می‌دهد — مؤدبانه، ولی دروغ."""
    calls = []
    rep = probe.build_report(
        get_fn=_make_get(_canned(pending_main=1, pending_center=1), calls),
        environ=dict(BOTH), health={"status": "silent"})
    assert rep["health_owner_env"] == "TG_CENTER_BOT_TOKEN", rep["health_owner_env"]
    assert _bot(rep, "TG_CENTER_BOT_TOKEN")["verdict"] == "deaf"
    m = _bot(rep, "TELEGRAM_BOT_TOKEN")
    assert m["local"]["status"] == "not_covered", m["local"]
    assert m["verdict"] == "ok", f"شاهدِ باتِ دیگر نباید به این بات بچسبد: {m}"

    # مرکز که توکن ندارد ⇒ نویسنده باتِ اصلی است (همان fallback ِ tg_api)
    assert probe.health_owner_env({"TELEGRAM_BOT_TOKEN": FAKE_MAIN}) \
        == "TELEGRAM_BOT_TOKEN"


def t_k_two_env_vars_pointing_at_one_bot_is_a_409_warning():
    """یک بات و دو پولر = هرکدام آپدیتِ دیگری را می‌بلعد؛ شکلِ دیگرِ «نمی‌شنویم»."""
    calls = []
    rep = probe.build_report(
        get_fn=_make_get(_canned(user_main="same_bot", user_center="same_bot"), calls),
        environ=dict(BOTH))
    assert rep["shared_bot_usernames"] == ["same_bot"], rep["shared_bot_usernames"]
    assert probe.exit_code(rep) == 1
    assert "۴۰۹" in probe.render(rep, environ=dict(BOTH))


def t_l_a_network_failure_is_unknown_not_healthy():
    _clear_health()
    calls = []
    rep = probe.build_report(get_fn=_make_get({}, calls), environ=dict(BOTH))
    for b in rep["bots"]:
        assert b["verdict"] == "unreachable", b
        assert b["auth"] == "unreachable", b
    assert probe.exit_code(rep) == 2, "شبکهٔ خراب ≠ سالم"


def t_m_a_genuinely_quiet_morning_is_allowed_to_be_green():
    """گاردی که همیشه قرمز باشد قابلیت نیست. صفِ خالی + پولرِ سالم = سبز."""
    _clear_health()
    tg_api._record_poll(True)
    calls = []
    rep = probe.build_report(get_fn=_make_get(_canned(), calls), environ=dict(BOTH))
    assert _bot(rep, "TG_CENTER_BOT_TOKEN")["verdict"] == "ok", rep["bots"]
    assert probe.exit_code(rep) == 0, rep
    assert "واقعاً کسی پیام نداده" in probe.render(rep, environ=dict(BOTH))


def t_n_the_last_ditch_net_catches_a_field_that_forgot_to_scrub():
    """سدِ دوم **مستقل از** سدِ اول سنجیده می‌شود.

    فردا فیلدی به گزارش اضافه می‌شود و کسی یادش می‌رود در سرچشمه scrub کند.
    آن‌وقت تنها چیزِ باقی‌مانده بینِ توکن و ترمینال همین scrub ِ نهایی است — پس
    باید شاهدِ خودش را داشته باشد، نه این‌که چون سدِ اول کار کرد سبز به‌نظر
    برسد. دو مسیرِ چاپ جدا سنجیده می‌شوند چون رفتارشان یکی نیست: `render_json`
    کلِ dict را می‌ریزد (هر فیلدی، حتی ناشناخته)، ولی `render` فقط فیلدهای
    شناخته‌شده را می‌نویسد."""
    calls = []
    rep = probe.build_report(get_fn=_make_get(_canned(), calls), environ=dict(BOTH))
    assert rep["secret_leaks_redacted"] == 0, "پایه باید تمیز باشد وگرنه تست هیچ نمی‌سنجد"
    assert FAKE_MAIN not in probe.render(rep, environ=dict(BOTH))

    # (۱) فیلدی که هیچ‌کس نمی‌شناسد ⇒ فقط JSON آن را چاپ می‌کند
    rep["bots"][0]["future_field_someone_forgot"] = f"oops {FAKE_MAIN} oops"
    js = probe.render_json(rep, environ=dict(BOTH))
    assert FAKE_MAIN not in js and FAKE_MAIN.split(":", 1)[1] not in js, js[:300]
    assert probe._REDACTED in js, js[:300]
    assert json.loads(js)["secret_leaks_redacted"] >= 1

    # (۲) فیلدی که **چاپ می‌شود** ولی در سرچشمه دست‌نخورده مانده ⇒ سدِ رندر
    rep["bots"][0]["username"] = f"x{FAKE_MAIN}x"
    text = probe.render(rep, environ=dict(BOTH))
    assert FAKE_MAIN not in text and FAKE_MAIN.split(":", 1)[1] not in text, text
    assert probe._REDACTED in text and "redact" in text, text


def t_o_a_non_json_answer_is_unknown_not_a_traceback():
    """پاسخی که JSON نیست باید «نامعلوم» شود، نه crash.

    این ابزار دقیقاً برای لحظه‌های خرابی ساخته شده، و در همان لحظه‌ها پاسخ
    همیشه JSON نیست: پورتالِ اسیرِ وای‌فای یک صفحهٔ HTML با کدِ ۲۰۰ برمی‌گرداند،
    یک پراکسی ۵۰۲ ِ HTML می‌دهد، یک بایتِ خراب decode نمی‌شود. هر سه از راهِ
    `json.JSONDecodeError`/`UnicodeDecodeError` می‌آیند که **زیرشاخهٔ
    ValueError** اند — پس اگر ValueError از `_api` رد شود، ابزار به‌جای گزارش
    با traceback می‌میرد."""
    for boom in (json.JSONDecodeError("Expecting value", "<html>502</html>", 0),
                 UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 1, "invalid start byte")):
        rep = probe.build_report(
            get_fn=_make_get({FAKE_MAIN: {"getMe": boom}}, []),
            environ={"TELEGRAM_BOT_TOKEN": FAKE_MAIN}, health={"status": "ok"})
        m = _bot(rep, "TELEGRAM_BOT_TOKEN")
        assert m["verdict"] == "unreachable", f"{type(boom).__name__} ⇒ {m}"
        assert m["transport_error"] == type(boom).__name__, m
        assert probe.exit_code(rep) == 2, "پاسخِ نامفهوم ≠ سالم"
    # ولی allowlist هنوز باید بلند بشکند — «نامعلوم‌کردن» نباید گاردِ ساختاری را
    # هم بی‌صدا کند.
    try:
        probe._api(FAKE_MAIN, "getUpdates", lambda u, t: {}, 1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("_api نباید getUpdates را قبول کند")
    # و سدِ میزبان روی getter ِ **واقعی** (تنها جایی که به شبکه می‌رسد): باید
    # قبل از هر تماسی بشکند، نه بعدش. آدرس عمداً 127.0.0.1 است تا اگر روزی این
    # گارد برداشته شود، تست سریع و **بدونِ ترافیکِ بیرونی** قرمز شود (نه یک DNS
    # ِ واقعی به میزبانِ ناشناس).
    try:
        probe._url_json_get("http://127.0.0.1:9/botX/getMe", 0.01)
    except ValueError:
        pass
    else:
        raise AssertionError("_url_json_get فقط api.telegram.org را قبول می‌کند")


def t_p_a_token_on_the_truncation_boundary_is_still_scrubbed():
    """نشتیِ بی‌صدا از راهِ **ترتیب**: بریدنِ متن قبل از scrub.

    `last_error_message` تا ۲۰۰ کاراکتر نگه داشته می‌شود. اگر اول بریده شود،
    توکنی که روی مرز افتاده نصف می‌شود و دیگر با هیچ الگویی برابر نیست — پس
    scrub رد می‌شود، `secret_redactions` صفر می‌ماند، و تکهٔ راز چاپ می‌شود.
    گزارشی که می‌گوید «نشتی نبود» بدتر از گزارشی است که هشدار می‌دهد."""
    half = FAKE_CENTER.split(":", 1)[1]
    long_err = "x" * 175 + FAKE_CENTER + " /hook failed"
    assert len(long_err) > 200 and long_err.index(FAKE_CENTER) < 200
    rep = probe.build_report(
        get_fn=_make_get(_canned(err_center=long_err), []),
        environ=dict(BOTH), health={"status": "ok"})
    c = _bot(rep, "TG_CENTER_BOT_TOKEN")
    blob = json.dumps(c, ensure_ascii=False) + probe.render(rep, environ=dict(BOTH))
    for n in range(len(half), 5, -1):
        assert half[:n] not in blob, f"{n} کاراکترِ اولِ نیمهٔ محرمانه نشت کرد"
    assert c["secret_redactions"] >= 1, "نشتیِ گرفته‌شده باید شمرده شود، نه بی‌صدا"

    # و دو الگوی دیگرِ `_live_tokens` که تا امروز شاهد نداشتند:
    # (۱) نیمهٔ محرمانه به‌تنهایی، بدونِ `<id>:` — همان چیزی که در یک لاگ می‌افتد
    solo, hits = probe.scrub_secrets(f"leaked >> {half} << leaked", dict(BOTH))
    assert half not in solo and hits == 1, solo
    # (۲) شکلِ URL-encoded — `:` می‌شود `%3A` و رشتهٔ خام دیگر برابر نیست
    enc = __import__("urllib.parse", fromlist=["quote"]).quote(FAKE_CENTER, safe="")
    assert enc != FAKE_CENTER, "فرضِ تست: encode باید واقعاً متن را عوض کند"
    got, hits2 = probe.scrub_secrets(f"?url={enc}", dict(BOTH))
    assert enc not in got and hits2 >= 1, got


def t_q_a_token_hidden_in_the_webhook_userinfo_is_scrubbed_at_source():
    """`https://user:<token>@host/hook` یک webhook ِ کاملاً مجاز است.

    ابزار عمداً `url` را برنمی‌گرداند و فقط netloc را می‌دهد — ولی netloc خودش
    userinfo دارد. یعنی راهی هست که توکن از درِ «host» واردِ **ساختارِ** گزارش
    شود بدونِ آن‌که هیچ شمارنده‌ای بالا برود؛ و آن‌وقت هر مصرف‌کنندهٔ بعدیِ dict
    (لاگ، کارتِ تلگرام، فایل) بی‌گناه پخشش می‌کند."""
    url = f"https://user:{FAKE_CENTER}@evil.example/hook"
    rep = probe.build_report(get_fn=_make_get(_canned(hook_center=url), []),
                             environ=dict(BOTH), health={"status": "ok"})
    c = _bot(rep, "TG_CENTER_BOT_TOKEN")
    assert FAKE_CENTER not in json.dumps(rep, ensure_ascii=False), \
        "توکن از راهِ netloc واردِ ساختارِ گزارش شد"
    assert FAKE_CENTER.split(":", 1)[1] not in json.dumps(rep, ensure_ascii=False)
    assert "evil.example" in c["webhook_host"], c["webhook_host"]
    assert c["secret_redactions"] >= 1, "باید در سرچشمه گرفته و شمرده شود"
    assert c["verdict"] == "webhook_hijack", c


def t_r_one_healthy_bot_does_not_mask_the_other_bots_unknown():
    """«نمی‌دانم» ِ یک بات نباید زیرِ سبزیِ باتِ دیگر گم شود.

    کدِ خروج تنها کانالِ ماشین‌خوانِ این ابزار است؛ ۰ یعنی «پرسیدم و پاک بود».
    یک باتِ توکن‌دار که جواب نداده، پرسیده‌شده و **جواب نگرفته** — پس ۲.
    ولی باتی که اصلاً توکن ندارد فرق دارد: مالک ممکن است عمداً یکی را ست کرده
    باشد، و آن حالت نباید ابزار را برای همیشه زرد کند."""
    rep = probe.build_report(              # مرکز سالم، اصلی بی‌جواب
        get_fn=_make_get({FAKE_CENTER: {"getMe": _me("octo_center"),
                                        "getWebhookInfo": _hook(0)}}, []),
        environ=dict(BOTH), health={"status": "ok"})
    assert _bot(rep, "TG_CENTER_BOT_TOKEN")["verdict"] == "ok", rep["bots"]
    assert _bot(rep, "TELEGRAM_BOT_TOKEN")["verdict"] == "unreachable", rep["bots"]
    assert probe.exit_code(rep) == 2, "نامعلومِ یک بات نباید پشتِ سبزِ دیگری قایم شود"

    # کنترلِ ضدِتزئین: فقط-یک-توکن باید سبز بماند
    rep2 = probe.build_report(
        get_fn=_make_get({FAKE_CENTER: {"getMe": _me("octo_center"),
                                        "getWebhookInfo": _hook(0)}}, []),
        environ={"TG_CENTER_BOT_TOKEN": FAKE_CENTER}, health={"status": "ok"})
    assert _bot(rep2, "TELEGRAM_BOT_TOKEN")["verdict"] == "no_token", rep2["bots"]
    assert probe.exit_code(rep2) == 0, "نبودِ توکن ≠ پروبِ شکست‌خورده"


def t_s_a_competing_webhook_and_a_recorded_error_have_their_own_verdicts():
    """دو حکمی که تا امروز شاهد نداشتند.

    `webhook_hijack` قلبِ نیمهٔ دومِ سوال است: اگر webhook ست باشد، `getUpdates`
    ِ ما **ساختاراً** هرگز چیزی نمی‌گیرد و صفِ خالی هیچ معنایی ندارد. و
    `tg_error` تنها جایی است که خطای ثبت‌شدهٔ خودِ تلگرام به کدِ خروج می‌رسد."""
    rep = probe.build_report(
        get_fn=_make_get(_canned(hook_center="https://other.example/hook"), []),
        environ=dict(BOTH), health={"status": "ok"})
    c = _bot(rep, "TG_CENTER_BOT_TOKEN")
    assert c["verdict"] == "webhook_hijack", c
    assert c["webhook_url_set"] is True and c["webhook_host"] == "other.example", c
    assert probe.exit_code(rep) == 1, "webhook ِ رقیب یعنی ما کر شده‌ایم"

    rep2 = probe.build_report(
        get_fn=_make_get(_canned(err_center="Wrong response from the webhook"), []),
        environ=dict(BOTH), health={"status": "ok"})
    c2 = _bot(rep2, "TG_CENTER_BOT_TOKEN")
    assert c2["verdict"] == "tg_error", c2
    assert probe.exit_code(rep2) == 1


def t_t_a_poller_that_is_running_but_failing_is_reported_failing():
    """`silent` (نمی‌دود) از `failing` (می‌دود و می‌افتد) جدا است — و هر دو راهِ
    رسیدن به `failing` شاهد می‌خواهند، وگرنه نصفِ این تفکیک تزئین است.

    راهِ ۱: دورها تازه‌اند ولی پیاپی شکست می‌خورند.
    راهِ ۲: شکستِ پیاپی هنوز به آستانه نرسیده، ولی از آخرین موفقیت آن‌قدر
            گذشته که دیگر «نوسان» نیست."""
    now = time.time()
    _write_health(last_ok_ts=now - 20, last_round_ts=now - 5,
                  consecutive_failures=3, last_reason="URLError")
    h = probe.local_poll_health(now=now)
    assert h["status"] == "failing", f"شکستِ پیاپی باید دیده شود: {h}"

    _write_health(last_ok_ts=now - 3600, last_round_ts=now - 5,
                  consecutive_failures=1, last_reason="timeout")
    h2 = probe.local_poll_health(now=now)
    assert h2["status"] == "failing", f"یک ساعت بی‌موفقیت = قرمز، نه سبز: {h2}"
    assert h2["last_round_age_s"] < probe.STALE_ROUND_S, "این حالت باید *غیرِ* silent باشد"

    # و کنترل: دورِ تازه + موفقیتِ تازه + صفر شکست = سبزِ مجاز
    _write_health(last_ok_ts=now - 5, last_round_ts=now - 2,
                  consecutive_failures=0, last_reason="")
    assert probe.local_poll_health(now=now)["status"] == "ok"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_receive_probe: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
