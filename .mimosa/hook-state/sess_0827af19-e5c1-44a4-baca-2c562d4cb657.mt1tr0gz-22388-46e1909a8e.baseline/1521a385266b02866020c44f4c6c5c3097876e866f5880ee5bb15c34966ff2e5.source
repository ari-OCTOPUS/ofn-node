"""runnerِ قلابی برای آزمون‌های منطقی — بدون اجرای هیچ فرایند واقعی.
last_env را نگه می‌دارد تا تزریقِ رمز را بشود تست کرد."""
class FakeRunner:
    def __init__(self):
        self.alive_pids = set()
        self._next = 1000
        self.run_result = (0, "ok")
        self.last_env = None
    def spawn(self, cmd, cwd, env=None):
        self.last_env = env
        self._next += 1
        self.alive_pids.add(self._next)
        return self._next
    def alive(self, pid):
        return pid in self.alive_pids
    def kill(self, pid):
        self.alive_pids.discard(pid)
    def run(self, cmd, cwd, timeout=120, env=None):
        self.last_env = env
        return self.run_result
