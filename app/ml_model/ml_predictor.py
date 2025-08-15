import os
import json
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path

from app.config.config import Config  # Paths

ZONE_MAP_PATH = Path(Config.ZONE_LOCATIONS_PATH)

# Zone name loader
def _load_zone_map() -> Dict[str, str]:
    try:
        with open(ZONE_MAP_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Error] Failed to load zone map: {e}")
        return {}

# Helper: get datetime
def _next_datetime_for(day_type: str, hour: int) -> datetime:
    now = datetime.now()
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    day = day_map.get(day_type.lower(), now.weekday())
    days_ahead = (day - now.weekday()) % 7
    return (now + timedelta(days=days_ahead)).replace(hour=int(hour), minute=0, second=0, microsecond=0)

# 🔹 Fake prediction generator
def _fake_prediction() -> Dict[str, Any]:
    availability = round(random.uniform(0.2, 0.95), 3)
    available_spots = int(availability * 100)
    status = (
        "🟢 Good" if availability >= 0.6 else
        "🟡 Fair" if availability >= 0.3 else
        "🔴 Poor"
    )
    confidence = round(1 - 2 * abs(availability - 0.5), 2)
    return {
        "predicted_availability": availability,
        "available_spots": available_spots,
        "status": status,
        "confidence_score": confidence
    }

# Predict by location
def predict_by_location(location_name: str, hour: int, day_type: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        end_time = _next_datetime_for(day_type, int(hour))
        base = _fake_prediction()
        return {
            "location": location_name,
            "hour": hour,
            "day_type": day_type.capitalize(),
            **base
        }, None
    except Exception as e:
        return None, f"Prediction failed: {e}"

# Predict by zone
def predict_by_zone(zone_number: int, hour: int, day_type: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    zone_map = _load_zone_map()
    try:
        zone_id = str(int(zone_number))
    except Exception:
        return None, "Zone is missing or invalid"
    loc = zone_map.get(zone_id)
    if not loc:
        return None, f"Zone {zone_id} has no mapping in {ZONE_MAP_PATH.name}"
    return predict_by_location(loc, hour, day_type)

# Predict for multiple future hours
def predict_many_by_zone(zone_number: int, hour: int, day_type: str, hours_ahead: int = 3) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    zone_map = _load_zone_map()
    try:
        zone_id = str(int(zone_number))
    except Exception:
        return None, "Zone is missing or invalid"

    loc = zone_map.get(zone_id)
    if not loc:
        return None, f"Zone {zone_id} has no mapping in {ZONE_MAP_PATH.name}"

    start_dt = _next_datetime_for(day_type, int(hour))
    output = []
    for i in range(hours_ahead):
        end_time = start_dt + timedelta(hours=i)
        pred = _fake_prediction()
        output.append({
            "Zone_Number": int(zone_number),
            "hour": end_time.hour,
            "day_type": day_type.capitalize(),
            "location": loc,
            **pred
        })
    return output, None

# Health check
def health_check() -> Dict[str, Any]:
    zone_exists = os.path.exists(ZONE_MAP_PATH)
    return {
        "zone_map_file": str(ZONE_MAP_PATH),
        "zone_map_exists": zone_exists,
        "model_loaded": False,
        "preprocessor_loaded": False,
        "has_scaler": False,
        "has_location_encoder": False
    }
