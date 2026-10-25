import streamlit as st
from .repository import DQRepository
from .calculations import calculate_metrics

def _metric(label, value, suffix=""):
    if value is None:
        st.metric(label, "No data")
    elif isinstance(value, float):
        st.metric(label, f"{value:.2f}{suffix}")
    else:
        st.metric(label, f"{value:,}{suffix}")

def render():
    st.title("Data Quality & Import Monitoring")
    st.caption("Monitor the quality and readiness of data feeding energy analytics.")

    repo = DQRepository()

    c1, c2, c3 = st.columns(3)
    start = c1.date_input("From")
    end = c2.date_input("To")
    plaza = c3.selectbox("Plaza", ["All", "TP01", "TP02", "TP03"])

    summary = repo.summary(start, end, None if plaza == "All" else plaza)

    st.subheader("Data Quality KPIs")
    if not summary:
        st.info("No production data is available for the selected period.")
    else:
        m = calculate_metrics(
            summary.get("records_received", 0),
            summary.get("records_valid", 0),
            summary.get("records_invalid", 0),
            summary.get("records_duplicate", 0),
            summary.get("expected_records"),
            summary.get("exceptions", 0),
            summary.get("corrections", 0),
            summary.get("traceable", 0),
        )
        cols = st.columns(5)
        with cols[0]: _metric("Records Received", m["records_received"])
        with cols[1]: _metric("Completeness", m["completeness_pct"], "%")
        with cols[2]: _metric("Validation Pass", m["validation_pass_pct"], "%")
        with cols[3]: _metric("Duplicate Rate", m["duplicate_rate_pct"], "%")
        with cols[4]: _metric("Audit Traceability", m["audit_traceability_pct"], "%")

    st.subheader("Source Health")
    source_df = repo.source_health(start, end, None if plaza == "All" else plaza)
    if source_df.empty:
        st.info("No source-health records available.")
    else:
        st.dataframe(source_df, use_container_width=True, hide_index=True)

    st.subheader("Import Health Trend")
    import_df = repo.import_health(start, end)
    if import_df.empty:
        st.info("No import history available.")
    else:
        st.line_chart(import_df.set_index("Date")[["Received", "Imported", "Invalid", "Duplicate"]])

    st.subheader("Exception Ageing")
    age_df = repo.exception_ageing()
    if age_df.empty:
        st.info("No exception-ageing data available.")
    else:
        st.dataframe(age_df, use_container_width=True, hide_index=True)
