"""تست‌های پلِ RBAC حاکمیتِ زیمان (G9) — نگاشتِ نقش، fail-closed، chat_id."""
from core.authz import Authz, Role, User


def test_control_admin_maps_to_owner():
    az = Authz([User("admin", "آری", Role.ADMIN, telegram_chat_id=111)])
    assert az.ziman_role_for_chat(111) == "owner"       # SahebZiman


def test_operator_and_viewer_map_to_viewer_failclosed():
    az = Authz([
        User("op", "اپراتور", Role.OPERATOR, telegram_chat_id=222),
        User("vw", "بیننده", Role.VIEWER, telegram_chat_id=333),
    ])
    assert az.ziman_role_for_chat(222) == "viewer"      # اپراتورِ کنترل ≠ تأییدکننده
    assert az.ziman_role_for_chat(333) == "viewer"


def test_explicit_ziman_role_wins():
    az = Authz([User("h", "کمک‌کار", Role.OPERATOR, telegram_chat_id=444,
                     ziman_role="admin")])
    assert az.ziman_role_for_chat(444) == "admin"


def test_unknown_chat_is_viewer():
    az = Authz([User("admin", "آری", Role.ADMIN, telegram_chat_id=111)])
    assert az.ziman_role_for_chat(999999) == "viewer"   # fail-closed


def test_disabled_user_is_viewer():
    az = Authz([User("admin", "آری", Role.ADMIN, telegram_chat_id=111,
                     enabled=False)])
    assert az.ziman_role_for_chat(111) == "viewer"


def test_invalid_explicit_role_falls_back_to_mapping():
    az = Authz([User("admin", "آری", Role.ADMIN, telegram_chat_id=111,
                     ziman_role="superking")])
    assert az.ziman_role_for_chat(111) == "owner"       # نامعتبر → مشتق از role


def test_from_yaml_reads_ziman_role(tmp_path):
    p = tmp_path / "users.yaml"
    p.write_text(
        "users:\n"
        "  - id: admin\n    name: آری\n    role: admin\n"
        "    ziman_role: owner\n    telegram_chat_id: 55\n    enabled: true\n",
        encoding="utf-8")
    az = Authz.from_yaml(p)
    assert az.ziman_role_for_chat(55) == "owner"
