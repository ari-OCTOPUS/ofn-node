#!/usr/bin/env python3
"""Convenience entry point. Run from the project root:

    python rsc.py validate specs/debate_extraction.yaml
    python rsc.py run debate_extraction
    python rsc.py list
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_compiler.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
