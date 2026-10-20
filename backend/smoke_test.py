"""
smoke_test.py – comprehensive smoke test that exercises every analytics and
visualisation function without launching the browser.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_cleaning import load_raw, clean, quality_report, DATA_PATH
from data_loader import get_dataframe, apply_filters
from pandas_analysis import (
    top_states_by_production, yearwise_production, cropwise_production,
    seasonal_production, statewise_production, district_production,
    crop_trend, state_crop_comparison, yearwise_by_state,
    compare_multiple_crops, season_crop_breakdown,
    production_distribution_by_state,
)
from map_utils import build_state_map_df, CSV_TO_GEOJSON
from visualizations import (
    india_choropleth, yearwise_trend_plotly, top_states_bar,
    seasonal_comparison_plotly, crop_production_bar, crop_trend_plotly,
    multi_crop_trend, district_bar, production_pie, area_vs_production_scatter,
    state_crop_radar, yield_boxplot,
    matplotlib_yearwise_trend, matplotlib_seasonal_bar, matplotlib_state_production,
)

PASS = []
FAIL = []

def ok(name):
    PASS.append(name)
    print("PASS:", name)

def fail(name, err):
    FAIL.append(name)
    print("FAIL:", name, "|", err)

# ─── Data load ───────────────────────────────────────────────────────────────
try:
    df = get_dataframe()
    assert len(df) > 400_000
    ok("data_load")
except Exception as e:
    fail("data_load", e); raise  # fatal

# ─── Quality report ──────────────────────────────────────────────────────────
try:
    rpt = quality_report(df)
    assert rpt["total_records"] > 0
    ok("quality_report")
except Exception as e:
    fail("quality_report", e)

# ─── apply_filters ───────────────────────────────────────────────────────────
try:
    f1 = apply_filters(df, years=[2020], states=["Punjab"], seasons=["Rabi"])
    assert len(f1) > 0
    ok("apply_filters")
except Exception as e:
    fail("apply_filters", e)

# ─── Pandas aggregations ─────────────────────────────────────────────────────
for name, fn, args in [
    ("top_states_by_production",      top_states_by_production,      (df, 10)),
    ("yearwise_production",           yearwise_production,           (df,)),
    ("cropwise_production",           cropwise_production,           (df, 15)),
    ("seasonal_production",           seasonal_production,           (df,)),
    ("statewise_production",          statewise_production,          (df,)),
    ("district_production_all",       district_production,           (df,)),
    ("district_production_state",     district_production,           (df, "Punjab", 10)),
    ("crop_trend_Rice",               crop_trend,                    (df, "Rice")),
    ("state_crop_comparison",         state_crop_comparison,         (df, "Punjab")),
    ("yearwise_by_state",             yearwise_by_state,             (df, "Punjab")),
    ("compare_multiple_crops",        compare_multiple_crops,        (df, ["Rice", "Wheat", "Maize"])),
    ("season_crop_breakdown",         season_crop_breakdown,         (df,)),
    ("production_distribution",       production_distribution_by_state, (df, 2020)),
]:
    try:
        result = fn(*args)
        assert result is not None and len(result) >= 0
        ok(name)
    except Exception as e:
        fail(name, e)

# ─── Map aggregation ─────────────────────────────────────────────────────────
try:
    map_df = build_state_map_df(df, year=2020, crop="Rice", season="Kharif")
    assert len(map_df) > 0
    ok("build_state_map_df")
except Exception as e:
    fail("build_state_map_df", e)

# ─── Plotly charts ───────────────────────────────────────────────────────────
map_df_all = build_state_map_df(df, year=2022)
yr_df  = yearwise_production(df)
sea_df = seasonal_production(df)
crop_df = cropwise_production(df, 15)
dist_df = district_production(df, n=10)
state_df = statewise_production(df)
rice_trend = crop_trend(df, "Rice")
state_crops = state_crop_comparison(df, "Punjab")

for name, fn, args in [
    ("india_choropleth",           india_choropleth,            (map_df_all,)),
    ("yearwise_trend_plotly",      yearwise_trend_plotly,       (yr_df,)),
    ("top_states_bar",             top_states_bar,              (top_states_by_production(df, 10),)),
    ("seasonal_comparison_plotly", seasonal_comparison_plotly,  (sea_df,)),
    ("crop_production_bar",        crop_production_bar,         (crop_df, 15)),
    ("crop_trend_plotly",          crop_trend_plotly,           (rice_trend, "Rice")),
    ("multi_crop_trend",           multi_crop_trend,            (df, ["Rice", "Wheat"])),
    ("district_bar",               district_bar,                (dist_df,)),
    ("production_pie",             production_pie,              (state_df,)),
    ("area_vs_production_scatter", area_vs_production_scatter,  (df,)),
    ("state_crop_radar",           state_crop_radar,            (state_crops, "Punjab")),
    ("yield_boxplot",              yield_boxplot,               (df, 8)),
]:
    try:
        fig = fn(*args)
        assert fig is not None
        ok(name)
    except Exception as e:
        fail(name, e)

# ─── Matplotlib charts ───────────────────────────────────────────────────────
import matplotlib; matplotlib.use("Agg")  # non-interactive backend

for name, fn, args in [
    ("matplotlib_yearwise_trend",   matplotlib_yearwise_trend,   (yr_df,)),
    ("matplotlib_seasonal_bar",     matplotlib_seasonal_bar,     (sea_df,)),
    ("matplotlib_state_production", matplotlib_state_production, (state_df,)),
]:
    try:
        fig = fn(*args)
        assert fig is not None
        import matplotlib.pyplot as plt; plt.close(fig)
        ok(name)
    except Exception as e:
        fail(name, e)

# ─── Summary ─────────────────────────────────────────────────────────────────
print()
print("=" * 50)
print("SMOKE TEST RESULTS")
print("=" * 50)
print("PASSED:", len(PASS))
print("FAILED:", len(FAIL))
if FAIL:
    print("FAILURES:", FAIL)
else:
    print("ALL CHECKS PASSED")
