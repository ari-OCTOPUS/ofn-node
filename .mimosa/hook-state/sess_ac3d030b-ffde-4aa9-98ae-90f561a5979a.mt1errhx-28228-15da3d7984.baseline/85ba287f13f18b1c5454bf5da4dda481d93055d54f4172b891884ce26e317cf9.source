"""تست‌های command_registry — طبقه‌بندیِ ریسک، aliasها، و fail-closedِ ناشناخته."""
from core.command_registry import CommandRegistry, find_registry


def _reg():
    # از فایلِ واقعیِ repo اگر بود؛ وگرنه نسخهٔ امبدد (هر دو باید یکسان رفتار کنند).
    return CommandRegistry.load(find_registry())


def test_read_status_is_green_and_open():
    r = _reg()
    info = r.classify("/status")
    assert info["risk"] == "GREEN" and info["mode"] == "auto"
    assert r.role_allowed("/status", "viewer") is True
    assert r.role_allowed("/status", "agent") is True


def test_approval_group_is_red_owner_only():
    r = _reg()
    for cmd in ("/approve", "/reject", "/defer", "/rollback", "/halt_ziman"):
        info = r.classify(cmd)
        assert info["risk"] == "RED", cmd
        assert r.role_allowed(cmd, "owner") is True
        assert r.role_allowed(cmd, "admin") is False    # RED = owner only
        assert r.role_allowed(cmd, "agent") is False


def test_control_is_orange_and_catalog_yellow():
    r = _reg()
    assert r.classify("/policy")["risk"] == "ORANGE"
    assert r.classify("/catalog")["risk"] == "YELLOW"
    assert r.classify("/catalog")["mode"] == "propose"


def test_role_allowed_for_intermediate_tiers():
    """گیتِ نقش برای طبقاتِ میانی (ORANGE/YELLOW) هم پوشش داشته باشد."""
    r = _reg()
    # ORANGE control — operator/viewer اجازه ندارند؛ admin/owner دارند
    assert r.role_allowed("/policy", "operator") is False
    assert r.role_allowed("/policy", "viewer") is False
    assert r.role_allowed("/policy", "admin") is True
    assert r.role_allowed("/policy", "owner") is True
    # YELLOW data_catalog — operator مجاز است، viewer نه
    assert r.role_allowed("/product", "operator") is True
    assert r.role_allowed("/product", "viewer") is False


def test_alias_resolution():
    r = _reg()
    assert r.canonical("/ziman_status") == "/status"
    assert r.classify("/ziman_status")["risk"] == "GREEN"
    assert r.classify("/ziman_decisions")["command"] == "/queue"


def test_unknown_command_fail_closed():
    r = _reg()
    info = r.classify("/definitely_not_a_command")
    assert info["known"] is False
    assert info["risk"] == "RED" and info["mode"] == "deny"
    assert info["roles"] == []
    assert r.role_allowed("/definitely_not_a_command", "owner") is False


def test_embedded_fallback_matches_file():
    """اگر فایل نبود، نسخهٔ امبدد باید همان طبقه‌بندی را بدهد."""
    embedded = CommandRegistry.load("/no/such/path.yaml")
    assert embedded.classify("/approve")["risk"] == "RED"
    assert embedded.classify("/status")["risk"] == "GREEN"
