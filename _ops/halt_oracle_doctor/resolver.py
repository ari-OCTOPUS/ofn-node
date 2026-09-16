"""resolver — discover halt-reading sites, resolve what each WOULD read, classify file state.

Two things are deliberately kept apart, and the receipt says which is which:

  (i)  `is_halted` — the REAL predicate, imported under the single bounded allowlist
       (`ofn.kernel.halt`). Tested directly.
  (ii) the path resolution and file-state classification below — the doctor's own
       logic, which MIRRORS the policy documented in `ofn/adapters/halt_flag.py`.
       It proves what the doctor does, NOT what the live adapter does. Proving the
       live adapter is Half B (on-node), which is not authorized.

Conflating (i) and (ii) would be the same error as testing a reimplementation and
calling it verification, so the receipt carries `policy_source` per row.
"""

from __future__ import annotations

import ast
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

POLICY_SOURCE = "mirrors ofn/adapters/halt_flag.py:24-50 documented semantics; NOT proof of the live adapter"

# Documented mapping from halt_flag.py, quoted so the mirror can be audited:
#   is_symlink()            -> True  (a planted link is not a verifiable flag)
#   not exists()            -> halt.is_halted(None)  -> False (absent == RUNNING)
#   undecodable / unreadable-> raw = "" -> is_halted("") -> True
#   directory               -> read_bytes() raises OSError -> "" -> True
FILE_STATES = ("absent", "present", "malformed", "unreadable", "symlink", "directory")

HALT_CALL_NAMES = ("master_halted", "halt_flag_active", "is_halted")


@dataclass
class HaltSite:
    """A place in the code that reads a halt signal."""
    file: str
    line: int
    enclosing: str
    call: str
    path_source: str                 # resolved | caller_supplied | env_only | unknown
    resolved_path: str | None = None
    evidence: str = ""

    def as_dict(self) -> dict:
        return {
            "file": self.file, "line": self.line, "enclosing": self.enclosing,
            "call": self.call, "path_source": self.path_source,
            "resolved_path": self.resolved_path, "evidence": self.evidence,
        }


def _enclosing(tree: ast.AST) -> dict[int, str]:
    """Map line -> dotted enclosing function/class for every node."""
    out: dict[int, str] = {}

    def walk(node: ast.AST, stack: list[str]) -> None:
        for child in ast.iter_child_nodes(node):
            name = getattr(child, "name", None)
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and name:
                stack2 = stack + [name]
                for sub in ast.walk(child):
                    out.setdefault(getattr(sub, "lineno", 0), ".".join(stack2))
                walk(child, stack2)
            else:
                walk(child, stack)

    walk(tree, [])
    return out


def _resolve_expr(node: ast.AST, consts: dict[str, Any]) -> Any:
    """Resolve the small subset of expressions opslib uses for path constants.

    Pure STRING joining with POSIX separators, deliberately: the target is a Linux
    board path, and `pathlib.Path` on Windows would reinterpret a leading "/" against
    the current drive (observed: it produced `C:\\Program Files\\Git\\home\\ari\\...`).
    Modelling a Linux path must not depend on the host OS.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return consts.get(node.id, "<unresolved:%s>" % node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _resolve_expr(node.left, consts)
        right = _resolve_expr(node.right, consts)
        if (isinstance(left, str) and isinstance(right, str)
                and not left.startswith("<unresolved") and not right.startswith("<unresolved")):
            return left.rstrip("/") + "/" + right.lstrip("/")
        return f"<unresolved:{left!r}/{right!r}>"
    if isinstance(node, ast.Call):
        # _P(expr)  /  Path(expr)  /  _os.path.expanduser("~")
        dotted = _dotted_name(node.func)
        if dotted.endswith("expanduser"):
            return consts.get("__HOME__", "<unresolved:expanduser>")
        if node.args:
            return _resolve_expr(node.args[0], consts)
    return "<unresolved>"


def _dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def resolve_canonical_oracle(repo: Path, declared_home: str) -> dict:
    """Read opslib's own constants and compute what the oracle resolves to.

    This is discovery, not a hardcode: change the declared HOME and the answer moves.
    """
    f = repo / "ofn" / "budget" / "opslib.py"
    if not f.exists():
        return {"found": False, "reason": f"missing {f}"}

    tree, err = parse_python(f)
    if err is not None:
        return {"found": False, "reason": f"unparsable: {err}"}
    src_text = f.read_text(encoding="utf-8-sig")
    consts: dict[str, Any] = {"__HOME__": declared_home, "HOME": declared_home}
    raw_exprs: dict[str, str] = {}

    # two passes so forward references resolve
    for _ in range(3):
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                raw_exprs[name] = ast.unparse(node.value)
                consts[name] = _resolve_expr(node.value, consts)

    flag_expr = raw_exprs.get("HALT_FLAG")
    env_override = "HALT_SURVIVAL_LOOP" in src_text
    resolved = consts.get("HALT_FLAG")

    ok = isinstance(resolved, str) and not resolved.startswith("<unresolved")
    return {
        "found": True,
        "module": "ofn/budget/opslib.py",
        "literal_expression": flag_expr,
        "declared_home": declared_home,
        "resolved_path": resolved if ok else None,
        "resolved_ok": bool(ok),
        "env_override": "HALT_SURVIVAL_LOOP=1" if env_override else None,
        "note": "the canonical oracle in code is the one opslib computes; a second path literal elsewhere would recreate D-3",
    }


def parse_python(path: Path):
    """Parse a Python source file, tolerating a UTF-8 BOM.

    Returns (tree, error). `error` is None on success. A file that cannot be parsed is
    NOT skipped silently — the caller records it, because an unparsed file is an
    unknown, not a clean result. (Real finding, 2026-09-17: `ofn/helpers/brainport.py`
    carries a U+FEFF BOM; reading it as plain utf-8 makes ast.parse raise.)
    """
    try:
        src = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return None, f"unreadable: {type(exc).__name__}"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")   # invalid-escape noise from foreign files
            return ast.parse(src, filename=str(path)), None
    except SyntaxError as exc:
        return None, f"SyntaxError: {exc.msg} (line {exc.lineno})"


def discover_sites(repo: Path):
    """Every production site that reads a halt signal, with its path source.

    Returns (sites, parse_failures).
    """
    sites: list[HaltSite] = []
    parse_failures: list[dict] = []

    for path in sorted((repo / "ofn").rglob("*.py")):
        if "__pycache__" in path.parts or path.name.startswith("test_"):
            continue
        tree, err = parse_python(path)
        rel = path.relative_to(repo).as_posix()
        if err is not None:
            parse_failures.append({"file": rel, "error": err})
            continue
        enclosing = _enclosing(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _dotted_name(node.func)
            short = name.split(".")[-1]
            if short not in HALT_CALL_NAMES:
                continue

            line = getattr(node, "lineno", 0)
            resolved = None
            if short == "master_halted":
                source = "resolved"
            elif short == "halt_flag_active":
                if node.args:
                    arg = ast.unparse(node.args[0])
                    if isinstance(node.args[0], (ast.Attribute, ast.Name)) and "self." in arg:
                        source = "caller_supplied"
                        resolved = arg
                    else:
                        source = "resolved"
                        resolved = arg
                else:
                    source = "unknown"
            else:  # is_halted — pure predicate on an already-read string
                source = "env_only" if not node.args else "resolved"

            sites.append(HaltSite(
                file=rel, line=line,
                enclosing=enclosing.get(line, "<module>"),
                call=name, path_source=source, resolved_path=resolved,
                evidence=ast.unparse(node)[:120],
            ))

    # literal <root>/HALT constructions (the ignition's own convention)
    for path in sorted(repo.rglob("*.py")):
        if any(x in path.parts for x in ("__pycache__", ".git")):
            continue
        tree, err = parse_python(path)
        rel = path.relative_to(repo).as_posix()
        if err is not None:
            if not any(f["file"] == rel for f in parse_failures):
                parse_failures.append({"file": rel, "error": err})
            continue
        enclosing = _enclosing(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "HALT":
                        line = getattr(node, "lineno", 0)
                        sites.append(HaltSite(
                            file=rel, line=line,
                            enclosing=enclosing.get(line, "<module>"),
                            call="<literal HALT path constant>",
                            path_source="resolved",
                            resolved_path=ast.unparse(node.value),
                            evidence=ast.unparse(node)[:120],
                        ))
    return sites, parse_failures


def classify_file(p, is_halted_callable=None) -> dict:
    """Classify a halt-flag path the way halt_flag.py documents.

    `is_halted_callable` is the REAL predicate when available; when None the mirror
    substitutes the documented string mapping and says so via policy_source.
    """
    p = Path(p)
    state = "absent"
    raw: str | None = None

    try:
        if p.is_symlink():
            state = "symlink"
        elif p.is_dir():
            state = "directory"
        elif not p.exists():
            state = "absent"
        else:
            state = "present"
            try:
                raw = p.read_bytes().decode("utf-8")
            except (UnicodeDecodeError, ValueError):
                state = "malformed"
                raw = ""
            except OSError:
                state = "unreadable"
                raw = ""
    except OSError:
        state = "unreadable"
        raw = ""

    # fail-closed mapping for the states that never reach a decoded string
    if state in ("symlink", "directory", "unreadable", "malformed"):
        raw_for_predicate = ""          # unparsable intent == HALTED
    elif state == "absent":
        raw_for_predicate = None        # absent == RUNNING
    else:
        raw_for_predicate = raw

    if is_halted_callable is not None:
        predicate = bool(is_halted_callable(raw_for_predicate))
        predicate_source = "ofn.kernel.halt.is_halted (real predicate, allowlisted)"
    else:
        t = (raw_for_predicate or "").strip().lower() if raw_for_predicate is not None else None
        if t is None:
            predicate = False
        elif t in ("0", "false", "no", "off"):
            predicate = False
        elif t in ("1", "true", "yes", "on"):
            predicate = True
        else:
            predicate = True            # anything unparsable => HALTED
        predicate_source = POLICY_SOURCE

    return {
        "path": str(p),
        "state": state,
        "predicate": "HALTED" if predicate else "RUNNING",
        "predicate_bool": predicate,
        "predicate_source": predicate_source,
        "raw_len": None if raw is None else len(raw),
    }
