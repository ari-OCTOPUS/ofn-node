"""
brain/self_code.py — خطِ لوله‌ی خودتغییریِ کد: propose → (owner) approve → apply.

تصمیمِ مالک («ویرایشِ کدِ .py را باز کن، پرریسک»). بازبینیِ خصمانه نشان داد که
«آزمونِ کد پیش از تأیید = اجرای کدِ نامطمئن با اختیارِ کامل» است (کپیِ temp مرزِ
امنیتی نیست؛ مسیرِ مطلق از آن فرار می‌کند). پس طراحی این‌طور سخت شد:

  ۱. PROPOSE (خودکار، از جمله daemonِ بی‌مراقب): فقط تحلیلِ **ایستا** —
     نحو + اسکنِ AST الگوهای خطرناک + TCB. **هیچ کدی اجرا نمی‌شود.**
  ۲. مالک در داشبورد/تلگرام کلِ دیف را می‌بیند و آگاهانه approve/reject می‌کند.
  ۳. APPROVE (فقط با حضورِ مالک): تنها جایی که کد اجرا می‌شود، و آن هم:
       • env پاک‌سازی‌شده (بدونِ کلید/توکن) + .env در کپی نیست → نشتِ راز بسته.
       • اجرا در کپیِ throwaway؛ سپس **تشخیصِ دستکاری**: اگر اجرای کاندیدا هر فایلِ
         .pyِ زنده‌ای را عوض کرده باشد (فرار با مسیرِ مطلق) → کلِ درخت بازگردانی و
         پیشنهاد «مخرب» رد می‌شود.
       • فقط اگر سوییت سبز شد و دستکاری نبود → اعمالِ متنیِ ساده روی زنده
         (بدونِ اجرای دوباره‌ی کد روی درختِ زنده).

هسته‌ی موردِاعتماد (TCB) هرگز هدفِ پیشنهاد نیست (guardrails.assert_code_target_allowed).
صداقت: بدونِ sandboxِ سیستم‌عامل، «تأییدِ آگاهانه‌ی تو با دیدنِ کد» مرزِ نهایی است؛
سبزشدنِ اسکن به‌معنیِ بی‌خطربودن نیست — کد را ببین.
"""
from __future__ import annotations

import os
import ast
import json
import shutil
import logging
import subprocess
import tempfile
import stat
from pathlib import Path
from datetime import datetime

from brain import guardrails

logger = logging.getLogger(__name__)

_SENTINEL = "SELFCODE_SUITE_DONE"

# پوشه‌ها/فایل‌هایی که هنگامِ کپی به temp نادیده گرفته می‌شوند (سنگین/حساس).
_COPY_IGNORE = shutil.ignore_patterns(
    "outputs", "__pycache__", ".git", ".claude", ".venv", "venv",
    "*.egg-info", "node_modules", "chroma_db", "*.pyc", ".pytest_cache",
    ".env", "*.bak", "*.selfcode.bak",
)

_TEST_TIMEOUT = int(os.getenv("SELF_CODE_TEST_TIMEOUT", "300"))

# پسوندِ substring (پیش‌فیلترِ سریع) — گیتِ اصلی AST است.
_DANGEROUS_SUBSTR = (
    "os.system(", "subprocess", "shutil.rmtree", "eval(", "exec(",
    "__import__(", "os.remove(", "os.unlink(", "compile(", "pickle.load",
    "marshal.load", "ctypes", "os.popen", "importlib", "urllib", "socket",
)


def enabled() -> bool:
    return os.getenv("SELF_CODE_ENABLED", "0").lower() in ("1", "true", "yes")


def _root() -> Path:
    from config.settings import SYSTEM_ROOT
    return SYSTEM_ROOT.resolve()


def _proposals_dir() -> Path:
    from config.settings import OUTPUT_DIR
    d = OUTPUT_DIR / "self_code_proposals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _meta_path(pid: str) -> Path:
    return _proposals_dir() / pid / "meta.json"


def _load_meta(pid: str) -> dict | None:
    p = _meta_path(pid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_meta(pid: str, meta: dict) -> None:
    p = _meta_path(pid)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


# ════════════════════════════════════════════════════════════════════════
#  تحلیلِ ایستای خطر — AST (نه substringِ ساده)
# ════════════════════════════════════════════════════════════════════════

# importهایی که «تازه‌واردشدن»شان در یک بهبودِ کوچک مشکوک است (شبکه/سریال/پویا).
# os/sys/shutil عمداً نیستند (بسیار رایج)؛ سوءاستفاده‌شان در سطحِ فراخوانی گرفته می‌شود.
_DANGER_IMPORTS = {
    "subprocess", "importlib", "ctypes", "pickle", "marshal", "socket",
    "urllib", "http", "ftplib", "smtplib", "telnetlib", "requests", "httpx",
    "multiprocessing", "builtins", "pty", "code", "codeop", "aiohttp",
    "paramiko", "pexpect", "asyncio",
}
_DANGER_CALL_NAMES = {"eval", "exec", "compile", "__import__",
                      "getattr", "setattr", "vars", "globals", "locals"}
_DANGER_ATTRS = {
    "system", "popen", "popen2", "popen3", "popen4", "spawn", "spawnl",
    "spawnv", "spawnve", "execv", "execve", "execvp", "kill", "remove",
    "unlink", "rename", "replace", "rmtree", "move", "copy", "copy2",
    "copytree", "copyfile", "urlopen", "urlretrieve", "write_text",
    "write_bytes", "chmod", "chown", "fork", "setuid", "putenv", "startfile",
}


def _danger_features(code: str) -> set[str]:
    """مجموعه‌ی «ویژگی‌های خطرناک»ِ ساختاریِ کد (via AST). خطای نحوی → مجموعه‌ی حسّاس."""
    feats: set[str] = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"syntax_error"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                base = (a.name or "").split(".")[0]
                if base in _DANGER_IMPORTS:
                    feats.add(f"import:{base}")
        elif isinstance(node, ast.ImportFrom):
            base = (node.module or "").split(".")[0]
            if base in _DANGER_IMPORTS:
                feats.add(f"import:{base}")
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                if f.id in _DANGER_CALL_NAMES:
                    feats.add(f"call:{f.id}")
                if f.id == "open":
                    mode = ""
                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                        mode = str(node.args[1].value)
                    for kw in node.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                            mode = str(kw.value.value)
                    if any(c in mode for c in ("w", "a", "x", "+")):
                        feats.add("open:write")
            elif isinstance(f, ast.Attribute):
                if f.attr in _DANGER_ATTRS:
                    feats.add(f"attr:{f.attr}")
        # رشته‌سازیِ پویا به‌عنوانِ آرگومانِ نام‌های خطرناک → مبهم‌سازی
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            feats.add("strconcat")  # فقط اگر تازه باشد شمرده می‌شود (delta)
    return feats


def _ast_danger(original: str, new: str) -> str | None:
    """اگر نسخه‌ی جدید یک ویژگیِ خطرناکِ **تازه** (نبود در اصل) وارد کند → دلیل."""
    of = _danger_features(original)
    nf = _danger_features(new)
    fresh = nf - of
    # strconcat به‌تنهایی خطر نیست؛ فقط وقتی importِ پویا/reflection هم تازه باشد.
    hard = {x for x in fresh if not x.startswith("strconcat") and x != "syntax_error"}
    if "syntax_error" in nf:
        return "نحوِ نامعتبر"
    if hard:
        return "الگوی خطرناکِ تازه: " + "، ".join(sorted(hard)[:5])
    return None


def _scan_dangerous(original: str, new: str) -> str | None:
    """پیش‌فیلترِ سریعِ substring (لایه‌ی دوم کنارِ AST)."""
    for tok in _DANGEROUS_SUBSTR:
        if tok in new and tok not in original:
            return f"الگوی پرخطرِ تازه: «{tok}»"
    return None


def _static_check(original: str, new: str) -> str | None:
    """همه‌ی گیت‌های ایستا. دلیلِ رد یا None."""
    try:
        ast.parse(new)
    except SyntaxError as e:
        return f"نحوِ نامعتبر: {e}"
    if new.strip() == original.strip():
        return "تغییری ندارد"
    return _ast_danger(original, new) or _scan_dangerous(original, new)


# ════════════════════════════════════════════════════════════════════════
#  ۱) PROPOSE — فقط ایستا؛ هیچ کدی اجرا نمی‌شود
# ════════════════════════════════════════════════════════════════════════

def propose_code_change(target_rel: str, new_content: str, rationale: str,
                        proposer: str = "auto", goal: str = "") -> dict:
    """پیشنهادِ تغییرِ کد (فقط sandbox + تحلیلِ ایستا). کدِ زنده و کدِ کاندیدا اجرا نمی‌شود."""
    if not enabled():
        return {"ok": False, "reason": "SELF_CODE_ENABLED خاموش است"}

    root = _root()
    target = (root / target_rel).resolve()

    ok, reason = guardrails.assert_code_target_allowed(target)
    if not ok:
        return {"ok": False, "reason": f"هدفِ نامجاز: {reason}"}
    if not target.exists():
        return {"ok": False, "reason": "فایلِ هدف موجود نیست (فقط بهبودِ فایلِ موجود)"}

    original = target.read_text(encoding="utf-8", errors="replace")
    bad = _static_check(original, new_content)
    if bad:
        return {"ok": False, "reason": f"رد (گیتِ ایستا): {bad}"}

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    n = len(list(_proposals_dir().glob(f"{stamp}*")))
    pid = f"{stamp}-{n}" if n else stamp

    pdir = _proposals_dir() / pid
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "original.py").write_text(original, encoding="utf-8")
    (pdir / "new.py").write_text(new_content, encoding="utf-8")

    meta = {
        "id": pid,
        "target": target_rel.replace("\\", "/"),
        "rationale": rationale[:1000],
        "goal": goal[:200],
        "proposer": proposer,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pending_approval",     # ایستا-پاس؛ منتظرِ تأییدِ مالک
        "static_ok": True,
        "lines_original": original.count("\n") + 1,
        "lines_new": new_content.count("\n") + 1,
    }
    _save_meta(pid, meta)
    logger.info("self_code proposal %s → %s (static-checked, not executed)", pid, target_rel)
    return {"ok": True, "pid": pid, "status": "pending_approval",
            "reason": "پیشنهادِ ایستا-پاس ثبت شد — منتظرِ تأییدِ مالک"}


# ════════════════════════════════════════════════════════════════════════
#  Snapshot/tamper — دفاع در برابرِ فرار با مسیرِ مطلق هنگامِ اجرا
# ════════════════════════════════════════════════════════════════════════

def _all_py_files():
    root = _root()
    skip = {"outputs", ".git", ".claude", "__pycache__", ".venv", "venv",
            "node_modules", ".pytest_cache"}
    for p in root.rglob("*.py"):
        rel = p.relative_to(root)
        if any(part in skip for part in rel.parts):
            continue
        yield p


def _snapshot_py() -> dict:
    snap = {}
    for p in _all_py_files():
        try:
            snap[str(p)] = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return snap


def _detect_tamper(snap: dict) -> list[str]:
    """فایل‌های .pyِ زنده که از زمانِ snapshot عوض شده‌اند (نشانه‌ی فرارِ کاندیدا)."""
    changed = []
    for path, content in snap.items():
        p = Path(path)
        try:
            if (not p.exists()) or p.read_text(encoding="utf-8", errors="replace") != content:
                changed.append(path)
        except Exception:
            changed.append(path)
    return changed


def _restore_py(snap: dict) -> int:
    n = 0
    for path, content in snap.items():
        p = Path(path)
        try:
            if (not p.exists()) or p.read_text(encoding="utf-8", errors="replace") != content:
                p.write_text(content, encoding="utf-8")
                n += 1
        except Exception as e:
            logger.error("restore failed for %s: %s", path, e)
    return n


def _scrubbed_env() -> dict:
    """env کمینه بدونِ راز (کلید/توکن) برای اجرای کاندیدا — نشتِ راز بسته."""
    def secret(k: str) -> bool:
        ku = k.upper()
        return any(s in ku for s in ("KEY", "TOKEN", "SECRET", "PASSWORD",
                                     "PASSWD", "CREDENTIAL", "API"))
    env = {k: v for k, v in os.environ.items() if not secret(k)}
    env["MOCK_MODE"] = "true"
    env["PYTHONIOENCODING"] = "utf-8"
    env["SELF_CODE_ENABLED"] = "0"         # جلوگیری از بازگشتِ خودتغییری در فرزند
    return env


def _rmtree_quiet(path: Path) -> None:
    def _onexc(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception as e:
            logger.warning("temp cleanup failed for %s: %s", p, e)
    try:
        try:
            shutil.rmtree(path, onexc=_onexc)          # py 3.12+
        except TypeError:
            shutil.rmtree(path, onerror=lambda f, p, e: _onexc(f, p, e))
    except Exception as e:
        logger.warning("temp cleanup failed for %s: %s", path, e)


def _test_in_temp(pid: str) -> tuple[bool, str]:
    """کاندیدا را در کپیِ throwaway (env پاک) اجرا و کلِ سوییت را می‌سنجد.

    تنها جایی که کدِ کاندیدا اجرا می‌شود. sentinel جلوی os._exit(0)ِ زودرس را می‌گیرد.
    """
    meta = _load_meta(pid)
    target_rel = meta["target"]
    new_content = (_proposals_dir() / pid / "new.py").read_text(encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="selfcode_"))
    try:
        dst = tmp / "proj"
        shutil.copytree(_root(), dst, ignore=_COPY_IGNORE)
        (dst / target_rel).write_text(new_content, encoding="utf-8")
        wrapper = (
            "import sys, unittest\n"
            "from pathlib import Path\n"
            "ROOT=Path.cwd(); sys.path.insert(0,str(ROOT))\n"
            "from tests import _bootstrap\n"
            "s=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))\n"
            "r=unittest.TextTestRunner(verbosity=0).run(s)\n"
            f"print('{_SENTINEL}:'+('PASS' if r.wasSuccessful() else 'FAIL'))\n"
        )
        proc = subprocess.run(
            ["python", "-c", wrapper],
            cwd=str(dst), capture_output=True,
            encoding="utf-8", errors="replace",
            timeout=_TEST_TIMEOUT, env=_scrubbed_env(),
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        passed = (f"{_SENTINEL}:PASS" in out) and proc.returncode == 0
        return passed, out[-1500:]
    except subprocess.TimeoutExpired:
        return False, f"timeout پس از {_TEST_TIMEOUT}s"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        _rmtree_quiet(tmp)


# ════════════════════════════════════════════════════════════════════════
#  ۲) APPROVE / REJECT — فقط با تصمیمِ مالک
# ════════════════════════════════════════════════════════════════════════

def list_pending() -> list[dict]:
    out = []
    for pdir in sorted(_proposals_dir().glob("*/"), reverse=True):
        meta = _load_meta(pdir.name)
        if meta and meta.get("status") == "pending_approval":
            out.append(meta)
    return out


def list_all(limit: int = 30) -> list[dict]:
    out = []
    for pdir in sorted(_proposals_dir().glob("*/"), reverse=True):
        meta = _load_meta(pdir.name)
        if meta:
            out.append(meta)
        if len(out) >= limit:
            break
    return out


def reject(pid: str, note: str = "") -> dict:
    meta = _load_meta(pid)
    if not meta:
        return {"ok": False, "reason": "یافت نشد"}
    meta["status"] = "rejected"
    meta["decided_at"] = datetime.now().isoformat(timespec="seconds")
    if note:
        meta["note"] = note[:300]
    _save_meta(pid, meta)
    return {"ok": True, "reason": "رد شد"}


def approve(pid: str) -> dict:
    """اعمالِ پیشنهاد — فقط با تأییدِ مالک، با اجرای امنِ کاندیدا و تشخیصِ دستکاری.

    مراحل: TCB + stale + بازاسکنِ ایستا → snapshotِ کلِ .pyِ زنده → اجرا در temp
    (env پاک) → اگر اجرا هر فایلِ زنده‌ای را دستکاری کرد: بازگردانی + ردِ «مخرب» →
    اگر سوییت رد شد: تغییری اعمال نشده → اگر سبز و سالم: اعمالِ متنیِ ساده روی زنده.
    """
    meta = _load_meta(pid)
    if not meta:
        return {"ok": False, "reason": "یافت نشد"}
    if meta.get("status") != "pending_approval":
        return {"ok": False, "reason": f"وضعیتِ نامناسب: {meta.get('status')}"}

    target = (_root() / meta["target"]).resolve()
    ok, reason = guardrails.assert_code_target_allowed(target)
    if not ok:
        return {"ok": False, "reason": f"TCB: {reason}"}
    if not target.exists():
        return {"ok": False, "reason": "فایلِ هدف دیگر موجود نیست"}

    pdir = _proposals_dir() / pid
    original_snapshot = (pdir / "original.py").read_text(encoding="utf-8")
    new_content = (pdir / "new.py").read_text(encoding="utf-8")
    current = target.read_text(encoding="utf-8", errors="replace")

    if current.strip() != original_snapshot.strip():
        meta["status"] = "stale"
        _save_meta(pid, meta)
        return {"ok": False, "reason": "فایل از زمانِ پیشنهاد تغییر کرده (stale)"}

    # بازاسکنِ ایستا در لحظه‌ی اعمال (دفاعِ دولایه)
    bad = _static_check(current, new_content)
    if bad:
        meta["status"] = "rejected"
        meta["note"] = f"بازاسکن: {bad}"
        _save_meta(pid, meta)
        return {"ok": False, "reason": f"بازاسکنِ ایستا رد کرد: {bad}"}

    # اجرا در temp با تشخیصِ دستکاریِ درختِ زنده
    snap = _snapshot_py()
    passed, tail = _test_in_temp(pid)
    tampered = _detect_tamper(snap)
    if tampered:
        restored = _restore_py(snap)
        meta["status"] = "rejected_malicious"
        meta["tamper"] = {"files": tampered[:20], "restored": restored,
                          "at": datetime.now().isoformat(timespec="seconds")}
        _save_meta(pid, meta)
        logger.error("self_code %s TAMPERED live tree (%d files) → restored, rejected",
                     pid, len(tampered))
        return {"ok": False, "reason": f"⛔ دستکاریِ درختِ زنده ({len(tampered)} فایل) → "
                f"بازگردانی شد، پیشنهاد مخرب رد شد", "tampered": tampered[:10]}

    if not passed:
        meta["status"] = "tested_fail"
        meta["test"] = {"passed": False, "tail": tail[-800:],
                        "at": datetime.now().isoformat(timespec="seconds")}
        _save_meta(pid, meta)
        return {"ok": False, "reason": "سوییت در sandbox سبز نشد (کدِ زنده دست‌نخورده)"}

    # سالم + سبز → اعمالِ متنیِ ساده (بدونِ اجرای کد روی زنده)
    bak = target.with_suffix(target.suffix + ".selfcode.bak")
    try:
        bak.write_text(current, encoding="utf-8")
    except Exception as e:
        return {"ok": False, "reason": f"بکاپ نشد: {e}"}
    target.write_text(new_content, encoding="utf-8")
    meta["status"] = "applied"
    meta["apply"] = {"passed": True, "backup": bak.name,
                     "at": datetime.now().isoformat(timespec="seconds")}
    _save_meta(pid, meta)
    # ثبت به‌عنوانِ «قابلیتِ آموخته» (رشدِ هدف‌محور — با کمکِ تأییدِ مالک)
    try:
        from brain import self_growth
        self_growth.record_learned_capability(meta)
    except Exception as e:
        logger.debug("record capability failed: %s", e)
    logger.info("self_code approve %s: APPLIED to %s", pid, meta["target"])
    return {"ok": True, "reason": f"اعمال شد روی {meta['target']} (بکاپ: {bak.name})",
            "target": meta["target"]}


def revert_applied(pid: str) -> dict:
    """بازگردانیِ یک تغییرِ applied از بکاپِ .selfcode.bak."""
    meta = _load_meta(pid)
    if not meta or meta.get("status") != "applied":
        return {"ok": False, "reason": "پیشنهادِ applied یافت نشد"}
    target = (_root() / meta["target"]).resolve()
    bak = target.with_suffix(target.suffix + ".selfcode.bak")
    if not bak.exists():
        return {"ok": False, "reason": "بکاپ یافت نشد"}
    target.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
    meta["status"] = "reverted"
    _save_meta(pid, meta)
    return {"ok": True, "reason": "بازگردانی شد"}


def status_counts() -> dict:
    counts: dict[str, int] = {}
    for pdir in _proposals_dir().glob("*/"):
        meta = _load_meta(pdir.name)
        if meta:
            counts[meta.get("status", "?")] = counts.get(meta.get("status", "?"), 0) + 1
    return counts


# ════════════════════════════════════════════════════════════════════════
#  AUTO — پیشنهادِ خودکارِ بهبود با LLM (فقط ایستا؛ هرگز اجرا/اعمال)
# ════════════════════════════════════════════════════════════════════════

_EVOLVABLE = [
    "data/synthetic.py", "data/physical.py", "brain/frontier.py",
    "brain/conclusions.py", "brain/workspace.py", "ui/visuals.py",
    "memory/embeddings.py", "brain/meta_research.py",
]


def _extract_code(text: str) -> str | None:
    import re
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return blocks[-1].strip() if blocks else None


def auto_propose_once(target_rel: str | None = None, seed: int = 0,
                      goal: str = "") -> dict:
    """یک بهبودِ کد را با LLM پیشنهاد می‌کند (فقط تحلیلِ ایستا؛ هرگز اجرا/اعمال).

    daemonِ بی‌مراقب همین را صدا می‌زند — پس کدِ نامطمئن هرگز بی‌حضورِ مالک اجرا نمی‌شود.
    """
    if not enabled():
        return {"ok": False, "reason": "SELF_CODE_ENABLED خاموش است"}
    if target_rel is None:
        target_rel = _EVOLVABLE[seed % len(_EVOLVABLE)]

    ok, reason = guardrails.assert_code_target_allowed(_root() / target_rel)
    if not ok:
        return {"ok": False, "reason": f"هدفِ نامجاز: {reason}"}
    target = _root() / target_rel
    if not target.exists():
        return {"ok": False, "reason": "هدف موجود نیست"}

    original = target.read_text(encoding="utf-8", errors="replace")
    if len(original) > 12000:
        return {"ok": False, "reason": "فایل بزرگ‌تر از حدِ امنِ بازنویسیِ کامل"}

    goal_line = f"\nهدفِ پژوهشی که این بهبود باید به آن خدمت کند: {goal}\n" if goal else ""
    prompt = (
        "تو یک مهندسِ نرم‌افزارِ محتاطی. فایلِ پایتونِ زیر را «کمی» بهتر کن — فقط "
        "خوانایی، مقاومت در برابرِ خطا، یا docstring — بدونِ تغییرِ رفتارِ بیرونی، "
        "بدونِ تغییرِ امضای توابع/کلاس‌ها، بدونِ importهای جدیدِ سنگین/شبکه‌ای/پویا."
        f"{goal_line}"
        "کلِ فایلِ کاملِ جدید را در یک بلوکِ ```python برگردان و هیچ توضیحِ اضافه نده.\n\n"
        f"# فایل: {target_rel}\n```python\n{original}\n```"
    )
    try:
        from llm.router import get_router
        client = get_router().get_client("analysis")
        raw = client.quick(prompt, temperature=0.3)
    except Exception as e:
        return {"ok": False, "reason": f"LLM error: {type(e).__name__}: {e}"}

    if not raw or raw.startswith("["):
        return {"ok": False, "reason": f"پاسخِ نامعتبرِ LLM: {str(raw)[:60]}"}
    new_content = _extract_code(raw)
    if not new_content:
        return {"ok": False, "reason": "بلوکِ کد در پاسخ نبود"}
    if not (0.5 * len(original) <= len(new_content) <= 2.0 * len(original)):
        return {"ok": False, "reason": "اندازه‌ی خروجی نامتناسب"}

    return propose_code_change(target_rel, new_content,
                               rationale=f"auto LLM improvement of {target_rel}",
                               proposer="llm", goal=goal)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("enabled:", enabled(), "· pending:", len(list_pending()),
          "· counts:", status_counts())
