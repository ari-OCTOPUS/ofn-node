#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mail_credentials — حلِ credential ِ SMTP (Lane G، رأی ۱۷).

اثبات می‌کند:
  · تقدم: `OCTOPUS_SMTP_*` ِ صریح همیشه بر fallback ِ Gmail مقدم است.
  · fallback ِ Gmail فقط با فلگِ `OCTOPUS_SMTP_USE_GMAIL` مسلح می‌شود؛ بدونِ آن
    NOT_ARMED ِ صادق با دلیلی که **نامِ فلگ** را می‌گوید (نه «creds missing» ِ گمراه‌کننده).
  · ستِ ناقصِ صریح هرگز بی‌صدا به Gmail سقوط نمی‌کند — بلند شکست می‌خورد و
    نامِ کلیدهای غایب را می‌گوید.
  · **قاعدهٔ هرگز-پسورد-برنگردان**: هیچ خروجیِ این ماژول (resolve/status/repr)
    مقدارِ پسورد را حمل نمی‌کند — فقط **نامِ** متغیر.
  · `env_loader` واقعاً کلیدهای GMAIL_* را از یک فایلِ `.env` به os.environ می‌ریزد.

⚠️ تعیّن: این تست `_ensure_env_loaded` را no-op می‌کند تا صرفِ‌نظر از اینکه از
   کدام درخت اجرا شود (worktree یا درختِ زنده که `.env` ِ واقعی دارد) نتیجه‌اش
   یکی باشد — و تا هیچ کلیدِ **واقعی**ای وارد این تست نشود.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import harness

ENV = harness.setup("mail-credentials")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mail_credentials as mc   # noqa: E402

# رشته‌های نگهبان — اگر هرکدام در خروجی ظاهر شد یعنی نشتِ secret.
PW_OCTOPUS = "PW-SENTINEL-OCTOPUS-9f3a"
PW_GMAIL = "PW-SENTINEL-GMAIL-7b21"
OWNER = "owner.person@gmail.com"

_ALL_KEYS = mc.EXPLICIT_ENV + (mc.GMAIL_ADDR_ENV, mc.GMAIL_SECRET_ENV,
                               mc.GMAIL_FALLBACK_FLAG)

# تعیّن: هیچ `.env` ِ واقعی‌ای نباید وسطِ این تست کلید تزریق کند.
mc._ensure_env_loaded = lambda: None

_EXPLICIT = {"OCTOPUS_SMTP_HOST": "smtp.example.com", "OCTOPUS_SMTP_PORT": "587",
             "OCTOPUS_SMTP_USER": "relay-user",
             "OCTOPUS_SMTP_PASS": PW_OCTOPUS,
             "OCTOPUS_SMTP_FROM": "quotes@example.com"}

_GMAIL = {mc.GMAIL_ADDR_ENV: OWNER, mc.GMAIL_SECRET_ENV: PW_GMAIL}


def _scrub():
    for k in _ALL_KEYS:
        os.environ.pop(k, None)


def _set(d):
    os.environ.update({k: str(v) for k, v in d.items()})


def _leaks(obj) -> bool:
    """آیا هیچ‌کدام از پسوردهای نگهبان در نمایشِ متنیِ این شیء هست؟"""
    text = json.dumps(obj, ensure_ascii=False, default=str) + repr(obj)
    return PW_OCTOPUS in text or PW_GMAIL in text


def t_a_nothing_set_is_honest_not_armed():
    _scrub()
    cr = mc.resolve()
    assert cr["ok"] is False, cr
    assert cr["reason"] == "smtp-creds-missing", cr
    assert cr["how"] == "none" and cr["secret_env"] == "", cr
    # شکلِ ثابت حتی در شکست — صداکننده KeyError نمی‌گیرد
    for k in ("host", "port", "user", "from_addr"):
        assert k in cr, k


def t_b_explicit_five_arms_and_returns_only_the_secret_name():
    _scrub()
    _set(_EXPLICIT)
    cr = mc.resolve()
    assert cr["ok"] is True and cr["how"] == "octopus-smtp-env", cr
    assert cr["host"] == "smtp.example.com" and cr["port"] == 587, cr
    assert cr["user"] == "relay-user" and cr["from_addr"] == "quotes@example.com", cr
    assert cr["secret_env"] == "OCTOPUS_SMTP_PASS", cr
    assert not _leaks(cr), "پسورد در خروجیِ resolve نشسته!"
    assert PW_OCTOPUS not in list(cr.values()), cr
    # ولی نام درست است و خواندنش با آن نام کار می‌کند
    assert os.environ[cr["secret_env"]] == PW_OCTOPUS
    assert mc.secret_present(cr) is True


def t_c_explicit_beats_gmail_even_when_gmail_is_armed():
    _scrub()
    _set(_EXPLICIT)
    _set(_GMAIL)
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    cr = mc.resolve()
    assert cr["how"] == "octopus-smtp-env", f"تقدم شکست: {cr}"
    assert cr["from_addr"] == "quotes@example.com", cr
    assert cr["secret_env"] == "OCTOPUS_SMTP_PASS", cr


def t_d_partial_explicit_never_silently_falls_back_to_gmail():
    """ستِ ناقص = خطای اپراتور. سقوطِ بی‌صدا به Gmail یعنی هویتِ فرستنده
    بی‌خبر عوض شود — ممنوع. باید بلند و با نامِ کلیدهای غایب شکست بخورد."""
    _scrub()
    _set(_GMAIL)
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"     # Gmail کاملاً آماده و مسلح
    os.environ["OCTOPUS_SMTP_HOST"] = "smtp.example.com"   # ولی صریح ناقص
    cr = mc.resolve()
    assert cr["ok"] is False, f"ستِ ناقص نباید مسلح شود: {cr}"
    assert cr["how"] == "none", cr
    assert cr["reason"].startswith("octopus-smtp-incomplete:"), cr
    for miss in ("OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
                 "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_FROM"):
        assert miss in cr["reason"], (miss, cr["reason"])
    assert "OCTOPUS_SMTP_HOST" not in cr["reason"], "کلیدِ موجود نباید غایب اعلام شود"


def t_e_gmail_fallback_arms_with_the_flag():
    _scrub()
    _set(_GMAIL)
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    cr = mc.resolve()
    assert cr["ok"] is True and cr["how"] == "gmail-app-password", cr
    assert cr["host"] == "smtp.gmail.com", cr
    assert cr["port"] == 465, "Gmail باید TLS ِ implicit (۴۶۵) باشد"
    assert cr["user"] == OWNER and cr["from_addr"] == OWNER, cr
    assert cr["secret_env"] == mc.GMAIL_SECRET_ENV, cr
    assert not _leaks(cr), "پسوردِ Gmail در خروجی نشسته!"
    assert mc.owner_address() == OWNER
    assert mc.secret_present(cr) is True


def t_f_gmail_creds_without_the_flag_name_the_flag():
    """credential هست ولی رأیِ مالک نیست — دلیل باید **نامِ فلگ** را بگوید،
    نه «creds missing» ِ گمراه‌کننده (وگرنه اپراتور دنبالِ secret می‌گردد)."""
    _scrub()
    _set(_GMAIL)
    cr = mc.resolve()
    assert cr["ok"] is False, cr
    assert cr["reason"] == "gmail-fallback-not-enabled:" + mc.GMAIL_FALLBACK_FLAG, cr
    assert mc.gmail_fallback_enabled() is False
    assert mc.owner_address() == "", "بدونِ arming آدرسِ مالک هم نباید بیرون بیاید"


def t_g_flag_on_but_creds_missing_names_the_missing_keys():
    _scrub()
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    cr = mc.resolve()
    assert cr["ok"] is False and cr["reason"].startswith("gmail-creds-missing:"), cr
    assert mc.GMAIL_ADDR_ENV in cr["reason"] and mc.GMAIL_SECRET_ENV in cr["reason"], cr
    # فقط آدرس هست، پسورد نه → همچنان ناقص و صادق
    _scrub()
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    os.environ[mc.GMAIL_ADDR_ENV] = OWNER
    cr2 = mc.resolve()
    assert cr2["ok"] is False and mc.GMAIL_SECRET_ENV in cr2["reason"], cr2
    assert mc.GMAIL_ADDR_ENV not in cr2["reason"], cr2


def t_h_bad_port_is_refused_not_guessed():
    _scrub()
    _set(_EXPLICIT)
    for bad in ("not-a-number", "0", "70000", "-1"):
        os.environ["OCTOPUS_SMTP_PORT"] = bad
        cr = mc.resolve()
        assert cr["ok"] is False, (bad, cr)
        assert cr["reason"] == "octopus-smtp-bad-port:OCTOPUS_SMTP_PORT", (bad, cr)


def t_i_the_secret_value_never_appears_in_any_public_output():
    """قاعدهٔ مرکزی: هیچ سطحِ عمومیِ این ماژول مقدارِ پسورد را حمل نمی‌کند."""
    for setup in ("explicit", "gmail"):
        _scrub()
        if setup == "explicit":
            _set(_EXPLICIT)
        else:
            _set(_GMAIL)
            os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
        for out in (mc.resolve(), mc.status()):
            assert not _leaks(out), (setup, "نشتِ پسورد در", out)
        # و مقدارِ برگشتیِ owner_address هم آدرس است نه secret
        assert not _leaks(mc.owner_address())


def t_j_status_masks_the_owner_address_and_reports_only_booleans():
    _scrub()
    _set(_GMAIL)
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    st = mc.status()
    assert st["ok"] is True and st["how"] == "gmail-app-password", st
    assert st["from_masked"] == "ow***@gmail.com", st
    assert OWNER not in json.dumps(st, ensure_ascii=False), "آدرسِ کاملِ مالک در گزارش!"
    assert st["secret_env"] == mc.GMAIL_SECRET_ENV and st["secret_present"] is True, st
    assert st["gmail_fallback_flag"] == mc.GMAIL_FALLBACK_FLAG, st
    assert st["gmail_fallback_enabled"] is True, st
    assert mc.mask_address("") == "***"
    assert mc.mask_address("a@b.com") == "a***@b.com"


def t_k_secret_present_is_false_when_the_named_var_is_empty():
    """اگر متغیرِ نام‌برده خالی باشد، `secret_present` باید دروغ نگوید."""
    _scrub()
    _set(_GMAIL)
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    cr = mc.resolve()
    assert mc.secret_present(cr) is True
    os.environ[mc.GMAIL_SECRET_ENV] = ""
    assert mc.secret_present(cr) is False, "متغیرِ خالی نباید present شمرده شود"


def t_l_env_loader_really_carries_the_gmail_keys_from_a_dotenv_file():
    """پلِ واقعی: `env_loader` (همان لودری که organism در بوت صدا می‌زند) باید
    کلیدهای GMAIL_* را از یک فایلِ `.env` به os.environ برساند — وگرنه fallback
    در تولید هرگز کلید نمی‌بیند. فایلِ موقت، نه `.env` ِ زنده."""
    import env_loader
    _scrub()
    tmp = Path(tempfile.mkdtemp(prefix="mailcred-env-")) / ".env"
    tmp.write_text(f"# comment\n{mc.GMAIL_ADDR_ENV}={OWNER}\n"
                   f'{mc.GMAIL_SECRET_ENV}="{PW_GMAIL}"\n', "utf-8")
    env_loader.load_env(path=str(tmp))
    assert os.environ.get(mc.GMAIL_ADDR_ENV) == OWNER, "آدرس از .env نیامد"
    assert os.environ.get(mc.GMAIL_SECRET_ENV) == PW_GMAIL, "پسورد از .env نیامد"
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    cr = mc.resolve()
    assert cr["ok"] is True and cr["how"] == "gmail-app-password", cr
    assert not _leaks(cr)
    _scrub()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mail_credentials: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
