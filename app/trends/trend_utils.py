# app/trends/trend_utils.py
import os
import pandas as pd
from typing import List, Dict, Any

from app.config.config import Config

def _read_table(path: str) -> pd.DataFrame:
    if path.lower().endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    df.columns = df.columns.str.strip()
    return df

# ---- Population ----

def load_population_df() -> pd.DataFrame:
    try:
        return _read_table(Config.POPULATION_DATA)
    except Exception:
        return pd.DataFrame()

def filter_population(start_year: int | None, end_year: int | None) -> List[Dict[str, Any]]:
    df = load_population_df()
    if df.empty:
        return []
    if start_year is not None and "Year" in df.columns:
        df = df[df["Year"] >= int(start_year)]
    if end_year is not None and "Year" in df.columns:
        df = df[df["Year"] <= int(end_year)]
    return df.to_dict(orient="records")

# ---- Vehicles ----

def load_vehicle_df() -> pd.DataFrame:
    try:
        return _read_table(Config.VEHICLE_DATA)
    except Exception:
        return pd.DataFrame()

def filter_vehicles(vehicle_type: str | None, start_year: int | None, end_year: int | None, suburb: str | None) -> List[Dict[str, Any]]:
    df = load_vehicle_df()
    if df.empty:
        return []
    if vehicle_type and "Vehicle_Type" in df.columns:
        df = df[df["Vehicle_Type"].astype(str).str.lower() == vehicle_type.lower()]
    if suburb and "Suburb" in df.columns:
        df = df[df["Suburb"].astype(str).str.lower() == suburb.lower()]
    if start_year is not None and "Year" in df.columns:
        df = df[df["Year"] >= int(start_year)]
    if end_year is not None and "Year" in df.columns:
        df = df[df["Year"] <= int(end_year)]
    return df.to_dict(orient="records")
