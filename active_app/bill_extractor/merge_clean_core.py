from typing import Any
import pandas as pd


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
                merged[base_col] = merged[col].combine_first(merged[col_y])
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

    # ---------- SORT & RESET ----------
    sort_cols = [k for k in merge_keys if k in merged.columns]
    if sort_cols:
        merged.sort_values(sort_cols, inplace=True, na_position="last")
    merged.reset_index(drop=True, inplace=True)

    return merged
