"""
fleet/models.py — shared data models for fleet manager ↔ worker communication
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
import time


# ── Hardware roles ────────────────────────────────────────────────────────────
ROLE_WORKER  = "WORKER"    # OPi5 Pro — mines coins
ROLE_SENSOR  = "SENSOR"    # ESP32    — temp/power monitoring only
ROLE_WATCHDOG= "WATCHDOG"  # RPi3B    — health monitor
ROLE_MAIN    = "MAIN"      # OPi5+    — brain (manager itself)

# ── Per-algo realistic ARM hashrate estimates (H/s per OPi5 Pro = RK3588S) ──
# Benchmarked from community data: reddit/bitcointalk/xmrig issues, 2024-2025
ARM_HASHRATE_HS: dict[str, float] = {
    "yespower":    1500.0,   # Sugarchain, Myriad — best ARM algo
    "yespowerr16": 1400.0,   # C64 Chain variant
    "gr":           450.0,   # Ghostrider — CPU-friendly, moderate ARM
    "minotaur":     800.0,   # CPU-friendly hybrid
    "argon2d":      600.0,   # memory-hard, CPU-friendly
    "cryptonight":  300.0,   # classic; decent on A76
    "rx/c64":       120.0,   # RandomX/C64 — ARM weak vs x86
    "randomx":      110.0,   # Monero — ARM ~100-150 H/s vs Ryzen ~15,000
    "kawpow":       200.0,   # GPU algo; ARM placeholder (not viable at scale)
    "octopus":      150.0,   # Conflux GPU algo; ARM not viable
    "scrypt":       800.0,   # Litecoin/Doge — ARM viable at small scale
}

# OPi5+ main board: A76 cores are slightly faster (fewer but higher-clocked)
OPI5PLUS_MULTIPLIER = 1.2   # ~20% faster than OPi5 Pro per core

WORKER_COUNT   = 9          # 9× OPi5 Pro
MAIN_HASHRATE_SHARE = False # Main board does NOT mine (brain role)


def fleet_hashrate_for_algo(algo: str) -> float:
    """
    Total fleet hashrate for a given algo across all worker nodes.
    Uses conservative estimates — multiply by 0.85 for real-world overhead.
    """
    base = ARM_HASHRATE_HS.get(algo.lower(), 0.0)
    total = base * WORKER_COUNT * 0.85   # 15% overhead for OS/thermals
    return round(total, 1)


@dataclass
class MiningTarget:
    """What each worker should mine."""
    symbol:      str
    algo:        str
    pool_url:    str
    pool_port:   int
    wallet_addr: str
    coin_name:   str = ""
    issued_at:   float = field(default_factory=time.time)
    source:      str = "coordinator"   # "coordinator" | "manual"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MiningTarget":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class WorkerStatus:
    """Heartbeat from a worker node."""
    worker_id:      str          # e.g. "w01"
    ip:             str
    role:           str = ROLE_WORKER
    algo:           str = ""
    symbol:         str = ""
    hashrate_hs:    float = 0.0
    cpu_temp_c:     float = 0.0
    cpu_load_pct:   float = 0.0
    ram_used_pct:   float = 0.0
    uptime_s:       float = 0.0
    miner_running:  bool = False
    last_seen:      float = field(default_factory=time.time)
    error:          Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "WorkerStatus":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @property
    def is_alive(self) -> bool:
        return (time.time() - self.last_seen) < 120   # 2-minute timeout


@dataclass
class FleetStats:
    """Aggregated fleet summary — logged every cycle."""
    total_workers:        int = 0
    alive_workers:        int = 0
    mining_workers:       int = 0
    total_hashrate_hs:    float = 0.0
    avg_cpu_temp_c:       float = 0.0
    avg_cpu_load_pct:     float = 0.0
    current_target:       Optional[str] = None   # symbol being mined
    current_algo:         Optional[str] = None
    timestamp:            float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)
