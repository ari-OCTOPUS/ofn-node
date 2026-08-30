"""اجرای واقعی فرایندها + تزریقِ رمز به‌صورت متغیرِ محیطی.
در آزمون‌ها با نسخهٔ قلابی جایگزین می‌شود (تزریق وابستگی)."""
import os
import subprocess
from typing import Dict, List, Optional, Tuple


def _merged_env(env: Optional[Dict[str, str]]):
    if not env:
        return None
    return {**os.environ, **{k: str(v) for k, v in env.items()}}


class ProcessRunner:
    def spawn(self, cmd: List[str], cwd, env: Optional[Dict[str, str]] = None) -> int:
        popen = subprocess.Popen(cmd, cwd=str(cwd), env=_merged_env(env))
        return popen.pid

    def alive(self, pid) -> bool:
        import psutil
        if not pid or not psutil.pid_exists(int(pid)):
            return False
        try:
            p = psutil.Process(int(pid))
            return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except psutil.Error:
            return False

    def kill(self, pid) -> None:
        import psutil
        if not pid or not psutil.pid_exists(int(pid)):
            return
        try:
            p = psutil.Process(int(pid))
            for child in p.children(recursive=True):
                _terminate(child)
            _terminate(p)
        except psutil.Error:
            pass

    def run(self, cmd: List[str], cwd, timeout: int = 120,
            env: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
        try:
            r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                               timeout=timeout, env=_merged_env(env))
            out = ((r.stdout or "") + (r.stderr or "")).strip()
            return r.returncode, out[-2000:]
        except Exception as e:  # noqa: BLE001
            return 1, str(e)


def _terminate(proc) -> None:
    import psutil
    try:
        proc.terminate()
        gone, alive = psutil.wait_procs([proc], timeout=5)
        for p in alive:
            p.kill()
    except psutil.Error:
        pass
