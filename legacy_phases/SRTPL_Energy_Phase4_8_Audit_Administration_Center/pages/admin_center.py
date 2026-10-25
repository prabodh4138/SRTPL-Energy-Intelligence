import streamlit as st
from admin.repository import AdminRepository
from admin.service import AdminService

def render():
    st.title("Administration Center")
    st.caption("Controlled administration, governance and audit.")

    repo = AdminRepository()
    service = AdminService()

    tabs = st.tabs([
        "Users & Roles",
        "Master Data Governance",
        "Change Requests",
        "Reprocessing",
        "Audit Log",
        "System Configuration",
    ])

    with tabs[0]:
        st.subheader("Users & Roles")
        df = repo.users()
        if df.empty:
            st.info("No production users are available in the administration read model.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader("Master Data Governance")
        st.info("Master-data changes must be requested, approved and audited. Direct browser updates are disabled by design.")

    with tabs[2]:
        st.subheader("Change Requests")
        df = repo.change_requests()
        if df.empty:
            st.info("No pending production change requests.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("Controlled Reprocessing")
        df = repo.reprocess_jobs()
        if df.empty:
            st.info("No production reprocessing jobs.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.subheader("Audit Log")
        df = repo.audit_log()
        if df.empty:
            st.info("No production audit records.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.subheader("System Configuration")
        st.warning("Configuration changes must be versioned and audited. Secrets must never be displayed here.")
