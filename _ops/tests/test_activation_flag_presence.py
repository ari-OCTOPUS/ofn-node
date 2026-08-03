"""test_activation_flag_presence — یک فایلِ مسلح‌سازیِ باربر نباید بی‌صدا کشته شود.

گامِ ۷ ِ UNIFICATION-DESIGN-2026-08-03. موقعیتِ اندازه‌گیری‌شده‌ای که این تست را لازم کرد:

  · `_ops/state/pulse/heartstate-latest.json` هر ضربان نوشته می‌شود (در جلسهٔ ۰۸-۰۳ ‏`ts` اش
    از `16:01:30` به `16:04:16` رفت و `written: true` دارد).
  · نویسنده‌اش `heart/heartstate.py::persist` است، پشتِ `heart/heartstate.py::enabled`.
  · `enabled()` دو راه دارد: env ِ `HEARTSTATE_SHADOW` **یا** وجودِ *فایلِ*
    `heart/heartstate.py::_FLAG_FILE` = `_ops/ACTIVATION-HEARTSTATE.flag`.
  · نامِ env در هیچ‌کدام از ۴ فایلِ `_ops/state/flags-loaded-*.json` نیست، و فایل از
    `2026-07-23` لمس نشده.

پس یک ممیزیِ فلگ این قابلیت را «خاموش» می‌خواند در حالی که هر ~یک دقیقه می‌نویسد، و هر کسی که
آن فایلِ به‌ظاهر بیات را «تمیز» کند یک نویسندهٔ زنده را می‌کشد — بدونِ هیچ diff ای، چون
`.gitignore` خطِ `_ops/ACTIVATION-*.flag` را دارد و این فایل‌ها اصلاً tracked نیستند.

قرارداد این فایل:

  ۱. مجموعهٔ فلگ‌ها **کشف** می‌شود (AST روی `_ops/**/*.py`)، دستی نوشته نمی‌شود.
  ۲. مرجعِ tracked ِ رأی‌ها `_ops/ACTIVATION-FLAGS.md` است؛ `audit()` سه مجموعهٔ
     «منبع / دیسک / رجیستری» را برابر نگه می‌دارد.
  ۳. مسیرِ قرمز روی یک **رونوشتِ موقت** اثبات می‌شود. این تست هرگز چیزی زیرِ `_ops` ِ
     واقعی نمی‌سازد و حذف نمی‌کند.
  ۴. تازگی از `_ops/provenance.py` قرض گرفته می‌شود، بازاختراع نمی‌شود: mtime ِ یک فایلِ
     مسلح‌سازی صادقانه `UNKNOWN/mtime-only` است، نه شاهدِ «مرده».
"""
import ast
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness                                    # noqa: E402
ENV = harness.setup("activation-flag-presence")
_OPS = harness.SELF_OPS                           # کدِ زیرِ تست (worktree)

for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "heart")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import provenance                                 # noqa: E402
import heartstate                                 # noqa: E402  (فلگش داخلِ ops ِ موقتِ harness)

# فلگ‌ها **داده** اند (رأیِ مالک)، نه کد: مثل بقیهٔ harness از درختِ زنده خوانده می‌شوند،
# در حالی که منبع و رجیستری از worktree می‌آیند. در درختِ زنده هر دو یکی‌اند.
_LIVE_OPS = (harness.REAL_VAULT / "_ops").resolve()
_REGISTRY = _OPS / "ACTIVATION-FLAGS.md"

FLAG_GLOB = "ACTIVATION-*.flag"
FLAG_RE = re.compile(r"ACTIVATION-[A-Za-z0-9_-]+\.flag")
RAISED, CLOSED = "RAISED", "CLOSED"

# `tests/` فلگ‌های خیالی به‌عنوان فیکسچر می‌سازد (`ACTIVATION-TEST/X/ABSENT.flag` در
# `tests/test_go_live.py`) و `patch_backups/` رونوشتِ بایگانیِ کد است — هیچ‌کدام خوانندهٔ
# تولیدی نیستند. هر دو با دلیل کنار گذاشته می‌شوند، نه با سلیقه.
SCAN_SKIP_DIRS = frozenset({"tests", "patch_backups"})


# ─── کشفِ ارجاع‌ها از منبع (AST، نه فهرستِ دستی) ──────────────────────────────
def _docstring_ids(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                out.add(id(body[0].value))
    return out


_SCAN_CACHE = {}


def scan_source(ops_dir):
    """(refs, syms, unparsed) از `ops_dir/**/*.py`.

    refs: {نامِ فلگ -> {مسیرِ نسبی، ...}}  ·  syms: {نامِ فلگ -> {"rel.py::SYMBOL", ...}}
    فقط رشته‌های **غیرِ docstring** می‌شمارند (docstring نثر است نه خواننده)، و الگوهای
    wildcard مثل `ACTIVATION-*.flag` طبیعتاً match نمی‌کنند چون `*` در کلاسِ نام نیست.
    """
    key = str(Path(ops_dir).resolve())
    if key in _SCAN_CACHE:
        return _SCAN_CACHE[key]
    refs, syms, unparsed = {}, {}, []
    for path in sorted(Path(ops_dir).rglob("*.py")):
        rel = path.relative_to(ops_dir)
        if SCAN_SKIP_DIRS & set(rel.parts[:-1]):
            continue
        rel_s = rel.as_posix()
        try:
            # utf-8-sig چون ۴ فایلِ `agi2027_control/*` BOM دارند و با utf-8 خالص
            # SyntaxError می‌دهند — یک فایلِ بی‌صدا رد شده = نقطهٔ کورِ اسکن.
            tree = ast.parse(path.read_text("utf-8-sig"))
        except (OSError, SyntaxError, ValueError) as exc:
            unparsed.append(f"{rel_s} ({type(exc).__name__})")
            continue
        docs = _docstring_ids(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in docs:
                    continue
                for name in FLAG_RE.findall(node.value):
                    refs.setdefault(name, set()).add(rel_s)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            bound = [t.id for t in targets if isinstance(t, ast.Name)]
            if not bound:
                continue
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and isinstance(child.value, str):
                    for name in FLAG_RE.findall(child.value):
                        syms.setdefault(name, set()).update(f"{rel_s}::{b}" for b in bound)
    out = (refs, syms, unparsed)
    _SCAN_CACHE[key] = out
    return out


# ─── خواندنِ رجیستریِ tracked ─────────────────────────────────────────────────
def _cell(text):
    return text.replace("`", "").replace("*", "").strip()


def parse_registry(text):
    """(rows, problems) از جدولِ مارک‌داون. rows: {نام -> {reader, state}}."""
    rows, problems = {}, []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells or not FLAG_RE.fullmatch(_cell(cells[0])):
            continue
        name = _cell(cells[0])
        if len(cells) != 5:
            problems.append(f"BAD-ROW-SHAPE: {name} — ۵ ستون لازم است، {len(cells)} دیده شد")
            continue
        state = _cell(cells[4])
        if state not in (RAISED, CLOSED):
            problems.append(f"BAD-STATE-TOKEN: {name} — «{state}» نه RAISED است نه CLOSED")
            continue
        if name in rows:
            problems.append(f"DUPLICATE-ROW: {name} — دو ردیف برای یک فایل")
            continue
        rows[name] = {"reader": _cell(cells[2]), "state": state}
    return rows, problems


# ─── ممیزی: تابعِ خالص، سه مجموعه ────────────────────────────────────────────
def audit(*, source_ops, flags_dir, registry_text):
    """فهرستِ یافته‌ها (خالی = سالم). هر یافته نامِ فایل را در خودش دارد."""
    refs, syms, unparsed = scan_source(source_ops)
    rows, findings = parse_registry(registry_text)
    for rel in unparsed:
        findings.append(f"UNPARSED-SOURCE: {rel} — اسکنر نتوانست بخواند؛ نقطهٔ کورِ ارجاع")
    on_disk = {p.name for p in Path(flags_dir).glob(FLAG_GLOB)}

    for name in sorted(rows):
        row = rows[name]
        if row["state"] == RAISED and name not in on_disk:
            findings.append(
                f"MISSING-RAISED: {name} — رجیستری RAISED می‌گوید ولی فایل در «{flags_dir}» "
                f"نیست. این فایل tracked نیست ⇒ حذفش هیچ diff ای ندارد و قابلیتِ "
                f"«{row['reader']}» را بی‌صدا خاموش می‌کند.")
        if row["state"] == CLOSED and name in on_disk:
            findings.append(
                f"WRONGLY-CLOSED: {name} — فایل روی دیسک هست ولی رجیستری CLOSED می‌گوید؛ "
                f"رأیِ تازهٔ مالک در تنها جای tracked ثبت نشده.")
        if name not in refs:
            findings.append(
                f"STALE-REGISTRY-ROW: {name} — هیچ ماژولی در _ops آن را نمی‌خواند")
        elif row["reader"] not in syms.get(name, set()):
            findings.append(
                f"UNKNOWN-READER: {name} — رجیستری «{row['reader']}» را نام می‌برد ولی اسکن "
                f"آن را ندید؛ نمادهای دیده‌شده: {sorted(syms.get(name, ()))}")

    for name in sorted(refs):
        if name not in rows:
            findings.append(
                f"UNREGISTERED-REF: {name} — در {sorted(refs[name])} خوانده می‌شود ولی "
                f"ردیفی در ACTIVATION-FLAGS.md ندارد")
    for name in sorted(on_disk):
        if name not in rows:
            findings.append(
                f"UNDECLARED-ON-DISK: {name} — مسلح است ولی هیچ ردیفی ندارد")
    return findings


def _assert_outside_live(path):
    resolved = Path(path).resolve()
    live = harness.REAL_VAULT.resolve()
    assert live not in resolved.parents and resolved != live, (
        f"مسیرِ فیکسچر داخلِ درختِ زنده است: {resolved}")


def _fixture():
    """رونوشتِ موقتِ فلگ‌های زنده + رجیستری. هیچ‌چیزی زیرِ _ops ِ واقعی ساخته نمی‌شود."""
    tmp = Path(tempfile.mkdtemp(prefix="activation-flags-"))
    _assert_outside_live(tmp)
    for src in _LIVE_OPS.glob(FLAG_GLOB):
        shutil.copy2(src, tmp / src.name)
    shutil.copy2(_REGISTRY, tmp / _REGISTRY.name)
    return tmp, (tmp / _REGISTRY.name).read_text("utf-8")


# ═══ گاردها ═══════════════════════════════════════════════════════════════════
def t_registry_parses_into_rows():
    """اگر جدول شکسته شود بقیهٔ گاردها بی‌صدا تهی می‌شوند — اول شکلش را بسنج."""
    assert _REGISTRY.exists(), f"رجیستری نیست: {_REGISTRY}"
    rows, problems = parse_registry(_REGISTRY.read_text("utf-8"))
    assert not problems, f"ردیف‌های معیوبِ رجیستری: {problems}"
    assert len(rows) >= 10, f"جدول تقریباً تهی است ({len(rows)} ردیف) — پارسر یا سند شکسته"
    assert "ACTIVATION-HEARTSTATE.flag" in rows, (
        f"ردیفِ heartstate — همان فایلِ باربر — در رجیستری نیست: {sorted(rows)}")


def t_source_scan_has_no_blind_spots():
    """فایلی که parse نشود یعنی ارجاعش دیده نشده؛ سکوت را به‌عنوان «تمیز» نخوان."""
    _, _, unparsed = scan_source(_OPS)
    assert not unparsed, f"فایل‌های parse-نشدهٔ _ops: {unparsed}"


def t_every_referenced_flag_is_registered():
    """اهرمِ مسلح‌سازیِ تازه نمی‌تواند بدونِ یک ردیفِ tracked وارد شود."""
    refs, _, _ = scan_source(_OPS)
    assert refs, "اسکن هیچ ارجاعی پیدا نکرد — خودِ اسکنر شکسته است"
    rows, _ = parse_registry(_REGISTRY.read_text("utf-8"))
    missing = sorted(set(refs) - set(rows))
    assert not missing, f"فلگِ خوانده‌شده بدونِ ردیفِ رجیستری: {missing}"


def t_live_tree_audit_is_clean():
    """قلبِ گارد روی درختِ زنده: هر فایلِ RAISED باید واقعاً روی دیسک باشد."""
    findings = audit(source_ops=_OPS, flags_dir=_LIVE_OPS,
                     registry_text=_REGISTRY.read_text("utf-8"))
    assert not findings, "ممیزیِ ACTIVATION روی درختِ زنده قرمز است:\n  " + "\n  ".join(findings)


def t_deleting_the_heartstate_flag_turns_the_audit_red_naming_it():
    """مسیرِ قرمز، روی رونوشتِ موقت — با کنترلِ پایه تا قرمز واقعاً شاهد باشد."""
    tmp, text = _fixture()
    try:
        base = audit(source_ops=_OPS, flags_dir=tmp, registry_text=text)
        assert not base, f"فیکسچرِ پایه خودش قرمز است ⇒ قرمزِ بعدی شاهد نیست: {base}"
        victim = tmp / "ACTIVATION-HEARTSTATE.flag"
        assert victim.exists(), f"فیکسچر فایلِ قربانی را ندارد: {victim}"
        _assert_outside_live(victim)
        victim.unlink()
        after = audit(source_ops=_OPS, flags_dir=tmp, registry_text=text)
        assert len(after) == 1, f"دقیقاً یک یافته انتظار می‌رفت، دیده شد: {after}"
        assert after[0].startswith("MISSING-RAISED:"), f"ردهٔ یافته غلط است: {after[0]}"
        assert "ACTIVATION-HEARTSTATE.flag" in after[0], (
            f"یافته نامِ فایل را نمی‌برد: {after[0]}")
        assert "heart/heartstate.py::_FLAG_FILE" in after[0], (
            f"یافته نامِ خوانندهٔ ازدست‌رفته را نمی‌برد: {after[0]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_deleting_any_raised_flag_is_caught_by_name():
    """گارد فقط heartstate را نمی‌پاید — هر رأیِ مسلحِ مالک همین محافظت را دارد."""
    tmp, text = _fixture()
    try:
        rows, _ = parse_registry(text)
        raised = sorted(n for n, r in rows.items() if r["state"] == RAISED)
        assert raised, "هیچ ردیفِ RAISED ای نیست — گارد چیزی برای پاییدن ندارد"
        for name in raised:
            target = tmp / name
            assert target.exists(), f"فیکسچر «{name}» را ندارد (رجیستری RAISED می‌گوید)"
            _assert_outside_live(target)
            backup = target.read_bytes()
            target.unlink()
            found = audit(source_ops=_OPS, flags_dir=tmp, registry_text=text)
            target.write_bytes(backup)
            assert any(f.startswith("MISSING-RAISED:") and name in f for f in found), (
                f"حذفِ «{name}» گرفته نشد؛ یافته‌ها: {found}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_heartstate_is_armed_by_the_file_even_with_the_env_unset():
    """چرا ممیزیِ env دروغ می‌گوید: شاخهٔ فایل به‌تنهایی کافی است.

    کاملاً داخلِ ops ِ موقتِ harness اجرا می‌شود — `heartstate._FLAG_FILE` از
    `opslib.STATE_DIR.parent` می‌آید که harness به temp پین کرده.
    """
    flag = Path(heartstate._FLAG_FILE)
    _assert_outside_live(flag)
    saved = os.environ.pop("HEARTSTATE_SHADOW", None)
    existed = flag.exists()
    try:
        if existed:
            flag.unlink()
        assert heartstate.enabled() is False, (
            "بدونِ env و بدونِ فایل باید خاموش باشد — پیش‌فرضِ امن شکسته")
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text("fixture\n", "utf-8")
        assert heartstate.enabled() is True, (
            f"وجودِ فایلِ {flag.name} به‌تنهایی مسلح نمی‌کند — پس مدلِ ذهنیِ "
            "«فقط HEARTSTATE_SHADOW» درست بود و رجیستری باید اصلاح شود")
        flag.unlink()
        assert heartstate.enabled() is False, "حذفِ فایل خاموشش نکرد"
    finally:
        if flag.exists():
            flag.unlink()
        if existed:
            flag.write_text("restored\n", "utf-8")
        if saved is not None:
            os.environ["HEARTSTATE_SHADOW"] = saved


def t_flag_mtime_is_never_evidence_of_freshness():
    """دقیقاً همان استدلالی که این فایل را می‌کشد، این‌جا رد می‌شود.

    فایلِ مسلح‌سازی یک‌بار ساخته می‌شود و دیگر لمس نمی‌شود؛ mtime ِ `2026-07-23` دربارهٔ
    «آیا خوانده می‌شود؟» هیچ نمی‌گوید. با واژگانِ `_ops/provenance.py` (نه یک مفهومِ
    تازهٔ تازگی): `Mtime` همیشه UNKNOWN می‌شود.
    """
    flag = _LIVE_OPS / "ACTIVATION-HEARTSTATE.flag"
    assert flag.exists(), f"فایلِ باربر روی درختِ زنده نیست: {flag}"
    stamped = provenance.stamp(
        value=True, source=str(flag),
        observed_ts=provenance.Mtime(flag.stat().st_mtime),
        cadence_s=57.0, writer="heart/heartstate.py::persist")
    assert stamped["mode"] == provenance.Mode.UNKNOWN, (
        f"mtime به‌عنوان تازگی پذیرفته شد: mode={stamped['mode']}")
    assert stamped.get("reason") == "mtime-only", (
        f"دلیلِ UNKNOWN باید mtime-only باشد: {stamped.get('reason')}")
    assert not provenance.is_trustworthy(stamped), "یک mtime قابلِ تصمیم‌گیری شمرده شد"
    try:
        provenance.value_of(stamped)
        raise AssertionError("value_of روی UNKNOWN مقدار داد — سکوت به عدد تبدیل شد")
    except KeyError:
        pass


def t_registry_warns_that_env_audits_miss_heartstate():
    """هشدار متن است، پس فقط یک تست می‌تواند نگه‌داردش."""
    text = _REGISTRY.read_text("utf-8")
    for token in ("HEARTSTATE_SHADOW", "flags-loaded", "ACTIVATION-HEARTSTATE.flag"):
        assert token in text, f"رجیستری «{token}» را نمی‌برد — هشدارِ اصلی پاک شده"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_activation_flag_presence: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
