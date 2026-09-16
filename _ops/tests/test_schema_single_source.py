#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A3 (۲۰۲۶-۰۸-۰۳) — Property Schema تک‌منبعِ حقیقت است، نه فهرستِ هاردکدِ validator.

تا امروز `KNOWN_KEYS`/`TYPES`/`STATUSES` در `validate_frontmatter.py` هاردکد
بودند و بی‌صدا از `06 - Architecture Maps/Property Schema.md` جدا می‌افتادند:
همان روز که دو کلیدِ ویس به schema اضافه شد، validator تا ویرایشِ **سومین** جا
قرمز ماند. این سوییت قفلش می‌کند.

سنجهٔ پذیرشِ پلن: «افزودنِ یک کلیدِ ساختگی فقط به schema ⇒ validator بی‌ویرایشِ
کد قبولش کند؛ حذفش ⇒ دوباره ردش کند.» — `t_a_key_added_only_to_the_schema_is_accepted`
و `t_removing_it_from_the_schema_rejects_it_again`.

دندانِ تست: کلیدِ ساختگی عمداً در فهرستِ **پشتیبان** نیست، پس اگر روزی کسی
مسیر را به هاردکد برگرداند، تست قرمز می‌شود — نه اینکه تصادفی سبز بماند.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "04 - Architect System" / "scripts" / "validate_frontmatter.py"

_spec = importlib.util.spec_from_file_location("_vfm", VALIDATOR)
vfm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vfm)          # فقط تعاریف — اسکن زیرِ __main__ است

SYNTHETIC = "zz_synthetic_probe"

_BLOCK = """<!-- SCHEMA-MACHINE:BEGIN -->
```yaml
keys:
  type: text
  status: text
  tags: multitext
  updated: date
{extra}
types: [reference, log]
statuses: [active, idea]
```
<!-- SCHEMA-MACHINE:END -->
"""


def _schema_text(with_synthetic: bool) -> str:
    extra = f"  {SYNTHETIC}: text" if with_synthetic else "  created: date"
    return "بلاه بلاه\n" + _BLOCK.format(extra=extra) + "\nدنبالهٔ سند\n"


def _note(**extra):
    fm = {"type": "reference", "status": "active", "tags": "[x]", "updated": "2026-08-03"}
    fm.update(extra)
    return fm


# ── سنجهٔ پذیرشِ پلن ────────────────────────────────────────────────────────

def t_a_key_added_only_to_the_schema_is_accepted():
    keys, types, statuses = vfm.parse_schema_block(_schema_text(True))
    assert SYNTHETIC in keys, keys
    errs = vfm.check_note("x.md", _note(**{SYNTHETIC: "v"}),
                          known_keys=vfm.CORE_KEYS | set(keys),
                          types=types, statuses=statuses)
    assert errs == [], errs


def t_removing_it_from_the_schema_rejects_it_again():
    keys, types, statuses = vfm.parse_schema_block(_schema_text(False))
    assert SYNTHETIC not in keys, keys
    errs = vfm.check_note("x.md", _note(**{SYNTHETIC: "v"}),
                          known_keys=vfm.CORE_KEYS | set(keys),
                          types=types, statuses=statuses)
    assert len(errs) == 1 and "خارج از schema" in errs[0], errs


def t_the_probe_key_is_absent_from_the_hardcoded_fallback():
    """دندان: اگر ساختگی تصادفاً در پشتیبان بود، دو تستِ بالا بی‌معنا می‌شدند."""
    assert SYNTHETIC not in vfm._FALLBACK_KEY_TYPES


# ── ناوردایی‌های خودِ مکانیزم ───────────────────────────────────────────────

def t_the_live_schema_is_machine_readable():
    """اگر این قرمز شد یعنی والتِ واقعی روی فهرستِ پشتیبان افتاده — سکوتِ خطرناک."""
    keys, types, statuses, source = vfm.load_schema()
    assert source == "schema", source
    assert len(keys) > 30 and len(types) > 10 and len(statuses) >= 9


def t_live_schema_and_types_json_agree():
    assert vfm.types_json_drift() == [], vfm.types_json_drift()


def t_a_partial_block_is_rejected_rather_than_half_parsed():
    """نیمه‌پارس بدتر از پارس‌نشده است: فهرستِ ناقص یعنی ردِ کلیدهای سالم."""
    text = _schema_text(True).replace("statuses: [active, idea]\n", "")
    assert vfm.parse_schema_block(text) is None


def t_a_missing_block_falls_back_loudly():
    saved = vfm.SCHEMA_MD
    try:
        vfm.SCHEMA_MD = ROOT / "__nope__.md"
        keys, types, statuses, source = vfm.load_schema()
        assert source == "fallback"
        assert keys == vfm._FALLBACK_KEY_TYPES
    finally:
        vfm.SCHEMA_MD = saved


def t_no_markers_means_no_parse():
    assert vfm.parse_schema_block("هیچ مارکری این‌جا نیست") is None


def t_the_voice_keys_of_08_03_come_from_the_schema():
    """رگرسیونِ همان حادثه: دو کلیدِ ویس باید از schema بیایند، نه از هاردکد."""
    keys, _, _, source = vfm.load_schema()
    assert source == "schema"
    assert keys.get("transcribed_by") == "text"
    assert keys.get("transcript_secs") == "number"


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  ✅ {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {fn.__name__}: {e}", file=sys.stderr)
    ok = len(tests) - failed
    print(f"{'✅' if not failed else '❌'} test_schema_single_source: {ok}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
