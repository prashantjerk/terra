#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f /etc/os-release ]] || ! grep -Eq 'debian|raspbian' /etc/os-release; then
  echo 'This setup script targets Raspberry Pi OS (Bookworm or newer).'
  exit 1
fi
sudo apt-get update
sudo apt-get install -y python3-venv python3-opencv python3-numpy python3-picamera2
/usr/bin/python3 -m venv --system-site-packages .venv
.venv/bin/python -c 'import cv2, numpy; print("OpenCV", cv2.__version__)'
if [[ ! -f config.json ]]; then cp config.example.json config.json; fi
echo 'Setup complete. See README.md for camera capture and calibration.'
