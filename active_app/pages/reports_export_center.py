import streamlit as st
from datetime import date, timedelta
from reports.catalog import REPORT_CATALOG
from reports.repository import ReportRepository
from reports.models import ReportFilter, ReportRequest
from reports.exporters import export_csv, export_xlsx, export_pdf

def render():
    st.title("Reports & Export Center")
    st.caption("Generate traceable management, operational and audit reports.")

    report_code = st.selectbox(
        "Report",
        list(REPORT_CATALOG),
        format_func=lambda x: REPORT_CATALOG[x]["name"]
    )

    c1, c2 = st.columns(2)
    date_from = c1.date_input("From", date.today() - timedelta(days=30))
    date_to = c2.date_input("To", date.today())

    c3, c4, c5 = st.columns(3)
    plaza = c3.selectbox("Plaza", ["All", "TP01", "TP02", "TP03"])
    source = c4.selectbox("Source", ["All", "SOLAR", "DG", "EB", "TRANSFORMER", "UPS"])
    fmt = c5.selectbox("Format", REPORT_CATALOG[report_code]["formats"])

    if st.button("Generate Report", type="primary", width="stretch"):
        filters = ReportFilter(
            date_from=str(date_from),
            date_to=str(date_to),
            plaza_id=None if plaza == "All" else plaza,
            source_type=None if source == "All" else source,
        )
        request = ReportRequest(
            report_code=report_code,
            filters=filters,
            output_format=fmt,
            requested_by=st.session_state.get("user", "current_user"),
        )

        df = ReportRepository().fetch(report_code, filters)
        if df.empty:
            st.warning("No production data is available for the selected filters. No report file was generated.")
            return

        rows = df.to_dict("records")
        columns = list(df.columns)

        if fmt == "csv":
            content = export_csv(rows, columns)
            mime = "text/csv"
            extension = "csv"
        elif fmt == "xlsx":
            content = export_xlsx(rows, columns)
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        else:
            content = export_pdf(REPORT_CATALOG[report_code]["name"], rows, columns)
            mime = "application/pdf"
            extension = "pdf"

        file_name = f"{report_code}_{date_from}_{date_to}.{extension}"
        st.download_button(
            "Download Report",
            content,
            file_name=file_name,
            mime=mime,
            width="stretch",
        )
        st.success(f"Report generated: {file_name}")
