# فاز ۲ (Blueprint) — Shared Latent Space: هارمونی‌سازی زبانِ لایه‌ها

## هدف
هر لایهٔ ارگانیسم زبان خودش را دارد (text، float، dict، RFC). Phase 2 یک embedding space مشترک R^32 ایجاد می‌کند تا لایه‌ها بتوانند با هم «حرف بزنند».

## معماری

```
┌─────────────┐   encode()    ┌──────────────────┐
│ SensoryBus  │──────────────→│                  │
│ (text labels)│              │  SharedLatentSpace │
├─────────────┤   encode()    │  R^32 cosine sim  │
│ School       │──────────────→│  - embed()        │
│ (awareness)  │              │  - similar()      │
├─────────────┤   encode()    │  - store()        │
│ Doctor       │──────────────→│  - nearest()     │
│ (RFCs)       │              │  - integrate()    │
├─────────────┤   encode()    │                  │
│ Box          │──────────────→│  persist:         │
│ (phi_t)      │              │  state/latent.db  │
└─────────────┘              └──────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ canonical_         │
                              │ consolidation()   │
                              │ (vector integrate  │
                              │  نه text string)   │
                              └──────────────────┘
```

## تغییرات (۷ فایل جدید/تغییر + ۳ تست)

### فایل ۱ — `_ops/neural/latent_space.py` (nieuw, ~۲۰۰ خط)

**Core module.** SharedLatentSpace class با:

```python
class SharedLatentSpace:
    """فضای latent مشترک R^32 برای هارمونی‌سازی زبانِ لایه‌ها."""
    
    def __init__(self, dim=32, persist_path=None):
        self.dim = dim
        self._vectors: dict[str, np.ndarray] = {}  # key → R^32
        self._metadata: dict[str, dict] = {}         # key → {layer, ts, source}
        self._persist_path = persist_path  # JSON or SQLite
        self._load()
    
    def embed(self, key: str, vector: np.ndarray, layer: str, source: str) -> None:
        """یک embedding در فضای مشترک ذخیره کن."""
        assert vector.shape == (self.dim,), f"expected R^{self.dim}, got {vector.shape}"
        self._vectors[key] = vector
        self._metadata[key] = {"layer": layer, "ts": time.time(), "source": source}
    
    def similar(self, query: np.ndarray, top_k: int = 5) -> list[tuple[str, float]]:
        """cosine similarity retrieval — top_k نزدیک‌ترین."""
        # numpy vectorized
        if not self._vectors:
            return []
        query_norm = query / (np.linalg.norm(query) + 1e-12)
        keys = list(self._vectors.keys())
        matrix = np.array([self._vectors[k] for k in keys])
        norms = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12)
        scores = norms @ query_norm  # dot product = cosine (both normalized)
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(keys[i], float(scores[i])) for i in top_idx if scores[i] > 0.1]
    
    def nearest(self, key: str, top_k: int = 5) -> list[tuple[str, float]]:
        """nearest neighbors از یک key موجود."""
        if key not in self._vectors:
            return []
        return self.similar(self._vectors[key], top_k)
    
    def integrate(self, keys: list[str]) -> np.ndarray:
        """mean-pool از چند embedding → یک vector نماینده."""
        vecs = [self._vectors[k] for k in keys if k in self._vectors]
        if not vecs:
            return np.zeros(self.dim)
        return np.mean(vecs, axis=0)
    
    def store(self) -> None:
        """persist به JSON."""
        ...
    
    def _load(self) -> None:
        """load از JSON."""
        ...
```

**Persist:** `state/latent-vectors.json` — append-only JSON با `{key, vector, layer, ts, source}`.

**Dependency:** فقط `numpy`. `numpy` قبلاً در `neural/hebbian.py` و `doctor/box/b4_fusion.py` استفاده شده — نه جدید.

---

### فایل ۲ — `_ops/neural/encoders.py` (nieuw, ~۱۵۰ خط)

**Encoder per layer.** هر لایه native format → R^32:

```python
def encode_observation(obs_type: str, label: str, dim=32) -> np.ndarray:
    """SensoryBus observation → R^32 via hash-based projection."""
    # deterministic hash-based encoding (no LLM)
    # hash(obs_type + label) → seed → R^32 via PRNG
    
def encode_awareness(awareness_vector: np.ndarray, dim=32) -> np.ndarray:
    """School awareness field [0,1]^N → R^32 via learned linear projection.
    اگر dim != awareness dim → pad/truncate + normalize."""
    
def encode_rfc(rfc_id: str, bottleneck: str, severity: str, dim=32) -> np.ndarray:
    """Doctor RFC → R^32 via hash + severity injection."""
    
def encode_phi_t(phi_vec: np.ndarray, sigma: float, dim=32) -> np.ndarray:
    """Box fusion field → R^32 via spectral features."""
    
def encode_calibration(verdicts: list[dict], dim=32) -> np.ndarray:
    """Calibration verdict history → R^32 via statistical features."""
```

**همه encoders:** stdlib + numpy only. Hash-based projections (deterministic، بازتولیدپذیر). No LLM.

**Hash projection algorithm:**
```python
import hashlib, struct
def _hash_project(text: str, dim: int) -> np.ndarray:
    """Deterministic hash → R^dim via SHA-256 chunks."""
    h = hashlib.sha256(text.encode()).digest()
    vec = np.zeros(dim)
    for i in range(dim):
        chunk = h[i % len(h):i % len(h) + 4]
        vec[i] = struct.unpack('<f', chunk + b'\x00\x00\x00\x00'[:4-len(chunk)])[0]
    return vec / (np.linalg.norm(vec) + 1e-12)
```

---

### فایل ۳ — `_ops/neural/consolidation.py` — تغییر (ویرایش)

**`ConsolidatedInsight` dataclass اضافه‌شود:**
```python
@dataclass
class ConsolidatedInsight:
    cycle: int
    insights: list[str]
    verified_sources: list[str]
    discarded_sources: list[str]
    timestamp: float = field(default_factory=time.time)
    # Phase 2: latent representation
    latent_vector: list[float] | None = None  # R^32 mean-pool of source embeddings
    similar_keys: list[str] | None = None      # nearest neighbors from previous cycles
```

**`ConsolidationCycle.run()` تغییر:**
- بعد از text insight generation → optional: اگر latent_space موجود →
  - هر verified source را encode کن
  - mean-pool → `latent_vector`
  - `latent_space.similar()` → `similar_keys` (retrieval از تاریخچه)
  - `latent_space.store()` ذخیره

**backward compatible:** اگر latent_space=None → رفتار فعلی (فقط text strings)

---

### فایل ۴ — `_ops/wiring.py` — تغییر `canonical_consolidation()`

**پارامتر جدید:** `latent_space=None`

```python
def canonical_consolidation(neural_stack, school_bridge=None,
                            acquisition_data=None, doctor_archive=None,
                            latent_space=None):
    ...
    # Phase 2: اگر latent_space موجود → consolidation با vector integration
    if latent_space is not None:
        # encode هر source
        # integrate → latent_vector
        # similar → nearest from history
        # store در latent_space
    ...
```

**`consolidation_beat()` تغییر:**
- `neural_stack["consolidation"]` را پاس بده (همانطور که الان هست)
- `latent_space` instance از `_neural_stack["latent_space"]` یا ساخت جدید

---

### فایل ۵ — `_ops/wiring.py` — تغییر `make_school_bridge()`

**School output غنی‌تر:**
```python
def make_school_bridge(state_path=None):
    """..."""
    ...
    bridge.full_awareness_vector()  # ← جدید: کل vector را برمی‌گرداند
```

در `school_bridge.py`: متد جدید `full_awareness_vector() -> list[float] | None`
در `canonical_consolidation()`: اگر school_bridge و latent_space →
  `encode_awareness(bridge.full_awareness_vector())` به‌جای فقط `mean_awareness()`

---

### فایل ۶ — `_ops/afferent/school_bridge.py` — تغییر کوچک

**متد جدید:**
```python
def full_awareness_vector(self) -> list[float] | None:
    """کل awareness vector [0,1]^N — نه فقط mean."""
    return self.field.awareness.tolist() if self.field else None
```

---

### فایل ۷ — `_ops/neural/__init__.py` — تغییر

اضافه کردن exports:
```python
from .latent_space import SharedLatentSpace
from .encoders import encode_observation, encode_awareness, encode_rfc, encode_phi_t
```

---

### تست‌ها

**`_ops/tests/test_latent_space.py` (~۱۲ تست):**
1. embed + retrieve (cosine similarity)
2. nearest neighbors
3. integrate (mean-pool)
4. persist (save/load JSON)
5. dim validation
6. empty space → []
7. zero vector → []
8. duplicate key → overwrite
9. similar threshold (>0.1)
10. metadata tracking

**`_ops/tests/test_encoders.py` (~۱۰ تست):**
1. encode_observation: deterministic
2. encode_observation: same input → same output
3. encode_observation: different input → different output
4. encode_awareness: scalar → R^32
5. encode_rfc: deterministic
6. encode_phi_t: spectral features
7. encode_calibration: verdict history
8. all encoders: output dim=32
9. all encoders: normalized (||v|| ≈ 1)

**`_ops/tests/test_consolidation_latent.py` (~۷ تست):**
1. consolidation with latent_space → latent_vector not None
2. consolidation without latent_space → backward compatible
3. similar_keys populated from history
4. encode each source type
5. integrate mean-pool correctness
6. persist cycle in latent_space
7. retrieval finds previous cycles

**`run_all.py` → +۳ فایل → ۷۲ فایل**

---

## ترتیب اجرا

1. `latent_space.py` — core module (SharedLatentSpace)
2. `encoders.py` — per-layer encoders
3. `test_latent_space.py` — ۱۲ تست سبز
4. `test_encoders.py` — ۱۰ تست سبز
5. `consolidation.py` — dataclass + run() تغییر (backward compatible)
6. `school_bridge.py` — `full_awareness_vector()`
7. `wiring.py` — `canonical_consolidation()` + `consolidation_beat()` تغییر
8. `test_consolidation_latent.py` — ۷ تست سبز
9. `run_all.py` → ۷۲/۷۲ سبز

---

## خطوط قرمز
- **فقط stdlib + numpy** (numpy قبلاً در codebase موجود)
- **backward compatible:** latent_space=None → رفتار فعلی بدون تغییر
- **no LLM calls** — همه encoders deterministic hash-based
- **no money spend**
- **no change** به fitness.py, school_bridge.learn_from(), SensoryBus routing
- **persist JSON** — نه SQLite جدید
- **هر encoder بازتولیدپذیر** — همان input → همیشه همان output

## معیار pre-registered
- metric: `consolidation_latent_dim` == 32
- metric: `encoder_determinism` — same input → same output (100%)
- metric: `retrieval_recall` — stored embedding found in top-5 (100%)
- held-out suite 5/5 حفظ
- backward compat: consolidation without latent_space → None/empty (not crash)
