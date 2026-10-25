from datetime import date
import pandas as pd
from .models import PlazaDashboardData

class PlazaDashboardService:
    def available_plazas(self):
        # Production implementation will read energy_master.plaza.
        return ["TP01", "TP02", "TP03"]

    def get_dashboard(self, plaza: str, from_date: date, to_date: date):
        return PlazaDashboardData(
            plaza_id=plaza,
            plaza_name=plaza,
            asset_rows=pd.DataFrame(columns=[
                "Asset Type", "Asset", "Status", "Latest Reading",
                "Key KPI", "Exceptions"
            ]),
            trend_rows=pd.DataFrame(columns=[
                "Date", "EB kWh", "DG kWh", "Solar kWh"
            ]),
            exceptions=pd.DataFrame(columns=[
                "Severity", "Rule", "Asset", "Date", "Status"
            ]),
        )

    def get_asset_kpis(self, plaza, asset_type, from_date, to_date):
        # Production: query Phase 3.3 KPI result by plaza and asset type.
        return pd.DataFrame()

    def get_asset_latest_status(self, plaza):
        # Production: derive from latest normalized reading/asset status.
        return pd.DataFrame()
