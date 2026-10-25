from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from import_engine.service import ImportService
from energy_validation.normalizer import NormalizationEngine
from analytics.eb_phase5_4 import calculate_eb_kpis_from_normalized
from analytics.dg_phase5_3 import calculate_dg_kpis_from_normalized
from analytics.solar_phase5_5 import calculate_solar_kpis_from_normalized
from analytics.transformer_phase5_6 import calculate_transformer_kpis_from_normalized
from analytics.ups_phase5_7 import calculate_ups_kpis_from_normalized

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "source_data" / "raw"

SOURCE_FOLDERS = {
    "EB": "EB",
    "DG": "DG",
    "SOLAR": "Solar",
    "Solar": "Solar",
    "TRANSFORMER": "Transformer",
    "Transformer": "Transformer",
    "UPS": "UPS",
}

CALCULATORS = {
    "EB": (calculate_eb_kpis_from_normalized, "5.4.0"),
    "DG": (calculate_dg_kpis_from_normalized, "5.3.1"),
    "SOLAR": (calculate_solar_kpis_from_normalized, "5.5.0"),
    "TRANSFORMER": (calculate_transformer_kpis_from_normalized, "5.6.0"),
    "UPS": (calculate_ups_kpis_from_normalized, "5.7.0"),
}


def list_sample_files(category: str | None = None) -> list[dict[str, Any]]:
    """List available real JUNO CSV sample files from the project repository."""
    results = []
    if category:
        folder_name = SOURCE_FOLDERS.get(category, category)
        target_dirs = [RAW_DATA_DIR / folder_name]
    else:
        target_dirs = [RAW_DATA_DIR / f for f in ["EB", "DG", "Solar", "Transformer", "UPS"]]

    for d in target_dirs:
        if not d.exists():
            continue
        cat_name = d.name
        for p in sorted(d.glob("*.csv")):
            results.append({
                "category": cat_name,
                "filename": p.name,
                "path": str(p),
                "size_bytes": p.stat().st_size,
                "label": f"[{cat_name}] {p.name} ({p.stat().st_size // 1024} KB)",
            })
    return results


def run_local_ingestion_simulation(file_path: str | Path, expected_type: str | None = None) -> dict[str, Any]:
    """Execute complete end-to-end local parsing, validation rules and KPI calculations without requiring Supabase."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    service = ImportService()
    engine = NormalizationEngine()

    inspection = service.inspect(str(p))
    rtype = inspection["report_type"]

    if expected_type and rtype.upper() != expected_type.upper():
        raise ValueError(
            f"File detected as '{rtype}', but '{expected_type}' was expected for this ingestion portal."
        )

    norm_records = []
    all_issues = []
    exception_details = []
    prev = None

    for rec in inspection["records"]:
        cur = dict(rec.values)
        norm, issues = engine.process(rtype, cur, prev)
        norm_records.append(norm)
        all_issues.extend(issues)
        if issues:
            for issue in issues:
                exception_details.append({
                    "row_number": rec.source_row_number,
                    "timestamp": cur.get("reading_datetime") or "—",
                    "rule_code": issue.rule_code,
                    "severity": issue.severity,
                    "message": issue.message,
                    "offending_value": str(issue.source_value) if issue.source_value is not None else "—",
                    "expected_value": str(issue.expected_value) if issue.expected_value is not None else "—",
                    "raw_values": cur,
                    "previous_values": prev or {},
                })
        prev = cur

    if rtype not in CALCULATORS:
        raise ValueError(f"No KPI calculator registered for report type: {rtype}")

    calc_func, calc_version = CALCULATORS[rtype]
    kpi_result = calc_func(norm_records, batch_id=f"LOCAL-{inspection['sha256'][:8]}")

    # Build preview dataframe (up to first 100 rows)
    preview_df = pd.DataFrame(norm_records[:100])

    return {
        "status": "SIMULATED_LOCAL",
        "report_type": rtype,
        "calculation_version": calc_version,
        "filename": p.name,
        "sha256": inspection["sha256"],
        "metadata": inspection["metadata"],
        "headers": inspection["headers"],
        "record_count": len(inspection["records"]),
        "valid_rows": kpi_result.get("valid_source_rows", len(inspection["records"])),
        "exception_rows": kpi_result.get("exception_rows_excluded", 0),
        "kpis": kpi_result.get("results", []),
        "issues": all_issues,
        "exception_details": exception_details,
        "trace": kpi_result,
        "preview_df": preview_df,
    }
