from core.store import Store
from core.safety import SafetyGate


def test_halt_and_resume(tmp_path):
    store = Store(tmp_path / "s.db")
    gate = SafetyGate(store, tmp_path / "STOP")
    assert gate.is_halted() is False
    gate.halt("چون")
    assert gate.is_halted() is True
    assert (tmp_path / "STOP").exists()
    gate.resume()
    assert gate.is_halted() is False
    assert not (tmp_path / "STOP").exists()
