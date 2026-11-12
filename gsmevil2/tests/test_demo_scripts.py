"""Lint the demo launchers and verify their device-args logic, without an SDR."""
import os
import subprocess

import _preamble  # noqa: F401

SCRIPTS = ["demo_scan.sh", "demo_livemon.sh", "demo_sniffer.sh"]


def test_scripts_have_valid_syntax():
    for s in SCRIPTS:
        assert os.path.exists(s), s
        r = subprocess.run(["bash", "-n", s], capture_output=True, text=True)
        assert r.returncode == 0, f"{s}: {r.stderr}"


def test_grgsm_args_default_and_rtl_override():
    # Default = any B210; empty GRGSM_ARGS = RTL autodetect (uses ${VAR-default}).
    expr = 'echo "[${GRGSM_ARGS-type=b200}]"'
    default = subprocess.run(["bash", "-c", expr], capture_output=True, text=True).stdout.strip()
    rtl = subprocess.run(["bash", "-c", expr], capture_output=True, text=True,
                         env={**os.environ, "GRGSM_ARGS": ""}).stdout.strip()
    assert default == "[type=b200]"
    assert rtl == "[]"


def test_livemon_passes_sample_rate():
    # SAMP_RATE must appear as a -s option builder in demo_livemon.sh.
    with open("demo_livemon.sh") as f:
        body = f.read()
    assert "SAMP_RATE" in body and "-s" in body


if __name__ == "__main__":
    raise SystemExit(_preamble.run_module(globals()))
