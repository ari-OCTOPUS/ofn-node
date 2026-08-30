"""مدیرِ پروژه‌ها — مغزِ واقعی. بدونِ وابستگی به تلگرام یا وب، پس قابل‌تست.
هنگام روشن‌کردن، رمزهای لازمِ هر پروژه را به‌صورت متغیرِ محیطی تزریق می‌کند.
مجوزها (RBAC) اختیاری‌اند: بدونِ authz/actor، رفتار دقیقاً مثلِ تک‌کاربرهٔ قبلی است."""
from pathlib import Path
from typing import List, Tuple

from .models import Project, ProjectStatus, State


class ProjectManager:
    def __init__(self, registry, store, safety, runner, secrets=None, authz=None):
        self.registry = registry
        self.store = store
        self.safety = safety
        self.runner = runner
        self.secrets = secrets      # None یا شیئی با env_for(project)
        self.authz = authz          # None یا شیئی با can(actor, action, project)

    def _workdir(self, p: Project) -> Path:
        w = Path(p.workdir)
        return w if w.is_absolute() else (self.registry.base / w).resolve()

    def _env(self, p: Project):
        return self.secrets.env_for(p) if self.secrets else {}

    def _st(self, p, state=State.STOPPED, pid=None, healthy=None, detail=""):
        return ProjectStatus(p.id, p.name, p.enabled, state, pid, healthy, detail)

    def _authorize(self, action, actor, project) -> bool:
        if self.authz is None or actor is None:
            return True             # سازگارِ عقب‌رو: تک‌کاربره
        return self.authz.can(actor, action, project)

    @staticmethod
    def _actor_id(actor) -> str:
        return actor.id if actor is not None else "-"

    def status(self, pid: str, actor=None) -> ProjectStatus:
        p = self.registry.get(pid)
        if not p:
            return ProjectStatus(pid, pid, False, State.UNKNOWN, detail="پروژه پیدا نشد")
        if not self._authorize("status", actor, p):
            return self._st(p, detail="⛔ دسترسی رد شد")
        stored = self.store.get_pid(p.id)
        if stored and self.runner.alive(stored):
            state, pidnum = State.RUNNING, stored
        else:
            state, pidnum = State.STOPPED, None
            if stored:
                self.store.clear_pid(p.id)
        healthy = None
        if state == State.RUNNING and p.health:
            code, _ = self.runner.run(p.health, self._workdir(p), timeout=20, env=self._env(p))
            healthy = code == 0
        return self._st(p, state, pidnum, healthy)

    def status_all(self, actor=None) -> List[ProjectStatus]:
        projects = self.registry.all()
        if self.authz is not None and actor is not None:
            projects = self.authz.visible_projects(actor, projects)
        return [self.status(p.id, actor) for p in projects]

    def start(self, pid: str, actor=None) -> ProjectStatus:
        p = self.registry.get(pid)
        if not p:
            return ProjectStatus(pid, pid, False, State.UNKNOWN, detail="پروژه پیدا نشد")
        if not self._authorize("start", actor, p):
            return self._st(p, detail="⛔ دسترسی رد شد")
        if self.safety.is_halted():
            return self._st(p, detail="⛔ قفل ایمنی روشن است؛ اول resume کن")
        if not p.enabled:
            return self._st(p, detail="این پروژه غیرفعال است (تا تعویض رمزها)")
        cur = self.status(p.id, actor)
        if cur.state == State.RUNNING:
            return self._st(p, State.RUNNING, cur.pid, detail="از قبل روشن بود")
        wd = self._workdir(p)
        if not wd.exists():
            return self._st(p, detail=f"پوشه پیدا نشد: {wd}")
        env = self._env(p)
        newpid = self.runner.spawn(p.start, wd, env=env or None)
        self.store.set_pid(p.id, newpid)
        self.store.log("start", p.id, f"pid={newpid} secrets={len(env)}", actor=self._actor_id(actor))
        return self._st(p, State.RUNNING, newpid, detail="روشن شد")

    def stop(self, pid: str, actor=None) -> ProjectStatus:
        p = self.registry.get(pid)
        if not p:
            return ProjectStatus(pid, pid, False, State.UNKNOWN, detail="پروژه پیدا نشد")
        if not self._authorize("stop", actor, p):
            return self._st(p, detail="⛔ دسترسی رد شد")
        stored = self.store.get_pid(p.id)
        if stored and self.runner.alive(stored):
            self.runner.kill(stored)
        self.store.clear_pid(p.id)
        self.store.log("stop", p.id, "", actor=self._actor_id(actor))
        return self._st(p, State.STOPPED, detail="خاموش شد")

    def test(self, pid: str, actor=None) -> Tuple[bool, str]:
        p = self.registry.get(pid)
        if not p:
            return False, "پروژه پیدا نشد"
        if not self._authorize("test", actor, p):
            return False, "⛔ دسترسی رد شد"
        if not p.test:
            return False, "این پروژه دستور تست ندارد"
        code, out = self.runner.run(p.test, self._workdir(p), timeout=300, env=self._env(p) or None)
        self.store.log("test", p.id, f"code={code}", actor=self._actor_id(actor))
        return code == 0, out or "(بدون خروجی)"
