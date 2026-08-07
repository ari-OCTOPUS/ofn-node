"""
memory/vectorstore.py — ChromaDB vector store for RAG over the vault.

Indexes markdown notes into ChromaDB so agents can do semantic search over
the knowledge base. Two scopes, selected by the `root` arg on index_vault():

  · default (no `root` arg, or root=None): 4D-Vault/ only — the original,
    unchanged behavior. Collection "4d_vault", persisted at outputs/chroma_db,
    module-level singleton + `_indexed` skip-cache. Every existing caller of
    index_vault()/get_vectorstore()/search_vault() sees byte-identical
    behavior to before this file gained the `root` parameter.

  · root=<path>: index an arbitrary directory instead (e.g. the whole vault
    at DESKTOP, for the not-yet-wired whole-vault RAG capability). Applies an
    extended exclusion filter (segment safety-floor + reused .agentignore
    matcher — see `_make_path_filter`) instead of the narrow
    {".obsidian", "آرشیو"} check, and defaults to a *different* collection
    name ("vault_whole") unless `collection_name` is given explicitly. Kept
    deliberately distinct so nothing downstream ever conflates "4d_vault"
    (== 4D-Vault subset only) with whole-vault content just because both
    happen to live in the same physical Chroma persist directory.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

# 2026-08-07 — self-path bootstrap: this file loads both as a bare top-level
# module (`import vectorstore`, vault_bridge.py's pattern) and as a qualified
# submodule (`from memory import vectorstore`, brain/tools.py's and run.py's
# pattern). The internal imports below are deliberately absolute, not
# relative — a relative import depends on `__package__`, which is `""` under
# bare loading (the real ImportError logged in governor-alerts.md,
# 2026-08-06T23:02:39: "attempted relative import with no known parent
# package"). Adding this file's own directory to sys.path makes both loading
# styles resolve `embeddings`/`chunk_ids` the same way, independent of
# `__package__`.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from config.settings import DESKTOP

VAULT_DIR = DESKTOP / "4D-Vault"
CHROMA_DIR = Path(__file__).resolve().parent.parent / "outputs" / "chroma_db"

_vectorstore = None
_indexed = False

# Root-scoped indexing (index_vault(root=...)) never reads/writes the two
# globals above — it uses this separate cache instead, keyed by
# (collection_name, persist_directory). Keeps the default path's singleton
# semantics (and the existing test-suite's mock.patch.object(..., "_vectorstore",
# ...) / ("_indexed", ...) hooks) completely untouched.
_custom_vectorstores: dict[tuple[str, str], object] = {}

# Segments excluded no matter where in the tree they appear — used only by
# the root-scoped path (_make_path_filter below). The default 4D-Vault-only
# path keeps its original, narrower {".obsidian", "آرشیو"}-only check
# byte-for-byte (see index_vault()) so its behavior cannot shift.
#
# This set combines: the original two 4D-Vault content excludes, PLUS the
# repo constitution's hard no-touch list (_PROJECT_INSTRUCTIONS.md §0 "هرگز
# حذف نکن... هرگز به .git، هیچ پوشه _code... دست نزن" + §2's routing table,
# which marks _Archive/_Duplicates as transfer-only, never to be opened
# without explicit instruction). This floor applies REGARDLESS of what
# .agentignore does or doesn't list — belt-and-suspenders, not a substitute
# for it (see _agentignore_denier below for the .agentignore layer itself).
SAFE_EXCLUDE_SEGMENTS = frozenset({
    ".obsidian", "آرشیو",
    ".git", "_code", "_Archive", "_Duplicates",
    "node_modules", "_build", "_portable-build", "__pycache__",
})


def _agentignore_denier() -> Optional[Callable[[str], object]]:
    """Lazy-load `_denied()` from _ops/octopus_mcp/server.py.

    Reuses that module's exact .agentignore parsing/matching logic (same
    `_load_agentignore()` + `_denied()` pair the MCP path-guard uses) instead
    of a second, independently-maintained glob implementation here —
    consistency across the repo's tooling matters more than decoupling for
    something this security-relevant. Import is lazy and read-only (the
    module's only import-time side effect is reading .agentignore); it is
    only ever exercised on the root-scoped index_vault() path, never on the
    default call.

    Returns the `_denied(rel_str) -> str | None` callable, or None if the
    reused module can't be imported for any reason (fail-soft — the
    SAFE_EXCLUDE_SEGMENTS floor above still applies on its own either way).
    """
    try:
        _ops_dir = DESKTOP / "_ops"
        if str(_ops_dir) not in sys.path:
            sys.path.insert(0, str(_ops_dir))
        from octopus_mcp import server as _srv  # noqa: E402
        return _srv._denied
    except Exception:
        return None


def _make_path_filter(root: Path) -> Callable[[Path], bool]:
    """Build predicate(md_path) -> True-if-excluded for a root-scoped call.

    Two independent layers; either one excludes:
      1. SAFE_EXCLUDE_SEGMENTS, checked against the path's segments relative
         to `root` — always on, regardless of .agentignore content. Using
         root-relative parts (rather than the full absolute path) means a
         coincidental match somewhere in an ancestor directory (e.g. a temp
         dir under a path that happens to contain one of these names) can't
         cause a false exclusion.
      2. .agentignore, via the reused `_denied()`, checked against the path
         relative to the repo root (DESKTOP) — meaningful only for paths
         that actually live inside the repo. A path outside it (e.g. an
         isolated test-fixture directory) simply skips this layer; layer 1
         still applies.
    """
    denier = _agentignore_denier()
    root = Path(root)

    def _excluded(md_path: Path) -> bool:
        try:
            rel_parts = md_path.resolve().relative_to(root.resolve()).parts
        except ValueError:
            rel_parts = md_path.parts
        if any(seg in SAFE_EXCLUDE_SEGMENTS for seg in rel_parts):
            return True
        if denier is not None:
            try:
                rel_to_repo = md_path.resolve().relative_to(DESKTOP.resolve())
            except ValueError:
                return False
            if denier(str(rel_to_repo)) is not None:
                return True
        return False

    return _excluded


def get_vectorstore():
    """Get or create the default ChromaDB vector store (singleton, "4d_vault").
    Unchanged — backs the default (no-root) index_vault()/search_vault() path."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    from langchain_chroma import Chroma
    from embeddings import get_embeddings

    CHROMA_DIR.parent.mkdir(exist_ok=True)
    _vectorstore = Chroma(
        collection_name="4d_vault",
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )
    return _vectorstore


def get_vectorstore_for(collection_name: str, persist_directory: Optional[Path] = None):
    """Get/create a ChromaDB vector store for an arbitrary (collection_name,
    persist_directory) pair — singleton per pair, entirely separate from
    get_vectorstore()'s own "4d_vault" singleton/cache (never shares or
    collides with it). Used by root-scoped index_vault(root=...) calls, and
    by tests to point at a throwaway persist_directory so nothing ever
    touches the real outputs/chroma_db/ store."""
    from langchain_chroma import Chroma
    from embeddings import get_embeddings

    pdir = Path(persist_directory) if persist_directory is not None else CHROMA_DIR
    key = (collection_name, str(pdir))
    if key in _custom_vectorstores:
        return _custom_vectorstores[key]

    pdir.parent.mkdir(parents=True, exist_ok=True)
    vs = Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(pdir),
    )
    _custom_vectorstores[key] = vs
    return vs


def index_vault(force: bool = False, root: Optional[Path] = None,
                 collection_name: Optional[str] = None,
                 persist_directory: Optional[Path] = None) -> int:
    """
    Index markdown files into ChromaDB. Returns the number of chunks indexed.

    root=None (default): 4D-Vault/ only, exactly as before this function
      gained a `root` parameter — same VAULT_DIR, same
      {".obsidian", "آرشیو"} filter, same "4d_vault" singleton
      collection/store (get_vectorstore()), same module-level `_indexed`
      skip-cache (skips if already indexed unless force=True).
      `collection_name`/`persist_directory` are ignored on this path.

    root=<path>: index `root` instead of 4D-Vault/. Applies the extended
      exclusion filter (see `_make_path_filter`: SAFE_EXCLUDE_SEGMENTS +
      reused .agentignore matcher). Collection defaults to "vault_whole"
      (deliberately NOT "4d_vault") unless `collection_name` is given
      explicitly; persist_directory defaults to the same CHROMA_DIR as the
      default path but may be overridden (e.g. by tests, to a throwaway temp
      directory). Does not consult or set the legacy `_indexed` flag — every
      root-scoped call re-indexes.
    """
    global _indexed

    is_default = root is None
    target_dir = VAULT_DIR if is_default else Path(root)

    if is_default and _indexed and not force:
        return 0

    if not target_dir.exists():
        raise FileNotFoundError(f"Vault root not found at {target_dir}")

    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    if is_default:
        def _excluded(p: Path) -> bool:
            return ".obsidian" in p.parts or "آرشیو" in p.parts
    else:
        _excluded = _make_path_filter(target_dir)

    # Load all markdown files
    docs: list[Document] = []
    for md_path in target_dir.rglob("*.md"):
        if _excluded(md_path):
            continue
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
            # Extract title from first heading or filename
            title = md_path.stem
            for line in text.split("\n"):
                if line.startswith("# "):
                    title = line.lstrip("# ").strip()
                    break

            docs.append(Document(
                page_content=text,
                metadata={
                    "source": str(md_path.relative_to(target_dir)),
                    "title": title,
                    "path": str(md_path),
                }
            ))
        except Exception:
            continue

    if not docs:
        return 0

    # Split into chunks for better retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(docs)

    # Add to vector store
    if is_default:
        vs = get_vectorstore()
        # Clear existing if force
        if force:
            vs.delete_collection()
            global _vectorstore
            _vectorstore = None
            vs = get_vectorstore()
    else:
        cname = collection_name or "vault_whole"
        pdir = Path(persist_directory) if persist_directory is not None else CHROMA_DIR
        vs = get_vectorstore_for(cname, persist_directory=pdir)
        if force:
            vs.delete_collection()
            _custom_vectorstores.pop((cname, str(pdir)), None)
            vs = get_vectorstore_for(cname, persist_directory=pdir)

    # B3: ID پایدارِ per-source (memory/chunk_ids.py) — مستقل از ترتیبِ سراسری.
    # ID قبلی اندیسِ سراسریِ i را در خود داشت: ویرایشِ هر یادداشت، ID همه‌ی
    # chunkهای بعدی را عوض می‌کرد و نسخه‌های کهنه برای همیشه می‌ماندند.
    from chunk_ids import ids_for_chunks
    ids = ids_for_chunks([(ch.metadata.get("source", ""), ch.page_content)
                          for ch in chunks])

    # B3: پاک‌سازیِ chunkهای کهنه‌ی همان sourceها قبل از افزودن — ویرایشِ
    # یادداشت دیگر نسخه‌ی قدیمی به‌جا نمی‌گذارد (IDهای طرحِ قدیم هم همین‌جا
    # به‌طورِ طبیعی حذف می‌شوند). اگر delete در نسخه‌ی chroma موجود نبود،
    # مثل قبل فقط upsert می‌کنیم — index هرگز نمی‌شکند.
    try:
        for src in {ch.metadata.get("source", "") for ch in chunks}:
            vs.delete(where={"source": src})
    except Exception:
        pass

    # Chroma rejects a single add/upsert call above its own max batch size
    # (client.get_max_batch_size(), version-dependent -- 5461 on 1.5.9). A
    # vault this size (9k+ chunks) blows that in one call; split it up.
    try:
        max_batch = vs._client.get_max_batch_size()
    except Exception:
        max_batch = 2000
    for i in range(0, len(chunks), max_batch):
        vs.add_documents(chunks[i:i + max_batch], ids=ids[i:i + max_batch])
    if is_default:
        _indexed = True
    return len(chunks)


def search_vault(query: str, k: int = 3) -> list[dict]:
    """
    Semantic search over 4D-Vault.
    Returns list of {content, source, title} dicts.
    """
    vs = get_vectorstore()
    results = vs.similarity_search_with_relevance_scores(query, k=k)

    out = []
    for doc, score in results:
        out.append({
            "content": doc.page_content[:500],
            "source": doc.metadata.get("source", "unknown"),
            "title": doc.metadata.get("title", "unknown"),
            "relevance": round(score, 3),
        })
    return out


if __name__ == "__main__":
    print(f"Indexing {VAULT_DIR} ...")
    n = index_vault()
    print(f"✓ Indexed {n} chunks")

    # Test search
    print("\n=== Search: 'E_shadow چیست؟' ===")
    for r in search_vault("E_shadow چیست؟", k=3):
        print(f"  [{r['relevance']}] {r['title']}")
        print(f"    {r['content'][:100]}...")
        print()
