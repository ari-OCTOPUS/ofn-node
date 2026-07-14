"""
memory/vectorstore.py — ChromaDB vector store for RAG over the 4D-Vault.

Indexes all markdown notes from 4D-Vault/ so agents can do semantic search
over the entire knowledge base.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from config.settings import DESKTOP

VAULT_DIR = DESKTOP / "4D-Vault"
CHROMA_DIR = Path(__file__).resolve().parent.parent / "outputs" / "chroma_db"

_vectorstore = None
_indexed = False


def get_vectorstore():
    """Get or create the ChromaDB vector store (singleton)."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    from langchain_chroma import Chroma
    from .embeddings import get_embeddings

    CHROMA_DIR.parent.mkdir(exist_ok=True)
    _vectorstore = Chroma(
        collection_name="4d_vault",
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )
    return _vectorstore


def index_vault(force: bool = False) -> int:
    """
    Index all markdown files from 4D-Vault/ into ChromaDB.
    Returns the number of documents indexed.
    Skips if already indexed (unless force=True).
    """
    global _indexed

    if _indexed and not force:
        return 0

    if not VAULT_DIR.exists():
        raise FileNotFoundError(f"4D-Vault not found at {VAULT_DIR}")

    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # Load all markdown files
    docs: list[Document] = []
    for md_path in VAULT_DIR.rglob("*.md"):
        if ".obsidian" in md_path.parts or "آرشیو" in md_path.parts:
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
                    "source": str(md_path.relative_to(VAULT_DIR)),
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
    vs = get_vectorstore()
    # Clear existing if force
    if force:
        vs.delete_collection()
        global _vectorstore
        _vectorstore = None
        vs = get_vectorstore()

    # B3: ID پایدارِ per-source (memory/chunk_ids.py) — مستقل از ترتیبِ سراسری.
    # ID قبلی اندیسِ سراسریِ i را در خود داشت: ویرایشِ هر یادداشت، ID همه‌ی
    # chunkهای بعدی را عوض می‌کرد و نسخه‌های کهنه برای همیشه می‌ماندند.
    from .chunk_ids import ids_for_chunks
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

    vs.add_documents(chunks, ids=ids)
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
