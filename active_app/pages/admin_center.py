import os
import streamlit as st
from admin.repository import AdminRepository
from admin.service import AdminService
from core.supabase_manager import (
    get_database_status,
    get_network_info,
    inject_master_and_sample_data,
    remove_all_database_data,
    test_database_connection,
)

def render():
    st.title("Administration Center")
    st.caption("Controlled administration, governance, Supabase integration, and multi-device deployment.")

    repo = AdminRepository()
    service = AdminService()

    tabs = st.tabs([
        "Database & Cloud Deployment",
        "Users & Roles",
        "Master Data Governance",
        "Change Requests",
        "Reprocessing",
        "Audit Log",
        "System Configuration",
    ])

    with tabs[0]:
        st.subheader("Database & Deployment Management")
        st.caption("Manage Supabase database injection, wipe operational data, and view mobile/laptop network links.")

        net_info = get_network_info()
        db_status = test_database_connection()

        # 1. Multi-Device Network Access
        st.markdown("#### 📱 Multi-Device & Mobile Access")
        col_net1, col_net2 = st.columns(2)
        with col_net1:
            st.container(border=True).markdown(
                f"""
                **💻 Local Host (This PC)**  
                `{net_info['local_url']}`  
                <small style="color:#94a3b8;">Use this URL directly on the computer running the server.</small>
                """,
                unsafe_allow_html=True,
            )
        with col_net2:
            st.container(border=True).markdown(
                f"""
                **📱 Mobile Phone & Remote Laptop (Wi-Fi / LAN)**  
                `{net_info['network_url']}`  
                <small style="color:#94a3b8;">Open this URL on any phone, tablet, or laptop on the same network.</small>
                """,
                unsafe_allow_html=True,
            )

        st.info(
            "💡 **Mobile Access Tip:** Connect your smartphone or second laptop to the same Wi-Fi network as this PC, "
            f"then open **[{net_info['network_url']}]({net_info['network_url']})** in Chrome or Safari."
        )

        st.divider()

        # 2. Supabase Database Status & Credentials
        st.markdown("#### 🗄️ Supabase Database Connection")
        if db_status["connected"]:
            st.success(f"🟢 **Connected to Supabase:** {db_status['message']}")
        else:
            st.warning(f"🟡 **Database Mode:** {db_status['message']}")

        with st.expander("⚙️ View / Configure Supabase Credentials"):
            curr_url = os.getenv("SUPABASE_URL", "")
            curr_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_KEY", "")
            new_url = st.text_input("Supabase Project URL", value=curr_url, placeholder="https://xyzcompany.supabase.co")
            new_key = st.text_input("Supabase Service Role / Anon Key", value=curr_key, type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5c...")
            if st.button("Save & Test Supabase Connection", key="btn_save_db_creds"):
                os.environ["SUPABASE_URL"] = new_url.strip()
                os.environ["SUPABASE_KEY"] = new_key.strip()
                # Also write to .env if present
                env_path = os.path.join(os.getcwd(), ".env")
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    new_lines = []
                    for line in lines:
                        if line.startswith("SUPABASE_URL="):
                            new_lines.append(f"SUPABASE_URL={new_url.strip()}\n")
                        elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                            new_lines.append(f"SUPABASE_SERVICE_ROLE_KEY={new_key.strip()}\n")
                        else:
                            new_lines.append(line)
                    with open(env_path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                except Exception:
                    pass
                test_res = test_database_connection()
                if test_res["connected"]:
                    st.success("Connected to Supabase successfully!")
                else:
                    st.error(test_res["message"])
                st.rerun()

        st.divider()

        # 3. Actions: Inject Data & Wipe Database
        st.markdown("#### ⚡ Database Operations")
        act_col1, act_col2 = st.columns(2)

        with act_col1:
            st.markdown("##### 📥 Inject Data into Database")
            st.caption("Seeds 3 Plazas, 21 Assets, raw JUNO meter readings, 13 verified Energy Bills, and 4 Payment Receipts.")
            if st.button("🚀 Inject Data into Database / Supabase", width="stretch", key="btn_inject_db"):
                progress_slot = st.empty()
                bar_slot = st.progress(0.0)

                def _ui_cb(msg, frac):
                    progress_slot.caption(f"Status: {msg}")
                    bar_slot.progress(frac)

                try:
                    res = inject_master_and_sample_data(_ui_cb)
                    st.session_state["demo_mode_active"] = True
                    st.success(
                        f"✅ **Data Injected Successfully!**\n\n"
                        f"- **Plazas:** {res['plazas']}\n"
                        f"- **Assets:** {res['assets']}\n"
                        f"- **Meter Reading Samples:** {res['meter_readings']}\n"
                        f"- **Energy Bills:** {res['bills']}\n"
                        f"- **Payment Receipts:** {res['receipts']}\n"
                        f"- **Storage Target:** {res['mode']}"
                    )
                except Exception as exc:
                    st.error(f"Injection encountered error: {exc}")

        with act_col2:
            st.markdown("##### 🗑️ Remove All Data (Clean Production Reset)")
            st.caption("Wipes all operational telemetry, energy bills, payment receipts, and exceptions for a pristine start.")
            confirm_wipe = st.checkbox("I confirm I want to wipe all operational data from the database", key="confirm_wipe_cb")
            if st.button("⚠️ Wipe Database / Remove All Data", width="stretch", type="primary", disabled=not confirm_wipe, key="btn_wipe_db"):
                try:
                    wipe_res = remove_all_database_data()
                    st.session_state["demo_mode_active"] = False
                    st.success(f"🧹 **{wipe_res['message']}**")
                    st.info(f"Cleared {len(wipe_res['cleared_tables'])} tables. System is now empty and ready for fresh live uploads.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Wipe encountered error: {exc}")

        st.divider()

        # 4. Cloud Deployment Guide
        st.markdown("#### ☁️ Cloud Deployment (Global Public Access)")
        st.markdown(
            """
            To access this application on any mobile phone or computer globally without needing the same local Wi-Fi, 
            deploy it to **Streamlit Community Cloud** (100% Free):

            1. **Push your code to GitHub repository**:
               `git add . && git commit -m "SRTPL Energy Intelligence" && git push`
            2. **Go to [share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
            3. Click **"New App"** and select:
               - **Repository**: Your GitHub repository name
               - **Branch**: `main`
               - **Main file path**: `streamlit_app.py`
            4. **Advanced Settings (Secrets)**:
               Paste your Supabase credentials into the Secrets box:
               ```toml
               SUPABASE_URL = "https://your-project.supabase.co"
               SUPABASE_KEY = "your-service-role-or-anon-key"
               ```
            5. Click **"Deploy"**! You will receive a permanent public HTTPS URL (e.g. `https://srtpl-energy.streamlit.app`) accessible from any smartphone, tablet, or PC worldwide.
            """
        )

        with st.expander("📄 Download Master SQL Scripts for Supabase SQL Editor"):
            sql_clean_path = os.path.join(os.getcwd(), "sql", "supabase_clean_wipe_and_fresh_start.sql")
            sql_master_path = os.path.join(os.getcwd(), "sql", "supabase_master_setup.sql")
            sql_reset_path = os.path.join(os.getcwd(), "sql", "reset_database.sql")

            if os.path.exists(sql_clean_path):
                with open(sql_clean_path, "r", encoding="utf-8") as f:
                    clean_sql_txt = f.read()
                st.download_button(
                    "🔥 Download Total Wipe SQL (`supabase_clean_wipe_and_fresh_start.sql`)",
                    data=clean_sql_txt,
                    file_name="supabase_clean_wipe_and_fresh_start.sql",
                    mime="text/plain",
                    width="stretch",
                )

            if os.path.exists(sql_master_path):
                with open(sql_master_path, "r", encoding="utf-8") as f:
                    master_sql_txt = f.read()
                st.download_button(
                    "📥 Download Master Schema SQL (`supabase_master_setup.sql`)",
                    data=master_sql_txt,
                    file_name="supabase_master_setup.sql",
                    mime="text/plain",
                    width="stretch",
                )

            if os.path.exists(sql_reset_path):
                with open(sql_reset_path, "r", encoding="utf-8") as f:
                    reset_sql_txt = f.read()
                st.download_button(
                    "📥 Download Database Data Wipe SQL (`reset_database.sql`)",
                    data=reset_sql_txt,
                    file_name="reset_database.sql",
                    mime="text/plain",
                    width="stretch",
                )

    with tabs[1]:
        st.subheader("Users & Roles")
        df = repo.users()
        if df.empty:
            st.info("No production users are available in the administration read model.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)

    with tabs[2]:
        st.subheader("Master Data Governance")
        st.info("Master-data changes must be requested, approved and audited. Direct browser updates are disabled by design.")

    with tabs[3]:
        st.subheader("Change Requests")
        df = repo.change_requests()
        if df.empty:
            st.info("No pending production change requests.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)

    with tabs[4]:
        st.subheader("Controlled Reprocessing")
        df = repo.reprocess_jobs()
        if df.empty:
            st.info("No production reprocessing jobs.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)

    with tabs[5]:
        st.subheader("Audit Log")
        df = repo.audit_log()
        if df.empty:
            st.info("No production audit records.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)

    with tabs[6]:
        st.subheader("System Configuration")
        st.warning("Configuration changes must be versioned and audited. Secrets must never be displayed here.")
