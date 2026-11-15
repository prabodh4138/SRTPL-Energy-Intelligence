from __future__ import annotations

from datetime import date
from typing import Any
import pandas as pd
from .models import EquipmentDashboardData
from core.cloud_views_service import fetch_asset_latest_readings_from_sql_view
from core.local_db import get_sqlite_connection

SUPPORTED = ["EB", "DG", "SOLAR", "TRANSFORMER", "UPS"]


class EquipmentDashboardService:
    def available_types(self) -> list[str]:
        return SUPPORTED

    def available_assets(self, source_type: str, plaza: str | None = None) -> list[str]:
        from core.demo_store import is_demo_mode, ASSETS_BY_TYPE
        if is_demo_mode():
            return ASSETS_BY_TYPE.get(source_type.upper(), [])
        return []

    def get_dashboard(self, source_type: str, asset_id: str, from_date: date, to_date: date) -> EquipmentDashboardData:
        stype = source_type.lower().strip()
        df_latest = fetch_asset_latest_readings_from_sql_view(stype)

        asset_row: dict[str, Any] = {}
        if not df_latest.empty and "asset_code" in df_latest.columns:
            matched = df_latest[df_latest["asset_code"] == asset_id]
            if not matched.empty:
                asset_row = matched.iloc[0].to_dict()

        asset_name = asset_row.get("asset_name") or asset_id
        plaza = asset_row.get("plaza_id") or ""
        ts = asset_row.get("reading_datetime") or "—"
        status = asset_row.get("data_quality_status") or "VALID"

        # Construct Parameter and KPI rows based on module
        latest_params = []
        kpis_list = []

        if stype == "eb":
            kwh = asset_row.get("latest_cumulative_kwh")
            kvah = asset_row.get("latest_cumulative_kvah")
            pf = asset_row.get("latest_pf")
            md = asset_row.get("latest_maximum_demand")

            kpis_list = [
                {"KPI": "Active Energy", "Value": kwh if pd.notna(kwh) else 0.0, "Unit": "kWh", "Status": status},
                {"KPI": "Apparent Energy", "Value": kvah if pd.notna(kvah) else 0.0, "Unit": "kVAh", "Status": status},
                {"KPI": "Power Factor", "Value": pf if pd.notna(pf) else 0.98, "Unit": "PF", "Status": status},
                {"KPI": "Maximum Demand", "Value": md if pd.notna(md) else 0.0, "Unit": "kVA", "Status": status},
            ]
            latest_params = [
                {"Parameter": "Cumulative kWh", "Value": kwh, "Unit": "kWh", "Timestamp": ts},
                {"Parameter": "Cumulative kVAh", "Value": kvah, "Unit": "kVAh", "Timestamp": ts},
                {"Parameter": "Power Factor", "Value": pf, "Unit": "PF", "Timestamp": ts},
                {"Parameter": "Peak Demand", "Value": md, "Unit": "kVA", "Timestamp": ts},
            ]
        elif stype == "dg":
            kwh = asset_row.get("latest_cumulative_kwh")
            hrs = asset_row.get("latest_run_hours")
            fuel = asset_row.get("latest_fuel_level")
            load = asset_row.get("latest_load_pct")

            kpis_list = [
                {"KPI": "Backup Generation", "Value": kwh if pd.notna(kwh) else 0.0, "Unit": "kWh", "Status": status},
                {"KPI": "Cumulative Run Hours", "Value": hrs if pd.notna(hrs) else 0.0, "Unit": "Hrs", "Status": status},
                {"KPI": "Fuel Level", "Value": fuel if pd.notna(fuel) else 0.0, "Unit": "L", "Status": status},
                {"KPI": "Load %", "Value": load if pd.notna(load) else 0.0, "Unit": "%", "Status": status},
            ]
            latest_params = [
                {"Parameter": "Generation (kWh)", "Value": kwh, "Unit": "kWh", "Timestamp": ts},
                {"Parameter": "Run Hours", "Value": hrs, "Unit": "Hrs", "Timestamp": ts},
                {"Parameter": "Fuel Level", "Value": fuel, "Unit": "L", "Timestamp": ts},
                {"Parameter": "Load Percent", "Value": load, "Unit": "%", "Timestamp": ts},
            ]
        elif stype == "solar":
            kwh = asset_row.get("latest_cumulative_kwh")
            interval_kwh = asset_row.get("latest_interval_kwh")
            co2 = round((float(kwh or 0.0)) * 0.82, 2)

            kpis_list = [
                {"KPI": "Clean Solar Generation", "Value": kwh if pd.notna(kwh) else 0.0, "Unit": "kWh", "Status": status},
                {"KPI": "Recent Generation", "Value": interval_kwh if pd.notna(interval_kwh) else 0.0, "Unit": "kWh", "Status": status},
                {"KPI": "CO2 Avoided", "Value": co2, "Unit": "kg", "Status": status},
            ]
            latest_params = [
                {"Parameter": "Cumulative Clean Energy", "Value": kwh, "Unit": "kWh", "Timestamp": ts},
                {"Parameter": "Interval Clean Energy", "Value": interval_kwh, "Unit": "kWh", "Timestamp": ts},
                {"Parameter": "CO2 Offset", "Value": co2, "Unit": "kg", "Timestamp": ts},
            ]
        elif stype == "transformer":
            kwh = asset_row.get("latest_cumulative_kwh")
            oil = asset_row.get("latest_oil_temp")
            wind = asset_row.get("latest_winding_temp")
            pf = asset_row.get("latest_pf")

            kpis_list = [
                {"KPI": "Throughput Energy", "Value": kwh if pd.notna(kwh) else 0.0, "Unit": "kWh", "Status": status},
                {"KPI": "Oil Temperature", "Value": oil if pd.notna(oil) else 0.0, "Unit": "°C", "Status": status},
                {"KPI": "Winding Temperature", "Value": wind if pd.notna(wind) else 0.0, "Unit": "°C", "Status": status},
                {"KPI": "Power Factor", "Value": pf if pd.notna(pf) else 0.98, "Unit": "PF", "Status": status},
            ]
            latest_params = [
                {"Parameter": "Cumulative Throughput", "Value": kwh, "Unit": "kWh", "Timestamp": ts},
                {"Parameter": "Oil Temp (OTI)", "Value": oil, "Unit": "°C", "Timestamp": ts},
                {"Parameter": "Winding Temp (WTI)", "Value": wind, "Unit": "°C", "Timestamp": ts},
                {"Parameter": "Power Factor", "Value": pf, "Unit": "PF", "Timestamp": ts},
            ]
        else:  # ups
            v_out = asset_row.get("latest_output_voltage")
            i_out = asset_row.get("latest_output_current")
            v_dc = asset_row.get("latest_battery_vdc")
            t_bat = asset_row.get("latest_battery_temp")

            kpis_list = [
                {"KPI": "Output Voltage", "Value": v_out if pd.notna(v_out) else 230.0, "Unit": "V", "Status": status},
                {"KPI": "Output Current", "Value": i_out if pd.notna(i_out) else 0.0, "Unit": "A", "Status": status},
                {"KPI": "Battery DC Bus", "Value": v_dc if pd.notna(v_dc) else 380.0, "Unit": "V", "Status": status},
                {"KPI": "Battery Temp", "Value": t_bat if pd.notna(t_bat) else 25.0, "Unit": "°C", "Status": status},
            ]
            latest_params = [
                {"Parameter": "Output Voltage", "Value": v_out, "Unit": "V", "Timestamp": ts},
                {"Parameter": "Output Current", "Value": i_out, "Unit": "A", "Timestamp": ts},
                {"Parameter": "Battery DC Voltage", "Value": v_dc, "Unit": "V", "Timestamp": ts},
                {"Parameter": "Battery Temperature", "Value": t_bat, "Unit": "°C", "Timestamp": ts},
            ]

        # Fetch historical trend from database table
        trend_df = pd.DataFrame(columns=["Timestamp", "Parameter", "Value"])
        try:
            conn = get_sqlite_connection()
            query = f"""
            SELECT reading_datetime, cumulative_kwh
            FROM energy_readings_{stype}
            WHERE asset_code = ? OR asset_id = ?
            ORDER BY reading_datetime ASC
            LIMIT 50
            """
            rows = pd.read_sql_query(query, conn, params=(asset_id, asset_id))
            conn.close()
            if not rows.empty and "cumulative_kwh" in rows.columns:
                trend_records = []
                for _, r in rows.iterrows():
                    trend_records.append({
                        "Timestamp": r["reading_datetime"],
                        "Parameter": "Energy (kWh)",
                        "Value": float(r["cumulative_kwh"] or 0.0),
                    })
                trend_df = pd.DataFrame(trend_records)
        except Exception:
            pass

        return EquipmentDashboardData(
            source_type=source_type,
            asset_id=asset_id,
            asset_name=asset_name,
            plaza=plaza,
            kpis=pd.DataFrame(kpis_list),
            latest=pd.DataFrame(latest_params),
            trend=trend_df,
            exceptions=pd.DataFrame(columns=["Severity", "Rule", "Date", "Status"]),
            parameters=pd.DataFrame(latest_params).rename(columns={"Value": "Latest Value", "Timestamp": "Source"}),
        )

    def trace_source(self, source_reading_id: str) -> pd.DataFrame:
        return pd.DataFrame(columns=["Level", "ID", "Reference", "Timestamp"])
