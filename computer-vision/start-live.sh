#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# YOLO deployments can set TERRA_PYTHON=.venv-yolo/bin/python.
terra_python="${TERRA_PYTHON:-.venv/bin/python}"
if [[ ! -x "$terra_python" ]]; then
  echo "Python environment missing. Run bash setup.sh first."
  exit 1
fi
exec "$terra_python" src/live.py "$@"
