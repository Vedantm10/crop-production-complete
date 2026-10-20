"""
visualizations.py
-----------------
Plotly and Matplotlib visualisation functions for the crop production dashboard.

All Plotly functions return plotly.graph_objects.Figure objects.
All Matplotlib functions return matplotlib.figure.Figure objects.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import json
import os

# ── Colour palette ──────────────────────────────────────────────────────────
EMERALD   = "#10b981"
DARK_GRN  = "#065f46"
MID_GRN   = "#059669"
LIME      = "#84cc16"
AMBER     = "#f59e0b"
ROSE      = "#f43f5e"
SLATE     = "#334155"
LIGHT_BG  = "#f8fafc"

SEQUENTIAL = [
    "#d1fae5", "#6ee7b7", "#34d399", "#10b981",
    "#059669", "#047857", "#065f46", "#022c22",
]

CROP_COLORS = px.colors.qualitative.Vivid
SEASON_COLORS = {
    "Kharif":     "#10b981",
    "Rabi":       "#3b82f6",
    "Whole Year": "#f59e0b",
    "Summer":     "#ef4444",
    "Winter":     "#8b5cf6",
    "Autumn":     "#ec4899",
}

PLOTLY_TEMPLATE = "plotly_white"

GEOJSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "india_states.geojson"
)

_geojson_cache: dict = None


def _load_geojson() -> dict:
    global _geojson_cache
    if _geojson_cache is None:
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            _geojson_cache = json.load(f)
    return _geojson_cache


def _fmt(val: float) -> str:
    """Format large numbers with M/B suffixes."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    if val >= 1e9:
        return f"{val/1e9:.2f} B"
    if val >= 1e6:
        return f"{val/1e6:.2f} M"
    if val >= 1e3:
        return f"{val/1e3:.1f} K"
    return f"{val:.1f}"


# ═══════════════════════════════════════════════════════════════════════════
# PLOTLY CHARTS
# ═══════════════════════════════════════════════════════════════════════════


def india_choropleth(
    map_df: pd.DataFrame,
    metric: str = "Production_sum",
    title: str = "India — Crop Production by State",
    selected_state: str = None,
) -> go.Figure:
    """
    Interactive choropleth map of India coloured by the chosen metric.

    Parameters
    ----------
    map_df : DataFrame with columns geojson_name, State_Name, Production_sum,
             Area_sum, Yield_t_per_ha, record_count
    metric : column to colour by (Production_sum | Area_sum | Yield_t_per_ha)
    title  : chart title
    selected_state : GeoJSON NAME_1 of the currently selected state (highlighted)
    """
    geojson = _load_geojson()

    metric_labels = {
        "Production_sum": "Production (tonnes)",
        "Area_sum":        "Cultivated Area (ha)",
        "Yield_t_per_ha":  "Yield (t/ha)",
    }
    metric_label = metric_labels.get(metric, metric)

    # Build tooltip
    map_df = map_df.copy()
    map_df["tooltip"] = map_df.apply(
        lambda r: (
            f"<b>{r['State_Name']}</b><br>"
            f"Production: {_fmt(r.get('Production_sum'))} t<br>"
            f"Area: {_fmt(r.get('Area_sum'))} ha<br>"
            f"Yield: {r['Yield_t_per_ha']:.2f} t/ha"
            if pd.notna(r.get("Yield_t_per_ha")) else
            f"<b>{r['State_Name']}</b><br>"
            f"Production: {_fmt(r.get('Production_sum'))} t<br>"
            f"Area: {_fmt(r.get('Area_sum'))} ha"
        ),
        axis=1,
    )

    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="geojson_name",
        featureidkey="properties.NAME_1",
        color=metric,
        hover_name="State_Name",
        hover_data={
            "geojson_name": False,
            "Production_sum": ":.0f",
            "Area_sum": ":.0f",
            "Yield_t_per_ha": ":.3f",
            "record_count": True,
            metric: False,
        },
        color_continuous_scale=SEQUENTIAL,
        labels={
            "Production_sum": "Production (t)",
            "Area_sum": "Area (ha)",
            "Yield_t_per_ha": "Yield (t/ha)",
            "record_count": "Records",
        },
        title=title,
        template=PLOTLY_TEMPLATE,
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor=LIGHT_BG,
    )

    fig.update_layout(
        height=550,
        margin=dict(l=0, r=0, t=45, b=0),
        coloraxis_colorbar=dict(
            title=metric_label,
            tickformat=".2s",
            len=0.7,
        ),
        font=dict(family="Inter, sans-serif", size=12),
        title_font_size=15,
        title_font_color=SLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Highlight selected state with a marker
    if selected_state and not map_df.empty:
        sel = map_df[map_df["geojson_name"] == selected_state]
        if not sel.empty:
            fig.add_annotation(
                text=f"▶ {selected_state}",
                xref="paper", yref="paper",
                x=0.02, y=0.95,
                showarrow=False,
                font=dict(color=EMERALD, size=13, family="Inter, sans-serif"),
                bgcolor="rgba(16,185,129,0.12)",
                bordercolor=EMERALD,
                borderwidth=1,
                borderpad=6,
            )

    return fig


def yearwise_trend_plotly(
    year_df: pd.DataFrame,
    metric: str = "Total_Production",
    title: str = "Year-wise Production Trend",
) -> go.Figure:
    """Line + area chart for year-wise trend."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=year_df["Crop_Year"],
        y=year_df[metric],
        mode="lines+markers",
        name=metric.replace("_", " "),
        line=dict(color=EMERALD, width=2.5),
        marker=dict(size=6, color=EMERALD),
        fill="tozeroy",
        fillcolor="rgba(16,185,129,0.12)",
        hovertemplate="<b>Year %{x}</b><br>" + metric.replace("_", " ") + ": %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Crop Year",
        yaxis_title="Production (metric tonnes)" if "Prod" in metric else "Area (ha)",
        template=PLOTLY_TEMPLATE,
        height=380,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=45, b=10),
    )
    return fig


def top_states_bar(state_df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal bar chart of top N states by production."""
    top = state_df.head(n).sort_values("Production", ascending=True)
    fig = px.bar(
        top,
        x="Production",
        y="State_Name",
        orientation="h",
        color="Production",
        color_continuous_scale=SEQUENTIAL,
        title=f"Top {n} States by Production",
        labels={"Production": "Total Production (t)", "State_Name": "State"},
        template=PLOTLY_TEMPLATE,
        text="Production",
    )
    fig.update_traces(
        texttemplate="%{x:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Production: %{x:,.0f} t<extra></extra>",
    )
    fig.update_layout(
        height=400,
        showlegend=False,
        coloraxis_showscale=False,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_tickformat=".2s",
    )
    return fig


def seasonal_comparison_plotly(season_df: pd.DataFrame) -> go.Figure:
    """Grouped bar: production and area by season."""
    colors = [SEASON_COLORS.get(s, EMERALD) for s in season_df["Season"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=season_df["Season"],
        y=season_df["Total_Production"],
        name="Production (t)",
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Production: %{y:,.0f} t<extra></extra>",
    ))
    fig.update_layout(
        title="Production by Season",
        xaxis_title="Season",
        yaxis_title="Total Production (metric tonnes)",
        template=PLOTLY_TEMPLATE,
        height=350,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=45, b=10),
        yaxis_tickformat=".2s",
    )
    return fig


def crop_production_bar(crop_df: pd.DataFrame, n: int = 15) -> go.Figure:
    """Horizontal bar chart of top N crops by production."""
    top = crop_df.head(n).sort_values("Production", ascending=True)
    fig = px.bar(
        top,
        x="Production",
        y="Crop",
        orientation="h",
        color="Production",
        color_continuous_scale=["#d1fae5", EMERALD, DARK_GRN],
        title=f"Top {n} Crops by Total Production",
        labels={"Production": "Total Production (t)", "Crop": "Crop"},
        template=PLOTLY_TEMPLATE,
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Production: %{x:,.0f} t<extra></extra>",
    )
    fig.update_layout(
        height=420,
        showlegend=False,
        coloraxis_showscale=False,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_tickformat=".2s",
    )
    return fig


def crop_trend_plotly(trend_df: pd.DataFrame, crop: str) -> go.Figure:
    """Line chart of year-wise production for a single crop."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_df["Crop_Year"],
        y=trend_df["Total_Production"],
        mode="lines+markers",
        name="Production",
        line=dict(color=EMERALD, width=2.5),
        marker=dict(size=7),
        fill="tozeroy",
        fillcolor="rgba(16,185,129,0.12)",
        hovertemplate="<b>%{x}</b><br>Production: %{y:,.0f} t<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["Crop_Year"],
        y=trend_df["Total_Area"],
        mode="lines+markers",
        name="Area (ha)",
        line=dict(color=AMBER, width=2, dash="dot"),
        marker=dict(size=5),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Area: %{y:,.0f} ha<extra></extra>",
    ))
    fig.update_layout(
        title=f"{crop} — Production & Area Trend",
        xaxis_title="Year",
        yaxis=dict(title="Production (t)", tickformat=".2s", color=EMERALD),
        yaxis2=dict(title="Area (ha)", overlaying="y", side="right", tickformat=".2s", color=AMBER),
        template=PLOTLY_TEMPLATE,
        height=380,
        legend=dict(x=0, y=1.1, orientation="h"),
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=45, b=10),
    )
    return fig


def multi_crop_trend(df_filtered: pd.DataFrame, crops: list) -> go.Figure:
    """Overlapping line chart comparing multiple crops."""
    fig = go.Figure()
    for i, crop in enumerate(crops):
        crop_data = df_filtered[df_filtered["Crop"] == crop]
        agg = crop_data.groupby("Crop_Year", as_index=False)["Production"].sum()
        fig.add_trace(go.Scatter(
            x=agg["Crop_Year"],
            y=agg["Production"],
            mode="lines+markers",
            name=crop,
            line=dict(width=2),
            hovertemplate=f"<b>{crop}</b><br>Year: %{{x}}<br>Production: %{{y:,.0f}} t<extra></extra>",
        ))
    fig.update_layout(
        title="Crop Production Comparison Over Years",
        xaxis_title="Year",
        yaxis_title="Production (t)",
        template=PLOTLY_TEMPLATE,
        height=400,
        legend=dict(x=0, y=1.1, orientation="h"),
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickformat=".2s",
    )
    return fig


def district_bar(district_df: pd.DataFrame) -> go.Figure:
    """Bar chart of top districts by production."""
    top = district_df.sort_values("Production", ascending=True)
    fig = px.bar(
        top,
        x="Production",
        y="District_Name",
        orientation="h",
        color="State_Name",
        title="Top Districts by Production",
        labels={"Production": "Total Production (t)", "District_Name": "District"},
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=CROP_COLORS,
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Production: %{x:,.0f} t<extra></extra>",
    )
    fig.update_layout(
        height=420,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_tickformat=".2s",
    )
    return fig


def production_pie(state_df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Donut chart of production share by top N states."""
    top = state_df.head(n)
    rest = state_df.iloc[n:]["Total_Production"].sum()
    labels = list(top["State_Name"]) + (["Others"] if rest > 0 else [])
    values = list(top["Total_Production"]) + ([rest] if rest > 0 else [])
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Production: %{value:,.0f} t<br>Share: %{percent}<extra></extra>",
        marker_colors=CROP_COLORS,
    ))
    fig.update_layout(
        title=f"Production Share — Top {n} States",
        height=380,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(x=1, y=0.5),
        margin=dict(l=10, r=10, t=45, b=10),
    )
    return fig


def area_vs_production_scatter(df: pd.DataFrame, sample: int = 3000) -> go.Figure:
    """Scatter plot of Area vs Production coloured by Season."""
    valid = df.dropna(subset=["Production", "Area"])
    valid = valid[valid["Area"] > 0]
    if len(valid) > sample:
        valid = valid.sample(sample, random_state=42)
    colors = [SEASON_COLORS.get(s, SLATE) for s in valid["Season"]]
    fig = px.scatter(
        valid,
        x="Area",
        y="Production",
        color="Season",
        hover_data=["State_Name", "Crop", "Crop_Year"],
        opacity=0.55,
        color_discrete_map=SEASON_COLORS,
        title="Cultivated Area vs. Production",
        labels={"Area": "Area (ha)", "Production": "Production (t)"},
        template=PLOTLY_TEMPLATE,
        log_x=True,
        log_y=True,
    )
    fig.update_layout(
        height=400,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def state_crop_radar(crop_df: pd.DataFrame, state: str) -> go.Figure:
    """Radar chart of top crops for a state."""
    top = crop_df.head(8)
    fig = go.Figure(go.Scatterpolar(
        r=top["Production"],
        theta=top["Crop"],
        fill="toself",
        fillcolor="rgba(16,185,129,0.25)",
        line=dict(color=EMERALD, width=2),
        hovertemplate="<b>%{theta}</b><br>Production: %{r:,.0f} t<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                tickformat=".2s",
            )
        ),
        title=f"{state} — Crop Radar",
        height=380,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def yield_boxplot(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Box plot of yield distribution for top N crops."""
    valid = df[(df["Area"] > 0) & df["Production"].notna()].copy()
    valid["Yield"] = valid["Production"] / valid["Area"]

    top_crops = valid.groupby("Crop")["Production"].sum().nlargest(top_n).index.tolist()
    valid = valid[valid["Crop"].isin(top_crops)]

    fig = px.box(
        valid,
        x="Crop",
        y="Yield",
        color="Crop",
        notched=True,
        title=f"Yield Distribution — Top {top_n} Crops",
        labels={"Yield": "Yield (t/ha)"},
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=CROP_COLORS,
    )
    fig.update_layout(
        height=420,
        showlegend=False,
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-30,
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# MATPLOTLIB CHARTS (static analytical visualizations)
# ═══════════════════════════════════════════════════════════════════════════

def matplotlib_yearwise_trend(year_df: pd.DataFrame) -> plt.Figure:
    """Matplotlib dual-axis line chart: production and area over years."""
    fig, ax1 = plt.subplots(figsize=(10, 4), facecolor=LIGHT_BG)
    ax1.set_facecolor(LIGHT_BG)

    ax1.plot(
        year_df["Crop_Year"], year_df["Total_Production"],
        color=EMERALD, linewidth=2.5, marker="o", markersize=4, label="Production (t)"
    )
    ax1.fill_between(year_df["Crop_Year"], year_df["Total_Production"],
                     alpha=0.12, color=EMERALD)
    ax1.set_xlabel("Crop Year", fontsize=10)
    ax1.set_ylabel("Total Production (t)", color=EMERALD, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=EMERALD)
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x/1e9:.1f}B" if x >= 1e9 else f"{x/1e6:.0f}M")
    )

    ax2 = ax1.twinx()
    ax2.plot(
        year_df["Crop_Year"], year_df["Total_Area"],
        color=AMBER, linewidth=2, linestyle="--", marker="s", markersize=3, label="Area (ha)"
    )
    ax2.set_ylabel("Total Area (ha)", color=AMBER, fontsize=10)
    ax2.tick_params(axis="y", labelcolor=AMBER)
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M")
    )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    ax1.set_title("Year-wise Production and Area Trend (1997–2025)", fontsize=12, pad=8, color=SLATE)
    plt.tight_layout()
    return fig


def matplotlib_seasonal_bar(season_df: pd.DataFrame) -> plt.Figure:
    """Matplotlib horizontal stacked bar: production by season."""
    fig, ax = plt.subplots(figsize=(8, 3.5), facecolor=LIGHT_BG)
    ax.set_facecolor(LIGHT_BG)
    colors = [SEASON_COLORS.get(s, EMERALD) for s in season_df["Season"]]
    bars = ax.barh(season_df["Season"], season_df["Total_Production"], color=colors, height=0.55)
    ax.set_xlabel("Total Production (metric tonnes)", fontsize=9)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e9:.1f}B" if x >= 1e9 else f"{x/1e6:.0f}M"))
    ax.set_title("Seasonal Production Comparison", fontsize=11, color=SLATE)
    for bar, val in zip(bars, season_df["Total_Production"]):
        ax.text(
            bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2,
            f"{val/1e9:.2f}B" if val >= 1e9 else f"{val/1e6:.1f}M",
            va="center", fontsize=8, color=SLATE
        )
    plt.tight_layout()
    return fig


def matplotlib_state_production(state_df: pd.DataFrame, n: int = 10) -> plt.Figure:
    """Matplotlib horizontal bar: top N states."""
    top = state_df.head(n).sort_values("Total_Production")
    cmap = LinearSegmentedColormap.from_list("grn", ["#d1fae5", EMERALD, DARK_GRN])
    norms = (top["Total_Production"] - top["Total_Production"].min()) / (
        top["Total_Production"].max() - top["Total_Production"].min() + 1
    )
    colors = [cmap(v) for v in norms]

    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=LIGHT_BG)
    ax.set_facecolor(LIGHT_BG)
    bars = ax.barh(top["State_Name"], top["Total_Production"], color=colors, height=0.6)
    ax.set_xlabel("Total Production (t)", fontsize=9)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e9:.1f}B" if x >= 1e9 else f"{x/1e6:.0f}M"))
    ax.set_title(f"Top {n} States by Production", fontsize=11, color=SLATE)
    plt.tight_layout()
    return fig
