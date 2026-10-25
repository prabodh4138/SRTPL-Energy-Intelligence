import streamlit as st
from master_data.catalog import MASTER_DOMAINS
from master_data.repository import MasterDataRepository

def render():
    st.title("Master Data & Configuration Center")
    st.caption("Governed configuration for plazas, assets, parameters, thresholds, tariffs and KPIs.")

    repo = MasterDataRepository()
    domain = st.selectbox(
        "Configuration Domain",
        list(MASTER_DOMAINS),
        format_func=lambda x: MASTER_DOMAINS[x]
    )

    if domain == "PLAZA":
        df = repo.plazas()
    elif domain == "ASSET":
        df = repo.assets()
    elif domain == "PARAMETER":
        df = repo.parameters()
    elif domain == "ASSET_PARAMETER":
        df = repo.asset_parameters()
    elif domain == "THRESHOLD":
        df = repo.thresholds()
    elif domain == "TARIFF":
        df = repo.tariffs()
    elif domain == "KPI":
        df = repo.kpis()
    elif domain == "SOURCE_MAPPING":
        df = repo.source_mappings()
    else:
        df = repo.report_schedules()

    if df.empty:
        st.info("No production configuration records are available.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.warning(
        "Production changes must use the Phase 4.8 Change Request workflow. "
        "Do not directly edit database master tables from the browser."
    )
