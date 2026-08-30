"""test_state_write_monopoly — دقیقاً یک ماژول حق دارد `ORGANISM-STATE.json` را بنویسد.

گامِ ۱۱ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C12).

چرا ساختاری و نه انضباطی: «دو نویسنده روی یک فایلِ حالت» گران‌ترین باگِ تکرارشوندهٔ
این ارگانیسم است — چهار حادثه در چهار روز (نوسانِ کارت‌های گروه، حادثهٔ دو مرکز روی
یک توکن، نشانگرهای flush، و مورد چهارم در دایجست). هر بار در **تولید** کشف شد، نه
در مرور. این گارد کشف را به زمانِ تست می‌آورد.

اهمیتش همین حالا بیشتر می‌شود: گامِ ۱۷ (`proposal_metrics`) قرار است در همین فایل
بنویسد. گارد **پیش از** آن می‌نشیند تا اگر آن گام نویسندهٔ دوم بسازد، همان‌جا قرمز شود.

دو حالت پوشش داده می‌شود و هرکدام جدا جهش‌آزموده است:
  · مستقیم   — `LockedJson(STATE_FILE)`، `open(STATE_FILE,"w")`، `.write_text(...)`
  · غیرمستقیم — helperی که `STATE_FILE` را به‌عنوان آرگومان می‌گیرد (این همان راهی
                است که یک نویسندهٔ دوم معمولاً از کنارِ گاردِ ساده رد می‌شود)

گارد روی یک درختِ **دلخواه** کار می‌کند، پس خودش روی فیکسچر آزمون‌پذیر است — درسِ
«گاردی که برای آزمودنش باید درختِ زنده را بشکنی، هیچ‌وقت آزموده نمی‌شود».
"""
import ast
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("state-write-monopoly")

_OPS = harness.SELF_OPS

STATE_BASENAME = "ORGANISM-STATE.json"

#: تنها ورودیِ مجاز. اگر روزی دومی لازم شد، افزودنش باید یک تصمیمِ آگاهانه باشد
#: که در همین خط دیده شود — نه چیزی که در یک ماژولِ دور اتفاق بیفتد.
ALLOWLIST = {("organism.py", "_write_state")}

#: صدازدن‌هایی که گرفتنِ مسیر در آن‌ها نوشتن نیست.
READONLY_CALLEES = {
    "exists", "is_file", "stat", "read_text", "read_bytes", "resolve",
    "str", "Path", "len", "print", "_j", "loads", "load", "getmtime",
    "relative_to", "as_posix", "samefile", "iterdir",
}

WRITE_METHODS = {"write_text", "write_bytes", "unlink", "touch", "rename", "replace"}
WRITE_CTORS = {"LockedJson"}


def _skip(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return bool(parts & {"__pycache__", "tests", "patch_backups", ".git", "_archive"})


def _state_names(tree):
    """نام‌هایی که در این ماژول به فایلِ حالت اشاره می‌کنند."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            src = ast.dump(node.value)
            if STATE_BASENAME in src:
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        names.add(tgt.id)
    return names


def _enclosing(tree):
    """نگاشتِ node → نامِ تابع/کلاسِ دربرگیرنده، برای گزارشِ `file:symbol`."""
    owner = {}
    def walk(node, name):
        for child in ast.iter_child_nodes(node):
            nm = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                  ast.ClassDef)) else name
            owner[id(child)] = nm
            walk(child, nm)
    owner[id(tree)] = "<module>"
    walk(tree, "<module>")
    return owner


def _is_state_ref(node, names):
    if isinstance(node, ast.Name) and node.id in names:
        return True
    if isinstance(node, ast.Constant) and isinstance(node.value, str) \
            and STATE_BASENAME in node.value:
        return True
    if isinstance(node, ast.BinOp) and STATE_BASENAME in ast.dump(node):
        return True
    return False


def find_writers(root: Path):
    """هر نوشتنِ مستقیم یا غیرمستقیم روی فایلِ حالت. برمی‌گرداند [(file, symbol, kind)]."""
    found = []
    for path in sorted(root.rglob("*.py")):
        if _skip(path.relative_to(root)):
            continue
        try:
            src = path.read_text("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if STATE_BASENAME not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        names = _state_names(tree)
        owner = _enclosing(tree)
        rel = path.relative_to(root).as_posix()
        # نقشهٔ توابعِ همین ماژول، برای دنبال‌کردنِ یک‌سطحیِ پاس‌دادنِ مسیر
        local_funcs = {n.name: n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            callee = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            sym = owner.get(id(node), "<module>")
            # مستقیم: سازندهٔ نویسنده، یا open با حالتِ نوشتن
            if callee in WRITE_CTORS and any(_is_state_ref(a, names) for a in node.args):
                found.append((rel, sym, f"direct:{callee}"))
                continue
            if callee == "open" and any(_is_state_ref(a, names) for a in node.args):
                mode = ""
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = str(node.args[1].value)
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if any(c in mode for c in "wax+"):
                    found.append((rel, sym, "direct:open"))
                continue
            # مستقیم: متدِ نوشتنِ خودِ مسیر
            if callee in WRITE_METHODS and isinstance(node.func, ast.Attribute) \
                    and _is_state_ref(node.func.value, names):
                found.append((rel, sym, f"direct:{callee}"))
                continue
            # غیرمستقیم: مسیر را به تابعی پاس داد که **خودش می‌نویسد**.
            #
            # نسخهٔ اولِ این شاخه هر پاس‌دادنی را نقص می‌شمرد و ۱۱ خوانندهٔ سالم را
            # گرفت (`_read_json`، `_read_json_safe`، حتی `isinstance`). گاردی که
            # خواننده را نویسنده بخواند، همان‌قدر بی‌فایده است که گاردی که نویسنده
            # را نبیند — فقط پرسروصداتر. پس یک سطح دنبالِ تابع می‌رویم.
            if not callee:
                continue
            arg_idx = None
            for i, a in enumerate(node.args):
                if _is_state_ref(a, names):
                    arg_idx = i
                    break
            if arg_idx is None:
                if not any(_is_state_ref(k.value, names) for k in node.keywords):
                    continue
            target = local_funcs.get(callee)
            if target is not None:
                if _param_is_written(target, arg_idx):
                    found.append((rel, sym, f"indirect:{callee}"))
            elif callee in WRITE_CTORS or callee in WRITE_HINTS:
                # تابعِ بیرونی که نامش نوشتن را اعلام می‌کند
                found.append((rel, sym, f"indirect:{callee}"))
    return found


WRITE_HINTS = {"dump", "save", "persist", "atomic_write", "write_json", "store"}


def _param_is_written(fn, arg_idx):
    """آیا این تابع روی پارامترِ شمارهٔ arg_idx می‌نویسد؟ (یک سطح، بدونِ بازگشت)"""
    params = [a.arg for a in fn.args.args]
    if arg_idx is None or arg_idx >= len(params):
        # آرگومانِ کلیدواژه‌ای یا خارج از دامنه — محافظه‌کارانه همهٔ پارامترها را بسنج
        candidates = set(params)
    else:
        candidates = {params[arg_idx]}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        c = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        refs = [a for a in node.args if isinstance(a, ast.Name) and a.id in candidates]
        if c in WRITE_CTORS and refs:
            return True
        if c == "open" and refs:
            mode = ""
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(ch in mode for ch in "wax+"):
                return True
        if c in WRITE_METHODS and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id in candidates:
            return True
    return False


def _fixture(files: dict):
    root = Path(tempfile.mkdtemp(prefix="write-monopoly-"))
    assert str(_OPS).lower() not in str(root).lower(), f"fixture inside live tree: {root}"
    for name, body in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return root


_SOLE = '''
import opslib
STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"

def _write_state(extra):
    with opslib.LockedJson(STATE_FILE) as lj:
        lj.data.update(extra)
'''


def t_the_live_tree_has_exactly_one_writer():
    """سنجهٔ اصلی، روی درختِ واقعی."""
    writers = find_writers(_OPS)
    offenders = [(f, s, k) for (f, s, k) in writers if (f, s) not in ALLOWLIST]
    assert not offenders, (
        "نویسندهٔ غیرمجاز روی ORGANISM-STATE.json:\n  " +
        "\n  ".join(f"{f}::{s}  [{k}]" for f, s, k in offenders))
    assert any((f, s) in ALLOWLIST for f, s, _ in writers), \
        f"نویسندهٔ مجاز پیدا نشد — گارد دارد در خلأ سبز می‌شود: {writers}"


def t_fixture_with_the_sole_writer_is_clean():
    root = _fixture({"organism.py": _SOLE})
    try:
        offenders = [w for w in find_writers(root) if (w[0], w[1]) not in ALLOWLIST]
        assert not offenders, offenders
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_a_second_direct_writer_is_caught_with_file_and_symbol():
    """جهشِ سند، حالتِ مستقیم."""
    root = _fixture({
        "organism.py": _SOLE,
        "sneaky.py": '''
import opslib
P = opslib.STATE_DIR / "ORGANISM-STATE.json"

def stamp_something(v):
    with opslib.LockedJson(P) as lj:
        lj.data["x"] = v
''',
    })
    try:
        offenders = [w for w in find_writers(root) if (w[0], w[1]) not in ALLOWLIST]
        assert offenders, "نویسندهٔ دومِ مستقیم گرفته نشد"
        files = {f for f, _, _ in offenders}
        syms = {s for _, s, _ in offenders}
        assert "sneaky.py" in files, offenders
        assert "stamp_something" in syms, f"نامِ نماد گزارش نشد: {offenders}"
        # نوعِ آشکارسازی هم قفل می‌شود، نه فقط اینکه «گرفته شد».
        #
        # چرا: جهشِ اولِ من آشکارسازِ مستقیم را کور کرد و تست **سبز ماند** — چون
        # همان مورد از تورِ غیرمستقیم گرفته شد (`LockedJson` در WRITE_CTORS است).
        # دفاعِ لایه‌ای خوب است، ولی اگر تست نوع را نسنجد، پوسیدنِ لایهٔ اول
        # نامرئی می‌ماند و روزی که لایهٔ دوم هم عوض شود هیچ‌کس خبردار نمی‌شود.
        kinds = {k for _, _, k in offenders}
        assert "direct:LockedJson" in kinds, \
            f"باید به‌عنوان مستقیم آشکار شود، نه فقط گرفته شود: {sorted(kinds)}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_an_indirect_writer_is_caught_too():
    """جهشِ سند، حالتِ **غیرمستقیم** — همان راهی که از کنارِ گاردِ ساده رد می‌شود."""
    root = _fixture({
        "organism.py": _SOLE,
        "helper.py": '''
import opslib
P = opslib.STATE_DIR / "ORGANISM-STATE.json"

def _persist(path, payload):
    with opslib.LockedJson(path) as lj:
        lj.data.update(payload)

def publish(payload):
    _persist(P, payload)
''',
    })
    try:
        offenders = [w for w in find_writers(root) if (w[0], w[1]) not in ALLOWLIST]
        kinds = {k for _, _, k in offenders}
        assert offenders, "نوشتنِ غیرمستقیم گرفته نشد"
        assert any(k.startswith("indirect") for k in kinds), \
            f"به‌عنوان غیرمستقیم برچسب نخورد: {offenders}"
        assert "publish" in {s for _, s, _ in offenders}, offenders
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_write_text_on_the_state_file_is_caught():
    root = _fixture({
        "organism.py": _SOLE,
        "blunt.py": '''
import json, opslib
P = opslib.STATE_DIR / "ORGANISM-STATE.json"

def dump_it(d):
    P.write_text(json.dumps(d), encoding="utf-8")
''',
    })
    try:
        offenders = [w for w in find_writers(root) if (w[0], w[1]) not in ALLOWLIST]
        assert any(k == "direct:write_text" for _, _, k in offenders), offenders
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_readers_are_not_flagged():
    """جفتِ لازم: گاردی که خواننده‌ها را هم بگیرد، بی‌فایده و پرسروصداست."""
    root = _fixture({
        "organism.py": _SOLE,
        "reader.py": '''
import json, opslib
P = opslib.STATE_DIR / "ORGANISM-STATE.json"

def look():
    if P.exists():
        return json.loads(P.read_text("utf-8"))
    return {}
''',
    })
    try:
        offenders = [w for w in find_writers(root) if (w[0], w[1]) not in ALLOWLIST]
        assert not offenders, f"خواننده به‌اشتباه نویسنده شمرده شد: {offenders}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_allowlist_is_exactly_one_entry():
    """اگر روزی دومی اضافه شد، باید در همین خط دیده شود."""
    assert len(ALLOWLIST) == 1, f"allowlist بیش از یک ورودی دارد: {ALLOWLIST}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_state_write_monopoly: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
