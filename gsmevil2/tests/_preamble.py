"""Shared test setup: put gsmevil2/ on sys.path and make it the cwd (routes read
database/imsi.db relative to cwd). Imported first by every test module; works the
same under pytest and the per-file __main__ runner."""
import os
import sys

GSMEVIL2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if GSMEVIL2 not in sys.path:
    sys.path.insert(0, GSMEVIL2)
os.chdir(GSMEVIL2)


def run_module(ns):
    """Tiny no-framework runner: call every test_* in a module's namespace."""
    import traceback
    fns = [v for k, v in sorted(ns.items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for f in fns:
        try:
            f()
            print("PASS", f.__name__)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL", f.__name__, "->", e)
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    return 1 if failed else 0
