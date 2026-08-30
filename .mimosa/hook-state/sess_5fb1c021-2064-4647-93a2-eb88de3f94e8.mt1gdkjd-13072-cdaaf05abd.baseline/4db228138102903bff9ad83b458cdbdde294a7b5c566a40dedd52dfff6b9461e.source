"""octopus_bridge.py — پلِ Ziman control-brain ↔ اُرگانیسمِ اختاپوس (coupled-not-merged).

قراردادِ ADR-001: نه ادغام، نه دفترِ موازی. این پل governanceِ غنیِ control-brain
(کاتالوگِ ۳۵‌تاییِ F1–F4، صفِ propose→decide، دفترِ evt.v1، حالتِ shadow) را به‌شکلِ
یک digest/status عرضه می‌کند که `_ops/legs/ziman_leg.py` و gatewayِ مرکزیِ تلگرام
(approval_channel) از همان seamِ موجود مصرف می‌کنند — تا پای زیمان مغزِ واقعی پیدا کند.

از دیدِ اختاپوس کاملاً **فقط-خواندنی**: هیچ اجرا/ارسال/انتشار/خرج. اگر دیتابیسِ
control-brain هنوز ساخته نشده، هیچ فایلی نمی‌سازد (side-effect صفر). fail-soft:
هر خطا → None/خالی تا پا به رفتارِ فعلیِ خودش برگردد (بدونِ regression).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()


def _cb_root() -> Path:
    """ریشهٔ control-brain (پوشهٔ والدِ adapters/)."""
    return _HERE.parent.parent


def _state_db() -> Path:
    """همان مسیرِ دیتابیسی که app.py استفاده می‌کند تا حالتِ واقعی خوانده شود."""
    state = Path(os.environ.get("CONTROL_STATE_DIR") or _cb_root())
    return state / "data" / "state.db"


class OctopusBridge:
    """نمای فقط-خواندنیِ governanceِ زیمان برای اُرگانیسم/تلگرامِ مرکزی."""

    def __init__(self, state_db: Optional[Path] = None,
                 catalog_path: Optional[Path] = None):
        self.db_path = Path(state_db) if state_db else _state_db()
        # import‌های محلی تا نبودشان کلِ پا را نشکند (پا خودش سطحِ کنترل ندارد).
        from adapters.dashboard import _catalog_counts, _find_catalog
        self._catalog_counts = _catalog_counts
        self.catalog_path = Path(catalog_path) if catalog_path else _find_catalog()
        # فقط اگر دیتابیس هست بازش کن — هرگز نساز (خواندنِ اُرگانیسم side-effect ندارد).
        self.store = None
        if self.db_path.exists():
            try:
                from core.store import Store
                self.store = Store(self.db_path)
            except Exception:  # noqa: BLE001 — بدونِ store هم digest کار می‌کند
                self.store = None

    # ── داده‌های خام ─────────────────────────────────────────────────────────
    def _catalog(self) -> dict:
        try:
            return self._catalog_counts(self.catalog_path) or {}
        except Exception:  # noqa: BLE001
            return {}

    def status(self) -> dict:
        """وضعیتِ ساختاریافته برای heartbeatِ اُرگانیسم."""
        cat = self._catalog()
        out = {
            "source": "control-brain",
            "catalog_total": cat.get("total", 0),
            "by_family": cat.get("by_family", {}),
            "pending_proposals": 0,
            "decisions": 0,
            "ledger_ok": None,
            "shadow_on": True,           # پیش‌فرضِ امن اگر state نباشد
            "priced": 0,                 # propose-only تا ZIM-V5
            "outward_execution": False,
            "propose_only": True,
        }
        if self.store is not None:
            try:
                from core.governance import pending_summary
                props = self.store.list_proposals()
                out["pending_proposals"] = sum(1 for p in props if p.get("status") == "pending")
                out["decisions"] = sum(1 for p in props if p.get("status") != "pending")
                out["ledger_ok"] = self.store.verify_ledger().get("ok")
                out["shadow_on"] = self.store.get_flag("ziman_shadow", "on") != "off"
                out["_pending"] = pending_summary(self.store)
            except Exception:  # noqa: BLE001 — fail-soft
                pass
        return out

    def pending(self) -> list:
        if self.store is None:
            return []
        try:
            from core.governance import pending_summary
            return pending_summary(self.store)
        except Exception:  # noqa: BLE001
            return []

    def telegram_digest(self) -> str:
        """دایجستِ ۳-۴ خطیِ ADHD-first برای تلگرامِ مرکزی — غنی‌شده با governanceِ واقعی."""
        s = self.status()
        fam = s.get("by_family") or {}
        fam_s = " ".join(f"{k}={v}" for k, v in sorted(fam.items())) or "—"
        shadow_s = "🕶 shadow" if s.get("shadow_on") else "🔓 live-armed"
        led = s.get("ledger_ok")
        led_s = "دفتر✅" if led else ("دفتر⛔" if led is False else "دفتر—")
        return (
            f"🖼 Ziman (control-brain) · {shadow_s}\n"
            f"کاتالوگ {s.get('catalog_total', 0)} ({fam_s}) · قیمت‌گذاری‌شده={s.get('priced', 0)}\n"
            f"صف {s.get('pending_proposals', 0)} در انتظار · تصمیم‌ها {s.get('decisions', 0)} · {led_s}\n"
            "propose-only · صفر اجرا/ارسال/خرج"
        )


# ── توابعِ راحتیِ ماژول (fail-soft؛ پا این‌ها را صدا می‌زند) ─────────────────────

def digest(state_db=None, catalog_path=None) -> Optional[str]:
    """دایجستِ غنی یا None اگر چیزی در دسترس نبود (پا به رفتارِ خودش برمی‌گردد)."""
    try:
        return OctopusBridge(state_db=state_db, catalog_path=catalog_path).telegram_digest()
    except Exception:  # noqa: BLE001
        return None


def status(state_db=None, catalog_path=None) -> Optional[dict]:
    try:
        return OctopusBridge(state_db=state_db, catalog_path=catalog_path).status()
    except Exception:  # noqa: BLE001
        return None
