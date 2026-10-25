import streamlit as st
import pandas as pd

def display_value(v, unit=""):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:,.2f}{(' ' + unit) if unit else ''}"

def render_kpis(df):
    st.subheader("KPI Summary")
    if df is None or df.empty:
        st.info("No KPI results available for this asset.")
        return
    cols = st.columns(min(5, len(df)))
    for col, row in zip(cols, df.head(5).itertuples(index=False)):
        col.metric(str(row[0]), display_value(row[1], str(row[2])))

def render_latest(df):
    st.subheader("Latest Parameters")
    if df is None or df.empty:
        st.info("No latest reading available.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_parameters(df):
    st.subheader("Parameter Catalogue")
    if df is None or df.empty:
        st.info("No parameter mapping available.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_trend(df):
    st.subheader("Parameter Trend")
    if df is None or df.empty:
        st.info("No trend data available.")
        return
    work = df.copy()
    work["Timestamp"] = pd.to_datetime(work["Timestamp"])
    pivot = work.pivot_table(
        index="Timestamp", columns="Parameter", values="Value", aggfunc="last"
    )
    st.line_chart(pivot)

def render_exceptions(df):
    st.subheader("Equipment Exceptions")
    if df is None or df.empty:
        st.success("No exceptions for this equipment in the selected period.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_traceability(trace_df):
    st.subheader("Source Traceability")
    if trace_df is None or trace_df.empty:
        st.info("Select a production reading/KPI to view its JUNO source chain.")
        return
    st.dataframe(trace_df, use_container_width=True, hide_index=True)
