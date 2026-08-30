"""test_two_bot_bridge — دستوری که کارت پیشنهاد می‌دهد باید از همان‌جا کار کند.

یافتهٔ دبل‌چکِ ۲۰۲۶-۰۷-۲۷ (از رونوشتِ واقعیِ گروه، نه از حدس):

کارت‌های ارگانیسم صریحاً به مالک می‌گویند «/heart set sigma 0.8»، «/doctor focus
…»، «/brain guide …»، «۲۵۲ تراکنش منتظرِ توست — /review». هیچ‌کدام در روترِ
`telegram_center/center.py` نبودند. و باتِ ارگانیسم `TELEGRAM_ALLOWED_CHAT_IDS`
ندارد، پس پیامِ گروه را **رد می‌کند** و offset را جلو می‌برد.

یعنی **۳۲ دستور** از جایی که مالک می‌خواندشان به هیچ‌جا نمی‌رسیدند — و در آن ۳۲
تا `/panic` و `/stop` هم بودند. مالک ساعت‌ها در گروه حرف زد و «متوجه نشدم» گرفت.

قیدِ همراه، به‌اندازهٔ خودِ پل مهم: **پل هیچ گاردی را سست نمی‌کند.**
`handle_command` گیت‌های owner-only خودش را دارد و پل `from_id` واقعی را پاس
می‌دهد — پس این مسیر از فراخوانِ برنامه‌ایِ `from_id=None` **سخت‌گیرتر** است.
"""
import ast
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("two-bot-bridge")

_OPS = harness.REAL_VAULT / "_ops"
_CENTER = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
_AC = (_OPS / "budget" / "approval_channel.py").read_text("utf-8")


def _center_handlers() -> set:
    i = _CENTER.index("handlers = {")
    j = _CENTER.index("fn = handlers.get(cmd)", i)
    return {m.group(1) for m in re.finditer(r'"/([^"]+)"\s*:', _CENTER[i:j])}


def _advertised() -> set:
    """دستورهایی که متنِ کارت‌ها به مالک پیشنهاد می‌دهند."""
    out = set()
    for f in _OPS.rglob("*.py"):
        if set(f.parts) & {"tests", "_code", "__pycache__", "_Archive"}:
            continue
        try:
            s = f.read_text("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r'[«"\'\s(]/([a-z_]{3,12})(?:\s+[a-z<]|»|\'|"|\s|\))', s):
            out.add(m.group(1))
    return out


def _organism_cmds() -> set:
    return set(re.findall(r't\s*==\s*"/([a-z_]+)"', _AC)) | \
           set(re.findall(r'"/([a-z_]+)"', _AC))


# ─── ناوردیِ اصلی ──────────────────────────────────────────────────────────
def t_a_command_the_cards_advertise_is_reachable_from_the_group():
    """قلبِ یافته. اگر این بشکند، سیستم به مالک دستوری می‌دهد که کار نمی‌کند."""
    known = _center_handlers()
    org = _organism_cmds()
    unreachable = sorted(c for c in _advertised()
                         if c not in known and c in org)
    assert "_bridge_to_organism" in _CENTER, \
        (f"{len(unreachable)} دستورِ تبلیغ‌شده فقط در باتِ ارگانیسم‌اند و پلی "
         f"وجود ندارد: {unreachable[:8]}")


def t_the_emergency_commands_are_covered_by_the_bridge():
    """`/panic` و `/stop` از جایی که مالک می‌خواند باید در دسترس باشند."""
    org = _organism_cmds()
    for c in ("panic", "stop", "resume"):
        assert c in org, f"/{c} در روترِ ارگانیسم نیست"
    assert "_bridge_to_organism" in _CENTER


def t_the_bridge_runs_in_process_not_as_a_second_poller():
    """pollerِ دوم روی یک توکن = 409 Conflict. درسِ ۲۰۲۶-۰۷-۲۶."""
    i = _CENTER.index("def _bridge_to_organism")
    j = _CENTER.index("\n    def ", i + 10)
    body = _CENTER[i:j]
    for banned in ("poll_once", "getUpdates", "run_forever", "start_polling"):
        assert banned not in body, f"پل یک poller ساخت: {banned}"
    assert "handle_command" in body


# ─── قیدِ امنیتی: پل هیچ گاردی را سست نمی‌کند ─────────────────────────────
def t_the_bridge_passes_the_real_sender_so_owner_gates_fire():
    """`from_id=None` گیت‌های owner-only را **رد می‌کند** (backward-compat).

    اگر پل None بدهد، هر عضوِ گروه می‌تواند دستورِ تغییردهنده بزند. پس پاس‌دادنِ
    فرستندهٔ واقعی این‌جا یک جزئیات نیست — تفاوتِ بین گیتِ فعال و گیتِ خاموش است."""
    i = _CENTER.index("def _bridge_to_organism")
    j = _CENTER.index("\n    def ", i + 10)
    body = _CENTER[i:j]
    assert "from_id=" in body, "پل from_id پاس نمی‌دهد"
    assert "from_id=None" not in body.replace(" ", ""), "پل گیت را خاموش می‌کند"
    assert 'msg.get("from")' in body, "فرستندهٔ واقعی خوانده نمی‌شود"


def t_the_organism_router_still_owns_its_own_gates():
    """پل نباید منطقِ مجوز را کپی کند — منبعِ حقیقت یکی می‌ماند."""
    assert "_OWNER_ONLY_COMMANDS" in _AC
    assert "_OWNER_ONLY_COMMANDS" not in _CENTER, \
        "مرکز فهرستِ owner-only را کپی کرد — دو منبعِ حقیقت"


def t_the_bridge_never_breaks_the_existing_path():
    """ناشناخته برای هر دو → None → مسیرِ امروز بایت‌به‌بایت."""
    i = _CENTER.index("def _bridge_to_organism")
    j = _CENTER.index("\n    def ", i + 10)
    body = _CENTER[i:j]
    assert body.count("return None") >= 2, "پل روی شکست به مسیرِ قبلی برنمی‌گردد"
    assert "except Exception" in body


def t_the_bridge_is_tried_only_for_unknown_commands():
    """اگر مرکز خودش handler دارد، پل نباید دخالت کند."""
    i = _CENTER.index("_bridge_to_organism(text")
    around = _CENTER[max(0, i - 700):i]
    assert "fn is None" in around, "پل بی‌قید صدا زده می‌شود"
    assert 'cmd.startswith("/")' in around, "پل روی متنِ آزاد هم می‌دود"


# ─── عمومیت: دستورِ فردا هم بدونِ لمسِ کد کار کند ──────────────────────────
def t_the_bridge_is_generic_not_a_hand_written_list():
    """رأیِ مالک ۲۰۲۶-۰۷-۲۷: «یه پلی بساز هر دستوری بهش میدم خودکار بشه».

    اگر پل فهرستِ دستی داشته باشد، همان کژیِ اولیه است با لباسِ نو: هر دستورِ
    تازه‌ای که کسی به روترِ ارگانیسم اضافه کند، دوباره نامرئی می‌شود.

    پس شرط این است: پل **هیچ نامِ دستوری** نداشته باشد."""
    i = _CENTER.index("def _bridge_to_organism")
    j = _CENTER.index("\n    def ", i + 10)
    body = _CENTER[i:j]
    named = re.findall(r'"/[a-z_]{2,}', body)
    assert not named, f"پل نامِ دستور دارد — یعنی عام نیست: {named[:6]}"
    # تنها استثنای مجاز: دستورهایی که **خودِ مرکز** پشتِ فلگ گیت کرده. آن‌جا
    # «ناشناس بودن» یک قرارداد است نه اتفاق، و پل نباید تصمیمِ فلگ را دور بزند.
    # ولی این مجموعه باید کوچک و مستند بماند، وگرنه پل دوباره فهرستی می‌شود.
    m = re.search(r'_CENTRE_GATED\s*=\s*\{([^}]*)\}', _CENTER)
    assert m, "مجموعهٔ استثنا پیدا نشد"
    entries = re.findall(r'"(/[a-z_]+)"\s*:\s*"([^"]{10,})"', m.group(1))
    assert len(entries) <= 3, f"استثناها زیاد شدند: {len(entries)}"
    assert len(entries) == m.group(1).count('"/'), "مدخلی بدونِ دلیل"

    # و شرطِ فراخوانش هم نباید فهرست باشد
    k = _CENTER.index("_bridge_to_organism(text")
    guard = _CENTER[max(0, k - 400):k]
    assert not re.findall(r'cmd\s+in\s*\(', guard), "شرطِ پل یک فهرستِ دستی است"


def t_every_organism_command_is_covered_without_naming_it():
    """شمارشِ واقعی: چند دستور از روترِ ارگانیسم حالا از گروه در دسترس‌اند."""
    org = {c for c in _organism_cmds() if len(c) >= 3}
    known = _center_handlers()
    only_org = org - known
    assert len(only_org) >= 20, f"انتظارِ ده‌ها دستور بود، {len(only_org)} یافت شد"
    # همه‌شان از یک مسیرِ واحد می‌گذرند — هیچ‌کدام نامش در مرکز نیست
    for c in list(only_org)[:12]:
        assert f'"/{c}"' not in _CENTER, f"/{c} دستی سیم شده — پل عام نمانده"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_two_bot_bridge: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
