"""تستِ BackgroundLoopRunner (B8) — بدونِ streamlit، با step_fnِ ساختگی."""
from tests import _bootstrap  # noqa: F401

import ast
import inspect
import threading
import time
import unittest

from brain import bg_loop
from brain.bg_loop import BackgroundLoopRunner


def _wait_until(cond, timeout=5.0, interval=0.01):
    """انتظارِ فعال تا برقراریِ شرط — تستِ threading بدونِ sleepِ کور."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cond():
            return True
        time.sleep(interval)
    return cond()


class TestBackgroundLoopRunner(unittest.TestCase):
    def test_results_delivered_in_order(self):
        runner = BackgroundLoopRunner(lambda i: i * 10, max_iterations=5)
        runner.start()
        self.assertTrue(_wait_until(lambda: not runner.is_running))
        got = []
        while len(got) < 5:
            batch = runner.poll(max_items=2)       # تخلیهٔ چندمرحله‌ای
            if not batch:
                break
            got.extend(batch)
        self.assertEqual(got, [0, 10, 20, 30, 40])  # هم‌ترتیب با تولید
        self.assertIsNone(runner.error)
        self.assertEqual(runner.poll(), [])         # صفِ خالی → لیستِ خالی

    def test_error_captured_not_raised_and_stops(self):
        def step(i):
            if i == 2:
                raise ValueError("boom")
            return i

        runner = BackgroundLoopRunner(step, max_iterations=10)
        runner.start()
        self.assertTrue(_wait_until(lambda: not runner.is_running))
        results = runner.poll(max_items=20)         # نباید raise کند
        self.assertEqual(results, [0, 1])           # فقط گام‌های سالمِ قبل از خطا
        self.assertIsInstance(runner.error, ValueError)
        self.assertEqual(str(runner.error), "boom")
        self.assertFalse(runner.is_running)         # خطا → توقف، نه ادامهٔ کور

    def test_stop_terminates_promptly(self):
        release = threading.Event()
        started = threading.Event()

        def slow_step(i):
            started.set()
            release.wait(timeout=10)                # شبیه‌سازِ تماسِ کُندِ LLM
            return i

        runner = BackgroundLoopRunner(slow_step)    # بی‌سقف — فقط stop می‌ایستاندش
        runner.start()
        self.assertTrue(started.wait(timeout=5))
        self.assertTrue(runner.is_running)
        # stop وسطِ گامِ کُند: join با timeout برمی‌گردد و render را آویزان نمی‌کند
        t0 = time.monotonic()
        runner.stop(timeout=0.2)
        self.assertLess(time.monotonic() - t0, 2.0)
        # بعد از آزادشدنِ گامِ جاری، thread بی‌درنگ تمام می‌شود (گامِ بعدی شروع نمی‌شود)
        release.set()
        self.assertTrue(_wait_until(lambda: not runner.is_running))
        self.assertLessEqual(len(runner.poll(max_items=100)), 1)  # حداکثر نتیجهٔ گامِ جاری
        self.assertIsNone(runner.error)

    def test_no_streamlit_dependency(self):
        # قراردادِ ماژول: هیچ importی از streamlit — با AST، نه متنِ خام
        # (docstring مجاز است دربارهٔ streamlit توضیح بدهد).
        tree = ast.parse(inspect.getsource(bg_loop))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name.split(".")[0], "streamlit")
            elif isinstance(node, ast.ImportFrom):
                self.assertNotEqual((node.module or "").split(".")[0], "streamlit")


if __name__ == "__main__":
    unittest.main()
