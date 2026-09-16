#!/bin/bash
set -euo pipefail
cd /home/ari/ofn

git add -- \
  ofn/node.py \
  ofn/run.py \
  ofn/adapters/cockpit_v2_read_model.py \
  tests/test_cockpit_v2_owner_queue.py

git diff --cached --check
git diff --cached --stat

git commit -m "$(cat <<'EOF'
feat(cockpit-v2): metadata-only owner approval queue projection
EOF
)"

git status --short
