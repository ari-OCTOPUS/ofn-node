#!/usr/bin/env bash
# ============================================================
# Brushline deploy script -- RUN ON THE VPS.
# Pulls the latest code from GitHub (read-only mirror) and restarts.
# The server is a pull-only mirror of origin/main; local edits are discarded.
# ============================================================
set -euo pipefail

# --- Config (override via env if your layout differs) -------
REPO_DIR="${BRUSHLINE_REPO_DIR:-$HOME/brushline-repo}"
BRANCH="${BRUSHLINE_BRANCH:-main}"
APP_SUBDIR="Ai farm- sister Painting/brushline/60_code"
APP_DIR="$REPO_DIR/$APP_SUBDIR"

echo "[deploy] repo: $REPO_DIR  branch: $BRANCH"

# --- 1. Pull latest (hard reset to origin -- server is read-only) ---
cd "$REPO_DIR"
git fetch --all --prune
git reset --hard "origin/$BRANCH"
git clean -fd -- "$APP_SUBDIR" 2>/dev/null || true   # never touch ignored .env / data/
echo "[deploy] now at: $(git rev-parse --short HEAD) $(git log -1 --format='%s')"

# --- 2. Python deps in an isolated venv --------------------
cd "$APP_DIR"
if [ ! -d .venv ]; then
  echo "[deploy] creating venv ..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# --- 3. .env guard (secrets live ONLY on the server) -------
if [ ! -f .env ]; then
  echo "[deploy] ERROR: .env missing in $APP_DIR" >&2
  echo "[deploy] Run once: cp .env.example .env  && fill in real secrets." >&2
  exit 1
fi

# --- 4. AST sanity check before (re)start ------------------
python3 - <<'PYCHECK'
import ast, glob, sys
bad = []
for f in glob.glob("src/**/*.py", recursive=True):
    try:
        ast.parse(open(f, encoding="utf-8").read())
    except SyntaxError as e:
        bad.append(f"{f}: {e}")
if bad:
    print("[deploy] AST FAIL:\n  " + "\n  ".join(bad)); sys.exit(1)
print("[deploy] AST OK")
PYCHECK

# --- 5. Restart service ------------------------------------
# Adjust to your process manager. systemd --user example:
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-enabled brushline >/dev/null 2>&1; then
  systemctl --user restart brushline
  echo "[deploy] restarted systemd --user unit 'brushline'"
else
  echo "[deploy] No systemd unit 'brushline' found."
  echo "[deploy] Start manually:  cd \"$APP_DIR\" && . .venv/bin/activate && python3 main.py"
fi

echo "[deploy] DONE."
