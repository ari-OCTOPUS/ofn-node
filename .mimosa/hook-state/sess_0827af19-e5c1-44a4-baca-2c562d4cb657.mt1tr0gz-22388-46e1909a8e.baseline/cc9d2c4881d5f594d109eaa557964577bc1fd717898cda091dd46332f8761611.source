"""تست‌های داشبورد (G10) — امن‌سازیِ HTML و پنل‌های حاکمیت، بدونِ کرش."""
import json

from adapters.dashboard import _catalog_counts, _esc, _render, _find_catalog
from core.governance import decide, propose
from core.models import ProjectStatus, State
from core.store import Store


class _Manager:
    def __init__(self, statuses):
        self._s = statuses

    def status_all(self):
        return self._s


class _Safety:
    def is_halted(self):
        return False


def test_esc_neutralizes_html():
    assert _esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert "&quot;" in _esc('a "b"')


def test_render_escapes_project_name():
    mgr = _Manager([ProjectStatus(
        id="x", name="<img src=x onerror=alert(1)>", enabled=True,
        state=State.RUNNING, pid=5, healthy=True)])
    html = _render(mgr, _Safety())
    assert "<img src=x" not in html                 # نامِ خام نباید تزریق شود
    assert "&lt;img src=x" in html


def test_render_without_store_is_fine():
    mgr = _Manager([])
    html = _render(mgr, _Safety())
    assert "مغز کنترل" in html


def test_governance_panel_shows_pending_and_escapes(tmp_path):
    store = Store(tmp_path / "d.db")
    propose(store, "publish", "ziman", "<b>evil</b> detail", "RED", "octopus")
    mgr = _Manager([])
    html = _render(mgr, _Safety(), store=store)
    assert "حاکمیت" in html
    assert "ZIM-DEC-" in html                        # refِ رزروشدهٔ RED
    assert "<b>evil</b>" not in html                 # شرح باید escape شود
    assert "&lt;b&gt;evil" in html
    assert "SHADOW" in html                          # پیش‌فرض روشن


def test_catalog_counts_reads_real_file():
    path = _find_catalog()
    if path is None:
        return                                       # در چک‌اوتِ دیگر رد شود
    counts = _catalog_counts(path)
    assert counts["total"] >= 35
    assert counts["by_family"].get("F1") == 18


def test_decisions_panel_escapes_actor_and_detail(tmp_path):
    """رگرسیونِ یافتهٔ #6: ردیفِ تصمیمِ واقعی هم باید escape شود."""
    store = Store(tmp_path / "d.db")
    p = propose(store, "publish", "ziman", "<i>evil detail</i>", "RED", "octopus")
    decide(store, p["proposal_id"], "approve", "<b>attacker</b>", "owner")
    html = _render(_Manager([]), _Safety(), store=store)
    assert "<b>attacker</b>" not in html and "&lt;b&gt;attacker" in html
    assert "<i>evil detail</i>" not in html


def test_catalog_section_escapes_family_key(tmp_path):
    """رگرسیونِ یافتهٔ #6: کلیدِ خانوادهٔ آلوده در بخشِ کاتالوگ باید escape شود."""
    cat = tmp_path / "ziman-catalog.json"
    cat.write_text(json.dumps({"products": [
        {"product_id": "X", "family": "<script>alert(1)</script>"}]}),
        encoding="utf-8")
    html = _render(_Manager([]), _Safety(), catalog_path=cat)
    assert "<script>alert(1)" not in html
    assert "&lt;script&gt;" in html
