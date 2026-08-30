#!/usr/bin/env bash
# Make the genome directory read-only at the FILESYSTEM level -- a technical
# guarantee, not a mere convention. No agent (including the Guardian) may write
# here; genome changes go only through genome/genome_change_protocol.md.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GENOME="$HERE/genome"

chmod -R a-w "$GENOME"
echo "locked (read-only): $GENOME"
echo
echo "Windows equivalent (run in PowerShell as the owner):"
echo "  icacls \"$GENOME\" /deny \"\$($env:USERNAME):(W)\" /T"
echo
echo "To make an approved genome change, temporarily: chmod -R u+w \"$GENOME\""
echo "...then follow the 72h two-key protocol and re-lock."
