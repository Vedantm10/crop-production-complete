"""
map_utils.py
------------
State-name normalisation mapping and GeoJSON loading for the India choropleth map.

GeoJSON source: https://github.com/geohacker/india (NAME_1 property)
Dataset state names are normalised to match GeoJSON names exactly.
"""

import json
import os
import pandas as pd

def get_geojson_path() -> str:
    """Resolve the India states GeoJSON path across local, Docker, and Render environments."""
    env_path = os.environ.get("GEOJSON_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(current_dir), "assets", "india_states.geojson"),
        os.path.join(current_dir, "..", "assets", "india_states.geojson"),
        os.path.join(os.getcwd(), "backend", "assets", "india_states.geojson"),
        os.path.join(os.getcwd(), "assets", "india_states.geojson"),
        os.path.join(os.getcwd(), "frontend", "public", "geo", "india_states.geojson"),
    ]
    for candidate in candidates:
        norm = os.path.normpath(candidate)
        if os.path.exists(norm):
            return norm
    return os.path.normpath(candidates[0])

GEOJSON_PATH = get_geojson_path()

# Mapping: CSV State_Name -> GeoJSON NAME_1
# States not present in the GeoJSON are noted in UNMATCHED_STATES.
CSV_TO_GEOJSON: dict = {
    "Andaman And Nicobar Islands": "Andaman and Nicobar",
    "Andhra Pradesh": "Andhra Pradesh",
    "Arunachal Pradesh": "Arunachal Pradesh",
    "Assam": "Assam",
    "Bihar": "Bihar",
    "Chandigarh": "Chandigarh",
    "Chhattisgarh": "Chhattisgarh",
    "Goa": "Goa",
    "Gujarat": "Gujarat",
    "Haryana": "Haryana",
    "Himachal Pradesh": "Himachal Pradesh",
    "Jammu And Kashmir": "Jammu and Kashmir",
    "Jharkhand": "Jharkhand",
    "Karnataka": "Karnataka",
    "Kerala": "Kerala",
    "Ladakh": "Jammu and Kashmir",          # Ladakh carved from J&K 2019; mapped to J&K geometry
    "Madhya Pradesh": "Madhya Pradesh",
    "Maharashtra": "Maharashtra",
    "Manipur": "Manipur",
    "Meghalaya": "Meghalaya",
    "Mizoram": "Mizoram",
    "Nagaland": "Nagaland",
    "Odisha": "Orissa",                     # CSV uses "Odisha"; GeoJSON uses "Orissa"
    "Puducherry": "Puducherry",
    "Punjab": "Punjab",
    "Rajasthan": "Rajasthan",
    "Sikkim": "Sikkim",
    "Tamil Nadu": "Tamil Nadu",
    "Telangana": "Telangana",
    "The Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli",  # partial match
    "Tripura": "Tripura",
    "Uttar Pradesh": "Uttar Pradesh",
    "Uttarakhand": "Uttaranchal",            # CSV uses "Uttarakhand"; GeoJSON uses "Uttaranchal"
    "West Bengal": "West Bengal",
}

# States that cannot be perfectly matched or are absent from the GeoJSON
UNMATCHED_NOTES: dict = {
    "Ladakh": "Shown under Jammu & Kashmir geometry (carved out in 2019, not in GeoJSON).",
    "The Dadra And Nagar Haveli And Daman And Diu": (
        "Merged UT in 2020. GeoJSON has 'Dadra and Nagar Haveli' and 'Daman and Diu' separately. "
        "Mapped to 'Dadra and Nagar Haveli' only."
    ),
    "Uttarakhand": "GeoJSON uses the older name 'Uttaranchal'. Mapped correctly.",
    "Odisha": "GeoJSON uses the older name 'Orissa'. Mapped correctly.",
}


def load_geojson(path: str = GEOJSON_PATH) -> dict:
    """Load the India states GeoJSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalise_state_name(csv_name: str) -> str:
    """Return the GeoJSON NAME_1 corresponding to a CSV State_Name."""
    return CSV_TO_GEOJSON.get(csv_name, csv_name)


def build_state_map_df(
    df: pd.DataFrame,
    metric: str = "Production",
    year: int = None,
    crop: str = None,
    season: str = None,
) -> pd.DataFrame:
    """
    Aggregate the crop DataFrame by state for the given filters and metric.

    Returns a DataFrame with columns:
        geojson_name, State_Name, <metric>, record_count,
        Area_sum, Production_sum, Yield_t_per_ha_mean
    """
    filtered = df.copy()
    if year is not None:
        filtered = filtered[filtered["Crop_Year"] == year]
    if crop and crop != "All Crops":
        filtered = filtered[filtered["Crop"] == crop]
    if season and season != "All Seasons":
        filtered = filtered[filtered["Season"] == season]

    agg = (
        filtered.dropna(subset=["Production"])
        .groupby("State_Name", as_index=False)
        .agg(
            Production_sum=("Production", "sum"),
            Area_sum=("Area", "sum"),
            record_count=("Production", "count"),
        )
    )

    # Derived yield at state level
    agg["Yield_t_per_ha"] = agg.apply(
        lambda r: r["Production_sum"] / r["Area_sum"] if r["Area_sum"] > 0 else None,
        axis=1,
    )

    # Map to GeoJSON name
    agg["geojson_name"] = agg["State_Name"].apply(normalise_state_name)

    return agg
