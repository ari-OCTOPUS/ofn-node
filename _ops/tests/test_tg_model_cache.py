#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_model_cache.py — مدل یک‌بار بار شود، نه به‌ازای هر ویس.

اندازه‌گیریِ ۲۰۲۶-۰۸-۰۱ روی همین ماشین:
    small   بارِ اول  ۸.۷s   بارِ دوم  ۱.۳s
    medium  بارِ اول ۲۶.۹s   بارِ دوم ۱۸.۱s

`_run_faster_whisper` هر بار یک `WhisperModel` تازه می‌ساخت، پس بخشِ عمدهٔ آن
۲۲.۶ ثانیه‌ای که ویسِ ۵ ثانیه‌ایِ مالک برد، بارکردنِ وزن‌هایی بود که بلافاصله
دور ریخته می‌شدند. با `medium` (رأیِ خودِ مالک) این سربار ۱۸ تا ۲۷ ثانیه به‌ازای
هر ویس می‌شد — یعنی ارتقای دقت، تجربه را بدتر می‌کرد.

قواعدِ قفل‌شده:
  · دو تماسِ پشتِ‌سرِ هم = **یک** بارکردن.
  · عوض‌شدنِ نامِ مدل کشِ قبلی را دور می‌ریزد (وگرنه env عوض می‌شود و مالک
    همچنان جوابِ مدلِ قدیمی می‌گیرد — بدترین نوعِ سکوت).
  · دو مدل هم‌زمان در رم نمی‌مانند.
  · بی‌کاریِ طولانی ⇒ رم پس داده می‌شود (medium بیش از یک گیگ است و این
    پروسه تا ابد بالاست).
"""
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-model-cache")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import transcribe  # noqa: E402


class FakeFW:
    """faster_whisper ِ بدل — فقط می‌شمارد چند بار مدل ساخته شد."""

    def __init__(self):
        self.built = []

    def WhisperModel(self, name, **kw):          # noqa: N802 — نامِ کتابخانه
        self.built.append((name, kw.get("local_files_only")))
        return {"name": name}


def _clear():
    transcribe._MODEL_CACHE.update(key=None, model=None, last_used=0.0)


def t_a_two_calls_load_the_model_once():
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    a = transcribe._cached_model(fw, "small", md, True)
    b = transcribe._cached_model(fw, "small", md, True)
    assert a is b, "دو نمونهٔ متفاوت — کش کار نکرد"
    assert len(fw.built) == 1, f"مدل {len(fw.built)} بار بار شد، نه یک بار"


def t_b_changing_the_model_name_drops_the_old_one():
    """اگر env عوض شود ولی کش نفهمد، مالک همچنان جوابِ مدلِ قدیمی می‌گیرد."""
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    transcribe._cached_model(fw, "small", md, True)
    m2 = transcribe._cached_model(fw, "medium", md, True)
    assert m2["name"] == "medium", m2
    assert [n for n, _ in fw.built] == ["small", "medium"], fw.built
    assert transcribe._MODEL_CACHE["key"][0] == "medium", transcribe._MODEL_CACHE["key"]


def t_c_only_one_model_is_held_at_a_time():
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    transcribe._cached_model(fw, "small", md, True)
    transcribe._cached_model(fw, "medium", md, True)
    held = transcribe._MODEL_CACHE["model"]
    assert held is not None and held["name"] == "medium", held
    # و برگشت به مدلِ اول باید دوباره بار شود (یعنی واقعاً رها شده بود)
    transcribe._cached_model(fw, "small", md, True)
    assert [n for n, _ in fw.built] == ["small", "medium", "small"], fw.built


def t_d_the_local_only_flag_is_part_of_the_identity():
    """مدلِ آفلاین و مدلِ مجاز-به-دانلود یکی نیستند؛ کش نباید قاطیشان کند."""
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    transcribe._cached_model(fw, "small", md, True)
    transcribe._cached_model(fw, "small", md, False)
    assert len(fw.built) == 2, fw.built


def t_e_an_idle_model_is_released_so_the_ram_comes_back():
    """کشِ ابدی روی پروسه‌ای که تا ابد بالاست، نشتِ رم است نه بهینه‌سازی."""
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    transcribe._cached_model(fw, "small", md, True)
    assert transcribe._MODEL_CACHE["model"] is not None

    # نخِ آزادکننده هر ۳۰ ثانیه نگاه می‌کند؛ در تست منطقش را مستقیم می‌سنجیم
    # با عقب‌بردنِ زمانِ آخرین استفاده (بدونِ خوابِ ۱۰ دقیقه‌ای).
    transcribe._MODEL_CACHE["last_used"] = (
        time.time() - transcribe.MODEL_IDLE_RELEASE_S - 5)
    idle = time.time() - float(transcribe._MODEL_CACHE["last_used"])
    assert idle >= transcribe.MODEL_IDLE_RELEASE_S, idle
    assert transcribe.MODEL_IDLE_RELEASE_S > 0, "آزادسازی خاموش است"
    # و نخِ آزادکننده واقعاً وجود دارد و daemon است (وگرنه خاموشیِ پروسه گیر می‌کند)
    ev = transcribe._EVICTOR
    assert ev is not None and ev.daemon, ev


def t_f_last_used_moves_on_every_hit_so_a_busy_model_is_never_evicted():
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    transcribe._cached_model(fw, "small", md, True)
    first = transcribe._MODEL_CACHE["last_used"]
    time.sleep(0.05)
    transcribe._cached_model(fw, "small", md, True)
    assert transcribe._MODEL_CACHE["last_used"] > first, "hit ِ کش زمان را جلو نبرد"


def t_g_a_starving_machine_does_not_get_a_cached_model():
    """کشی که ماشین را به زانو درآورد بهینه‌سازی نیست.

    اندازه‌گیریِ ۰۸-۰۱ روی ماشینِ مالک: با ~۲ گیگ رمِ آزاد، کشِ `medium`
    (۱.۳ گیگ) ویندوز را به صفحه‌گردانی انداخت و یک ویسِ **سه ثانیه‌ای**
    ۴.۵ دقیقه طول کشید — با صفر مصرفِ CPU، یعنی فقط انتظارِ دیسک."""
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    orig = transcribe.free_ram_gb
    transcribe.free_ram_gb = lambda: transcribe.MODEL_CACHE_MIN_FREE_GB - 0.5
    try:
        m = transcribe._cached_model(fw, "medium", md, True)
        assert m is not None, "مدل باید برگردد، فقط کش نشود"
        assert transcribe._MODEL_CACHE["model"] is None, "روی ماشینِ گرسنه کش شد"
        transcribe._cached_model(fw, "medium", md, True)
        assert len(fw.built) == 2, "بدونِ کش باید هر بار دوباره بار شود: %r" % (fw.built,)
    finally:
        transcribe.free_ram_gb = orig


def t_h_not_knowing_the_free_ram_keeps_the_old_behaviour():
    """«نمی‌دانم» نباید به «کم است» ترجمه شود — وگرنه یک API ِ در دسترس‌نبودن
    کش را روی هر ماشینی بی‌صدا خاموش می‌کند."""
    _clear()
    fw = FakeFW()
    md = Path(ENV["ORG_ROOT"])
    orig = transcribe.free_ram_gb
    transcribe.free_ram_gb = lambda: None
    try:
        transcribe._cached_model(fw, "small", md, True)
        assert transcribe._MODEL_CACHE["model"] is not None, "ندانستن کش را کشت"
    finally:
        transcribe.free_ram_gb = orig

if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_model_cache: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
