from dataclasses import dataclass
import pandas as pd

@dataclass
class PlazaDashboardData:
    plaza_id: str
    plaza_name: str
    eb_kwh: float | None = None
    dg_kwh: float | None = None
    solar_kwh: float | None = None
    eb_cost: float | None = None
    dg_cost: float | None = None
    solar_saving: float | None = None
    energy_cost_per_kwh: float | None = None
    dg_runtime: float | None = None
    dg_efficiency: float | None = None
    eb_pf: float | None = None
    dg_pf: float | None = None
    data_quality: float | None = None
    exception_count: int = 0
    asset_rows: pd.DataFrame | None = None
    trend_rows: pd.DataFrame | None = None
    exceptions: pd.DataFrame | None = None
