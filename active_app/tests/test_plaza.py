from datetime import date
from plaza.filters import PlazaFilter
from plaza.services import PlazaDashboardService

def test_filter():
    f = PlazaFilter("TP01", date(2026,9,1), date(2026,9,30))
    f.validate()

def test_invalid_date():
    f = PlazaFilter("TP01", date(2026,9,30), date(2026,9,1))
    try:
        f.validate()
        assert False
    except ValueError:
        assert True

def test_service_empty_state():
    d = PlazaDashboardService().get_dashboard("TP01", date(2026,9,1), date(2026,9,30))
    assert d.plaza_id == "TP01"
    assert d.asset_rows.empty
    assert d.exceptions.empty
