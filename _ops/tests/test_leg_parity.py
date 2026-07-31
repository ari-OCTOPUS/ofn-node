"""test_leg_parity.py — هر پا باید هر سه اتصال را داشته باشد، وگرنه سوییت داد بزند.

رأیِ مالک ۲۰۲۶-۰۷-۲۸: «گروه و پاها همه‌رو اتصالات رو کدنویسی کن پروژه‌هارو».

مسئله این نیست که یک پا جا افتاده — مسئله این است که **هیچ‌چیز نمی‌پرسد کدام پا
جا افتاده**. تا امروز چهار رجیستریِ مستقل وجود داشت که هیچ‌کدام دیگری را نمی‌دید:

    ORGANS (روترِ ارگانیسم) · topics (configِ گروه) ·
    STAFF/LEGS (اتاقِ چت)   · CULTIVATED_LEGS (کشتِ پا)

و اختلافشان بی‌صدا بود. اندازه‌گیریِ امروز: سه اندامِ ثبت‌شده (`cartographer`
`crypto` `knowledge`) در اتاقِ چت نبودند، پس مالک هرچقدر هم فارسیِ درست
می‌نوشت به آن‌ها نمی‌رسید — و هیچ تستی قرمز نمی‌شد چون هر رجیستری **به‌تنهایی**
سالم بود. این همان الگویی است که در حافظه ثبت شده: باگ در **درزِ** دو چیزِ سبز.

این فایل درز را می‌بندد، نه نمونه را
────────────────────────────────────
شکاف‌های شناخته‌شده در `KNOWN_GAPS` **صریح و کامنت‌دار**اند. تست سبز می‌ماند
چون شکاف اعلام‌شده است، نه چون کسی ندیدش. اگر پای تازه‌ای اضافه شود و سیم‌کشی
نشود، این‌جا قرمز می‌شود — و اگر شکافی بسته شود ولی از `KNOWN_GAPS` پاک نشود،
باز هم قرمز می‌شود. اعلامِ کهنه به‌اندازهٔ شکافِ ندیده بد است.

هیچ‌کدام از این چک‌ها فرمانی را **اجرا** نمی‌کند؛ فقط ثبت‌ها را با هم می‌سنجد.
زنده‌بودنِ خودِ فرمان‌ها کارِ `test_chat_room.t_e` و `test_command_discoverability`
است — و آن تقسیمِ کار عمدی است: این فایل باید بدونِ شبکه و بدونِ حالت بدود.
"""
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("leg-parity")

_OPS = _HERE.parent


# ── شکاف‌های اعلام‌شده ────────────────────────────────────────────────────────
# هر ردیف باید دلیل داشته باشد. «بعداً» دلیل نیست.
KNOWN_GAPS: dict[str, str] = {
    # (فعلاً خالی — هر سه شکافِ ۰۷-۲۸ در همان روز بسته شدند.)
}

# تاپیک‌هایی که عمداً اندام نیستند. این‌ها زیرساخت‌اند، نه پا.
NON_ORGAN_TOPICS: dict[str, str] = {
    "mirror": "اتاقِ آینه — گفتگوی مستقیم با خودآگاهی؛ هیچ فرمانی نگاشت نمی‌شود.",
    "system": "زیرساخت — هشدار/سلامت/بودجه. پا نیست.",
    "studio_pf": "ونچر — پلِ فرمانش زنده است ولی به‌عنوان اندام ثبت نشده. "
                 "وضعیتش در AGENT_QUESTIONS ثبت شده؛ ثبتِ اندام رأیِ مالک است.",
}


# ── خواندنِ رجیستری‌ها از خودِ سورس (نه کپیِ دستی — کپی کهنه می‌شود) ───────────
def _organs() -> dict:
    src = (_OPS / "budget" / "approval_channel.py").read_text("utf-8", errors="replace")
    m = re.search(r"ORGANS = \((.*?)\n    \)", src, re.S)
    assert m, "بلوکِ ORGANS در approval_channel.py پیدا نشد"
    rows = re.findall(
        r'\("([a-z_]+)",\s*"([^"]+)",\s*(None|"[A-Z0-9_]+"),\s*"(\w+)"\)', m.group(1))
    assert rows, "ORGANS خالی پارس شد — قالبش عوض شده؟"
    return {k: {"display": d, "flag": f.strip('"'), "kind": t} for k, d, f, t in rows}


def _topics() -> dict:
    p = harness.REAL_VAULT / "_ops" / "state" / "telegram" / "center-config.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text("utf-8")).get("topics") or {}


def _chat_room() -> dict:
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import chat_room as cr
    return {**cr.STAFF, **cr.LEGS}


def _cultivated() -> set:
    src = (_OPS / "legs" / "leg_cultivate.py").read_text("utf-8", errors="replace")
    m = re.search(r"CULTIVATED_LEGS = \((.*?)\)", src, re.S)
    return set(re.findall(r'"(\w+)"', m.group(1))) if m else set()


# ── ناوردی‌ها ────────────────────────────────────────────────────────────────
def t_a_every_organ_has_a_room_in_the_group():
    """اندامی که تاپیک ندارد، حرفش در General می‌افتد — همان‌جا که ۶۲٪ ارسال‌های
    دو روز افتاده بود و مالک گروه را «لولهٔ سروصدا» خواند."""
    missing = sorted(set(_organs()) - set(_topics()))
    assert not missing, f"اندامِ بی‌تاپیک: {missing}"


def t_b_every_organ_is_reachable_by_talking():
    """قلبِ خواستهٔ مالک: «با حرف زدنم بفهمه». اندامی که در اتاقِ چت نیست، فقط
    با حفظ‌کردنِ فرمانش قابلِ دسترسی است — یعنی عملاً نیست."""
    gap = sorted(set(_organs()) - set(_chat_room()))
    undeclared = [k for k in gap if k not in KNOWN_GAPS]
    assert not undeclared, (
        f"اندام‌هایی که با فارسیِ ساده به آن‌ها نمی‌رسی: {undeclared} — "
        "یا در chat_room ثبتشان کن یا با دلیل در KNOWN_GAPS اعلامشان کن")


def t_c_a_closed_gap_must_leave_the_declared_list():
    """اعلامِ کهنه به‌اندازهٔ شکافِ ندیده بد است: می‌گوید «می‌دانیم و پذیرفته‌ایم»
    دربارهٔ چیزی که دیگر شکاف نیست، و دفعهٔ بعد کسی بی‌خود دنبالش می‌گردد."""
    stale = [k for k in KNOWN_GAPS if k in _chat_room()]
    assert not stale, f"این‌ها دیگر شکاف نیستند، از KNOWN_GAPS پاکشان کن: {stale}"


def t_d_no_orphan_topic():
    """تاپیکی که نه اندام است نه زیرساختِ اعلام‌شده، یعنی اتاقی که کسی صاحبش
    نیست — و اتاقِ بی‌صاحب همان ۷ تاپیکِ خالیِ ۰۷-۲۸ می‌شود."""
    orphan = sorted(set(_topics()) - set(_organs()) - set(NON_ORGAN_TOPICS))
    assert not orphan, f"تاپیکِ بی‌صاحب: {orphan}"


def t_e_declared_infrastructure_topics_really_exist():
    """اگر تاپیکی را به‌عنوان زیرساخت اعلام کرده‌ایم ولی در گروه نیست، اعلاممان
    دروغ است و چکِ بی‌صاحب‌بودن را الکی راضی می‌کند."""
    topics = _topics()
    if not topics:
        return                      # بدونِ config چیزی برای سنجیدن نیست
    ghost = [k for k in NON_ORGAN_TOPICS if k not in topics]
    assert not ghost, f"در NON_ORGAN_TOPICS هست ولی در گروه نیست: {ghost}"


def t_f_chat_room_never_invents_an_organ():
    """اتاقِ چت نباید پایی را تبلیغ کند که ارگانیسم نمی‌شناسد. STAFF مغزهاست
    (اندام نیست)، پس فقط LEGS سنجیده می‌شود."""
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import chat_room as cr
    organs = set(_organs())
    invented = [k for k in cr.LEGS if k not in organs and k not in NON_ORGAN_TOPICS]
    assert not invented, f"اتاقِ چت پایی می‌سازد که اندام نیست: {invented}"


def t_g_cultivation_only_touches_real_organs():
    """`CULTIVATED_LEGS` سرمایه‌گذاری می‌کند. روی چیزی که اندام نیست یعنی
    بودجه به جایی می‌رود که مصرف‌کننده ندارد."""
    ghost = sorted(_cultivated() - set(_organs()))
    assert not ghost, f"کشتِ پا روی غیر-اندام: {ghost}"


def t_ha_every_organ_room_knows_its_own_subject():
    """پایگاه یعنی اتاق خودش موضوع را بداند (رأیِ مالک ۰۷-۲۸).

    اندامی که تاپیک دارد ولی در `ROOM_SUBJECT` نیست، اتاقی است که در آن نوشتنِ
    «چطوره؟» به جوابِ عمومی می‌رسد — یعنی اتاق هست و پایگاه نیست. این دقیقاً
    همان حالتی است که پای تازه بی‌سروصدا در آن می‌افتد.
    """
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import chat_room as cr
    topics, organs = _topics(), set(_organs())
    if not topics:
        return
    blind = sorted(o for o in organs if o in topics
                   and o not in cr.ROOM_SUBJECT)
    assert not blind, f"اتاق دارند ولی موضوعشان را نمی‌دانند: {blind}"


def t_hb_no_room_subject_points_at_a_ghost():
    """وارونه‌اش هم بد است: موضوعی که مقصدش در جدول نیست یعنی نوشتن در آن اتاق
    به KeyError یا سکوت می‌رسد."""
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import chat_room as cr
    table = {**cr.STAFF, **cr.LEGS, **cr.ROOMS}
    ghost = sorted(v for v in cr.ROOM_SUBJECT.values() if v not in table)
    assert not ghost, f"موضوعِ اتاق به مقصدِ ناموجود اشاره می‌کند: {ghost}"
    topics = _topics()
    if topics:
        no_room = sorted(k for k in cr.ROOM_SUBJECT if k not in topics)
        assert not no_room, f"موضوع برای تاپیکی که در گروه نیست: {no_room}"


def t_h_every_advertised_leg_command_exists_in_a_router():
    """گاردِ ضدِ فرمانِ خیالی — همان دسته‌ای که ۰۷-۲۸ صبح تبلیغ می‌شد و در هیچ
    باتی نبود. سه روتر واقعی داریم؛ فرمان باید در یکی‌شان **متنی** پیدا شود.

    ⚠️ این چکِ متنی است و عمداً ضعیف‌تر از اجراست: زنده‌بودنِ واقعی را
    `test_chat_room.t_e` می‌سنجد. این‌جا فقط جلوی تایپوی خاموش گرفته می‌شود.
    """
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import chat_room as cr
    routers = "".join(
        (_OPS / p).read_text("utf-8", errors="replace") for p in (
            Path("telegram_center") / "center.py",
            Path("budget") / "approval_channel.py",
            Path("legs") / "langar_bridge.py",
        ))
    missing = [f"{k}:{cmd}" for k, (_d, cmd, _w) in {**cr.STAFF, **cr.LEGS}.items()
               if f'"{cmd.split()[0]}"' not in routers]
    assert not missing, f"فرمانِ بی‌روتر: {missing}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_leg_parity: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
