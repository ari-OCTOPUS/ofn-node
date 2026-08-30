"""تستِ پارامترِ root ِ index_vault: اسکوپِ کل-vault، جدا از 4D-Vault پیش‌فرض.

پس‌زمینه: index_vault() قبلاً فقط VAULT_DIR (4D-Vault/) را با یک فیلترِ نازکِ
{".obsidian", "آرشیو"} ایندکس می‌کرد. این تست سه ادعا را می‌سنجد -- بدونِ لمسِ
ChromaDB واقعی (outputs/chroma_db/) و بدونِ فراخوانیِ مدلِ embedding واقعی:

  1) فراخوانیِ پیش‌فرض (بدونِ root) دقیقاً همان رفتارِ قدیمی را دارد -- فیلترِ
     نازک، بدونِ نشتِ فیلترِ گسترده به مسیرِ پیش‌فرض (رگرسیون).
  2) فراخوانیِ root-scoped با فیلترِ گسترده: safety-floor (.git/_code/_Archive/
     _Duplicates/node_modules/_build/_portable-build/__pycache__/.obsidian/آرشیو)
     مسیرهای ناامن را حذف می‌کند، فایل‌های مشروع را نگه می‌دارد.
  3) نام‌گذاریِ collection: پیش‌فرضِ root-scoped "vault_whole" است، نه "4d_vault"
     -- تا محتوایِ کل-vault هرگز با محتوایِ فقط-4D-Vault قاطی نشود.

جداگانه (خارج از این فایل، طبقِ درخواستِ وظیفه): mutation-test با git stash
روی memory/vectorstore.py.
"""
from tests import _bootstrap  # noqa: F401

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import memory.vectorstore as vs_mod


class _FakeClient:
    def get_max_batch_size(self):
        return 2000


class _FakeVectorStore:
    """جایگزینِ langchain_chroma.Chroma -- فقط add_documents/delete را ضبط می‌کند."""

    def __init__(self):
        self._client = _FakeClient()
        self.added_sources: list[str] = []
        self.deleted: list = []

    def add_documents(self, docs, ids=None):
        assert ids is not None and len(ids) == len(docs)
        for d in docs:
            self.added_sources.append(d.metadata.get("source", ""))

    def delete(self, where=None):
        self.deleted.append(where)

    def delete_collection(self):
        pass


def _write(path: Path, text: str = "# نت\n\nمتنِ آزمایشی.\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestDefaultCallUnchanged(unittest.TestCase):
    """(۱) رگرسیون: root=None باید همان فیلترِ نازکِ قدیمی را داشته باشد --
    _Archive/_Duplicates/.git و غیره در مسیرِ پیش‌فرض *نباید* حذف شوند، چون
    فیلترِ گسترده هرگز نباید بی‌صدا وارد مسیرِ پیش‌فرض شود."""

    def test_narrow_filter_only_obsidian_and_arshiv_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            _write(vault / "good.md")
            _write(vault / ".obsidian" / "workspace.md")   # excluded (legacy)
            _write(vault / "آرشیو" / "old.md")               # excluded (legacy)
            # این سه تا زیرِ فیلترِ نازکِ قدیمی مجازند -- فقط فیلترِ گسترده
            # (که این مسیر نباید صداش کند) آن‌ها را می‌بندد:
            _write(vault / "_Archive" / "leak1.md")
            _write(vault / "_Duplicates" / "leak2.md")
            _write(vault / ".git" / "leak3.md")

            fake_vs = _FakeVectorStore()
            with mock.patch.object(vs_mod, "VAULT_DIR", vault), \
                 mock.patch.object(vs_mod, "get_vectorstore", lambda: fake_vs), \
                 mock.patch.object(vs_mod, "_vectorstore", None), \
                 mock.patch.object(vs_mod, "_indexed", False):
                n = vs_mod.index_vault(force=False)

            self.assertGreater(n, 0)
            sources = set(fake_vs.added_sources)
            self.assertIn("good.md", sources)
            self.assertNotIn(str(Path(".obsidian") / "workspace.md"), sources)
            self.assertNotIn(str(Path("آرشیو") / "old.md"), sources)
            # رگرسیون: فیلترِ گسترده نباید بی‌صدا به مسیرِ پیش‌فرض نشت کند
            self.assertIn(str(Path("_Archive") / "leak1.md"), sources,
                           "فیلترِ گسترده وارد مسیرِ پیش‌فرض شده -- رگرسیون")
            self.assertIn(str(Path("_Duplicates") / "leak2.md"), sources)
            self.assertIn(str(Path(".git") / "leak3.md"), sources)


class TestRootScopedExclusionFilter(unittest.TestCase):
    """(۲) فراخوانیِ root-scoped: safety-floor مسیرهای ناامن را می‌بندد،
    فایل‌های مشروع را رد می‌کند -- بدونِ لمسِ ChromaDB واقعی."""

    def _run(self, vault: Path, collection_name: str = "test_whole"):
        fake_vs = _FakeVectorStore()
        with mock.patch.object(vs_mod, "get_vectorstore_for",
                                lambda *a, **kw: fake_vs) as gvf:
            n = vs_mod.index_vault(root=vault, collection_name=collection_name)
        return n, fake_vs, gvf

    def test_excludes_safety_floor_includes_legit_files(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            # مشروع -- باید ایندکس شوند
            _write(vault / "note1.md")
            _write(vault / "03 - Projects" / "note2.md")
            # ناامن -- باید حذف شوند (safety floor، مستقل از .agentignore)
            _write(vault / "_Archive" / "old.md")
            _write(vault / "_Duplicates" / "dup.md")
            _write(vault / ".git" / "config.md")
            _write(vault / "some_pkg" / "_code" / "impl.md")
            _write(vault / "node_modules" / "pkg" / "readme.md")
            _write(vault / "__pycache__" / "cache.md")
            _write(vault / "_build" / "out.md")
            _write(vault / "_portable-build" / "out2.md")
            _write(vault / ".obsidian" / "ws.md")
            _write(vault / "آرشیو" / "old2.md")

            n, fake_vs, _ = self._run(vault)

            sources = set(fake_vs.added_sources)
            self.assertEqual(sources, {"note1.md", str(Path("03 - Projects") / "note2.md")})
            self.assertGreater(n, 0)

    def test_default_collection_name_is_vault_whole_not_4d_vault(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            _write(vault / "note.md")
            fake_vs = _FakeVectorStore()
            with mock.patch.object(vs_mod, "get_vectorstore_for",
                                    return_value=fake_vs) as gvf:
                vs_mod.index_vault(root=vault)  # collection_name omitted
            args, kwargs = gvf.call_args
            called_name = args[0] if args else kwargs.get("collection_name")
            self.assertEqual(called_name, "vault_whole")
            self.assertNotEqual(called_name, "4d_vault")

    def test_explicit_collection_name_is_respected(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            _write(vault / "note.md")
            fake_vs = _FakeVectorStore()
            with mock.patch.object(vs_mod, "get_vectorstore_for",
                                    return_value=fake_vs) as gvf:
                vs_mod.index_vault(root=vault, collection_name="my_custom_scope")
            args, kwargs = gvf.call_args
            called_name = args[0] if args else kwargs.get("collection_name")
            self.assertEqual(called_name, "my_custom_scope")

    def test_root_scoped_never_touches_legacy_indexed_flag(self):
        """root-scoped نباید global _indexed را دست بزند -- مسیرِ پیش‌فرض
        هنوز باید بعدش عادی رفتار کند (skip-cache قدیمی دست‌نخورده)."""
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            _write(vault / "note.md")
            fake_vs = _FakeVectorStore()
            with mock.patch.object(vs_mod, "get_vectorstore_for",
                                    lambda *a, **kw: fake_vs), \
                 mock.patch.object(vs_mod, "_indexed", False):
                vs_mod.index_vault(root=vault)
                self.assertFalse(vs_mod._indexed,
                                  "root-scoped نباید global _indexed را True کند")


class TestAgentignoreReuse(unittest.TestCase):
    """(۳الف) لایه‌ی .agentignore -- از طریقِ _denied ِ بازاستفاده‌شده از
    octopus_mcp/server.py، بدونِ ساختن هیچ فایلی."""

    def test_denier_loads_and_matches_real_agentignore(self):
        denier = vs_mod._agentignore_denier()
        self.assertIsNotNone(denier, "بازاستفاده از octopus_mcp/server._denied شکست خورد")
        self.assertIsNotNone(denier("secrets-export/x.md"))
        self.assertIsNotNone(denier("creds.env"))
        self.assertIsNone(denier("03 - Projects/foo.md"))


if __name__ == "__main__":
    unittest.main()
