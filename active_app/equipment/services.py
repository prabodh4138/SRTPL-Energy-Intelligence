from datetime import date
import pandas as pd
from .models import EquipmentDashboardData

SUPPORTED = ["SOLAR", "DG", "EB", "TRANSFORMER", "UPS"]

class EquipmentDashboardService:
    def available_types(self):
        return SUPPORTED

    def available_assets(self, source_type, plaza=None):
        from core.demo_store import is_demo_mode, ASSETS_BY_TYPE
        if is_demo_mode():
            return ASSETS_BY_TYPE.get(source_type.upper(), [])
        return []

    def get_dashboard(self, source_type, asset_id, from_date: date, to_date: date):
        from core.demo_store import is_demo_mode, get_demo_equipment_dashboard
        if is_demo_mode():
            return get_demo_equipment_dashboard(source_type, asset_id, from_date, to_date)

        return EquipmentDashboardData(
            source_type=source_type,
            asset_id=asset_id,
            asset_name=asset_id,
            plaza="",
            kpis=pd.DataFrame(columns=["KPI", "Value", "Unit", "Status"]),
            latest=pd.DataFrame(columns=["Parameter", "Value", "Unit", "Timestamp"]),
            trend=pd.DataFrame(columns=["Timestamp", "Parameter", "Value"]),
            exceptions=pd.DataFrame(columns=["Severity", "Rule", "Date", "Status"]),
            parameters=pd.DataFrame(columns=["Parameter", "Unit", "Source", "Latest Value"]),
        )

    def trace_source(self, source_reading_id):
        # Production implementation should return:
        # normalized reading -> raw JUNO -> import row -> original CSV.
        return pd.DataFrame(columns=[
            "Level", "ID", "Reference", "Timestamp"
        ])
