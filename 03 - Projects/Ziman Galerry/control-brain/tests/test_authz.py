"""آزمون‌های authz و enforcement در مدیر (بدونِ فرایندِ واقعی)."""
from pathlib import Path

from core.authz import Authz, Role, User
from core.manager import ProjectManager
from core.models import Project


def _proj(pid, owner="", allowed=None, enabled=True):
    return Project(id=pid, name=pid, workdir=".", start=["echo", "x"],
                   enabled=enabled, owner=owner, allowed=allowed or [])


def test_admin_can_everything():
    az = Authz.seeded_admin(123, "admin"); adm = az.admin()
    assert az.can(adm, "start", _proj("x"))
    assert az.can(adm, "halt")
    assert az.can(adm, "status", _proj("x"))


def test_operator_only_own_projects():
    az = Authz([User("op", "Op", Role.OPERATOR, 0, True)]); op = az.user("op")
    assert az.can(op, "start", _proj("m", owner="op"))
    assert not az.can(op, "start", _proj("o", owner="admin"))
    assert not az.can(op, "halt")
    assert not az.can(op, "status", _proj("o", owner="admin"))


def test_viewer_read_only():
    az = Authz([User("v", "V", Role.VIEWER, 0, True)]); v = az.user("v")
    assert az.can(v, "status", _proj("x"))
    assert not az.can(v, "start", _proj("x"))


def test_disabled_user_denied():
    az = Authz([User("op", "Op", Role.OPERATOR, 0, False)])
    assert not az.can(az.user("op"), "status", _proj("x"))


def test_user_by_chat():
    az = Authz([User("op", "Op", Role.OPERATOR, 555, True)])
    assert az.user_by_chat(555).id == "op"
    assert az.user_by_chat(999) is None


def test_visible_projects():
    az = Authz([User("op", "Op", Role.OPERATOR, 0, True), User("v", "V", Role.VIEWER, 0, True)])
    ps = [_proj("a", owner="op"), _proj("b", owner="admin"), _proj("c")]
    assert [p.id for p in az.visible_projects(az.user("op"), ps)] == ["a"]
    assert [p.id for p in az.visible_projects(az.user("v"), ps)] == ["a", "b", "c"]


# --- enforcement در مدیر ---
class _Store:
    def __init__(self): self.p = {}; self.f = {}
    def get_pid(self, i): return self.p.get(i)
    def set_pid(self, i, v): self.p[i] = v
    def clear_pid(self, i): self.p.pop(i, None)
    def get_flag(self, k, d=None): return self.f.get(k, d)
    def set_flag(self, k, v): self.f[k] = v
    def log(self, *a, **k): pass


class _Safety:
    def is_halted(self): return False


class _Runner:
    def __init__(self): self.spawned = False; self._n = 100
    def spawn(self, cmd, cwd, env=None): self.spawned = True; self._n += 1; return self._n
    def alive(self, pid): return False
    def kill(self, pid): pass
    def run(self, cmd, cwd, timeout=120, env=None): return 0, "ok"


class _Reg:
    def __init__(self, projs): self._d = {p.id: p for p in projs}; self.base = Path(".").resolve()
    def all(self): return list(self._d.values())
    def get(self, i): return self._d.get(i)


def test_manager_denies_operator_on_others_project():
    az = Authz([User("op", "Op", Role.OPERATOR, 0, True)]); op = az.user("op")
    r = _Runner()
    mgr = ProjectManager(_Reg([_proj("o", owner="admin")]), _Store(), _Safety(), r, authz=az)
    st = mgr.start("o", actor=op)
    assert "دسترسی" in st.detail and r.spawned is False


def test_manager_backward_compatible_without_actor():
    r = _Runner()
    mgr = ProjectManager(_Reg([_proj("x")]), _Store(), _Safety(), r)  # authz=None
    mgr.start("x")
    assert r.spawned is True
