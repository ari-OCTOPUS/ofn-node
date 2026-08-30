#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claim_when_ready.py — قدم ۲: claim فقط وقتی lead+amount واقعی باشد. جعل ممنوع."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent


def main() -> int:
    lead_id = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    amount = (sys.argv[2] if len(sys.argv) > 2 else "").strip()
    if not lead_id or not amount:
        print(json.dumps({
            "ok": False,
            "reason": "need lead_id and amount — refuse fake claim",
            "blocker": "lead 667951 suburb from owner OR close lead",
            "usage": "python claim_when_ready.py <lead_id> <amount>",
            "may_authorize": False,
        }, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({
        "ok": False,
        "reason": "scaffold only — wire to attribution.claim when owner confirms",
        "lead_id": lead_id,
        "amount": amount,
        "sot": "docs/MONEY-CLAIM-VS-CONFIRM.md",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
