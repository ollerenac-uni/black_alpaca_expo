#!/bin/bash
# Terminal 2 of the 2G demo: GSMEvil2 web UI + pyshark sniffer on lo:4729.
# Capturing on lo needs root (cap_net_raw), so this uses sudo + the venv python.
# Usage: ./demo_sniffer.sh [port]   then open http://localhost:<port>/ and turn IMSI sniffer ON.
cd "$(dirname "$0")" || exit 1
PORT="${1:-80}"   # matches your usual http://localhost/imsi/
echo ">> GSMEvil2 on http://localhost:$PORT/   (IMSI page: /imsi/)"
exec sudo .gsmevil_venv/bin/python GsmEvil.py -p "$PORT"
