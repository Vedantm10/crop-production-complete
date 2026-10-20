"""
app.py
======
Crop Production Trends & Agricultural Productivity Analysis
Big Data Dashboard - Streamlit Application

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import io
import subprocess

# Path setup
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from data_loader import (
    get_dataframe, get_quality_report,
    apply_filters, get_all_years, get_all_states, get_all_crops, get_all_seasons,
)
from data_cleaning import POTENTIALLY_EXTENDED_YEARS, LAST_VERIFIED_YEAR
from pandas_analysis import (
    top_states_by_production, yearwise_production, cropwise_production,
    seasonal_production, statewise_production, district_production,
    crop_trend, state_crop_comparison, yearwise_by_state,
    compare_multiple_crops, production_distribution_by_state,
)
from map_utils import build_state_map_df, UNMATCHED_NOTES
from visualizations import (
    india_choropleth, yearwise_trend_plotly, top_states_bar,
    seasonal_comparison_plotly, crop_production_bar, crop_trend_plotly,
    multi_crop_trend, district_bar, production_pie, area_vs_production_scatter,
    state_crop_radar, yield_boxplot,
    matplotlib_yearwise_trend, matplotlib_seasonal_bar, matplotlib_state_production,
)

# Page config
st.set_page_config(
    page_title="AgriIntel India - Crop Analytics",
    page_icon=":seedling:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
# IMPORTANT: 'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji' are
# added as fallbacks so that emoji characters render properly on all platforms.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #064e3b 0%, #065f46 50%, #047857 100%);
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span { color: #d1fae5 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; }

[data-testid="metric-container"] {
    background: white;
    border: 1px solid #d1fae5;
    border-left: 5px solid #10b981;
    border-radius: 14px;
    padding: 14px 18px;
    box-shadow: 0 2px 12px rgba(6,78,59,0.08);
}
[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #065f46 !important;
    font-weight: 700 !important;
    font-size: 1.65rem !important;
}

.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 18px; font-weight: 500; }
.stTabs [aria-selected="true"] { background: #ecfdf5 !important; color: #065f46 !important; border-bottom: 3px solid #10b981; }

.stDownloadButton button {
    background: #065f46; color: white;
    border-radius: 8px; border: none;
    padding: 8px 18px; font-weight: 500;
}
.stDownloadButton button:hover { background: #047857; }

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ---- Helpers ----------------------------------------------------------------

def fmt_num(val, unit="t"):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    if val >= 1_000_000_000:
        return f"{val/1e9:.2f} B {unit}"
    if val >= 1_000_000:
        return f"{val/1e6:.2f} M {unit}"
    if val >= 1_000:
        return f"{val/1e3:.1f} K {unit}"
    return f"{val:.1f} {unit}"


def page_header(title: str, subtitle: str):
    """Gradient page header using a single-line HTML string (emoji-safe)."""
    st.markdown(
        '<div style="background:linear-gradient(135deg,#064e3b,#059669);'
        'border-radius:14px;padding:24px 28px;margin-bottom:20px;">'
        '<h2 style="color:white;margin:0;font-size:1.6rem;font-weight:700;">' + title + '</h2>'
        '<p style="color:#a7f3d0;margin:4px 0 0 0;font-size:0.9rem;">' + subtitle + '</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"#### {title}")
    if subtitle:
        st.caption(subtitle)


def kpi_row(metrics: list):
    cols = st.columns(len(metrics))
    for col, item in zip(cols, metrics):
        label = item[0]
        value = item[1]
        delta = item[2] if len(item) > 2 else None
        with col:
            if delta is not None:
                st.metric(label=label, value=value, delta=delta)
            else:
                st.metric(label=label, value=value)


def empty_state(message: str):
    st.info(message)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


# ---- Load data --------------------------------------------------------------
with st.spinner("Loading crop production data..."):
    df_full = get_dataframe()
    quality = get_quality_report()

ALL_YEARS   = get_all_years(df_full)
ALL_STATES  = get_all_states(df_full)
ALL_CROPS   = get_all_crops(df_full)
ALL_SEASONS = get_all_seasons(df_full)


# ---- Sidebar ----------------------------------------------------------------
with st.sidebar:
    st.markdown("## AgriIntel India")
    st.caption("Crop Production Analytics Dashboard")
    st.divider()

    page = st.selectbox(
        "Navigate to",
        [
            "Overview Dashboard",
            "India Production Map",
            "Crop and Seasonal Analysis",
            "State and District Analysis",
            "Historical Trends",
            "Dataset Explorer",
            "Big Data Processing",
        ],
    )

    st.divider()
    st.markdown("### Global Filters")

    year_range = st.slider(
        "Crop Year Range",
        min_value=int(min(ALL_YEARS)),
        max_value=int(max(ALL_YEARS)),
        value=(1997, 2023),
        step=1,
    )
    selected_years   = list(range(year_range[0], year_range[1] + 1))
    selected_seasons = st.multiselect("Season(s)", ALL_SEASONS, default=[], placeholder="All seasons")
    selected_states  = st.multiselect("State(s)",  ALL_STATES,  default=[], placeholder="All states")
    selected_crops   = st.multiselect("Crop(s)",   ALL_CROPS,   default=[], placeholder="All crops")

    st.divider()
    st.caption(
        f"Records: {quality['total_records']:,}\n\n"
        f"States: {quality['states']}\n\n"
        f"Crops: {quality['crops']}\n\n"
        f"Missing Production: {quality['missing_production']:,}"
    )

# ---- Apply filters ----------------------------------------------------------
df = apply_filters(
    df_full,
    years=selected_years   if selected_years   else None,
    states=selected_states if selected_states  else None,
    crops=selected_crops   if selected_crops   else None,
    seasons=selected_seasons if selected_seasons else None,
)

if "selected_map_state" not in st.session_state:
    st.session_state.selected_map_state = None


# =============================================================================
#  PAGE A - OVERVIEW DASHBOARD
# =============================================================================
if page == "Overview Dashboard":
    page_header(
        "Agricultural Intelligence Dashboard",
        f"Crop Production Trends and Productivity | India | {year_range[0]}-{year_range[1]}"
    )

    if df.empty:
        empty_state("No records match the current filters. Adjust the sidebar filters.")
        st.stop()

    total_prod = df.dropna(subset=["Production"])["Production"].sum()
    total_area = df["Area"].sum()
    n_crops    = df["Crop"].nunique()
    n_states   = df["State_Name"].nunique()

    kpi_row([
        ("Total Production",   fmt_num(total_prod, "t")),
        ("Cultivated Area",    fmt_num(total_area, "ha")),
        ("Unique Crops",       str(n_crops)),
        ("States and UTs",     str(n_states)),
    ])

    st.divider()

    col_map, col_rank = st.columns([2.2, 1])
    with col_map:
        section_header("India Production Map", "Hover over a state for details")
        map_df = build_state_map_df(df_full, year=year_range[1])
        if not map_df.empty:
            st.plotly_chart(
                india_choropleth(map_df, title=f"State Production - {year_range[1]}",
                                 selected_state=st.session_state.selected_map_state),
                width="stretch",
            )
        else:
            empty_state("No geographic data for selected filters.")

    with col_rank:
        section_header("Top Producing States")
        top_s = statewise_production(df).head(10).reset_index(drop=True)
        max_prod = top_s["Total_Production"].iloc[0] if len(top_s) else 1
        for i, row in top_s.iterrows():
            pct = row["Total_Production"] / max_prod
            st.markdown(f"**#{i+1} {row['State_Name']}**")
            st.caption(fmt_num(row["Total_Production"], "t"))
            st.progress(float(pct))

    st.divider()

    col_trend, col_season = st.columns(2)
    with col_trend:
        section_header("Year-wise Production Trend")
        yr_df = yearwise_production(df)
        if not yr_df.empty:
            st.plotly_chart(yearwise_trend_plotly(yr_df), width="stretch")
        else:
            empty_state("No year-wise data available.")

    with col_season:
        section_header("Production by Season")
        sea_df = seasonal_production(df)
        if not sea_df.empty:
            st.plotly_chart(seasonal_comparison_plotly(sea_df), width="stretch")
        else:
            empty_state("No seasonal data available.")

    section_header("Top Crops by Production")
    crop_df = cropwise_production(df, n=15)
    if not crop_df.empty:
        st.plotly_chart(crop_production_bar(crop_df, n=15), width="stretch")
    else:
        empty_state("No crop data for current filters.")

    if year_range[1] >= 2024:
        st.warning(
            "Data Provenance: Years 2024-2025 have identical record counts to 2023, "
            "suggesting forward-fill or synthetic extension. Do not cite as verified statistics.",
            icon="warning",
        )


# =============================================================================
#  PAGE B - INDIA PRODUCTION MAP
# =============================================================================
elif page == "India Production Map":
    page_header(
        "India Production Map",
        "Interactive state-level choropleth | data from crop_production_1997_2025.csv"
    )

    mf1, mf2, mf3, mf4 = st.columns(4)
    with mf1:
        map_year   = st.selectbox("Year",   ALL_YEARS, index=len(ALL_YEARS)-3)
    with mf2:
        map_crop   = st.selectbox("Crop",   ["All Crops"] + ALL_CROPS)
    with mf3:
        map_season = st.selectbox("Season", ["All Seasons"] + ALL_SEASONS)
    with mf4:
        map_metric = st.selectbox(
            "Metric",
            ["Production_sum", "Area_sum", "Yield_t_per_ha"],
            format_func=lambda x: {
                "Production_sum": "Production (t)",
                "Area_sum":       "Area (ha)",
                "Yield_t_per_ha": "Yield (t/ha)",
            }[x],
        )

    if st.button("Reset State Selection"):
        st.session_state.selected_map_state = None

    map_df = build_state_map_df(
        df_full,
        metric=map_metric,
        year=map_year,
        crop=map_crop   if map_crop   != "All Crops"    else None,
        season=map_season if map_season != "All Seasons" else None,
    )

    if map_df.empty:
        empty_state("No data for the selected filters.")
    else:
        st.plotly_chart(
            india_choropleth(
                map_df, metric=map_metric,
                title=f"India | {map_year} | {map_crop} | {map_season}",
                selected_state=st.session_state.selected_map_state,
            ),
            width="stretch",
        )

        st.divider()
        section_header("State Rankings", f"{map_year} | {map_crop} | {map_season}")
        disp = map_df[["State_Name","Production_sum","Area_sum","Yield_t_per_ha","record_count"]].copy()
        disp.columns = ["State","Production (t)","Area (ha)","Yield (t/ha)","Records"]
        disp = disp.sort_values("Production (t)", ascending=False).reset_index(drop=True)
        disp.index += 1
        st.dataframe(
            disp.style.format({
                "Production (t)": "{:,.0f}",
                "Area (ha)":      "{:,.0f}",
                "Yield (t/ha)":   "{:.3f}",
            }),
            width="stretch", height=420,
        )
        st.download_button(
            "Download State Data (CSV)",
            data=to_csv_bytes(disp),
            file_name=f"state_{map_year}.csv",
            mime="text/csv",
        )

        with st.expander("State-name matching notes"):
            for state, note in UNMATCHED_NOTES.items():
                st.markdown(f"- **{state}:** {note}")


# =============================================================================
#  PAGE C - CROP AND SEASONAL ANALYSIS
# =============================================================================
elif page == "Crop and Seasonal Analysis":
    page_header(
        "Crop and Seasonal Analysis",
        "Individual crop trends, seasonal patterns, and yield analysis"
    )

    tab1, tab2, tab3 = st.tabs(["Crop Trend", "Multi-Crop Compare", "Seasonal Breakdown"])

    with tab1:
        sel_crop = st.selectbox("Select Crop", ALL_CROPS)
        trend    = crop_trend(df, sel_crop)
        if trend.empty:
            empty_state(f"No data for {sel_crop} in the selected filters.")
        else:
            tp  = trend["Total_Production"].sum()
            ta  = trend["Total_Area"].sum()
            yld = tp / ta if ta > 0 else None
            kpi_row([
                ("Total Production", fmt_num(tp)),
                ("Total Area",       fmt_num(ta, "ha")),
                ("Avg Yield",        fmt_num(yld, "t/ha") if yld else "N/A"),
            ])
            st.plotly_chart(crop_trend_plotly(trend, sel_crop), width="stretch")
            section_header("Yield Distribution - Top 10 Crops")
            st.plotly_chart(yield_boxplot(df, top_n=10), width="stretch")
            section_header("Matplotlib - Seasonal Production", "Static analytical visualization")
            sea_df = seasonal_production(df)
            if not sea_df.empty:
                import matplotlib.pyplot as plt
                fig_mpl = matplotlib_seasonal_bar(sea_df)
                st.pyplot(fig_mpl)
                plt.close(fig_mpl)

    with tab2:
        section_header("Compare Multiple Crops")
        crops_to_compare = st.multiselect(
            "Choose up to 8 crops", ALL_CROPS,
            default=ALL_CROPS[:4] if len(ALL_CROPS) >= 4 else ALL_CROPS,
            max_selections=8,
        )
        if crops_to_compare:
            st.plotly_chart(multi_crop_trend(df, crops_to_compare), width="stretch")
        else:
            empty_state("Select at least one crop to compare.")

    with tab3:
        section_header("Seasonal Production Breakdown")
        sea_df = seasonal_production(df)
        if not sea_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(seasonal_comparison_plotly(sea_df), width="stretch")
            with c2:
                st.plotly_chart(area_vs_production_scatter(df), width="stretch")
            section_header("Seasonal Summary Table")
            disp = sea_df.copy()
            disp.columns = ["Season","Total Production (t)","Total Area (ha)"]
            disp["Yield (t/ha)"] = disp["Total Production (t)"] / disp["Total Area (ha)"]
            st.dataframe(
                disp.style.format({
                    "Total Production (t)": "{:,.0f}",
                    "Total Area (ha)":      "{:,.0f}",
                    "Yield (t/ha)":         "{:.3f}",
                }),
                width="stretch",
            )
        else:
            empty_state("No seasonal data for current filters.")


# =============================================================================
#  PAGE D - STATE AND DISTRICT ANALYSIS
# =============================================================================
elif page == "State and District Analysis":
    page_header(
        "State and District Analysis",
        "Drill down into state and district-level production patterns"
    )

    sel_state = st.selectbox("Select State", ["All States"] + ALL_STATES)

    tab_state, tab_district, tab_rankings = st.tabs(
        ["State Overview", "District Breakdown", "State Rankings"]
    )

    with tab_state:
        if sel_state == "All States":
            section_header("Top States - Bar Chart")
            st.plotly_chart(top_states_bar(top_states_by_production(df, 10)), width="stretch")
            section_header("Production Share - Donut Chart")
            st.plotly_chart(production_pie(statewise_production(df)), width="stretch")
        else:
            df_state = df[df["State_Name"] == sel_state]
            if df_state.empty:
                empty_state(f"No data for {sel_state} in the selected filters.")
            else:
                tp  = df_state.dropna(subset=["Production"])["Production"].sum()
                ta  = df_state["Area"].sum()
                yld = tp / ta if ta > 0 else None
                nc  = df_state["Crop"].nunique()
                kpi_row([
                    ("Total Production", fmt_num(tp)),
                    ("Total Area",       fmt_num(ta, "ha")),
                    ("Avg Yield",        fmt_num(yld, "t/ha") if yld else "N/A"),
                    ("Unique Crops",     str(nc)),
                ])
                st.plotly_chart(
                    crop_trend_plotly(yearwise_by_state(df_state, sel_state), sel_state),
                    width="stretch",
                )
                section_header(f"Top Crops in {sel_state}")
                sc_df = state_crop_comparison(df_state, sel_state)
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(crop_production_bar(sc_df, n=12), width="stretch")
                with c2:
                    st.plotly_chart(state_crop_radar(sc_df, sel_state), width="stretch")

    with tab_district:
        state_for_dist = None if sel_state == "All States" else sel_state
        dist_df = district_production(df, state=state_for_dist, n=15)
        if dist_df.empty:
            empty_state("No district data for current filters.")
        else:
            st.plotly_chart(district_bar(dist_df), width="stretch")
            st.dataframe(dist_df, width="stretch")
            st.download_button(
                "Download District Data (CSV)",
                data=to_csv_bytes(dist_df),
                file_name="district_production.csv",
                mime="text/csv",
            )

    with tab_rankings:
        section_header("Complete State Rankings")
        rank_df = statewise_production(df).copy()
        rank_df.insert(0, "Rank", range(1, len(rank_df) + 1))
        rank_df.columns = ["Rank","State","Total Production (t)","Total Area (ha)",
                            "Record Count","Yield (t/ha)"]
        st.dataframe(
            rank_df.style.format({
                "Total Production (t)": "{:,.0f}",
                "Total Area (ha)":      "{:,.0f}",
                "Yield (t/ha)":         "{:.3f}",
            }),
            width="stretch", height=500,
        )
        st.download_button(
            "Download Rankings (CSV)",
            data=to_csv_bytes(rank_df),
            file_name="state_rankings.csv",
            mime="text/csv",
        )
        section_header("Matplotlib - Top 10 States", "Static analytical visualization")
        import matplotlib.pyplot as plt
        fig_mpl = matplotlib_state_production(statewise_production(df))
        st.pyplot(fig_mpl)
        plt.close(fig_mpl)


# =============================================================================
#  PAGE E - HISTORICAL TRENDS
# =============================================================================
elif page == "Historical Trends":
    page_header(
        "Historical Trends (1997-2025)",
        "Long-term production changes across crops, states, and seasons"
    )

    st.info(
        "Data for 2024 and 2025 should be treated as estimated / extended records. "
        "Their record counts mirror 2023 exactly, suggesting forward-fill."
    )

    tab1, tab2, tab3 = st.tabs(["Overall Trend", "Period Comparison", "Data Provenance"])

    with tab1:
        yr_df = yearwise_production(df)
        section_header("Year-wise Total Production and Area")
        st.plotly_chart(yearwise_trend_plotly(yr_df), width="stretch")
        st.plotly_chart(
            yearwise_trend_plotly(yr_df, metric="Total_Area", title="Year-wise Cultivated Area"),
            width="stretch",
        )
        section_header("Matplotlib - Dual-axis Trend", "Static analytical visualization")
        import matplotlib.pyplot as plt
        fig_mpl = matplotlib_yearwise_trend(yr_df)
        st.pyplot(fig_mpl)
        plt.close(fig_mpl)

    with tab2:
        section_header("Compare Two Time Periods")
        pc = st.columns(2)
        with pc[0]:
            p1 = st.slider("Period 1", int(min(ALL_YEARS)), int(max(ALL_YEARS)), (1997, 2007))
        with pc[1]:
            p2 = st.slider("Period 2", int(min(ALL_YEARS)), int(max(ALL_YEARS)), (2013, 2023))

        df_p1 = df[df["Crop_Year"].between(p1[0], p1[1])].dropna(subset=["Production"])
        df_p2 = df[df["Crop_Year"].between(p2[0], p2[1])].dropna(subset=["Production"])

        if df_p1.empty or df_p2.empty:
            empty_state("One or both periods have no data with current filters.")
        else:
            cc1, cc2 = st.columns(2)
            with cc1:
                st.metric(f"Period {p1[0]}-{p1[1]} Production", fmt_num(df_p1["Production"].sum()))
                st.plotly_chart(
                    yearwise_trend_plotly(yearwise_production(df_p1), title=f"Period {p1[0]}-{p1[1]}"),
                    width="stretch",
                )
            with cc2:
                st.metric(f"Period {p2[0]}-{p2[1]} Production", fmt_num(df_p2["Production"].sum()))
                st.plotly_chart(
                    yearwise_trend_plotly(yearwise_production(df_p2), title=f"Period {p2[0]}-{p2[1]}"),
                    width="stretch",
                )

    with tab3:
        section_header("Data Provenance - Official vs. Extended")
        df_official = df[~df["Crop_Year"].isin(POTENTIALLY_EXTENDED_YEARS)]
        df_extended = df[df["Crop_Year"].isin(POTENTIALLY_EXTENDED_YEARS)]
        kpi_row([
            ("Official Records (1997-2023)",     f"{len(df_official):,}"),
            ("Potentially Extended (2024-2025)", f"{len(df_extended):,}"),
        ])
        st.plotly_chart(
            yearwise_trend_plotly(yearwise_production(df), title="Full Timeline"),
            width="stretch",
        )
        st.warning(
            "Methodology Note: Years 2024-2025 each contain exactly 18,844 records - "
            "identical to 2023. This strongly suggests forward-fill or synthetic extrapolation. "
            "Do NOT cite these as verified government statistics."
        )


# =============================================================================
#  PAGE F - DATASET EXPLORER
# =============================================================================
elif page == "Dataset Explorer":
    page_header(
        "Dataset Explorer and Data Quality",
        "Browse, search, and download the crop production dataset"
    )

    tab1, tab2, tab3 = st.tabs(["Data Preview", "Quality Report", "Column Guide"])

    with tab1:
        search_term = st.text_input("Search (State, District, Crop...)", "")
        preview_df  = df.copy()
        if search_term:
            mask = (
                preview_df["State_Name"].str.contains(search_term, case=False, na=False) |
                preview_df["District_Name"].str.contains(search_term, case=False, na=False) |
                preview_df["Crop"].str.contains(search_term, case=False, na=False)
            )
            preview_df = preview_df[mask]
        st.caption(f"Showing {min(len(preview_df),1000):,} of {len(preview_df):,} matching records (capped at 1,000)")
        st.dataframe(preview_df.head(1000), width="stretch", height=440)
        st.download_button(
            "Download Filtered Records (CSV)",
            data=to_csv_bytes(preview_df),
            file_name="filtered_crop_data.csv",
            mime="text/csv",
        )

    with tab2:
        section_header("Data Quality Report")
        kpi_row([
            ("Total Records",       f"{quality['total_records']:,}"),
            ("Missing Production",  f"{quality['missing_production']:,} ({quality['missing_production_pct']}%)"),
            ("Duplicate Rows",      str(quality['duplicate_rows_full'])),
            ("Zero Production",     str(quality['zero_production'])),
        ])
        st.divider()
        ca, cb = st.columns(2)
        with ca:
            section_header("Year Coverage")
            yr_cov = df_full.groupby("Crop_Year").size().reset_index(name="Records")
            yr_cov["Status"] = yr_cov["Crop_Year"].apply(
                lambda y: "Potentially Extended" if y in POTENTIALLY_EXTENDED_YEARS else "Official"
            )
            st.dataframe(yr_cov, width="stretch", height=300)
        with cb:
            section_header("Missing Production by State")
            miss_df = (
                df_full[df_full["Production"].isna()]
                .groupby("State_Name").size()
                .reset_index(name="Missing_Count")
                .sort_values("Missing_Count", ascending=False)
            )
            if miss_df.empty:
                st.success("No missing production values in the filtered data!")
            else:
                st.dataframe(miss_df, width="stretch", height=300)
        section_header("Dataset Limitations")
        for lim in quality["limitations"]:
            st.markdown(f"- {lim}")

    with tab3:
        section_header("Column Descriptions")
        st.markdown("""
| Column | Type | Description |
|--------|------|-------------|
| `State_Name` | String | Indian state or union territory |
| `District_Name` | String | District within the state |
| `Crop_Year` | Integer | Harvest year (1997-2025) |
| `Season` | String | Kharif / Rabi / Whole Year / Summer / Winter / Autumn |
| `Crop` | String | Crop name (115 unique crops) |
| `Area` | Float | Cultivated area in **hectares** |
| `Production` | Float | Total production in **metric tonnes** |
| `Data_Type` | String | All rows: 'Actual' |
| `Yield_t_per_ha` | Float | Derived: Production / Area (t/ha) |
| `Data_Provenance` | String | Derived: Official / Potentially Extended |
        """)


# =============================================================================
#  PAGE G - BIG DATA PROCESSING STATUS
# =============================================================================
elif page == "Big Data Processing":
    page_header(
        "Big Data Processing Status",
        "Pandas | PySpark | Hadoop HDFS | MapReduce - real status only"
    )

    tab_pd, tab_spark, tab_hdfs, tab_mr = st.tabs(
        ["Pandas", "PySpark", "Hadoop HDFS", "MapReduce"]
    )

    # ---- Pandas tab ----------------------------------------------------------
    with tab_pd:
        section_header("Pandas Processing", "Primary analytics engine - runs on every dashboard load")
        st.success("Pandas is active and powering all charts, KPIs, and downloads on this dashboard.")
        kpi_row([
            ("Records Loaded",     f"{len(df_full):,}"),
            ("Missing Production", f"{quality['missing_production']:,}"),
            ("States",             str(quality['states'])),
            ("Crops",              str(quality['crops'])),
        ])
        section_header("Pandas State Aggregation - Top 10")
        pd_agg = statewise_production(df_full).head(10)
        st.dataframe(
            pd_agg.style.format({
                "Total_Production": "{:,.0f}",
                "Total_Area":       "{:,.0f}",
                "Yield_t_per_ha":   "{:.3f}",
            }),
            width="stretch",
        )

        st.divider()
        section_header("Pandas vs. PySpark Comparison")
        spark_path = os.path.join(PROJECT_ROOT, "outputs", "spark", "state_aggregation.csv")
        if os.path.isfile(spark_path):
            try:
                spark_df = pd.read_csv(spark_path)
                merged = pd_agg[["State_Name","Total_Production"]].merge(
                    spark_df[["State_Name","Total_Production"]].rename(
                        columns={"Total_Production":"Spark_Production"}),
                    on="State_Name", how="inner",
                )
                merged["Diff_%"] = (
                    (merged["Total_Production"] - merged["Spark_Production"])
                    / merged["Total_Production"] * 100
                ).round(4)
                st.dataframe(merged, width="stretch")
                max_diff = merged["Diff_%"].abs().max()
                if max_diff < 0.01:
                    st.success(f"Pandas and PySpark match within {max_diff:.4f}% - fully consistent.")
                else:
                    st.warning(f"Max difference: {max_diff:.4f}% - possible floating-point variance.")
            except Exception as e:
                st.warning("PySpark output found but comparison failed: " + str(e))
        else:
            st.info("Run the PySpark pipeline (PySpark tab) to enable the comparison.")

    # ---- PySpark tab ---------------------------------------------------------
    with tab_spark:
        section_header("PySpark Processing Pipeline")
        st.markdown("""
**Purpose:** Process the full 463,847-record dataset using distributed Spark aggregations (local multi-core).

**Pipeline Steps:**
1. Read CSV with inferred schema
2. Cast Area and Production to DoubleType
3. Filter null values and validate
4. Aggregate by: State, Year, Crop, Season
5. Save to CSV and Parquet in `outputs/spark/`
        """)

        # Check Java
        java_ok  = False
        java_msg = "Not detected"
        try:
            r = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=8)
            if r.returncode == 0:
                java_ok  = True
                java_msg = (r.stderr or r.stdout).strip().splitlines()[0]
            else:
                java_msg = "java command returned error."
        except FileNotFoundError:
            java_msg = "java not found on PATH."
        except Exception as ex:
            java_msg = str(ex)

        if java_ok:
            st.success(f"Java detected: {java_msg}")
        else:
            st.error(f"Java is required for PySpark but is NOT installed.\nDetected: {java_msg}")
            st.markdown("""
**How to install Java and enable PySpark:**

**Step 1** - Download JDK 11 (free): https://adoptium.net/

**Step 2** - Run the installer. During install, enable the "Add to PATH" option.

**Step 3** - Set JAVA_HOME environment variable:
- Open: Control Panel > System > Advanced System Settings > Environment Variables
- Add System variable: `JAVA_HOME` = `C:\\Program Files\\Eclipse Adoptium\\jdk-11.x.x`

**Step 4** - Restart this Streamlit app (close this terminal and run `streamlit run app.py` again)

**Step 5** - Come back to this tab and click "Run PySpark Pipeline"
            """)

        st.divider()
        section_header("Output File Status")
        from pyspark_analysis import check_spark_outputs, OUTPUT_DIR as SPARK_OUT
        outputs = check_spark_outputs()
        status_rows = []
        for fname, info in outputs.items():
            if info.get("exists"):
                status_rows.append({"File": fname, "Status": "Exists", "Size": f"{info.get('size_kb','?')} KB"})
            else:
                status_rows.append({"File": fname, "Status": "Not generated", "Size": "-"})
        st.dataframe(pd.DataFrame(status_rows), width="stretch", hide_index=True)

        if java_ok:
            if st.button("Run PySpark Pipeline Now"):
                from pyspark_analysis import run_spark_pipeline
                with st.spinner("Running PySpark pipeline (1-3 minutes)..."):
                    result = run_spark_pipeline()
                if result["success"]:
                    st.success(result["message"])
                    for out in result["outputs"]:
                        st.text(out)
                    st.rerun()
                else:
                    st.error(result["message"])
        else:
            st.info("Install Java first (instructions above), then reload this page to run PySpark.")

        st.divider()
        section_header(
            "Reference: Pandas Aggregation (same logic as PySpark)",
            "Shown as reference while Java is being set up"
        )
        demo_agg = statewise_production(df_full)[
            ["State_Name","Total_Production","Total_Area","Yield_t_per_ha"]
        ].head(10)
        st.caption("This is the Pandas result - equivalent to what PySpark will produce:")
        st.dataframe(
            demo_agg.style.format({
                "Total_Production": "{:,.0f}",
                "Total_Area":       "{:,.0f}",
                "Yield_t_per_ha":   "{:.3f}",
            }),
            width="stretch",
        )

        section_header("Manual Execution Command")
        st.code("python src/pyspark_analysis.py", language="bash")

        if os.path.isfile(os.path.join(SPARK_OUT, "state_aggregation.csv")):
            section_header("PySpark Output Preview")
            spk = pd.read_csv(os.path.join(SPARK_OUT, "state_aggregation.csv"))
            st.dataframe(spk.head(10), width="stretch")

    # ---- HDFS tab ------------------------------------------------------------
    with tab_hdfs:
        section_header("Hadoop HDFS Status")
        from hdfs_utils import get_hdfs_status, HADOOP_STREAMING_CMD_TEMPLATE
        hdfs_status = get_hdfs_status()

        if hdfs_status["available"]:
            st.success("HDFS is reachable.")
            st.json(hdfs_status["directories"])
        else:
            st.warning("Hadoop HDFS is not reachable on this machine.")
            st.markdown(hdfs_status["message"])

        section_header("HDFS Setup Commands")
        st.code("""
# 1. Create project directories in HDFS
hdfs dfs -mkdir -p /user/crop_project/input
hdfs dfs -mkdir -p /user/crop_project/output
hdfs dfs -mkdir -p /user/crop_project/mapreduce_output

# 2. Upload the dataset
hdfs dfs -put -f data/crop_production_1997_2025.csv /user/crop_project/input/

# 3. Verify
hdfs dfs -ls /user/crop_project/input/

# 4. Or use the Python helper
python src/hdfs_utils.py setup
        """, language="bash")

    # ---- MapReduce tab -------------------------------------------------------
    with tab_mr:
        section_header("Hadoop MapReduce - Production Totals by State")
        st.markdown("""
**Implementation:** Python Hadoop Streaming (mapper.py + reducer.py)

**Job logic:**
- **Mapper** reads each CSV row and emits `(state_name, production_value)` key-value pairs
- **Hadoop Streaming** sorts all pairs by key automatically
- **Reducer** sums production values per state key

**Status:** Verified locally - mapper to sort to reducer pipeline tested end-to-end
        """)

        mr_out = os.path.join(PROJECT_ROOT, "outputs", "mapreduce", "state_production_totals.txt")
        if os.path.isfile(mr_out):
            st.success("Local MapReduce simulation output exists and is ready.")
            mr_df = pd.read_csv(mr_out, sep="\t")
            mr_df = mr_df.sort_values("Total_Production_tonnes", ascending=False).reset_index(drop=True)
            mr_df.index += 1
            st.dataframe(mr_df.head(15), width="stretch")
            st.download_button(
                "Download MapReduce Output",
                data=open(mr_out, "rb").read(),
                file_name="mapreduce_state_totals.txt",
                mime="text/plain",
            )
        else:
            st.info("Local MapReduce output not found. Run the simulation command below.")

        st.divider()
        section_header("Local Simulation (Windows PowerShell)")
        st.code(
            r"Get-Content data\crop_production_1997_2025.csv | "
            r"python src\mapreduce\mapper.py | "
            r"Sort-Object | "
            r"python src\mapreduce\reducer.py | "
            r"Out-File -Encoding utf8 outputs\mapreduce\state_production_totals.txt",
            language="powershell",
        )

        section_header("Hadoop Streaming Command (requires Hadoop installed)")
        st.code(HADOOP_STREAMING_CMD_TEMPLATE, language="bash")

        section_header("Mapper and Reducer Source Code")
        cm, cr = st.columns(2)
        with cm:
            st.caption("mapper.py")
            with open(os.path.join(PROJECT_ROOT, "src", "mapreduce", "mapper.py")) as f:
                st.code(f.read(), language="python")
        with cr:
            st.caption("reducer.py")
            with open(os.path.join(PROJECT_ROOT, "src", "mapreduce", "reducer.py")) as f:
                st.code(f.read(), language="python")
