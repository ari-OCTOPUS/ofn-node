"""«اختاپوس داده ذخیره می‌کند؟» — بله، و از امشب سطحش هم دارد.

۲۰۲۶-۰۸-۰۵. ممیزیِ خودآگاهی/خودترمیمی نشان داد `memory.db` واقعاً می‌نویسد
(۲۸ ردیفِ واقعی) ولی `MemoryStore.metrics()` — از قبل ساخته و تست‌شده —
هیچ صداکنندهٔ تولیدی نداشت. این تست‌ها قرارداد را قفل می‌کنند: `/api/selfmap`
حالا `out["memory"]` را از همان `metrics()` می‌سازد، و غیابِ پایگاه به
UNKNOWN می‌رود نه صفرِ جعلی.
"""
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve()
_OPS = _HERE.parent.parent
for _d in (str(_OPS), str(_OPS / "telegram_center")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import miniapp_state  # noqa: E402
import memory.memory_store as memory_store  # noqa: E402


class SelfmapMemorySurface(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="selfmap-mem-"))
        self.addCleanup(self._rmtree)
        self.db = self.tmp / "memory.db"

    def _rmtree(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_real_rows_surface_as_real_counts(self):
        store = memory_store.MemoryStore(path=self.db)
        for i in range(3):
            store.insert({
                "memory_id": f"mem_test_{i}", "namespace": "episodic",
                "mkey": f"k{i}", "content": "x", "trust": "GRADED",
                "confidence": 0.9, "salience": 0.5,
                "valid_from": "2026-08-01T00:00:00Z", "privacy": "internal",
            })
        store.close()

        import unittest.mock as mock
        with mock.patch.object(memory_store, "_default_path", return_value=self.db):
            out = miniapp_state.get_selfmap_state()

        self.assertIn("memory", out)
        self.assertEqual(out["memory"].get("total"), 3,
                         "سه ردیفِ واقعی باید در نمای selfmap دیده شود")
        self.assertEqual(out["memory"].get("active"), 3)
        self.assertEqual(out["memory"].get("by_namespace", {}).get("episodic"), 3)

    def test_missing_db_is_unknown_not_zero(self):
        """پایگاهِ نبود ≠ صفر رکورد. باید UNKNOWN بگوید."""
        import unittest.mock as mock

        def boom():
            raise RuntimeError("db unreachable")

        with mock.patch.object(memory_store, "MemoryStore", side_effect=boom):
            out = miniapp_state.get_selfmap_state()
        self.assertEqual(out["memory"].get("status"), "unknown",
                         "خطای دسترسی نباید به صفرِ جعلی تبدیل شود")

    def test_field_shape_matches_what_the_ui_reads(self):
        """قراردادِ خواننده و نویسنده: app.js دقیقاً همین کلیدها را می‌خواند."""
        store = memory_store.MemoryStore(path=self.db)
        store.insert({
            "memory_id": "mem_x", "namespace": "semantic", "mkey": "k",
            "content": "x", "trust": "GRADED", "confidence": 0.9, "salience": 0.5,
            "valid_from": "2026-08-01T00:00:00Z", "privacy": "internal",
        })
        store.close()
        import unittest.mock as mock
        with mock.patch.object(memory_store, "_default_path", return_value=self.db):
            out = miniapp_state.get_selfmap_state()
        m = out["memory"]
        for key in ("total", "active", "pending", "retracted", "by_namespace"):
            self.assertIn(key, m, f"app.js به کلیدِ {key} نیاز دارد")


if __name__ == "__main__":
    unittest.main(verbosity=2)
