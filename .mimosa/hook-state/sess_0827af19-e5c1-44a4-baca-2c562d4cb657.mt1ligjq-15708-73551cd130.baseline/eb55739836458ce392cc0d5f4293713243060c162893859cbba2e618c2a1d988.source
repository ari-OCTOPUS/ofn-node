#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owner_verdicts — رأی‌های تاریخ‌دارِ مالک، از یک فایلِ **tracked**.

ردیفِ A2 ِ `REPAIR-PLAN-2026-08-03` (رأیِ مالک ۲۰۲۶-۰۸-۰۳).

مسئله: `_ops/OCTOPUS-flags.cmd` عمداً gitignore است (داشبورد تولیدش می‌کند و
ممکن است secret بگیرد). نتیجهٔ ناخواسته‌اش این بود که **هر رأیِ مالک که به فلگ
تبدیل می‌شد در هیچ کامیتی نبود** — تمدیدِ ۰۸-۰۳ ِ دو استثنا فقط روی یک ماشین
زندگی می‌کرد و با بازتولیدِ آن فایل می‌پرید.

راه‌حل: دو نگرانی جدا شدند. secretها همان‌جا (ignored) می‌مانند؛ knobهای
غیرمحرمانهٔ تاریخ‌دار به `_ops/owner-verdicts.yaml` ِ tracked می‌روند.

**تقدم عمدی: env برنده است.** این ماژول فقط وقتی حرف می‌زند که env غایب باشد.
پس رفتارِ امروز بایت‌به‌بایت همان است و این فایل تورِ نجات است، نه یک منبعِ
رقیب. واگرایی هم سکوت نمی‌شود: `drift()` نام‌به‌نام گزارشش می‌دهد.

**fail-soft مطلق:** این ماژول در مسیرِ پول (`budget_gate`) صدا زده می‌شود. هر
خطا — فایلِ غایب، قالبِ خراب، انکودینگِ بد — یعنی «چیزی نگفتم»، نه استثنا.
بدترین حالتش برگشت به رفتارِ قبلیِ env-only است.

بدونِ کش خوانده می‌شود (مثل `budget_gate._caps()`) تا ویرایشِ مالک بدونِ
ری‌استارت اعمال شود؛ فایل کوچک است.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

PATH_ENV = "OCTOPUS_OWNER_VERDICTS"
_DEFAULT = Path(__file__).resolve().parent / "owner-verdicts.yaml"

_NAME_RE = re.compile(r"^ {2}([A-Za-z_][A-Za-z0-9_]*):\s*$")
_ATTR_RE = re.compile(r"^ {4}([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def path() -> Path:
    override = str(os.environ.get(PATH_ENV, "") or "").strip()
    return Path(override) if override else _DEFAULT


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def load(p=None) -> dict:
    """`{نامِ رأی: {کلید: مقدار}}`. هر خطایی ⇒ `{}` (هرگز استثنا)."""
    try:
        text = Path(p or path()).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return {}
    out, cur, in_section = {}, None, False
    try:
        for raw in text.splitlines():
            line = raw.rstrip()
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line == "verdicts:":
                in_section = True
                continue
            if not in_section:
                continue
            if not line.startswith(" "):   # کلیدِ سطحِ بالای دیگر ⇒ پایانِ بخش
                in_section = False
                continue
            m = _NAME_RE.match(line)
            if m:
                cur = m.group(1)
                out[cur] = {}
                continue
            m = _ATTR_RE.match(line)
            if m and cur:
                out[cur][m.group(1)] = _unquote(m.group(2))
    except Exception:  # noqa: BLE001 — قالبِ خراب هم یعنی «چیزی نگفتم»
        return {}
    return {k: v for k, v in out.items() if v}


def env_map(p=None) -> dict:
    """`{نامِ env: مقدار}` — شاملِ جفتِ `until_env` هر رأی."""
    out = {}
    for spec in load(p).values():
        name, val = spec.get("env"), spec.get("value")
        if name and val is not None:
            out[name] = val
        until_name, until = spec.get("until_env"), spec.get("until")
        if until_name and until is not None:
            out[until_name] = until
    return out


def get(env_name: str, environ=None, p=None) -> str:
    """مقدارِ مؤثرِ یک knob. **env برنده است**؛ این فایل فقط پرکنندهٔ جای خالی."""
    env = os.environ if environ is None else environ
    live = str(env.get(env_name, "") or "").strip()
    if live:
        return live
    return str(env_map(p).get(env_name, "") or "").strip()


def drift(environ=None, p=None) -> list:
    """جاهایی که env و فایلِ tracked **هر دو** حرف می‌زنند ولی یکی نیستند.
    سکوت بدترین حالت است: اگر flags.cmd از رأیِ ثبت‌شده جدا شد، باید دیده شود."""
    env = os.environ if environ is None else environ
    out = []
    for name, val in sorted(env_map(p).items()):
        live = str(env.get(name, "") or "").strip()
        if live and live != str(val).strip():
            out.append(f"{name}: env='{live}' ≠ owner-verdicts='{val}'")
    return out


def main() -> int:
    v = load()
    print(f"رأی‌های ثبت‌شده: {len(v)}  ({path()})")
    for name, spec in sorted(v.items()):
        print(f"  · {name}: {spec.get('value')} {spec.get('unit', '')}"
              f" تا {spec.get('until')} → {spec.get('expires_to')}"
              f"  [خواننده: {spec.get('reader')}]")
    d = drift()
    if d:
        print("رانشِ env ↔ owner-verdicts:")
        for line in d:
            print("  ✗", line)
        return 1
    print("✓ env و رأی‌های ثبت‌شده هم‌داستان‌اند (یا env ست نیست)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
