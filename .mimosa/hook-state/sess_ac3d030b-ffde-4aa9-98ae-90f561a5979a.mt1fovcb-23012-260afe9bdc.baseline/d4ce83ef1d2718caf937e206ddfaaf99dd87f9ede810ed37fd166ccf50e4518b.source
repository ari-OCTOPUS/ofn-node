# tests/test_experiment_accounting.py — تستِ بازطراحیِ P3 (at-discovery accounting، §۶)
#
# اجرا:  py -m pytest _ops/hypothesis_engine/tests/test_experiment_accounting.py -q
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments"))
from deceptive_grid import falsified_assists_at  # noqa: E402


def test_falsified_assists_sums_only_falsified():
    hyps = [
        {"tested_steps": 10, "falsified": True},
        {"tested_steps": 5, "falsified": False},   # نادیده
        {"tested_steps": 7, "falsified": True},
        {"tested_steps": 0, "falsified": True},     # صفر
    ]
    assert falsified_assists_at(hyps) == 17


def test_falsified_assists_empty_and_missing_keys_safe():
    assert falsified_assists_at([]) == 0
    # نبودِ کلید نباید بشکنه
    assert falsified_assists_at([{}, {"falsified": True}]) == 0


def test_at_discovery_not_end_of_run():
    """حیاتی: اگر فرضیه‌ای بعد از کشف falsified شود، نباید به P3ِ آن run اضافه شود.
    معیارِ درست فقط وضعیتِ لحظهٔ کشف را می‌بیند، نه پایانِ run را."""
    at_discovery = [{"tested_steps": 4, "falsified": False}]   # هنوز falsified نیست
    later = [{"tested_steps": 9, "falsified": True}]           # بعداً falsified شد
    assert falsified_assists_at(at_discovery) == 0             # در لحظهٔ کشف: صفر
    assert falsified_assists_at(later) == 9                    # در پایانِ run: ۹
