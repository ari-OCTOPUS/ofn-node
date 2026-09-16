#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""canary.py — canary session برای تستِ واقعیِ context_assembler.

این یک ابزارِ CLI است که ContextAssembler را با flag روشن اجرا می‌کند و
خروجیِ واقعی را نشان می‌دهد — بدون نیاز به wire کردنِ bot.py.

استفاده:
  $env:OCTOPUS_WIRE_SEED_ASSEMBLER = "1"
  python -X utf8 _ops/seed/canary.py "وضعیت سیستم چیه؟"
  python -X utf8 _ops/seed/canary.py --json "وضعیت سیستم چیه؟"
  Remove-Item Env:OCTOPUS_WIRE_SEED_ASSEMBLER

اگر flag خاموش باشد، می‌گوید «assembler disabled» و exit می‌کند.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from context_assembler import ContextAssembler, AssembleInput  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    json_mode = "--json" in args
    args = [a for a in args if a != "--json"]

    if not args:
        print("Usage: canary.py [--json] <message>")
        return 1

    message = " ".join(args)

    if os.environ.get("OCTOPUS_WIRE_SEED_ASSEMBLER", "0") != "1":
        print("⚠️  OCTOPUS_WIRE_SEED_ASSEMBLER=0 — assembler disabled.")
        print("    powershell: $env:OCTOPUS_WIRE_SEED_ASSEMBLER = \"1\"")
        return 1

    ca = ContextAssembler(total_budget=4000)
    prompt, trace = ca.build(AssembleInput(
        user_msg=message,
        mission={"goal": "analyze_octopus", "acceptance": "evidence-based answer", "risk_level": "low"},
        query=message,
    ))

    if json_mode:
        output = {
            "flag_on": trace.flag_on,
            "query": trace.query,
            "total_chars": trace.total_chars,
            "slots": trace.slots,
            "trimmed": trace.trimmed,
            "error": trace.error,
            "prompt": prompt,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("═" * 60)
        print(f"  ASSEMBLED PROMPT ({trace.total_chars} chars, {len(trace.slots)} slots)")
        if trace.trimmed:
            print(f"  trimmed: {', '.join(trace.trimmed)}")
        if trace.error:
            print(f"  ⚠️  {trace.error}")
        print("═" * 60)
        print(prompt)
        print("═" * 60)
        print(f"slots: {', '.join(s['name'] for s in trace.slots)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
