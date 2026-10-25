import streamlit as st
import pandas as pd

def _money(value):
    return "—" if value is None else f"₹{value:,.2f}"

def _number(value, unit=""):
    return "—" if value is None else f"{value:,.2f}{unit}"

def metric_row(summary):
    cols = st.columns(5)
    cols[0].metric("EB Consumption", _number(summary.total_eb_kwh, " kWh"))
    cols[1].metric("DG Generation", _number(summary.total_dg_kwh, " kWh"))
    cols[2].metric("Solar Generation", _number(summary.total_solar_kwh, " kWh"))
    cols[3].metric("Energy Cost", _money(summary.eb_cost if summary.eb_cost is not None else summary.dg_cost))
    cols[4].metric("Solar Saving", _money(summary.solar_saving))

def energy_mix(summary):
    st.subheader("Energy Mix")
    vals = {
        "EB": summary.total_eb_kwh,
        "DG": summary.total_dg_kwh,
        "Solar": summary.total_solar_kwh,
    }
    clean = {k: v for k, v in vals.items() if v is not None}
    if not clean:
        st.info("No KPI data available for the selected period.")
        return
    st.bar_chart(pd.DataFrame([clean]).T.rename(columns={0: "kWh"}))

def trend_chart(summary):
    df = summary.trend_rows
    if df is None or df.empty:
        st.info("No trend data available for the selected period.")
        return
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    st.line_chart(df.set_index("Date")[["EB kWh", "DG kWh", "Solar kWh"]])

def plaza_table(summary):
    if summary.plaza_rows is None or summary.plaza_rows.empty:
        st.info("No plaza KPI data available.")
        return
    st.dataframe(summary.plaza_rows, use_container_width=True, hide_index=True)

def exception_panel(summary):
    if summary.exception_count == 0:
        st.success("No open exceptions for the selected scope.")
    else:
        st.warning(f"{summary.exception_count} exception(s) require attention.")

def data_quality_panel(summary):
    value = "—" if summary.data_quality_percent is None else f"{summary.data_quality_percent:.1f}%"
    st.metric("Data Quality", value)
    if summary.data_quality_percent is None:
        st.info("Data-quality KPIs will appear after production database integration.")
