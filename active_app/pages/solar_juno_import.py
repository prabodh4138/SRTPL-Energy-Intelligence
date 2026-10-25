from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st
import pandas as pd

from import_center.simulation import list_sample_files
from import_engine.service import ImportService
from core.live_pipeline import (
    execute_live_juno_ingestion,
    execute_batch_live_juno_ingestion,
    clear_local_ingestion_hashes,
)
from core.supabase_manager import remove_all_database_data


def _save_uploaded(uploaded) -> Path:
    fd, name = tempfile.mkstemp(prefix="srtpl_solar_", suffix=".csv")
    os.close(fd)
    path = Path(name)
    path.write_bytes(uploaded.getvalue())
    return path


def _safe_unlink(path: Path | None) -> None:
    if path and path.exists():
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _render_single_solar_results(res: dict, is_temp: bool = False, path: Path | None = None):
    """Renders the comprehensive results view for a single ingested Solar file."""
    if res.get("status") == "DUPLICATE_FILE":
        st.error(res["message"])
        col_clear, col_force, col_wipe = st.columns(3)
        if col_clear.button("🔄 Clear Cache & Retry", key=f"clear_dup_sol_{res.get('sha256', '')[:6]}", width="stretch"):
            clear_local_ingestion_hashes()
            st.rerun()
        if col_force.button("⚡ Force Ingest & Overwrite", key=f"force_dup_sol_{res.get('sha256', '')[:6]}", width="stretch"):
            with st.spinner("Force ingesting Solar into Supabase..."):
                execute_live_juno_ingestion(
                    path,
                    expected_type="SOLAR",
                    uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
                    allow_reimport=True,
                )
            st.rerun()
        if col_wipe.button("🗑️ Wipe All Database Data", key=f"wipe_dup_sol_{res.get('sha256', '')[:6]}", width="stretch"):
            wipe_res = remove_all_database_data()
            st.success(wipe_res["message"])
            st.rerun()
        return

    if not res.get("success"):
        st.error(res.get("message", "Solar Pipeline execution failed."))
        return

    if res.get("cloud_injected"):
        st.success(
            f"✅ **Solar Pipeline Complete!** Clean readings successfully injected into Supabase "
            f"(`energy_readings.solar`). Linked Asset: `{res['asset_id']}`"
        )
    elif res.get("cloud_error"):
        st.warning(
            f"⚠️ **Supabase Cloud Notice**: Database reported: `{res['cloud_error']}`.\n\n"
            "💡 **Fix PGRST002**: Run `NOTIFY pgrst, 'reload schema';` in Supabase SQL Editor to reload the schema cache."
        )
    else:
        st.info(
            f"⚡ **Solar Pipeline Verified!** Running in local mode (Asset: `{res['asset_id']}`). "
            "Supabase cloud persistence active when credentials are provided in secrets or .env."
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Batch ID", f"LIVE-{res['sha256'][:8]}")
    m2.metric("Total Records", f"{res['total_records']:,}")
    m3.metric("Valid Readings Injected", f"{res['valid_rows']:,}")
    m4.metric("Exceptions Excluded", f"{res['exception_rows']:,}")

    st.subheader("Solar KPI Results")
    kpis = res.get("kpis", [])
    if kpis:
        kpi_cols = st.columns(len(kpis))
        for idx, kpi in enumerate(kpis):
            val = kpi["value"]
            kpi_cols[idx].metric(
                kpi["kpi_code"],
                "NULL" if val is None else f"{float(val):,.4f}",
                kpi.get("unit", ""),
            )

    if res.get("exception_details"):
        st.warning(f"⚠️ {res['exception_rows']} raw record(s) flagged with validation errors and excluded from KPI calculations. Offending rows:")
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

    with st.expander("Full Traceability & Audit Trail"):
        st.json({
            "batch_id": f"LIVE-{res['sha256'][:8]}",
            "source_type": "SOLAR",
            "asset_id": res["asset_id"],
            "asset_code": res["asset_code"],
            "calculation_version": res["calculation_version"],
            "total_records": res["total_records"],
            "valid_rows": res["valid_rows"],
            "exception_rows": res["exception_rows"],
            "sha256": res["sha256"],
            "cloud_injected": res.get("cloud_injected", False),
        })


def render():
    st.title("Solar — JUNO Import → Validation → KPI")
    st.caption(
        "Upload single or multiple raw JUNO Solar CSV files without modifications. "
        "Strict Level 1 (SHA-256) and Level 2 (asset_id, datetime) deduplication enforced. "
        "Clean valid records inject directly into Supabase (`energy_readings.solar`) while exceptions are logged to energy_validation.exception_record."
    )

    sample_files = list_sample_files("Solar")
    sample_options = {s["label"]: s["path"] for s in sample_files}

    uploaded = st.file_uploader(
        "Upload original JUNO Solar CSV (Single or Multiple files supported)",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload one or multiple raw Solar files downloaded from JUNO without editing headings or rows.",
    )

    files_to_process: list[dict] = []

    if uploaded:
        for uf in uploaded:
            p = _save_uploaded(uf)
            files_to_process.append({
                "path": p,
                "name": uf.name,
                "size": uf.size,
                "is_temp": True,
            })
    else:
        st.info("💡 Upload one or multiple untouched JUNO Solar CSV files above, or select from sample files below:")
        st.subheader("Repository Sample Solar Files")
        selected_sample_label = st.selectbox(
            "Select sample file to inspect and process:",
            list(sample_options.keys()),
            index=0 if sample_options else None,
        )
        col_load_one, col_load_all = st.columns(2)
        if col_load_one.button("📂 Load Selected Sample CSV", type="secondary", width="stretch"):
            st.session_state["solar_selected_samples"] = [sample_options[selected_sample_label]]

        if col_load_all.button("📦 Load All Repository Solar Samples", type="secondary", width="stretch"):
            st.session_state["solar_selected_samples"] = list(sample_options.values())

        active_samples = st.session_state.get("solar_selected_samples")
        if active_samples:
            for s_path in active_samples:
                p = Path(s_path)
                if p.exists():
                    files_to_process.append({
                        "path": p,
                        "name": p.name,
                        "size": p.stat().st_size,
                        "is_temp": False,
                    })
        else:
            return

    if not files_to_process:
        return

    service = ImportService()
    inspected_files = []
    overview_rows = []

    for item in files_to_process:
        try:
            insp = service.inspect(str(item["path"]))
            item["inspection"] = insp
            inspected_files.append(item)
            overview_rows.append({
                "File Name": item["name"],
                "Source Type": insp["report_type"],
                "Plant ID (asset_code)": insp["metadata"].asset_code or "—",
                "Location": insp["metadata"].location or "—",
                "Parsed Rows": f"{insp['record_count']:,}",
                "File Size": f"{item['size']:,} bytes",
                "Status": "READY ✓" if insp["report_type"] == "SOLAR" else f"MISMATCH ({insp['report_type']})",
            })
        except Exception as exc:
            overview_rows.append({
                "File Name": item["name"],
                "Source Type": "PARSE_ERROR",
                "Plant ID": "—",
                "Location": "—",
                "Parsed Rows": "0",
                "File Size": f"{item['size']:,} bytes",
                "Status": f"ERROR: {exc}",
            })

    st.subheader(f"📁 Queued Files ({len(files_to_process)} CSV file{'s' if len(files_to_process) > 1 else ''})")
    st.dataframe(pd.DataFrame(overview_rows), width="stretch", hide_index=True)

    reimport_override = st.checkbox(
        "Force re-import / overwrite if previously ingested",
        value=False,
        help="Bypasses duplicate file rejection and re-runs ingestion directly into Supabase.",
        key="solar_multi_reimport_cb",
    )

    if len(inspected_files) == 1:
        single_item = inspected_files[0]
        single_insp = single_item["inspection"]
        if single_insp["report_type"] != "SOLAR":
            st.error(f"File '{single_item['name']}' was detected as '{single_insp['report_type']}', not SOLAR. Import blocked.")
            return

        with st.expander("Detected metadata & solar details"):
            st.json({
                "solar_plant_id (asset_code)": single_insp["metadata"].asset_code,
                "location": single_insp["metadata"].location or "—",
                "report_title": single_insp["metadata"].report_title,
                "downloaded_by": single_insp["metadata"].downloaded_by,
                "organization": single_insp["metadata"].organization,
                "sha256": single_insp["sha256"],
                "parser_version": single_insp["parser_version"],
            })

        if st.button("🚀 Ingest Solar → Supabase → Validate → Calculate KPI", type="primary", width="stretch"):
            with st.spinner("Processing Solar pipeline: Deduplication → Validation → Supabase Injection → Master KPIs..."):
                res = execute_live_juno_ingestion(
                    single_item["path"],
                    expected_type="SOLAR",
                    uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
                    allow_reimport=reimport_override,
                )
            _render_single_solar_results(res, is_temp=single_item["is_temp"], path=single_item["path"])

    else:
        btn_label = f"🚀 Ingest All {len(inspected_files)} Solar Files → Supabase → Validate → Calculate KPIs"
        if st.button(btn_label, type="primary", width="stretch"):
            with st.spinner(f"Processing batch of {len(inspected_files)} Solar files in sequence..."):
                batch_res = execute_batch_live_juno_ingestion(
                    [f["path"] for f in inspected_files],
                    expected_type="SOLAR",
                    uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
                    allow_reimport=reimport_override,
                )

            st.divider()
            st.subheader("📊 Solar Batch Ingestion Summary")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Total Files Processed", f"{batch_res['total_files']}")
            b2.metric("Successful Imports", f"{batch_res['success_count']}")
            b3.metric("Total Readings Injected", f"{batch_res['total_injected']:,}")
            b4.metric("Exceptions Excluded", f"{batch_res['total_exceptions']:,}")

            if batch_res["duplicate_count"] > 0:
                st.warning(f"⚠️ {batch_res['duplicate_count']} file(s) were skipped because they were already imported. Enable 'Force re-import' to overwrite them.")

            st.subheader("📑 Individual File Results & KPIs")
            for idx, res in enumerate(batch_res["file_results"]):
                fname = inspected_files[idx]["name"]
                status_icon = "✅" if res.get("status") == "SUCCESS" else ("⛔" if res.get("status") == "DUPLICATE_FILE" else "❌")
                with st.expander(f"{status_icon} **{fname}** — {res.get('status')} ({res.get('valid_rows', 0)} valid readings)"):
                    _render_single_solar_results(res, is_temp=inspected_files[idx]["is_temp"], path=inspected_files[idx]["path"])


if __name__ == "__main__":
    render()
