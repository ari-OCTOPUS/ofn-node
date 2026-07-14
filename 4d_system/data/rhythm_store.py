"""
data/rhythm_store.py — حافظه‌ی ریتم‌های خام

هر سری زمانی کشف‌شده/تولیدشده رو به‌عنوان فایل `.npy` ذخیره می‌کنه
و خلاصه‌ی آماری‌اش رو تو SQLite. این «حافظه‌ی پایه» سیستم است —
autoloop از این ریتم‌های ذخیره‌شده استفاده می‌کنه.

ساختار فایل‌ها:
    outputs/rhythms/
        ├── r0001_Damped-oscillator.npy
        ├── r0002_AR1-noise.npy
        └── ...
"""
from __future__ import annotations

import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


RHYTHM_DIR = Path(__file__).resolve().parent.parent / "outputs" / "rhythms"


@dataclass
class Rhythm:
    """یک ریتم ذخیره‌شده."""
    name: str
    series: np.ndarray
    source_type: str = "synthetic"    # synthetic/physical/real
    mi: float = 0.0
    rho_hat: float = 0.0
    detectable: bool = False
    tags: str = ""
    file_path: str = ""
    id: Optional[int] = None


def _ensure_dir():
    RHYTHM_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_db():
    from memory.store import _ensure_db
    _ensure_db()


def save_rhythm(name: str, series: np.ndarray, source_type: str = "synthetic",
                mi: float = 0.0, rho_hat: float = 0.0, detectable: bool = False,
                tags: str = "") -> Rhythm:
    """
    ذخیره‌ی یک ریتم خام.

    ۱. فایل .npy ذخیره میشه
    ۲. خلاصه در SQLite

    Returns: Rhythm object با id و file_path
    """
    _ensure_dir()
    _ensure_db()

    from memory.store import DB_PATH

    # Generate filename
    safe_name = name.replace(" ", "-").replace(":", "-")[:40]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{safe_name}_{timestamp}.npy"
    filepath = RHYTHM_DIR / filename

    # Save raw data
    np.save(str(filepath), series)

    rel_path = str(filepath.relative_to(filepath.parent.parent.parent))

    # Save summary in DB — B5: بسته‌شدنِ تضمینی + پاک‌سازیِ npy یتیم اگر INSERT شکست
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute(
            """INSERT INTO rhythms
               (timestamp, name, source_type, n_points, mean, std,
                mi, rho_hat, detectable, file_path, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), name, source_type,
             len(series), float(np.mean(series)), float(np.std(series)),
             float(mi), float(rho_hat), int(detectable), rel_path, tags)
        )
        conn.commit()
        rid = cur.lastrowid
    except Exception:
        # فایلِ .npy قبل از INSERT نوشته شده — بدونِ ردیفِ DB یتیم می‌ماند
        try:
            filepath.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    finally:
        conn.close()

    return Rhythm(
        name=name, series=series, source_type=source_type,
        mi=float(mi), rho_hat=float(rho_hat), detectable=detectable,
        tags=tags, file_path=rel_path, id=rid,
    )


def load_rhythm(rhythm_id: int) -> Optional[Rhythm]:
    """بارگذاری یک ریتم از DB + فایل."""
    _ensure_db()
    from memory.store import DB_PATH

    conn = sqlite3.connect(str(DB_PATH))
    try:
        row = conn.execute("SELECT * FROM rhythms WHERE id=?", (rhythm_id,)).fetchone()
        cols = [d[0] for d in conn.execute("SELECT * FROM rhythms LIMIT 0").description]
    finally:
        conn.close()

    if not row:
        return None

    d = dict(zip(cols, row))

    # Load the .npy file — مسیر ذخیره‌شده نسبت به ریشه‌ی پروژه است (نه Desktop)
    base_dir = Path(__file__).resolve().parent.parent
    filepath = base_dir / d["file_path"]
    if not filepath.exists():
        # fallback: شاید فقط نام فایل معتبر باشد
        fallback = RHYTHM_DIR / Path(d["file_path"]).name
        if fallback.exists():
            filepath = fallback
        else:
            return None

    series = np.load(str(filepath))

    return Rhythm(
        name=d["name"], series=series, source_type=d.get("source_type", ""),
        mi=d.get("mi", 0), rho_hat=d.get("rho_hat", 0),
        detectable=bool(d.get("detectable", 0)),
        tags=d.get("tags", ""), file_path=d["file_path"], id=d["id"],
    )


def get_rhythms(limit: int = 50, tags: str = None) -> list[dict]:
    """لیست همه‌ی ریتم‌های ذخیره‌شده (بدون داده‌ی خام)."""
    _ensure_db()
    from memory.store import DB_PATH

    conn = sqlite3.connect(str(DB_PATH))
    try:
        if tags:
            rows = conn.execute(
                "SELECT * FROM rhythms WHERE tags LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{tags}%", limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM rhythms ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM rhythms LIMIT 0").description]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def get_rhythm_count() -> int:
    """تعداد کل ریتم‌های ذخیره‌شده."""
    _ensure_db()
    from memory.store import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    try:
        return conn.execute("SELECT COUNT(*) FROM rhythms").fetchone()[0]
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════
#  ریتم‌های پایه — حافظه‌ی پیش‌فرض
# ════════════════════════════════════════════════════════════════════════

def ensure_base_rhythms(force: bool = False) -> int:
    """
    تولید و ذخیره‌ی ۶ ریتم مرجع به‌عنوان حافظه‌ی پایه.
    اگه از قبل وجود دارن و force=False نیست، چیزی اضافه نمی‌کنه.

    Returns: تعداد ریتم‌های جدید.
    """
    if get_rhythm_count() > 0 and not force:
        return 0

    from data.synthetic import ar1_plus_noise, gaussian_iid, logistic_map
    from data.physical import brownian_motion, harmonic_oscillator, lorenz_system
    from core.metrics import empirical_shadow, fit_shadow_parameters

    base_rhythms = [
        ("Brownian motion", lambda: brownian_motion(5000), "physical"),
        ("Damped oscillator", lambda: harmonic_oscillator(5000), "physical"),
        ("Lorenz (chaos)", lambda: lorenz_system(5000), "physical"),
        ("AR(1)+noise (SOG analog)", lambda: ar1_plus_noise(5000, rho=0.7), "synthetic"),
        ("Gaussian iid (NULL model)", lambda: gaussian_iid(5000), "synthetic"),
        ("Logistic map (chaos)", lambda: logistic_map(5000), "synthetic"),
    ]

    added = 0
    for name, gen_fn, src_type in base_rhythms:
        try:
            series = gen_fn()

            # Analyze
            shadow = empirical_shadow(series)
            fit = fit_shadow_parameters(series)

            save_rhythm(
                name=name,
                series=series,
                source_type=src_type,
                mi=float(shadow["temporal_mi"]),
                rho_hat=float(fit["rho_hat"]),
                detectable=bool(fit.get("detectable", False)),
                tags=f"base,{src_type}",
            )
            added += 1
        except Exception as e:
            print(f"[rhythm_store] error saving '{name}': {e}")

    return added


# ════════════════════════════════════════════════════════════════════════
#  Test
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== Rhythm Store Test ===\n")

    # Create base rhythms
    n = ensure_base_rhythms()
    print(f"Created {n} base rhythms")

    total = get_rhythm_count()
    print(f"Total rhythms in DB: {total}")

    # List
    rhythms = get_rhythms()
    for r in rhythms:
        print(f"  #{r['id']} | {r['name']:30s} | MI={r['mi']:.4f} | "
              f"det={bool(r['detectable'])} | {r['n_points']} pts | {r['file_path']}")

    # Load one
    if rhythms:
        loaded = load_rhythm(rhythms[0]["id"])
        if loaded:
            print(f"\nLoaded #{loaded.id}: {loaded.name}")
            print(f"  shape: {loaded.series.shape}")
            print(f"  mean: {np.mean(loaded.series):.4f}")
