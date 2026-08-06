"""تستِ index_vault: چانک‌ها باید در batchهای زیرِ سقفِ Chroma فرستاده شوند.

پسِ‌زمینه: بازسازیِ 4D-Vault (۲۰۲۶-۰۸-۰۶) روی vault ِ واقعی (۹۳۵۵ چانک) با
`chromadb.errors.InternalError: Batch size of 9295 is greater than max batch
size of 5461` شکست خورد -- `index_vault()` همه‌ی چانک‌ها را در یک فراخوانیِ
`add_documents` می‌فرستاد. این تست همان مرزِ batch را با یک سقفِ ساختگیِ کوچک
شبیه‌سازی می‌کند تا بدونِ vault ِ واقعی و بدونِ مدلِ embedding واقعی سریع بماند.
"""
from tests import _bootstrap  # noqa: F401

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import memory.vectorstore as vs_mod


class _FakeClient:
    def __init__(self, cap):
        self._cap = cap

    def get_max_batch_size(self):
        return self._cap


class _FakeVectorStore:
    """جایگزینِ langchain_chroma.Chroma -- فقط add_documents را ضبط می‌کند."""

    def __init__(self, cap):
        self._client = _FakeClient(cap)
        self.calls = []
        self.deleted = []

    def add_documents(self, docs, ids=None):
        assert ids is not None and len(ids) == len(docs)
        self.calls.append((list(docs), list(ids)))

    def delete(self, where=None):
        self.deleted.append(where)

    def delete_collection(self):
        pass


def _write_vault(root: Path, n_files: int = 6, paras_per_file: int = 4) -> None:
    """چند فایل md با چند پاراگرافِ بلند -- برای تولیدِ چانکِ کافی بدونِ کنترلِ دقیقِ عدد."""
    for i in range(n_files):
        body = "\n\n".join(
            f"## بخشِ {i}-{j}\n\n" + ("متنِ آزمایشی برای اندازه. " * 60)
            for j in range(paras_per_file)
        )
        (root / f"note-{i}.md").write_text(f"# نُتِ {i}\n\n{body}", encoding="utf-8")


class TestIndexVaultBatching(unittest.TestCase):
    def test_add_documents_is_split_below_the_cap(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            _write_vault(vault)

            fake_vs = _FakeVectorStore(cap=3)   # سقفِ خیلی کوچک -> چند batch تضمینی
            with mock.patch.object(vs_mod, "VAULT_DIR", vault), \
                 mock.patch.object(vs_mod, "get_vectorstore", lambda: fake_vs), \
                 mock.patch.object(vs_mod, "_vectorstore", None), \
                 mock.patch.object(vs_mod, "_indexed", False):
                n = vs_mod.index_vault(force=False)

            self.assertGreater(n, 3, "vault آزمایشی باید بیش از سقفِ ساختگی چانک بسازد")
            self.assertGreater(len(fake_vs.calls), 1,
                                "با سقفِ ۳، یک فراخوانیِ تک برای >۳ چانک یعنی batching اعمال نشده")
            total = 0
            for docs, ids in fake_vs.calls:
                self.assertLessEqual(len(docs), 3, "هیچ batch نباید از سقفِ کلاینت بزرگ‌تر باشد")
                self.assertEqual(len(docs), len(ids))
                total += len(docs)
            self.assertEqual(total, n, "مجموعِ همه‌ی batchها باید دقیقاً همان تعدادِ چانک باشد")

    def test_get_max_batch_size_failure_falls_back_safely(self):
        """اگر کلاینت get_max_batch_size نداشت (نسخه‌ی قدیمی)، ایندکس نباید بترکد."""
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            _write_vault(vault, n_files=2, paras_per_file=1)

            fake_vs = _FakeVectorStore(cap=3)
            del fake_vs._client   # get_max_batch_size دیگر قابلِ صدازدن نیست

            with mock.patch.object(vs_mod, "VAULT_DIR", vault), \
                 mock.patch.object(vs_mod, "get_vectorstore", lambda: fake_vs), \
                 mock.patch.object(vs_mod, "_vectorstore", None), \
                 mock.patch.object(vs_mod, "_indexed", False):
                n = vs_mod.index_vault(force=False)

            total = sum(len(docs) for docs, _ids in fake_vs.calls)
            self.assertEqual(total, n)


if __name__ == "__main__":
    unittest.main()
