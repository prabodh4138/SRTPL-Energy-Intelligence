from dataclasses import dataclass
import pandas as pd

@dataclass
class EquipmentDashboardData:
    source_type: str
    asset_id: str
    asset_name: str
    plaza: str
    kpis: pd.DataFrame
    latest: pd.DataFrame
    trend: pd.DataFrame
    exceptions: pd.DataFrame
    parameters: pd.DataFrame
