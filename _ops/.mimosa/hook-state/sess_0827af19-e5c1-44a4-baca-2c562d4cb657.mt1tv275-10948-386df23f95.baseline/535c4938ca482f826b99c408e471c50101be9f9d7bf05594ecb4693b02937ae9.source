#!/usr/bin/env python3
"""test_sog_provenance — C8: اصالتِ sog دیگر نمی‌تواند سبزِ کاذب بسازد.

سه گیتِ زندهٔ قلب (`delta_self`, `e_shadow`, `i_pred`) در برابرِ
`_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` همه `locked` اند. اصالتِ آن قفل به
`4.py`ِ مالک گره خورده — فایلی که امروز **وجود ندارد**. باگ این بود که
`_sha256_file()` روی OSError رشتهٔ لفظیِ `"unavailable"` برمی‌گرداند و همان به‌عنوانِ
`provenance.source_4py_sha256` نوشته می‌شد: مقداری truthy و غیرِ null که هم از گاردِ
«null نباشد» و هم از گاردِ «هش حاضر باشد» رد می‌شود.

این تست چهار ناوردی را می‌سنجد، همه روی فیکسچرِ موقت — هرگز روی قفلِ زنده:

  ۱) `run_lock()` روی اصالتِ غیرقابلِ راستی‌آزمایی **fail-closed** است: استثنا، خروجِ
     non-zero، و قفلِ روی دیسک بایت‌به‌بایت دست‌نخورده.
  ۲) `read_lock()` روی غیاب/خرابی نشانگرِ صریحِ UNKNOWN می‌دهد، نه `{}`.
  ۳) برچسبِ `sog_provenance` سه‌حالتی است و MISMATCH به VERIFIED نمی‌افتد.
  ۴) خروجی‌های عددیِ سه گیت بایت‌به‌بایت (bit-for-bit، از راهِ `float.hex()`) همان‌اند.
"""
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("sog-provenance")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from heart import sog_math as sm    # noqa: E402

LIVE_VAULT = Path(r"F:\backup").resolve()
LIVE_LOCK = LIVE_VAULT / "_ops" / "state" / "sim" / "PULSE-EQUATIONS-LOCKED.json"
FIX = Path(ENV["OPS_DIR"]) / "state" / "sim"
FIX.mkdir(parents=True, exist_ok=True)
FIX_LOCK = FIX / "PULSE-EQUATIONS-LOCKED.json"
FIX_4PY = Path(ENV["root"]) / "fixture-4.py"
FIX_4PY.write_bytes(b"# fixture stand-in for 4.py\nX = 1\n")
FIX_DIGEST = hashlib.sha256(FIX_4PY.read_bytes()).hexdigest()
MISSING_4PY = Path(ENV["root"]) / "no-such-dir" / "4.py"


def _fixture_lock_record(source_digest: str) -> dict:
    """کمینه‌ترین قفلِ معتبر — شکلِ روی دیسکِ واقعی، مقادیرِ فیکسچر."""
    return {
        "ts": "2026-07-10T20:09:22",
        "schema": "PULSE-EQUATIONS-LOCKED.v1",
        "full_run": True,
        "status": {"delta_self": "locked", "e_shadow": "locked",
                   "i_pred": "locked", "i_pred_gates_nothing": True},
        "provenance": {"code_sha256": "a" * 64,
                       "source_4py_sha256": source_digest,
                       "method": "fixture"},
    }


def _write_fixture_lock(source_digest: str = FIX_DIGEST) -> str:
    FIX_LOCK.write_text(json.dumps(_fixture_lock_record(source_digest)), "utf-8")
    return hashlib.sha256(FIX_LOCK.read_bytes()).hexdigest()


def _under_live_vault(p: Path) -> bool:
    try:
        Path(p).resolve().relative_to(LIVE_VAULT)
        return True
    except ValueError:
        return False


# ─── ۰: ایزولاسیون — هر مسیرِ این تست بیرونِ درختِ زنده است ─────────────────────
def t_every_fixture_path_is_outside_the_live_vault():
    """تستی که مسیرش pin نشده باشد، دیر یا زود روی state زنده می‌نویسد."""
    for p in (Path(ENV["root"]), Path(ENV["OPS_DIR"]), FIX_LOCK, FIX_4PY,
              MISSING_4PY, Path(ENV["GENOME_DIR"]), Path(ENV["BRAIN_DIR"])):
        assert not _under_live_vault(p), f"فیکسچر داخلِ درختِ زنده: {p}"
    assert not _under_live_vault(sm.LOCK_PATH_DEFAULT), \
        f"مسیرِ پیش‌فرضِ قفلِ ماژول پین نشده: {sm.LOCK_PATH_DEFAULT}"
    assert Path(ENV["OPS_DIR"]) == Path(os.environ["OPS_DIR"]), "OPS_DIR پین نشده"


# ─── ۱: ردِ صریحِ رشتهٔ "unavailable" ────────────────────────────────────────────
def t_unavailable_string_is_not_a_verifiable_digest():
    """قلبِ باگ: «حاضر و truthy» با «قابلِ راستی‌آزمایی» یکی گرفته شده بود."""
    assert sm.is_verifiable_digest(sm.UNAVAILABLE) is False, "رشتهٔ unavailable پذیرفته شد"
    assert sm.is_verifiable_digest("UNAVAILABLE") is False
    assert sm.is_verifiable_digest("  unavailable  ") is False
    # گاردِ ساده‌لوحانه‌ای که این باگ را ساخت، روی همین مقدار سبز می‌شود:
    assert bool(sm.UNAVAILABLE) is True, "پیش‌فرضِ تست: مقدار truthy است"
    assert sm.UNAVAILABLE is not None


def t_only_a_real_sha256_counts_as_verifiable():
    """۶۴ نویسهٔ hex — نه کوتاه‌تر، نه غیرِ hex، نه None، نه عدد."""
    assert sm.is_verifiable_digest(FIX_DIGEST) is True
    assert sm.is_verifiable_digest(FIX_DIGEST.upper()) is True   # hexِ بزرگ‌حرف
    assert sm.is_verifiable_digest("z" * 64) is False, "غیرِ hex پذیرفته شد"
    assert sm.is_verifiable_digest("a" * 63) is False, "طولِ غلط پذیرفته شد"
    assert sm.is_verifiable_digest("a" * 65) is False
    assert sm.is_verifiable_digest("") is False
    assert sm.is_verifiable_digest(None) is False
    assert sm.is_verifiable_digest(123) is False


# ─── ۲: run_lock روی اصالتِ غیرقابلِ راستی‌آزمایی چیزی نمی‌نویسد ────────────────
def t_run_lock_refuses_and_leaves_the_lock_byte_identical():
    """سنجهٔ C8: قفلِ موجود باید بایت‌به‌بایت همان بماند."""
    before = _write_fixture_lock()
    os.environ["SOG_4PY_PATH"] = str(MISSING_4PY)
    try:
        raised = None
        try:
            sm.run_lock(out_path=FIX_LOCK, full=False, write=True)
        except sm.ProvenanceUnverifiable as e:
            raised = e
        assert raised is not None, "run_lock با منبعِ غایب قفل نوشت (fail-open)"
        assert raised.digest == sm.UNAVAILABLE, f"digest گزارش‌شده: {raised.digest!r}"
        after = hashlib.sha256(FIX_LOCK.read_bytes()).hexdigest()
        assert after == before, f"قفل عوض شد: {before} -> {after}"
        on_disk = json.loads(FIX_LOCK.read_text("utf-8"))
        assert on_disk["provenance"]["source_4py_sha256"] == FIX_DIGEST, \
            "هشِ اصالتِ قدیمی بازنویسی شد"
    finally:
        os.environ.pop("SOG_4PY_PATH", None)


def t_run_lock_main_exits_non_zero_and_touches_no_lock():
    """خروجِ واقعیِ پروسه، نه فقط استثنا — و ایزولاسیون از قفلِ زنده."""
    before = _write_fixture_lock()
    live_before = (hashlib.sha256(LIVE_LOCK.read_bytes()).hexdigest()
                   if LIVE_LOCK.exists() else None)
    env = dict(os.environ)
    env["SOG_4PY_PATH"] = str(MISSING_4PY)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["OPS_DIR"] = ENV["OPS_DIR"]          # صریح، حتی اگر harness ست کرده باشد
    env["ORG_ROOT"] = str(ENV["root"])
    proc = subprocess.run([sys.executable, "-X", "utf8",
                           str(_OPS / "heart" / "sog_math.py")],
                          capture_output=True, text=True, env=env, timeout=300)
    assert proc.returncode != 0, f"__main__ صفر برگرداند: {proc.stdout[:400]}"
    assert proc.returncode == 2, f"کدِ خروج {proc.returncode} (انتظار ۲)"
    assert "provenance_unverifiable" in proc.stdout, proc.stdout[:400]
    assert '"lock_written": false' in proc.stdout.lower(), proc.stdout[:400]
    assert hashlib.sha256(FIX_LOCK.read_bytes()).hexdigest() == before, \
        "قفلِ فیکسچر عوض شد"
    if live_before is not None:
        assert hashlib.sha256(LIVE_LOCK.read_bytes()).hexdigest() == live_before, \
            "قفلِ زنده لمس شد — ایزولاسیون شکست"


def t_run_lock_still_writes_when_provenance_is_verifiable():
    """گاردِ «همیشه نه» بی‌ارزش است: با منبعِ حاضر باید قفل نوشته شود."""
    out = FIX / "positive-control-LOCK.json"
    if out.exists():
        out.unlink()
    os.environ["SOG_4PY_PATH"] = str(FIX_4PY)
    try:
        rec = sm.run_lock(out_path=out, full=False, write=True)
    finally:
        os.environ.pop("SOG_4PY_PATH", None)
    assert out.exists(), "با اصالتِ معتبر هم چیزی نوشته نشد"
    on_disk = json.loads(out.read_text("utf-8"))
    assert on_disk["provenance"]["source_4py_sha256"] == FIX_DIGEST
    assert sm.is_verifiable_digest(on_disk["provenance"]["source_4py_sha256"])
    assert on_disk["full_run"] is False
    assert rec["status"]["i_pred_gates_nothing"] is True


# ─── ۳: برچسبِ سه‌حالتیِ اصالت ──────────────────────────────────────────────────
def t_missing_source_is_unverifiable():
    """امروزِ ارگانیسم: SOG_4PY_PATH ست نیست و 4.py غایب است."""
    lock = _fixture_lock_record(FIX_DIGEST)
    assert MISSING_4PY.exists() is False, "پیش‌فرضِ تست نقض شد"
    assert sm.source_provenance(lock=lock, source=MISSING_4PY) == sm.PROV_UNVERIFIABLE


def t_matching_file_is_verified():
    """VERIFIED فقط با تطابقِ هش — هشِ مرجع از خودِ قفل، نه hardcode."""
    lock = _fixture_lock_record(FIX_DIGEST)
    assert sm.source_provenance(lock=lock, source=FIX_4PY) == sm.PROV_VERIFIED


def t_one_byte_changed_is_mismatch_not_verified():
    """۴.pyِ بازیابی‌شده از نسخهٔ ناشناخته حق ندارد سبزِ کاذب بسازد."""
    other = Path(ENV["root"]) / "fixture-4-mutated.py"
    body = bytearray(FIX_4PY.read_bytes())
    body[-2] = body[-2] ^ 0x01          # دقیقاً یک بایت
    other.write_bytes(bytes(body))
    assert len(body) == len(FIX_4PY.read_bytes()), "طول عوض شد — تستِ یک‌بایت نیست"
    assert hashlib.sha256(bytes(body)).hexdigest() != FIX_DIGEST
    lock = _fixture_lock_record(FIX_DIGEST)
    got = sm.source_provenance(lock=lock, source=other)
    assert got == sm.PROV_MISMATCH, f"یک بایتِ تفاوت برچسبِ {got} گرفت"
    assert got != sm.PROV_VERIFIED


def t_unverifiable_recorded_digest_cannot_be_matched():
    """اگر خودِ قفل «unavailable» ثبت کرده باشد، هیچ فایلی نمی‌تواند تأییدش کند."""
    bad = _fixture_lock_record(sm.UNAVAILABLE)
    assert sm.source_provenance(lock=bad, source=FIX_4PY) == sm.PROV_UNVERIFIABLE
    empty = {"schema": "PULSE-EQUATIONS-LOCKED.v1"}
    assert sm.source_provenance(lock=empty, source=FIX_4PY) == sm.PROV_UNVERIFIABLE
    unknown = sm._lock_unknown(MISSING_4PY, "missing")
    assert sm.source_provenance(lock=unknown, source=FIX_4PY) == sm.PROV_UNVERIFIABLE


# ─── ۴: read_lock — غیاب یک نوع دارد ───────────────────────────────────────────
def t_read_lock_absent_returns_unknown_not_empty():
    """`{}` یعنی «ورودیِ تهی»؛ غیاب یعنی «نمی‌دانم». این دو یکی نیستند."""
    absent = FIX / "no-such-lock.json"
    assert not absent.exists()
    got = sm.read_lock(absent)
    assert got != {}, "غیاب دوباره به دیکشنریِ تهی ترجمه شد"
    assert got.get(sm.LOCK_STATE_KEY) == sm.LOCK_UNKNOWN, got
    assert sm.lock_is_unknown(got) is True
    # ناوردیِ پایین‌دست: UNKNOWN هم مثل قبل fail-closed می‌ماند (هیچ گیتی باز نمی‌شود)
    assert (got.get("status") or {}).get("delta_self") != "locked"
    assert not got.get("full_run")


def t_read_lock_corrupt_returns_unknown():
    """JSONِ خراب هم «نمی‌دانم» است، نه «تهی»."""
    broken = FIX / "broken-lock.json"
    broken.write_text("{not json", "utf-8")
    got = sm.read_lock(broken)
    assert sm.lock_is_unknown(got) is True, got
    assert got != {}
    notmap = FIX / "notmap-lock.json"
    notmap.write_text("null", "utf-8")
    assert sm.lock_is_unknown(sm.read_lock(notmap)) is True


def t_read_lock_present_is_returned_untouched():
    """مسیرِ موفق هیچ کلیدِ تزریقی نمی‌گیرد — وگرنه ~۱۵ مصرف‌کننده شکل عوض می‌کنند."""
    _write_fixture_lock()
    got = sm.read_lock(FIX_LOCK)
    assert got == json.loads(FIX_LOCK.read_text("utf-8")), "رکورد دست‌کاری شد"
    assert sm.LOCK_STATE_KEY not in got
    assert sm.lock_is_unknown(got) is False


# ─── ۵: صفر تغییرِ عددی ────────────────────────────────────────────────────────
def t_numeric_gate_outputs_are_bit_identical():
    """C8 فقط برچسب اضافه می‌کند. این سه عدد bit-for-bit پین شده‌اند."""
    fl = sm.solve_floors(**sm.CANONICAL)
    got = {"delta_self": float(sm.delta_self(fl)).hex(),
           "e_shadow": float(sm.e_shadow(fl)).hex(),
           "i_pred": float(sm.i_pred_riccati(**sm.CANONICAL)["total"]).hex()}
    pinned = {"delta_self": "0x1.f5d7dda2346cep-4",
              "e_shadow": "0x1.9b5544060174fp-7",
              "i_pred": "0x1.d871e7e01b35fp-7"}
    assert got == pinned, f"خروجیِ عددی عوض شد: {got}"


# ─── ۶: نویسندهٔ واحد — فیلدِ نو از همان نویسنده می‌آید، نه نویسندهٔ دوم ─────────
def _shadow_tree():
    return ast.parse((_OPS / "heart" / "shadow.py").read_text("utf-8"))


def t_shadow_stamps_sog_provenance_from_sog_math():
    """کلیدِ `sog_provenance` باید مقدارش را از `sog_math.source_provenance()` بگیرد."""
    found = []
    for node in ast.walk(_shadow_tree()):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "sog_provenance":
                found.append(v)
    assert len(found) == 1, f"{len(found)} جای `sog_provenance` (انتظار دقیقاً ۱)"
    val = found[0]
    assert isinstance(val, ast.Call), "مقدار ثابت است نه فراخوانیِ محاسبه"
    assert getattr(val.func, "attr", None) == "source_provenance", ast.dump(val.func)


def t_shadow_latest_still_has_exactly_one_writer():
    """گران‌ترین باگِ تکرارشوندهٔ این ارگانیسم: نویسندهٔ دوم روی یک فایلِ حالت."""
    writers = 0
    for node in ast.walk(_shadow_tree()):
        if isinstance(node, ast.Call) and (
                getattr(node.func, "id", None) == "LockedJson"
                or getattr(node.func, "attr", None) == "LockedJson"):
            args = [getattr(a, "id", None) or getattr(a, "attr", None)
                    for a in node.args]
            if "SHADOW_LATEST" in args:
                writers += 1
    assert writers == 1, f"{writers} نویسنده روی heart-shadow-latest.json"
    src = (_OPS / "heart" / "shadow.py").read_text("utf-8")
    assert src.count("SHADOW_LATEST.write_text") == 0, "نوشتنِ مستقیم دورِ قفل"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_sog_provenance: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
