#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""miniyaml — strict parser for the LAB-DOCTOR-CONTRACT YAML subset.

The repo carries no YAML dependency and the vault doctor is stdlib-pure by
charter; this parser covers exactly the subset the contract uses — nested
mappings, block sequences, inline sequences, and scalars — and FAILS CLOSED
(duplicate keys, tabs, inconsistent indentation, stray syntax all raise)
instead of guessing. If the contract ever grows beyond this subset the parse
error is the correct outcome: better a loud refusal than a silent misread.
"""
from __future__ import annotations

from pathlib import Path

__all__ = ["MiniYAMLError", "loads", "load_file"]


class MiniYAMLError(ValueError):
    """Raised on any construct outside the supported subset."""


def _scalar(text: str):
    s = text.strip()
    if not s:
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    low = s.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if s.startswith("[") != s.endswith("]"):  # half an inline list
        raise MiniYAMLError(f"unbalanced inline sequence: {s!r}")
    if s.startswith("{"):
        raise MiniYAMLError(f"inline mappings not in subset: {s!r}")
    return s


def _inline_list(body: str):
    inner = body.strip()[1:-1].strip()
    if not inner:
        return []
    return [_scalar(part) for part in inner.split(",")]


class _Line:
    __slots__ = ("indent", "text", "no")

    def __init__(self, no: int, raw: str):
        if "\t" in raw:
            raise MiniYAMLError(f"line {no}: tab indentation is forbidden")
        stripped = raw.strip()
        if stripped.startswith("#") or not stripped:
            self.indent, self.text, self.no = None, "", no
        else:
            self.indent = len(raw) - len(raw.lstrip(" "))
            self.text, self.no = stripped, no


def _parse_block(lines: list[_Line], pos: int, indent: int):
    """Parse one mapping-or-sequence block at `indent`; returns (value, next_pos)."""
    if pos < len(lines) and lines[pos].indent == indent and lines[pos].text.startswith("- "):
        seq: list = []
        while pos < len(lines):
            ln = lines[pos]
            if ln.indent is None:
                pos += 1
                continue
            if ln.indent < indent:
                break
            if ln.indent > indent:
                raise MiniYAMLError(f"line {ln.no}: unexpected indent inside sequence")
            if not ln.text.startswith("- "):
                break
            item = ln.text[2:].strip()
            if item.startswith("[") and item.endswith("]"):
                seq.append(_inline_list(item))
            elif ":" in item:
                # sequence-of-mappings: "- key: value" with sibling keys
                # continuing at a deeper indent (the contract's `flow:` shape).
                key, _, rest = item.partition(":")
                key = key.strip()
                child = _child_indent(lines, pos + 1, indent)
                mapping: dict = {}
                if rest.strip():
                    mapping[key] = _scalar(rest)
                elif child is not None:
                    sub, pos = _parse_block(lines, pos + 1, child)
                    mapping = {key: None, **sub}
                    pos -= 1  # compensate the loop's pos += 1 below
                else:
                    mapping[key] = None
                if child is not None and rest.strip():
                    sub, pos = _parse_block(lines, pos + 1, child)
                    for k, v in sub.items():
                        if k in mapping:
                            raise MiniYAMLError(f"line {ln.no}: duplicate key {k!r}")
                        mapping[k] = v
                    pos -= 1
                seq.append(mapping)
            elif not item:
                sub, pos = _parse_block(lines, pos + 1, _child_indent(lines, pos + 1, indent))
                seq.append(sub)
                continue
            else:
                seq.append(_scalar(item))
            pos += 1
        return seq, pos

    mapping: dict = {}
    while pos < len(lines):
        ln = lines[pos]
        if ln.indent is None:
            pos += 1
            continue
        if ln.indent < indent:
            break
        if ln.indent > indent:
            raise MiniYAMLError(f"line {ln.no}: unexpected indent (expected {indent})")
        if ln.text.startswith("- "):
            break
        if ":" not in ln.text:
            raise MiniYAMLError(f"line {ln.no}: expected 'key: value', got {ln.text!r}")
        key, _, rest = ln.text.partition(":")
        key = key.strip()
        if key.startswith("-"):
            raise MiniYAMLError(f"line {ln.no}: malformed key {key!r}")
        if key in mapping:
            raise MiniYAMLError(f"line {ln.no}: duplicate key {key!r}")
        rest = rest.strip()
        if rest.startswith("[") and rest.endswith("]"):
            mapping[key] = _inline_list(rest)
            pos += 1
        elif rest:
            mapping[key] = _scalar(rest)
            pos += 1
        else:
            child = _child_indent(lines, pos + 1, indent)
            if child is None:
                mapping[key] = None
                pos += 1
            else:
                mapping[key], pos = _parse_block(lines, pos + 1, child)
    return mapping, pos


def _child_indent(lines: list[_Line], pos: int, parent_indent: int):
    while pos < len(lines) and lines[pos].indent is None:
        pos += 1
    if pos >= len(lines) or lines[pos].indent <= parent_indent:
        return None
    return lines[pos].indent


def loads(text: str):
    lines = [_Line(i + 1, raw) for i, raw in enumerate(text.splitlines())]
    pos = 0
    while pos < len(lines) and lines[pos].indent is None:
        pos += 1
    if pos >= len(lines):
        return {}
    if lines[pos].indent != 0:
        raise MiniYAMLError(f"line {lines[pos].no}: document must start at column 0")
    value, end = _parse_block(lines, pos, 0)
    while end < len(lines) and lines[end].indent is None:
        end += 1
    if end < len(lines):
        raise MiniYAMLError(f"line {lines[end].no}: trailing content after document root")
    return value


def load_file(path: Path | str):
    return loads(Path(path).read_text(encoding="utf-8"))
