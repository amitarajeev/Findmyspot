import os
import json
from functools import lru_cache
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import requests

from app.config.config import Config
from app.utils import haversine_m

# ------------------------------------
# LocationIQ Autocomplete + Geocode
# ------------------------------------
LIQ_AUTOCOMPLETE_URL = "https://us1.locationiq.com/v1/autocomplete"
LIQ_SEARCH_URL = "https://us1.locationiq.com/v1/search"

def _liq_key() -> str:
    return os.getenv("LOCATIONIQ_API_KEY", Config.LOCATIONIQ_API_KEY)

def liq_autocomplete(q: str, limit: int = 5) -> List[Dict[str, Any]]:
    if not q:
        return []
    params = {
        "key": _liq_key(),
        "q": q,
        "limit": limit,
        "countrycodes": "au",
        "dedupe": 1,
        "normalizeaddress": 1,
        "format": "json"
    }
    r = requests.get(LIQ_AUTOCOMPLETE_URL, params=params, timeout=8)
    r.raise_for_status()
    rows = r.json()
    return [
        {
            "display_name": r0.get("display_name"),
            "lat": float(r0.get("lat")),
            "lon": float(r0.get("lon")),
            "type": r0.get("type")
        }
        for r0 in rows if "lat" in r0 and "lon" in r0
    ]

def liq_geocode(q: str) -> Optional[Dict[str, Any]]:
    if not q:
        return None
    params = {
        "key": _liq_key(),
        "q": q,
        "countrycodes": "au",
        "limit": 1,
        "format": "json",
        "normalizeaddress": 1
    }
    r = requests.get(LIQ_SEARCH_URL, params=params, timeout=8)
    r.raise_for_status()
    js = r.json()
    if not js:
        return None
    top = js[0]
    return {
        "display_name": top.get("display_name"),
        "lat": float(top["lat"]),
        "lon": float(top["lon"]),
        "type": top.get("type")
    }

# ------------------------------------
# Load data files
# ------------------------------------
@lru_cache(maxsize=1)
def load_sensors() -> pd.DataFrame:
    df = pd.read_csv(Config.BAY_SENSORS_DATA)
    df.columns = df.columns.str.strip()
    return df

@lru_cache(maxsize=1)
def load_bays() -> pd.DataFrame:
    df = pd.read_excel(Config.PARKING_BAYS_DATA)
    df.columns = df.columns.str.strip()
    return df

@lru_cache(maxsize=1)
def load_zone_links() -> pd.DataFrame:
    df = pd.read_csv(Config.PARKING_ZONES_DATA)
    df.columns = df.columns.str.strip()
    return df

@lru_cache(maxsize=1)
def load_sign_plates() -> pd.DataFrame:
    df = pd.read_csv(Config.SIGN_PLATES_DATA)
    df.columns = df.columns.str.strip()
    return df

@lru_cache(maxsize=1)
def load_zone_map() -> Dict[str, str]:
    try:
        with open(Config.ZONE_LOCATIONS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

# ------------------------------------
# English description formatter
# ------------------------------------
def generate_signplate_descriptions(df: pd.DataFrame) -> List[str]:
    descriptions = []
    for _, row in df.iterrows():
        days = row.get("Days", "")
        start = row.get("StartTime", "")
        end = row.get("EndTime", "")
        duration = row.get("Duration", "")
        permit = row.get("Permit", "")

        sentence = f"You can park here on {days}"
        if start and end:
            sentence += f" from {start} to {end}"
        if duration:
            sentence += f" for {duration.lower()}"
        if permit and permit.strip().lower() != "none":
            sentence += f" with permit {permit}"
        descriptions.append(sentence)
    return descriptions

# ------------------------------------
# Main Logic: Find bays near lat/lon
# ------------------------------------
def find_nearby_bays(lat: float, lon: float, radius: float = 0.001):
    bays_df = load_bays()
    sensors_df = load_sensors()
    sign_df = load_sign_plates()
    zone_links_df = load_zone_links()

    # Filter bays using bounding box radius
    nearby_bays = bays_df[
        (np.abs(bays_df["Latitude"] - lat) < radius) &
        (np.abs(bays_df["Longitude"] - lon) < radius)
    ]

    if nearby_bays.empty:
        return {"error": "No bays found near given coordinates."}

    kerbside_ids = nearby_bays["KerbsideID"].astype(str).tolist()
    sensors_df["KerbsideID"] = sensors_df["KerbsideID"].astype(str)

    match_sensors = sensors_df[sensors_df["KerbsideID"].isin(kerbside_ids)]
    zone_numbers = match_sensors["Zone_Number"].astype(str).unique().tolist()

    # Count occupancy
    available = (match_sensors["Status_Description"].str.lower() == "unoccupied").sum()
    occupied = (match_sensors["Status_Description"].str.lower() == "present").sum()

    # Map KerbsideID → RoadSegmentID → Segment_ID → ParkingZone
    bays_df["KerbsideID"] = bays_df["KerbsideID"].astype(str)
    zone_links_df["Segment_ID"] = zone_links_df["Segment_ID"].astype(str)
    sign_df["ParkingZone"] = sign_df["ParkingZone"].astype(str)

    matching_segments = bays_df[bays_df["KerbsideID"].isin(kerbside_ids)][["KerbsideID", "RoadSegmentID"]]
    matching_segments["RoadSegmentID"] = matching_segments["RoadSegmentID"].astype(str)

    matched_zones = pd.merge(
        matching_segments,
        zone_links_df[["Segment_ID", "ParkingZone"]],
        left_on="RoadSegmentID",
        right_on="Segment_ID",
        how="left"
    )

    matched_zones = matched_zones.dropna(subset=["ParkingZone"])
    matched_zone_ids = matched_zones["ParkingZone"].unique().astype(str).tolist()

    matching_signs = sign_df[sign_df["ParkingZone"].astype(str).isin(matched_zone_ids)]

    return {
        "bays_found": int(len(nearby_bays)),
        "available_bays": int(available),
        "occupied_bays": int(occupied),
        "zones": [str(z) for z in zone_numbers],
        "restrictions": matching_signs.to_dict(orient="records"),
        "restrictions_pretty": generate_signplate_descriptions(matching_signs)
    }


# ------------------------------------
# Prediction Model Integration
# ------------------------------------
def _now_day_type() -> str:
    wd = datetime.now().weekday()
    return "saturday" if wd == 5 else "sunday" if wd == 6 else "weekday"

def attach_predictions(bays: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from app.ml_model.ml_predictor import predict_by_zone
    zone_map = load_zone_map()
    hour_now = datetime.now().hour
    day_type = _now_day_type()

    for b in bays:
        pred_block, err = None, None
        z = b.get("zone") or b.get("zone_number") or b.get("ZoneNumber")

        # Skip if zone is None or NaN
        if z is None or str(z).lower() == "nan":
            b["prediction"] = None
            b["prediction_error"] = "Zone is missing or invalid"
            continue

        try:
            zone_id = int(float(z))  # e.g., '7539.0' → 7539
        except Exception:
            b["prediction"] = None
            b["prediction_error"] = f"Invalid zone format: {z}"
            continue

        try:
            # Try prediction
            pred_block, err = predict_by_zone(zone_id, hour_now, day_type)

            # Fallback to string version if zone not in zone_map
            zone_name = zone_map.get(str(zone_id), f"Zone {zone_id}")
            b["zone"] = str(zone_id)
            b["zone_name"] = zone_name

        except Exception as e:
            pred_block, err = None, str(e)

        b["prediction"] = pred_block
        b["prediction_error"] = err

    return bays
