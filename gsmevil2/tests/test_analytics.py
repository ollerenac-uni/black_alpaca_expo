"""Unit tests for analytics.py (overview, drilldown, lookup, labels) against a
controlled temp DB — no hardware, no Flask. Mirrors analytics.py's self-check."""
import os
import sqlite3
import tempfile

import _preamble  # noqa: F401  (sets sys.path/cwd)
import analytics


def _db():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "imsi.db")
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE imsi_data(id INTEGER PRIMARY KEY, imsi TEXT, tmsi TEXT, "
              "mcc INTEGER, mnc INTEGER, lac INTEGER, ci INTEGER, date_time timestamp)")
    rows = [
        ("716060857701849", "",   716, 6,  2306, 17292, "19:16:21 2026-11-11"),
        ("716060857701849", "",   716, 6,  2306, 17292, "19:16:27 2026-11-11"),  # repeat
        ("716100111222333", "T1", 716, 10, 1287, 11378, "19:10:00 2026-11-11"),
        ("310260999888777", "",   310, 260, 2306, 17292, "19:20:00 2026-11-11"),  # USA roamer
    ]
    for r in rows:
        c.execute("INSERT INTO imsi_data(imsi,tmsi,mcc,mnc,lac,ci,date_time) "
                  "VALUES (?,?,?,?,?,?,?)", r)
    c.commit(); c.close()
    return p


def test_overview_counts_and_foreign_flag():
    ov = analytics.imsi_analytics(_db())
    assert ov["totals"]["subscribers"] == 3
    assert ov["totals"]["combos"] == 3
    assert ov["totals"]["foreign_subscribers"] == 1
    assert any(r["foreign"] and r["country"] == "USA" for r in ov["rows"])
    assert any((not r["foreign"]) and r["operator"] == "Movistar" for r in ov["rows"])


def test_drilldown_presence():
    dd = analytics.imsi_analytics(_db(), mcc=716, mnc=6)
    assert dd["mode"] == "drilldown"
    assert dd["rows"][0]["imsi"] == "716060857701849"
    assert dd["rows"][0]["hits"] == 2          # repeat counted as presence
    assert dd["selected"]["foreign"] is False


def test_lookup_full_and_partial():
    p = _db()
    full = analytics.imsi_lookup(p, "716060857701849")
    assert full["found"] and full["rows"][0]["hits"] == 2
    assert full["total_subscribers"] == 3
    partial = analytics.imsi_lookup(p, "701849")      # last digits only
    assert partial["found"] and partial["match_count"] == 1


def test_lookup_miss_and_too_short():
    p = _db()
    assert analytics.imsi_lookup(p, "000000000000000")["found"] is False
    assert analytics.imsi_lookup(p, "12")["too_short"] is True


def test_lookup_injection_safe():
    inj = analytics.imsi_lookup(_db(), "7160' OR '1'='1")
    assert inj["digits"] == "716011"          # non-digits stripped
    assert inj["found"] is False              # treated as literal, no match-all


def test_empty_and_missing_db_safe():
    assert analytics.imsi_analytics("/nonexistent/imsi.db")["totals"]["subscribers"] == 0
    assert analytics.imsi_lookup("/nonexistent/imsi.db", "123456")["found"] is False


if __name__ == "__main__":
    raise SystemExit(_preamble.run_module(globals()))
