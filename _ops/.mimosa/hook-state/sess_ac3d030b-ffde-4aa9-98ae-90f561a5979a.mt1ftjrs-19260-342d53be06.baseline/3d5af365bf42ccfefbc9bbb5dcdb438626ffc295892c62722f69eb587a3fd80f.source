# -*- coding: utf-8 -*-
"""دستور #۱۱ §۱ — دو تست allowlist:
۱) هر مسیر executable=True در _ops باید مدخل allowlist داشته باشد.
۲) هیچ مدخل allowlist نمی‌تواند اثر گسترش‌دهنده داشته باشد (ساختار کد باید
   فقط halt/throttle/skip/defer باشد)."""
import re
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
ALLOWLIST = _OPS / "safety/EXECUTABLE-ALLOWLIST.md"

# فایل‌های زندهٔ پایتون (بدون تست/آرشیو) که در آنها executable=True نوشته می‌شود
SCAN_ROOTS = [_OPS]


def _python_files():
    for root in SCAN_ROOTS:
        for p in root.rglob("*.py"):
            s = str(p)
            if "__pycache__" in s or "/tests/" in s.replace("\\", "/") \
               or s.endswith("test_" + "x") or "/_archive/" in s.replace("\\", "/"):
                continue
            yield p


def _executable_true_sites():
    """(file, line) برای هر انتساب/کلید-دیکشنریِ واقعیِ executable=True.
    با AST — متنِ docstring/کامنت هرگز سایت حساب نمی‌شود."""
    import ast
    out = []
    for p in _python_files():
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            hit = False
            if isinstance(node, ast.Assign):
                hit = (any(isinstance(t, ast.Name) and "executable" in t.id.lower()
                           for t in node.targets)
                       and isinstance(node.value, ast.Constant) and node.value.value is True)
            elif isinstance(node, ast.Dict):
                for k, v in zip(node.keys or [], node.values or []):
                    if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                            and "executable" in k.value.lower()
                            and isinstance(v, ast.Constant) and v.value is True):
                        hit = True
            if hit:
                out.append((str(p.relative_to(_OPS)), node.lineno))
    return out


def _allowlisted_files():
    text = ALLOWLIST.read_text(encoding="utf-8")
    return {m.group(1).replace("_ops/", "") for m in
            re.finditer(r"`(_ops/[^:`]+)[:.`]", text)}


def test_no_unexpected_executable_true():
    allowed = _allowlisted_files()
    unexpected = [s for s in _executable_true_sites() if s[0] not in allowed]
    assert not unexpected, f"executable=True outside allowlist: {unexpected}"


def test_allowlist_effects_are_restrictive_only():
    """مدخل‌های allowlist فقط halt/throttle/skip/defer مجازند؛ هر نشانهٔ اثر
    گسترش‌دهنده (send/spend/write خارجی/deploy) در بافت همان فایل‌ها ممنوع."""
    for f in _allowlisted_files():
        path = _OPS / f.replace("_ops/", "")
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in ("executable = True", "executable = True", '"protective_executable": True'):
            for m in re.finditer(re.escape(marker), text):
                ctx = text[max(0, m.start() - 400):m.end() + 200]
                assert not re.search(
                    r"(requests\.post|urlopen|send_message|sendMessage|deploy|spend_aud)",
                    ctx), f"expansive effect near {marker} in {f}"
