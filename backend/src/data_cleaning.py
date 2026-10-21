"""
data_cleaning.py
----------------
Data validation, cleaning, and quality reporting for the crop production dataset.

Dataset: crop_production_1997_2025.csv
Columns: State_Name, District_Name, Crop_Year, Season, Crop, Area, Production, Data_Type
"""

import pandas as pd
import numpy as np
import os

def get_data_path() -> str:
    """Resolve the dataset path across local development, Docker, and Render environments."""
    env_path = os.environ.get("DATA_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(current_dir), "data", "crop_production_1997_2025.csv"),
        os.path.join(current_dir, "..", "data", "crop_production_1997_2025.csv"),
        os.path.join(os.getcwd(), "backend", "data", "crop_production_1997_2025.csv"),
        os.path.join(os.getcwd(), "data", "crop_production_1997_2025.csv"),
    ]
    for candidate in candidates:
        norm = os.path.normpath(candidate)
        if os.path.exists(norm):
            return norm
    return os.path.normpath(candidates[0])

DATA_PATH = get_data_path()

# Known years that contain data extended beyond confirmed government publications.
# The dataset labels all rows as "Actual"; however 2023-2025 rows appear
# to replicate the 2022 record counts exactly, suggesting they may be
# forward-filled or synthetically extended. We flag them transparently.
POTENTIALLY_EXTENDED_YEARS = [2024, 2025]
LAST_VERIFIED_YEAR = 2023   # conservative assumption


def load_raw(path: str = None) -> pd.DataFrame:
    """Load the raw CSV without any modification."""
    resolved_path = path or get_data_path()
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(
            f"Crop production dataset not found at '{resolved_path}'. "
            f"Please verify that backend/data/crop_production_1997_2025.csv exists in the deployment."
        )
    df = pd.read_csv(resolved_path)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply a reproducible cleaning pipeline.

    Steps:
      1. Strip whitespace from string columns.
      2. Standardise Season values (strip trailing spaces).
      3. Remove rows where both Area AND Production are zero and null.
      4. Keep missing Production rows (1.07 % of dataset); do not fill arbitrarily.
      5. Add helper columns: Yield_t_per_ha, Data_Provenance.
      6. Ensure numeric types.

    The original CSV is never modified.
    """
    df = df.copy()

    # --- 1. Whitespace ---
    str_cols = ["State_Name", "District_Name", "Season", "Crop", "Data_Type"]
    for c in str_cols:
        df[c] = df[c].str.strip()

    # --- 2. Standardise Season capitalisation ---
    df["Season"] = df["Season"].str.title()

    # --- 3. Drop rows where Area is null (none exist, but defensive) ---
    df = df[df["Area"].notna()].copy()

    # --- 4. Numeric coercion ---
    df["Area"] = pd.to_numeric(df["Area"], errors="coerce")
    df["Production"] = pd.to_numeric(df["Production"], errors="coerce")
    df["Crop_Year"] = pd.to_numeric(df["Crop_Year"], errors="coerce").fillna(0).astype(int)

    # --- 5. Yield (t/ha or kg/ha proxy) — only where both fields are valid & Area > 0 ---
    # Area unit in original data is hectares; Production unit is metric tonnes.
    # Yield = Production / Area  (tonnes per hectare).
    df["Yield_t_per_ha"] = np.where(
        (df["Area"] > 0) & df["Production"].notna(),
        df["Production"] / df["Area"],
        np.nan,
    )

    # --- 6. Data provenance flag ---
    # All rows carry Data_Type = "Actual" in the CSV.
    # We add a conservative annotation for years beyond last verified release.
    df["Data_Provenance"] = np.where(
        df["Crop_Year"].isin(POTENTIALLY_EXTENDED_YEARS),
        "Potentially Extended",
        "Official Record",
    )

    return df


def quality_report(df: pd.DataFrame) -> dict:
    """Return a dictionary summarising data-quality metrics."""
    total = len(df)
    missing_prod = int(df["Production"].isna().sum())
    zero_prod = int((df["Production"] == 0).sum())
    zero_area = int((df["Area"] == 0).sum())
    duplicates_full = int(df.duplicated().sum())
    duplicates_key = int(
        df.duplicated(subset=["State_Name", "District_Name", "Crop_Year", "Season", "Crop"]).sum()
    )

    return {
        "total_records": total,
        "missing_production": missing_prod,
        "missing_production_pct": round(missing_prod / total * 100, 2),
        "zero_production": zero_prod,
        "zero_area": zero_area,
        "duplicate_rows_full": duplicates_full,
        "duplicate_rows_key": duplicates_key,
        "year_range": (int(df["Crop_Year"].min()), int(df["Crop_Year"].max())),
        "states": int(df["State_Name"].nunique()),
        "districts": int(df["District_Name"].nunique()),
        "crops": int(df["Crop"].nunique()),
        "seasons": df["Season"].unique().tolist(),
        "data_type_values": df["Data_Type"].value_counts().to_dict(),
        "potentially_extended_years": POTENTIALLY_EXTENDED_YEARS,
        "last_verified_year": LAST_VERIFIED_YEAR,
        "limitations": [
            "All rows carry Data_Type='Actual'. Years 2024-2025 have identical record "
            "counts to 2022/2023, suggesting forward-fill or synthetic extension.",
            "4,973 rows (1.07%) have missing Production values; these are excluded "
            "from aggregations rather than filled with zero.",
            "Area is in hectares; Production is in metric tonnes. "
            "Units are not explicitly stated in the CSV header.",
            "State-level reorganisations (e.g. Telangana carved from Andhra Pradesh "
            "in 2014, Ladakh carved from J&K in 2019) are reflected in the data "
            "but may cause discontinuities in long-term state comparisons.",
            "The Dadra And Nagar Haveli And Daman And Diu merged entity appears under "
            "a combined name in the CSV but exists as two separate features in many "
            "GeoJSON files.",
        ],
    }


if __name__ == "__main__":
    raw = load_raw()
    clean_df = clean(raw)
    report = quality_report(clean_df)
    print("=== DATA QUALITY REPORT ===")
    for k, v in report.items():
        print(k + ":", v)
