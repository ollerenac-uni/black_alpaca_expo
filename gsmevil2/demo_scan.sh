#!/bin/bash
# Find live GSM cells with the B210 (run in any shell; uses radioconda by path).
# Usage: ./demo_scan.sh [band]   band default GSM850 (also: GSM900, DCS1800, PCS1900, EGSM...)
SCANNER="${GRGSM_SCANNER:-$HOME/radioconda/bin/grgsm_scanner}"
BAND="${1:-GSM850}"
[ -x "$SCANNER" ] || { echo "ERROR: grgsm_scanner not found at $SCANNER"; exit 1; }
echo ">> scanning $BAND with B210 (serial=KUDOS) ..."
exec "$SCANNER" --args='uhd,type=b200,serial=KUDOS' -b "$BAND" -s 2e6
