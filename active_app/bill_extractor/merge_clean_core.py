import pandas as pd


def merge_and_clean_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    merge_keys=("Consumer ID", "Consumer A/c No.", "Bill Month")
) -> pd.DataFrame:
    """
    Merge and clean two energy-bill DataFrames.

    - Preserves Bill Number as TEXT
    - Removes blank rows / columns
    - Removes Source-PDF-only junk rows
    - Resolves duplicate columns safely

    Returns: cleaned merged DataFrame
    """

    # ---------- STANDARDIZE COLUMN NAMES ----------
    df1 = df1.copy()
    df2 = df2.copy()

    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    # ---------- FORCE BILL NUMBER AS TEXT ----------
    if "Bill Number" in df1.columns:
        df1["Bill Number"] = df1["Bill Number"].astype(str)
    if "Bill Number" in df2.columns:
        df2["Bill Number"] = df2["Bill Number"].astype(str)

    # ---------- ENSURE MERGE KEYS EXIST ----------
    for key in merge_keys:
        if key not in df1.columns or key not in df2.columns:
            raise ValueError(f"Merge key missing: {key}")

    # ---------- MERGE ----------
    merged = pd.merge(
        df1,
        df2,
        on=list(merge_keys),
        how="outer",
        suffixes=("_x", "_y")
    )

    # ---------- RESOLVE DUPLICATE COLUMNS ----------
    for col in list(merged.columns):
        if col.endswith("_x"):
            base_col = col[:-2]
            col_y = base_col + "_y"

            if col_y in merged.columns:
                merged[base_col] = merged[col].combine_first(merged[col_y])
                merged.drop([col, col_y], axis=1, inplace=True)

    # ---------- REMOVE FULLY BLANK ROWS ----------
    merged.dropna(how="all", inplace=True)

    # ---------- REMOVE FULLY BLANK COLUMNS ----------
    merged.dropna(axis=1, how="all", inplace=True)

    # ---------- REMOVE PARTIALLY FILLED JUNK ROWS ----------
    non_key_cols = [c for c in merged.columns if c not in merge_keys]
    if non_key_cols:
        merged = merged.dropna(subset=non_key_cols, how="all")

    # ---------- REMOVE SOURCE-PDF-ONLY + NAN-KEY ROWS ----------
    if "Source PDF" in merged.columns:
        merged = merged[
            ~(
                merged[list(merge_keys)].isna().all(axis=1)
                & merged.drop(columns=["Source PDF"]).isna().all(axis=1)
            )
        ]

    # ---------- SORT & RESET ----------
    merged.sort_values(list(merge_keys), inplace=True, na_position="last")
    merged.reset_index(drop=True, inplace=True)

    return merged
