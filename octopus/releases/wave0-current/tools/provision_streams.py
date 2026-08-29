#!/usr/bin/env python3
"""OFFLINE / one-shot stream provisioning. Do not run from octopus-sensorium.service."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--i-am-the-provisioner", action="store_true")
    args = parser.parse_args()
    if os.environ.get("OCTOPUS_ROLE") == "sensorium-agent" or not args.i_am_the_provisioner:
        print("refusing: allow_nats_provisioning=false for the Sensorium runtime", file=sys.stderr)
        return 2
    print("This tool is intentionally not executed on WAVE0_OBSERVE_ONLY.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
