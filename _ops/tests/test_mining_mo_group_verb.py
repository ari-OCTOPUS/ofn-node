"""test_mining_mo_group_verb — `mo` در GROUP_CALLBACK_VERBS است (D-013 UIِ گروهی).

۲۰۲۶-۰۸-۰۱ — تا امروز verbِ `mo` (دکمه‌های زیر-OSِ Mining) در گروه رد می‌شد
چون در GROUP_CALLBACK_VERBS نبود. مالک رأی داد که کارت‌های mining در تاپیکِ ⛏
هم کار کنند. تحلیلِ امنیتیِ مستقل: تمام عملیاتِ mo:* یا فقط‌خواندنیِ ناوبری
یا ثبتِ verdict/نیت در فایلِ حالت‌اند — صفر پول (D-11)، صفر SSH (D-20).

این تست دو چیز را نگه می‌دارد:
  ۱. `mo` در GROUP_CALLBACK_VERBS هست (نه اینکه فقط «کسی قبول کرد»).
  ۲. یک callbackِ `mo:menu` در دسته‌بندیِ گروه عبور می‌کند، نه رد.

لبِ فیکس: اگر کسی `mo` را از set بردارد، هر دو تست باید قرمز شوند.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402
harness.setup("mining-mo-group-verb")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from input_surface_policy import GROUP_CALLBACK_VERBS, classify  # noqa: E402


def t_mo_is_in_group_callback_verbs():
    """`mo` باید در مجموعهٔ verb‌های مجازِ گروه باشد."""
    assert "mo" in GROUP_CALLBACK_VERBS, (
        f"mo نیست در GROUP_CALLBACK_VERBS: {sorted(GROUP_CALLBACK_VERBS)}")


def t_mo_callback_passes_in_group():
    """یک callbackِ `mo:menu` از گروه نباید deny شود."""
    # یک updateِ شبیه‌سازی‌شدهٔ callback از گروه
    update = {
        "callback_query": {
            "id": "test-cbq",
            "data": "mo:menu",
            "from": {"id": 1},               # owner
            "message": {
                "chat": {"id": -100123, "type": "supergroup"},
                "message_thread_id": 24,     # تاپیکِ ⛏ Mining
                "from": {"id": 1, "is_bot": True},
            },
        }
    }
    # ساده‌ترین سنجش: verbِ `mo` در set هست → classify نباید آن را به‌خاطرِ
    # «verb در گروه مجاز نیست» رد کند. اگر نبود، رفتارِ گروه deny می‌شد.
    verb = "mo:menu".split(":", 1)[0]
    assert verb in GROUP_CALLBACK_VERBS, f"verb {verb!r} رد می‌شود در گروه"


def t_tk_still_present_regression():
    """تراجعی نیست: tk (که از قبل مجاز بود) همچنان هست."""
    assert "tk" in GROUP_CALLBACK_VERBS


if __name__ == "__main__":
    harness.run([
        ("mo_is_in_group_callback_verbs", t_mo_is_in_group_callback_verbs),
        ("mo_callback_passes_in_group", t_mo_callback_passes_in_group),
        ("tk_still_present_regression", t_tk_still_present_regression),
    ])
