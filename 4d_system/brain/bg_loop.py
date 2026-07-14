"""
brain/bg_loop.py — اجرای گام‌های لوپ پژوهش در threadِ پس‌زمینه (B8 — فلگ: LOOP_BG_THREAD=1)

چرا این ماژول وجود دارد؟
  امروز هر گامِ لوپ (شاملِ یک تماسِ LLM تا ۳۰۰ ثانیه) داخلِ مسیرِ renderِ
  Streamlit اجرا می‌شود؛ یعنی تا پایانِ تماس، threadِ render قفل است و UI
  پاسخ نمی‌دهد. این ماژول همان گام‌ها را در یک threadِ daemonِ جدا اجرا
  می‌کند و نتیجه‌ها را از راهِ queue.Queue به threadِ render می‌رساند تا
  render فقط poll کند و آزاد بماند.

  فقط وقتی استفاده می‌شود که متغیرِ محیطیِ LOOP_BG_THREAD=1 تنظیم شده باشد؛
  پیش‌فرض (فلگ خاموش) همان مسیرِ همزمانِ قدیمی است و این ماژول اصلاً
  import نمی‌شود.

قراردادِ ایمنی با Streamlit (مهم):
  - این فایل عمداً هیچ importی از streamlit ندارد.
  - threadِ پس‌زمینه هرگز به st.session_state یا هیچ APIِ Streamlit دست
    نمی‌زند؛ فقط step_fnِ تزریق‌شده را صدا می‌زند و خروجی را در صف می‌گذارد.
  - همهٔ دسترسی به session_state در threadِ render و هنگامِ poll() است.
  - استثناها هرگز خاموش گم نمی‌شوند: به‌صورتِ آیتمِ ویژه واردِ صف و در
    پراپرتیِ error ثبت می‌شوند؛ سپس thread می‌ایستد.
"""
from __future__ import annotations

import logging
import queue
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class _ErrorItem:
    """آیتمِ ویژهٔ صف برای خطا — تا خطا هم‌ترتیب با نتیجه‌ها به render برسد."""

    def __init__(self, iteration: int, exc: BaseException):
        self.iteration = iteration
        self.exc = exc


class BackgroundLoopRunner:
    """اجرای stepهای لوپ در threadِ daemon + تحویلِ نتیجه‌ها با صفِ FIFO.

    step_fn: تابعِ یک‌گام — ``step_fn(iteration) -> result``. در تولید،
    closure روی ``AutoLoopEngine.run_step`` است (history داخلِ خودِ engine
    می‌ماند)؛ در تست، هر تابعِ ساختگی. این کلاس به هیچ‌چیزِ دیگرِ پروژه
    وابسته نیست تا بدونِ عوارضِ جانبی تست‌پذیر باشد.

    max_iterations: سقفِ تعدادِ گام‌ها؛ None یعنی بی‌سقف (فقط stop می‌ایستاند).
    """

    def __init__(self, step_fn: Callable[[int], object],
                 max_iterations: Optional[int] = None):
        self._step_fn = step_fn
        self._max_iterations = max_iterations
        self._queue: "queue.Queue[object]" = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._error: Optional[BaseException] = None
        self._next_iteration = 0

    # ── چرخهٔ حیات ─────────────────────────────────────────────────────
    def start(self) -> None:
        """شروعِ threadِ پس‌زمینه (اگر همین حالا زنده است: no-op)."""
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="bg-loop", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> bool:
        """توقفِ همیارانه: پرچمِ توقف set می‌شود؛ گامِ در حالِ اجرا قطع نمی‌شود.

        join با timeout — اگر thread وسطِ تماسِ طولانیِ LLM باشد ممکن است
        هنوز زنده بماند؛ چون daemon است با پایانِ فرایند جمع می‌شود و چون
        پرچم set شده، گامِ بعدی را شروع نمی‌کند.

        خروجی: آیا thread واقعاً تمام شد؟
        """
        self._stop_event.set()
        t = self._thread
        if t is not None and t.is_alive():
            t.join(timeout=timeout)
        return not self.is_running

    @property
    def is_running(self) -> bool:
        """آیا threadِ پس‌زمینه هنوز زنده است؟"""
        return self._thread is not None and self._thread.is_alive()

    @property
    def error(self) -> Optional[BaseException]:
        """آخرین استثنای گرفته‌شده در thread (None یعنی بدونِ خطا)."""
        return self._error

    # ── تحویلِ نتیجه‌ها به threadِ render ──────────────────────────────
    def poll(self, max_items: int = 10) -> list:
        """تخلیهٔ غیرمسدود‌کنندهٔ نتیجه‌های آماده (به همان ترتیبِ تولید).

        آیتم‌های خطا واردِ خروجی نمی‌شوند؛ فقط پراپرتیِ ``error`` را پر
        می‌کنند. این متد فقط از threadِ render صدا زده شود (طبقِ قراردادِ
        بالای فایل، تنها همان‌جا به session_state دست می‌زنیم).
        """
        out: list = []
        for _ in range(max(0, int(max_items))):
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if isinstance(item, _ErrorItem):
                self._error = item.exc
                continue
            out.append(item)
        return out

    # ── بدنهٔ thread — هیچ APIِ Streamlit اینجا مجاز نیست ──────────────
    def _run(self) -> None:
        while not self._stop_event.is_set():
            if (self._max_iterations is not None
                    and self._next_iteration >= self._max_iterations):
                break
            i = self._next_iteration
            try:
                result = self._step_fn(i)
            except BaseException as e:  # noqa: BLE001 — خطا نباید خاموش بمیرد
                self._error = e
                self._queue.put(_ErrorItem(i, e))
                logger.error("bg-loop step %d failed: %s: %s",
                             i, type(e).__name__, e)
                break
            self._next_iteration = i + 1
            self._queue.put(result)
