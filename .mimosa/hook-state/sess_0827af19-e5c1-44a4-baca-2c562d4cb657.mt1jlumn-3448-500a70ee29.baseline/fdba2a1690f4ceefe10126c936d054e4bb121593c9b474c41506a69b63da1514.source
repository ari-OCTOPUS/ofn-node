#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_every_limb_loads_its_credentials.py — هیچ پایی نباید بی‌اعتبارنامه بالا بیاید.

حادثهٔ ۲۰۲۶-۰۸-۰۴ (VQ-GATEWAY-NO-CREDS-001)
──────────────────────────────────────────
`miniapp_gateway.py` **تنها** پایی بود که `env_loader.load_env()` را صدا
نمی‌زد. چهار پای دیگر می‌زنند:

    organism.py:231 · center.py:5089 · cortex.py:579 · live/server.py:1039

gateway کاملاً به env ِ ارثی تکیه داشت، و واچداگش (`miniapp-watchdog.ps1`)
فقط `_ops/OCTOPUS.env` را می‌خواند که **هیچ‌کدام** از سه نامِ اعتبارنامه را
تعریف نمی‌کند. سنجشِ بولینی (بدونِ لمسِ هیچ مقداری): قبل از `load_env` هر سه
`False`، بعدش هر سه `True` — یعنی `.env` داشتشان و gateway نمی‌گرفتشان.

نتیجه: `validate_init_data` سرِ **اولین** گاردش (`if not bot_token`) `None`
می‌داد ⇒ gateway **صددرصدِ** درخواست‌ها را ۴۰۳ می‌کرد. مینی‌اپ ناامن نبود،
**مرده** بود.

⚠️ و چرا هیچ‌کس نفهمید — درسِ اصلی: از بیرون این دقیقاً شبیهِ «احراز درست کار
می‌کند» بود. ۰۸-۰۳ یک ۴۰۳ ِ زنده به‌عنوان شاهدِ سلامتِ احراز ثبت شد؛ آن ۴۰۳
واقعی بود ولی **دلیلش غلط** — ردِ درست، به دلیلِ اشتباه. یک پاسخِ منفی هرگز
بینِ «قانون کار کرد» و «قانون هرگز اجرا نشد» تفکیک نمی‌کند.

`flags-loaded-miniapp-gateway.json` هم گمراه‌کننده بود: ۳ فلگ در برابرِ ۱۵۵،
ولی آن snapshot فقط `OCTOPUS_*` را ثبت می‌کند، پس دربارهٔ `TG_CENTER_BOT_TOKEN`
اصلاً حرفی نمی‌زد. عکسِ ناقص بدتر از نبودِ عکس است.
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("limb-credentials")

OPS = harness.REAL_VAULT / "_ops"

#: هر پایی که یک پروسهٔ بلندمدت است و ممکن است به secret نیاز داشته باشد.
LIMBS = {
    "organism": OPS / "organism.py",
    "center": OPS / "telegram_center" / "center.py",
    "cortex": OPS / "cortex" / "cortex.py",
    "live": OPS / "live" / "server.py",
    "gateway": OPS / "telegram_center" / "miniapp_gateway.py",
}


def _calls_load_env(path: Path) -> bool:
    """با AST نه زیررشته: یک کامنت که دربارهٔ `env_loader` حرف می‌زند، صدازدنش
    نیست. همان تفکیکی که یک‌بار در همین جلسه یک گارد را بی‌اعتبار کرد."""
    tree = ast.parse(path.read_text("utf-8", errors="replace"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr == "load_env":
                return True
    return False


def _imports_env_loader(path: Path) -> bool:
    tree = ast.parse(path.read_text("utf-8", errors="replace"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            if any(a.name == "env_loader" for a in n.names):
                return True
        if isinstance(n, ast.ImportFrom) and n.module == "env_loader":
            return True
    return False


def t_a_every_limb_file_exists():
    """گاردِ «اسکنر خراب است» — مسیرِ عوض‌شده نباید سبزِ کاذب بدهد."""
    missing = [k for k, p in LIMBS.items() if not p.exists()]
    assert not missing, ("مسیرِ این پاها پیدا نشد — گارد کور شده", missing)


def t_b_every_limb_calls_load_env():
    """قلبِ گارد. `gateway` تا ۰۸-۰۴ تنها استثنا بود."""
    missing = sorted(k for k, p in LIMBS.items() if not _calls_load_env(p))
    assert not missing, (
        "این پاها `env_loader.load_env()` را صدا نمی‌زنند ⇒ بدونِ اعتبارنامه "
        "بالا می‌آیند. اگر مسیرِ احراز داشته باشند، **هر** درخواست را رد "
        "می‌کنند و از بیرون شبیهِ «احراز سالم» به‌نظر می‌رسد", missing)


def t_c_every_limb_imports_it_too():
    """قرینه: `load_env` بدونِ import یعنی `NameError` که در `except` بلعیده
    می‌شود و دوباره سکوت — همان الگوی «مسلح ولی بی‌اثر»."""
    missing = sorted(k for k, p in LIMBS.items() if not _imports_env_loader(p))
    assert not missing, missing


def t_d_the_gateway_loads_before_it_accepts_a_request():
    """ترتیب باربر است — ولی ترتیبِ **اجرا**، نه ترتیبِ خطِ سورس.

    ⚠️ نسخهٔ اولِ همین تست، `load_env` را با اولین خطی که توکن را می‌خواند
    مقایسه می‌کرد و قرمز شد: توکن در خطِ ۲۲۸ خوانده می‌شود و `load_env` در
    ۴۶۳. ولی خطِ ۲۲۸ داخلِ یک **تابعِ handler** است که فقط سرِ درخواست صدا
    زده می‌شود — یعنی بعد از `main()`. مقایسهٔ شمارهٔ خط بینِ دو تابعِ مختلف
    معنایی ندارد و آن قرمز مثبتِ کاذب بود.

    ناوردیِ درست: داخلِ **خودِ `main()`** — جایی که ترتیبِ سورس همان ترتیبِ
    اجراست — `load_env()` باید پیش از `serve_forever()` بیاید. بارگذاری بعد
    از شروعِ پذیرش یعنی اولین درخواست‌ها هنوز بی‌اعتبارنامه‌اند."""
    tree = ast.parse(LIMBS["gateway"].read_text("utf-8", errors="replace"))
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    assert fn is not None, "تابعِ main در gateway پیدا نشد — گارد کور شده"
    load_line = serve_line = None
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr == "load_env":
                load_line = n.lineno if load_line is None else min(load_line, n.lineno)
            if n.func.attr == "serve_forever":
                serve_line = n.lineno if serve_line is None else min(serve_line, n.lineno)
    assert load_line, "`main()` ِ gateway ‏`load_env()` را صدا نمی‌زند"
    assert serve_line, "`serve_forever` در main پیدا نشد — این گارد را به‌روز کن"
    assert load_line < serve_line, (
        f"load_env در خطِ {load_line} ولی پذیرشِ درخواست از خطِ {serve_line} "
        "شروع می‌شود — بارگذاری باید مقدم باشد")


def t_e_validate_init_data_still_fails_closed_without_a_token():
    """ناوردیِ ایمنی که این باگ را از «فاجعه» به «مرده» تنزل داد.
    اگر روزی fail-open شود، همین شکاف تونلِ عمومی را باز می‌کند.

    ⚠️ نسخهٔ اولِ این تست **بی‌دندان بود**. جهشِ «`not bot_token` را از گارد
    بردار» زنده ماند، چون همهٔ موردهایش هشِ آشغال داشتند: با حذفِ گارد، کد جلو
    می‌رفت، HMAC را با توکنِ خالی حساب می‌کرد، و **به‌هرحال** نامنطبق می‌شد و
    `None` می‌داد. تست سبز می‌ماند به دلیلِ غلط — دقیقاً همان «جهشِ سبز = خطِ
    نادیده».

    موردِ باربر پایین ساخته می‌شود: یک initData که **با توکنِ خالی درست امضا
    شده** و user id ِ درستی دارد. تنها چیزی که جلویش را می‌گیرد همان گاردِ
    `not bot_token` است. با گارد ⇒ None. بدونِ گارد ⇒ رد می‌شد."""
    import hashlib
    import hmac as _hmac
    import importlib.util
    import json as _json
    import time as _time
    from urllib.parse import urlencode

    spec = importlib.util.spec_from_file_location("mg_probe", LIMBS["gateway"])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    # موردهای ساده (هنوز مفیدند: مسیرهای دیگرِ رد را می‌پوشانند)
    assert m.validate_init_data("user=x&hash=y", bot_token="", owner_id=1) is None
    assert m.validate_init_data("user=x&hash=y", bot_token=None, owner_id=1) is None
    assert m.validate_init_data("", bot_token="t", owner_id=1) is None
    assert m.validate_init_data("user=x&hash=y", bot_token="t", owner_id=None) is None
    assert m.validate_init_data("user=x&hash=y", bot_token="t", owner_id="") is None

    # ── موردِ باربر: امضای معتبر **زیرِ توکنِ خالی** ───────────────────────
    owner = 987654321
    fields = {"auth_date": str(int(_time.time())),
              "user": _json.dumps({"id": owner}, separators=(",", ":"))}
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    for empty in ("", None):
        secret = _hmac.new(b"WebAppData", str(empty or "").encode("utf-8"),
                           hashlib.sha256).digest()
        sig = _hmac.new(secret, check.encode("utf-8"), hashlib.sha256).hexdigest()
        init = urlencode(dict(fields, hash=sig))
        assert m.validate_init_data(init, bot_token=empty, owner_id=owner) is None, (
            "fail-open! ‏initData ِ امضاشده با توکنِ خالی پذیرفته شد — گاردِ "
            "`not bot_token` برداشته شده و تونلِ عمومی باز است")

    # و همان امضا با توکنِ **واقعی** هم باید رد شود (کلید فرق دارد)
    secret = _hmac.new(b"WebAppData", b"", hashlib.sha256).digest()
    sig = _hmac.new(secret, check.encode("utf-8"), hashlib.sha256).hexdigest()
    init = urlencode(dict(fields, hash=sig))
    assert m.validate_init_data(init, bot_token="a-real-token", owner_id=owner) is None


def t_f_this_test_never_reads_a_secret_value():
    """این فایل فقط **نام** و AST را می‌بیند. §۱۰ منشور: هیچ مقداری در تست،
    لاگ یا چت نمی‌آید — و یک تستی که secret را چاپ کند، خودش نشتی است."""
    src = Path(__file__).read_text("utf-8")
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr in ("get", "getenv"):
                base = f.value
                if (isinstance(base, ast.Attribute) and base.attr == "environ") or \
                   (isinstance(base, ast.Name) and base.id == "os"):
                    raise AssertionError(
                        f"خطِ {n.lineno}: این تست نباید env را بخواند — "
                        "فقط AST و نام")


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_every_limb_loads_its_credentials: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
