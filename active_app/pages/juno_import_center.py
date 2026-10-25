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
from core.live_pipeline import execute_live_juno_ingestion


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
        "Strict Level 1 (SHA-256) and Level 2 (asset_id, datetime) deduplication enforced. "
        "Clean valid records inject directly into Supabase while exceptions are logged to energy_validation.exception_record."
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

    if st.button(f"🚀 Ingest {rtype} → Supabase → Validate Rules → Calculate Master KPIs", type="primary", width="stretch"):
        with st.spinner(f"Processing unified master pipeline for {rtype}: Deduplication → Validation → Supabase Injection..."):
            res = execute_live_juno_ingestion(
                temp_path,
                expected_type=rtype,
                uploaded_by=st.session_state.get("user", "admin@srtpl.com"),
            )

        if res.get("status") == "DUPLICATE_FILE":
            st.error(res["message"])
            if is_temp:
                temp_path.unlink(missing_ok=True)
            return

        if not res.get("success"):
            st.error(res.get("message", "Master pipeline execution failed."))
            if is_temp:
                temp_path.unlink(missing_ok=True)
            return

        if res.get("cloud_injected"):
            st.success(
                f"✅ **Master Ingestion Complete!** {res['valid_rows']} clean readings injected into Supabase "
                f"(`energy_readings.{rtype.lower()}`). Linked Asset: `{res['asset_id']}`"
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
                "source_type": rtype,
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
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    render()
