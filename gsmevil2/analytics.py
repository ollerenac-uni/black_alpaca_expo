"""
Read-only analytics over the captured imsi.db for the 2G-privacy demo.

Two views, both from already-captured data (no live capture, separate RO conn):
  - overview: unique (MCC,MNC) home-network combos, subscriber counts, foreign flag
  - drilldown: per-IMSI presence (hits, first/last seen) for one MCC+MNC

MCC/MNC come from the e212 fields of the paging packet = the SUBSCRIBER's home
network, so a foreign MCC = a roaming/foreign SIM seen passively.

ponytail: date_time is stored as "%H:%M:%S %Y-%m-%d" (time first). MIN/MAX order
correctly within a single day (the demo case). Cross-day ordering would need an
ISO timestamp in save_data(); upgrade there if the demo ever spans midnight.
"""
import os
import sqlite3

LOCAL_MCC = int(os.environ.get("DEMO_LOCAL_MCC", "716"))  # 716 = Peru

# Compact MCC->country map: local + the ones realistically seen roaming. Unknown
# MCCs fall back to "MCC <n>" so a foreign SIM is never hidden, only unlabeled.
MCC_COUNTRY = {
    716: "Peru", 730: "Chile", 740: "Ecuador", 732: "Colombia", 724: "Brazil",
    722: "Argentina", 736: "Bolivia", 744: "Paraguay", 748: "Uruguay",
    734: "Venezuela", 310: "USA", 311: "USA", 312: "USA", 313: "USA", 316: "USA",
    302: "Canada", 334: "Mexico", 214: "Spain", 234: "UK", 262: "Germany",
    208: "France", 222: "Italy", 460: "China", 440: "Japan", 450: "South Korea",
    404: "India", 405: "India", 250: "Russia", 714: "Panama", 710: "Nicaragua",
    712: "Costa Rica", 706: "El Salvador", 704: "Guatemala", 708: "Honduras",
    530: "New Zealand", 602: "Egypt", 505: "Australia", 525: "Singapore",
    510: "Indonesia", 272: "Ireland", 204: "Netherlands", 228: "Switzerland",
    260: "Poland", 240: "Sweden", 238: "Denmark", 242: "Norway", 268: "Portugal",
}

# Peru operator names by MNC (home-network labeling for the local case).
PE_MNC = {0: "Claro", 10: "Claro", 6: "Movistar", 7: "Movistar", 60: "Movistar",
          15: "Entel", 17: "Entel", 20: "Bitel", 2: "Bitel"}


def country_for(mcc):
    try:
        mcc = int(mcc)
    except (TypeError, ValueError):
        return "Unknown"
    return MCC_COUNTRY.get(mcc, f"MCC {mcc}")


def operator_for(mcc, mnc):
    try:
        mcc, mnc = int(mcc), int(mnc)
    except (TypeError, ValueError):
        return ""
    if mcc == LOCAL_MCC:
        return PE_MNC.get(mnc, f"MNC {mnc}")
    return f"MNC {mnc}"


def _connect_ro(db_path):
    # Read-only URI connection: never writes, never disturbs the live sniffer's
    # own connection to the same file.
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def imsi_analytics(db_path, mcc=None, mnc=None, local_mcc=LOCAL_MCC):
    """Return a dict the template renders. Safe on missing/empty DB."""
    result = {
        "mode": "overview",
        "local_mcc": local_mcc,
        "totals": {"subscribers": 0, "combos": 0, "foreign_subscribers": 0, "hits": 0},
        "rows": [],
        "selected": None,
    }
    if not os.path.exists(db_path):
        return result
    con = _connect_ro(db_path)
    try:
        cur = con.cursor()
        # Totals
        cur.execute("SELECT COUNT(DISTINCT imsi), COUNT(*), COUNT(DISTINCT mcc||'-'||mnc) FROM imsi_data")
        subs, hits, combos = cur.fetchone()
        cur.execute("SELECT COUNT(DISTINCT imsi) FROM imsi_data WHERE mcc != ?", (local_mcc,))
        foreign = cur.fetchone()[0]
        result["totals"] = {"subscribers": subs or 0, "combos": combos or 0,
                            "foreign_subscribers": foreign or 0, "hits": hits or 0}

        if mcc is not None and mnc is not None:
            # Drilldown: per-IMSI presence for one home network.
            result["mode"] = "drilldown"
            result["selected"] = {"mcc": int(mcc), "mnc": int(mnc),
                                  "country": country_for(mcc),
                                  "operator": operator_for(mcc, mnc),
                                  "foreign": int(mcc) != local_mcc}
            cur.execute(
                """SELECT imsi, COUNT(*) hits, MIN(date_time) first_seen,
                          MAX(date_time) last_seen, COUNT(DISTINCT NULLIF(tmsi,'')) tmsi_count
                   FROM imsi_data WHERE mcc=? AND mnc=?
                   GROUP BY imsi ORDER BY hits DESC, last_seen DESC""",
                (int(mcc), int(mnc)))
            for imsi, h, first, last, tc in cur.fetchall():
                result["rows"].append({"imsi": imsi, "hits": h, "first_seen": first,
                                       "last_seen": last, "tmsi_count": tc})
        else:
            # Overview: one row per (MCC,MNC) home network.
            cur.execute(
                """SELECT mcc, mnc, COUNT(DISTINCT imsi) subs, COUNT(*) hits,
                          MIN(date_time) first_seen, MAX(date_time) last_seen
                   FROM imsi_data GROUP BY mcc, mnc ORDER BY subs DESC, hits DESC""")
            for mcc_, mnc_, subs_, hits_, first, last in cur.fetchall():
                result["rows"].append({
                    "mcc": mcc_, "mnc": mnc_, "subscribers": subs_, "hits": hits_,
                    "first_seen": first, "last_seen": last,
                    "country": country_for(mcc_), "operator": operator_for(mcc_, mnc_),
                    "foreign": (mcc_ is not None and int(mcc_) != local_mcc)})
    finally:
        con.close()
    return result


if __name__ == "__main__":
    # ponytail self-check: build a temp DB, verify overview + drilldown + foreign flag.
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "imsi.db")
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE imsi_data(id INTEGER PRIMARY KEY, imsi TEXT, tmsi TEXT, mcc INTEGER, mnc INTEGER, lac INTEGER, ci INTEGER, date_time timestamp)")
    rows = [
        ("716060857701849", "", 716, 6, 2306, 17292, "19:16:21 2026-11-11"),
        ("716060857701849", "", 716, 6, 2306, 17292, "19:16:27 2026-11-11"),  # repeat -> presence
        ("716100111222333", "T1", 716, 10, 1287, 11378, "19:10:00 2026-11-11"),
        ("310260999888777", "", 310, 260, 2306, 17292, "19:20:00 2026-11-11"),  # USA roamer
    ]
    for r in rows:
        c.execute("INSERT INTO imsi_data(imsi,tmsi,mcc,mnc,lac,ci,date_time) VALUES (?,?,?,?,?,?,?)", r)
    c.commit(); c.close()

    ov = imsi_analytics(p)
    assert ov["totals"]["subscribers"] == 3, ov["totals"]
    assert ov["totals"]["combos"] == 3
    assert ov["totals"]["foreign_subscribers"] == 1, "one USA IMSI"
    assert any(r["foreign"] and r["country"] == "USA" for r in ov["rows"]), "USA flagged foreign"
    assert any((not r["foreign"]) and r["operator"] == "Movistar" for r in ov["rows"])

    dd = imsi_analytics(p, mcc=716, mnc=6)
    assert dd["mode"] == "drilldown"
    assert dd["rows"][0]["imsi"] == "716060857701849"
    assert dd["rows"][0]["hits"] == 2, "repeat IMSI counted as presence"
    assert dd["selected"]["foreign"] is False

    # Missing DB must not crash.
    assert imsi_analytics(os.path.join(d, "nope.db"))["totals"]["subscribers"] == 0
    print("OK analytics self-check: overview, drilldown, foreign flag, presence, empty-safe")
