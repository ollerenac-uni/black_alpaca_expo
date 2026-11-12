"""Regression test for the imsi_id crash.

Before the fix, ImsiEvil.filter_imsi() only set self.imsi_id inside save_data(),
which it skips when an IMSI is already in the DB with the same TMSI. On a restart
(imsi_live_db empty) that path hit line 109 -> AttributeError. These tests drive
the three branches with stubs (no real DB, no socketio) and assert imsi_id is
always set and the live dict is seeded with the right id."""
import _preamble  # noqa: F401
import GsmEvil


def _evil(data, imsi, tmsi="", mcc=716, mnc=6):
    e = GsmEvil.ImsiEvil()
    e.sql_db = lambda: None                    # no real sqlite
    e.get_data = lambda: None                  # self.data preset below
    e.output = lambda: None                    # no socketio
    e.update_data = lambda *a: None
    e.save_data = lambda: setattr(e, "imsi_id", 9999)  # the "new row" id
    e.imsi, e.tmsi, e.mcc, e.mnc = imsi, tmsi, mcc, mnc
    e.data = data
    return e


def test_repeat_imsi_after_restart_no_crash():
    # Row columns: id, imsi, tmsi, mcc, mnc, lac, ci, date_time
    GsmEvil.imsi_live_db = {}                   # fresh restart: empty live dict
    row = (1184, "716060857701849", "T1", 716, 6, 2306, 17292, "ts")
    e = _evil([row], imsi="716060857701849", tmsi="T1")
    e.filter_imsi()                             # must NOT raise AttributeError
    assert e.imsi_id == 1184                    # reused existing row id
    assert GsmEvil.imsi_live_db["716060857701849"]["id"] == 1184


def test_new_imsi_uses_saved_id():
    GsmEvil.imsi_live_db = {}
    e = _evil([], imsi="716999000111222", tmsi="")   # empty data -> save_data path
    e.filter_imsi()
    assert e.imsi_id == 9999
    assert GsmEvil.imsi_live_db["716999000111222"]["id"] == 9999


def test_changed_imsi_uses_saved_id():
    GsmEvil.imsi_live_db = {}
    row = (500, "716000000000001", "", 716, 6, 2306, 17292, "ts")
    e = _evil([row], imsi="716000000000002", tmsi="")  # differs from stored imsi
    e.filter_imsi()
    assert e.imsi_id == 9999                    # save_data branch


if __name__ == "__main__":
    raise SystemExit(_preamble.run_module(globals()))
