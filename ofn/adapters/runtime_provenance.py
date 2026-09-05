"""Bounded, read-only correspondence evidence for selected loaded functions.

This is not proof of an entire module, its mutable globals, a different
process, or its dependencies. Compilation is performed without executing the
source. No time, PID, environment, command line, or external handle is read.
"""
from __future__ import annotations

import hashlib
import marshal
import os
from pathlib import Path
import stat
import sys
import types
from typing import Any, Sequence

MAX_SOURCE_BYTES = 1024 * 1024
MAX_FUNCTIONS = 32


def _source_bytes(path: Path) -> bytes:
    if not path.is_absolute() or path.suffix != ".py":
        raise ValueError("source_path_not_absolute_python")
    for part in (path, *path.parents):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("source_path_link_or_reparse_point")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_SOURCE_BYTES:
            raise ValueError("source_not_regular_or_over_budget")
        body = handle.read(MAX_SOURCE_BYTES + 1)
        after = os.fstat(handle.fileno())
    if len(body) > MAX_SOURCE_BYTES:
        raise ValueError("source_over_budget")
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    if identity(before) != identity(after) or len(body) != after.st_size:
        raise ValueError("source_changed_during_read")
    return body


def _digest(code: types.CodeType) -> str:
    # Marshal fingerprints are interpreter-specific. Both compared objects
    # use the same interpreter and filename; version/cache_tag are reported.
    # Version 2 deliberately excludes reference sharing introduced in v3:
    # v3/v4 can differ for equal imported vs freshly compiled code objects.
    return hashlib.sha256(marshal.dumps(code, 2)).hexdigest()


def code_witness(module: types.ModuleType, function_names: Sequence[str]) -> dict[str, Any]:
    """Compare named, top-level live functions with current source compilation.

    ``matched`` is true only when every requested function matches. Errors
    fail closed and expose only a bounded reason, never source or exception
    text. The caller may separately attach its observed PID/invocation time.
    """
    result: dict[str, Any] = {
        "schema": "octopus.selected-code-witness.v1",
        "scope": "selected_loaded_function_code_only",
        "status": "unverified",
        "matched": False,
        "python": {
            "implementation": sys.implementation.name,
            "version": list(sys.version_info[:3]),
            "cache_tag": sys.implementation.cache_tag,
            "marshal_version": 2,
            "optimization": sys.flags.optimize,
        },
        "functions": {},
        "limitations": [
            "Does not verify mutable globals, module initialization, dependencies or another process.",
            "Source correspondence is observed at call time, not an immutable deployment attestation.",
        ],
    }
    if not isinstance(module, types.ModuleType):
        result["reason"] = "invalid_module"
        return result
    if not isinstance(function_names, (list, tuple)) or not 1 <= len(function_names) <= MAX_FUNCTIONS:
        result["reason"] = "invalid_function_names"
        return result
    if any(not isinstance(name, str) or not name.isidentifier() or name.startswith("_")
           for name in function_names) or len(set(function_names)) != len(function_names):
        result["reason"] = "invalid_function_names"
        return result
    namespace = vars(module)
    name = namespace.get("__name__")
    raw_path = namespace.get("__file__")
    if not isinstance(name, str) or not isinstance(raw_path, str):
        result["reason"] = "module_source_unavailable"
        return result
    result["module"] = name
    result["module_path"] = raw_path
    try:
        body = _source_bytes(Path(raw_path))
    except (OSError, ValueError):
        result["reason"] = "source_unreadable_unsafe_or_over_budget"
        return result
    result["source_sha256"] = hashlib.sha256(body).hexdigest()
    result["source_bytes"] = len(body)
    compiled_by_filename: dict[str, types.CodeType] = {}
    for function_name in function_names:
        detail: dict[str, Any] = {"matched": False}
        result["functions"][function_name] = detail
        function = namespace.get(function_name)
        if not isinstance(function, types.FunctionType) or function.__module__ != name:
            detail["reason"] = "not_a_local_python_function"
            continue
        loaded = function.__code__
        detail["loaded_sha256"] = _digest(loaded)
        # Preserve exactly the live code object's filename for the comparison;
        # module_path is reported separately and no other file is opened.
        filename = loaded.co_filename
        try:
            if filename not in compiled_by_filename:
                compiled_by_filename[filename] = compile(
                    body, filename, "exec", dont_inherit=True, optimize=sys.flags.optimize)
        except (SyntaxError, ValueError, TypeError, OverflowError, RecursionError, MemoryError):
            detail["reason"] = "source_compile_failed"
            continue
        candidates = [code for code in compiled_by_filename[filename].co_consts
                      if isinstance(code, types.CodeType) and code.co_name == function_name]
        if len(candidates) != 1:
            detail["reason"] = "source_function_missing_or_ambiguous"
            continue
        detail["compiled_source_sha256"] = _digest(candidates[0])
        detail["matched"] = (loaded == candidates[0] and
                             detail["loaded_sha256"] == detail["compiled_source_sha256"])
        if not detail["matched"]:
            detail["reason"] = "loaded_function_differs_from_current_source"
    result["matched"] = all(value["matched"] for value in result["functions"].values())
    result["status"] = "matched" if result["matched"] else "mismatch_or_unverified"
    return result
