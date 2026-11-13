#!/bin/bash
# Record N seconds of live GSMTAP from ONE base station into a pcap, for offline
# replay later (see replay.sh). Run this now, while 2G cells are in range.
#
# Usage: ./record.sh <freq> [seconds] [outfile] [sdr_args]
#   ./record.sh 879.8M 600 rec_879M.pcap type=b200     # B210, 10 min
#   ./record.sh 892.2M 600 rec_892M.pcap rtl=0         # RTL-SDR
#
# Produces a few MB per 10 min. Record each strong BCCH carrier once.
set -e
FREQ="${1:?freq, e.g. 879.8M}"
SECS="${2:-600}"
OUT="${3:-rec_${FREQ}.pcap}"
ARGS="${4:-type=b200}"
IMAGE="${IMAGE:-black-alpaca-expo}"

mkdir -p "$(dirname "$OUT")"
OUTDIR="$(cd "$(dirname "$OUT")" && pwd)"
OUTBASE="$(basename "$OUT")"

echo ">> recording ${SECS}s @ $FREQ (args=$ARGS) -> $OUTDIR/$OUTBASE"
docker run --rm --cap-add SYS_RAWIO --cap-add NET_RAW --cap-add NET_ADMIN --device /dev/bus/usb \
  -v "$OUTDIR":/out \
  -e SDR_FREQ="$FREQ" -e SDR_ARGS="$ARGS" -e SDR_SR=2e6 -e SDR_GAIN=42 \
  -e RECORD_PCAP="/out/$OUTBASE" -e RECORD_SECONDS="$SECS" \
  "$IMAGE"
echo ">> saved $OUTDIR/$OUTBASE"
