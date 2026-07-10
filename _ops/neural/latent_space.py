#!/usr/bin/env python3
"""latent_space.py — Phase 2 (Blueprint): فضای latent مشترک R^32.

هر لایهٔ ارگانیسم زبان خودش دارد (text، float، dict، RFC). این ماژول یک
فضای مشترکِ embedding ایجاد می‌کند تا لایه‌ها بتوانند semantically با هم مقایسه
شوند — cosine similarity، nearest-neighbor retrieval، و mean-pool integration.

Dependency: numpy (قبلاً در codebase موجود — hebbian.py, b4_fusion.py).
Persist: JSON (state/latent-vectors.json).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np


def _default_persist() -> Path:
    """env-اول (OPS_DIR) تا تستِ harness-ایزوله state واقعی/repo را آلوده نکند
    (همان درسِ bcm 2026-07-10)؛ بدونِ env = _ops/state کنارِ ماژول (production)."""
    ops = os.environ.get("OPS_DIR")
    base = Path(ops) if ops else Path(__file__).resolve().parent.parent
    return base / "state" / "latent-vectors.json"


_DEFAULT_PERSIST = _default_persist()

# آستانهٔ cosine similarity — نتایج زیر این مقدار discard می‌شوند
_SIMILARITY_THRESHOLD = 0.1


class SharedLatentSpace:
    """فضای latent مشترک برای هارمونی‌سازی زبانِ لایه‌ها.

    هر embedding یک key منحصربفرد + vector R^dim + metadata {layer, ts, source} دارد.
    cosine similarity برای retrieval. mean-pool برای integration. JSON برای persist.
    """

    def __init__(self, dim: int = 32, persist_path: Path | str | None = None):
        self.dim = dim
        self._vectors: dict[str, np.ndarray] = {}
        self._metadata: dict[str, dict] = {}
        self._persist_path = Path(persist_path) if persist_path else _DEFAULT_PERSIST
        self._load()

    # ─── core operations ────────────────────────────────────────────────────

    def embed(self, key: str, vector: np.ndarray, layer: str = "",
              source: str = "") -> None:
        """یک embedding در فضای مشترک ذخیره کن. key منحصربفرد — overwrite."""
        if vector.shape != (self.dim,):
            # auto-resize: اگر vector کم‌بُعد‌تر → pad با صفر
            if vector.ndim == 1 and len(vector) < self.dim:
                padded = np.zeros(self.dim)
                padded[:len(vector)] = vector
                vector = padded
            else:
                raise ValueError(f"expected R^{self.dim}, got {vector.shape}")
        self._vectors[key] = vector.copy()
        self._metadata[key] = {"layer": layer, "ts": time.time(), "source": source}

    def get(self, key: str) -> np.ndarray | None:
        """Read-only access به یک embedding."""
        return self._vectors.get(key)

    def similar(self, query: np.ndarray, top_k: int = 5,
                threshold: float = _SIMILARITY_THRESHOLD) -> list[tuple[str, float]]:
        """cosine similarity retrieval — top_k نزدیک‌ترین به query vector.

        returns: [(key, cosine_score), ...] sorted descending. فقط scores > threshold."""
        if not self._vectors:
            return []
        if query.shape != (self.dim,):
            return []
        q_norm = np.linalg.norm(query)
        if q_norm < 1e-12:
            return []  # zero vector → no meaningful similarity
        q_unit = query / q_norm

        keys = list(self._vectors.keys())
        # vectorized: build matrix and compute all dot products
        matrix = np.array([self._vectors[k] for k in keys])  # (N, dim)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms < 1e-12, 1.0, norms)  # avoid div-by-zero
        unit_matrix = matrix / norms
        scores = unit_matrix @ q_unit  # (N,) = cosine similarities

        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(keys[i], float(scores[i]))
                for i in top_idx if scores[i] > threshold]

    def nearest(self, key: str, top_k: int = 5) -> list[tuple[str, float]]:
        """nearest neighbors از یک key موجود در space."""
        if key not in self._vectors:
            return []
        return self.similar(self._vectors[key], top_k)

    def integrate(self, keys: list[str]) -> np.ndarray:
        """mean-pool از چند embedding → یک vector نماینده.
        اگر هیچ key موجود نباشد → zero vector."""
        vecs = [self._vectors[k] for k in keys if k in self._vectors]
        if not vecs:
            return np.zeros(self.dim)
        return np.mean(vecs, axis=0)

    def count(self) -> int:
        """تعداد embeddingهای ذخیره‌شده."""
        return len(self._vectors)

    def keys(self) -> list[str]:
        """همه keyهای ذخیره‌شده (برای sync لایه‌های بالاتر مثل BCM — Phase 3)."""
        return list(self._vectors.keys())

    def keys_by_layer(self, layer: str) -> list[str]:
        """همه keyهایی که از یک layer هستند."""
        return [k for k, m in self._metadata.items() if m.get("layer") == layer]

    def remove(self, key: str) -> bool:
        """حذف یک embedding. returns True اگر وجود داشت."""
        if key in self._vectors:
            del self._vectors[key]
            self._metadata.pop(key, None)
            return True
        return False

    # ─── persistence (JSON) ────────────────────────────────────────────────

    def store(self) -> None:
        """persist به JSON. atomic write via .tmp + replace."""
        if not self._vectors:
            return
        try:
            records = []
            for key, vec in self._vectors.items():
                meta = self._metadata.get(key, {})
                records.append({
                    "key": key,
                    "vector": vec.tolist(),
                    "layer": meta.get("layer", ""),
                    "ts": meta.get("ts", 0),
                    "source": meta.get("source", ""),
                })
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._persist_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(records, ensure_ascii=False), "utf-8")
            tmp.replace(self._persist_path)
        except OSError:
            pass  # fail-soft: persist نباید crash کند

    def _load(self) -> None:
        """load از JSON."""
        if not self._persist_path.exists():
            return
        try:
            records = json.loads(self._persist_path.read_text("utf-8"))
            for rec in records:
                key = rec.get("key", "")
                vec = rec.get("vector", [])
                if not key or not vec:
                    continue
                arr = np.array(vec, dtype=np.float64)
                # اگر dim نمی‌خواند → skip (backward compat)
                if len(arr) != self.dim:
                    continue
                self._vectors[key] = arr
                self._metadata[key] = {
                    "layer": rec.get("layer", ""),
                    "ts": rec.get("ts", 0),
                    "source": rec.get("source", ""),
                }
        except (json.JSONDecodeError, OSError, ValueError):
            pass  # corrupt file → start fresh (fail-soft)
