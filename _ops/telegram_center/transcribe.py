#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""transcribe — نردبانِ متن‌سازیِ ویس (منشور رأی ۹: «ویس → نوتِ ساختاریافته»).

این ماژول **هیچ‌وقت متن نمی‌سازد؛ فقط متن را از یک موتورِ واقعی می‌گیرد.**
اگر موتوری نبود، صادقانه `{"ok": False, "reason": "no-backend"}` برمی‌گرداند و
دستورِ دقیقِ نصب را همراهش می‌فرستد. جعلِ transcript ممنوعِ مطلق است — نوتِ
غایب از نوتِ دروغ بی‌نهایت بهتر است.

نردبان (هر پله اختیاری، **در لحظهٔ فراخوانی** probe می‌شود، نه در import):
  ۱. faster-whisper  — CPU/int8، مدل از ``OCTOPUS_WHISPER_MODEL`` (پیش‌فرض small)
  ۲. openai-whisper  — همان مدل، اگر پلهٔ اول نبود
  ۳. هیچ‌کدام        — {"ok": False, "reason": "no-backend", "hint": …}

مرزها:
  · import-time خالص: نه شبکه، نه دانلودِ مدل، نه importِ سنگین. `available()`
    فقط `find_spec` می‌زند (مدل را load نمی‌کند).
  · مدل‌ها زیرِ `_ops/state/models/whisper` می‌نشینند (نه پروفایلِ کاربر) تا
    درختِ vault و AppData ِ مالک تمیز بماند.
  · سقفِ طولِ صدا: ``OCTOPUS_WHISPER_MAX_S`` (پیش‌فرض ۳۰۰ ثانیه). بلندتر ⇒
    `reason: "too-long"` — نه متنِ نیمه، نه سکوت.
  · فایلِ صوت را پاک نمی‌کند؛ مالکِ فایل صداکننده است (capture در temp).

seamِ تست (بدونِ نصبِ هیچ‌چیز): `_find_spec` و `_RUNNERS` ماژول‌سطح‌اند و در
تست جایگزین می‌شوند — پس مسیرِ واقعی سنجیده می‌شود، نه یک fixture ِ موازی.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import threading
import time
from pathlib import Path

ENV_MODEL = "OCTOPUS_WHISPER_MODEL"
ENV_MAX_S = "OCTOPUS_WHISPER_MAX_S"
ENV_LANG = "OCTOPUS_WHISPER_LANG"
ENV_ALLOW_DOWNLOAD = "OCTOPUS_WHISPER_ALLOW_DOWNLOAD"
DEFAULT_MODEL = "small"
DEFAULT_MAX_S = 300

# دستورِ دقیقِ نصب — همراهِ هر پاسخِ no-backend می‌رود تا «چرا کار نمی‌کند»
# هیچ‌وقت یک معمّا نباشد. نصب = رأیِ مالک؛ این ماژول هرگز چیزی نصب نمی‌کند.
INSTALL_HINT = "pip install faster-whisper"

# مدلِ غایب: دانلود **پیش‌فرض خاموش** است (رأیِ ضمنیِ منشور UX-7 «سکوت ممنوع»).
# ⚠️ چرا: اولین ویس روی مدلِ نبوده یعنی ~۵۰۰MB دانلودِ inline وسطِ هندلرِ پیام —
# حلقهٔ poll دقایقی می‌خوابد و مالک فقط «سکوت» می‌بیند. با این گارد، به‌جای
# خوابِ چنددقیقه‌ای یک شکستِ فوریِ صادق (`model-missing`) می‌گیرد.
DOWNLOAD_HINT = (f"{ENV_ALLOW_DOWNLOAD}=1 (یک‌بار، ~۵۰۰MB) یا مدل را از قبل "
                 "در models_dir بگذار")

# نامِ استثناهایی که یعنی «مدل در کش نیست» (نه خرابیِ موتور) — تفکیک لازم است
# چون درمانِ این دو فرق دارد: یکی دانلود می‌خواهد، دیگری عیب‌یابی.
_MISSING_MODEL_ERRORS = ("LocalEntryNotFoundError", "EntryNotFoundError",
                         "RepositoryNotFoundError", "FileNotFoundError",
                         "OfflineModeIsEnabled", "HFValidationError",
                         "OSError")

# ترتیبِ نردبان: (نامِ موتور، نامِ ماژولی که باید importable باشد)
_LADDER: tuple[tuple[str, str], ...] = (
    ("faster-whisper", "faster_whisper"),
    ("openai-whisper", "whisper"),
)

_find_spec = importlib.util.find_spec       # seamِ تست (بالا را ببین)


def _env_int(name: str, default: int) -> int:
    try:
        v = int(str(os.environ.get(name, default)).strip())
    except (TypeError, ValueError):
        return default
    return v if v > 0 else default


def max_seconds() -> int:
    """سقفِ طولِ صدا برایِ متن‌سازی (ثانیه)."""
    return _env_int(ENV_MAX_S, DEFAULT_MAX_S)


def model_name() -> str:
    return (os.environ.get(ENV_MODEL, "") or "").strip() or DEFAULT_MODEL


def allow_download() -> bool:
    return os.environ.get(ENV_ALLOW_DOWNLOAD, "0") == "1"


def default_lang() -> str:
    """زبانِ پیش‌فرضِ متن‌سازی. `auto` = تشخیصِ خودکارِ خودِ موتور."""
    return (os.environ.get(ENV_LANG, "") or "").strip() or "fa"


def _lang_arg(lang) -> "str | None":
    """`auto`/خالی ⇒ None تا موتور خودش زبان را تشخیص دهد.

    ⚠️ چرا لازم شد: پروبِ زندهٔ ۰۸-۰۱ نشان داد مالک ویسِ انگلیسی هم می‌فرستد
    (نامِ بیزنس‌ها/اصطلاحات). قفلِ سختِ `fa` یعنی متنِ مچاله برای همان ویس‌ها."""
    v = str(lang if lang is not None else "").strip().lower()
    return None if v in ("", "auto", "none") else str(lang).strip()


def models_dir() -> Path:
    """جایِ مدل: `_ops/state/models`.

    ⚠️ بدونِ `download_root`، هر دو کتابخانه مدل را در پروفایلِ کاربر
    (`~/.cache/huggingface`) می‌ریزند — چند گیگابایت جایی که هیچ‌کس دنبالش
    نمی‌گردد و هیچ backup ای شاملش نیست. `OCTOPUS_STATE_DIR` اول است تا
    harness ِ تست هم ایزوله بماند.

    مسیر عمداً همان `state/models` است (نه زیرشاخهٔ whisper): مدلِ
    `faster-whisper-small` همین امشب روی درختِ زنده دقیقاً همان‌جا کش شده —
    یک قرارداد بیشتر یعنی ۵۰۰MB دانلودِ دوباره برای هیچ."""
    env = (os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    base = Path(env) if env else (Path(__file__).resolve().parent.parent / "state")
    return base / "models"


def _importable(mod: str) -> bool:
    try:
        return _find_spec(mod) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def available() -> "tuple[bool, str]":
    """(هست؟، نامِ موتور یا دلیل). صفر شبکه، صفر loadِ مدل — فقط probe."""
    for engine, mod in _LADDER:
        if _importable(mod):
            return True, engine
    return False, "no-backend"


# ── کشِ مدل: بارکردن یک‌بار، نه به‌ازای هر ویس ────────────────────────────────
# اندازه‌گیریِ ۲۰۲۶-۰۸-۰۱ روی همین ماشین:
#     small   بارِ اول  ۸.۷s   بارِ دوم  ۱.۳s
#     medium  بارِ اول ۲۶.۹s   بارِ دوم ۱۸.۱s
# یعنی از ۲۲.۶ ثانیه‌ای که ویسِ ۵ ثانیه‌ایِ مالک برد، بخشِ عمده **بارکردنِ
# وزن‌هایی** بود که بلافاصله دور ریخته می‌شدند. با medium این سربار ۱۸ تا ۲۷
# ثانیه به‌ازای هر ویس است — یعنی انتخابِ خودِ مالک را بدتر از مدلِ قبلی
# می‌کرد.
#
# پس مدل کش می‌شود، **ولی برای همیشه نگه داشته نمی‌شود**: medium در int8 بیش
# از یک گیگابایت رم می‌گیرد و این پروسه تا ابد بالاست. بعد از بی‌کاری آزاد
# می‌شود — سریع وقتی واقعاً استفاده می‌کند، بی‌مالیاتِ دائمی وقتی نمی‌کند.
MODEL_IDLE_RELEASE_S = 600.0     # ۱۰ دقیقه بی‌ویس ⇒ رم را پس بده

_MODEL_CACHE = {"key": None, "model": None, "last_used": 0.0}
_MODEL_LOCK = threading.Lock()
_EVICTOR = None


def _start_evictor() -> None:
    """نخِ آزادکننده (تنبل، daemon). بدونِ آن، رم فقط با تماسِ بعدی آزاد
    می‌شد — یعنی دقیقاً وقتی که دیگر نمی‌خواهیم آزاد شود."""
    global _EVICTOR
    if _EVICTOR is not None and _EVICTOR.is_alive():
        return

    def _loop():
        while True:
            time.sleep(30.0)
            with _MODEL_LOCK:
                if _MODEL_CACHE["model"] is None:
                    continue
                idle = time.time() - float(_MODEL_CACHE["last_used"] or 0.0)
                if idle >= MODEL_IDLE_RELEASE_S:
                    _MODEL_CACHE.update(key=None, model=None, last_used=0.0)

    _EVICTOR = threading.Thread(target=_loop, name="whisper-model-evictor",
                                daemon=True)
    _EVICTOR.start()


def _cached_model(fw, name: str, md, local_only: bool):
    """مدلِ آماده — از کش اگر همان مدل است، وگرنه تازه ساخته و کش می‌شود.

    تعویضِ نامِ مدل (env) کشِ قبلی را دور می‌ریزد؛ دو مدل هم‌زمان در رم
    نگه داشته نمی‌شوند."""
    key = (str(name), bool(local_only))
    with _MODEL_LOCK:
        if _MODEL_CACHE["key"] == key and _MODEL_CACHE["model"] is not None:
            _MODEL_CACHE["last_used"] = time.time()
            return _MODEL_CACHE["model"]
        _MODEL_CACHE.update(key=None, model=None)      # مدلِ قبلی آزاد شود
    model = fw.WhisperModel(name, device="cpu", compute_type="int8",
                            download_root=str(md), local_files_only=local_only)
    with _MODEL_LOCK:
        _MODEL_CACHE.update(key=key, model=model, last_used=time.time())
    _start_evictor()
    return model


# ── موتورها (هر کدام: (path, lang) → متنِ خام؛ استثنا مجاز است) ──────────────
def _run_faster_whisper(path: str, lang: str) -> str:
    fw = importlib.import_module("faster_whisper")
    md = models_dir()
    md.mkdir(parents=True, exist_ok=True)
    model = _cached_model(fw, model_name(), md, not allow_download())
    segments, _info = model.transcribe(str(path), language=_lang_arg(lang),
                                       vad_filter=True)
    return " ".join(str(getattr(s, "text", "") or "").strip() for s in segments)


def _run_openai_whisper(path: str, lang: str) -> str:
    wh = importlib.import_module("whisper")
    md = models_dir()
    md.mkdir(parents=True, exist_ok=True)
    # openai-whisper پارامترِ local_files_only ندارد؛ پس خودمان جلوی دانلودِ
    # ناخواسته را می‌گیریم (وگرنه همان خوابِ چنددقیقه‌ایِ وسطِ هندلر).
    if not allow_download() and not (md / f"{model_name()}.pt").exists():
        raise FileNotFoundError("whisper model not cached")
    model = wh.load_model(model_name(), device="cpu", download_root=str(md))
    res = model.transcribe(str(path), language=_lang_arg(lang), fp16=False)
    return str((res or {}).get("text") or "")


_RUNNERS = {"faster-whisper": _run_faster_whisper,
            "openai-whisper": _run_openai_whisper}


def _clean(text: str) -> str:
    return " ".join(str(text or "").split()).strip()


def _fail(reason: str, *, engine: str = "", secs: float = 0.0, **extra) -> dict:
    """هر شکست: **متنِ خالی**، دلیلِ صریح. ناوردایِ ماژول — شکست متن ندارد."""
    out = {"ok": False, "text": "", "engine": engine,
           "secs": round(float(secs), 2), "reason": str(reason)}
    out.update(extra)
    out["text"] = ""            # حتی اگر extra بخواهد متن بگذارد: خیر.
    return out


def transcribe(path, lang: str = "fa", *, duration_s=None) -> dict:
    """صوت → {ok, text, engine, secs, reason}. هرگز متنِ ساختگی.

    `duration_s` = طولِ صوت که خودِ تلگرام در پیامِ ویس می‌دهد (ما فایل را
    decode نمی‌کنیم). نبودش یعنی سقف قابلِ سنجش نیست — آن‌وقت موتور خودش
    محدود می‌شود، نه یک حدسِ ما.
    """
    p = Path(str(path or ""))
    if not str(path or "").strip() or not p.exists():
        return _fail("file-missing")

    limit = max_seconds()
    try:
        dur = float(duration_s) if duration_s is not None else None
    except (TypeError, ValueError):
        dur = None
    if dur is not None and dur > limit:
        # صادقانه رد می‌شود: نیمه‌ترجمهٔ بی‌اعلام = همان دروغِ کوچک.
        return _fail("too-long", duration_s=dur, limit_s=limit)

    ok, engine = available()
    if not ok:
        return _fail("no-backend", hint=INSTALL_HINT)

    runner = _RUNNERS.get(engine)
    if runner is None:
        return _fail("no-runner", engine=engine)

    t0 = time.time()
    try:
        raw = runner(str(p), str(lang or "fa"))
    except Exception as e:  # noqa: BLE001 — شکستِ موتور = دلیلِ صادق، نه crash
        # فقط نوعِ استثنا؛ پیامِ کتابخانه می‌تواند مسیر/توکن داشته باشد.
        name = type(e).__name__
        if not allow_download() and name in _MISSING_MODEL_ERRORS:
            # «مدل نیست» ≠ «موتور خراب است» — درمانشان فرق دارد، پس پیامشان هم.
            return _fail("model-missing", engine=engine,
                         secs=time.time() - t0, error=name,
                         hint=DOWNLOAD_HINT, model=model_name())
        return _fail("backend-error", engine=engine, secs=time.time() - t0,
                     error=name)
    secs = time.time() - t0

    text = _clean(raw)
    if not text:
        # موتور دوید ولی چیزی نشنید. سکوت را «متنِ خالیِ موفق» جا نمی‌زنیم —
        # صداکننده باید بتواند فرقِ «حرفی نبود» و «متن داریم» را ببیند.
        return _fail("empty-transcript", engine=engine, secs=secs)
    return {"ok": True, "text": text, "engine": engine,
            "secs": round(secs, 2), "reason": ""}


def install_hint() -> str:
    """دستورِ نصب برایِ ack/گزارش — نصب هرگز خودکار نیست (رأیِ مالک)."""
    return INSTALL_HINT


if __name__ == "__main__":   # pragma: no cover — پروبِ دستیِ اپراتور
    _ok, _eng = available()
    print(f"backend={_eng} available={_ok} model={model_name()} "
          f"max_s={max_seconds()} allow_download={allow_download()} "
          f"models_dir={models_dir()}")
    if not _ok:
        print(f"نصب: {INSTALL_HINT}")
