"""test_capability_registry — سطحِ تلگرام دیگر از بدنِ ارگانیسم عقب نمی‌ماند.

مسئله‌ای که این ماژول حل می‌کند ساختاری است، نه موردی: تا امروز هر توانایی باید
دستی به `center.py` سیم می‌شد، پس هر ماژولِ تازه پیش‌فرضاً نامرئی بود و شکاف با
گذرِ زمان **بزرگ‌تر** می‌شد. شمارشِ ۲۰۲۶-۰۷-۲۷: ۱۰ کارتِ بی‌آرگومان وجود داشت و
فقط ۳ تا از تلگرام باز می‌شد.

پس مهم‌ترین ناوردیِ این فایل این است: **ماژولِ بعدی هم بدونِ لمسِ هیچ فایلی پیدا
شود.** تستی که فقط امروز را بسنجد، همان کژی را دوباره می‌سازد.

و دو مرزِ امنیتی که کشفِ پویا می‌آورد:
  · کلیدِ ورودی هرگز مستقیم به `import` نرود (allowlistِ مشتق از اسکن).
  · کشف هیچ ماژولی را import نکند (وگرنه اثرِ جانبیِ ۲۵۰ import را اجرا کرده‌ایم).
"""
import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("capability-registry")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import capability_registry as cr   # noqa: E402


# ─── ۱: کشف عقب نمی‌ماند ───────────────────────────────────────────────────
def t_discovery_finds_every_zero_arg_card_in_the_tree():
    """قلبِ ماژول. اگر این بشکند، یعنی توانایی‌ای ساخته شده و نامرئی مانده.

    مرجع مستقلاً از خودِ درخت ساخته می‌شود — نه از فهرستی که کد نگه می‌دارد —
    وگرنه تست فقط ادعای کد را تکرار می‌کند."""
    # ⚠️ مرجع از `cr.SCAN_DIRS` ساخته **نمی‌شود**. نسخهٔ اول همین کار را کرد و
    # جهشِ عمدیِ «فقط ریشه را اسکن کن» را نگرفت — چون مرجع هم با کد کوچک شد.
    # تستی که ثابتِ خودِ کد را به‌عنوان حقیقت بخواند، فقط ادعای کد را تکرار
    # می‌کند. پس کلِ درخت مستقلاً پیمایش می‌شود.
    import warnings
    expect = set()
    for f in sorted(_OPS.rglob("*.py")):
        if set(f.parts) & {"tests", "_code", ".git", "__pycache__",
                           "_Archive", "_Duplicates"} or f.name.startswith("test_"):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(f.read_text("utf-8"))
        except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
            continue
        for n in tree.body:
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if n.name != "card":
                continue
            a = n.args
            req = [x for x in a.args if x.arg not in ("self", "cls")]
            if len(req) - len(a.defaults) <= 0 and not any(
                    d is None for d in (a.kw_defaults or [])):
                expect.add(f.stem)
    found = {r["key"] for r in cr.discover(refresh=True)}
    assert found == expect, f"جاافتاده: {expect - found} · اضافه: {found - expect}"
    assert len(found) >= 8, f"کشف ناگهان کوچک شد: {len(found)}"


def t_a_card_that_needs_arguments_is_correctly_excluded():
    """کارتی که ورودی می‌خواهد از منوی عمومی باز نمی‌شود — و نباید بشود."""
    found = {r["key"] for r in cr.discover(refresh=True)}
    for k in ("decision_gate", "initiative", "mirror_room", "negotiate", "ask_brain"):
        assert k not in found, f"«{k}» آرگومان لازم دارد ولی در فهرستِ عمومی آمد"


def t_discovery_imports_nothing():
    """کشف باید ارزان و بی‌ضرر باشد. importِ ۲۵۰ ماژول یعنی اجرای هر اثرِ
    جانبیِ import-time — از جمله شبکه و نوشتنِ فایل."""
    before = set(sys.modules)
    cr.discover(refresh=True)
    new = set(sys.modules) - before - {"warnings"}
    leaked = [m for m in new if not m.startswith(("_", "encodings", "importlib"))]
    assert not leaked, f"کشف ماژول وارد کرد: {leaked[:6]}"


# ─── ۲: مرزِ امنیتی ────────────────────────────────────────────────────────
def t_an_arbitrary_key_can_never_reach_import():
    for bad in ("../../etc/passwd", "os", "subprocess", "_ops.secrets",
                "telegram_center.tg_api", "", None, "..", "\\\\net\\share"):
        out = cr.render(bad)
        assert "چنین توانایی‌ای نیست" in out, (bad, out[:60])


def t_only_discovered_keys_render():
    keys = [r["key"] for r in cr.discover(refresh=True)]
    for k in keys:
        out = cr.render(k)
        assert isinstance(out, str) and out.strip(), k


def t_a_broken_card_does_not_kill_the_menu():
    """یک کارتِ خراب نباید بقیه را ببرد — منو باید تاب بیاورد."""
    real = cr.discover
    try:
        cr._cache = None
        rows = real(refresh=True) + [{"key": "__ghost__", "module": "__ghost__",
                                      "path": "__ghost__.py", "title": "شبح",
                                      "flag": "", "flag_on": True}]
        cr.discover = lambda refresh=False: rows
        out = cr.render("__ghost__")
        assert "باز نشد" in out and "بقیهٔ کارت‌ها سالم‌اند" in out, out
    finally:
        cr.discover = real
        cr._cache = None


# ─── ۳: صداقتِ کارت ────────────────────────────────────────────────────────
def t_the_card_distinguishes_live_from_dark():
    """مالک باید **قبل** از بازکردن بداند کارت محتوا دارد یا فقط «خاموشم»."""
    body = cr.card()
    c = cr.coverage()
    assert str(c["total"]) in body
    if c["dark"]:
        assert "خاموش" in body, body
    assert "نکنی:" in body


def t_coverage_numbers_are_consistent():
    c = cr.coverage()
    rows = cr.discover()
    assert c["total"] == len(rows)
    assert c["live"] + c["dark"] == c["total"]
    assert set(c["dark_keys"]) <= {r["key"] for r in rows}


def t_a_flag_flip_moves_a_card_between_live_and_dark():
    """عدد باید **زنده** باشد نه عکسِ لحظهٔ نوشتن."""
    row = next((r for r in cr.discover(refresh=True) if r["flag"]), None)
    assert row is not None, "هیچ کارتِ فلگ‌داری نیست — تست بی‌معنی"
    was = cr.coverage()["live"]
    os.environ[row["flag"]] = "1"
    try:
        now = cr.coverage.__wrapped__() if hasattr(cr.coverage, "__wrapped__") else None
        cr._cache = None
        assert cr.coverage()["live"] > was, "فلگ روشن شد ولی عدد تکان نخورد"
    finally:
        os.environ.pop(row["flag"], None)
        cr._cache = None


def t_a_dark_card_shows_the_exact_way_to_turn_it_on():
    """کارتِ خاموش نباید بن‌بست باشد.

    قبلاً فقط می‌گفت «خاموشم» — مالک می‌دید چیزی هست ولی هیچ راهی نداشت.
    حالا که عبارتِ مجوز واقعاً ثبت می‌شود، همان جمله نشان داده می‌شود و مسیر
    کامل می‌شود: می‌بینم ← می‌دانم چه بنویسم ← می‌نویسم ← می‌ماند."""
    dark = next((r for r in cr.discover(refresh=True)
                 if r["flag"] and not r["flag_on"]), None)
    assert dark is not None, "هیچ کارتِ خاموشی نیست — تست بی‌معنی"
    out = cr.render(dark["key"])
    assert "OWNER_AUTH: ARM FLAG" in out, out[-200:]
    assert dark["flag"] in out, out[-200:]
    # و همان جمله باید واقعاً توسطِ ثبت‌کننده شناخته شود — وگرنه دستورالعملی
    # داده‌ایم که به هیچ‌جا نمی‌رسد.
    sys.path.insert(0, str(_OPS))
    import owner_auth_log as oa
    line = [ln for ln in out.splitlines() if "ARM FLAG" in ln][0]
    line = line.replace("<code>", "").replace("</code>", "")
    hit = oa.parse(line)
    assert hit and hit["kind"] == "ARM_FLAG" and hit["arg"] == dark["flag"], (line, hit)


def t_a_live_card_is_not_polluted_with_unlock_text():
    live = next((r for r in cr.discover(refresh=True) if r["flag_on"]), None)
    assert live is not None
    assert "OWNER_AUTH" not in cr.render(live["key"])


def t_the_unlock_hint_is_text_not_a_button():
    """دکمه یعنی یک تپ فلگ را بچرخاند — و مسلح‌کردن عملِ استقرار است نه پیام."""
    src = Path(cr.__file__).read_text("utf-8")
    i = src.index("OWNER_AUTH: ARM FLAG")
    around = src[max(0, i - 600):i + 400]
    assert "callback_data" not in around, "راهنمای مسلح‌کردن دکمه شد"


# ─── ۴: صفحه‌کلید ──────────────────────────────────────────────────────────
def t_every_capability_is_reachable_through_paging():
    """اگر ردیفی در هیچ صفحه‌ای نیاید، همان کژیِ قبلی است با لباسِ نو."""
    rows = cr.discover(refresh=True)
    seen, page = set(), 0
    while page < 50:
        kb = cr.keyboard(page)
        keys = [b["callback_data"].split(":", 2)[2] for row in kb for b in row
                if b["callback_data"].startswith("x:c:")]
        if not keys:
            break
        seen.update(keys)
        if not any(b["callback_data"].startswith("x:p:") and
                   int(b["callback_data"].split(":")[2]) > page
                   for row in kb for b in row):
            break
        page += 1
    assert seen == {r["key"] for r in rows}, {r["key"] for r in rows} - seen


def t_callback_data_respects_the_64_byte_limit():
    for page in (0, 1, 2):
        for row in cr.keyboard(page):
            for b in row:
                assert len(b["callback_data"].encode()) <= 64, b


def t_hostile_page_numbers_do_not_crash():
    for p in (-5, 0, 999, "x", None, 2.5):
        kb = cr.keyboard(p)
        assert isinstance(kb, list) and kb


# ─── ۵: مرزِ ماژول ─────────────────────────────────────────────────────────
def t_the_registry_only_shows_never_acts():
    tree = ast.parse(Path(cr.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "shutil"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("unlink", "write_text", "rmtree", "system", "run", "send", "apply"):
        assert d not in called, f"فهرستِ فقط‌ناظر عمل می‌کند: {d}"


def t_forbidden_directories_are_never_scanned():
    for bad in ("_code", ".git", "tests", "_Archive", "_Duplicates"):
        assert bad in cr._SKIP_PARTS, bad
    assert not any("test" in r["path"] for r in cr.discover())


# ─── ۶: خودآگاهی ──────────────────────────────────────────────────────────
def t_self_knowledge_knows_how_visible_it_is():
    """سطحِ نامرئی، از دیدِ مالک، با نبودن فرقی ندارد — پس باید در تصویرِ خودِ
    سیستم بنشیند، وگرنه می‌تواند ده کارتِ بازنشدنی بسازد و «سالم» گزارش دهد."""
    sys.path.insert(0, str(_OPS / "doctor"))
    sys.path.insert(0, str(_OPS / "cortex"))
    import self_knowledge as sk
    snap = sk.snapshot()
    surf = snap.get("surface") or {}
    assert surf.get("cards_total"), surf
    assert surf["cards_total"] == cr.coverage()["total"]
    # و باید hash را عوض کند، وگرنه پشتِ `cached:no-change` یخ می‌زند
    d = sk._hash_digest(snap)
    assert "surface_live" in d and "surface_total" in d, d


# ─── ۷: دفترِ اثرها (ب-۴، ۲۰۲۶-۰۸-۰۷) ───────────────────────────────────────
def t_card_shows_a_summary_line_when_effects_ledger_has_rows():
    """`capabilities.effects()` تا حالا صفر خوانندهٔ تولیدی داشت — دفترِ
    `capability-effects.jsonl` از طریقِ `record_effect` نوشته می‌شد ولی هرگز
    نمایش داده نمی‌شد. این تست قفل می‌کند که `card()` اکنون یک خطِ خلاصه
    («N اثرِ اخیر») می‌سازد وقتی دفتر ردیف دارد.

    با monkeypatch روی `_ledger_path` کار می‌کند تا به دفترِ زنده وابسته نباشد."""
    import tempfile, json
    import capabilities as cap
    orig = cap._ledger_path
    try:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "cap-effects.jsonl"
            with open(ledger, "w", encoding="utf-8") as fh:
                for rec in (
                    {"schema": "capability.v1.effect", "ts": "2026-08-07T10:00:00",
                     "capability": "shell.raw", "action": "git status", "ok": True,
                     "detail": ""},
                    {"schema": "capability.v1.effect", "ts": "2026-08-07T10:01:00",
                     "capability": "shell.raw", "action": "rm -rf", "ok": False,
                     "detail": "denied"},
                ):
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            cap._ledger_path = lambda: ledger
            body = cr.card()
            assert "اثرِ اخیر" in body, "خطِ خلاصهٔ اثرها ظاهر نشد"
            assert "2" in body, "شمارِ اثرها در خط نیست"
            # شکست باید دیده شود: ۱ ok + ۱ fail
            assert "✗" in body or "‹" in body, "شکستِ effect در خلاصه دیده نشد"
    finally:
        cap._ledger_path = orig


def t_card_hides_the_effects_line_when_ledger_is_empty():
    """وقتی دفتر خالی است (یا نیست)، خط نباید ظاهر شود — نباید «۰ اثر» بنویسد
    که نویز است. fail-soft هم: نبودِ دفتر = سکوت."""
    import tempfile
    import capabilities as cap
    orig = cap._ledger_path
    try:
        with tempfile.TemporaryDirectory() as td:
            cap._ledger_path = lambda: Path(td) / "nonexist.jsonl"
            body = cr.card()
            assert "اثرِ اخیر" not in body, "دفترِ خالی خطِ اثرها چاپ کرد — نویز"
            assert "نکنی:" in body, "خطِ اصلیِ کارت گم شد"
    finally:
        cap._ledger_path = orig


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_capability_registry: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
