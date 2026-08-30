#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_voice_keep_audio.py — صوت فقط با اجازهٔ صریح می‌ماند.

چرا این فلگ ساخته شد (۲۰۲۶-۰۸-۰۱): دو ویسِ فارسیِ مالک با دو مدلِ متفاوت متنِ
پرت دادند. مسیرِ صدا با آزمایشِ کنترل‌شده تبرئه شد — همان جملهٔ انگلیسی از WAV
و از OGG/Opus ِ ۴۸ کیلوهرتز (فرمتِ واقعیِ تلگرام)، با و بدونِ VAD، هر چهار بار
بی‌غلط خوانده شد. پس متغیرِ باقی‌مانده یا تواناییِ فارسیِ مدل است یا چیزی مختصِ
همان صدا، و جداکردنشان بدونِ خودِ فایل ممکن نیست؛ در حالی که capture صوت را
بلافاصله پاک می‌کند.

قاعده‌ای که این‌جا قفل می‌شود ساده و سخت است: **پیش‌فرض، صوت می‌رود.**
نگه‌داشتن فقط با فلگِ صریح، و شکستِ خودِ نگه‌داشتن نباید ویس را بشکند.
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-voice-keep-audio")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import capture  # noqa: E402

DEPS_OK = {
    "download_fn": lambda fid, dest: (Path(dest).write_bytes(b"OggS-fake"), True)[1],
    "transcribe_fn": lambda p, lang="fa", duration_s=None: {
        "ok": True, "text": "سلام حالت چطوره", "engine": "fake", "secs": 0.1},
    "transcribe_available": lambda: (True, "fake"),
}
META = {"file_id": "V-1", "message_id": 4242, "duration": 5}


def _on(name):
    os.environ[name] = "1"


def _off(*names):
    for n in names:
        os.environ.pop(n, None)


def _kept():
    d = capture._keep_dir()
    return sorted(p.name for p in d.glob("*.oga")) if d.exists() else []


def t_a_by_default_the_audio_is_gone():
    """هیچ فلگی = هیچ صوتی. این پیش‌فرض باید بی‌سروصدا درست بماند."""
    _on(capture.FLAG_VOICE)
    _off(capture.FLAG_KEEP_AUDIO)
    try:
        r = capture._voice_transcribe(META, DEPS_OK)
        assert r.get("ok"), r
        assert _kept() == [], f"صوت بدونِ اجازه ماند: {_kept()}"
    finally:
        _off(capture.FLAG_VOICE)


def t_b_with_the_flag_one_file_is_kept_for_diagnosis():
    _on(capture.FLAG_VOICE)
    _on(capture.FLAG_KEEP_AUDIO)
    try:
        r = capture._voice_transcribe(dict(META, message_id=4243), DEPS_OK)
        assert r.get("ok"), r
        assert _kept() == ["voice-4243.oga"], _kept()
        kept = capture._keep_dir() / "voice-4243.oga"
        assert kept.read_bytes() == b"OggS-fake", "فایلِ نگه‌داشته‌شده همان صوت نیست"
    finally:
        _off(capture.FLAG_VOICE, capture.FLAG_KEEP_AUDIO)
        for p in capture._keep_dir().glob("*.oga"):
            p.unlink()


def t_c_the_audio_never_lands_in_the_note_tree():
    """صوت کنارِ state می‌ماند، نه در درختِ نوت‌ها.

    نسخهٔ اولِ این تست ادعای غلطی می‌کرد — «بیرونِ والت» — در حالی که
    `_ops/state` ذاتاً زیرِ همان ریشه است، در تست و در تولید. ناوردایِ
    واقعی این است: صوت نباید در پوشه‌ای بنشیند که ابسیدین ایندکس می‌کند و
    بکاپِ نوت‌ها برمی‌دارد (`10 - Telegram processing/Raw` و خویشاوندانش)."""
    d = capture._keep_dir().resolve()
    parts = [p.lower() for p in d.parts]
    assert "state" in parts and "_ops" in parts, f"صوت کنارِ state نیست: {d}"
    notes = (Path(ENV["ORG_ROOT"]).resolve()
             .joinpath(*capture.RAW_SUBDIR))
    assert notes not in d.parents and d != notes, f"صوت در درختِ نوت‌هاست: {d}"


def t_d_a_failed_keep_never_breaks_the_voice():
    """اگر نگه‌داشتن شکست بخورد، ویس باید همچنان متن شود."""
    _on(capture.FLAG_VOICE)
    _on(capture.FLAG_KEEP_AUDIO)
    orig = capture._keep_dir
    capture._keep_dir = lambda: (_ for _ in ()).throw(RuntimeError("no disk"))
    try:
        r = capture._voice_transcribe(dict(META, message_id=4244), DEPS_OK)
        assert r.get("ok") and "سلام" in str(r.get("text")), r
    finally:
        capture._keep_dir = orig
        _off(capture.FLAG_VOICE, capture.FLAG_KEEP_AUDIO)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_voice_keep_audio: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
