#!/usr/bin/env python3
"""Static consistency checker for the Dart sources (no Dart toolchain in the
cloud workspace, so this catches the mechanical blunders before handoff):

1. Every relative and package:tradequote_local import resolves to a file.
2. Balanced (), {}, [] per file, string/comment aware (catches truncation).
3. Screen classes referenced by the router exist in the imported files.
4. Providers referenced across features are defined in lib/providers.dart.
5. `part` directives listed (expected: database.g.dart, generated later).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'lib')
TEST = os.path.join(ROOT, 'test')

errors = []
warnings = []


def dart_files():
    for base in (LIB, TEST):
        for dirpath, _, files in os.walk(base):
            for f in sorted(files):
                if f.endswith('.dart'):
                    yield os.path.join(dirpath, f)


def strip_strings_and_comments(src: str) -> str:
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ''
        if ch == '/' and nxt == '/':
            j = src.find('\n', i)
            i = n if j == -1 else j
            continue
        if ch == '/' and nxt == '*':
            j = src.find('*/', i + 2)
            i = n if j == -1 else j + 2
            continue
        if ch in ('"', "'"):
            triple = src[i:i + 3] in ('"""', "'''")
            quote = src[i:i + 3] if triple else ch
            raw = i > 0 and src[i - 1] == 'r'
            j = i + len(quote)
            while j < n:
                if not raw and src[j] == '\\':
                    j += 2
                    continue
                # keep ${...} interpolation content (it is code)
                if not raw and src[j] == '$' and j + 1 < n and src[j + 1] == '{':
                    depth = 1
                    k = j + 2
                    while k < n and depth:
                        if src[k] == '{':
                            depth += 1
                        elif src[k] == '}':
                            depth -= 1
                        k += 1
                    out.append(src[j + 1:k])
                    j = k
                    continue
                if src[j:j + len(quote)] == quote:
                    j += len(quote)
                    break
                j += 1
            i = j
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


# ---- 1 & 5: imports resolve ------------------------------------------------
import_re = re.compile(r"^\s*(?:import|export|part)\s+'([^']+)'", re.M)
parts = []
for path in dart_files():
    src = open(path, encoding='utf-8').read()
    for target in import_re.findall(src):
        if target.startswith('dart:'):
            continue
        if target.startswith('package:'):
            pkg = target.split('/', 1)
            if pkg[0] == 'package:tradequote_local':
                resolved = os.path.join(LIB, pkg[1])
                if not os.path.exists(resolved):
                    errors.append(f'{os.path.relpath(path, ROOT)}: unresolved {target}')
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if target.endswith('.g.dart'):
            parts.append(f'{os.path.relpath(path, ROOT)} -> {target} (generated later by build_runner)')
            continue
        if not os.path.exists(resolved):
            errors.append(f'{os.path.relpath(path, ROOT)}: unresolved import {target}')

# ---- 2: balanced delimiters -------------------------------------------------
for path in dart_files():
    src = strip_strings_and_comments(open(path, encoding='utf-8').read())
    for open_ch, close_ch in (('(', ')'), ('{', '}'), ('[', ']')):
        diff = src.count(open_ch) - src.count(close_ch)
        if diff != 0:
            errors.append(
                f'{os.path.relpath(path, ROOT)}: unbalanced {open_ch}{close_ch} (diff {diff:+d})')

# ---- 3: router screen classes exist ----------------------------------------
router = open(os.path.join(LIB, 'app', 'router.dart'), encoding='utf-8').read()
screen_classes = set(re.findall(r'\b(?:const\s+)?([A-Z]\w+Screen)\(', router))
lib_src = {}
for path in dart_files():
    lib_src[path] = open(path, encoding='utf-8').read()
all_lib = '\n'.join(v for k, v in lib_src.items() if k.startswith(LIB))
for cls in sorted(screen_classes):
    if not re.search(rf'class {cls}\b', all_lib):
        errors.append(f'router references missing class {cls}')

# ---- 4: providers referenced are defined ------------------------------------
providers_src = open(os.path.join(LIB, 'providers.dart'), encoding='utf-8').read()
defined = set(re.findall(r'^final (\w+Provider)\b', providers_src, re.M))
used = set()
for path, src in lib_src.items():
    if path.startswith(LIB) and not path.endswith('providers.dart'):
        used |= set(re.findall(r'\b(\w+Provider)\b', src))
# Filter to plausible app providers (defined-style names) only.
missing = {u for u in used if u not in defined and not u[0].isupper()}
for m in sorted(missing):
    errors.append(f'provider used but not defined in providers.dart: {m}')

# ---- report -----------------------------------------------------------------
print(f'Checked {len(lib_src)} Dart files.')
for p in parts:
    print(f'PART   {p}')
for w in warnings:
    print(f'WARN   {w}')
for e in errors:
    print(f'ERROR  {e}')
print()
print('RESULT:', 'FAIL' if errors else 'PASS (no unresolved imports, no unbalanced delimiters, router/providers consistent)')
sys.exit(1 if errors else 0)
