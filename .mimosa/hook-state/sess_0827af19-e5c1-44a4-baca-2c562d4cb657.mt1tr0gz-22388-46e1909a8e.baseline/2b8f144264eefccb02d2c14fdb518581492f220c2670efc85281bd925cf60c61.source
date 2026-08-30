"""لایهٔ احراز هویت و مجوز (RBAC) — فاز ۱ چند-کاربره.

طراحی: تنها منبعِ حقیقتِ «چه کسی چه‌کاری می‌تواند بکند». مستقل از تلگرام/وب و کاملاً تست‌پذیر.
behavior-preserving: اگر مدیر (ProjectManager) بدونِ authz/actor صدا زده شود، هیچ محدودیتی اعمال نمی‌شود
(رفتارِ تک‌کاربرهٔ فعلی). به‌محضِ دادنِ authz + actor، مجوزها enforce می‌شوند.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# اکشن‌های فقط-ادمین
ADMIN_ONLY = {"adduser", "secrets", "halt", "resume", "rotate"}
# اکشن‌هایی که operator روی پروژه‌های خودش می‌تواند
OPERATOR_ACTIONS = {"start", "stop", "test", "status"}


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


@dataclass
class User:
    id: str
    name: str
    role: Role = Role.VIEWER
    telegram_chat_id: int = 0
    enabled: bool = True
    # نقشِ حاکمیتِ زیمان (owner=SahebZiman | admin | viewer). خالی = مشتق از role.
    ziman_role: str = ""


# نگاشتِ نقشِ control-plane → نقشِ حاکمیتِ زیمان وقتی ziman_role صریح نیست.
# fail-closed: فقط ادمینِ کنترل به owner می‌رسد؛ بقیه viewer (بدونِ اختیارِ approve).
_CONTROL_TO_ZIMAN = {
    Role.ADMIN: "owner",       # آری = SahebZiman (تنها تأییدکنندهٔ RED)
    Role.OPERATOR: "viewer",   # اپراتورِ کنترل ≠ تأییدکنندهٔ زیمان (محافظه‌کار)
    Role.VIEWER: "viewer",
}
_VALID_ZIMAN_ROLES = {"owner", "admin", "viewer", "agent"}


class Authz:
    def __init__(self, users: Optional[List[User]] = None):
        self._by_id: Dict[str, User] = {}
        for u in users or []:
            self._by_id[u.id] = u

    # ---- بارگذاری ----
    @classmethod
    def from_yaml(cls, path) -> "Authz":
        import yaml
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        users = []
        for u in raw.get("users", []) or []:
            users.append(User(
                id=str(u["id"]),
                name=u.get("name", u["id"]),
                role=Role(str(u.get("role", "viewer"))),
                telegram_chat_id=int(u.get("telegram_chat_id", 0) or 0),
                enabled=bool(u.get("enabled", True)),
                ziman_role=str(u.get("ziman_role", "") or "").strip().lower(),
            ))
        return cls(users)

    @classmethod
    def seeded_admin(cls, chat_id: int = 0, name: str = "admin") -> "Authz":
        return cls([User("admin", name, Role.ADMIN, int(chat_id or 0), True)])

    # ---- جستجو ----
    def all_users(self) -> List[User]:
        return list(self._by_id.values())

    def user(self, uid: str) -> Optional[User]:
        return self._by_id.get(uid)

    def user_by_chat(self, chat_id: int) -> Optional[User]:
        for u in self._by_id.values():
            if u.telegram_chat_id and u.telegram_chat_id == int(chat_id):
                return u
        return None

    def admin(self) -> Optional[User]:
        for u in self._by_id.values():
            if u.role == Role.ADMIN:
                return u
        return None

    # ---- پلِ نقشِ حاکمیتِ زیمان (G9) ----
    def ziman_role_of(self, user: Optional[User]) -> str:
        """نقشِ حاکمیتِ زیمان برای یک کاربر. fail-closed → viewer."""
        if user is None or not user.enabled:
            return "viewer"
        explicit = (user.ziman_role or "").strip().lower()
        if explicit in _VALID_ZIMAN_ROLES:
            return explicit
        return _CONTROL_TO_ZIMAN.get(user.role, "viewer")

    def ziman_role_for_chat(self, chat_id: int) -> str:
        """از chat_idِ تلگرام به نقشِ حاکمیتِ زیمان. ناشناخته → viewer (fail-closed)."""
        return self.ziman_role_of(self.user_by_chat(chat_id))

    # ---- تصمیمِ مجوز ----
    @staticmethod
    def _owns(actor: User, project) -> bool:
        owner = getattr(project, "owner", "") or ""
        allowed = getattr(project, "allowed", []) or []
        return owner == actor.id or actor.id in allowed

    def can(self, actor: Optional[User], action: str, project=None) -> bool:
        if actor is None or not actor.enabled:
            return False
        if actor.role == Role.ADMIN:
            return True
        if action in ADMIN_ONLY:
            return False
        if actor.role == Role.VIEWER:
            return action == "status"
        if actor.role == Role.OPERATOR:
            if action not in OPERATOR_ACTIONS:
                return False
            if project is None:
                return action == "status"
            return self._owns(actor, project)
        return False

    def visible_projects(self, actor: Optional[User], projects: List) -> List:
        if actor is None or not actor.enabled:
            return []
        if actor.role in (Role.ADMIN, Role.VIEWER):
            return list(projects)
        return [p for p in projects if self._owns(actor, p)]
