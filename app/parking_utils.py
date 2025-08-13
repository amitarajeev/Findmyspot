# app/parking_utils.py
import os
import pandas as pd
import json
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
import math


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")  # <— FIX
ML_MODEL_DIR = os.path.join(BASE_DIR, "ml_model")
PREDICTION_RESULTS_PATH = os.path.join(ML_MODEL_DIR, "findmyspot_results.json")

SENSORS_PATH = os.path.join(DATA_DIR, "on_street_parking_bay_sensors_cleaned.csv")
BAYS_PATH    = os.path.join(DATA_DIR, "on_street_parking_bays_cleaned.xlsx")
ZONES_PATH   = os.path.join(DATA_DIR, "parking_zones_linked_to_street_segments_cleaned.csv")
PLATES_PATH  = os.path.join(DATA_DIR, "sign_plates_located_in_each_parking_zone_cleaned.csv")

DATASET_SOURCES = {
    "sensors": "https://data.melbourne.vic.gov.au/explore/dataset/on-street-parking-bay-sensors/information/",
    "bays":    "https://data.melbourne.vic.gov.au/explore/dataset/on-street-parking-bays/information/",
    "zones":   "http://data.melbourne.vic.gov.au/explore/dataset/parking-zones-linked-to-street-segments/information/",
    "plates":  "https://data.melbourne.vic.gov.au/explore/dataset/on-street-parking-bay-sensors/information/",
}

_HAS_ML = True
_ML_IMPORT_ERR = None
try:
    from .ml_predictor import predict_by_zone, predict_many_by_zone
except Exception as e1:
    try:
        from ml_predictor import predict_by_zone, predict_many_by_zone
    except Exception as e2:
        _HAS_ML = False
        _ML_IMPORT_ERR = f"{e1!s} | {e2!s}"

def load_datasets():
    sensors = pd.read_csv(SENSORS_PATH)
    bays    = pd.read_excel(BAYS_PATH)
    zones   = pd.read_csv(ZONES_PATH)
    plates  = pd.read_csv(PLATES_PATH)
    return sensors, bays, zones, plates

def get_realtime_parking(zone_number: Optional[int] = None, only_available: bool = True) -> Dict[str, Any]:
    sensors, bays, _, _ = load_datasets()
    if zone_number:
        sensors = sensors[sensors["Zone_Number"] == int(zone_number)]
    if only_available:
        sensors = sensors[sensors["Status_Description"].str.lower() == "unoccupied"]
    merged = pd.merge(sensors, bays, on="KerbsideID", how="left")
    merged = merged.dropna(subset=["RoadSegmentDescription", "KerbsideID", "Latitude_x", "Longitude_x"])
    if "Zone_Number" in sensors.columns and merged["Zone_Number"].isnull().any():
        merged["Zone_Number"] = merged["Zone_Number"].fillna(method="ffill").fillna(method="bfill")
    results = (
        merged[
            ["KerbsideID", "Zone_Number", "RoadSegmentDescription", "Latitude_x", "Longitude_x", "Status_Description"]
        ]
        .rename(columns={"Latitude_x": "Latitude", "Longitude_x": "Longitude"})
        .to_dict(orient="records")
    )
    return {
        "results": results,
        "count": len(results),
        "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]]
    }

def get_historical_parking_by_hour(zone_number: Optional[int] = None, day_type: str = "Weekday") -> Dict[str, Any]:
    sensors, bays, _, _ = load_datasets()
    merged = pd.merge(sensors, bays, on="KerbsideID", how="left")
    if zone_number:
        merged = merged[merged["Zone_Number"] == int(zone_number)]
    if "Status_Timestamp" not in merged.columns:
        return {"error": "Status_Timestamp column not found in sensors dataset.", "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]]}
    merged["timestamp"] = pd.to_datetime(merged["Status_Timestamp"], errors="coerce", utc=True)
    merged = merged.dropna(subset=["timestamp"])
    if merged.empty:
        return {"zone_number": zone_number, "availability_by_hour": {}, "note": "No rows with parsable timestamps.", "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]]}

    try:
        merged["local_ts"] = merged["timestamp"].dt.tz_convert("Australia/Melbourne")
    except Exception:
        merged["local_ts"] = merged["timestamp"]

    merged["hour"] = merged["local_ts"].dt.hour
    merged["weekday"] = merged["local_ts"].dt.weekday
    if "Status_Description" not in merged.columns:
        return {"error": "Status_Description column not found in sensors dataset.", "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]]}
    merged["Status_Description"] = merged["Status_Description"].astype(str).str.strip()

    d = (day_type or "weekday").strip().lower()
    if d == "weekday":
        merged = merged[merged["weekday"] < 5]
    elif d == "saturday":
        merged = merged[merged["weekday"] == 5]
    elif d == "sunday":
        merged = merged[merged["weekday"] == 6]

    if merged.empty:
        return {"zone_number": zone_number, "availability_by_hour": {}, "note": f"No rows for day_type={day_type}.", "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]]}

    mask_unocc = merged["Status_Description"].str.lower().str.contains("unoccupied", na=False)
    hourly = merged[mask_unocc].groupby("hour")["KerbsideID"].nunique().to_dict()
    return {"zone_number": zone_number, "availability_by_hour": hourly, "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]]}

def _status_from_rate(r: float) -> str:
    return "🟢 Good" if r >= 0.6 else "🟡 Fair" if r >= 0.3 else "🔴 Poor"

def _confidence_from_rate(r: float) -> float:
    return round(1 - 2 * abs(r - 0.5), 2)

def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl   = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def _zone_centroids(sensors: pd.DataFrame) -> pd.DataFrame:
    lat_col = "Latitude" if "Latitude" in sensors.columns else "Latitude_x"
    lon_col = "Longitude" if "Longitude" in sensors.columns else "Longitude_x"
    c = sensors.dropna(subset=["Zone_Number", lat_col, lon_col]).groupby("Zone_Number")[[lat_col, lon_col]].median().reset_index()
    return c.rename(columns={lat_col: "lat", lon_col: "lon"})

def _historical_rate_for_zone_hour(sensors: pd.DataFrame, zone_number: int, hour: int, day_type: str) -> Optional[float]:
    df = sensors[sensors["Zone_Number"] == int(zone_number)].copy()
    if df.empty or "Status_Timestamp" not in df.columns:
        return None
    df["timestamp"] = pd.to_datetime(df["Status_Timestamp"], errors="coerce", utc=True)
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        return None
    try:
        df["local_ts"] = df["timestamp"].dt.tz_convert("Australia/Melbourne")
    except Exception:
        df["local_ts"] = df["timestamp"]
    df["hour"] = df["local_ts"].dt.hour
    df["weekday"] = df["local_ts"].dt.weekday
    d = (day_type or "weekday").strip().lower()
    if d == "weekday":
        df = df[df["weekday"] < 5]
    elif d == "saturday":
        df = df[df["weekday"] == 5]
    elif d == "sunday":
        df = df[df["weekday"] == 6]
    df = df[df["hour"] == int(hour)]
    if df.empty:
        return None
    total_bays = df["KerbsideID"].nunique()
    if total_bays == 0:
        return None
    free = df[df["Status_Description"].astype(str).str.lower().str.contains("unoccupied", na=False)]["KerbsideID"].nunique()
    rate = free / float(total_bays)
    return max(0.0, min(1.0, float(rate)))

def get_predicted_parking(
    zone_number: Optional[int] = None,
    hour: Optional[int] = None,
    day_type: Optional[str] = None,
    hours_ahead: int = 3,
    suggest_nearby: bool = True,
    max_suggestions: int = 3,
    radius_m: int = 600
) -> Dict[str, Any]:
    if zone_number is None:
        return {"error": "zone_number is required for prediction", "source": "AI Model + datasets"}
    sensors, bays, zones, plates = load_datasets()
    hours_ahead = max(1, min(int(hours_ahead or 1), 3))
    if hour is None:
        hour = datetime.now().hour
    if not day_type:
        day_type = "Weekday"

    if _HAS_ML:
        try:
            rows, err = predict_many_by_zone(int(zone_number), int(hour), str(day_type), hours_ahead=hours_ahead)
            if err is None and rows is not None:
                predictions = rows
                source = "LSTM_AI (findmyspot_model.pth)"
            else:
                predictions = []
                source = "Historical fallback"
        except Exception:
            predictions = []
            source = "Historical fallback"
    else:
        predictions = []
        source = "Historical fallback"

    if not predictions:
        preds = []
        for i in range(hours_ahead):
            target_hour = (int(hour) + i) % 24
            rate = _historical_rate_for_zone_hour(sensors, int(zone_number), target_hour, str(day_type))
            if rate is None:
                continue
            preds.append({
                "Zone_Number": int(zone_number),
                "hour": target_hour,
                "day_type": (day_type or "weekday").capitalize(),
                "location": None,
                "predicted_availability": round(rate, 3),
                "available_spots": int(rate * 100),
                "status": _status_from_rate(rate),
                "confidence_score": _confidence_from_rate(rate)
            })
        if preds:
            predictions = preds
        else:
            try:
                with open(PREDICTION_RESULTS_PATH, "r") as f:
                    blob = json.load(f)
                demo = blob.get("api_examples", {}).get("prediction", {})
                items = demo.get("predictions", [])
                if items:
                    it = items[0]
                    predictions = [{
                        "Zone_Number": int(zone_number),
                        "hour": int(hour),
                        "day_type": (day_type or "weekday").capitalize(),
                        "location": demo.get("location"),
                        "predicted_availability": it.get("predicted_availability", 0.3),
                        "available_spots": it.get("available_spots", 30),
                        "status": it.get("status", _status_from_rate(0.3)),
                        "confidence_score": it.get("confidence_score", 0.6)
                    }]
                    source = "Pre-generated demo (api_examples in findmyspot_results.json)"
                else:
                    return {"error": "No prediction found for specified parameters.", "source": "AI Model + datasets"}
            except FileNotFoundError:
                msg = "Prediction results file not found."
                if not _HAS_ML and _ML_IMPORT_ERR:
                    msg += f" (ml_predictor import failed: {_ML_IMPORT_ERR})"
                return {"error": msg, "source": "AI Model + datasets"}

    suggestions: List[Dict[str, Any]] = []
    if suggest_nearby:
        c = _zone_centroids(sensors)
        this = c[c["Zone_Number"] == int(zone_number)]
        if not this.empty:
            lat0 = float(this.iloc[0]["lat"])
            lon0 = float(this.iloc[0]["lon"])
            c["dist_m"] = c.apply(lambda r: _haversine_m(lat0, lon0, r["lat"], r["lon"]), axis=1)
            nearby = c[(c["Zone_Number"] != int(zone_number)) & (c["dist_m"] <= int(radius_m))].sort_values("dist_m")
            nearby = nearby.head(max(5, max_suggestions * 2))
            for _, row in nearby.iterrows():
                zid = int(row["Zone_Number"])
                per_zone_preds: List[Dict[str, Any]] = []
                if _HAS_ML:
                    try:
                        rows, err = predict_many_by_zone(zid, int(hour), str(day_type), hours_ahead=hours_ahead)
                        if err is None and rows is not None:
                            per_zone_preds = rows
                    except Exception:
                        per_zone_preds = []
                if not per_zone_preds:
                    tmp = []
                    for i in range(hours_ahead):
                        hh = (int(hour) + i) % 24
                        r = _historical_rate_for_zone_hour(sensors, zid, hh, str(day_type))
                        if r is not None:
                            tmp.append({
                                "Zone_Number": zid,
                                "hour": hh,
                                "day_type": (day_type or "weekday").capitalize(),
                                "location": None,
                                "predicted_availability": round(r, 3),
                                "available_spots": int(r * 100),
                                "status": _status_from_rate(r),
                                "confidence_score": _confidence_from_rate(r)
                            })
                    per_zone_preds = tmp
                if per_zone_preds:
                    best = max(per_zone_preds, key=lambda d: d.get("predicted_availability", 0))
                    suggestions.append({
                        "zone_number": zid,
                        "distance_m": int(row["dist_m"]),
                        "best_hour": best["hour"],
                        "best_predicted_availability": best["predicted_availability"],
                        "predictions": per_zone_preds
                    })
        suggestions = sorted(suggestions, key=lambda s: (-s["best_predicted_availability"], s["distance_m"]))[:max_suggestions]

    return {
        "zone_number": int(zone_number),
        "requested_hour": int(hour),
        "day_type": (day_type or "weekday").capitalize(),
        "hours_ahead": hours_ahead,
        "predictions": predictions,
        "count": len(predictions),
        "suggested_zones": suggestions,
        "suggestion_count": len(suggestions),
        "source": source
    }

def get_zone_rules(parking_zone: int) -> Dict[str, Any]:
    plates = pd.read_csv(PLATES_PATH)
    rules  = plates[plates["ParkingZone"] == int(parking_zone)]
    return {"ParkingZone": parking_zone, "rules": rules.to_dict(orient="records"), "source": [DATASET_SOURCES["plates"]]}

def get_zones_by_street(on_street: str) -> Dict[str, Any]:
    zones = pd.read_csv(ZONES_PATH)
    matched = zones[zones["OnStreet"].str.contains(on_street, case=False, na=False)]
    return {"zones": matched["ParkingZone"].unique().tolist(), "source": [DATASET_SOURCES["zones"]]}
