#!/bin/bash
# One container, three modes (GSMEvil2 always sniffs the container's own lo:4729):
#   REPLAY_PCAP="a.pcap b.pcap"  -> replay recorded GSMTAP in a loop, NO SDR
#   RECORD_PCAP=/out.pcap        -> record RECORD_SECONDS of live GSMTAP, then exit
#   (neither)                    -> live: demodulate the SDR into lo:4729
set -e

SDR_GAIN="${SDR_GAIN:-40}"
SDR_SR="${SDR_SR:-1e6}"
SDR_ARGS="${SDR_ARGS-rtl=0}"   # RTL default. B210: type=b200. autodetect: ''
PORT="${PORT:-80}"

# ---- REPLAY: seamless demo from recordings, no radio needed ----------------
if [ -n "${REPLAY_PCAP:-}" ]; then
  echo ">> REPLAY mode (no SDR): $REPLAY_PCAP -> lo:4729 (loop)"
  export AUTOSTART_IMSI="${AUTOSTART_IMSI:-1}"
  # shellcheck disable=SC2086
  /opt/venv/bin/python /opt/gsmevil2/replay.py $REPLAY_PCAP &
  FEED=$!
  trap 'kill "$FEED" 2>/dev/null' EXIT
  echo ">> GSMEvil2 on http://localhost:$PORT/   (/imsi/  /analytics/  /search/)"
  exec /opt/venv/bin/python GsmEvil.py -p "$PORT" --host 0.0.0.0
fi

# ---- RECORD: capture live GSMTAP to a pcap for later replay -----------------
if [ -n "${RECORD_PCAP:-}" ]; then
  : "${SDR_FREQ:?RECORD needs SDR_FREQ, e.g. -e SDR_FREQ=879.8M}"
  SECS="${RECORD_SECONDS:-600}"   # default 10 min
  echo ">> RECORD mode: ${SECS}s of GSMTAP @ $SDR_FREQ (args='$SDR_ARGS') -> $RECORD_PCAP"
  grgsm_livemon_headless --args="$SDR_ARGS" -f "$SDR_FREQ" -g "$SDR_GAIN" -s "$SDR_SR" &
  LIVE=$!
  trap 'kill "$LIVE" 2>/dev/null' EXIT
  sleep 3
  kill -0 "$LIVE" 2>/dev/null || { echo "ERROR: SDR not found / busy"; exit 1; }
  # dumpcap drops privileges and can't write to a host bind-mount; capture to the
  # container's world-writable /tmp, then copy to the mount as root.
  TMP=/tmp/_rec.pcap
  tshark -i lo -f 'udp port 4729 and not icmp' -w "$TMP" -a duration:"$SECS"
  cp "$TMP" "$RECORD_PCAP"
  echo ">> recorded $RECORD_PCAP ($(tshark -r "$RECORD_PCAP" 2>/dev/null | wc -l) packets)"
  exit 0
fi

# ---- LIVE: demodulate the SDR ----------------------------------------------
: "${SDR_FREQ:?Set SDR_FREQ, e.g. -e SDR_FREQ=879.8M}"
echo ">> grgsm_livemon_headless args='$SDR_ARGS' f=$SDR_FREQ g=$SDR_GAIN sr=$SDR_SR -> lo:4729"
grgsm_livemon_headless --args="$SDR_ARGS" -f "$SDR_FREQ" -g "$SDR_GAIN" -s "$SDR_SR" &
LIVE=$!
trap 'kill "$LIVE" 2>/dev/null' EXIT
sleep 3
kill -0 "$LIVE" 2>/dev/null || { echo "ERROR: grgsm_livemon_headless exited (SDR not found / busy?)"; exit 1; }

export AUTOSTART_IMSI="${AUTOSTART_IMSI:-1}"
echo ">> GSMEvil2 on http://localhost:$PORT/   (/imsi/  /analytics/  /search/)"
exec /opt/venv/bin/python GsmEvil.py -p "$PORT" --host 0.0.0.0
