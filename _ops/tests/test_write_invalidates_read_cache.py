"""نوشتنِ موفق باید کشِ خواندن را باطل کند.

باگِ زندهٔ ۲۰۲۶-۰۸-۰۵: `task.done` وضعِ APPLIED می‌داد، ردیف در پایگاه‌داده
واقعاً done می‌شد، ولی `renderTasks()` که **درجا** بعدش صدا زده می‌شود از کشِ
۳ثانیه‌ای می‌خواند و همان کارِ باز را برمی‌گرداند. یعنی مالک تُستِ سبز
می‌دید و ردیف سرِ جایش می‌ماند — همان «زدم و هیچ نشد».

این تست‌ها به **رفتار** لنگر می‌اندازند نه به متن: یک شمارندهٔ فراخوان روی
منبع می‌گذارند و می‌سنجند که خواندنِ بعد از نوشتن واقعاً به منبع رسید.
"""
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve()
_OPS = _HERE.parent.parent
for _d in (str(_OPS), str(_OPS / "telegram_center")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import miniapp_state  # noqa: E402


class CacheInvalidationContract(unittest.TestCase):
    """قراردادِ خودِ لایهٔ کش، مستقل از گیت‌وی."""

    def setUp(self):
        miniapp_state.cache_clear()
        self.addCleanup(miniapp_state.cache_clear)

    # جدولِ هندلرها **داخلِ** dispatch_api و از globals ساخته می‌شود، پس
    # رِبایندِ خودِ تابع روی ماژول گرفته می‌شود. نامِ تابع را از همان منبع
    # می‌خوانیم تا اگر روزی مسیر به تابعِ دیگری وصل شد، تست دروغ نگوید.
    def _handler_name(self, path):
        import ast
        src = (_OPS / "telegram_center" / "miniapp_state.py").read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Dict):
                continue
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == path
                        and isinstance(v, ast.Name)):
                    return v.id
        return None

    def _instrumented(self, path):
        """یک شمارنده جای تابعِ واقعیِ همان مسیر بگذار."""
        name = self._handler_name(path)
        self.assertIsNotNone(name, f"مسیرِ {path} در جدولِ dispatch_api نیست")
        original = getattr(miniapp_state, name)
        calls = {"n": 0}

        def counting(root=None):
            calls["n"] += 1
            return {"status": "ok", "n": calls["n"]}

        setattr(miniapp_state, name, counting)
        self.addCleanup(lambda: setattr(miniapp_state, name, original))
        return calls

    def test_second_read_is_served_from_cache(self):
        """پایه: بدونِ باطل‌سازی، خواندنِ دوم به منبع نمی‌رسد.

        بدونِ این مورد، تستِ بعدی بی‌معناست: اگر کش اصلاً کار نکند، «خواندنِ
        بعد از نوشتن تازه است» بی‌زحمت سبز می‌شود.
        """
        path = "/api/ops/tasks"
        calls = self._instrumented(path)
        miniapp_state.dispatch_api(path)
        miniapp_state.dispatch_api(path)
        self.assertEqual(calls["n"], 1, "کش کار نمی‌کند — پایهٔ این تست باطل است")

    def test_cache_clear_forces_a_fresh_read(self):
        path = "/api/ops/tasks"
        calls = self._instrumented(path)
        miniapp_state.dispatch_api(path)
        miniapp_state.cache_clear()
        miniapp_state.dispatch_api(path)
        self.assertEqual(calls["n"], 2, "بعد از cache_clear هنوز از کش سرو شد")

    def test_clear_reaches_every_cached_path_not_just_one(self):
        """باطل‌سازی سراسری است. اگر روزی به prefix محدود شد، این می‌شکند."""
        paths = [p for p in ("/api/ops/tasks", "/api/ops/leads")
                 if self._handler_name(p)]
        self.assertGreaterEqual(len(paths), 2, "برای این تست ≥۲ مسیرِ کش‌شونده لازم است")
        counters = {p: self._instrumented(p) for p in paths}
        for p in paths:
            miniapp_state.dispatch_api(p)
        miniapp_state.cache_clear()
        for p in paths:
            miniapp_state.dispatch_api(p)
        for p in paths:
            self.assertEqual(counters[p]["n"], 2, f"{p} بعد از باطل‌سازی هنوز کهنه بود")


class GatewayInvalidatesOnWrite(unittest.TestCase):
    """گره در خودِ گیت‌وی: کدام وضعیت‌ها کش را پاک می‌کنند.

    گرهِ AST — نه grep روی متن. جهشِ شرط (مثلاً حذفِ ERROR یا برعکس‌کردنِ
    شرط) باید این را قرمز کند، و کامنتِ بالای کد نباید سبزش نگه دارد.
    """

    def _statuses_that_clear(self):
        import ast
        src = (_OPS / "telegram_center" / "miniapp_gateway.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        found = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            # آیا بدنهٔ این if به cache_clear می‌رسد؟
            hits = [n for n in ast.walk(node)
                    if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "cache_clear"]
            if not hits:
                continue
            for lit in ast.walk(node.test):
                if isinstance(lit, ast.Constant) and isinstance(lit.value, str):
                    found.append(lit.value.upper())
        return set(found)

    def test_applied_and_error_clear_the_cache(self):
        got = self._statuses_that_clear()
        self.assertIn("APPLIED", got, "APPLIED کش را پاک نمی‌کند — باگِ اصلی برگشته")
        self.assertIn("ERROR", got, "ERROR کش را پاک نمی‌کند — کرشِ نیمه‌نوشته کهنه می‌ماند")

    def test_non_mutating_statuses_do_not_clear(self):
        got = self._statuses_that_clear()
        for s in ("BLOCKED", "DENIED", "DUPLICATE"):
            self.assertNotIn(s, got, f"{s} حالت را عوض نمی‌کند؛ نباید کش را بریزد")

    def test_the_clear_call_lives_in_the_actions_handler(self):
        """جای فراخوان مهم است: باید بعد از execute باشد، نه هرجایِ فایل."""
        import ast
        src = (_OPS / "telegram_center" / "miniapp_gateway.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        clears = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "cache_clear"]
        self.assertTrue(clears, "هیچ فراخوانِ cache_clear در گیت‌وی نیست")
        executes = [n.lineno for n in ast.walk(tree)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "execute"]
        self.assertTrue(executes, "فراخوانِ execute پیدا نشد — ساختار عوض شده")
        self.assertTrue(any(c.lineno > min(executes) for c in clears),
                        "cache_clear قبل از execute است — نتیجه‌ای برای باطل‌کردن نیست")


if __name__ == "__main__":
    unittest.main(verbosity=2)
