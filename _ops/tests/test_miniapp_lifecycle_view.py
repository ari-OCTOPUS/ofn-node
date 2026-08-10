"""test_miniapp_lifecycle_view — مینی‌اپ یک سطحِ **خواندنیِ اضافی** است، نه صفحهٔ فرمانِ دوم.

گامِ ۱۹ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C6). سه ناوردی سنجیده می‌شوند و
هر سه با جهش آزموده شده‌اند:

  ۱) **دیوارِ 405 دست‌نخورده.** هیچ verb ِ نوشتنی به این نما اضافه نشده؛ متنِ
     دیوارِ متد در `miniapp_gateway._handle_core` بایت‌به‌بایت pin شده و
     `POST/PUT/DELETE` روی مسیرِ نو ۴۰۵ می‌گیرد در حالی که ذخیرهٔ کارت‌ها
     بایت‌یکسان می‌ماند.
  ۲) **whitelist ِ سختِ بدنه.** بدنهٔ سریالایزشده byte-grep می‌شود: صفر رخداد
     از `token_sha256`، `nonce`، `owner`، `summary` — نه نامِ کلید و نه هیچ
     مقدارِ واقعی‌شان. `pending-cards.json` هر چهار فیلد را دارد و تنها مقصدِ
     تونلِ cloudflared همین gateway است.
  ۳) **غیاب ⇒ UNKNOWN، هرگز صفر.** یک ذخیرهٔ غایب هم‌شکلِ «صفر کارتِ راکد»
     رندر نمی‌شود؛ stampِ UNKNOWN کلیدِ `value` ندارد.

ایزوله (درسِ ثبت‌شدهٔ ۰۸-۰۳): هر مسیرِ تحتِ آزمون `state_dir` صریحِ موقت
می‌گیرد و `t_fixture_is_never_the_live_tree` اثبات می‌کند فیکسچر زیرِ درختِ
زنده نیست. هیچ تستی به `F:\\backup\\_ops\\state` نمی‌نویسد.
"""
import ast
import hashlib
import hmac
import json
import os
import sqlite3
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("miniapp-lifecycle")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes"),
           str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lifecycle_fold as lf        # noqa: E402
import miniapp_state as ms         # noqa: E402
import miniapp_gateway as mg       # noqa: E402

LIVE_TREE = Path(r"F:\backup").resolve()

# نشانگرهای یکتا — byte-grep دنبالِ همین‌ها می‌گردد، پس یک نشتِ واقعی
# نمی‌تواند پشتِ رشتهٔ عمومی پنهان شود.
MARK_TOKEN = "b7f3c0d1" * 8            # ۶۴ هگز، شکلِ واقعیِ token_sha256
MARK_NONCE = "NONCEMARKER9911"
MARK_OWNER = "OWNERMARKER4242"
MARK_SUMMARY = "SUMMARYMARKER تغییرِ setpoint قلب"

N_STALLED = 20        # سنجهٔ زندهٔ ۲۰۲۶-۰۸-۰۳ (stalled_cards روی درختِ زنده)
N_DECIDED = 21        # ۲۱ ردیفِ RECONCILE_REQUIRED با receipt_id تهی
N_TOTAL = N_STALLED + N_DECIDED


# ─── فیکسچر ────────────────────────────────────────────────────────────────
def _card(idx: int, *, delivery: str, decision: str, decision_key="decision") -> dict:
    """پاکتِ واقعیِ rfc — با همان یازده فیلدی که درختِ زنده دارد."""
    return {
        "kind": "rfc",
        "rfc_id": f"RFC-{idx:04d}",
        "summary": f"{MARK_SUMMARY} #{idx}",
        "owner": MARK_OWNER,
        "nonce": f"{MARK_NONCE}-{idx}",
        "token_sha256": MARK_TOKEN,
        "expires_at": 1785200000 + idx,
        "delivery": delivery,
        decision_key: decision,
        "created_ts": 1785027842.0 + idx,
        "updated_ts": 1785100000.0 + idx,
    }


def _make_state_dir(*, cards=True, verdicts=True, applied_with_receipt=0,
                    applied_without_receipt=0, decision_key="decision") -> Path:
    root = Path(tempfile.mkdtemp(prefix="miniapp-lifecycle-"))
    state = root / "_ops" / "state"
    (state / "pulse").mkdir(parents=True)
    if cards:
        store = {}
        for i in range(N_STALLED):
            store[f"rfc:RFC-{i:04d}"] = _card(i, delivery="SENT", decision="SUBMITTED",
                                              decision_key=decision_key)
        for i in range(N_STALLED, N_TOTAL):
            store[f"rfc:RFC-{i:04d}"] = _card(i, delivery="SENT", decision="DECIDED",
                                              decision_key=decision_key)
        (state / "pulse" / "pending-cards.json").write_text(
            json.dumps(store, ensure_ascii=False), "utf-8")
    if verdicts:
        (state / "doctor").mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(state / "doctor" / "rfc-verdicts.db"))
        con.execute("CREATE TABLE IF NOT EXISTS rfc_decision("
                    "rfc_id TEXT PRIMARY KEY, verdict TEXT NOT NULL, revision INTEGER NOT NULL,"
                    "state TEXT NOT NULL, lease_owner TEXT, lease_until INTEGER,"
                    "receipt_id TEXT, operation_key TEXT, updated_ts INTEGER NOT NULL)")
        rows = []
        for i in range(N_STALLED, N_TOTAL):
            j = i - N_STALLED
            if j < applied_with_receipt:
                st, receipt = "APPLIED", f"RCPT-{i:04d}"
            elif j < applied_with_receipt + applied_without_receipt:
                st, receipt = "APPLIED", ""
            else:
                st, receipt = "RECONCILE_REQUIRED", ""
            rows.append((f"RFC-{i:04d}", "approve", 1, st, None, None, receipt,
                         None, 1785100000 + i))
        con.executemany("INSERT INTO rfc_decision(rfc_id,verdict,revision,state,"
                        "lease_owner,lease_until,receipt_id,operation_key,updated_ts) "
                        "VALUES (?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
        con.close()
    return state


def _armed(fn):
    """فلگ را فقط برای همین فراخوانی روشن می‌کند — هرگز نشتِ env."""
    saved = os.environ.get(ms.LIFECYCLE_FLAG)
    os.environ[ms.LIFECYCLE_FLAG] = "1"
    try:
        return fn()
    finally:
        if saved is None:
            os.environ.pop(ms.LIFECYCLE_FLAG, None)
        else:
            os.environ[ms.LIFECYCLE_FLAG] = saved


#: توکنِ **جعلیِ** تستی — تست هرگز به اعتبارنامهٔ واقعی وابسته نمی‌شود، و
#: هرگز آن را در خروجی نمی‌گذارد. شکلش واقعی است تا اعتبارسنج راضی شود.
FAKE_TOKEN = "123456789:AA" + "y" * 32
FAKE_OWNER = "777"


def _owner_initdata() -> str:
    """initData ِ امضاشدهٔ مالک — همان چیزی که وب‌ویوِ تلگرام می‌فرستد."""
    d = {"auth_date": str(int(time.time()) - 10),
         "user": json.dumps({"id": int(FAKE_OWNER), "first_name": "ari"},
                            ensure_ascii=False)}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(d.items()))
    sec = hmac.new(b"WebAppData", FAKE_TOKEN.encode("utf-8"), hashlib.sha256).digest()
    d["hash"] = hmac.new(sec, dcs.encode("utf-8"), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(d)


def _handle(path: str, *, signed: bool):
    """فراخوانِ gateway با گیتِ خواندنی **روشن** و توکنِ جعلیِ پین‌شده.

    گیت باید صریحاً روشن شود، وگرنه اگر روزی پیش‌فرضش خاموش برگردد این
    تست بی‌صدا «۲۰۰ برای همه» را پاس می‌کند و فکر می‌کنیم گیت را سنجیده‌ایم.
    """
    saved = {k: os.environ.get(k) for k in
             ("TG_CENTER_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID", mg.READ_GATE_FLAG)}
    os.environ["TG_CENTER_BOT_TOKEN"] = FAKE_TOKEN
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = FAKE_OWNER
    os.environ[mg.READ_GATE_FLAG] = "1"
    try:
        headers = {"X-Tg-Init-Data": _owner_initdata()} if signed else {}
        return mg._handle_core("GET", path, headers)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _tree(path: Path):
    return ast.parse(Path(path).read_text("utf-8"))


# ─── ۰: ایزوله ─────────────────────────────────────────────────────────────
def t_fixture_is_never_the_live_tree():
    """هر مسیرِ تحتِ آزمون باید موقت باشد — وگرنه تست درختِ زنده را می‌نویسد."""
    state = _make_state_dir()
    resolved = state.resolve()
    assert LIVE_TREE not in resolved.parents and resolved != LIVE_TREE, \
        f"فیکسچر زیرِ درختِ زنده است: {resolved}"
    assert str(resolved).lower().startswith(tempfile.gettempdir().lower()), \
        f"فیکسچر بیرونِ پوشهٔ موقت ساخته شد: {resolved}"
    live_store = LIVE_TREE / "_ops" / "state" / "pulse" / "pending-cards.json"
    before = _sha(live_store) if live_store.exists() else None
    _armed(lambda: ms.get_lifecycle_state(state_dir=state, now=1785200000.0))
    after = _sha(live_store) if live_store.exists() else None
    assert before == after, "نما ذخیرهٔ زندهٔ کارت‌ها را تغییر داد"


# ─── ۱: تاریکی و نبودِ verb ِ نوشتنی ───────────────────────────────────────
def t_flag_off_the_route_does_not_exist():
    """رأیِ مالک (گامِ ۲۴): پیش‌فرض خاموش ⇒ ۴۰۴، نه ۲۰۰ ِ تهی."""
    saved = os.environ.pop(ms.LIFECYCLE_FLAG, None)
    try:
        st, body, ctype = ms.dispatch_api(ms.LIFECYCLE_PATH)
        assert st == 404, f"مسیرِ فلگ‌خاموش {st} داد نه ۴۰۴"
        assert body == b'{"status":"not_found"}', f"بدنهٔ ۴۰۴ عوض شد: {body!r}"
        assert "json" in ctype, ctype
    finally:
        if saved is not None:
            os.environ[ms.LIFECYCLE_FLAG] = saved


def t_flag_off_opens_no_file_at_all():
    """flag-off یعنی no-op مطلق — نه یک خواندنِ «بی‌ضرر»."""
    def boom(*a, **k):
        raise AssertionError("فلگ خاموش بود ولی منبع خوانده شد")
    saved = os.environ.pop(ms.LIFECYCLE_FLAG, None)
    try:
        out = ms.get_lifecycle_state(state_dir=_make_state_dir(),
                                     _fold=boom, _stalled=boom)
        assert out.get("status") == "disabled", out
        assert "counts" not in out, f"نمای خاموش داده منتشر کرد: {sorted(out)}"
    finally:
        if saved is not None:
            os.environ[ms.LIFECYCLE_FLAG] = saved


def t_this_module_declares_no_write_verb():
    """سطحِ خواندنی حق ندارد صفحهٔ فرمانِ دوم شود — ساختاراً، نه با نیت."""
    src_path = _OPS / "telegram_center" / "miniapp_state.py"
    tree = _tree(src_path)
    verbs = {"POST", "PUT", "DELETE", "PATCH"}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            assert not node.name.upper().startswith("DO_") or \
                node.name.upper()[3:] not in verbs, \
                f"handler ِ نوشتن اضافه شد: {node.name}"
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert node.value.strip().upper() not in verbs, \
                f"رشتهٔ متدِ نوشتن در ماژول: {node.value!r}"
    writes = {"write_text", "write_bytes", "mkdir", "unlink", "rmtree",
              "touch", "makedirs", "remove", "rename", "rmdir"}
    bad = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name in writes:
            bad.add(name)
        if (isinstance(node.func, ast.Attribute) and node.func.attr == "replace"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"):
            bad.add("os.replace")
        if name == "open":
            for arg in list(node.args[1:]) + [k.value for k in node.keywords
                                              if k.arg == "mode"]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                        and set("wax+") & set(arg.value):
                    bad.add("open(mode=w)")
    assert not bad, f"ماژولِ read-only می‌نویسد: {sorted(bad)}"
    sql_bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            up = node.value.upper()
            for verb in ("INSERT ", "UPDATE ", "DELETE ", "CREATE ", "DROP ", "ALTER "):
                if verb in up:
                    sql_bad.append(node.value[:40])
    assert not sql_bad, f"SQL ِ جهش‌دهنده در ماژولِ read-only: {sql_bad}"


def t_dispatcher_takes_no_method_argument():
    """dispatcher ساختاراً GET-only است: پارامترِ متد وجود ندارد."""
    tree = _tree(_OPS / "telegram_center" / "miniapp_state.py")
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "dispatch_api")
    args = [a.arg for a in list(fn.args.args) + list(fn.args.kwonlyargs)]
    assert "method" not in args and "verb" not in args, \
        f"dispatcher متد می‌گیرد ⇒ می‌تواند صفحهٔ فرمان شود: {args}"


# ─── ۲: دیوارِ 405 ─────────────────────────────────────────────────────────
#: متنِ pin‌شدهٔ دیوارِ متد در `miniapp_gateway._handle_core`. هر بایتِ متفاوت
#: یعنی دیوار بازنویسی شده — و همین دیوار (نه بازبینیِ انسانی) تنها چیزی است
#: که امروز هیچ verdict/ارسال/جهشی را از تونلِ عمومی قابلِ رسیدن نمی‌گذارد.
GATEWAY_405_WALL = (
    '    if method_u not in {"GET", "POST"}:\n'
    '        return 405, b"", "text/plain; charset=utf-8"\n'
)
# 2026-08-10: gateway اکنون چند مسیرِ POST مجاز دارد (actions/ask/mirror/restart).
# فهرستِ مجاز از خودِ gateway استخراج می‌شود، ولی سپس **کاملاً pin می‌شود** —
# هر مسیرِ مجازِ نو باید تست را هم به‌روز کند (نه باز یا خودکار).
EXPECTED_POST_ROUTES = frozenset({"/api/actions", "/api/ask", "/api/mirror", "/api/restart"})


def t_gateway_405_wall_is_byte_identical():
    """دیوارِ متد سیاست نمی‌شود — بایت می‌ماند.

    2026-08-10: مسیرهای POST مجاز از actions به actions+ask+mirror+restart
    گسترش یافت (08-08). فهرست از gateway استخراج می‌شود ولی سپس دقیقاً با
    EXPECTED_POST_ROUTES مقایسه می‌شود — اضافه‌شدنِ مسیرِ ناخواسته قرمز می‌شود."""
    import re
    src = (_OPS / "telegram_center" / "miniapp_gateway.py").read_text("utf-8")
    assert GATEWAY_405_WALL in src, \
        "متنِ دیوارِ 405 در miniapp_gateway._handle_core تغییر کرده است"
    # استخراجِ مسیرهای POST مجاز از gateway
    m = re.search(r'method_u == "POST" and p not in \(([^)]+)\)', src)
    assert m, "ساختارِ استثنای POST پیدا نشد — دیوار احتمالاً حذف شده"
    # مسیرهای واقعی را از gateway parse کن
    actual_routes = frozenset(re.findall(r'"(/api/[^"]+)"', m.group(1)))
    assert actual_routes == EXPECTED_POST_ROUTES, \
        f"مسیرهای POST مجاز تغییر کرده: gateway={actual_routes} ≠ expected={EXPECTED_POST_ROUTES}"


def t_write_verbs_on_the_view_are_405_and_the_store_is_byte_identical():
    """POST/PUT/DELETE روی مسیرِ نو ⇒ ۴۰۵، و ذخیرهٔ کارت‌ها بایت‌یکسان."""
    state = _make_state_dir()
    store = state / "pulse" / "pending-cards.json"
    before = _sha(store)
    saved_stop = mg._stopped
    mg._stopped = lambda: False           # کلیدِ کشتار نباید نتیجه را مبهم کند
    try:
        for method in ("POST", "PUT", "DELETE", "PATCH"):
            st, body, _ = mg._handle_core(method, ms.LIFECYCLE_PATH, {})
            assert st == 405, f"{method} روی نما {st} داد نه ۴۰۵"
            assert body == b"", f"{method} بدنه برگرداند: {body!r}"
    finally:
        mg._stopped = saved_stop
    assert _sha(store) == before, "ذخیرهٔ کارت‌ها پس از تلاشِ نوشتن عوض شد"


def t_the_flag_is_the_only_gate_and_it_holds_in_all_three_directions():
    """گیتِ نما — هر سه جهت، چون یک جهت هیچ چیزی ثابت نمی‌کند.

    ⚠️ بازنویسیِ ۰۸-۰۴. نسخهٔ قبلی ادعا می‌کرد whitelist ِ gateway دیوارِ
    **دوم** است و «مسلح‌کردنِ فلگ به‌تنهایی نما را زنده نمی‌کند». آن premise
    دیگر درست نیست: برشِ ۳ عمداً `/api/lifecycle` را به `READ_API_PATHS`
    اضافه کرد (handler وجود داشت ولی هرگز dispatch نمی‌شد). پس امروز
    **فلگ تنها گیت است** و تست باید همین را بگوید، نه چیزی که دیگر نیست.

    و آن تست بی‌امضا صدا می‌زد، پس ۴۰۳ ِ `owner_auth_required` می‌گرفت و
    آن را «تاریکی» می‌خواند — دقیقاً همان خطای «۴۰۳ اثباتِ احراز نیست».
    یک ردِ بی‌امضا هم با «مسیر وجود ندارد» سازگار است هم با «مسیر هست ولی
    در بسته است»؛ فرقشان فقط با امضای **درست** معلوم می‌شود.

    سه جهت:
      ۱. بی‌امضا  ⇒ ۴۰۳ (در بسته است)
      ۲. امضادار + فلگِ خاموش ⇒ ۴۰۴ (تاریکِ واقعی — نه صرفاً ردشده)
      ۳. امضادار + فلگِ روشن ⇒ ۲۰۰ (پس گیت مرده نیست؛ یعنی جهتِ ۲ معنا دارد)
    """
    saved_stop = mg._stopped
    mg._stopped = lambda: False
    try:
        unsigned, _, _ = _handle(ms.LIFECYCLE_PATH, signed=False)
        assert unsigned == 403, f"بی‌امضا {unsigned} داد، انتظار ۴۰۳"

        dark, _, _ = _handle(ms.LIFECYCLE_PATH, signed=True)
        assert dark == 404, f"با امضای درست و فلگِ خاموش {dark} داد — تاریکی شکست"

        lit, body, _ = _armed(lambda: _handle(ms.LIFECYCLE_PATH, signed=True))
        assert lit == 200, (
            f"با امضای درست و فلگِ روشن {lit} داد — یعنی جهتِ ۲ بی‌معنا بود "
            f"و این تست هر رفتاری را پاس می‌کرد")
        assert b"counts" in body, f"بدنهٔ روشن شمارش ندارد: {body[:120]!r}"
    finally:
        mg._stopped = saved_stop


# ─── ۳: whitelist ِ بدنه (byte-grep) ───────────────────────────────────────
def t_serialised_body_carries_zero_card_text_or_token_material():
    """byte-grep روی **بدنهٔ HTTP**، نه بازرسیِ کدِ projection."""
    state = _make_state_dir()
    st, body, ctype = _armed(lambda: ms.dispatch_api(
        ms.LIFECYCLE_PATH, root=state.parent.parent))
    assert st == 200, f"نمای مسلح {st} داد: {body[:200]!r}"
    needles = [b"token_sha256", b"nonce", b"summary", b"owner",
               MARK_TOKEN.encode("utf-8"), MARK_NONCE.encode("utf-8"),
               MARK_OWNER.encode("utf-8"), MARK_SUMMARY.encode("utf-8"),
               b"RFC-0000", b"expires_at", b"rfc_id"]
    hits = [n for n in needles if n in body or n.lower() in body.lower()]
    assert not hits, f"بدنه مادهٔ ممنوع دارد: {hits}"
    assert b"stalled" in body, "بدنه اصلاً شمارشِ راکد ندارد — گرپ کور است"


def t_projection_keys_are_a_closed_whitelist():
    """هر کلیدِ سطحِ بالا باید عمدی باشد؛ کلیدِ تازه بی‌رأی وارد نمی‌شود."""
    state = _make_state_dir()
    out = _armed(lambda: ms.get_lifecycle_state(state_dir=state, now=1785200000.0))
    # ۲۰۲۶-۰۸-۰۶: `stalled_list`/`stalled_list_truncated` به رأیِ مالکِ
    # ۰۸-۰۵ اضافه شدند و این whitelist از قلم افتاده بود — همین غفلت باعثِ
    # نشتِ `rfc_id` شد (رفع‌شده در miniapp_state._lifecycle_public_stalled_rows).
    # حالا که فیلدها بی‌هویت‌اند (فقط `created_ts`/`age_days`)، عمداً اعلام
    # می‌شوند: whitelist باید با خودِ نما هم‌قدم بماند، نه یک بار برای همیشه.
    allowed = {"status", "flag", "sources", "readable", "counts", "by_stage",
               "oldest_stalled_ts", "total_cards",
               "stalled_list", "stalled_list_truncated"}
    assert set(out) <= allowed, f"کلیدِ اعلام‌نشده در نما: {sorted(set(out) - allowed)}"
    assert set(out["counts"]) == set(ms.LIFECYCLE_COUNTS), \
        f"مجموعهٔ شمارش‌ها عوض شد: {sorted(out['counts'])}"
    for name, stamped in out["counts"].items():
        assert set(stamped) <= set(ms.LIFECYCLE_STAMP_KEYS), \
            f"stampِ «{name}» کلیدِ اضافه دارد: {sorted(stamped)}"


def t_sources_are_a_pinned_allowlist_not_derived_text():
    """`sources` تنها فیلدی است که از اسکنِ زیررشته‌ای معاف است — پس باید
    allowlist ِ **دقیق** داشته باشد، وگرنه معافیت خودش یک درِ باز است."""
    state = _make_state_dir()
    out = _armed(lambda: ms.get_lifecycle_state(state_dir=state, now=1785200000.0))
    allowed = set(ms.LIFECYCLE_DECLARED_SOURCES) | {"unlisted-source"}
    assert set(out["sources"]) <= allowed, \
        f"منبعِ اعلام‌نشده منتشر شد: {sorted(set(out['sources']) - allowed)}"
    derived = ms._lifecycle_safe_sources(
        [f"C:/queue/{MARK_OWNER}/{MARK_SUMMARY}.json", MARK_TOKEN])
    assert derived == ["unlisted-source", "unlisted-source"], \
        f"رشتهٔ مشتق‌شده از داده به‌عنوان منبع عبور کرد: {derived}"
    for s in ms.LIFECYCLE_DECLARED_SOURCES:
        for needle in ("token_sha256", "nonce", "summary", "owner", "rfc_id"):
            assert needle not in s.lower(), \
                f"مسیرِ اعلام‌شدهٔ «{s}» خودش شاملِ «{needle}» است"


def t_the_second_wall_refuses_a_leaking_projection():
    """اگر روزی projection نشت کند، `_lifecycle_enforce` باید **استثنا** بدهد."""
    try:
        ms._lifecycle_enforce({"counts": {"stalled": {"summary": "متنِ کارت"}}})
    except ValueError as exc:
        assert "summary" in str(exc), f"پیامِ خطا فیلدِ نشتی را نام نمی‌برد: {exc}"
    else:
        raise AssertionError("دیوارِ دوم یک کلیدِ ممنوع را عبور داد")
    try:
        ms._lifecycle_enforce({"note": MARK_TOKEN + " nonce=x"})
    except ValueError:
        pass
    else:
        raise AssertionError("دیوارِ دوم یک **مقدارِ** ممنوع را عبور داد")


# ─── ۴: عدد باید با پروب یکی باشد، و غیاب UNKNOWN بماند ───────────────────
def t_stalled_equals_the_probe():
    """سنجهٔ پذیرشِ طرح: عددِ نما == عددِ پروبِ C2 (زندهٔ امروز: ۲۰)."""
    state = _make_state_dir()
    probe_count, probe_oldest, probe_total = lf.stalled_cards(state)
    out = _armed(lambda: ms.get_lifecycle_state(state_dir=state, now=1785200000.0))
    view = out["counts"]["stalled"]
    assert "value" in view, f"شمارشِ راکد بی‌مقدار آمد: {view}"
    assert view["value"] == probe_count, \
        f"نما {view['value']} می‌گوید، پروب {probe_count}"
    assert view["value"] == N_STALLED, \
        f"فیکسچرِ هم‌شکلِ درختِ زنده باید {N_STALLED} بدهد، داد {view['value']}"
    assert out["oldest_stalled_ts"].get("value") == probe_oldest, \
        f"قدیمی‌ترینِ راکد با پروب یکی نیست: {out['oldest_stalled_ts']}"
    assert out["total_cards"].get("value") == probe_total == N_TOTAL, \
        f"شمارِ کلِ کارت‌ها با پروب یکی نیست: {out['total_cards']}"


def t_a_renamed_decision_field_renders_unknown_not_a_clean_zero():
    """اینجا `fold` و پروب **واقعاً** واگرا می‌شوند — و نما باید طرفِ پروب بایستد.

    اگر کلیدِ `decision` روزی نام عوض کند، `fold` هر رکورد را `UNKNOWN` طبقه
    می‌کند و `stalled` را یک **صفرِ تمیزِ LIVE** می‌دهد؛ `stalled_cards` همان
    حالت را `-1` (UNKNOWN) اعلام می‌کند. دقیقاً همان تلهٔ predicate مرده که
    این طرح آمده ببندد — پس عددِ نما باید از پروب بیاید، نه از fold.
    """
    state = _make_state_dir(decision_key="decision_state")
    probe_count, _, probe_total = lf.stalled_cards(state)
    assert probe_count == -1, f"فیکسچرِ واگرایی نساخت؛ پروب {probe_count} داد"
    folded = lf.fold(state, now=1785200000.0)
    assert folded["stalled"].get("value") == 0 and folded["stalled"]["mode"] == "LIVE", \
        f"fold دیگر صفرِ تمیز نمی‌دهد — این تست باید بازنویسی شود: {folded['stalled']}"

    out = _armed(lambda: ms.get_lifecycle_state(state_dir=state, now=1785200000.0))
    view = out["counts"]["stalled"]
    assert view.get("mode") == "UNKNOWN", \
        f"نما صفرِ fold را باور کرد به‌جای UNKNOWN ِ پروب: {view}"
    assert "value" not in view, f"نما روی کلیدِ گم‌شده مقدار منتشر کرد: {view}"
    assert "value" not in out["total_cards"], \
        f"شمارِ کل روی ذخیرهٔ نامفهوم مقدار داد: {out['total_cards']} (پروب {probe_total})"


def t_effected_is_zero_only_when_a_receipt_is_missing():
    """«APPLIED بدونِ رسید، اثر نیست» — نما همان قرارداد را منتشر می‌کند."""
    dark = _make_state_dir(applied_without_receipt=3)
    out = _armed(lambda: ms.get_lifecycle_state(state_dir=dark, now=1785200000.0))
    assert out["counts"]["effected"].get("value") == 0, \
        f"APPLIED ِ بی‌رسید به‌عنوان اثر شمرده شد: {out['counts']['effected']}"
    lit = _make_state_dir(applied_with_receipt=3)
    out2 = _armed(lambda: ms.get_lifecycle_state(state_dir=lit, now=1785200000.0))
    assert out2["counts"]["effected"].get("value") == 3, \
        f"سه رسیدِ ناتهی دیده نشد: {out2['counts']['effected']}"
    assert out2["counts"]["decided"].get("value") == N_DECIDED, \
        f"شمارشِ decided جابه‌جا شد: {out2['counts']['decided']}"


def t_absence_renders_unknown_never_zero():
    """ذخیرهٔ غایب ≠ صفر کارت. stampِ UNKNOWN کلیدِ `value` ندارد."""
    empty = _make_state_dir(cards=False, verdicts=False)
    out = _armed(lambda: ms.get_lifecycle_state(state_dir=empty, now=1785200000.0))
    for name in ms.LIFECYCLE_COUNTS:
        stamped = out["counts"][name]
        assert stamped.get("mode") == "UNKNOWN", \
            f"«{name}» روی ذخیرهٔ غایب {stamped.get('mode')} شد نه UNKNOWN"
        assert "value" not in stamped, \
            f"«{name}» روی غیاب مقدار منتشر کرد: {stamped}"
    assert out["by_stage"].get("mode") == "UNKNOWN", out["by_stage"]
    assert "value" not in out["by_stage"], \
        f"by_stage روی غیاب صفرهای جعلی داد: {out['by_stage']}"
    assert out["readable"] is False, out["readable"]
    body = json.dumps(out, ensure_ascii=False).encode("utf-8")
    assert b'"value": 0' not in body and b'"value":0' not in body, \
        "غیاب به صفر رندر شد — دقیقاً همان باگی که این نما آمده ببندد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_miniapp_lifecycle_view: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
