"""
SRTPL Power Project - Automated Bill & Receipt Extraction Engine
Extracts 14 core tariff/meter/jurisdiction fields + bill totals + receipt records.
Provides mathematical audit verification for Energy Charges, Electricity Charges, and Current Totals.
Supports in-memory ZIP unpacking for batch processing.
"""
from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.extractor_md_full import extract_md_bill_data
from bill_extractor.extractor_receipt_full import extract_energy_receipt_data
from bill_extractor.merge_clean_core import merge_and_clean_dataframes
from bill_extractor.verifier import verify_bill_calculations
from bill_extractor.zip_handler import extract_pdfs_from_inputs, NamedBytesIO
from bill_extractor.ai_model_router import classify_bill_format, compute_derived_sbm_slabs, MODEL_CATALOG

__all__ = [
    "extract_energy_bill_full",
    "extract_md_bill_data",
    "extract_energy_receipt_data",
    "merge_and_clean_dataframes",
    "verify_bill_calculations",
    "extract_pdfs_from_inputs",
    "NamedBytesIO",
    "classify_bill_format",
    "compute_derived_sbm_slabs",
    "MODEL_CATALOG",
]
