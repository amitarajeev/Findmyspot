# app/parking_utils.py
import os
import pandas as pd
import json
from typing import Optional, Dict, Any, Tuple

# ---------------- constants/paths ----------------
# keep data paths as you had (they were working)
DATA_DIR = "data"

# make the ML-model folder path robust regardless of CWD
BASE_DIR = os.path.dirname(__file__)                 # -> app/
ML_MODEL_DIR = os.path.join(BASE_DIR, "ml_model")    # -> app/ml_model
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

# ---------------- try importing the predictor ----------------
_HAS_ML = True
_ML_IMPORT_ERR = None
try:
    # when running as a package (e.g. `python -m findmyspot.run`)
    from .ml_predictor import predict_by_zone  # we only need this here
except Exception as e1:
    try:
        # when running as a script from repo root (older style)
        from ml_predictor import predict_by_zone
    except Exception as e2:
        _HAS_ML = False
        _ML_IMPORT_ERR = f"{e1!s} | {e2!s}"

# ---------------- dataset loaders (unchanged) ----------------
def load_datasets():
    sensors = pd.read_csv(SENSORS_PATH)
    bays    = pd.read_excel(BAYS_PATH)
    zones   = pd.read_csv(ZONES_PATH)
    plates  = pd.read_csv(PLATES_PATH)
    return sensors, bays, zones, plates

# ---------------- realtime (unchanged) ----------------
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
        "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]],
    }

# ---------------- historical (unchanged) ----------------
def get_historical_parking_by_hour(zone_number: Optional[int] = None, day_type: str = "Weekday") -> Dict[str, Any]:
    sensors, bays, _, _ = load_datasets()
    merged = pd.merge(sensors, bays, on="KerbsideID", how="left")

    if zone_number:
        merged = merged[merged["Zone_Number"] == int(zone_number)]

    # Robust datetime parsing
    if "Status_Timestamp" not in merged.columns:
        return {
            "error": "Status_Timestamp column not found in sensors dataset.",
            "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]],
        }

    merged["timestamp"] = pd.to_datetime(merged["Status_Timestamp"], errors="coerce", utc=True)
    merged = merged.dropna(subset=["timestamp"])
    if merged.empty:
        return {
            "zone_number": zone_number,
            "availability_by_hour": {},
            "note": "No rows with parsable timestamps.",
            "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]],
        }

    # Local time (best-effort)
    try:
        merged["local_ts"] = merged["timestamp"].dt.tz_convert("Australia/Melbourne")
    except Exception:
        merged["local_ts"] = merged["timestamp"]

    merged["hour"] = merged["local_ts"].dt.hour
    merged["weekday"] = merged["local_ts"].dt.weekday

    # Normalize status string for robust filtering
    if "Status_Description" not in merged.columns:
        return {
            "error": "Status_Description column not found in sensors dataset.",
            "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]],
        }
    merged["Status_Description"] = merged["Status_Description"].astype(str).str.strip()

    # Day filter
    d = (day_type or "weekday").strip().lower()
    if d == "weekday":
        merged = merged[merged["weekday"] < 5]
    elif d == "saturday":
        merged = merged[merged["weekday"] == 5]
    elif d == "sunday":
        merged = merged[merged["weekday"] == 6]

    if merged.empty:
        return {
            "zone_number": zone_number,
            "availability_by_hour": {},
            "note": f"No rows for day_type={day_type}.",
            "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]],
        }

    # Count bays marked as some form of "unoccupied"
    mask_unocc = merged["Status_Description"].str.lower().str.contains("unoccupied", na=False)
    hourly = (
        merged[mask_unocc]
        .groupby("hour")["KerbsideID"]
        .nunique()  # unique bays free in that hour
        .to_dict()
    )

    return {
        "zone_number": zone_number,
        "availability_by_hour": hourly,
        "source": [DATASET_SOURCES["sensors"], DATASET_SOURCES["bays"]],
    }


# ---------------- prediction (ONLY this part is new) ----------------
def get_predicted_parking(zone_number: Optional[int] = None, hour: Optional[int] = None, day_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Try live LSTM prediction first (via ml_predictor.predict_by_zone).
    If unavailable or it fails, fall back to app/ml_model/findmyspot_results.json.
    """
    # 1) live model
    if _HAS_ML and zone_number is not None and hour is not None and day_type:
        try:
            result, err = predict_by_zone(int(zone_number), int(hour), str(day_type))
            if err is None and result is not None:
                return {
                    "predictions": [{
                        "Zone_Number": int(zone_number),
                        "hour": int(hour),
                        "day_type": result["day_type"],
                        "predicted_availability": result["predicted_availability"],
                        "available_spots": result["available_spots"],
                        "status": result["status"],
                        "confidence_score": result["confidence_score"],
                        "location": result["location"],
                    }],
                    "count": 1,
                    "source": "LSTM_AI (findmyspot_model.pth)"
                }
        except Exception:
            pass  # swallow and fall back

    # 2) JSON fallback (robust path)
    try:
        with open(PREDICTION_RESULTS_PATH, "r") as f:
            preds = json.load(f)
    except FileNotFoundError:
        # give a useful hint if the ml path failed
        msg = "Prediction results file not found."
        if not _HAS_ML and _ML_IMPORT_ERR:
            msg += f" (ml_predictor import failed: {_ML_IMPORT_ERR})"
        return {"error": msg, "source": "AI Model"}

    # Normalize inputs for comparison
    zone_str = str(zone_number) if zone_number is not None else None
    hour_str = str(hour) if hour is not None else None
    day_str  = str(day_type).lower() if day_type else None

    all_predictions = preds.get("predictions", [])

    # ---------- Handle both formats ----------
    if isinstance(all_predictions, list):
        # ---- original expected list-of-dicts format ----
        if not zone_str and not hour_str and not day_str:
            return {"predictions": all_predictions, "source": "AI Model + " + DATASET_SOURCES["sensors"]}

        filtered = []
        for entry in all_predictions:
            # entry is a dict (expected)
            entry_zone = str(entry.get("Zone_Number")).split(".")[0] if entry.get("Zone_Number") is not None else None
            entry_hour = str(entry.get("hour")) if entry.get("hour") is not None else None
            entry_day  = str(entry.get("day_type", "")).lower()

            if zone_str and entry_zone != zone_str: continue
            if hour_str and entry_hour != hour_str: continue
            if day_str and entry_day  != day_str:  continue

            filtered.append(entry)

        if not filtered:
            return {"error": "No prediction found for specified parameters.", "source": "AI Model + " + DATASET_SOURCES["sensors"]}

        return {
            "predictions": filtered,
            "count": len(filtered),
            "source": "Pre-generated predictions (" + os.path.basename(PREDICTION_RESULTS_PATH) + ")"
        }

    elif isinstance(all_predictions, dict):
        # ---- training JSON shape: {"y_test": [...], "locations": [...] } ----
        # Synthesize a single meaningful row from api_examples.prediction
        demo = preds.get("api_examples", {}).get("prediction")
        if isinstance(demo, dict):
            loc_name = demo.get("location")
            items = demo.get("predictions", [])
            if isinstance(items, list) and items:
                it = items[0]  # just use the first demo item
                mapped = {
                    "Zone_Number": int(zone_number) if zone_number is not None else None,
                    "hour": int(hour) if hour is not None else None,
                    "day_type": day_type if day_type is not None else None,
                    "predicted_availability": it.get("predicted_availability"),
                    "available_spots": it.get("available_spots"),
                    "status": it.get("status"),
                    "confidence_score": it.get("confidence_score"),
                    "location": loc_name,
                }
                return {
                    "predictions": [mapped],
                    "count": 1,
                    "source": "Pre-generated demo (api_examples in findmyspot_results.json)"
                }

        # If we get here, we can't produce a compatible row
        return {
            "error": "Pre-generated predictions are not in the expected list format.",
            "hint": "Your JSON has {'predictions': {...}} from training; expected a list of row objects.",
            "source": "AI Model + " + DATASET_SOURCES["sensors"]
        }

    else:
        # Unknown structure
        return {
            "error": f"Unexpected predictions type: {type(all_predictions).__name__}",
            "source": "AI Model + " + DATASET_SOURCES["sensors"]
        }

# ---------------- rules/zones (unchanged) ----------------
def get_zone_rules(parking_zone: int) -> Dict[str, Any]:
    plates = pd.read_csv(PLATES_PATH)
    rules  = plates[plates["ParkingZone"] == int(parking_zone)]
    return {
        "ParkingZone": parking_zone,
        "rules": rules.to_dict(orient="records"),
        "source": [DATASET_SOURCES["plates"]],
    }

def get_zones_by_street(on_street: str) -> Dict[str, Any]:
    zones = pd.read_csv(ZONES_PATH)
    matched = zones[zones["OnStreet"].str.contains(on_street, case=False, na=False)]
    return {
        "zones": matched["ParkingZone"].unique().tolist(),
        "source": [DATASET_SOURCES["zones"]],
    }
