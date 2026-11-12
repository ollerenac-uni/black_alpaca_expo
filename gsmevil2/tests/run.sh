#!/bin/bash
# Run the test suite. Prefers pytest if available, else the no-framework runners.
# Needs a python with the app deps (flask, pyshark) — e.g. the GSMEvil2 venv:
#   PY=../.gsmevil_venv/bin/python ./run.sh
set -e
cd "$(dirname "$0")"
PY="${PY:-python3}"
if "$PY" -c "import pytest" 2>/dev/null; then
  exec "$PY" -m pytest -q
fi
echo "(pytest not found — running files directly)"
rc=0
for t in test_*.py; do
  echo "=== $t ==="
  "$PY" "$t" || rc=1
done
exit $rc
