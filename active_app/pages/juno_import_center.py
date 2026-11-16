from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import pandas as pd

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st

from import_center.service import JunoImportService
from import_center.simulation import list_sample_files
from import_engine.service import ImportService
from core.live_pipeline import (
    execute_live_juno_ingestion,
    clear_local_ingestion_hashes,
)
from core.supabase_manager import remove_all_database_data


def _save_temp(data: bytes, filename: str) -> Path:
    ext = Path(filename).suffix or ".csv"
    fd, name = tempfile.mkstemp(prefix="srtpl_unified_", suffix=ext)
    p = Path(name)
    p.write_bytes(data)
    return p


def _render_single_center_results(res: dict, rtype: str, temp_path: Path | None = None, is_temp: bool = False):
    """Renders results view for a single file in JUNO Import Center."""
    if res.get("status") == "DUPLICATE_FILE":
        st.error(res["message"])
        col_clear, col_force, col_wipe = st.columns(3)
        if col_clear.button("🔄 Clear Cache & Retry", key=f"clear_dup_ctr_{res.get('sha256', '')[:6]}", width="stretch"):
            clear_local_ingestion_hashes()
            st.rerun()
        if col_force.button("⚡ Force Ingest & Overwrite", key=f"force_dup_ctr_{res.get('sha256', '')[:6]}", width="stretch"):
            with st.spinner(f"Force ingesting {rtype} into Supabase..."):
                execute_live_juno_ingestion(
                    temp_path,
                    expected_type=rtype,
                    uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
                    allow_reimport=True,
                )
            st.rerun()
        if col_wipe.button("🗑️ Wipe All Database Data", key=f"wipe_dup_ctr_{res.get('sha256', '')[:6]}", width="stretch"):
            wipe_res = remove_all_database_data()
            st.success(wipe_res["message"])
            st.rerun()
        return

    if not res.get("success"):
        st.error(res.get("message", "Master pipeline execution failed."))
        return

    if res.get("cloud_injected"):
        st.success(
            f"✅ **Master Ingestion Complete!** {res['valid_rows']} clean readings injected into Supabase "
            f"(`energy_readings.{rtype.lower()}`). Linked Asset: `{res['asset_id']}`"
        )
    elif res.get("cloud_error"):
        st.warning(
            f"⚠️ **Supabase Cloud Notice**: Database reported: `{res['cloud_error']}`.\n\n"
            "💡 **Fix PGRST002**: Run `NOTIFY pgrst, 'reload schema';` in Supabase SQL Editor to reload the schema cache."
        )
    else:
        st.info(
            f"⚡ **Master Ingestion Verified!** Running in local mode (Asset: `{res['asset_id']}`). "
            "Supabase cloud persistence active when credentials are provided in secrets or .env."
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Batch ID", f"LIVE-{res['sha256'][:8]}")
    m2.metric("Total Records", f"{res['total_records']:,}")
    m3.metric("Valid Readings Injected", f"{res['valid_rows']:,}")
    m4.metric("Exceptions Excluded", f"{res['exception_rows']:,}")

    # Asset telemetry breakdown
    if res.get("asset_breakdown"):
        st.markdown("##### 🏷️ Asset Code Telemetry Breakdown")
        breakdown_rows = []
        for ac, info in res["asset_breakdown"].items():
            breakdown_rows.append({
                "Asset Code": ac,
                "Asset ID": info.get("asset_id", "—"),
                "Toll Plaza": info.get("plaza_id", "—"),
                "Module": info.get("source_type", rtype),
                "Readings Injected": f"{info.get('count', 0):,}",
                "Start Date": info.get("start_date", "—"),
                "Last Date": info.get("last_date", "—"),
                "Status": "INGESTED ✓",
            })
        st.dataframe(pd.DataFrame(breakdown_rows), width="stretch", hide_index=True)

    st.subheader(f"{rtype} Master KPI Results")
    kpis = res.get("kpis", [])
    if kpis:
        kpi_cols = st.columns(min(len(kpis), 4))
        for idx, kpi in enumerate(kpis):
            col = kpi_cols[idx % len(kpi_cols)]
            val = kpi["value"]
            col.metric(
                kpi["kpi_code"],
                "NULL" if val is None else f"{float(val):,.4f}",
                kpi.get("unit", ""),
            )

    if res.get("exception_details"):
        st.warning(f"⚠️ {res['exception_rows']} raw record(s) flagged with validation errors and excluded from KPI calculations. Offending rows with responsible technician:")
        exc_table = pd.DataFrame([
            {
                "Row #": d["row_number"],
                "Timestamp": d["timestamp"],
                "Technician (Created By)": d.get("technician_name", "—"),
                "Logged At (Created On)": d.get("created_on", "—"),
                "Rule": d["rule_code"],
                "Severity": d["severity"],
                "Offending Value": d["offending_value"],
                "Expected": d["expected_value"],
                "Message": d["message"],
            }
            for d in res["exception_details"]
        ])
        st.dataframe(exc_table, width="stretch", hide_index=True)
        with st.expander("🔍 Inspect Exact Raw Data of Offending Rows"):
            for d in res["exception_details"]:
                st.markdown(f"**Row #{d['row_number']}** ({d['timestamp']}) — `{d['rule_code']}`: {d['message']}")
                st.json(d["raw_values"])

    st.subheader("Validated Data Preview (First 50 Rows)")
    st.dataframe(res["preview_df"].head(50), width="stretch", hide_index=True)


def render():
    st.title("JUNO Import Center — Unified Master Ingestion")
    st.caption(
        "Single ingestion portal supporting single or multiple CSV uploads across all 5 energy sources: EB, DG, Solar, Transformer, and UPS. "
        "Strict Level 1 (SHA-256) and Level 2 (asset_id, datetime) deduplication enforced. "
        "Clean valid records inject directly into Supabase while exceptions are logged to energy_validation.exception_record."
    )

    all_samples = list_sample_files()
    sample_options = {s["label"]: s["path"] for s in all_samples}

    col_up, col_samp = st.columns([1.2, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Upload original JUNO CSV (Single or Multiple files: EB / DG / Solar / Transformer / UPS)",
            type=["csv"],
            accept_multiple_files=True,
            help="Upload one or multiple raw files directly from JUNO without modifying headings or data.",
        )
    with col_samp:
        st.write("**Or select from 21 repository sample files:**")
        selected_sample_label = st.selectbox(
            "Available Repository Samples",
            list(sample_options.keys()),
            index=0 if sample_options else None,
            label_visibility="collapsed",
        )
        col_sm1, col_sm2 = st.columns(2)
        use_sample = col_sm1.button("📂 Load Selected Sample CSV", width="stretch")
        use_all_samples = col_sm2.button("📦 Load All 21 Samples", width="stretch")

    files_to_process = []

    if uploaded:
        for uf in uploaded:
            data = uf.getvalue()
            p = _save_temp(data, uf.name)
            files_to_process.append({
                "path": p,
                "name": uf.name,
                "size": uf.size,
                "data": data,
                "is_temp": True,
            })
    elif use_all_samples or "unified_load_all" in st.session_state:
        if use_all_samples:
            st.session_state["unified_load_all"] = True
        for label, s_path in sample_options.items():
            p = Path(s_path)
            if p.exists():
                files_to_process.append({
                    "path": p,
                    "name": p.name,
                    "size": p.stat().st_size,
                    "data": p.read_bytes(),
                    "is_temp": False,
                })
    elif use_sample or "unified_active_path" in st.session_state:
        if use_sample and selected_sample_label:
            st.session_state["unified_active_path"] = sample_options[selected_sample_label]
        target_path = st.session_state.get("unified_active_path", list(sample_options.values())[0])
        temp_path = Path(target_path)
        data = temp_path.read_bytes()
        files_to_process.append({
            "path": temp_path,
            "name": temp_path.name,
            "size": temp_path.stat().st_size,
            "data": data,
            "is_temp": False,
        })
    else:
        first_path = list(sample_options.values())[0] if sample_options else None
        if first_path:
            temp_path = Path(first_path)
            data = temp_path.read_bytes()
            files_to_process.append({
                "path": temp_path,
                "name": temp_path.name,
                "size": temp_path.stat().st_size,
                "data": data,
                "is_temp": False,
            })
            st.info(f"💡 Showing default sample file: **{temp_path.name}**. Upload your files or click Ingest below.")
        else:
            st.info("Upload any JUNO CSV to begin master ingestion.")
            return

    if not files_to_process:
        return

    # Inspect all queued files
    center_service = JunoImportService()
    import_service = ImportService()
    inspected_files = []
    overview_rows = []

    for item in files_to_process:
        try:
            insp = import_service.inspect(str(item["path"]))
            meta, checks = center_service.precheck(item["name"], item["data"])
            item["inspection"] = insp
            item["meta"] = meta
            item["checks"] = checks
            item["rtype"] = insp["report_type"]
            inspected_files.append(item)
            overview_rows.append({
                "File Name": item["name"],
                "Source Type": insp["report_type"],
                "Asset / Meter ID": insp["metadata"].asset_code or "—",
                "Location": insp["metadata"].location or "—",
                "Parsed Rows": f"{insp['record_count']:,}",
                "File Size": f"{item['size']:,} bytes",
                "Status": "READY ✓",
            })
        except Exception as exc:
            overview_rows.append({
                "File Name": item["name"],
                "Source Type": "ERROR",
                "Asset / Meter ID": "—",
                "Location": "—",
                "Parsed Rows": "0",
                "File Size": f"{item['size']:,} bytes",
                "Status": f"ERROR: {exc}",
            })

    st.subheader(f"📁 Queued Files ({len(files_to_process)} CSV file{'s' if len(files_to_process) > 1 else ''})")
    st.dataframe(pd.DataFrame(overview_rows), width="stretch", hide_index=True)

    # Module-Wise Pre-Ingestion Data Counts
    module_stats = {
        "EB": {"files": 0, "rows": 0, "icon": "⚡"},
        "DG": {"files": 0, "rows": 0, "icon": "🛢️"},
        "SOLAR": {"files": 0, "rows": 0, "icon": "☀️"},
        "TRANSFORMER": {"files": 0, "rows": 0, "icon": "🔌"},
        "UPS": {"files": 0, "rows": 0, "icon": "🔋"},
    }
    for item in inspected_files:
        rtype = str(item.get("rtype", "")).upper()
        if rtype in module_stats:
            module_stats[rtype]["files"] += 1
            module_stats[rtype]["rows"] += item["inspection"]["record_count"]

    st.markdown("#### 📦 Queued Data Breakdown (Module-Wise)")
    st.caption("Pre-ingestion telemetry row count and files queued per module:")
    qc1, qc2, qc3, qc4, qc5 = st.columns(5)
    cols = [qc1, qc2, qc3, qc4, qc5]
    for idx, (m_code, m_info) in enumerate(module_stats.items()):
        cols[idx].metric(
            label=f"{m_info['icon']} {m_code}",
            value=f"{m_info['rows']:,} rows",
            delta=f"{m_info['files']} file(s)",
        )

    # Asset Code-Wise Pre-Ingestion Data Breakdown
    from backend.services.energy_command_store import resolve_canonical_asset
    asset_pre_stats = []
    for item in inspected_files:
        acode = item["inspection"]["metadata"].asset_code or "—"
        rtype = item.get("rtype", "EB")
        resolved = resolve_canonical_asset(acode, rtype)
        asset_pre_stats.append({
            "Asset Code": resolved["asset_code"],
            "Plaza": resolved["plaza_id"],
            "Equipment": resolved["source_type"],
            "Asset Name": resolved["asset_name"],
            "File Name": item["name"],
            "Queued Telemetry Rows": f"{item['inspection']['record_count']:,}",
            "Status": "READY ✓",
        })

    st.markdown("#### 🏷️ Queued Data Breakdown (Asset Code-Wise)")
    st.caption("Pre-ingestion telemetry record count and plaza assignment per individual asset code:")
    st.dataframe(pd.DataFrame(asset_pre_stats), width="stretch", hide_index=True)

    reimport_override = st.checkbox(
        "Force re-import / overwrite if previously ingested",
        value=False,
        help="Bypasses duplicate file rejection and re-runs ingestion directly into Supabase.",
        key="unified_multi_reimport_cb",
    )

    # If Single File
    if len(inspected_files) == 1:
        it = inspected_files[0]
        st.caption(f"Asset / Meter ID: **{it['inspection']['metadata'].asset_code or '—'}** • Location: **{it['inspection']['metadata'].location or 'Unspecified'}**")

        st.subheader("Pre-check Integrity")
        pcols = st.columns(len(it["checks"])) if it["checks"] else [st.container()]
        for idx, check in enumerate(it["checks"]):
            col = pcols[idx % len(pcols)]
            icon = "✅" if check.status == "PASS" else ("⛔" if check.status in {"FAIL", "BLOCK"} else "⚠️")
            col.write(f"{icon} **{check.code}**")
            col.caption(check.message)

        rtype = it["rtype"]
        if st.button(f"🚀 Ingest {rtype} → Supabase → Validate Rules → Calculate Master KPIs", type="primary", width="stretch"):
            with st.spinner(f"Processing unified master pipeline for {rtype}: Deduplication → Validation → Supabase Injection..."):
                res = execute_live_juno_ingestion(
                    it["path"],
                    expected_type=rtype,
                    uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
                    allow_reimport=reimport_override,
                    original_filename=it["name"],
                )
            _render_single_center_results(res, rtype, it["path"], it["is_temp"])
            from core.supabase_manager import get_live_module_counts
            live_counts = get_live_module_counts()
            st.divider()
            st.markdown("#### 🏛️ Live Supabase PostgreSQL Record Count (Post-Ingestion)")
            mod_code = rtype.upper()
            live_val = live_counts.get(mod_code, 0)
            st.metric(f"⚡ {mod_code} Live Records in Supabase", f"{live_val:,} records", help="Direct live query on Supabase PostgreSQL")

    # If Multiple Files
    else:
        btn_label = f"🚀 Ingest All {len(inspected_files)} Files → Supabase → Validate Rules → Calculate Master KPIs"
        if st.button(btn_label, type="primary", width="stretch"):
            with st.spinner(f"Processing batch of {len(inspected_files)} mixed files in sequence..."):
                batch_results = []
                total_injected = 0
                total_exceptions = 0
                success_count = 0
                dup_count = 0
                fail_count = 0

                for it in inspected_files:
                    res = execute_live_juno_ingestion(
                        it["path"],
                        expected_type=it["rtype"],
                        uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
                        allow_reimport=reimport_override,
                        original_filename=it["name"],
                    )
                    batch_results.append((it, res))
                    if res.get("status") == "SUCCESS":
                        success_count += 1
                        total_injected += res.get("injected_readings", 0)
                        total_exceptions += res.get("exception_rows", 0)
                    elif res.get("status") == "DUPLICATE_FILE":
                        dup_count += 1
                    else:
                        fail_count += 1

            st.divider()
            st.subheader("📊 Unified Batch Ingestion Summary")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Total Files Processed", f"{len(inspected_files)}")
            b2.metric("Successful Imports", f"{success_count}")
            b3.metric("Total Readings Injected", f"{total_injected:,}")
            b4.metric("Exceptions Excluded", f"{total_exceptions:,}")

            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} file(s) were skipped because they were already imported. Enable 'Force re-import' to overwrite them.")

            # Asset Code-wise breakdown of batch ingested results
            ingested_asset_rows = []
            for it, res in batch_results:
                if res.get("asset_breakdown"):
                    for ac, b_info in res["asset_breakdown"].items():
                        ingested_asset_rows.append({
                            "Asset Code": ac,
                            "Plaza": b_info.get("plaza_id", "—"),
                            "Equipment": b_info.get("source_type", it.get("rtype")),
                            "Injected Readings": f"{b_info.get('count', 0):,}",
                            "Start Date": b_info.get("start_date", "—"),
                            "Last Date": b_info.get("last_date", "—"),
                            "Status": "PERSISTED ✓",
                        })
            if ingested_asset_rows:
                st.subheader("🏷️ Asset Code-Wise Ingestion Telemetry Summary (Post-Insertion)")
                st.caption("Automatic telemetry registration across asset master:")
                st.dataframe(pd.DataFrame(ingested_asset_rows), width="stretch", hide_index=True)

            st.subheader("📑 Individual File Results & KPIs")
            for it, res in batch_results:
                fname = it["name"]
                rtype = it["rtype"]
                status_icon = "✅" if res.get("status") == "SUCCESS" else ("⛔" if res.get("status") == "DUPLICATE_FILE" else "❌")
                with st.expander(f"{status_icon} **{fname}** [{rtype}] — {res.get('status')} ({res.get('valid_rows', 0)} valid readings)"):
                    _render_single_center_results(res, rtype, it["path"], it["is_temp"])
            # Module-wise breakdown of batch ingested results
            ingested_module_breakdown = {}
            for it, res in batch_results:
                mod = str(it.get("rtype", "")).upper()
                item_stats = ingested_module_breakdown.setdefault(mod, {
                    "Module": mod,
                    "Files Processed": 0,
                    "Parsed Rows": 0,
                    "Valid Injected": 0,
                    "Exceptions Excluded": 0,
                })
                item_stats["Files Processed"] += 1
                item_stats["Parsed Rows"] += it["inspection"]["record_count"]
                item_stats["Valid Injected"] += res.get("valid_rows", 0)
                item_stats["Exceptions Excluded"] += res.get("exception_rows", 0)

            st.divider()
            st.subheader("📊 Ingestion Execution Results (Module-Wise)")
            st.dataframe(pd.DataFrame(list(ingested_module_breakdown.values())), width="stretch", hide_index=True)

            from core.supabase_manager import get_live_module_counts
            live_counts = get_live_module_counts()
            st.markdown("#### 🏛️ Live Supabase PostgreSQL Record Counts (Post-Ingestion)")
            st.caption("Verified live record totals queried directly from Supabase PostgreSQL tables:")
            post_c1, post_c2, post_c3, post_c4, post_c5 = st.columns(5)
            p_cols = [post_c1, post_c2, post_c3, post_c4, post_c5]
            for idx, (m_code, m_info) in enumerate(module_stats.items()):
                live_cnt = live_counts.get(m_code, 0)
                p_cols[idx].metric(
                    label=f"{m_info['icon']} {m_code} in Supabase",
                    value=f"{live_cnt:,} records",
                    help=f"Direct live query on Supabase energy_readings.{m_code.lower()}",
                )


if __name__ == "__main__":
    render()
