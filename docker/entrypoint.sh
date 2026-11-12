#!/bin/bash
# Starts the demodulator (headless) + GSMEvil2 in one container; they share this
# container's loopback, so GSMTAP on lo:4729 reaches the sniffer. Open the web UI
# and turn the IMSI sniffer ON.
set -e

: "${SDR_FREQ:?Set SDR_FREQ, e.g. -e SDR_FREQ=879.8M}"
SDR_GAIN="${SDR_GAIN:-40}"
SDR_SR="${SDR_SR:-1e6}"
# RTL-SDR default. B210: -e SDR_ARGS=type=b200 . Autodetect: -e SDR_ARGS=''
SDR_ARGS="${SDR_ARGS-rtl=0}"
PORT="${PORT:-80}"

echo ">> grgsm_livemon_headless args='$SDR_ARGS' f=$SDR_FREQ g=$SDR_GAIN sr=$SDR_SR -> lo:4729"
grgsm_livemon_headless --args="$SDR_ARGS" -f "$SDR_FREQ" -g "$SDR_GAIN" -s "$SDR_SR" &
LIVE=$!
trap 'kill "$LIVE" 2>/dev/null' EXIT

# Give the SDR a moment to come up; fail loudly if livemon died (no device, etc).
sleep 3
kill -0 "$LIVE" 2>/dev/null || { echo "ERROR: grgsm_livemon_headless exited (SDR not found / busy?)"; exit 1; }

echo ">> GSMEvil2 on http://localhost:$PORT/   (open /imsi/ and enable IMSI, /analytics/ for roamers)"
exec /opt/venv/bin/python GsmEvil.py -p "$PORT"
