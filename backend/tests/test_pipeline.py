"""
tests/test_pipeline.py
----------------------
Automated tests for the crop production analytics pipeline.

Run with:
    python -m pytest tests/ -v
or:
    python tests/test_pipeline.py
"""

import sys
import os
import pandas as pd
import numpy as np

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from data_cleaning import load_raw, clean, quality_report, DATA_PATH
from pandas_analysis import (
    top_states_by_production, yearwise_production, cropwise_production,
    seasonal_production, statewise_production, district_production,
    crop_trend,
)
from map_utils import build_state_map_df, CSV_TO_GEOJSON, normalise_state_name


def test_raw_load():
    """Dataset loads without errors and has expected shape."""
    df = load_raw(DATA_PATH)
    assert len(df) > 400000, "Expected more than 400,000 records"
    assert list(df.columns) == [
        "State_Name", "District_Name", "Crop_Year", "Season",
        "Crop", "Area", "Production", "Data_Type"
    ], "Column names do not match expected"
    print("✅ test_raw_load passed")


def test_clean_adds_columns():
    """Cleaning adds Yield_t_per_ha and Data_Provenance columns."""
    df = load_raw(DATA_PATH)
    clean_df = clean(df)
    assert "Yield_t_per_ha" in clean_df.columns
    assert "Data_Provenance" in clean_df.columns
    print("✅ test_clean_adds_columns passed")


def test_no_negative_area():
    """No negative area values after cleaning."""
    df = clean(load_raw(DATA_PATH))
    assert (df["Area"] < 0).sum() == 0, "Negative area values found"
    print("✅ test_no_negative_area passed")


def test_no_negative_production():
    """No negative production values after cleaning."""
    df = clean(load_raw(DATA_PATH))
    assert (df["Production"] < 0).sum() == 0, "Negative production values found"
    print("✅ test_no_negative_production passed")


def test_quality_report_keys():
    """Quality report contains all expected keys."""
    df = clean(load_raw(DATA_PATH))
    report = quality_report(df)
    required_keys = [
        "total_records", "missing_production", "year_range",
        "states", "crops", "limitations"
    ]
    for key in required_keys:
        assert key in report, f"Missing key in quality report: {key}"
    print("✅ test_quality_report_keys passed")


def test_state_name_mapping():
    """All CSV state names map to a GeoJSON name."""
    df = clean(load_raw(DATA_PATH))
    for state in df["State_Name"].unique():
        mapped = normalise_state_name(state)
        assert mapped is not None, f"No mapping for state: {state}"
    print("✅ test_state_name_mapping passed")


def test_yearwise_production_monotone_years():
    """Year-wise aggregation returns sorted years."""
    df = clean(load_raw(DATA_PATH))
    yr = yearwise_production(df)
    years = yr["Crop_Year"].tolist()
    assert years == sorted(years), "Years not sorted in yearwise_production"
    print("✅ test_yearwise_production_monotone_years passed")


def test_top_states_count():
    """top_states_by_production returns exactly n rows (or fewer if fewer states)."""
    df = clean(load_raw(DATA_PATH))
    top = top_states_by_production(df, n=10)
    assert len(top) <= 10
    assert len(top) > 0
    print("✅ test_top_states_count passed")


def test_no_duplicate_key():
    """No duplicate key combination (State, District, Year, Season, Crop)."""
    df = clean(load_raw(DATA_PATH))
    dup = df.duplicated(subset=["State_Name", "District_Name", "Crop_Year", "Season", "Crop"]).sum()
    assert dup == 0, f"Found {dup} duplicate key combinations"
    print("✅ test_no_duplicate_key passed")


def test_build_state_map_df():
    """Map aggregation returns expected columns."""
    df = clean(load_raw(DATA_PATH))
    map_df = build_state_map_df(df, year=2020)
    required = ["State_Name", "Production_sum", "Area_sum", "Yield_t_per_ha", "geojson_name"]
    for col in required:
        assert col in map_df.columns, f"Missing column in map_df: {col}"
    assert len(map_df) > 0, "Empty map aggregation"
    print("✅ test_build_state_map_df passed")


def test_crop_trend_rice():
    """Crop trend for 'Rice' returns plausible data."""
    df = clean(load_raw(DATA_PATH))
    trend = crop_trend(df, "Rice")
    assert len(trend) > 0, "No trend data for Rice"
    assert trend["Total_Production"].sum() > 0
    print("✅ test_crop_trend_rice passed")


def test_mapreduce_mapper():
    """Mapper emits correct key-value pairs."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "mapreduce"))
    import io
    import subprocess

    sample_csv = (
        "State_Name,District_Name,Crop_Year,Season,Crop,Area,Production,Data_Type\n"
        "Andhra Pradesh,Ananthapuramu,1997,Kharif,Rice,35600,75400,Actual\n"
        "Bihar,Patna,2000,Rabi,Wheat,10000,25000,Actual\n"
        "Bihar,Gaya,2000,Rabi,Wheat,8000,,Actual\n"   # missing production — should be skipped
    )

    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "mapreduce", "mapper.py")],
        input=sample_csv,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()
    # Should emit 2 lines (not the missing production row)
    assert len(lines) == 2, f"Expected 2 mapper outputs, got {len(lines)}: {lines}"
    assert lines[0] == "Andhra Pradesh\t75400.0"
    assert lines[1] == "Bihar\t25000.0"
    print("✅ test_mapreduce_mapper passed")


def test_mapreduce_reducer():
    """Reducer correctly sums values per state."""
    import subprocess

    sorted_input = (
        "Andhra Pradesh\t75400.0\n"
        "Bihar\t25000.0\n"
        "Bihar\t8000.0\n"
    )
    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "mapreduce", "reducer.py")],
        input=sorted_input,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 2
    assert lines[0] == "Andhra Pradesh\t75400.0"
    assert lines[1] == "Bihar\t33000.0"
    print("✅ test_mapreduce_reducer passed")


if __name__ == "__main__":
    tests = [
        test_raw_load,
        test_clean_adds_columns,
        test_no_negative_area,
        test_no_negative_production,
        test_quality_report_keys,
        test_state_name_mapping,
        test_yearwise_production_monotone_years,
        test_top_states_count,
        test_no_duplicate_key,
        test_build_state_map_df,
        test_crop_trend_rice,
        test_mapreduce_mapper,
        test_mapreduce_reducer,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("🎉 All tests passed!")
