from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import pandas as pd

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st

from analytics.dg_phase5_3 import calculate_dg_kpis
from analytics.eb_phase5_4 import calculate_eb_kpis
from analytics.solar_phase5_5 import calculate_solar_kpis
from analytics.transformer_phase5_6 import calculate_transformer_kpis
from analytics.ups_phase5_7 import calculate_ups_kpis
from energy_validation.persistence import NormalizationPersistence
from import_center.service import JunoImportService
from import_center.simulation import list_sample_files, run_local_ingestion_simulation
from import_engine.service import ImportService
from supabase_import.config import load_settings
from supabase_import.pipeline import ImportPipeline

KPI_CALCULATORS = {
    "EB": (calculate_eb_kpis, "5.4.0"),
    "DG": (calculate_dg_kpis, "5.3.1"),
    "SOLAR": (calculate_solar_kpis, "5.5.0"),
    "TRANSFORMER": (calculate_transformer_kpis, "5.6.0"),
    "UPS": (calculate_ups_kpis, "5.7.0"),
}


def _save_temp(data: bytes, filename: str) -> Path:
    ext = Path(filename).suffix or ".csv"
    fd, name = tempfile.mkstemp(prefix="srtpl_unified_", suffix=ext)
    p = Path(name)
    p.write_bytes(data)
    return p


def render():
    st.title("JUNO Import Center — Unified Master Ingestion")
    st.caption(
        "Single ingestion portal supporting all 5 energy sources: EB, DG, Solar, Transformer, and UPS. "
        "The original file is preserved; duplicate SHA-256 detection is enforced; NULL remains NULL."
    )

    all_samples = list_sample_files()
    sample_options = {s["label"]: s["path"] for s in all_samples}

    col_up, col_samp = st.columns([1.2, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Upload original JUNO CSV (EB / DG / Solar / Transformer / UPS)",
            type=["csv"],
            accept_multiple_files=False,
            help="Upload raw file directly from JUNO without modifying headings or data.",
        )
    with col_samp:
        st.write("**Or select from 21 repository sample files:**")
        selected_sample_label = st.selectbox(
            "Available Repository Samples",
            list(sample_options.keys()),
            index=0 if sample_options else None,
            label_visibility="collapsed",
        )
        use_sample = st.button("📂 Load Selected Sample CSV", width="stretch")

    if uploaded:
        data = uploaded.getvalue()
        source_name = uploaded.name
        temp_path = _save_temp(data, source_name)
        is_temp = True
    elif use_sample or "unified_active_path" in st.session_state:
        if use_sample and selected_sample_label:
            st.session_state["unified_active_path"] = sample_options[selected_sample_label]
        target_path = st.session_state.get("unified_active_path", list(sample_options.values())[0])
        temp_path = Path(target_path)
        data = temp_path.read_bytes()
        source_name = temp_path.name
        is_temp = False
    else:
        first_path = list(sample_options.values())[0] if sample_options else None
        if first_path:
            temp_path = Path(first_path)
            data = temp_path.read_bytes()
            source_name = temp_path.name
            is_temp = False
            st.info(f"💡 Showing default sample file: **{source_name}**. Upload a live file or click **Import** to process.")
        else:
            st.info("Upload any JUNO CSV to begin master ingestion.")
            return

    center_service = JunoImportService()
    metadata, checks = center_service.precheck(source_name, data)

    st.subheader("File Details & Auto-detection")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("File Size", f"{metadata.size_bytes:,} bytes")
    c2.metric("SHA-256", metadata.sha256[:16] + "…")
    c3.metric("Detected Source", metadata.report_type or "REVIEW")

    import_service = ImportService()
    try:
        inspection = import_service.inspect(str(temp_path))
        c4.metric("Parsed Rows", f'{inspection["record_count"]:,}')
        asset_code = inspection["metadata"].asset_code or "—"
    except Exception as exc:
        c4.metric("Parse Status", "FAIL")
        st.error(f"Failed to inspect JUNO structure: {exc}")
        if is_temp:
            temp_path.unlink(missing_ok=True)
        return

    st.caption(f"Asset / Meter ID: **{asset_code}** • Location: **{inspection['metadata'].location or 'Unspecified'}**")

    st.subheader("Pre-check Integrity")
    pcols = st.columns(len(checks)) if checks else [st.container()]
    for idx, check in enumerate(checks):
        col = pcols[idx % len(pcols)]
        icon = "✅" if check.status == "PASS" else ("⛔" if check.status in {"FAIL", "BLOCK"} else "⚠️")
        col.write(f"{icon} **{check.code}**")
        col.caption(check.message)

    with st.expander("Preview Original CSV Header & Top Lines", expanded=False):
        st.code(data.decode("utf-8-sig", errors="replace")[:3000])

    rtype = inspection["report_type"]
    if rtype not in KPI_CALCULATORS:
        st.error(f"Detected report type '{rtype}' is not registered for automated KPI calculation.")
        if is_temp:
            temp_path.unlink(missing_ok=True)
        return

    calc_func, calc_version = KPI_CALCULATORS[rtype]

    if st.button(f"🚀 Ingest {rtype} → Validate Rules → Calculate Master KPIs", type="primary", width="stretch"):
        settings = load_settings()
        has_supabase = bool(settings.supabase_url and settings.supabase_key)
        demo_mode = st.session_state.get("demo_mode_active", True)

        if has_supabase and not demo_mode:
            try:
                from supabase import create_client
                db = create_client(settings.supabase_url, settings.supabase_key)

                pipeline_result = ImportPipeline(db, settings, import_service).run(
                    str(temp_path), uploaded_by=st.session_state.get("user", "admin@srtpl.com")
                )

                if pipeline_result.get("status") == "DUPLICATE_FILE":
                    st.warning(f"Duplicate file detected: {pipeline_result.get('message')}")
                    st.json(pipeline_result)
                    return

                if pipeline_result.get("status") != "IMPORTED":
                    st.warning(pipeline_result)
                    return

                batch_id = pipeline_result["import_batch_id"]
                norm_persistence = NormalizationPersistence(
                    db, calculation_version=calc_version
                ).process_batch(batch_id, rtype)

                kpis = calc_func(db, batch_id, calc_version)

                st.success(f"Unified master pipeline completed for {rtype}. Batch: {batch_id}")

                st.subheader("Import Result")
                st.json({
                    "status": pipeline_result["status"],
                    "batch_id": batch_id,
                    "report_type": rtype,
                    "rows_imported": pipeline_result["rows"],
                    "sha256": pipeline_result["sha256"],
                })

                st.subheader(f"{rtype} Production KPI Results")
                k_cols = st.columns(len(kpis.get("results", [])))
                for idx, row in enumerate(kpis.get("results", [])):
                    val = row["value"]
                    k_cols[idx].metric(
                        row["kpi_code"],
                        "NULL" if val is None else f"{float(val):,.4f}",
                        row.get("unit", ""),
                    )
            except Exception as exc:
                st.error(f"Unified production pipeline execution failed: {exc}")
        else:
            with st.spinner(f"Executing master {rtype} validation rules and KPI calculation locally..."):
                sim_res = run_local_ingestion_simulation(temp_path, expected_type=rtype)

            st.success(f"⚡ Ingestion and calculation verified locally for {rtype} (Supabase bypass / demo mode active).")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Batch ID", f"LOCAL-{sim_res['sha256'][:8]}")
            m2.metric("Total Records", f"{sim_res['record_count']:,}")
            m3.metric("Valid Readings", f"{sim_res['valid_rows']:,}")
            m4.metric("Exceptions Excluded", f"{sim_res['exception_rows']:,}")

            st.subheader(f"{rtype} KPI Results")
            kpi_cols = st.columns(min(len(sim_res["kpis"]), 4))
            for idx, kpi in enumerate(sim_res["kpis"]):
                col = kpi_cols[idx % len(kpi_cols)]
                val = kpi["value"]
                col.metric(
                    kpi["kpi_code"],
                    "NULL" if val is None else f"{float(val):,.4f}",
                    kpi.get("unit", ""),
                )

            if sim_res.get("exception_details"):
                st.error(f"⚠️ {sim_res['exception_rows']} raw record(s) flagged with validation errors. Offending raw rows below:")
                exc_table = pd.DataFrame([
                    {
                        "Row #": d["row_number"],
                        "Timestamp": d["timestamp"],
                        "Rule": d["rule_code"],
                        "Severity": d["severity"],
                        "Offending Value": d["offending_value"],
                        "Expected": d["expected_value"],
                        "Message": d["message"],
                    }
                    for d in sim_res["exception_details"]
                ])
                st.dataframe(exc_table, width="stretch", hide_index=True)
                with st.expander("🔍 Inspect Exact Raw Data of Offending Rows"):
                    for d in sim_res["exception_details"]:
                        st.markdown(f"**Row #{d['row_number']}** ({d['timestamp']}) — `{d['rule_code']}`: {d['message']}")
                        st.json(d["raw_values"])

            st.subheader("Validated Data Preview (First 50 Rows)")
            st.dataframe(sim_res["preview_df"].head(50), width="stretch", hide_index=True)

            with st.expander("Full Traceability & Audit Trail"):
                st.json({
                    "batch_id": f"LOCAL-{sim_res['sha256'][:8]}",
                    "source_type": rtype,
                    "calculation_version": sim_res["calculation_version"],
                    "source_reading_count": sim_res["valid_rows"],
                    "exception_count": sim_res["exception_rows"],
                    "sha256": sim_res["sha256"],
                })

    if is_temp:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    render()
