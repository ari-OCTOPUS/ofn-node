"""
config/settings.py — System configuration and golden-rule paths.

GOLDEN RULE: The 4D/ directory is the immutable reference. We NEVER write to it.
All paths below are READ-ONLY pointers to the source of truth.
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env is optional; falls back to defaults


# ── Paths ────────────────────────────────────────────────────────────────
SYSTEM_ROOT = Path(__file__).resolve().parent.parent          # 4d_system/
DESKTOP     = SYSTEM_ROOT.parent                              # Desktop/

# The immutable reference directory (GOLDEN RULE: READ-ONLY)
# مسیرِ نسبی در .env نسبت به ریشه‌ی پروژه resolve می‌شود، نه cwd —
# وگرنه اجرا از دایرکتوریِ دیگر (مثلاً worktree) پوشه را پیدا نمی‌کند.
def _resolve_reference_dir() -> Path:
    raw = os.getenv("REFERENCE_DIR")
    if not raw:
        return DESKTOP / "4D"
    p = Path(raw)
    if p.is_absolute():
        return p
    return (SYSTEM_ROOT / raw).resolve()


REFERENCE_DIR = _resolve_reference_dir()

# Key reference files inside 4D/ — these define the project's DNA
# Note: the theory file has a Persian name with a ZWNJ (\u200c); we glob for it.
def _find_theory_file():
    """Glob for the theory markdown file (Persian name with special chars)."""
    import glob
    matches = glob.glob(str(REFERENCE_DIR / "برداشت*.md"))
    return Path(matches[0]) if matches else REFERENCE_DIR / "برداشت_missing.md"


REF_FILES = {
    "verify_script":   REFERENCE_DIR / "4.py",
    "handoff":         REFERENCE_DIR / "SOG-multiagent-handoff 2.md",
    "handoff_v1":      REFERENCE_DIR / "SOG-multiagent-handoff.md",
    "theory":          _find_theory_file(),
    "docx_report":     REFERENCE_DIR / "سایه_های_ابعاد_بالاتر-در-دنیای-انسان.docx",
}

# Output / logs directory (we CAN write here)
OUTPUT_DIR = SYSTEM_ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Logging ──────────────────────────────────────────────────────────────
import logging


def setup_logging(level: int = logging.INFO) -> None:
    """پیکربندی یک‌باره‌ی logging — کنسول (پیش‌فرض) + فایل outputs/system.log.

    idempotent: چند بار صدا زدنش handler تکراری اضافه نمی‌کند.
    """
    root = logging.getLogger()
    if any(getattr(h, "_4d_system", False) for h in root.handlers):
        return
    fh = logging.FileHandler(OUTPUT_DIR / "system.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"))
    fh._4d_system = True
    root.addHandler(fh)
    if root.level > level:
        root.setLevel(level)


# ── Network timeouts (seconds) — یک منبع واحد برای همه‌ی call siteها ─────
FUGU_TIMEOUT = float(os.getenv("FUGU_TIMEOUT", "300"))   # Fugu کند است (multi-agent reasoning)
GLM_TIMEOUT  = float(os.getenv("GLM_TIMEOUT", "60"))
WEB_TIMEOUT  = float(os.getenv("WEB_TIMEOUT", "20"))


# ── API configuration ────────────────────────────────────────────────────
@dataclass
class LLMConfig:
    # default_factory تا مقدار env در لحظه‌ی ساختِ instance خوانده شود،
    # نه یک‌بار در import (وگرنه load_dotenv(override=True) بعدی بی‌اثر است)
    glm_api_key:  str = field(default_factory=lambda: os.getenv("GLM_API_KEY", ""))
    glm_base_url: str = field(default_factory=lambda: os.getenv("GLM_BASE_URL", "https://open.bigmodel.com/api/paas/v4"))
    glm_model:    str = field(default_factory=lambda: os.getenv("GLM_MODEL", "glm-4-max"))

    fugu_api_key:  str = field(default_factory=lambda: os.getenv("FUGU_API_KEY", ""))
    fugu_base_url: str = field(default_factory=lambda: os.getenv("FUGU_BASE_URL", "https://api.sakana.ai/v1"))
    fugu_model:    str = field(default_factory=lambda: os.getenv("FUGU_MODEL", "fugu-v1"))

    mock_mode: bool = field(default_factory=lambda: os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes"))

    @property
    def glm_available(self) -> bool:
        key = self.glm_api_key.strip()
        return bool(key) and not key.startswith("YOUR_") and not self.mock_mode

    @property
    def fugu_available(self) -> bool:
        key = self.fugu_api_key.strip()
        return bool(key) and not key.startswith("YOUR_") and not self.mock_mode


# ── SOG model: canonical operating point (from 4.py / ledger) ────────────
# These are the ANCHOR values that core/model.py must reproduce.
@dataclass
class OperatingPoint:
    rho:  float = 0.5
    lam:  float = 0.5
    se:   float = 0.1     # σ_ε  (measurement noise std)
    sz:   float = 0.05    # σ_ζ  (process noise std)
    sd:   float = 0.1     # σ_d  (private dither std)
    B:    float = 0.2     # bias range
    gamma: float = 1.0    # pinned

    @property
    def se2(self):  return self.se ** 2
    @property
    def sz2(self):  return self.sz ** 2
    @property
    def sd2(self):  return self.sd ** 2

    @property
    def dc_gain(self):  return self.lam * self.gamma / (1 - self.rho)

    def __repr__(self):
        return (f"OperatingPoint(ρ={self.rho}, λ={self.lam}, σ_ε={self.se}, "
                f"σ_ζ={self.sz}, σ_d={self.sd}, g={self.dc_gain:.2f})")


# Anchor values expected from 4.py (for cross-validation)
ANCHORS = {
    "P":        0.00325184,
    "S":        0.01081296,
    "P_blind":  0.01526172,
    "S_blind":  0.01381543,
    "Delta_self":  0.122520,
    "E_shadow":    0.012553,
    "I_pred":      0.0144179,
    "Var_ex":      0.217327,
    "Var_eff":     0.208232,
    "identity":    0.135073,   # ½log(σ_z²/S) = E_shadow + Δ_self
    "sigma_z2":    0.0141667,
}


def get_llm_config() -> LLMConfig:
    return LLMConfig()


def get_operating_point() -> OperatingPoint:
    return OperatingPoint()


def verify_reference_dir() -> bool:
    """Check that the golden-rule reference directory exists and is intact."""
    if not REFERENCE_DIR.exists():
        return False
    return all(p.exists() for p in [REF_FILES["verify_script"], REF_FILES["handoff"]])
