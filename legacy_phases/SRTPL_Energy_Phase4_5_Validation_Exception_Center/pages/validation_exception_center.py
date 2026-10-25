import streamlit as st
from exception_center.repository import ExceptionRepository
from exception_center.service import ExceptionService

def render():
    st.title("Validation & Exception Center")
    st.caption("Review, investigate, resolve and audit data-quality exceptions.")

    repo = ExceptionRepository()
    service = ExceptionService()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open", "—")
    c2.metric("Warning", "—")
    c3.metric("Error", "—")
    c4.metric("Critical", "—")

    st.subheader("Filters")
    f1, f2, f3, f4 = st.columns(4)
    source = f1.selectbox("Source", ["All", "SOLAR", "DG", "EB", "TRANSFORMER", "UPS"])
    severity = f2.selectbox("Severity", ["All", "INFO", "WARNING", "ERROR", "CRITICAL"])
    status = f3.selectbox(
        "Status",
        ["All", "OPEN", "ACKNOWLEDGED", "UNDER_REVIEW", "RESOLVED", "ACCEPTED_EXCEPTION"]
    )
    plaza = f4.selectbox("Plaza", ["All", "TP01", "TP02", "TP03"])

    df = repo.list_exceptions({
        "source": None if source == "All" else source,
        "severity": None if severity == "All" else severity,
        "status": None if status == "All" else status,
        "plaza": None if plaza == "All" else plaza,
    })

    if df.empty:
        st.info("No production exceptions match the selected filters.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Exception Action")
    exception_id = st.selectbox("Exception ID", df["Exception ID"].tolist())
    row = df[df["Exception ID"] == exception_id].iloc[0]
    st.write(f"**Rule:** {row['Rule']}  |  **Severity:** {row['Severity']}  |  **Status:** {row['Status']}")
    note = st.text_area("Resolution / acceptance note")

    b1, b2 = st.columns(2)
    if b1.button("Resolve", use_container_width=True):
        try:
            service.resolve(repo, exception_id, row["Status"], note, st.session_state.get("user", "current_user"))
            st.success("Exception resolved and audit record should be created.")
        except ValueError as exc:
            st.error(str(exc))

    if b2.button("Accept as Exception", use_container_width=True):
        try:
            service.accept_exception(repo, exception_id, row["Status"], note, st.session_state.get("user", "current_user"))
            st.warning("Exception accepted. It remains visible for audit.")
        except ValueError as exc:
            st.error(str(exc))
