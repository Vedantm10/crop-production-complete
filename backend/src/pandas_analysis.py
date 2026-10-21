"""
pandas_analysis.py
------------------
Core analytical aggregations using Pandas.
All functions return DataFrames ready for charting.
"""

import pandas as pd
import numpy as np


def top_states_by_production(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N states by total production (excluding missing values)."""
    return (
        df.dropna(subset=["Production"])
        .groupby("State_Name", as_index=False)["Production"]
        .sum()
        .sort_values("Production", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def yearwise_production(df: pd.DataFrame) -> pd.DataFrame:
    """Year-wise total production and area."""
    return (
        df.dropna(subset=["Production"])
        .groupby("Crop_Year", as_index=False)
        .agg(
            Total_Production=("Production", "sum"),
            Total_Area=("Area", "sum"),
            Record_Count=("Production", "count"),
        )
        .sort_values("Crop_Year")
    )


def cropwise_production(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Top N crops by total production."""
    return (
        df.dropna(subset=["Production"])
        .groupby("Crop", as_index=False)["Production"]
        .sum()
        .sort_values("Production", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def seasonal_production(df: pd.DataFrame) -> pd.DataFrame:
    """Total production and area by season."""
    return (
        df.dropna(subset=["Production"])
        .groupby("Season", as_index=False)
        .agg(
            Total_Production=("Production", "sum"),
            Total_Area=("Area", "sum"),
        )
        .sort_values("Total_Production", ascending=False)
    )


def statewise_production(df: pd.DataFrame) -> pd.DataFrame:
    """Production, area, and yield by state."""
    agg = (
        df.dropna(subset=["Production"])
        .groupby("State_Name", as_index=False)
        .agg(
            Total_Production=("Production", "sum"),
            Total_Area=("Area", "sum"),
            Record_Count=("Production", "count"),
            District_Count=("District_Name", "nunique"),
            Crop_Count=("Crop", "nunique"),
        )
        .sort_values("Total_Production", ascending=False)
    )
    agg["Yield_t_per_ha"] = agg.apply(
        lambda r: r["Total_Production"] / r["Total_Area"] if r["Total_Area"] > 0 else None,
        axis=1,
    )
    return agg


def district_production(df: pd.DataFrame, state: str = None, n: int = 15) -> pd.DataFrame:
    """Top N districts by total production, optionally filtered by state."""
    filtered = df.dropna(subset=["Production"])
    if state and state != "All States":
        filtered = filtered[filtered["State_Name"] == state]
    agg = (
        filtered
        .groupby(["State_Name", "District_Name"], as_index=False)
        .agg(
            Production=("Production", "sum"),
            Total_Production=("Production", "sum"),
            Area=("Area", "sum"),
            Total_Area=("Area", "sum"),
            Record_Count=("Production", "count"),
            Crop_Count=("Crop", "nunique"),
        )
        .sort_values("Production", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )
    agg["Yield_t_per_ha"] = agg.apply(
        lambda r: r["Total_Production"] / r["Total_Area"] if r["Total_Area"] and r["Total_Area"] > 0 else None,
        axis=1,
    )
    return agg


def crop_trend(df: pd.DataFrame, crop: str) -> pd.DataFrame:
    """Year-wise production trend for a specific crop."""
    return (
        df[df["Crop"] == crop]
        .dropna(subset=["Production"])
        .groupby("Crop_Year", as_index=False)
        .agg(
            Total_Production=("Production", "sum"),
            Total_Area=("Area", "sum"),
        )
        .sort_values("Crop_Year")
    )


def state_crop_comparison(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """Top crops for a given state."""
    return (
        df[df["State_Name"] == state]
        .dropna(subset=["Production"])
        .groupby("Crop", as_index=False)["Production"]
        .sum()
        .sort_values("Production", ascending=False)
        .head(12)
        .reset_index(drop=True)
    )


def yearwise_by_state(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """Year-wise production for a specific state."""
    return (
        df[df["State_Name"] == state]
        .dropna(subset=["Production"])
        .groupby("Crop_Year", as_index=False)
        .agg(
            Total_Production=("Production", "sum"),
            Total_Area=("Area", "sum"),
        )
        .sort_values("Crop_Year")
    )


def compare_multiple_crops(df: pd.DataFrame, crops: list) -> pd.DataFrame:
    """Year-wise production for multiple crops — useful for comparison charts."""
    return (
        df[df["Crop"].isin(crops)]
        .dropna(subset=["Production"])
        .groupby(["Crop_Year", "Crop"], as_index=False)["Production"]
        .sum()
        .sort_values(["Crop_Year", "Crop"])
    )


def season_crop_breakdown(df: pd.DataFrame, crop: str = None) -> pd.DataFrame:
    """Production by season and crop."""
    filtered = df.dropna(subset=["Production"])
    if crop and crop != "All Crops":
        filtered = filtered[filtered["Crop"] == crop]
    return (
        filtered.groupby(["Season", "Crop"], as_index=False)["Production"]
        .sum()
        .sort_values("Production", ascending=False)
    )


def production_distribution_by_state(df: pd.DataFrame, year: int = None) -> pd.DataFrame:
    """State-level production shares for the given year (or all years)."""
    filtered = df.dropna(subset=["Production"])
    if year:
        filtered = filtered[filtered["Crop_Year"] == year]
    return (
        filtered.groupby("State_Name", as_index=False)["Production"]
        .sum()
        .sort_values("Production", ascending=False)
    )


def compare_pandas_pyspark(pandas_agg: pd.DataFrame, spark_path: str) -> pd.DataFrame:
    """Load a PySpark output CSV and compare aggregates with pandas results."""
    try:
        spark_df = pd.read_csv(spark_path)
        return pandas_agg.merge(spark_df, on="State_Name", suffixes=("_pandas", "_spark"))
    except FileNotFoundError:
        return pd.DataFrame({"error": ["PySpark output not found. Run pyspark_analysis.py first."]})
