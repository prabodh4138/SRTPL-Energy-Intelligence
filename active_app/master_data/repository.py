import pandas as pd

class MasterDataRepository:
    def _demo_or_empty(self, domain, empty_cols):
        from core.demo_store import is_demo_mode, get_demo_master_data
        if is_demo_mode():
            df = get_demo_master_data(domain)
            if not df.empty:
                return df
        return pd.DataFrame(columns=empty_cols)

    def plazas(self):
        try:
            from core.db_sync import get_all_plazas
            df = get_all_plazas()
            if not df.empty:
                return df.rename(columns={
                    "plaza_id": "ID",
                    "plaza_name": "Name",
                    "location": "Location",
                    "is_active": "Active",
                })
        except Exception:
            pass
        return self._demo_or_empty("PLAZA", ["ID", "Code", "Name", "Active"])

    def assets(self):
        try:
            from core.db_sync import get_all_assets
            df = get_all_assets()
            if not df.empty:
                return df.rename(columns={
                    "asset_id": "ID",
                    "asset_code": "Code",
                    "asset_name": "Name",
                    "source_type": "Type",
                    "plaza_id": "Plaza",
                    "is_active": "Active",
                })
        except Exception:
            pass
        return self._demo_or_empty("ASSET", ["ID", "Code", "Type", "Plaza", "Location", "Active"])

    def parameters(self):
        return self._demo_or_empty("PARAMETER", [
            "ID", "Code", "Name", "Unit", "Data Type", "Cumulative", "Active"
        ])

    def asset_parameters(self):
        return self._demo_or_empty("ASSET_PARAMETER", [
            "ID", "Asset", "Parameter", "Required", "Frequency", "Active"
        ])

    def thresholds(self):
        return self._demo_or_empty("THRESHOLD", [
            "ID", "Parameter", "Condition", "Warning", "Critical", "Unit", "Active"
        ])

    def tariffs(self):
        return self._demo_or_empty("TARIFF", [
            "ID", "Code", "Name", "Energy Rate", "Demand Rate",
            "Fixed Charge", "Effective From", "Effective To", "Active"
        ])

    def kpis(self):
        return self._demo_or_empty("KPI", [
            "ID", "Code", "Name", "Formula", "Unit", "Scope", "Version", "Active"
        ])

    def source_mappings(self):
        return self._demo_or_empty("SOURCE_MAPPING", [
            "ID", "Report Type", "Source Column", "Target Parameter",
            "Transform", "Required", "Active"
        ])

    def report_schedules(self):
        return self._demo_or_empty("SCHEDULE", [
            "ID", "Report Code", "Frequency", "Recipient Scope",
            "Active", "Last Run", "Next Run"
        ])
