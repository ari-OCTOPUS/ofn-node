#!/usr/bin/env python3
"""OFFLINE signing only. This host must not generate or use a root private key."""

from __future__ import annotations

import argparse
import pathlib
import sys

CA_DIR = pathlib.Path("/root/octopus-ca")
KEY_PATH = CA_DIR / "root.ed25519"
PUB_EXPORT = pathlib.Path("/etc/octopus/trust/root.pub")


def _refuse() -> None:
    raise SystemExit(
        "signing_state=OFFLINE_ONLY: refuse to keygen/sign on the live Sensorium board. "
        "Use the Windows OCTOPUS-ROOT-V2 packager."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("keygen")
    p_sign = sub.add_parser("sign")
    p_sign.add_argument("path", type=pathlib.Path)
    args = parser.parse_args()
    if args.cmd in {"keygen", "sign"}:
        _refuse()


if __name__ == "__main__":
    main()
