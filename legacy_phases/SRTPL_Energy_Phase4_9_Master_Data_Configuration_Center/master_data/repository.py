import pandas as pd

class MasterDataRepository:
    def plazas(self):
        return pd.DataFrame(columns=["ID", "Code", "Name", "Active"])

    def assets(self):
        return pd.DataFrame(columns=["ID", "Code", "Type", "Plaza", "Location", "Active"])

    def parameters(self):
        return pd.DataFrame(columns=[
            "ID", "Code", "Name", "Unit", "Data Type", "Cumulative", "Active"
        ])

    def asset_parameters(self):
        return pd.DataFrame(columns=[
            "ID", "Asset", "Parameter", "Required", "Frequency", "Active"
        ])

    def thresholds(self):
        return pd.DataFrame(columns=[
            "ID", "Parameter", "Condition", "Warning", "Critical", "Unit", "Active"
        ])

    def tariffs(self):
        return pd.DataFrame(columns=[
            "ID", "Code", "Name", "Energy Rate", "Demand Rate",
            "Fixed Charge", "Effective From", "Effective To", "Active"
        ])

    def kpis(self):
        return pd.DataFrame(columns=[
            "ID", "Code", "Name", "Formula", "Unit", "Scope", "Version", "Active"
        ])

    def source_mappings(self):
        return pd.DataFrame(columns=[
            "ID", "Report Type", "Source Column", "Target Parameter",
            "Transform", "Required", "Active"
        ])

    def report_schedules(self):
        return pd.DataFrame(columns=[
            "ID", "Report Code", "Frequency", "Recipient Scope",
            "Active", "Last Run", "Next Run"
        ])
