"""
api.py
======
FastAPI REST backend for the Next.js agricultural analytics frontend.
Reuses the existing src/ analysis functions — no logic is duplicated here.

Start with:
    .venv\\Scripts\\python.exe -m uvicorn api:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
"""

import io
import math
import os
import sys
from contextlib import asynccontextmanager
from typing import Literal, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from data_cleaning import (
    DATA_PATH,
    LAST_VERIFIED_YEAR,
    POTENTIALLY_EXTENDED_YEARS,
    clean,
    load_raw,
    quality_report,
)
from map_utils import CSV_TO_GEOJSON, UNMATCHED_NOTES, build_state_map_df
from pandas_analysis import (
    crop_trend,
    cropwise_production,
    district_production,
    seasonal_production,
    statewise_production,
    top_states_by_production,
    yearwise_by_state,
    yearwise_production,
)

# ── In-memory dataset cache ───────────────────────────────────────────────────
# Loaded once at startup; never reloaded per-request.
_DF: Optional[pd.DataFrame] = None
_DATASET_LOAD_ERROR: Optional[str] = None
_METADATA_CACHE: Optional[dict] = None


def get_df() -> pd.DataFrame:
    """Return the cleaned DataFrame, loading it the first time."""
    global _DF, _DATASET_LOAD_ERROR
    if _DATASET_LOAD_ERROR:
        raise HTTPException(
            status_code=503,
            detail=f"Dataset unavailable due to startup error: {_DATASET_LOAD_ERROR}",
        )
    if _DF is None:
        try:
            _DF = clean(load_raw(DATA_PATH))
            _DF._year_min = int(_DF["Crop_Year"].min()) if not _DF.empty else 1997
            _DF._year_max = int(_DF["Crop_Year"].max()) if not _DF.empty else 2025
        except Exception as e:
            _DATASET_LOAD_ERROR = str(e)
            raise HTTPException(
                status_code=503,
                detail=f"Failed to load dataset: {e}",
            )
    return _DF


# ── Provenance & caveat constants ─────────────────────────────────────────────
_COCONUT_CAVEAT = (
    "Coconut production in this dataset is recorded in NUMBER OF NUTS, not "
    "metric tonnes, unlike every other crop. This inflates totals for Kerala, "
    "Tamil Nadu, Karnataka, and Andhra Pradesh. All-crop production sums are "
    "therefore NOT directly comparable in a single unit."
)

_PROVENANCE_NOTE = (
    f"Years {POTENTIALLY_EXTENDED_YEARS} are labelled 'Actual' in the source "
    f"CSV but share the exact same district/crop combinations as "
    f"{LAST_VERIFIED_YEAR}, with only small sequential value increments. "
    "They appear to be algorithmically extrapolated, not verified government "
    "statistics. Do not cite as official data."
)


# ── JSON serialisation helper ─────────────────────────────────────────────────
def _safe(val):
    """
    Convert one value to a JSON-serialisable Python native type.

    Rules:
    - pandas NA / NaT  → None
    - numpy integer    → int
    - numpy float      → float (NaN/Inf → None)
    - numpy bool       → bool
    - Python float NaN/Inf → None
    - everything else  → unchanged
    """
    # pandas nullable sentinels
    if val is pd.NA or val is pd.NaT:
        return None
    # numpy scalar types
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        f = float(val)
        return None if not math.isfinite(f) else f
    if isinstance(val, np.bool_):
        return bool(val)
    # Python built-in float edge cases
    if isinstance(val, float) and not math.isfinite(val):
        return None
    return val


def _df_to_records(df: pd.DataFrame) -> list:
    """
    Convert a DataFrame to a list of JSON-safe dicts.
    Handles numpy integer/float types, NaN, Inf, and pandas NA.
    """
    rows = []
    for rec in df.to_dict(orient="records"):
        rows.append({k: _safe(v) for k, v in rec.items()})
    return rows


def _make_safe(obj):
    """Recursively make a nested dict/list/scalar JSON-safe."""
    if isinstance(obj, dict):
        return {k: _make_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_safe(v) for v in obj]
    return _safe(obj)


# ── In-memory query result cache ──────────────────────────────────────────────
_CACHE: dict = {}
_CACHE_MAX_SIZE = 512

def _get_cached_query(key: str):
    return _CACHE.get(key)

def _set_cached_query(key: str, val):
    if len(_CACHE) >= _CACHE_MAX_SIZE:
        _CACHE.clear()
    _CACHE[key] = val


# ── Filter helper ─────────────────────────────────────────────────────────────
def _apply_filters(
    df: pd.DataFrame,
    years: Optional[list] = None,
    states: Optional[list] = None,
    crops: Optional[list] = None,
    seasons: Optional[list] = None,
    districts: Optional[list] = None,
    district: Optional[str] = None,
    data_type: Optional[str] = None,
) -> pd.DataFrame:
    """Apply optional dimension filters efficiently. Unknown values silently produce empty DF."""
    if years:
        year_min = getattr(df, "_year_min", 1997)
        year_max = getattr(df, "_year_max", 2025)
        # Skip boolean filter if all dataset years are included
        if not (min(years) <= year_min and max(years) >= year_max and len(years) >= (year_max - year_min + 1)):
            df = df[df["Crop_Year"].isin(years)]
    if states:
        df = df[df["State_Name"].isin(states)]
    district_list = districts or ([district] if district else None)
    if district_list:
        df = df[df["District_Name"].isin(district_list)]
    if crops:
        df = df[df["Crop"].isin(crops)]
    if seasons:
        df = df[df["Season"].isin(seasons)]
    if data_type and data_type != "all":
        df = df[df["Data_Type"] == data_type]
    return df


def _clean_str(val) -> Optional[str]:
    """Return trimmed string if val is a non-empty string, else None."""
    return val.strip() if isinstance(val, str) and val.strip() else None


def _parse_csv_param(raw: Optional[str]) -> Optional[list]:
    """Split a comma-separated query-string value into a list, or return None."""
    if not raw or not isinstance(raw, str):
        return None
    return [v.strip() for v in raw.split(",") if v.strip()]


def _parse_year_list(raw: Optional[str]) -> Optional[list]:
    parts = _parse_csv_param(raw)
    if parts is None:
        return None
    try:
        return [int(p) for p in parts]
    except ValueError:
        raise HTTPException(status_code=422, detail="years must be comma-separated integers.")


# ── App ───────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Pre-load and cache the dataset on server startup."""
    global _DATASET_LOAD_ERROR
    try:
        get_df()
        get_metadata_dict()
    except Exception as e:
        _DATASET_LOAD_ERROR = str(e)
        print(f"[ERROR] Lifespan preloading failed: {e}", file=sys.stderr)
    yield


app = FastAPI(
    title="AgriIntel India — Crop Production Analytics API",
    description=(
        "REST backend for the India crop production dataset (1997–2025). "
        "Source: Government of India district-level crop statistics. "
        f"Data provenance: {_PROVENANCE_NOTE} "
        f"Unit caveat: {_COCONUT_CAVEAT}"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS setup ───────────────────────────────────────────────────────────────
DEFAULT_ALLOWED_ORIGINS = [
    "https://crop-production-complete-kxthfkj9a-vedantmore077-9813.vercel.app",
    "https://crop-production-complete-kd2sxmq5m-vedantmore077-9813.vercel.app",
    "https://crop-production-complete.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_env_origins = os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
for _orig in DEFAULT_ALLOWED_ORIGINS:
    if _orig not in _allowed_origins:
        _allowed_origins.append(_orig)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"^https://crop-production-complete.*\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Record-Count"],
)


# =============================================================================
# GET /api/health
# =============================================================================
@app.get("/api/health", tags=["Meta"])
def health():
    """
    Liveness and readiness check. Returns status, record count, and year bounds.
    Distinguishes application availability from dataset readiness.
    """
    if _DATASET_LOAD_ERROR:
        raise HTTPException(
            status_code=503,
            detail=f"Backend startup error: {_DATASET_LOAD_ERROR}",
        )
    df = get_df()
    return {
        "status": "ok",
        "ready": True,
        "records": int(len(df)),
        "record_count": int(len(df)),
        "year_min": int(df["Crop_Year"].min()),
        "year_max": int(df["Crop_Year"].max()),
    }


def get_metadata_dict() -> dict:
    """Compute and cache metadata dictionary once."""
    global _METADATA_CACHE
    if _METADATA_CACHE is not None:
        return _METADATA_CACHE

    df = get_df()

    # Build per-state district and crop mappings for the frontend filter bar.
    # These power the cascading State → District and State → Crop selectors.
    districts_by_state: dict = (
        df.groupby("State_Name")["District_Name"]
        .apply(lambda s: sorted(s.dropna().unique().tolist()))
        .to_dict()
    )
    crops_by_state: dict = (
        df.groupby("State_Name")["Crop"]
        .apply(lambda s: sorted(s.dropna().unique().tolist()))
        .to_dict()
    )
    seasons_by_crop: dict = (
        df.groupby("Crop")["Season"]
        .apply(lambda s: sorted(s.dropna().unique().tolist()))
        .to_dict()
    )

    _METADATA_CACHE = {
        "years":   sorted(int(y) for y in df["Crop_Year"].dropna().unique()),
        "states":  sorted(str(s) for s in df["State_Name"].dropna().unique()),
        "crops":   sorted(str(c) for c in df["Crop"].dropna().unique()),
        "seasons": sorted(str(s) for s in df["Season"].dropna().unique()),
        "data_types": sorted(str(d) for d in df["Data_Type"].dropna().unique()),
        "record_count": int(len(df)),
        "districts_by_state": districts_by_state,
        "crops_by_state":     crops_by_state,
        "seasons_by_crop":    seasons_by_crop,
        "state_name_mapping":        CSV_TO_GEOJSON,
        "unmatched_geometry_notes":  UNMATCHED_NOTES,
        "potentially_extended_years": POTENTIALLY_EXTENDED_YEARS,
        "last_verified_year":         LAST_VERIFIED_YEAR,
        "provenance_note":            _PROVENANCE_NOTE,
        "coconut_unit_caveat":        _COCONUT_CAVEAT,
    }
    return _METADATA_CACHE


# =============================================================================
# GET /api/metadata
# =============================================================================
@app.get("/api/metadata", tags=["Meta"])
def metadata():
    """
    Returns all available dimension values (years, states, crops, seasons),
    per-state district and crop lists for dependent filters,
    the GeoJSON state-name mapping, provenance note, and unit caveats.
    """
    return get_metadata_dict()


# =============================================================================
# GET /api/quality
# =============================================================================
@app.get("/api/quality", tags=["Meta"])
def quality():
    """
    Data quality report: record counts, missing values, duplicates, year range,
    and known dataset limitations.
    """
    df = get_df()
    rpt = quality_report(df)
    # year_range is a tuple — convert to list for JSON
    rpt["year_range"] = list(rpt["year_range"])
    rpt["provenance_note"]     = _PROVENANCE_NOTE
    rpt["coconut_unit_caveat"] = _COCONUT_CAVEAT

    # Detailed column profile
    cols = ["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production", "Data_Type"]
    total = len(df)
    rpt["columns"] = [
        {
            "column": col,
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
            "missingPct": round(float(df[col].isna().sum() / total * 100), 2) if total > 0 else 0.0,
            "invalid": 0,
        }
        for col in cols if col in df.columns
    ]

    # Records per year breakdown
    year_counts = df["Crop_Year"].value_counts().sort_index().to_dict()
    rpt["year_coverage"] = [
        {
            "year": int(y),
            "records": int(count),
            "dataType": "Synthetic" if int(y) in POTENTIALLY_EXTENDED_YEARS else "Observed",
        }
        for y, count in year_counts.items()
    ]

    # Provenance counts
    synthetic_count = int(df["Crop_Year"].isin(POTENTIALLY_EXTENDED_YEARS).sum())
    observed_count = total - synthetic_count
    rpt["provenance"] = [
        {"dataType": "Observed", "records": observed_count},
        {"dataType": "Synthetic", "records": synthetic_count},
    ]

    # State mappings
    state_counts = df["State_Name"].value_counts().to_dict()
    rpt["state_name_mappings"] = [
        {"raw": raw, "normalized": norm, "records": state_counts.get(raw, 0)}
        for raw, norm in CSV_TO_GEOJSON.items()
        if raw != norm and raw in state_counts
    ]
    rpt["unmatched_states"] = [k for k in UNMATCHED_NOTES.keys() if k in state_counts]
    rpt["geo_regions_without_data"] = ["Lakshadweep", "Daman and Diu"]

    return _make_safe(rpt)


# =============================================================================
# GET /api/kpis
# =============================================================================
@app.get("/api/kpis", tags=["Aggregations"])
def kpis(
    years:     Optional[str] = Query(None, description="Comma-separated years"),
    states:    Optional[str] = Query(None, description="Comma-separated state names"),
    state:     Optional[str] = Query(None, description="Single state name"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    crops:     Optional[str] = Query(None, description="Comma-separated crop names"),
    crop:      Optional[str] = Query(None, description="Single crop name"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    season:    Optional[str] = Query(None, description="Single season name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Fast single-query KPI summary for the dashboard overview cards.
    Calculates total production, area, unique crops, states, districts,
    and year-over-year production/area percentage change in a single fast pass.
    """
    cache_key = f"kpis:{years}:{states}:{state}:{districts}:{district}:{crops}:{crop}:{seasons}:{season}:{data_type}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    s_clean = _clean_str(state)
    c_clean = _clean_str(crop)
    d_clean = _clean_str(district)
    sn_clean = _clean_str(season)
    dt_clean = _clean_str(data_type)

    state_list = _parse_csv_param(states) or ([s_clean] if s_clean else None)
    crop_list = _parse_csv_param(crops) or ([c_clean] if c_clean else None)
    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)
    season_list = _parse_csv_param(seasons) or ([sn_clean] if sn_clean else None)

    df = _apply_filters(
        get_df(),
        years=_parse_year_list(years),
        states=state_list,
        crops=crop_list,
        seasons=season_list,
        districts=district_list,
        data_type=dt_clean,
    )

    if df.empty:
        res = {
            "totalProduction": 0.0,
            "totalArea": 0.0,
            "cropCount": 0,
            "stateCount": 0,
            "districtCount": 0,
            "recordCount": 0,
            "excludedRecords": 0,
            "productionChangePct": None,
            "areaChangePct": None,
            "lastYear": None,
        }
        _set_cached_query(cache_key, res)
        return res

    prod_valid = df.dropna(subset=["Production"])
    tot_prod = float(prod_valid["Production"].sum()) if not prod_valid.empty else 0.0
    tot_area = float(prod_valid["Area"].sum()) if not prod_valid.empty else 0.0
    crop_cnt = int(df["Crop"].nunique())
    state_cnt = int(df["State_Name"].nunique())
    dist_cnt = int(df["District_Name"].nunique())
    rec_cnt = int(len(df))
    excluded = int(df["Production"].isna().sum())

    # YoY calculations
    year_agg = prod_valid.groupby("Crop_Year").agg(
        prod=("Production", "sum"),
        area=("Area", "sum"),
    )
    last_year = int(year_agg.index.max()) if not year_agg.empty else None
    prod_change = None
    area_change = None
    if last_year and (last_year - 1) in year_agg.index:
        prev_prod = float(year_agg.loc[last_year - 1, "prod"])
        curr_prod = float(year_agg.loc[last_year, "prod"])
        if prev_prod > 0:
            prod_change = round(((curr_prod - prev_prod) / prev_prod) * 100.0, 2)

        prev_area = float(year_agg.loc[last_year - 1, "area"])
        curr_area = float(year_agg.loc[last_year, "area"])
        if prev_area > 0:
            area_change = round(((curr_area - prev_area) / prev_area) * 100.0, 2)

    res = {
        "totalProduction": tot_prod,
        "totalArea": tot_area,
        "cropCount": crop_cnt,
        "stateCount": state_cnt,
        "districtCount": dist_cnt,
        "recordCount": rec_cnt,
        "excludedRecords": excluded,
        "productionChangePct": prod_change,
        "areaChangePct": area_change,
        "lastYear": last_year,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/statewise
# =============================================================================
@app.get("/api/statewise", tags=["Aggregations"])
def statewise(
    years:     Optional[str] = Query(None, description="Comma-separated years, e.g. 2020,2021"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    crops:     Optional[str] = Query(None, description="Comma-separated crop names"),
    states:    Optional[str] = Query(None, description="Comma-separated state names"),
    state:     Optional[str] = Query(None, description="Single state name"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Total production, area, record count, and derived yield by state.
    Sorted by Total_Production descending.
    """
    cache_key = f"statewise:{years}:{states}:{state}:{districts}:{district}:{crops}:{seasons}:{data_type}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    s_clean = _clean_str(state)
    d_clean = _clean_str(district)
    dt_clean = _clean_str(data_type)

    state_list = _parse_csv_param(states) or ([s_clean] if s_clean else None)
    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)
    df = _apply_filters(
        get_df(),
        years=_parse_year_list(years),
        seasons=_parse_csv_param(seasons),
        crops=_parse_csv_param(crops),
        states=state_list,
        districts=district_list,
        data_type=dt_clean,
    )
    if df.empty:
        raise HTTPException(status_code=404, detail="No data matches the given filters.")
    res = {
        "data":                _df_to_records(statewise_production(df)),
        "coconut_unit_caveat": _COCONUT_CAVEAT,
        "provenance_note":     _PROVENANCE_NOTE,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/yearwise
# =============================================================================
@app.get("/api/yearwise", tags=["Aggregations"])
def yearwise(
    years:     Optional[str] = Query(None, description="Comma-separated years"),
    state:     Optional[str] = Query(None, description="Single state name"),
    states:    Optional[str] = Query(None, description="Comma-separated state names"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    crops:     Optional[str] = Query(None, description="Comma-separated crop names"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Year-wise total production, area, and record count.
    Accepts `state` (single) or `states` (comma-separated) for filtering.
    """
    cache_key = f"yearwise:{years}:{states}:{state}:{districts}:{district}:{crops}:{seasons}:{data_type}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    s_clean = _clean_str(state)
    d_clean = _clean_str(district)
    dt_clean = _clean_str(data_type)

    state_list = _parse_csv_param(states) or ([s_clean] if s_clean else None)
    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)

    df = _apply_filters(
        get_df(),
        years=_parse_year_list(years),
        states=state_list,
        seasons=_parse_csv_param(seasons),
        crops=_parse_csv_param(crops),
        districts=district_list,
        data_type=dt_clean,
    )
    if df.empty:
        raise HTTPException(status_code=404, detail="No data matches the given filters.")

    if s_clean and not states:
        result = yearwise_by_state(df, s_clean)
    else:
        result = yearwise_production(df)

    res = {
        "data":                       _df_to_records(result),
        "potentially_extended_years": POTENTIALLY_EXTENDED_YEARS,
        "provenance_note":            _PROVENANCE_NOTE,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/cropwise
# =============================================================================
@app.get("/api/cropwise", tags=["Aggregations"])
def cropwise(
    n:         int           = Query(15, ge=1, le=115, description="Top-N crops to return (1–115)"),
    years:     Optional[str] = Query(None, description="Comma-separated years"),
    states:    Optional[str] = Query(None, description="Comma-separated states"),
    state:     Optional[str] = Query(None, description="Single state name"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    crops:     Optional[str] = Query(None, description="Comma-separated crop names"),
    crop:      Optional[str] = Query(None, description="Single crop name"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Top-N crops by total production. Default n=15.
    """
    cache_key = f"cropwise:{n}:{years}:{states}:{state}:{districts}:{district}:{crops}:{crop}:{seasons}:{data_type}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    s_clean = _clean_str(state)
    c_clean = _clean_str(crop)
    d_clean = _clean_str(district)
    dt_clean = _clean_str(data_type)

    state_list = _parse_csv_param(states) or ([s_clean] if s_clean else None)
    crop_list = _parse_csv_param(crops) or ([c_clean] if c_clean else None)
    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)

    df = _apply_filters(
        get_df(),
        years=_parse_year_list(years),
        states=state_list,
        seasons=_parse_csv_param(seasons),
        crops=crop_list,
        districts=district_list,
        data_type=dt_clean,
    )
    if df.empty:
        raise HTTPException(status_code=404, detail="No data matches the given filters.")
    res = {
        "n":                   n,
        "data":                _df_to_records(cropwise_production(df, n=n)),
        "coconut_unit_caveat": _COCONUT_CAVEAT,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/seasonal
# =============================================================================
@app.get("/api/seasonal", tags=["Aggregations"])
def seasonal(
    years:     Optional[str] = Query(None, description="Comma-separated years"),
    states:    Optional[str] = Query(None, description="Comma-separated states"),
    state:     Optional[str] = Query(None, description="Single state name"),
    crops:     Optional[str] = Query(None, description="Comma-separated crop names"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Total production, area, yield, and record count broken down by season.
    """
    cache_key = f"seasonal:{years}:{states}:{state}:{districts}:{district}:{crops}:{seasons}:{data_type}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    s_clean = _clean_str(state)
    d_clean = _clean_str(district)
    dt_clean = _clean_str(data_type)

    state_list = _parse_csv_param(states) or ([s_clean] if s_clean else None)
    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)

    df = _apply_filters(
        get_df(),
        years=_parse_year_list(years),
        states=state_list,
        crops=_parse_csv_param(crops),
        seasons=_parse_csv_param(seasons),
        districts=district_list,
        data_type=dt_clean,
    )
    if df.empty:
        raise HTTPException(status_code=404, detail="No data matches the given filters.")
    res = {
        "data":                _df_to_records(seasonal_production(df)),
        "coconut_unit_caveat": _COCONUT_CAVEAT,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/mapdata
# =============================================================================
@app.get("/api/mapdata", tags=["Map"])
def mapdata(
    year:   Optional[int] = Query(None, description="Single crop year"),
    crop:   Optional[str] = Query(None, description="Single crop name"),
    season: Optional[str] = Query(None, description="Single season name"),
    metric: Literal["Production_sum", "Area_sum", "Yield_t_per_ha"] = Query(
        "Production_sum",
        description="Value to colour the map by",
    ),
):
    """
    State-level aggregation for the choropleth map.
    """
    c_clean = _clean_str(crop)
    sn_clean = _clean_str(season)
    cache_key = f"mapdata:{year}:{c_clean}:{sn_clean}:{metric}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    df = get_df()
    result = build_state_map_df(df, metric=metric, year=year, crop=c_clean, season=sn_clean)

    if result.empty:
        raise HTTPException(status_code=404, detail="No data matches the given filters.")

    prov = _PROVENANCE_NOTE if (year is not None and year in POTENTIALLY_EXTENDED_YEARS) else None
    coco = _COCONUT_CAVEAT if (c_clean is None or c_clean == "Coconut") else None

    res = {
        "metric":                   metric,
        "year":                     year,
        "crop":                     c_clean,
        "season":                   sn_clean,
        "data":                     _df_to_records(result),
        "unmatched_geometry_notes": UNMATCHED_NOTES,
        "provenance_note":          prov,
        "coconut_unit_caveat":      coco,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/crop-trend
# =============================================================================
@app.get("/api/crop-trend", tags=["Trends"])
def crop_trend_endpoint(
    crop:      str           = Query(..., description="Crop name (required)"),
    years:     Optional[str] = Query(None, description="Comma-separated years"),
    states:    Optional[str] = Query(None, description="Comma-separated states"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Year-wise production and area for a single named crop.
    """
    c_clean = _clean_str(crop)
    d_clean = _clean_str(district)
    dt_clean = _clean_str(data_type)

    cache_key = f"croptrend:{c_clean}:{years}:{states}:{districts}:{d_clean}:{seasons}:{dt_clean}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)
    df = _apply_filters(
        get_df(),
        years=_parse_year_list(years),
        states=_parse_csv_param(states),
        seasons=_parse_csv_param(seasons),
        districts=district_list,
        data_type=dt_clean,
    )
    result = crop_trend(df, c_clean or crop)
    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for crop '{crop}'.",
        )
    res = {
        "crop":            crop,
        "data":            _df_to_records(result),
        "provenance_note": _PROVENANCE_NOTE,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/state-trend
# =============================================================================
@app.get("/api/state-trend", tags=["Trends"])
def state_trend_endpoint(
    state:     str           = Query(..., description="State name (required)"),
    years:     Optional[str] = Query(None, description="Comma-separated years"),
    crops:     Optional[str] = Query(None, description="Comma-separated crop names"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Year-wise production and area for a single named state.
    """
    s_clean = _clean_str(state)
    d_clean = _clean_str(district)
    dt_clean = _clean_str(data_type)

    cache_key = f"statetrend:{s_clean}:{years}:{crops}:{districts}:{d_clean}:{seasons}:{dt_clean}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    df = get_df()
    valid_states = set(df["State_Name"].unique())
    target_state = s_clean or state
    if target_state not in valid_states:
        raise HTTPException(
            status_code=404,
            detail=f"State '{target_state}' not found. Use /api/metadata for valid state names.",
        )
    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)
    df = _apply_filters(
        df,
        years=_parse_year_list(years),
        crops=_parse_csv_param(crops),
        seasons=_parse_csv_param(seasons),
        districts=district_list,
        data_type=dt_clean,
    )
    result = yearwise_by_state(df, target_state)
    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No production data for '{target_state}' with the given filters.",
        )
    res = {
        "state":           target_state,
        "data":            _df_to_records(result),
        "provenance_note": _PROVENANCE_NOTE,
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# GET /api/districts
# =============================================================================
@app.get("/api/districts", tags=["Aggregations"])
def districts(
    state:     Optional[str] = Query(None, description="Filter to one state"),
    states:    Optional[str] = Query(None, description="Comma-separated states"),
    n:         int           = Query(15, ge=1, le=100, description="Top-N districts to return"),
    years:     Optional[str] = Query(None, description="Comma-separated years"),
    seasons:   Optional[str] = Query(None, description="Comma-separated seasons"),
    crops:     Optional[str] = Query(None, description="Comma-separated crop names"),
    districts: Optional[str] = Query(None, description="Comma-separated district names"),
    district:  Optional[str] = Query(None, description="Single district name"),
    data_type: Optional[str] = Query(None, description="Observed or Synthetic"),
):
    """
    Top-N districts by total production. Optionally filtered by state.
    """
    s_clean = _clean_str(state)
    d_clean = _clean_str(district)
    dt_clean = _clean_str(data_type)

    cache_key = f"districts:{n}:{s_clean}:{states}:{districts}:{d_clean}:{years}:{seasons}:{crops}:{dt_clean}"
    cached = _get_cached_query(cache_key)
    if cached is not None:
        return cached

    target_state = s_clean
    if not target_state and states:
        parsed = _parse_csv_param(states)
        if parsed:
            target_state = parsed[0]

    district_list = _parse_csv_param(districts) or ([d_clean] if d_clean else None)

    df = _apply_filters(
        get_df(),
        years=_parse_year_list(years),
        seasons=_parse_csv_param(seasons),
        crops=_parse_csv_param(crops),
        districts=district_list,
        data_type=dt_clean,
    )
    result = district_production(df, state=target_state, n=n)
    if result.empty:
        raise HTTPException(status_code=404, detail="No district data for the given filters.")
    res = {
        "state":  target_state,
        "n":      n,
        "data":   _df_to_records(result),
    }
    _set_cached_query(cache_key, res)
    return res


# =============================================================================
# Shared helpers for /api/records and /api/export/records
# =============================================================================

# Columns the frontend may sort on (mapped frontend key → CSV column name).
_SORTABLE_COLUMNS: dict[str, str] = {
    "state":      "State_Name",
    "district":   "District_Name",
    "year":       "Crop_Year",
    "season":     "Season",
    "crop":       "Crop",
    "area":       "Area",
    "production": "Production",
    "dataType":   "Data_Type",
    # Allow raw column names too
    "State_Name":      "State_Name",
    "District_Name":   "District_Name",
    "Crop_Year":       "Crop_Year",
    "Season":          "Season",
    "Crop":            "Crop",
    "Area":            "Area",
    "Production":      "Production",
    "Data_Type":       "Data_Type",
}

# Columns that are searched by the free-text search parameter.
_SEARCH_COLUMNS = ["State_Name", "District_Name", "Crop", "Season", "Data_Type"]

# Maximum rows per page.
_MAX_PAGE_SIZE = 100


def _filter_records(
    year_from: Optional[int],
    year_to:   Optional[int],
    state:     Optional[str],
    district:  Optional[str],
    crop:      Optional[str],
    season:    Optional[str],
    data_type: Optional[str],
    search:    Optional[str],
) -> pd.DataFrame:
    """
    Apply all row-level filters to the cached DataFrame and return the result.
    Does NOT apply sorting or pagination — those are the caller's responsibility.
    """
    df = get_df()

    # Year range
    if year_from is not None:
        df = df[df["Crop_Year"] >= year_from]
    if year_to is not None:
        df = df[df["Crop_Year"] <= year_to]

    # Dimension filters (case-sensitive, exact match — values come from the dataset)
    if state:
        df = df[df["State_Name"] == state]
    if district:
        df = df[df["District_Name"] == district]
    if crop:
        df = df[df["Crop"] == crop]
    if season:
        df = df[df["Season"] == season]
    if data_type:
        df = df[df["Data_Type"] == data_type]

    # Free-text search across text columns (case-insensitive, substring)
    if search and search.strip():
        term = search.strip().lower()
        mask = pd.Series(False, index=df.index)
        for col in _SEARCH_COLUMNS:
            mask |= df[col].str.lower().str.contains(term, na=False, regex=False)
        df = df[mask]

    return df


# =============================================================================
# GET /api/records
# =============================================================================
@app.get("/api/records", tags=["Records"])
def records(
    year_from:  Optional[int] = Query(None, description="Earliest crop year (inclusive)"),
    year_to:    Optional[int] = Query(None, description="Latest crop year (inclusive)"),
    state:      Optional[str] = Query(None, description="Exact state name"),
    district:   Optional[str] = Query(None, description="Exact district name"),
    crop:       Optional[str] = Query(None, description="Exact crop name"),
    season:     Optional[str] = Query(None, description="Exact season name"),
    data_type:  Optional[str] = Query(None, alias="data_type", description="Exact Data_Type value"),
    search:     Optional[str] = Query(None, description="Free-text search across state, district, crop, season, data type"),
    sort_by:    Optional[str] = Query("year", description="Column to sort by (frontend key or raw CSV column name)"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    page:       int            = Query(1, ge=1, description="1-indexed page number"),
    page_size:  int            = Query(25, ge=1, le=_MAX_PAGE_SIZE, description=f"Rows per page (max {_MAX_PAGE_SIZE})"),
):
    """
    Paginated, filtered, sortable access to raw crop-production records.

    All filters are applied server-side on the pre-loaded, cleaned DataFrame.
    Yields are included per row when both Area > 0 and Production is non-null.

    **Coconut caveat:** rows where Crop = 'Coconut' have Production in number
    of nuts, not metric tonnes — do not aggregate across crops.
    """
    # ── Validate year range ───────────────────────────────────────────────────
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(
            status_code=422,
            detail="year_from must be less than or equal to year_to.",
        )

    # ── Validate sort column ──────────────────────────────────────────────────
    resolved_sort = _SORTABLE_COLUMNS.get(sort_by or "year")
    if resolved_sort is None:
        raise HTTPException(
            status_code=422,
            detail=(
                f"sort_by '{sort_by}' is not a sortable column. "
                f"Valid values: {sorted(_SORTABLE_COLUMNS.keys())}"
            ),
        )

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = _filter_records(
        year_from=year_from,
        year_to=year_to,
        state=state,
        district=district,
        crop=crop,
        season=season,
        data_type=data_type,
        search=search,
    )

    total = len(filtered)

    # ── Sort ──────────────────────────────────────────────────────────────────
    ascending = sort_order == "asc"
    try:
        filtered = filtered.sort_values(resolved_sort, ascending=ascending, na_position="last")
    except KeyError:
        pass  # Column may not exist in edge cases; proceed unsorted.

    # ── Paginate ──────────────────────────────────────────────────────────────
    total_pages = max(1, math.ceil(total / page_size))
    safe_page = min(page, total_pages)
    offset = (safe_page - 1) * page_size
    page_df = filtered.iloc[offset: offset + page_size]

    # ── Build response rows ───────────────────────────────────────────────────
    # Return only the columns the frontend expects, renaming to the canonical
    # CropRecord field names to keep the service.ts mapper simple.
    rows = []
    for idx, (_, row) in enumerate(page_df.iterrows()):
        year_val = _safe(row.get("Crop_Year"))
        rows.append({
            "id":         offset + idx + 1,
            "State_Name":    _safe(row.get("State_Name")),
            "District_Name": _safe(row.get("District_Name")),
            "Crop_Year":     year_val,
            "Season":        _safe(row.get("Season")),
            "Crop":          _safe(row.get("Crop")),
            "Area":          _safe(row.get("Area")),
            "Production":    _safe(row.get("Production")),
            "Data_Type":     _safe(row.get("Data_Type")),
            "Yield_t_per_ha": _safe(row.get("Yield_t_per_ha")),
            "Data_Provenance": _safe(row.get("Data_Provenance")),
        })

    return {
        "total":      total,
        "page":       safe_page,
        "page_size":  page_size,
        "total_pages": total_pages,
        "records":    rows,
        "coconut_unit_caveat": _COCONUT_CAVEAT if (crop is None or crop == "Coconut") else None,
    }


# =============================================================================
# GET /api/export/records
# =============================================================================
@app.get("/api/export/records", tags=["Records"])
def export_records(
    year_from:  Optional[int] = Query(None, description="Earliest crop year (inclusive)"),
    year_to:    Optional[int] = Query(None, description="Latest crop year (inclusive)"),
    state:      Optional[str] = Query(None, description="Exact state name"),
    district:   Optional[str] = Query(None, description="Exact district name"),
    crop:       Optional[str] = Query(None, description="Exact crop name"),
    season:     Optional[str] = Query(None, description="Exact season name"),
    data_type:  Optional[str] = Query(None, alias="data_type", description="Exact Data_Type value"),
    search:     Optional[str] = Query(None, description="Free-text search across text columns"),
    sort_by:    Optional[str] = Query("year", description="Column to sort by"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
):
    """
    Stream a CSV export of **all** filtered records (no pagination limit).

    The response Content-Disposition header will trigger a file download in
    browsers. Large exports may take several seconds to stream.
    Do not use this endpoint for interactive display — use /api/records instead.
    """
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(
            status_code=422,
            detail="year_from must be less than or equal to year_to.",
        )

    resolved_sort = _SORTABLE_COLUMNS.get(sort_by or "year")
    if resolved_sort is None:
        resolved_sort = "Crop_Year"

    filtered = _filter_records(
        year_from=year_from,
        year_to=year_to,
        state=state,
        district=district,
        crop=crop,
        season=season,
        data_type=data_type,
        search=search,
    )

    ascending = sort_order == "asc"
    try:
        filtered = filtered.sort_values(resolved_sort, ascending=ascending, na_position="last")
    except KeyError:
        pass

    # Select only the 8 canonical columns for the export
    export_cols = ["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production", "Data_Type"]
    export_df = filtered[export_cols]

    buf = io.StringIO()
    export_df.to_csv(buf, index=False)
    buf.seek(0)

    filename = "crop-records-export.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Record-Count": str(len(filtered)),
    }
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers=headers,
    )
