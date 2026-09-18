"""Read-only CLI: python -m tools.replay_revenue_run PATH --policy-sha SHA."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ofn.adapters.revenue_run import replay
from ofn.kernel.errors import FailClosedError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--policy-sha", required=True)
    args = parser.parse_args(argv)
    try:
        with args.path.open(encoding="utf-8") as stream:
            # Never skip malformed or blank ledger entries.
            result = replay((json.loads(line) for line in stream),
                            expected_policy_sha=args.policy_sha)
    except (OSError, ValueError, TypeError, FailClosedError) as exc:
        # Do not echo malformed source text, file contents, or possible PII.
        print(json.dumps({"status": "INVALID", "error_type": type(exc).__name__,
                          "cash_verified": False, "may_authorize": False}),
              file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
