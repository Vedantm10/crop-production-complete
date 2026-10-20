"""
data_loader.py
--------------
Cached data loading layer for the Streamlit dashboard.
Provides a single cleaned DataFrame that all pages share.
"""

import streamlit as st
import pandas as pd
import sys
import os

# Make src importable when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from data_cleaning import load_raw, clean, quality_report, DATA_PATH


@st.cache_data(show_spinner=False)
def get_dataframe() -> pd.DataFrame:
    """Load and clean the crop production CSV. Cached for the session."""
    raw = load_raw(DATA_PATH)
    return clean(raw)


@st.cache_data(show_spinner=False)
def get_quality_report() -> dict:
    """Return the data quality report. Cached for the session."""
    df = get_dataframe()
    return quality_report(df)


def apply_filters(
    df: pd.DataFrame,
    years: list = None,
    states: list = None,
    crops: list = None,
    seasons: list = None,
) -> pd.DataFrame:
    """Return a filtered view of the DataFrame based on user selections."""
    filtered = df.copy()
    if years:
        filtered = filtered[filtered["Crop_Year"].isin(years)]
    if states:
        filtered = filtered[filtered["State_Name"].isin(states)]
    if crops:
        filtered = filtered[filtered["Crop"].isin(crops)]
    if seasons:
        filtered = filtered[filtered["Season"].isin(seasons)]
    return filtered


def get_all_years(df: pd.DataFrame) -> list:
    return sorted(df["Crop_Year"].dropna().unique().tolist())


def get_all_states(df: pd.DataFrame) -> list:
    return sorted(df["State_Name"].dropna().unique().tolist())


def get_all_crops(df: pd.DataFrame) -> list:
    return sorted(df["Crop"].dropna().unique().tolist())


def get_all_seasons(df: pd.DataFrame) -> list:
    return sorted(df["Season"].dropna().unique().tolist())
