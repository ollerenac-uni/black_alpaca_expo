"""Flask route smoke tests via test_client (no hardware). Uses the real
database/imsi.db, so assertions are loose (status + key markup), not exact counts.
Also checks /search/ handles a SQL-injection string without error or dumping."""
import _preamble  # noqa: F401
import GsmEvil

client = GsmEvil.app.test_client()


def test_static_pages_render():
    for path in ("/", "/imsi/", "/sms/"):
        assert client.get(path).status_code == 200, path


def test_analytics_overview_and_drilldown():
    r = client.get("/analytics/")
    assert r.status_code == 200 and "<table" in r.get_data(as_text=True)
    r2 = client.get("/analytics/?mcc=716&mnc=6")
    assert r2.status_code == 200


def test_search_empty_shows_form():
    r = client.get("/search/")
    assert r.status_code == 200 and "<form" in r.get_data(as_text=True)


def test_search_too_short():
    r = client.get("/search/?imsi=12")
    assert r.status_code == 200 and "4" in r.get_data(as_text=True)


def test_search_injection_is_safe():
    # Must not 500 and must not report a FOUND verdict from a SQL metachar.
    r = client.get("/search/?imsi=' OR '1'='1")
    assert r.status_code == 200
    assert "ENCONTRADO" not in r.get_data(as_text=True)


if __name__ == "__main__":
    raise SystemExit(_preamble.run_module(globals()))
