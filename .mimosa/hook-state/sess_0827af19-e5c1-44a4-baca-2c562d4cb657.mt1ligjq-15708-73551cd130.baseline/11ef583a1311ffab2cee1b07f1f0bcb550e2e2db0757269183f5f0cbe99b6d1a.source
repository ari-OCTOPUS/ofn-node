"""test_chat_room.py — اتاقِ چت: فارسیِ ساده → کارمندِ درست.

رأیِ مالک ۲۰۲۶-۰۷-۲۸: «تو گروه یه جا رو بزار چت کنم از طریقش همه پاهارو کنترل
کنم … تعاملارو بیشتر چت گونه میخوام و با مغزهای مختلف اختاپوس حرف بزنم».

این فایل چهار چیز را قفل می‌کند — سه‌تایش دربارهٔ چیزی است که **نباید** بشود:

  ۱ فلگ خاموش = مرکز بایت‌به‌بایت مثل امروز (اتاق حتی کلاسیفای هم نمی‌کند).
  ۲ جملهٔ فارسیِ ساده به فرمانِ درست بازپخش می‌شود — با متنِ فرمان، نه متنِ مالک.
  ۳ مبهم = **می‌پرسد**؛ هیچ‌وقت یکی از دو کارمند را حدس نمی‌زند.
  ۴ هیچ فرمانِ خیالی‌ای تبلیغ نمی‌شود (۸ تای امروز صبح دقیقاً همین بودند).

بندِ ۲ ظریف‌ترین است: نسخهٔ اولِ ذهنیِ من handler را مستقیم صدا می‌زد، ولی
کلوژرِ handlerها متنِ **مالک** را بسته‌اند — `_funnel_cmd(text)` آرگومانش را از
جملهٔ فارسی می‌خواند. تستِ `t_c` همان را می‌گیرد.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("chat-room")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))
import os                       # noqa: E402
import chat_room as cr          # noqa: E402

FLAG = cr.FLAG


def _on():
    os.environ[FLAG] = "1"


def _off():
    os.environ.pop(FLAG, None)


# ── لایهٔ ۱: خودِ مسیریاب ──────────────────────────────────────────────────

def t_a_plain_persian_reaches_the_right_employee():
    """جمله‌هایی که مالک واقعاً می‌نویسد — نه کلیدواژهٔ تمیزشده."""
    cases = {
        "چه خبر": "/now",
        "پول چطوره": "/money",
        "مشکلی هست؟": "/doctor",
        "چی یاد گرفتی": "/school",
        "تو کی هستی": "/reveal",
        "قلب چطوره": "/heart",
        "چیزی منتظر رأی منه؟": "/queue",
        "لید جدید داریم؟": "/lead",
        "ماینینگ چطوره": "/mining",
        "نظرت چیه": "/brain",
    }
    for text, want in cases.items():
        got = cr.classify(text)
        assert got.get("command") == want, (text, got)


def t_ab_a_new_keyword_may_never_steal_an_old_route():
    """قفلِ ضدِ رگرسیونِ جدول.

    ۲۰۲۶-۰۷-۲۸ سه پا اضافه شد (crypto/knowledge/cartographer). خطرِ واقعیِ آن
    کار «جا افتادنِ پا» نبود — **دزدیده‌شدنِ مسیرِ موجود** بود: یک کلیدواژهٔ تازه
    که در جملهٔ قدیمی هم پیدا می‌شود، بی‌صدا برنده می‌شود و مالک جوابِ کارمندِ
    اشتباه می‌گیرد که شبیهِ جوابِ درست است. دو نمونهٔ واقعی که همان روز نزدیک بود
    اتفاق بیفتد: «دانش» (مالِ school) و «کوین» درونِ «بیت‌کوین» (مالِ mining).

    این جدول رفتارِ **پذیرفته‌شدهٔ** امروز است، نه آرزو. هر تغییری در
    `STAFF`/`LEGS` که این را بشکند باید عمدی و توضیح‌دار باشد.
    """
    locked = {
        "چه خبر": "/now", "پول چطوره": "/money", "مشکلی هست؟": "/doctor",
        "چی یاد گرفتی": "/school", "تو کی هستی": "/reveal",
        "قلب چطوره": "/heart", "چیزی منتظر رأی منه؟": "/queue",
        "لید جدید داریم؟": "/lead", "ماینینگ چطوره": "/mining",
        "نظرت چیه": "/brain", "گالری زیمان چطوره": "/deal",
        "دفتر حسابداری": "/books", "تحقیق کردی؟": "/school",
        # پاهای تازه — و «بیت‌کوین» که «کوین»ِ ماینینگ را درون خود دارد و باید
        # با قاعدهٔ spanِ خاص‌تر به کریپتو برود، نه به ماینینگ.
        "کریپتو چطوره": "/organs crypto",
        "بیت‌کوین چقدر شد": "/organs crypto",
        "نقشه معماری رو بده": "/organs cartographer",
        "یادداشت‌هام کجاست": "/organs knowledge",
    }
    stolen = {s: (want, cr.classify(s).get("command"))
              for s, want in locked.items()
              if cr.classify(s).get("command") != want}
    assert not stolen, f"مسیرِ دزدیده‌شده: {stolen}"


def t_ac_the_room_is_part_of_the_question():
    """پایگاه، نه تابلوی اعلانات (رأیِ مالک ۰۷-۲۸: «گروه بشه پایگاهِ پروژه‌ها»).

    سه قاعده، و ترتیبشان تمامِ ماجراست. مدلِ ذهنی که مالک باید نگه دارد یک جمله
    است: **هرچه نام ببری همان را می‌گیری؛ چیزی نام نبری، اتاق را می‌گیری** — با
    یک استثنای اعلام‌شده برای پرسشِ عمومیِ وضعیت، چون «چه خبر از این؟» در اتاقِ
    لید یعنی لید، نه کلِ سیستم.
    """
    # ۳ — بی‌کلیدواژه در اتاقِ موضوع‌دار
    for room, txt, want in (("mining", "چطوره؟", "/mining"),
                            ("accounting", "خب؟", "/books"),
                            ("knowledge", "تازه چی داری", "/organs knowledge"),
                            ("studio_pf", "چطور پیش میره", "/brief")):
        got = cr.classify(txt, room=room)
        assert got.get("command") == want, (room, txt, got)
        assert got["reason"] == "room-context", got

    # استثنا — پرسشِ عمومیِ وضعیت مالِ خودِ اتاق است
    for room, want in (("lead", "/lead"), ("ziman", "/deal"),
                       ("crypto", "/organs crypto")):
        got = cr.classify("چه خبر از این؟", room=room)
        assert got.get("command") == want, (room, got)
        assert got["reason"] == "room-owns-status", got

    # ۱ — کلیدواژهٔ صریح بر اتاق مقدم است، وگرنه اتاق زندان می‌شود
    for room, txt, want in (("mining", "پول چطوره", "/money"),
                            ("lead", "مشکلی هست؟", "/doctor"),
                            ("crypto", "تو کی هستی", "/reveal"),
                            ("mining", "چی یاد گرفتی", "/school")):
        got = cr.classify(txt, room=room)
        assert got.get("command") == want, (room, txt, got)

    # ۲ — اتاق تساوی را می‌شکند، ولی فقط اگر خودش نامزد باشد
    inside = cr.classify("پول و ماینینگ", room="mining")
    assert inside.get("command") == "/mining", inside
    assert inside["reason"] == "room-breaks-tie", inside
    outside = cr.classify("پول و ماینینگ", room="system")
    assert outside["match"] is None and outside["tied"], outside


def t_acb_saying_the_name_of_the_room_you_are_in_is_not_a_jump():
    """رأیِ مالک ۰۷-۲۸: «مغز دانش‌نامه، قلب سیستم، چشم نقشه‌بردار».

    اتاق‌های گروه نامِ استعاریِ بدنِ اختاپوس دارند، و یکی‌شان مستقیماً با
    کلیدواژهٔ یک کارمند تصادم می‌کند: اتاقِ دانش‌نامه «مغز» نام دارد و «مغز»
    کلیدواژهٔ کورتکس است.

    بدونِ قاعدهٔ alias، «مغز چطوره» **داخلِ اتاقِ مغز** به کورتکس می‌رفت — مالک
    اسمِ اتاقِ خودش را می‌گفت و جای دیگری می‌رسید. راه‌حلِ ساده‌لوحانه (دادنِ
    کلیدواژهٔ «مغز» به دانش‌نامه) کورتکس را برای همیشه بی‌نام می‌کرد.
    """
    inside = cr.classify("مغز چطوره", room="knowledge")
    assert inside.get("command") == "/organs knowledge", inside
    assert inside["reason"] == "room-alias", inside
    # همان جمله بیرون از آن اتاق همچنان یعنی کورتکس
    for room in ("", "mining", "lead", "system"):
        out = cr.classify("مغز چطوره", room=room)
        assert out.get("command") == "/brain", (room, out)
    # و اسمِ اتاق را نگفتن، حتی داخلِ همان اتاق، جهشِ عادی است
    assert cr.classify("نظرت چیه", room="knowledge").get("command") == "/brain"


def t_acc_the_cards_speak_the_group_s_own_names():
    """کارت «⛏ ماینینگ» می‌گفت و اتاق «بازوی معدن» بود — دو اسم برای یک چیز، و
    مالک باید در ذهنش ترجمه می‌کرد. حالا یکی‌اند."""
    names = {k: v[0] for k, v in cr.LEGS.items()}
    for key, must in (("mining", "معدن"), ("crypto", "سکه"),
                      ("knowledge", "مغز"), ("cartographer", "چشم"),
                      ("accounting", "دفتر"), ("ziman", "گالری"),
                      ("lead", "رنگ")):
        assert must in names[key], (key, names[key])
    # و هر aliasِ اعلام‌شده باید یا تاپیکی باشد که موضوع دارد، یا زیرساختِ
    # شناخته‌شده — وگرنه یک قاعدهٔ مرده است که کسی خبر ندارد.
    for room in cr.ROOM_ALIAS:
        assert room in cr.ROOM_SUBJECT or room in ("system", "mirror"), room


def t_ad_outside_a_subject_room_nothing_changed():
    """گاردِ رگرسیون: هر جای دیگر — General، خصوصی، اتاقِ آینه، اتاقِ سیستم —
    باید **دقیقاً** همان جوابِ قبل از پایگاه را بدهد. اگر این بشکند یعنی
    contextِ اتاق به جایی نشت کرده که نباید."""
    probes = ("چه خبر", "پول چطوره", "مشکلی هست؟", "سلام", "امروز هوا خوبه",
              "پول و ماینینگ", "تو کی هستی")
    for txt in probes:
        base = cr.classify(txt)
        for room in ("", "system", "mirror", "unknown_room_xyz"):
            got = cr.classify(txt, room=room)
            assert got.get("command") == base.get("command"), (txt, room, got)
            assert got["reason"] == base["reason"], (txt, room, got)


def t_ae_the_venture_is_reachable_only_from_its_own_room():
    """ونچر عمداً کلیدواژه ندارد: قراردادِ این مخزن محتوا-آزاد و هویت-آزاد است،
    پس نامش نه در کد می‌آید نه مالک لازم است تایپش کند. نوشتن **در اتاقش**
    تنها راه است — و همین هم آزموده می‌شود که واقعاً راه باشد."""
    assert "venture" in cr.ROOMS
    assert cr.ROOM_SUBJECT.get("studio_pf") == "venture"
    assert cr.ROOMS["venture"][2] == (), "ونچر نباید کلیدواژه داشته باشد"
    # از هیچ متنی، در هیچ اتاقِ دیگری، نباید به ونچر رسید
    for txt in ("چه خبر", "پول چطوره", "ونچر", "پروژه", "استودیو"):
        for room in ("", "mining", "lead", "system"):
            got = cr.classify(txt, room=room)
            assert got.get("match") != "venture", (txt, room, got)
    assert cr.classify("چطور پیش میره", room="studio_pf").get("match") == "venture"


def t_b_arabic_forms_normalise():
    """«میتونم» و «می‌تونم» و «كي» نباید سه چیزِ متفاوت باشند — وگرنه جدولِ
    کلیدواژه بی‌صدا نصفه کار می‌کند و هیچ تستی هم قرمز نمی‌شود."""
    assert cr.classify("تو كي هستی")["command"] == "/reveal"
    assert cr.classify("چه‌خبر").get("command") == "/now"


def t_c_ambiguous_asks_instead_of_guessing():
    """تساوی → `match=None` و `tied` پر. مسیریابیِ غلطِ بی‌صدا بدترین حالت است."""
    got = cr.classify("پول و ماینینگ")
    assert got["match"] is None, got
    assert set(got["tied"]) == {"money", "mining"}, got
    card = cr.ask_which(got["tied"])
    assert "/money" in card and "/mining" in card


def t_d_no_keyword_returns_none_not_a_guess():
    for text in ("سلام", "امروز هوا خوبه", "ok", ""):
        got = cr.classify(text)
        assert got["match"] is None, (text, got)
        assert got["reason"] in ("no-keyword", "empty"), (text, got)


def t_e_every_advertised_command_is_real():
    """۰۷-۲۸: ۸ فرمان تبلیغ می‌شد که در **هیچ باتی** وجود نداشت
    (`/brief /drafts /gates /guards /rules /spine /start_exp /think`).
    این تست همان دسته را برای اتاقِ چت غیرممکن می‌کند: هر فرمانِ جدول باید
    در `center.py` یا در باتِ ارگانیسم واقعاً handler داشته باشد."""
    phantom = {"/brief", "/drafts", "/gates", "/guards", "/rules", "/spine",
               "/start_exp", "/think"}
    src = (_HERE.parent / "telegram_center" / "center.py").read_text(
        encoding="utf-8", errors="replace")
    bridged = (_HERE.parent / "budget" / "approval_channel.py").read_text(
        encoding="utf-8", errors="replace")
    for key, (_disp, cmd, _w) in {**cr.STAFF, **cr.LEGS}.items():
        base = cmd.split()[0]        # `/organs crypto` → `/organs`
        assert base not in phantom, f"{key} یک فرمانِ خیالی را تبلیغ می‌کند: {cmd}"
        # فرمانِ آرگومان‌دار دو شرط دارد: خودِ فرمان ثبت باشد، **و** شاخهٔ
        # آرگومان‌دارش وجود داشته باشد. بدونِ شرطِ دوم `/organs crypto` به
        # تطابقِ دقیقِ `/organs` نمی‌خورد، از همهٔ شاخه‌ها رد می‌شود و به
        # `return None` می‌رسد — یعنی دقیقاً همان سکوتی که این تست جلویش را
        # می‌گیرد، فقط یک لایه عمیق‌تر.
        assert (f'"{base}"' in src) or (f'"{base}"' in bridged), \
            f"{key}: {base} در هیچ روتری پیدا نشد"
        if " " in cmd:
            assert f'"{base} "' in src or f'"{base} "' in bridged, \
                f"{key}: {cmd} آرگومان دارد ولی هیچ روتری شاخهٔ آرگومان‌دار ندارد"


def t_f_menu_lists_only_live_staff():
    m = cr.menu()
    for _k, (_d, cmd, _w) in cr.STAFF.items():
        assert cmd in m
    assert "/brief" not in m and "/think" not in m


# ── لایهٔ ۲: سیم‌کشی در مرکز ───────────────────────────────────────────────

class _Client:
    def __init__(self):
        self.sent = []

    def send(self, text, chat_id=None, keyboard=None, topic_id=None):
        self.sent.append(text)
        return 1


class _Fake:
    """کمینه‌ترین چیزی که `_chat_room` لمس می‌کند — بدونِ بالاآوردنِ کلِ مرکز."""

    def __init__(self):
        self._client = _Client()
        self.replayed = []

    _chat_room = None          # در setup از کلاسِ واقعی وصل می‌شود
    _reply_thread = staticmethod(lambda msg: None)

    def _topic_key(self, msg):
        """اتاقِ پیام. فیک ساده است چون قراردادش ساده است: نامِ تاپیک یا "".
        نسخهٔ واقعی در center.py وارونهٔ نگاشتِ center-config را می‌زند."""
        return str(msg.get("_room") or "")

    def _handle_message(self, msg):
        self.replayed.append(msg)
        return {"kind": str(msg.get("text", "")).lstrip("/"), "sent": True}


def _wire():
    """متدِ واقعیِ مرکز را روی کلاسِ فیک ببند. importِ خودِ `center` سنگین و
    پرعارضه است (poller می‌سازد)، ولی خودِ متد stdlib-only است."""
    import ast
    src = (_HERE.parent / "telegram_center" / "center.py").read_text(
        encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_chat_room":
            fn = node
            break
    assert fn is not None, "متدِ _chat_room در center.py نیست"
    ns = {"_scrub": lambda s: s}
    exec(compile(ast.Module(body=[fn], type_ignores=[]),
                 "<center._chat_room>", "exec"), ns)
    _Fake._chat_room = ns["_chat_room"]
    return _Fake()


def t_g_flag_off_is_a_no_op():
    """خاموش = مرکز دست‌نخورده. اگر این قرمز شود یعنی رفتارِ امروزِ مالک عوض شده."""
    _off()
    f = _wire()
    out = f._chat_room({"chat": {"id": 1}}, "پول چطوره")
    assert out is None, out
    assert f.replayed == [] and f._client.sent == []


def t_h_flag_on_replays_the_command_not_the_persian():
    """بازپخش باید متنِ **فرمان** را ببرد. اگر متنِ مالک برود، هر handlerی که
    آرگومان می‌خواند (`/quote`، `/won`، …) بی‌صدا غلط پارس می‌کند."""
    _on()
    try:
        f = _wire()
        out = f._chat_room({"chat": {"id": 1}}, "پول چطوره")
        assert out is not None
        assert len(f.replayed) == 1, f.replayed
        assert f.replayed[0]["text"] == "/money", f.replayed[0]
        assert "پول" not in f.replayed[0]["text"]
        assert out.get("routed_from") == "chat-room"
    finally:
        _off()


def t_hb_the_replay_keeps_the_real_sender():
    """گیت‌های owner-only روی `msg["from"]["id"]` می‌نشینند (center.py:929).

    اگر بازپخش این را گم کند، یک عضوِ گروه می‌تواند با یک جملهٔ فارسیِ ساده به
    فرمانی برسد که فقط مالک باید بتواند بزند — بالا بردنِ سطحِ دسترسی از راهِ
    یک درِ راحتی. این تست همان را غیرممکن می‌کند.
    """
    _on()
    try:
        f = _wire()
        msg = {"chat": {"id": -100}, "from": {"id": 6150431610, "is_bot": False},
               "message_thread_id": 7}
        f._chat_room(msg, "پول چطوره")
        assert len(f.replayed) == 1
        r = f.replayed[0]
        assert r.get("from") == msg["from"], r
        assert r.get("chat") == msg["chat"], r
        assert r.get("message_thread_id") == 7, r   # جواب در همان تاپیک
    finally:
        _off()


def t_i_ambiguous_sends_a_question_and_replays_nothing():
    _on()
    try:
        f = _wire()
        out = f._chat_room({"chat": {"id": 1}}, "پول و ماینینگ")
        assert out["kind"] == "chat-room-ask", out
        assert f.replayed == [], f.replayed
        assert len(f._client.sent) == 1
        assert "/money" in f._client.sent[0]
    finally:
        _off()


def t_j_depth_guard_blocks_a_second_hop():
    """گاردِ دومِ صریح. بازگشتِ بی‌پایان از راهِ `/` هم بسته است، ولی یک عدد
    ارزان‌تر از اتکا به یک ناوردیِ نانوشته است."""
    _on()
    try:
        f = _wire()
        out = f._chat_room({"chat": {"id": 1}, "_chat_room_depth": 1},
                           "پول چطوره")
        assert out is None
        assert f.replayed == []
    finally:
        _off()


def t_ka_silence_is_never_an_answer():
    """اگر فرمانِ کارمند پشتِ فلگِ خاموش باشد، اتاق باید **بگوید**، نه ساکت شود.

    این باگ در کارِ خودم بود و قبل از ارسال گرفته شد: `/mining` در
    `_CENTRE_GATED` است، پس با فلگِ خاموشِ `OCTOPUS_WIRE_MINING_UI` جملهٔ
    «ماینینگ چطوره» درست مسیریابی می‌شد و بعد **هیچ** — همان تجربه‌ای که
    مالک «گمراه‌کننده» خواندش، این بار ساختهٔ درِ تازه.
    """
    _on()
    try:
        f = _wire()
        f._handle_message = lambda msg: None          # روتر ساکت
        out = f._chat_room({"chat": {"id": 1}}, "ماینینگ چطوره")
        assert out is not None and out["kind"] == "chat-room-dark", out
        assert out["command"] == "/mining", out
        assert len(f._client.sent) == 1
        assert "/mining" in f._client.sent[0]
    finally:
        _off()


def t_kb_the_room_reaches_the_centre_not_just_classify():
    """قفلِ سیم‌کشی. `classify` می‌تواند بی‌نقص باشد و مرکز اتاق را پاس ندهد —
    و آن‌وقت همه‌چیز سبز است و مالک در تاپیکِ ماینینگ باز هم جوابِ عمومی
    می‌گیرد. این تست از **مرکز** می‌سنجد، نه از ماژول."""
    _on()
    try:
        f = _wire()
        out = f._chat_room({"chat": {"id": -100}, "_room": "mining"}, "چطوره؟")
        assert out is not None, "اتاق به مرکز نرسید"
        assert len(f.replayed) == 1 and f.replayed[0]["text"] == "/mining", f.replayed
        # همان جمله بیرونِ اتاق نباید به ماینینگ برود
        g = _wire()
        assert g._chat_room({"chat": {"id": 1}}, "چطوره؟") is None, g.replayed
    finally:
        _off()


def t_kc_a_broken_room_lookup_must_not_silence_the_room():
    """اگر تشخیصِ اتاق بترکد، «اتاق ندارم» درست است و «حرف نزن» غلط.

    نسخهٔ اولِ سیم‌کشی `_topic_key` را داخلِ همان try گذاشته بود که خطایش
    `return None` می‌داد؛ یعنی یک نقصِ کوچک در تشخیصِ اتاق کلِ اتاقِ چت را
    بی‌صدا خاموش می‌کرد. چهار تست همان لحظه گرفتندش — این یکی نگه‌اش می‌دارد.
    """
    _on()
    try:
        f = _wire()

        def _boom(_msg):
            raise RuntimeError("configِ تاپیک خراب")

        f._topic_key = _boom
        out = f._chat_room({"chat": {"id": 1}}, "پول چطوره")
        assert out is not None, "تشخیصِ اتاقِ خراب کلِ اتاق را خاموش کرد"
        assert f.replayed and f.replayed[0]["text"] == "/money", f.replayed
    finally:
        _off()


def t_kd_a_gated_command_falls_back_to_the_generic_organ_card():
    """بن‌بست ممنوع — حتی بن‌بستِ مؤدب.

    آزمونِ زندهٔ مالک (۰۷-۲۸ ۱۹:۴۰): «چطوره؟» در بازوی معدن درست مسیریابی شد و
    کارتِ «⛏ ماینینگ الان جواب نمی‌دهد» گرفت، چون `/mining` پشتِ فلگِ خاموش
    است. جوابش این بود: «دکمه نداشت» — و حق داشت. کارتی که می‌گوید خاموشم و
    راهی نشان نمی‌دهد همان تجربه‌ای است که کلِ هفته ازش شکایت داشت، فقط
    مؤدبانه‌تر.

    ولی `/organs mining` **زنده است** و وضعیتِ واقعی را دارد. پس فرمانِ گیت‌شده
    باید به آن بیفتد. عام است نه وصلهٔ ماینینگ: هر پایی، هر فلگی.
    """
    _on()
    try:
        f = _wire()
        seen = []

        def _router(m):
            seen.append(m["text"])
            if m["text"] == "/mining":
                return None                     # گیت‌شده
            return {"kind": m["text"].lstrip("/"), "sent": True}

        f._handle_message = _router
        out = f._chat_room({"chat": {"id": 1}}, "ماینینگ چطوره")
        assert out is not None, out
        assert out.get("routed_from") == "chat-room-fallback", out
        assert out.get("gated") == "/mining" and out.get("served") == "/organs mining", out
        assert seen == ["/mining", "/organs mining"], seen
        assert f._client.sent == [], "کارتِ خاموشی نباید فرستاده می‌شد"
    finally:
        _off()


def t_kda_a_gated_brain_never_falls_back_to_an_organ_card():
    """جوابِ غلط از بن‌بست بدتر است.

    `LEGS` اندام‌اند و `/organs <slug>` برایشان معنا دارد. `STAFF` مغزند و
    `/organs doctor` جوابِ «اندامی به این نام نیست» می‌دهد — یعنی مالک به‌جای
    سکوت یک **جوابِ غلط** می‌گیرد که شبیهِ جوابِ درست است. همان مسیریابیِ
    بی‌صدایی که کلِ این ماژول برای جلوگیری از آن ساخته شد.
    """
    _on()
    try:
        f = _wire()
        seen = []

        def _router(m):
            seen.append(m["text"])
            return None                        # همه‌چیز گیت‌شده

        f._handle_message = _router
        out = f._chat_room({"chat": {"id": 1}}, "مشکلی هست؟")   # → /doctor (مغز)
        assert out["kind"] == "chat-room-dark", out
        assert seen == ["/doctor"], f"نباید سراغِ /organs می‌رفت: {seen}"
    finally:
        _off()


def t_ke_the_dark_card_still_comes_when_there_is_no_fallback():
    """اگر جایگزین هم ساکت بود، سکوت باز هم ممنوع است."""
    _on()
    try:
        f = _wire()
        f._handle_message = lambda m: None
        out = f._chat_room({"chat": {"id": 1}}, "ماینینگ چطوره")
        assert out["kind"] == "chat-room-dark", out
        assert len(f._client.sent) == 1
    finally:
        _off()


def t_k_no_match_falls_through_untouched():
    _on()
    try:
        f = _wire()
        assert f._chat_room({"chat": {"id": 1}}, "سلام") is None
        assert f.replayed == [] and f._client.sent == []
    finally:
        _off()


if __name__ == "__main__":
    _fails = []
    for _n, _f in sorted(globals().items()):
        if _n.startswith("t_") and callable(_f):
            try:
                _f()
                print(f"  ok   {_n}")
            except Exception as _e:  # noqa: BLE001
                _fails.append((_n, _e))
                print(f"  FAIL {_n}: {type(_e).__name__}: {_e}")
    print(f"\n{'FAILED' if _fails else 'PASSED'}: {len(_fails)} fail")
    sys.exit(1 if _fails else 0)
