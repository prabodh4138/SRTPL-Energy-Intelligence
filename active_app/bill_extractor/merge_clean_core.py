from typing import Any
import re
import pandas as pd


REQUIRED_EXTRACTION_FIELDS = [
    "Security Deposit",
    "MD",
    "Contract Demand",
    "Section",
    "Sub-Division",
    "Rebate Date",
    "CUML MD-KVA",
    "CUML MD-KW",
    "DPS(Rs.)",
    "Tariff Category",
    "Meter Sl. No.",
    "Net Payable Amount Before Rbt. Dt.(Rs.)",
    "Net Payable Amount After Rbt. Dt.(Rs.)",
]


FIELD_SYNONYM_MAP = {
    "security_deposit": ["Security Deposit", "security_deposit"],
    "md": ["MD", "md", "MD-KW", "MD-KVA"],
    "contract_demand": ["Contract Demand", "contract_demand"],
    "section": ["Section", "section"],
    "sub_division": ["Sub-Division", "sub_division", "Sub Division"],
    "division": ["Division", "division", "division_name"],
    "rebate_date": ["Rebate Date", "rebate_date"],
    "cuml_md_kva": ["CUML MD-KVA", "cuml_md_kva"],
    "cuml_md_kw": ["CUML MD-KW", "cuml_md_kw"],
    "dps_rs": ["DPS(Rs.)", "DPS (Rs.)", "dps_rs", "DPS"],
    "tariff_category": ["Tariff Category", "tariff_category", "tariff_type"],
    "meter_sl_no": ["Meter Sl. No.", "meter_sl_no", "Meter Serial No"],
    "net_payable_amount_before_rbt_dt_rs": [
        "Net Payable Amount Before Rbt. Dt.(Rs.)", "net_payable_amount_before_rbt_dt_rs", "net_before_rebate"
    ],
    "net_payable_amount_after_rbt_dt_rs": [
        "Net Payable Amount After Rbt. Dt.(Rs.)", "net_payable_amount_after_rbt_dt_rs", "net_after_rebate"
    ],
}


def enrich_bill_record(row: dict[str, Any]) -> dict[str, Any]:
    """Enriches bill record with authoritative bill_type (HT/LT), consumer_scope (PLAZA/HIGHWAY),
    and parsed sanctioned_load_kw directly from contract demand, master accounts, and tariff classification.
    Synchronizes both Title Case and snake_case keys for all 13 required fields.
    """
    # 0. Sync synonyms across all known fields first
    for canon, syns in FIELD_SYNONYM_MAP.items():
        found_val = None
        for s in syns:
            if s in row and row[s] is not None and str(row[s]).strip() not in ("", "—", "nan", "None"):
                found_val = row[s]
                break
        if found_val is not None:
            for s in syns:
                row[s] = found_val

    ac = str(row.get("Consumer A/c No.") or row.get("consumer_account_no") or "").strip()
    tariff = str(row.get("Tariff Category") or row.get("tariff_category") or "").strip().upper()
    cd_raw = str(row.get("Contract Demand") or row.get("contract_demand") or "").strip()

    # Look up authoritative master consumer account
    master_acc: dict[str, Any] = {}
    try:
        from core.db_sync import DEFAULT_CONSUMER_ACCOUNTS
        for a in DEFAULT_CONSUMER_ACCOUNTS:
            if str(a.get("consumer_account_no", "")).strip() == ac:
                master_acc = a
                break
    except Exception:
        master_acc = {}

    # 1. Determine bill_type (Exactly 3 HT accounts for the 3 Toll Plazas; remaining 57 are LT)
    is_ht = False
    if master_acc.get("bill_type") == "HT":
        is_ht = True
    elif ac in {"416000000110", "813000000281", "812001020208"}:
        is_ht = True
    elif bool(re.search(r'\b(HT|HIGH TENSION|EHT|LARGE INDUSTRY)\b', tariff)) or bool(re.search(r'>=?\s*110', tariff)) or bool(re.search(r'>\s*70', tariff)):
        is_ht = True
    elif "KVA" in cd_raw.upper():
        cd_nums = re.findall(r"(\d+(?:\.\d+)?)", cd_raw)
        if cd_nums and float(cd_nums[0]) >= 70.0:
            is_ht = True
    elif str(row.get("bill_type", "")).strip().upper() == "HT" or str(row.get("Bill Type", "")).strip().upper() == "HT":
        is_ht = True

    b_type = "HT" if is_ht else "LT"

    # 2. Determine consumer_scope: PLAZA for 3 Plaza HT connections, HIGHWAY for corridor lighting
    if master_acc.get("consumer_scope"):
        scope = master_acc["consumer_scope"].upper()
    else:
        is_plaza = is_ht or ac in {"416000000110", "813000000281", "812001020208"} or str(row.get("consumer_scope", "")).strip().upper() in ["PLAZA", "TOLL_PLAZA"]
        scope = "PLAZA" if is_plaza else "HIGHWAY"

    # 3. Determine sanctioned_load_kw: Parsed directly from Contract Demand or Master Account
    load_val = None
    cd_nums = re.findall(r"(\d+(?:\.\d+)?)", cd_raw)
    if cd_nums:
        try:
            load_val = float(cd_nums[0])
        except (ValueError, TypeError):
            pass
    if load_val is None or load_val <= 0.0:
        if master_acc.get("sanctioned_load_kw") is not None:
            try:
                load_val = float(master_acc["sanctioned_load_kw"])
            except (ValueError, TypeError):
                pass
    if load_val is None or load_val <= 0.0:
        raw_load = row.get("sanctioned_load_kw") or row.get("Sanctioned Load (KW)") or row.get("md_kw") or row.get("MD-KW")
        if raw_load is not None:
            try:
                load_val = float(raw_load)
            except (ValueError, TypeError):
                pass
    if load_val is None or load_val <= 0.0:
        load_val = 120.0 if is_ht else 10.0

    row["bill_type"] = b_type
    row["Bill Type"] = b_type
    row["consumer_scope"] = scope
    row["Consumer Scope"] = scope
    row["sanctioned_load_kw"] = load_val
    row["Sanctioned Load (KW)"] = load_val

    # Ensure Contract Demand is reflected in both styles
    if not cd_raw or cd_raw in ["—", "None", "nan"]:
        cd_raw = f"{load_val:.0f} KVA" if is_ht else f"{load_val:.0f} KW"
    row["Contract Demand"] = cd_raw
    row["contract_demand"] = cd_raw

    # Carry forward master account details if not present in bill
    if master_acc:
        if not row.get("toll_plaza_id") and master_acc.get("toll_plaza_id"):
            row["toll_plaza_id"] = master_acc["toll_plaza_id"]
        if not row.get("Division") and not row.get("division") and master_acc.get("division_name"):
            row["Division"] = master_acc["division_name"]
            row["division"] = master_acc["division_name"]
            row["division_name"] = master_acc["division_name"]
        if not row.get("asset_code") and master_acc.get("asset_code"):
            row["asset_code"] = master_acc["asset_code"]
        if not row.get("location") and master_acc.get("location"):
            row["location"] = master_acc["location"]

    # Ensure all 13 requested fields are present in both casing formats
    for fld in REQUIRED_EXTRACTION_FIELDS:
        if fld not in row or row[fld] is None:
            row[fld] = ""

    for canon, syns in FIELD_SYNONYM_MAP.items():
        found_val = None
        for s in syns:
            if s in row and row[s] is not None and str(row[s]).strip() not in ("", "—", "nan", "None"):
                found_val = row[s]
                break
        if found_val is not None:
            for s in syns:
                row[s] = found_val

    return row


def merge_and_clean_dataframes(
    df1: pd.DataFrame | dict | list[dict],
    df2: pd.DataFrame | dict | list[dict],
    merge_keys=("Consumer ID", "Consumer A/c No.", "Bill Month"),
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Merge and clean two energy-bill DataFrames or dictionaries.

    - Accepts pd.DataFrame, dict, or list[dict]
    - Accepts optional kwargs (e.g. filename, raw_bytes) without error
    - Preserves Bill Number as TEXT
    - Removes blank rows / columns
    - Removes Source-PDF-only junk rows
    - Resolves duplicate columns safely
    - Automatically falls back if individual merge keys are absent

    Returns: cleaned merged DataFrame
    """
    # ---------- CONVERT INPUTS TO DATAFRAME ----------
    if isinstance(df1, dict):
        df1 = pd.DataFrame([df1])
    elif isinstance(df1, list):
        df1 = pd.DataFrame(df1)
    elif not isinstance(df1, pd.DataFrame):
        df1 = pd.DataFrame(df1)

    if isinstance(df2, dict):
        df2 = pd.DataFrame([df2])
    elif isinstance(df2, list):
        df2 = pd.DataFrame(df2)
    elif not isinstance(df2, pd.DataFrame):
        df2 = pd.DataFrame(df2)

    if df1.empty and df2.empty:
        return pd.DataFrame()
    if df1.empty:
        return df2.copy()
    if df2.empty:
        return df1.copy()

    # ---------- STANDARDIZE COLUMN NAMES ----------
    df1 = df1.copy()
    df2 = df2.copy()

    df1.columns = [str(c).strip() for c in df1.columns]
    df2.columns = [str(c).strip() for c in df2.columns]

    # ---------- FORCE BILL NUMBER AS TEXT ----------
    if "Bill Number" in df1.columns:
        df1["Bill Number"] = df1["Bill Number"].astype(str)
    if "Bill Number" in df2.columns:
        df2["Bill Number"] = df2["Bill Number"].astype(str)

    # ---------- DYNAMIC MERGE KEYS ----------
    actual_keys = [k for k in merge_keys if k in df1.columns and k in df2.columns]

    # ---------- MERGE ----------
    if actual_keys:
        merged = pd.merge(
            df1,
            df2,
            on=actual_keys,
            how="outer",
            suffixes=("_x", "_y")
        )
    else:
        # Fallback to horizontal concat if no common keys exist
        merged = pd.concat([df1.reset_index(drop=True), df2.reset_index(drop=True)], axis=1)

    # ---------- RESOLVE DUPLICATE COLUMNS ----------
    for col in list(merged.columns):
        if col not in merged.columns:
            continue
        if col.endswith("_x"):
            base_col = col[:-2]
            col_y = base_col + "_y"

            if col_y in merged.columns:
                s_x = merged[col].astype(object).replace(r"^\s*$", None, regex=True)
                s_y = merged[col_y].astype(object).replace(r"^\s*$", None, regex=True)
                merged[base_col] = s_x.combine_first(s_y).fillna("")
                merged.drop([col, col_y], axis=1, inplace=True, errors="ignore")
            else:
                merged[base_col] = merged[col]
                merged.drop(columns=[col], inplace=True, errors="ignore")
        elif col.endswith("_y"):
            base_col = col[:-2]
            merged[base_col] = merged[col]
            merged.drop(columns=[col], inplace=True, errors="ignore")

    # Drop any duplicate column names after merge
    merged = merged.loc[:, ~merged.columns.duplicated()]

    # ---------- REMOVE FULLY BLANK ROWS ----------
    merged.dropna(how="all", inplace=True)

    # ---------- REMOVE FULLY BLANK COLUMNS ----------
    merged.dropna(axis=1, how="all", inplace=True)

    # ---------- REMOVE PARTIALLY FILLED JUNK ROWS ----------
    non_key_cols = [c for c in merged.columns if c not in merge_keys and c not in ["Source PDF", "raw_text"]]
    if non_key_cols:
        merged = merged.dropna(subset=non_key_cols, how="all")

    # ---------- ASSIGN SOURCE PDF IF PROVIDED ----------
    fname = kwargs.get("filename") or kwargs.get("source_name")
    if fname:
        if "Source PDF" not in merged.columns or merged["Source PDF"].isna().all():
            merged["Source PDF"] = fname

    # ---------- REMOVE SOURCE-PDF-ONLY + NAN-KEY ROWS ----------
    if "Source PDF" in merged.columns and actual_keys:
        merged = merged[
            ~(
                merged[actual_keys].isna().all(axis=1)
                & merged.drop(columns=["Source PDF", "raw_text"], errors="ignore").isna().all(axis=1)
            )
        ]

    # ---------- ENRICH & GUARANTEE REQUIRED 13 FIELDS ----------
    if not merged.empty:
        records = [enrich_bill_record(dict(r)) for r in merged.to_dict(orient="records")]
        merged = pd.DataFrame(records)

    # ---------- SORT & RESET ----------
    sort_cols = [k for k in merge_keys if k in merged.columns]
    if sort_cols:
        merged.sort_values(sort_cols, inplace=True, na_position="last")
    merged.reset_index(drop=True, inplace=True)

    return merged
