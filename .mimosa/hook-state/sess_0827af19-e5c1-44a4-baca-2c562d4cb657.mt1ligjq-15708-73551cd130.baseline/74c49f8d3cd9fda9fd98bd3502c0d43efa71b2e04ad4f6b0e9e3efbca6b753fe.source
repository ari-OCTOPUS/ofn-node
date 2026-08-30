#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_transcribe — نردبانِ متن‌سازیِ ویس (منشور رأی ۹).

    probeِ در-لحظه · ترتیبِ نردبان · سقفِ طول · هر شاخهٔ شکستِ صادق ·
    **ناوردایِ ضدِ جعل**: هیچ مسیرِ شکستی متن برنمی‌گرداند.

صفر نصب، صفر شبکه، صفر دانلودِ مدل: `_find_spec` و `_RUNNERS` (seamِ صریحِ
خودِ ماژول) جعل می‌شوند، پس همان کدِ تولیدی سنجیده می‌شود نه یک نسخهٔ موازی.
"""
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-transcribe")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import transcribe  # noqa: E402


class _Spec:
    """کمینه‌ترین چیزی که `find_spec` می‌تواند برگرداند (non-None = importable)."""


def _fake_spec(present):
    """`_find_spec` ِ جعلی: فقط ماژول‌های نام‌بردهٔ `present` را موجود می‌داند."""
    names = set(present)

    def _fs(name, package=None):
        return _Spec() if name in names else None
    return _fs


class _Seam:
    """context managerِ کوچک: probe + runnerها را جعل می‌کند و برمی‌گرداند."""

    def __init__(self, present=(), runners=None):
        self.present = present
        self.runners = runners

    def __enter__(self):
        self._old_fs = transcribe._find_spec
        self._old_run = dict(transcribe._RUNNERS)
        transcribe._find_spec = _fake_spec(self.present)
        if self.runners is not None:
            transcribe._RUNNERS.clear()
            transcribe._RUNNERS.update(self.runners)
        return self

    def __exit__(self, *exc):
        transcribe._find_spec = self._old_fs
        transcribe._RUNNERS.clear()
        transcribe._RUNNERS.update(self._old_run)
        return False


def _audio(name="v.oga", data=b"OggS-fake-bytes"):
    p = Path(ENV["ORG_ROOT"]) / "_audio"
    p.mkdir(parents=True, exist_ok=True)
    f = p / name
    f.write_bytes(data)
    return str(f)


# ── probe: در لحظهٔ فراخوانی، بدونِ importِ سنگین ────────────────────────────
def t_a_available_reports_the_truth_and_keeps_ladder_order():
    with _Seam(present=()):
        assert transcribe.available() == (False, "no-backend")
    with _Seam(present=("whisper",)):
        assert transcribe.available() == (True, "openai-whisper")
    with _Seam(present=("faster_whisper",)):
        assert transcribe.available() == (True, "faster-whisper")
    with _Seam(present=("faster_whisper", "whisper")):
        # هر دو موجود ⇒ پلهٔ اول برنده (سریع‌تر، int8، CPU-پسند)
        assert transcribe.available() == (True, "faster-whisper")


def t_b_import_is_pure_no_backend_or_model_loaded():
    """importِ این ماژول نباید کتابخانهٔ سنگین را بالا بیاورد (import-time خالص)."""
    assert "faster_whisper" not in sys.modules
    assert "whisper" not in sys.modules
    with _Seam(present=("faster_whisper",)):
        transcribe.available()
    assert "faster_whisper" not in sys.modules, "probe نباید ماژول را import کند"


def t_c_models_land_in_ops_state_never_in_the_default_hf_cache():
    """مدل‌ها زیرِ `_ops/state/models/whisper` — نه `~/.cache/huggingface`، نه vault.

    بدونِ `download_root` هر دو کتابخانه چند گیگ در کشِ پروفایل می‌ریزند؛ این
    تست هر دو حالت را قفل می‌کند: با `OCTOPUS_STATE_DIR` (تست/ایزوله) و
    بدونش (تولید ⇒ کنارِ خودِ `_ops`)."""
    md = str(transcribe.models_dir()).replace("\\", "/").lower()
    assert md.startswith(str(ENV["ops"]).replace("\\", "/").lower()), md
    assert md.endswith("state/models"), md
    keep = os.environ.pop("OCTOPUS_STATE_DIR", None)
    try:
        fallback = str(transcribe.models_dir()).replace("\\", "/").lower()
    finally:
        if keep is not None:
            os.environ["OCTOPUS_STATE_DIR"] = keep
    assert fallback.endswith("_ops/state/models"), fallback
    for cache in (".cache/huggingface", ".cache/whisper", "appdata/roaming"):
        assert cache not in fallback, f"مدل در کشِ پیش‌فرض می‌افتد: {fallback}"


# ── شاخه‌های شکستِ صادق ──────────────────────────────────────────────────────
def t_d_no_backend_carries_the_exact_install_command():
    with _Seam(present=()):
        r = transcribe.transcribe(_audio())
    assert r["ok"] is False and r["reason"] == "no-backend", r
    assert r["text"] == "", "شکست هرگز متن ندارد"
    assert r["hint"] == transcribe.INSTALL_HINT, r
    assert "faster-whisper" in r["hint"], r["hint"]


def t_e_missing_file_is_reported_not_guessed():
    r = transcribe.transcribe(str(Path(ENV["ORG_ROOT"]) / "_audio" / "nope.oga"))
    assert r["ok"] is False and r["reason"] == "file-missing", r
    assert r["text"] == ""
    r2 = transcribe.transcribe("")
    assert r2["ok"] is False and r2["reason"] == "file-missing", r2


def t_f_audio_longer_than_the_cap_is_refused_before_any_engine_runs():
    """سقفِ OCTOPUS_WHISPER_MAX_S: بلندتر ⇒ رد، و موتور اصلاً صدا نمی‌خورد."""
    calls = []
    os.environ["OCTOPUS_WHISPER_MAX_S"] = "60"
    try:
        with _Seam(present=("faster_whisper",),
                   runners={"faster-whisper": lambda p, l: calls.append(p) or "x"}):
            r = transcribe.transcribe(_audio(), duration_s=61)
            ok = transcribe.transcribe(_audio(), duration_s=59)
    finally:
        os.environ.pop("OCTOPUS_WHISPER_MAX_S", None)
    assert r["ok"] is False and r["reason"] == "too-long", r
    assert r["limit_s"] == 60 and r["duration_s"] == 61.0, r
    assert r["text"] == ""
    assert len(calls) == 1, f"موتور برای ویسِ بلند هم دوید: {calls}"
    assert ok["ok"] is True, ok       # درست زیرِ سقف ⇒ می‌دود


def t_g_backend_error_never_leaks_the_library_message():
    """پیامِ استثنای کتابخانه می‌تواند مسیرِ کامل داشته باشد ⇒ فقط نوعِ خطا."""
    secret_ish = "C:/Users/Armin/model.bin FAILED"

    def boom(path, lang):
        raise RuntimeError(secret_ish)

    with _Seam(present=("faster_whisper",), runners={"faster-whisper": boom}):
        r = transcribe.transcribe(_audio())
    assert r["ok"] is False and r["reason"] == "backend-error", r
    assert r["error"] == "RuntimeError", r
    assert secret_ish not in str(r), "پیامِ خامِ کتابخانه نشت کرد"
    assert r["text"] == ""


def t_h_empty_result_is_never_sold_as_success():
    """گاردِ ضدِ جعل ۱: موتور دوید ولی چیزی نشنید ⇒ ok=False، نه «متنِ خالیِ موفق».

    جهش (`if not text:` → `if False:`) این تست را قرمز می‌کند."""
    for blank in ("", "   ", "\n\t "):
        with _Seam(present=("faster_whisper",),
                   runners={"faster-whisper": lambda p, l, b=blank: b}):
            r = transcribe.transcribe(_audio())
        assert r["ok"] is False, (blank, r)
        assert r["reason"] == "empty-transcript", r
        assert r["text"] == "", r


def t_h2_missing_model_is_its_own_reason_not_a_generic_error():
    """«مدل کش نشده» ≠ «موتور خراب» — و دانلودِ inline پیش‌فرض **خاموش** است.

    بدونِ این تفکیک، اولین ویسِ مالک روی مدلِ نبوده یعنی ~۵۰۰MB دانلودِ وسطِ
    هندلر و چند دقیقه سکوت. حالا شکستِ فوریِ صادق با دستورِ رفع."""
    def not_cached(path, lang):
        raise FileNotFoundError("model not in cache")

    os.environ.pop("OCTOPUS_WHISPER_ALLOW_DOWNLOAD", None)
    with _Seam(present=("faster_whisper",), runners={"faster-whisper": not_cached}):
        r = transcribe.transcribe(_audio())
        # با مجوزِ صریحِ مالک، همان خطا دیگر «مدلِ غایب» نیست بلکه خطای واقعی
        os.environ["OCTOPUS_WHISPER_ALLOW_DOWNLOAD"] = "1"
        try:
            r2 = transcribe.transcribe(_audio())
        finally:
            os.environ.pop("OCTOPUS_WHISPER_ALLOW_DOWNLOAD", None)
    assert r["ok"] is False and r["reason"] == "model-missing", r
    assert r["hint"] == transcribe.DOWNLOAD_HINT and r["model"] == "small", r
    assert r["text"] == ""
    assert transcribe.allow_download() is False, "دانلود باید پیش‌فرض خاموش باشد"
    assert r2["reason"] == "backend-error", r2


def t_i_no_failure_path_ever_returns_text():
    """ناوردایِ ماژول: هیچ شاخهٔ شکستی متن ندارد — حتی اگر extra بخواهد."""
    forced = transcribe._fail("x", text="متنِ جعلی", engine="e")
    assert forced["text"] == "", forced
    assert forced["ok"] is False


# ── مسیرِ موفق ──────────────────────────────────────────────────────────────
def t_j_happy_path_returns_cleaned_text_with_engine_and_secs():
    with _Seam(present=("faster_whisper",),
               runners={"faster-whisper":
                        lambda p, l: "  سلام   \n به آرمین بگو  "}):
        r = transcribe.transcribe(_audio(), lang="fa", duration_s=12)
    assert r["ok"] is True, r
    assert r["text"] == "سلام به آرمین بگو", r          # فاصله‌ها نرمال شد
    assert r["engine"] == "faster-whisper", r
    assert isinstance(r["secs"], float) and r["secs"] >= 0.0, r
    assert set(r) >= {"ok", "text", "engine", "secs", "reason"}, r


def t_k_language_and_path_reach_the_runner_unchanged():
    seen = []
    path = _audio("lang.oga")
    with _Seam(present=("whisper",),
               runners={"openai-whisper":
                        lambda p, l: seen.append((p, l)) or "متن"}):
        r = transcribe.transcribe(path, lang="fa")
    assert r["engine"] == "openai-whisper", r
    assert seen == [(path, "fa")], seen


def t_k2_auto_language_means_let_the_engine_decide():
    """`auto`/خالی ⇒ None به موتور (تشخیصِ خودکار)؛ زبانِ صریح دست‌نخورده.

    پروبِ زندهٔ ۰۸-۰۱: ویسِ انگلیسیِ مالک با قفلِ سختِ `fa` مچاله می‌شد."""
    assert transcribe._lang_arg("auto") is None
    assert transcribe._lang_arg("") is None
    assert transcribe._lang_arg(None) is None
    assert transcribe._lang_arg("  fa ") == "fa"
    assert transcribe._lang_arg("en") == "en"
    os.environ.pop("OCTOPUS_WHISPER_LANG", None)
    assert transcribe.default_lang() == "fa", "پیش‌فرضِ مالک فارسی است"
    os.environ["OCTOPUS_WHISPER_LANG"] = "auto"
    try:
        assert transcribe.default_lang() == "auto"
    finally:
        os.environ.pop("OCTOPUS_WHISPER_LANG", None)


def t_l_selected_engine_without_a_runner_fails_loudly():
    """probe بگوید هست ولی runner نباشد ⇒ no-runner، نه سکوت و نه متن."""
    with _Seam(present=("faster_whisper",), runners={}):
        r = transcribe.transcribe(_audio())
    assert r["ok"] is False and r["reason"] == "no-runner", r
    assert r["text"] == ""


def t_m_env_knobs_have_honest_defaults():
    os.environ.pop("OCTOPUS_WHISPER_MODEL", None)
    os.environ.pop("OCTOPUS_WHISPER_MAX_S", None)
    assert transcribe.model_name() == "small"
    assert transcribe.max_seconds() == 300
    os.environ["OCTOPUS_WHISPER_MODEL"] = "medium"
    os.environ["OCTOPUS_WHISPER_MAX_S"] = "0"      # نامعتبر ⇒ پیش‌فرض
    try:
        assert transcribe.model_name() == "medium"
        assert transcribe.max_seconds() == 300
    finally:
        os.environ.pop("OCTOPUS_WHISPER_MODEL", None)
        os.environ.pop("OCTOPUS_WHISPER_MAX_S", None)


def t_n_real_environment_state_is_reported_truthfully():
    """بدونِ جعلِ seam: امروز هیچ موتوری نصب نیست ⇒ باید همین را بگوید.

    اگر روزی مالک faster-whisper را نصب کند، این تست همچنان درست می‌ماند —
    فقط شاخهٔ دیگرش را می‌سنجد. هدف: ادعای ماژول با واقعیتِ ماشین یکی باشد."""
    import importlib.util as _u
    really = [e for e, m in transcribe._LADDER if _u.find_spec(m) is not None]
    ok, eng = transcribe.available()
    assert ok is bool(really), (ok, really)
    if not really:
        assert eng == "no-backend", eng
        r = transcribe.transcribe(_audio())
        assert r["ok"] is False and r["reason"] == "no-backend" and r["text"] == ""
    else:
        # موتور نصب است ⇒ نام باید همان پلهٔ واقعیِ نردبان باشد، نه ادعا.
        assert eng == really[0], (eng, really)
        assert transcribe._RUNNERS.get(eng) is not None, eng


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_transcribe: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
