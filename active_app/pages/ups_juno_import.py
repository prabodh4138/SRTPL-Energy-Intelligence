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

from analytics.ups_phase5_7 import calculate_ups_kpis
from energy_validation.persistence import NormalizationPersistence
from import_center.simulation import list_sample_files, run_local_ingestion_simulation
from import_engine.service import ImportService
from supabase_import.config import load_settings
from supabase_import.pipeline import ImportPipeline


def _save_uploaded(uploaded) -> Path:
    fd, name = tempfile.mkstemp(prefix="srtpl_ups_", suffix=".csv")
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


def render():
    st.title("UPS — JUNO Import → Validation → KPI")
    st.caption(
        "Phase 5.7 • Uninterruptible Power Supply (UPS) telemetry, battery voltages, bypass and inverter metrics. "
        "Upload the untouched JUNO CSV without editing it."
    )

    sample_files = list_sample_files("UPS")
    sample_options = {s["label"]: s["path"] for s in sample_files}

    uploaded = st.file_uploader(
        "Upload original JUNO UPS CSV",
        type=["csv"],
        accept_multiple_files=False,
        help="Upload raw file directly from JUNO without modifying headings or data.",
    )

    path: Path | None = None
    is_temp = False
    file_size = 0

    if uploaded:
        path = _save_uploaded(uploaded)
        is_temp = True
        file_size = uploaded.size
    else:
        st.info("💡 Upload an untouched JUNO UPS CSV above, or select from sample files below:")
        st.subheader("Repository Sample UPS Files")
        selected_sample_label = st.selectbox(
            "Select sample file to inspect and process:",
            list(sample_options.keys()),
            index=0 if sample_options else None,
        )
        if st.button("📂 Load Selected Sample CSV", type="secondary", width="stretch"):
            st.session_state["ups_selected_sample"] = sample_options[selected_sample_label]

        active_sample = st.session_state.get("ups_selected_sample")
        if active_sample:
            path = Path(active_sample)
            is_temp = False
            file_size = path.stat().st_size
        else:
            return

    service = ImportService()
    try:
        inspection = service.inspect(str(path))
    except Exception as exc:
        st.error(f"UPS CSV inspection failed: {exc}")
        if is_temp:
            _safe_unlink(path)
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Detected type", inspection["report_type"])
    c2.metric("Parsed rows", f'{inspection["record_count"]:,}')
    c3.metric("UPS unit", inspection["metadata"].asset_code or "—")
    c4.metric("File size", f"{file_size:,} bytes")

    if inspection["report_type"] != "UPS":
        st.error("This file was not detected as a UPS JUNO report. Import is blocked.")
        if is_temp:
            _safe_unlink(path)
        return

    st.success("UPS JUNO structure detected. Ready for controlled Supabase import.")

    with st.expander("Detected metadata"):
        st.json({
            "report_title": inspection["metadata"].report_title,
            "downloaded_by": inspection["metadata"].downloaded_by,
            "organization": inspection["metadata"].organization,
            "asset_code": inspection["metadata"].asset_code,
            "location": inspection["metadata"].location,
            "sha256": inspection["sha256"],
            "parser_version": inspection["parser_version"],
        })

    with st.expander("Detected column mapping"):
        st.write(inspection["headers"])

    if st.button("Import UPS → Supabase → Validate → Calculate KPI", type="primary", width="stretch"):
        settings = load_settings()
        has_supabase = bool(settings.supabase_url and settings.supabase_key)
        demo_mode = st.session_state.get("demo_mode_active", True)

        if has_supabase and not demo_mode:
            try:
                from supabase import create_client
                db = create_client(settings.supabase_url, settings.supabase_key)
                result = ImportPipeline(db, settings, service).run(
                    str(path), uploaded_by=st.session_state.get("user", "admin@srtpl.com")
                )
                if result.get("status") != "IMPORTED":
                    st.warning(result)
                    return
                batch_id = result["import_batch_id"]
                norm_res = NormalizationPersistence(db, calculation_version="5.7.0").process_batch(batch_id, "UPS")
                kpis = calculate_ups_kpis(db, batch_id, "5.7.0")

                st.success(f"UPS production pipeline completed. Batch: {batch_id}")
                st.subheader("UPS KPI Results")
                for row in kpis.get("results", []):
                    val = row["value"]
                    st.metric(row["kpi_code"], "NULL" if val is None else f"{float(val):,.4f}", row.get("unit", ""))
            except Exception as exc:
                st.error(f"Production database ingestion failed: {exc}")
        else:
            with st.spinner("Processing local validation rules and KPI calculation..."):
                sim_res = run_local_ingestion_simulation(path, expected_type="UPS")

            st.success("⚡ Ingestion and calculation verified locally (Supabase bypass / demo mode active).")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Batch ID", f"LOCAL-{sim_res['sha256'][:8]}")
            m2.metric("Total Records", f"{sim_res['record_count']:,}")
            m3.metric("Valid Readings", f"{sim_res['valid_rows']:,}")
            m4.metric("Exceptions Excluded", f"{sim_res['exception_rows']:,}")

            st.subheader("UPS Power Continuity & Telemetry KPIs")
            cols = st.columns(min(len(sim_res["kpis"]), 4))
            for idx, kpi in enumerate(sim_res["kpis"]):
                col = cols[idx % len(cols)]
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
                    "source_type": "UPS",
                    "calculation_version": sim_res["calculation_version"],
                    "source_reading_count": sim_res["valid_rows"],
                    "exception_count": sim_res["exception_rows"],
                    "sha256": sim_res["sha256"],
                })


if __name__ == "__main__":
    render()
