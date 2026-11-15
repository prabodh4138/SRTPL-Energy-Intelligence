from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import pandas as pd

@dataclass
class DashboardSummary:
    total_eb_kwh: float | None = None
    total_dg_kwh: float | None = None
    total_solar_kwh: float | None = None
    eb_cost: float | None = None
    dg_cost: float | None = None
    solar_saving: float | None = None
    energy_cost_per_kwh: float | None = None
    exception_count: int = 0
    data_quality_percent: float | None = None
    plaza_rows: pd.DataFrame | None = None
    trend_rows: pd.DataFrame | None = None

class DashboardService:
    """Read-only dashboard service."""

    def executive_summary(self, from_date: date, to_date: date, plazas: list[str]) -> DashboardSummary:
        from core.demo_store import is_demo_mode, get_demo_executive_summary
        if is_demo_mode():
            return get_demo_executive_summary(from_date, to_date, plazas)

        return DashboardSummary(
            plaza_rows=pd.DataFrame(columns=[
                "Plaza", "EB kWh", "DG kWh", "Solar kWh",
                "Energy Cost", "Solar Saving", "Data Quality %", "Exceptions"
            ]),
            trend_rows=pd.DataFrame(columns=[
                "Date", "EB kWh", "DG kWh", "Solar kWh"
            ]),
        )

    def fetch_kpi(self, kpi_code: str, from_date: date, to_date: date, plazas: list[str]) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_exceptions(self, from_date: date, to_date: date, plazas: list[str]) -> pd.DataFrame:
        return pd.DataFrame()
