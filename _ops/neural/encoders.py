#!/usr/bin/env python3
"""encoders.py — Phase 2 (Blueprint): encoder per layer (native format → R^32).

هر لایهٔ ارگانیسم فرمت متفاوتی دارد. این ماژول یک encoder برای هر لایه فراهم
می‌کند — deterministic (همان input → همیشه همان output)، بدون LLM.

Encoders:
  - encode_observation: SensoryBus (text labels) → R^32
  - encode_awareness: School (awareness vector [0,1]^N) → R^32
  - encode_rfc: Doctor (RFC) → R^32
  - encode_phi_t: Box (fusion field + sigma) → R^32
  - encode_calibration: Calibration (verdict history) → R^32

همه encoders: stdlib + numpy. Hash-based projection (SHA-256 → R^dim).
"""
from __future__ import annotations

import hashlib
import struct
from typing import Any

import numpy as np

# ─── hash-based projection core ────────────────────────────────────────────

def _hash_project(text: str, dim: int = 32) -> np.ndarray:
    """Deterministic hash → R^dim via SHA-256 chunks.

    SHA-256 = 32 bytes = 8 floats (little-endian). For dim > 8, hash text+index
    to generate more dimensions. Output normalized to unit vector."""
    vec = np.zeros(dim, dtype=np.float64)
    for i in range(0, dim, 8):
        # هر 8 بُعد یک hash مجزا (برای differentiate بیشتر)
        chunk_text = f"{text}:{i // 8}"
        h = hashlib.sha256(chunk_text.encode("utf-8")).digest()  # 32 bytes
        for j in range(min(8, dim - i)):
            # هر 4 bytes → یک float32 little-endian
            b = h[j * 4:(j + 1) * 4]
            if len(b) < 4:
                b = b + b'\x00' * (4 - len(b))
            val = struct.unpack('<f', b)[0]
            vec[i + j] = val
    norm = np.linalg.norm(vec)
    if norm < 1e-12:
        # fallback: اگر vector صفر شد، seed از text
        seed_val = hash(text) % 10000 / 10000.0
        vec[0] = seed_val
        norm = np.linalg.norm(vec)
    return vec / norm  # unit vector


def _hash_project_multi(texts: list[str], dim: int = 32) -> np.ndarray:
    """چند text → mean-pool از hash projections → R^32."""
    if not texts:
        return np.zeros(dim)
    vecs = [_hash_project(t, dim) for t in texts]
    return np.mean(vecs, axis=0)


# ─── per-layer encoders ────────────────────────────────────────────────────

def encode_observation(obs_type: str, label: str, dim: int = 32) -> np.ndarray:
    """SensoryBus observation → R^32.

    obs_type: نوع مشاهده (مثلاً "lead", "error", "payment")
    label: متنِ برچسب (مثلاً "A01", "E03")
    Deterministic: همان input → همیشه همان output."""
    combined = f"obs:{obs_type}:{label}"
    return _hash_project(combined, dim)


def encode_awareness(awareness_vector: list[float] | np.ndarray | None,
                     dim: int = 32) -> np.ndarray:
    """School awareness field [0,1]^N → R^32.

    اگر awareness_vector None یا خالی → zero vector.
    اگر dim متفاوت → pad با صفر یا truncate."""
    if awareness_vector is None:
        return np.zeros(dim)
    arr = np.array(awareness_vector, dtype=np.float64)
    if arr.size == 0:
        return np.zeros(dim)
    # flatten
    arr = arr.flatten()
    # pad/truncate به dim
    if len(arr) < dim:
        padded = np.zeros(dim)
        padded[:len(arr)] = arr
        arr = padded
    elif len(arr) > dim:
        arr = arr[:dim]
    norm = np.linalg.norm(arr)
    if norm < 1e-12:
        return np.zeros(dim)
    return arr / norm


def encode_rfc(rfc_id: str, bottleneck: str, severity: str = "",
               dim: int = 32) -> np.ndarray:
    """Doctor RFC → R^32 via hash projection.

    rfc_id: شناسهٔ RFC (مثلاً "RFC-abc123")
    bottleneck: متنِ گلوگاه
    severity: "critical" | "high" | "medium" | "low" (injects semantic signal)
    Deterministic."""
    combined = f"rfc:{rfc_id}:{bottleneck}:{severity}"
    base = _hash_project(combined, dim)
    # severity injection: first 4 dims را با severity weight تعدیل کن
    sev_weights = {"critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.7}
    w = sev_weights.get(severity, 1.0)
    base[:4] *= w
    norm = np.linalg.norm(base)
    if norm < 1e-12:
        return base
    return base / norm


def encode_phi_t(phi_vec: np.ndarray | list[float] | None,
                 sigma: float = 0.0, dim: int = 32) -> np.ndarray:
    """Box fusion field → R^32.

    phi_vec: vector فیلدِ فیوژن (از b4_fusion.py)
    sigma: spectral ratio (near-critical ≈ 1.0)
    اگر phi_vec None → hash-based encoding از sigma."""
    if phi_vec is None:
        # fallback: از sigma encoding
        return _hash_project(f"phi:sigma={sigma:.4f}", dim)
    arr = np.array(phi_vec, dtype=np.float64).flatten()
    if arr.size == 0:
        return _hash_project(f"phi:sigma={sigma:.4f}", dim)
    # spectral features: combine phi_vec statistics with sigma
    stats = np.array([
        np.mean(arr), np.std(arr), np.min(arr), np.max(arr),
        np.median(arr), sigma, sigma ** 2, len(arr),
    ])
    base = np.zeros(dim)
    # stats → first dims
    for i, s in enumerate(stats):
        if i < dim:
            base[i] = s
    # بقیه dims از hash projection برای deterministic content signal
    hash_vec = _hash_project(f"phi:{len(arr)}:{sigma:.4f}", dim)
    # blend: stats + hash
    base = base + hash_vec
    norm = np.linalg.norm(base)
    if norm < 1e-12:
        return base
    return base / norm


def encode_calibration(verdicts: list[dict] | None, dim: int = 32) -> np.ndarray:
    """Calibration verdict history → R^32.

    verdicts: list of dicts با "verdict" key
    اگر None یا خالی → zero vector."""
    if not verdicts:
        return np.zeros(dim)
    # statistical features from verdicts
    total = len(verdicts)
    # count verdict types
    types = {}
    for v in verdicts:
        vt = v.get("verdict", "unknown") if isinstance(v, dict) else str(v)
        types[vt] = types.get(vt, 0) + 1
    # features: total count + normalized type frequencies
    features = [total]
    for vt in sorted(types.keys()):
        features.append(types[vt] / total if total > 0 else 0)
    # pad/truncate to dim
    arr = np.zeros(dim)
    for i, f in enumerate(features):
        if i < dim:
            arr[i] = f
    norm = np.linalg.norm(arr)
    if norm < 1e-12:
        return arr
    return arr / norm
