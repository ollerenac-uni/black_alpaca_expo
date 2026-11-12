#!/bin/bash
# Terminal 1 of the 2G demo: demodulate a GSM downlink BCCH carrier with the
# USRP B210 and stream GSMTAP to lo:4729 (where GSMEvil2 listens).
#
# grgsm_livemon lives in the radioconda ENV, NOT in .gsmevil_venv. We call it by
# ABSOLUTE PATH so this works no matter which conda/venv is active in the shell.
# Usage: ./demo_livemon.sh [freq] [gain] [ppm]
# Defaults = strongest live cell (ARFCN 181, Movistar PE, found 2026-11-11).
# RTL-SDR overruns (flood of 'O') or PLL issues? run volk_profile once, then
# lower the sample rate:  SAMP_RATE=1e6 GRGSM_ARGS='' ./demo_livemon.sh 879.8M
LIVEMON="${GRGSM_LIVEMON:-$HOME/radioconda/bin/grgsm_livemon}"
# Device args: default = any B210. RTL-SDR: GRGSM_ARGS='' ./demo_livemon.sh
# Specific B210: GRGSM_ARGS='type=b200,serial=XXXX'
DEV_ARGS="${GRGSM_ARGS-type=b200}"
FREQ="${1:-879.8M}"
GAIN="${2:-40}"
PPM="${3:-0}"
SR_OPT=()
[ -n "${SAMP_RATE:-}" ] && SR_OPT=(-s "$SAMP_RATE")   # e.g. SAMP_RATE=1e6 for RTL
[ -x "$LIVEMON" ] || { echo "ERROR: grgsm_livemon not found at $LIVEMON (set GRGSM_LIVEMON)"; exit 1; }
echo ">> $LIVEMON  args='$DEV_ARGS'  f=$FREQ g=$GAIN ppm=$PPM sr='${SAMP_RATE:-default}' -> GSMTAP lo:4729"
echo ">> Healthy = scrolling hex that is NOT all '2b'. All 2b = wrong freq/weak signal."
exec "$LIVEMON" --args="$DEV_ARGS" -f "$FREQ" -g "$GAIN" -p "$PPM" "${SR_OPT[@]}"
