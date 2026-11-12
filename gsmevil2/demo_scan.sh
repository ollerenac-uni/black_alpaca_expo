#!/bin/bash
# Find live GSM cells with the B210 (run in any shell; uses radioconda by path).
# Usage: ./demo_scan.sh [band]   band default GSM850 (also: GSM900, DCS1800, PCS1900, EGSM...)
# Device args: default = any B210. RTL-SDR: GRGSM_ARGS='' ./demo_scan.sh
SCANNER="${GRGSM_SCANNER:-$HOME/radioconda/bin/grgsm_scanner}"
DEV_ARGS="${GRGSM_ARGS-type=b200}"
BAND="${1:-GSM850}"
[ -x "$SCANNER" ] || { echo "ERROR: grgsm_scanner not found at $SCANNER"; exit 1; }
echo ">> scanning $BAND  args='$DEV_ARGS' ..."
exec "$SCANNER" --args="$DEV_ARGS" -b "$BAND" -s 2e6
