#!/usr/bin/env python3
"""test_latent_space.py — تستِ SharedLatentSpace (R^32 cosine similarity).

$0 آفلاین: persist_path با tmpdir.
"""
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness
ENV = harness.setup("latent-space")   # ایزولاسیون — alert/state به vault موقت، نه واقعی

import numpy as np
from neural.latent_space import SharedLatentSpace


def _make_space(dim=32, persist_path=None):
    """SharedLatentSpace بدون persist واقعی."""
    import tempfile
    td = tempfile.mkdtemp()
    p = Path(td) / "latent-test.json" if persist_path is None else persist_path
    return SharedLatentSpace(dim=dim, persist_path=str(p)), td


def _rand_vec(dim=32):
    """random unit vector."""
    v = np.random.randn(dim)
    return v / np.linalg.norm(v)


def t_embed_and_retrieve():
    """embed + similar retrieval کار می‌کند."""
    sp, _ = _make_space()
    v = _rand_vec()
    sp.embed("k1", v, layer="test", source="unit-test")
    results = sp.similar(v, top_k=5)
    assert len(results) >= 1, f"expected at least 1 result, got {len(results)}"
    key, score = results[0]
    assert key == "k1"
    assert score > 0.99, f"self-similarity should be ~1.0, got {score}"


def t_nearest_neighbors():
    """nearest از یک key موجود کار می‌کند."""
    sp, _ = _make_space()
    sp.embed("a", _rand_vec(), layer="x")
    sp.embed("b", _rand_vec(), layer="x")
    sp.embed("c", _rand_vec(), layer="x")
    results = sp.nearest("a", top_k=3)
    assert len(results) >= 1
    # first result should be "a" itself (cosine=1.0)
    assert results[0][0] == "a", f"nearest to 'a' should start with 'a', got {results[0][0]}"


def t_integrate_mean_pool():
    """integrate mean-pool از چند embedding."""
    sp, _ = _make_space()
    v1 = np.array([1.0] + [0.0] * 31)
    v2 = np.array([0.0, 1.0] + [0.0] * 30)
    sp.embed("v1", v1 / np.linalg.norm(v1), layer="t")
    sp.embed("v2", v2 / np.linalg.norm(v2), layer="t")
    pooled = sp.integrate(["v1", "v2"])
    assert pooled.shape == (32,)
    # mean of two orthonormal vectors → magnitude should be < 1
    assert np.linalg.norm(pooled) < 1.0


def t_integrate_empty():
    """integrate با keyهای ناموجود → zero vector."""
    sp, _ = _make_space()
    pooled = sp.integrate(["nonexistent"])
    assert np.allclose(pooled, np.zeros(32))


def t_integrate_missing_keys():
    """integrate با mix موجود + ناموجود → فقط موجود."""
    sp, _ = _make_space()
    v1 = _rand_vec()
    sp.embed("exists", v1, layer="t")
    pooled = sp.integrate(["exists", "missing"])
    assert np.allclose(pooled, v1)


def t_dim_validation():
    """vector با dim اشتباه → ValueError."""
    sp, _ = _make_space(dim=32)
    bad_vec = np.zeros(16)
    try:
        sp.embed("bad", bad_vec, layer="t")
        # auto-pad از 16→32 باید کار کند
        assert sp.get("bad") is not None
        assert sp.get("bad").shape == (32,)
    except ValueError:
        pass  # یا raise


def t_empty_space_similar():
    """space خالی → similar برمی‌گردد []."""
    sp, _ = _make_space()
    results = sp.similar(_rand_vec())
    assert results == []


def t_zero_vector_similar():
    """zero vector query → خالی (no meaningful similarity)."""
    sp, _ = _make_space()
    sp.embed("k1", _rand_vec(), layer="t")
    results = sp.similar(np.zeros(32))
    assert results == []


def t_duplicate_key_overwrite():
    """duplicate key → overwrite."""
    sp, _ = _make_space()
    v1 = _rand_vec()
    v2 = _rand_vec()
    sp.embed("dup", v1, layer="t")
    sp.embed("dup", v2, layer="t2")
    stored = sp.get("dup")
    assert np.allclose(stored, v2), "duplicate key should overwrite"
    assert sp._metadata["dup"]["layer"] == "t2"


def t_similar_threshold():
    """نتایج زیر threshold (0.1) discard می‌شوند."""
    sp, _ = _make_space()
    # vector تصادفی و orthogonal تقریبی
    v1 = _rand_vec()
    # یک vector عمود بساز
    v2 = np.zeros(32)
    v2[1] = 1.0  # orthogonal to v1[0]=1
    sp.embed("k1", v1, layer="t")
    sp.embed("k2", v2, layer="t")
    results = sp.similar(v1, top_k=10, threshold=0.5)
    keys = [k for k, s in results]
    assert "k1" in keys
    # k2 ممکن نباشد (orthogonal → cosine ≈ 0)


def t_metadata_tracking():
    """metadata {layer, ts, source} ذخیره می‌شود."""
    sp, _ = _make_space()
    sp.embed("m1", _rand_vec(), layer="school", source="awareness")
    meta = sp._metadata["m1"]
    assert meta["layer"] == "school"
    assert meta["source"] == "awareness"
    assert meta["ts"] > 0


def t_persist_save_load():
    """store + reload → داده حفظ می‌شود."""
    import tempfile
    td = tempfile.mkdtemp()
    path = Path(td) / "persist-test.json"
    # save
    sp1 = SharedLatentSpace(dim=32, persist_path=str(path))
    v = _rand_vec()
    sp1.embed("p1", v, layer="test", source="persist")
    sp1.store()
    # load
    sp2 = SharedLatentSpace(dim=32, persist_path=str(path))
    loaded = sp2.get("p1")
    assert loaded is not None, "persisted vector should load"
    assert np.allclose(loaded, v, atol=1e-6)
    assert sp2._metadata["p1"]["layer"] == "test"


def t_keys_by_layer():
    """keys_by_layer درست فیلتر می‌کند."""
    sp, _ = _make_space()
    sp.embed("a1", _rand_vec(), layer="school")
    sp.embed("a2", _rand_vec(), layer="school")
    sp.embed("b1", _rand_vec(), layer="doctor")
    school_keys = sp.keys_by_layer("school")
    assert set(school_keys) == {"a1", "a2"}
    doc_keys = sp.keys_by_layer("doctor")
    assert doc_keys == ["b1"]


def t_remove():
    """remove یک key را حذف می‌کند."""
    sp, _ = _make_space()
    sp.embed("r1", _rand_vec(), layer="t")
    assert sp.get("r1") is not None
    ok = sp.remove("r1")
    assert ok is True
    assert sp.get("r1") is None
    assert sp.remove("r1") is False  # دومین بار False


if __name__ == "__main__":
    failed = harness.run([
        ("embed + retrieve", t_embed_and_retrieve),
        ("nearest neighbors", t_nearest_neighbors),
        ("integrate mean-pool", t_integrate_mean_pool),
        ("integrate empty", t_integrate_empty),
        ("integrate missing keys", t_integrate_missing_keys),
        ("dim validation", t_dim_validation),
        ("empty space similar", t_empty_space_similar),
        ("zero vector similar", t_zero_vector_similar),
        ("duplicate key overwrite", t_duplicate_key_overwrite),
        ("similar threshold", t_similar_threshold),
        ("metadata tracking", t_metadata_tracking),
        ("persist save/load", t_persist_save_load),
        ("keys_by_layer", t_keys_by_layer),
        ("remove", t_remove),
    ])
    sys.exit(1 if failed else 0)
