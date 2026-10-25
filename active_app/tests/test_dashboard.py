from datetime import date
from dashboard.filters import DashboardFilter
from dashboard.services import DashboardService

def test_filter_valid():
    f = DashboardFilter(date(2026, 9, 1), date(2026, 9, 30), ("TP01","TP02","TP03"))
    f.validate()

def test_filter_invalid_date():
    f = DashboardFilter(date(2026, 9, 30), date(2026, 9, 1), ("TP01",))
    try:
        f.validate()
        assert False
    except ValueError:
        assert True

def test_filter_invalid_plaza():
    f = DashboardFilter(date(2026, 9, 1), date(2026, 9, 30), ("TP99",))
    try:
        f.validate()
        assert False
    except ValueError:
        assert True

def test_empty_summary_is_safe():
    result = DashboardService().executive_summary(
        date(2026,9,1), date(2026,9,30), ["TP01"]
    )
    assert result.exception_count == 0
    assert result.plaza_rows.empty
