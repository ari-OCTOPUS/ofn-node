"""تست چک‌لیست #۲/#۶ (HITL) و #۳ (audit) و #۴ (least-privilege)."""
import pytest
from src.hitl import HITLGate
from src.tools import ToolGateway, ToolPermissionError
from src.tracing import AuditLog


def test_hitl_reject_blocks():
    gate = HITLGate(approver=lambda a, c: False)   # انسان «نه» می‌گوید
    assert gate.requires_approval("finalize") is True
    assert gate.request("finalize", {"x": 1}) is False


def test_hitl_approve_passes():
    gate = HITLGate(approver=lambda a, c: True)
    assert gate.request("finalize", {"x": 1}) is True


def test_least_privilege_denies_unscoped_tool():
    gw = ToolGateway()
    # analyst اجازه‌ی web_search_mock ندارد
    with pytest.raises(ToolPermissionError):
        gw.call("analyst", "web_search_mock", query="x")


def test_researcher_allowed_tool():
    gw = ToolGateway()
    out = gw.call("researcher", "web_search_mock", query="x")
    assert "نمونه" in out


def test_audit_chain_integrity(tmp_path):
    log = AuditLog(path=str(tmp_path / "audit.jsonl"))
    log.log("a", "x", v=1)
    log.log("b", "y", v=2)
    assert log.verify_chain() is True
    # دستکاری دستی یک خط → زنجیره باید بشکند
    p = tmp_path / "audit.jsonl"
    lines = p.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace('"v": 1', '"v": 999')
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert AuditLog(path=str(p)).verify_chain() is False
