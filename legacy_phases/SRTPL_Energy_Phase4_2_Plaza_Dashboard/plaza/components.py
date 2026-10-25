import streamlit as st
import pandas as pd

def money(v):
    return "—" if v is None else f"₹{v:,.2f}"

def num(v, unit=""):
    return "—" if v is None else f"{v:,.2f}{unit}"

def render_kpis(d):
    st.subheader(f"{d.plaza_name} — Key Performance Indicators")
    cols = st.columns(6)
    cols[0].metric("EB Consumption", num(d.eb_kwh, " kWh"))
    cols[1].metric("DG Generation", num(d.dg_kwh, " kWh"))
    cols[2].metric("Solar Generation", num(d.solar_kwh, " kWh"))
    cols[3].metric("DG Runtime", num(d.dg_runtime, " hr"))
    cols[4].metric("Energy Cost", money(d.eb_cost if d.eb_cost is not None else d.dg_cost))
    cols[5].metric("Solar Saving", money(d.solar_saving))

    cols2 = st.columns(3)
    cols2[0].metric("DG kWh/hr", num(d.dg_efficiency))
    cols2[1].metric("EB PF", num(d.eb_pf))
    cols2[2].metric("DG PF", num(d.dg_pf))

def render_energy_mix(d):
    st.subheader("Energy Mix")
    vals = {k: v for k, v in {
        "EB": d.eb_kwh, "DG": d.dg_kwh, "Solar": d.solar_kwh
    }.items() if v is not None}
    if not vals:
        st.info("No energy KPI data available.")
        return
    st.bar_chart(pd.DataFrame({"kWh": vals}).T)

def render_quality(d):
    st.subheader("Data Quality")
    value = "—" if d.data_quality is None else f"{d.data_quality:.1f}%"
    st.metric("Quality", value)
    if d.exception_count:
        st.warning(f"{d.exception_count} open exception(s).")
    else:
        st.success("No open exceptions.")

def render_asset_status(d):
    st.subheader("Asset Status")
    if d.asset_rows is None or d.asset_rows.empty:
        st.info("No asset status data available.")
        return
    st.dataframe(d.asset_rows, use_container_width=True, hide_index=True)

def render_trends(d):
    st.subheader("Energy Trend")
    if d.trend_rows is None or d.trend_rows.empty:
        st.info("No trend data available.")
        return
    df = d.trend_rows.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    st.line_chart(df.set_index("Date")[["EB kWh", "DG kWh", "Solar kWh"]])

def render_asset_table(d):
    st.subheader("Equipment Performance")
    if d.asset_rows is None or d.asset_rows.empty:
        st.info("Equipment KPI data will appear after production integration.")
        return
    st.dataframe(d.asset_rows, use_container_width=True, hide_index=True)

def render_exceptions(d):
    st.subheader("Plaza Exceptions")
    if d.exceptions is None or d.exceptions.empty:
        st.success("No exception records for this period.")
        return
    st.dataframe(d.exceptions, use_container_width=True, hide_index=True)
