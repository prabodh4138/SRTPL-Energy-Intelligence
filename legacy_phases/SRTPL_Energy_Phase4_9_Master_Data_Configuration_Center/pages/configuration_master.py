import streamlit as st
from master_data.repository import MasterDataRepository

def render():
    st.title("Configuration Masters")
    repo = MasterDataRepository()
    tabs = st.tabs(["Parameters", "Asset Mapping", "Thresholds", "Tariffs", "KPIs", "JUNO Mapping", "Report Schedules"])
    datasets = [
        repo.parameters(), repo.asset_parameters(), repo.thresholds(),
        repo.tariffs(), repo.kpis(), repo.source_mappings(),
        repo.report_schedules()
    ]
    for tab, df in zip(tabs, datasets):
        with tab:
            if df.empty:
                st.info("No production configuration records.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
