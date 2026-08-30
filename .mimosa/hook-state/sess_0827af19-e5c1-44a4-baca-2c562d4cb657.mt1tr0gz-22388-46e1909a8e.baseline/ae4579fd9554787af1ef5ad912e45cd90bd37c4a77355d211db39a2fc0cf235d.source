"""
client.py — کلاینتِ سمتِ ecology. کرنل را به‌صورت subprocessِ جدا بالا می‌آورد
و فقط از طریقِ پروتکل با آن حرف می‌زند. کلیدِ امضا را *ندارد* — فقط می‌تواند بپرسد.

ActuationGate: هر actuation را در خود می‌پیچد؛ بدون permitِ مصرف‌شده، اقدام رد می‌شود
(fail-closed). «فراموش‌کردنِ check» دیگر به اجرای آزاد منجر نمی‌شود — به رد منجر می‌شود.
"""
from __future__ import annotations
import subprocess, sys, os, json


class KernelClient:
    def __init__(self, state_dir: str, stop_path: str | None = None):
        here = os.path.dirname(os.path.abspath(__file__))
        argv = [sys.executable, os.path.join(here, "daemon.py"), state_dir]
        if stop_path:
            argv.append(stop_path)
        self.p = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1)

    def _call(self, **req) -> dict:
        self.p.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        return json.loads(line)

    # verbهای مجاز
    def audit(self, event, actor, **data): return self._call(verb="audit", event=event, actor=actor, data=data)
    def verify(self):                      return self._call(verb="verify")
    def permit(self, action, actor):       return self._call(verb="permit", action=action, actor=actor)
    def consume(self, token):              return self._call(verb="consume", token=token)
    def ground(self, claims, actor):       return self._call(verb="ground", claims=claims, actor=actor)
    def canon(self):                       return self._call(verb="canon")
    def status(self):                      return self._call(verb="status")

    def close(self):
        try:
            self.p.stdin.close(); self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


class PermitDenied(Exception):
    pass


class ActuationGate:
    """هر کنشِ بیرونی را می‌پیچد؛ بدون permitِ معتبرِ مصرف‌شده اجرا نمی‌شود."""
    def __init__(self, client: KernelClient, actor: str):
        self.k = client
        self.actor = actor

    def act(self, action: str, fn, *args, **kwargs):
        p = self.k.permit(action, self.actor)
        if not p.get("ok"):
            raise PermitDenied(f"permit رد شد: {p.get('reason')}")
        c = self.k.consume(p["token"])
        if not c.get("ok"):
            raise PermitDenied(f"consume رد شد: {c.get('reason')}")
        return fn(*args, **kwargs)
