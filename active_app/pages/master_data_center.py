import streamlit as st
from master_data.catalog import MASTER_DOMAINS
from master_data.repository import MasterDataRepository
from core.db_sync import (
    get_all_plazas,
    save_plaza,
    delete_plaza,
    get_all_assets,
    save_asset,
    delete_asset,
    get_all_consumer_accounts,
    save_consumer_account,
    delete_consumer_account,
)
from core.supabase_manager import test_database_connection


def render():
    st.title("Master Data & Configuration Center")
    st.caption("Live configuration and master registry for Plazas, Assets, and Energy Parameters with simultaneous Supabase database synchronization.")

    conn_status = test_database_connection()
    if conn_status["connected"]:
        st.success("🟢 **Live Database Sync Active:** Any additions, modifications, or deletions will immediately update Supabase in real-time.")
    else:
        st.info("🟡 **Local Mode Active:** Changes are saved in your operational session store. When connected to Supabase, they sync directly.")

    repo = MasterDataRepository()

    m_tab_view, m_tab_add, m_tab_edit, m_tab_delete = st.tabs([
        "📋 Browse Master Records",
        "➕ Add New Record",
        "✏️ Modify Record",
        "🗑️ Delete Record",
    ])

    # -----------------------------------------------------------------------
    # TAB 1: Browse Records
    # -----------------------------------------------------------------------
    with m_tab_view:
        domain = st.selectbox(
            "Configuration Domain",
            list(MASTER_DOMAINS),
            format_func=lambda x: MASTER_DOMAINS[x],
            key="md_browse_domain",
        )

        if domain == "CONSUMER_ACCOUNT":
            df = repo.consumer_accounts()
        elif domain == "PLAZA":
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
            st.info("No records are currently present in this domain.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)

    # -----------------------------------------------------------------------
    # TAB 2: Add New Record (Consumer Account, Plaza, Asset)
    # -----------------------------------------------------------------------
    with m_tab_add:
        st.subheader("Add Master Record")
        add_type = st.radio("Select Entity to Add", ["Consumer Account", "Plaza", "Asset"], horizontal=True, key="add_entity_type")

        if add_type == "Consumer Account":
            plazas_df = get_all_plazas()
            plaza_ids = plazas_df["plaza_id"].tolist() if not plazas_df.empty else ["TP01", "TP02", "TP03"]
            with st.form("form_add_consumer_account"):
                st.markdown("##### ⚡ Register Energy Consumer Account & Mapping")
                c1, c2, c3 = st.columns(3)
                ca_no = c1.text_input("Consumer Account No.*", placeholder="411001070208")
                ca_plz = c2.selectbox("Toll Plaza ID*", plaza_ids)
                ca_type = c3.selectbox("Bill Type*", ["HT", "LT"])

                c4, c5, c6 = st.columns(3)
                ca_asset = c4.text_input("Asset Code*", placeholder="SR-E-EM-EB-5-200")
                ca_scope = c5.selectbox("Consumer Scope*", ["HIGHWAY", "TOLL_PLAZA", "ADMIN"])
                ca_div = c6.text_input("Division Name*", placeholder="SED")

                c7, c8, c9 = st.columns(3)
                ca_usage = c7.text_input("Usage Type*", value="Street Light")
                ca_load = c8.number_input("Sanctioned Load (kW)*", min_value=0.0, value=10.0, step=1.0)
                ca_loc = c9.text_input("Location*", placeholder="Ainthapalli")

                ca_rem = st.text_input("Remarks", placeholder="Master mapping record")
                ca_act = st.checkbox("Active Status", value=True)

                if st.form_submit_button("💾 Save Consumer Account to Database", type="primary"):
                    if not ca_no or not ca_asset or not ca_loc:
                        st.error("Consumer Account No, Asset Code, and Location are required.")
                    else:
                        res = save_consumer_account({
                            "consumer_account_no": ca_no,
                            "toll_plaza_id": ca_plz,
                            "bill_type": ca_type,
                            "asset_code": ca_asset,
                            "consumer_scope": ca_scope,
                            "division_name": ca_div,
                            "usage_type": ca_usage,
                            "sanctioned_load_kw": ca_load,
                            "location": ca_loc,
                            "is_active": ca_act,
                            "remarks": ca_rem,
                        })
                        sync_msg = "and synchronized to Supabase" if res.get("cloud_synced") else "in local operational store"
                        st.success(f"✅ Consumer Account **{ca_no}** saved successfully {sync_msg}!")
                        st.rerun()

        elif add_type == "Plaza":
            with st.form("form_add_plaza"):
                st.markdown("##### 🏢 Register New Toll Plaza")
                p_id = st.text_input("Plaza ID (e.g. TP04)", placeholder="TP04")
                p_name = st.text_input("Plaza Name", placeholder="Toll Plaza 04 - Sambalpur Bypass")
                p_loc = st.text_input("Corridor Location", placeholder="SRTPL Corridor Km 145+200")
                p_active = st.checkbox("Active Status", value=True)
                btn_add_p = st.form_submit_button("💾 Save Plaza to Database", type="primary")

                if btn_add_p:
                    if not p_id or not p_name:
                        st.error("Plaza ID and Plaza Name are required.")
                    else:
                        res = save_plaza(p_id, p_name, p_loc, p_active)
                        sync_msg = "and synchronized to Supabase" if res["cloud_synced"] else "in local operational store"
                        st.success(f"✅ Plaza **{p_id.upper()}** saved successfully {sync_msg}!")
                        st.rerun()

        elif add_type == "Asset":
            plazas_df = get_all_plazas()
            plaza_ids = plazas_df["plaza_id"].tolist() if not plazas_df.empty else ["TP01", "TP02", "TP03"]

            with st.form("form_add_asset"):
                st.markdown("##### ⚡ Register New Equipment Asset")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    a_id = st.text_input("Asset ID", placeholder="AST-DG-07")
                    a_code = st.text_input("Asset Code (JUNO Reference)", placeholder="SR-E-AP-DGX-000007")
                    a_name = st.text_input("Asset Name", placeholder="Diesel Generator 7 (Standby)")
                with col_a2:
                    a_plz = st.selectbox("Assign to Plaza", plaza_ids)
                    a_type = st.selectbox("Source Type", ["EB", "DG", "SOLAR", "TRANSFORMER", "UPS"])
                    a_cap = st.number_input("Capacity (kVA / kW)", min_value=0.0, value=250.0, step=10.0)
                a_active = st.checkbox("Active Status", value=True, key="add_asset_active")
                btn_add_a = st.form_submit_button("💾 Save Asset to Database", type="primary")

                if btn_add_a:
                    if not a_id or not a_code or not a_name:
                        st.error("Asset ID, Asset Code, and Asset Name are required.")
                    else:
                        res = save_asset(a_id, a_code, a_name, a_plz, a_type, a_cap, a_active)
                        sync_msg = "and synchronized to Supabase" if res["cloud_synced"] else "in local operational store"
                        st.success(f"✅ Asset **{a_id}** saved successfully {sync_msg}!")
                        st.rerun()

    # -----------------------------------------------------------------------
    # TAB 3: Modify Record
    # -----------------------------------------------------------------------
    with m_tab_edit:
        st.subheader("Modify Existing Record")
        edit_type = st.radio("Select Entity to Edit", ["Consumer Account", "Plaza", "Asset"], horizontal=True, key="edit_entity_type")

        if edit_type == "Consumer Account":
            ca_df = get_all_consumer_accounts()
            plazas_df = get_all_plazas()
            plaza_ids = plazas_df["plaza_id"].tolist() if not plazas_df.empty else ["TP01", "TP02", "TP03"]
            if ca_df.empty:
                st.warning("No consumer accounts found in database.")
            else:
                ac_list = ca_df["consumer_account_no"].astype(str).tolist()
                sel_ac = st.selectbox("Select Consumer Account to Modify", ac_list, key="sel_edit_ca")
                curr_ca = ca_df[ca_df["consumer_account_no"].astype(str) == sel_ac].iloc[0]

                with st.form("form_edit_ca"):
                    ec1, ec2, ec3 = st.columns(3)
                    curr_p = str(curr_ca.get("toll_plaza_id", plaza_ids[0]))
                    p_idx = plaza_ids.index(curr_p) if curr_p in plaza_ids else 0
                    e_plz = ec1.selectbox("Toll Plaza ID", plaza_ids, index=p_idx)
                    curr_bt = str(curr_ca.get("bill_type", "HT")).upper()
                    bt_idx = 0 if curr_bt == "HT" else 1
                    e_bt = ec2.selectbox("Bill Type", ["HT", "LT"], index=bt_idx)
                    e_asset = ec3.text_input("Asset Code", value=str(curr_ca.get("asset_code", "")))

                    ec4, ec5, ec6 = st.columns(3)
                    curr_sc = str(curr_ca.get("consumer_scope", "HIGHWAY")).upper()
                    sc_list = ["HIGHWAY", "TOLL_PLAZA", "ADMIN"]
                    sc_idx = sc_list.index(curr_sc) if curr_sc in sc_list else 0
                    e_scope = ec4.selectbox("Consumer Scope", sc_list, index=sc_idx)
                    e_div = ec5.text_input("Division Name", value=str(curr_ca.get("division_name", "")))
                    e_usage = ec6.text_input("Usage Type", value=str(curr_ca.get("usage_type", "Street Light")))

                    ec7, ec8, ec9 = st.columns(3)
                    e_load = ec7.number_input("Sanctioned Load (kW)", value=float(curr_ca.get("sanctioned_load_kw", 10.0) or 0.0), step=1.0)
                    e_loc = ec8.text_input("Location", value=str(curr_ca.get("location", "")))
                    e_act = ec9.checkbox("Active", value=bool(curr_ca.get("is_active", True)), key="edit_ca_active")

                    e_rem = st.text_input("Remarks", value=str(curr_ca.get("remarks", "")))

                    if st.form_submit_button("🔄 Update Consumer Account in Database", type="primary"):
                        res = save_consumer_account({
                            "consumer_account_no": sel_ac,
                            "toll_plaza_id": e_plz,
                            "bill_type": e_bt,
                            "asset_code": e_asset,
                            "consumer_scope": e_scope,
                            "division_name": e_div,
                            "usage_type": e_usage,
                            "sanctioned_load_kw": e_load,
                            "location": e_loc,
                            "is_active": e_act,
                            "remarks": e_rem,
                        })
                        sync_msg = "and synchronized to Supabase" if res.get("cloud_synced") else "in local operational store"
                        st.success(f"✅ Consumer Account **{sel_ac}** updated successfully {sync_msg}!")
                        st.rerun()

        elif edit_type == "Plaza":
            plazas_df = get_all_plazas()
            if plazas_df.empty:
                st.warning("No plazas found in database.")
            else:
                p_opts = plazas_df["plaza_id"].tolist()
                sel_p = st.selectbox("Select Plaza to Modify", p_opts, key="sel_edit_plaza")
                current = plazas_df[plazas_df["plaza_id"] == sel_p].iloc[0]

                with st.form("form_edit_plaza"):
                    edit_p_name = st.text_input("Plaza Name", value=str(current.get("plaza_name", "")))
                    edit_p_loc = st.text_input("Location", value=str(current.get("location", "")))
                    edit_p_act = st.checkbox("Active", value=bool(current.get("is_active", True)))
                    btn_upd_p = st.form_submit_button("🔄 Update Plaza in Database", type="primary")

                    if btn_upd_p:
                        res = save_plaza(sel_p, edit_p_name, edit_p_loc, edit_p_act)
                        sync_msg = "and synchronized to Supabase" if res["cloud_synced"] else "in local operational store"
                        st.success(f"✅ Plaza **{sel_p}** updated successfully {sync_msg}!")
                        st.rerun()

        elif edit_type == "Asset":
            assets_df = get_all_assets()
            plazas_df = get_all_plazas()
            plaza_ids = plazas_df["plaza_id"].tolist() if not plazas_df.empty else ["TP01", "TP02", "TP03"]

            if assets_df.empty:
                st.warning("No assets found in database.")
            else:
                a_opts = assets_df["asset_id"].tolist()
                sel_a = st.selectbox("Select Asset to Modify", a_opts, key="sel_edit_asset")
                current_a = assets_df[assets_df["asset_id"] == sel_a].iloc[0]

                with st.form("form_edit_asset"):
                    col_ea1, col_ea2 = st.columns(2)
                    with col_ea1:
                        edit_a_code = st.text_input("Asset Code", value=str(current_a.get("asset_code", "")))
                        edit_a_name = st.text_input("Asset Name", value=str(current_a.get("asset_name", "")))
                        curr_plz = str(current_a.get("plaza_id", plaza_ids[0]))
                        plz_idx = plaza_ids.index(curr_plz) if curr_plz in plaza_ids else 0
                        edit_a_plz = st.selectbox("Plaza", plaza_ids, index=plz_idx)
                    with col_ea2:
                        curr_type = str(current_a.get("source_type", "EB")).upper()
                        types_list = ["EB", "DG", "SOLAR", "TRANSFORMER", "UPS"]
                        type_idx = types_list.index(curr_type) if curr_type in types_list else 0
                        edit_a_type = st.selectbox("Source Type", types_list, index=type_idx)
                        edit_a_cap = st.number_input("Capacity (kVA)", value=float(current_a.get("capacity_kva", 0.0) or 0.0))
                        edit_a_act = st.checkbox("Active", value=bool(current_a.get("is_active", True)), key="edit_asset_active")

                    btn_upd_a = st.form_submit_button("🔄 Update Asset in Database", type="primary")
                    if btn_upd_a:
                        res = save_asset(sel_a, edit_a_code, edit_a_name, edit_a_plz, edit_a_type, edit_a_cap, edit_a_act)
                        sync_msg = "and synchronized to Supabase" if res["cloud_synced"] else "in local operational store"
                        st.success(f"✅ Asset **{sel_a}** updated successfully {sync_msg}!")
                        st.rerun()

    # -----------------------------------------------------------------------
    # TAB 4: Delete Record
    # -----------------------------------------------------------------------
    with m_tab_delete:
        st.subheader("Delete Master Record")
        del_type = st.radio("Select Entity to Delete", ["Consumer Account", "Plaza", "Asset"], horizontal=True, key="del_entity_type")

        if del_type == "Consumer Account":
            ca_df = get_all_consumer_accounts()
            if ca_df.empty:
                st.warning("No consumer accounts found to delete.")
            else:
                sel_del_ca = st.selectbox("Select Consumer Account to Remove", ca_df["consumer_account_no"].astype(str).tolist(), key="sel_del_ca")
                st.warning(f"⚠️ Deleting Consumer Account **{sel_del_ca}** will remove it from both the application and the Supabase database.")
                confirm_del_ca = st.checkbox(f"Confirm deletion of consumer account {sel_del_ca}", key="confirm_del_ca")
                if st.button("🗑️ Delete Consumer Account from Database", type="primary", disabled=not confirm_del_ca, key="btn_exec_del_ca"):
                    res = delete_consumer_account(sel_del_ca)
                    sync_msg = "and removed from Supabase" if res.get("cloud_synced") else "from local store"
                    st.success(f"🧹 Consumer Account **{sel_del_ca}** deleted successfully {sync_msg}!")
                    st.rerun()

        elif del_type == "Plaza":
            plazas_df = get_all_plazas()
            if plazas_df.empty:
                st.warning("No plazas found to delete.")
            else:
                sel_del_p = st.selectbox("Select Plaza to Remove", plazas_df["plaza_id"].tolist(), key="sel_del_plaza")
                st.warning(f"⚠️ Deleting **{sel_del_p}** will remove it from both the application and the Supabase database.")
                confirm_del_p = st.checkbox(f"Confirm deletion of plaza {sel_del_p}", key="confirm_del_p")
                if st.button("🗑️ Delete Plaza from Database", type="primary", disabled=not confirm_del_p, key="btn_exec_del_p"):
                    res = delete_plaza(sel_del_p)
                    sync_msg = "and removed from Supabase" if res["cloud_synced"] else "from local store"
                    st.success(f"🧹 Plaza **{sel_del_p}** deleted successfully {sync_msg}!")
                    st.rerun()

        elif del_type == "Asset":
            assets_df = get_all_assets()
            if assets_df.empty:
                st.warning("No assets found to delete.")
            else:
                sel_del_a = st.selectbox("Select Asset to Remove", assets_df["asset_id"].tolist(), key="sel_del_asset")
                st.warning(f"⚠️ Deleting **{sel_del_a}** will remove it from both the application and the Supabase database.")
                confirm_del_a = st.checkbox(f"Confirm deletion of asset {sel_del_a}", key="confirm_del_a")
                if st.button("🗑️ Delete Asset from Database", type="primary", disabled=not confirm_del_a, key="btn_exec_del_a"):
                    res = delete_asset(sel_del_a)
                    sync_msg = "and removed from Supabase" if res["cloud_synced"] else "from local store"
                    st.success(f"🧹 Asset **{sel_del_a}** deleted successfully {sync_msg}!")
                    st.rerun()
