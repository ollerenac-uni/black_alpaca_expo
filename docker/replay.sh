#!/bin/bash
# Run the demo from recorded pcaps — NO SDR needed (venue with no live 2G).
# Loops forever; multiple pcaps play back-to-back (concatenated). Uses the image's
# baked-in capture history for rich /analytics/; mount a fresh db dir to start empty.
#
# Usage: ./replay.sh <dir-with-pcaps> [file1.pcap file2.pcap ...]
#   ./replay.sh ./recordings                 # all *.pcap in ./recordings (sorted)
#   ./replay.sh ./recordings rec_879M.pcap rec_892M.pcap
# Then open http://localhost/imsi/  /analytics/  /search/
set -e
DIR="${1:?dir with pcaps}"; shift || true
DIR="$(cd "$DIR" && pwd)"
IMAGE="${IMAGE:-black-alpaca-expo}"

if [ "$#" -gt 0 ]; then
  FILES=""; for f in "$@"; do FILES="$FILES /pcaps/$f"; done
else
  FILES="$(cd "$DIR" && ls *.pcap 2>/dev/null | sed 's#^#/pcaps/#' | tr '\n' ' ')"
fi
[ -n "${FILES// }" ] || { echo "no pcaps in $DIR"; exit 1; }

echo ">> replaying:$FILES (loop, no SDR) -> http://localhost/imsi/"
exec docker run --rm -it --cap-add NET_RAW --cap-add NET_ADMIN -p 127.0.0.1:80:80 \
  -v "$DIR":/pcaps:ro \
  -e REPLAY_PCAP="$FILES" \
  "$IMAGE"
