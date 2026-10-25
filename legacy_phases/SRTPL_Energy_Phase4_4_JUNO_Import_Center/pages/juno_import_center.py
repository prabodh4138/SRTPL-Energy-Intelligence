import streamlit as st
from import_center.service import JunoImportService

def render():
    st.title("JUNO Import Center")
    st.caption("Download from JUNO → upload the untouched CSV → automatic processing")

    st.info(
        "Do not edit, rename columns, delete headings, or manually reformat the JUNO CSV. "
        "Upload the original downloaded file."
    )

    uploaded = st.file_uploader(
        "Upload original JUNO CSV",
        type=["csv"],
        accept_multiple_files=False,
        help="The application preserves the original file and its headings."
    )

    if not uploaded:
        st.stop()

    data = uploaded.getvalue()
    service = JunoImportService()
    metadata, checks = service.precheck(uploaded.name, data)

    st.subheader("File Details")
    c1, c2, c3 = st.columns(3)
    c1.metric("File Size", f"{metadata.size_bytes:,} bytes")
    c2.metric("SHA-256", metadata.sha256[:16] + "…")
    c3.metric("Detected Type", metadata.report_type or "REVIEW")

    st.subheader("Pre-check")
    for check in checks:
        icon = "✅" if check.status == "PASS" else ("⛔" if check.status in {"FAIL","BLOCK"} else "⚠️")
        st.write(f"{icon} **{check.code}** — {check.message}")

    with st.expander("Preview original CSV"):
        st.code(data.decode("utf-8-sig", errors="replace")[:5000])

    if st.button("Start Import", type="primary", use_container_width=True):
        result = service.start_import(metadata, checks)
        if result.status == "READY_FOR_PIPELINE":
            st.success("Pre-check passed. Production import pipeline is ready to be connected.")
        elif result.status == "BLOCKED":
            st.error(result.message)
        else:
            st.warning(result.message)

        st.json({
            "status": result.status,
            "report_type": result.report_type,
            "file_hash": result.file_hash,
            "batch_id": result.batch_id
        })
