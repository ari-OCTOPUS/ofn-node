"""
memory/embeddings.py — Multilingual embedding model for RAG.

Uses sentence-transformers multilingual model (runs locally, free, offline).
The model downloads on first use, then is cached.
"""
from __future__ import annotations

from functools import lru_cache

# Multilingual model that handles Persian + English + math
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_EMBEDDINGS = None


def get_embeddings():
    """
    Get the HuggingFace embedding model (singleton).
    Downloads on first call (~120MB), then cached locally.
    """
    global _EMBEDDINGS
    if _EMBEDDINGS is not None:
        return _EMBEDDINGS

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        raise ImportError(
            "langchain-huggingface not installed. Run: pip install langchain-huggingface sentence-transformers"
        )

    _EMBEDDINGS = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return _EMBEDDINGS


if __name__ == "__main__":
    print(f"Loading embedding model: {MODEL_NAME}")
    print("(first run downloads ~120MB, please wait...)")
    emb = get_embeddings()
    # quick test
    vec = emb.embed_query("E_shadow چیست؟")
    print(f"✓ Embedding dim: {len(vec)}")
    print(f"✓ First 5 values: {vec[:5]}")
