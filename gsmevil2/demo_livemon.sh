#!/bin/bash
# Terminal 1 of the 2G demo: demodulate a GSM downlink BCCH carrier with the
# USRP B210 and stream GSMTAP to lo:4729 (where GSMEvil2 listens).
#
# grgsm_livemon lives in the radioconda ENV, NOT in .gsmevil_venv. We call it by
# ABSOLUTE PATH so this works no matter which conda/venv is active in the shell.
# Usage: ./demo_livemon.sh [freq] [gain] [ppm]
# Defaults = strongest live cell (ARFCN 181, Movistar PE, found 2026-11-11).
LIVEMON="${GRGSM_LIVEMON:-$HOME/radioconda/bin/grgsm_livemon}"
FREQ="${1:-879.8M}"
GAIN="${2:-40}"
PPM="${3:-0}"
[ -x "$LIVEMON" ] || { echo "ERROR: grgsm_livemon not found at $LIVEMON (set GRGSM_LIVEMON)"; exit 1; }
echo ">> $LIVEMON  B210(serial=KUDOS)  f=$FREQ g=$GAIN ppm=$PPM -> GSMTAP lo:4729"
echo ">> Healthy = scrolling hex that is NOT all '2b'. All 2b = wrong freq/weak signal."
exec "$LIVEMON" --args='uhd,type=b200,serial=KUDOS' -f "$FREQ" -g "$GAIN" -p "$PPM"
