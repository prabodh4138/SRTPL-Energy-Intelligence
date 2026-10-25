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
from core.live_pipeline import execute_live_juno_ingestion


def _save_uploaded(uploaded) -> Path:
    fd, name = tempfile.mkstemp(prefix="srtpl_trf_", suffix=".csv")
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
    st.title("Transformer — JUNO Import → Validation → KPI")
    st.caption(
        "Substation transformer health, voltage/current imbalance, and winding/oil temperatures. "
        "Strict Level 1 (SHA-256) and Level 2 (asset_id, datetime) deduplication enforced. "
        "Clean valid records inject directly into Supabase (`energy_readings.transformer`) while exceptions are logged to energy_validation.exception_record."
    )

    st.warning(
        "⚠️ **Mandatory Engineering Policy**: Transformer loss and efficiency calculations remain "
        "**disabled** until formal sign-off of measurement boundaries, ratings, and meter semantics."
    )

    sample_files = list_sample_files("Transformer")
    sample_options = {s["label"]: s["path"] for s in sample_files}

    uploaded = st.file_uploader(
        "Upload original JUNO Transformer CSV",
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
        st.info("💡 Upload an untouched JUNO Transformer CSV above, or select from sample files below:")
        st.subheader("Repository Sample Transformer Files")
        selected_sample_label = st.selectbox(
            "Select sample file to inspect and process:",
            list(sample_options.keys()),
            index=0 if sample_options else None,
        )
        if st.button("📂 Load Selected Sample CSV", type="secondary", width="stretch"):
            st.session_state["trf_selected_sample"] = sample_options[selected_sample_label]

        active_sample = st.session_state.get("trf_selected_sample")
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
        st.error(f"Transformer CSV inspection failed: {exc}")
        if is_temp:
            _safe_unlink(path)
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Detected type", inspection["report_type"])
    c2.metric("Parsed rows", f'{inspection["record_count"]:,}')
    c3.metric("Transformer", inspection["metadata"].asset_code or "—")
    c4.metric("File size", f"{file_size:,} bytes")

    if inspection["report_type"] != "TRANSFORMER":
        st.error("This file was not detected as a Transformer JUNO report. Import is blocked.")
        if is_temp:
            _safe_unlink(path)
        return

    st.success("Transformer JUNO structure detected. Ready for controlled ingestion.")

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

    if st.button("🚀 Ingest Transformer → Supabase → Validate → Calculate KPI", type="primary", width="stretch"):
        with st.spinner("Processing pipeline: Deduplication → Validation → Supabase Injection → Master KPIs..."):
            res = execute_live_juno_ingestion(
                path,
                expected_type="TRANSFORMER",
                uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
            )

        if res.get("status") == "DUPLICATE_FILE":
            st.error(res["message"])
            col_clear, col_wipe = st.columns(2)
            if col_clear.button("🔄 Clear Ingestion Session Cache & Retry", key="clear_dup_trf", width="stretch"):
                from core.live_pipeline import clear_local_ingestion_hashes
                clear_local_ingestion_hashes()
                st.rerun()
            if col_wipe.button("🗑️ Wipe All Database Data (Clean Start)", key="wipe_dup_trf", width="stretch"):
                from core.supabase_manager import remove_all_database_data
                wipe_res = remove_all_database_data()
                st.success(wipe_res["message"])
                st.rerun()
            if is_temp:
                _safe_unlink(path)
            return

        if not res.get("success"):
            st.error(res.get("message", "Pipeline execution failed."))
            if is_temp:
                _safe_unlink(path)
            return

        if res.get("cloud_injected"):
            st.success(
                f"✅ **Transformer Pipeline Complete!** Clean readings successfully injected into Supabase "
                f"(`energy_readings.transformer`). Linked Asset: `{res['asset_id']}`"
            )
        elif res.get("cloud_error"):
            st.warning(
                f"⚠️ **Supabase Cloud Notice**: Database reported: `{res['cloud_error']}`.\n\n"
                "💡 **Fix PGRST002**: Run `NOTIFY pgrst, 'reload schema';` in Supabase SQL Editor to reload the schema cache."
            )
        else:
            st.info(
                f"⚡ **Transformer Pipeline Verified!** Running in local mode (Asset: `{res['asset_id']}`). "
                "Supabase cloud persistence active when credentials are provided in secrets or .env."
            )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Batch ID", f"LIVE-{res['sha256'][:8]}")
        m2.metric("Total Records", f"{res['total_records']:,}")
        m3.metric("Valid Readings Injected", f"{res['valid_rows']:,}")
        m4.metric("Exceptions Excluded", f"{res['exception_rows']:,}")

        st.subheader("Transformer KPI Results")
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
                "source_type": "TRANSFORMER",
                "asset_id": res["asset_id"],
                "asset_code": res["asset_code"],
                "calculation_version": res["calculation_version"],
                "total_records": res["total_records"],
                "valid_rows": res["valid_rows"],
                "exception_rows": res["exception_rows"],
                "sha256": res["sha256"],
                "cloud_injected": res.get("cloud_injected", False),
            })

    if is_temp:
        _safe_unlink(path)


if __name__ == "__main__":
    render()
