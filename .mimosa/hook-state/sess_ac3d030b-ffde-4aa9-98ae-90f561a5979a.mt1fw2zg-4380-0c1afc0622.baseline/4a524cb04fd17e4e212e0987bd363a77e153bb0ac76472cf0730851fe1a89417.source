"""تست‌های OctopusBridge — نمای فقط-خواندنیِ governanceِ زیمان برای اختاپوس."""
from adapters.octopus_bridge import OctopusBridge, digest, status
from core.governance import propose
from core.store import Store


def test_no_db_is_failsoft_not_creating(tmp_path):
    """بدونِ دیتابیس: هیچ فایلی ساخته نمی‌شود و digest امن برمی‌گردد."""
    db = tmp_path / "data" / "state.db"
    b = OctopusBridge(state_db=db)
    assert b.store is None
    assert not db.exists()                       # side-effect صفر
    assert "Ziman" in b.telegram_digest()
    assert b.status()["shadow_on"] is True       # پیش‌فرضِ امن
    assert b.pending() == []


def test_reflects_real_pending_and_ledger(tmp_path):
    db = tmp_path / "state.db"
    store = Store(db)
    propose(store, "publish", "ziman", "hero post", "RED", "octopus")
    b = OctopusBridge(state_db=db)
    s = b.status()
    assert s["pending_proposals"] == 1
    assert s["ledger_ok"] is True
    assert s["outward_execution"] is False
    d = b.telegram_digest()
    assert "صف 1" in d and "propose-only" in d


def test_module_digest_and_status_failsoft(tmp_path):
    # مسیرِ ناموجود → None، بدونِ استثنا (پا به رفتارِ خودش برمی‌گردد)
    assert digest(state_db=tmp_path / "nope" / "x.db") is not None  # digest بدونِ store هم متن دارد
    st = status(state_db=tmp_path / "nope" / "x.db")
    assert st["source"] == "control-brain"


def test_catalog_counts_surface_when_present(tmp_path):
    from adapters.dashboard import _find_catalog
    if _find_catalog() is None:
        return
    b = OctopusBridge(state_db=tmp_path / "x.db")
    assert b.status()["catalog_total"] >= 35     # کاتالوگِ واقعیِ ۳۵‌تایی
