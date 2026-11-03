#!/usr/bin/env bash
# First-time local setup; does not install Gaussian, create a token, or start real calculations.
set -euo pipefail
umask 077
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG_DIR="$HOME/.config/minebenchmark"
STATE_DIR="$HOME/.local/share/minebenchmark"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$CFG_DIR" "$STATE_DIR" "$UNIT_DIR"
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required"; exit 1
fi
if ! python3 -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null; then
  echo "ERROR: Python >=3.10 required"; exit 1
fi
if [[ ! -f "$CFG_DIR/config.json" ]]; then
  cp "$ROOT/runner/config.example.json" "$CFG_DIR/config.json"
  chmod 600 "$CFG_DIR/config.json"
  echo "Created $CFG_DIR/config.json"
fi
if [[ ! -f "$CFG_DIR/token" ]]; then
  : > "$CFG_DIR/token"
  chmod 600 "$CFG_DIR/token"
  echo "Created empty private token file: $CFG_DIR/token"
fi
PYTHON_BIN="$(command -v python3)"
cat > "$UNIT_DIR/minebenchmark-runner.service" <<EOF
[Unit]
Description=MineBenchMark GitHub compute runner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=$PYTHON_BIN $ROOT/runner/worker.py --config $CFG_DIR/config.json --loop
Restart=on-failure
RestartSec=20
UMask=0077
NoNewPrivileges=true

[Install]
WantedBy=default.target
EOF
chmod 600 "$UNIT_DIR/minebenchmark-runner.service"
echo "Installed user service file: $UNIT_DIR/minebenchmark-runner.service"
echo "Nothing has been launched. Add a GitHub token, then run --once for the smoke test."
echo "If systemd --user is unavailable or your cluster forbids persistent jobs, use an approved compute/scheduler environment."
