"""آزمونِ واقعی — یک فرایند پایتونِ واقعی روشن و خاموش می‌شود (بدون قلابی)."""
import sys
import time
from core.runner import ProcessRunner


def test_real_process_lifecycle(tmp_path):
    r = ProcessRunner()
    pid = r.spawn([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path)
    time.sleep(1.0)
    assert r.alive(pid) is True
    r.kill(pid)
    time.sleep(1.0)
    assert r.alive(pid) is False
