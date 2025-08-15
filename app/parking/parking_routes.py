# app/parking/parking_routes.py
import requests
from flask import Blueprint, request, jsonify
from datetime import datetime
import pandas as pd
from geopy.distance import geodesic

from app.parking.parking_utils import (
    liq_autocomplete, liq_geocode, find_nearby_bays, attach_predictions
)
from app.utils import as_bool
from app.config.config import Config

# legacy model endpoints preserved
from app.ml_model.ml_predictor import (
    predict_by_zone, predict_many_by_zone, predict_by_location
)

parking_bp = Blueprint("parking", __name__)

# ---------- New address-first flow ----------

@parking_bp.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    if not Config.LOCATIONIQ_API_KEY:
        return jsonify({"error": "Missing LocationIQ API key"}), 500

    # Melbourne CBD bounding box (tight bounds to restrict results)
    bbox = {
        "left": 144.9510,   # min longitude (West)
        "top": -37.8060,    # max latitude (North)
        "right": 144.9750,  # max longitude (East)
        "bottom": -37.8260  # min latitude (South)
    }

    # LocationIQ Autocomplete API URL with bounding box + normalization
    url = (
        f"https://api.locationiq.com/v1/autocomplete"
        f"?key={Config.LOCATIONIQ_API_KEY}"
        f"&q={query}"
        f"&format=json"
        f"&bounded=1"
        f"&viewbox={bbox['left']},{bbox['top']},{bbox['right']},{bbox['bottom']}"
        f"&normalizecity=1"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        suggestions = response.json()

        # Filter out only the essential info (you can expand this as needed)
        simplified_results = []
        for item in suggestions:
            simplified_results.append({
                "display_name": item.get("display_name"),
                "lat": item.get("lat"),
                "lon": item.get("lon"),
                "road": item.get("address", {}).get("road", ""),
                "house_number": item.get("address", {}).get("house_number", ""),
                "postcode": item.get("address", {}).get("postcode", ""),
                "suburb": item.get("address", {}).get("suburb", ""),
            })

        return jsonify(simplified_results)

    except requests.exceptions.RequestException as e:
        print(f"[LocationIQ Error] {e}")
        return jsonify({
            "error": "Failed to fetch autocomplete results",
            "details": str(e)
        }), 500
    
@parking_bp.get("/geocode")
def api_geocode():
    q = request.args.get("q", "", type=str)
    try:
        match = liq_geocode(q)
        if not match:
            return jsonify({"q": q, "match": None}), 404
        return jsonify({"q": q, "match": match}), 200
    except Exception as e:
        return jsonify({"error": f"geocode failed: {e}"}), 500

@parking_bp.get("/find")
def api_find_nearby():
    """
    Main endpoint for nearby parking bays, with predictions and sign plates.
    """
    address = request.args.get("address", type=str)
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    radius = request.args.get("radius", default=200, type=int)
    include_predictions = as_bool(request.args.get("include_predictions"), default=True)

    if address and (lat is None or lon is None):
        match = liq_geocode(address)
        if not match:
            return jsonify({"error": "Address not found"}), 404
        lat, lon = match["lat"], match["lon"]

    if lat is None or lon is None:
        return jsonify({"error": "Provide either address or lat & lon"}), 400

    try:
        result = find_nearby_bays(lat, lon, radius=radius / 1000.0)  # result is a dict
        if include_predictions and "zones" in result:
            zones = [{"zone": z} for z in result["zones"]]
            result["zones"] = attach_predictions(zones)
        payload = {
            "center": {"lat": lat, "lon": lon},
            "radius_m": radius,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "result": result
        }
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": f"search failed: {e}"}), 500

# ---------- Legacy endpoints (kept so nothing breaks) ----------

@parking_bp.get("/realtime")
def api_realtime_by_zone():
    """
    Legacy: /api/parking/realtime?zone_number=1234&only_available=true
    We aggregate sensor rows that match the zone* column if present.
    """
    import pandas as pd
    import os

    zone_number = request.args.get("zone_number", type=int)
    only_available = as_bool(request.args.get("only_available"), default=False)

    if zone_number is None:
        return jsonify({"error": "Missing 'zone_number' parameter"}), 400

    try:
        file_path = Config.BAY_SENSORS_DATA
        if not os.path.exists(file_path):
            return jsonify({"error": f"Sensor data file not found: {file_path}"}), 500

        df = pd.read_csv(file_path) if file_path.lower().endswith(".csv") else pd.read_excel(file_path)
        df.columns = df.columns.str.strip().str.lower()

        zone_col = next((c for c in ["zone_number", "zone", "zoneid", "zone_id", "zonenumber"] if c in df.columns), None)
        lat_col = next((c for c in ["latitude", "lat"] if c in df.columns), None)
        lon_col = next((c for c in ["longitude", "lon", "lng"] if c in df.columns), None)
        status_col = next((c for c in ["status_description", "status", "occupancy", "available", "is_occupied", "current_status"] if c in df.columns), None)

        if not zone_col:
            return jsonify({"zone_number": zone_number, "items": [], "note": "No valid zone column found"}), 200

        rows = df[df[zone_col] == zone_number].copy()
        if rows.empty:
            return jsonify({"zone_number": zone_number, "items": []}), 200

        if only_available and status_col:
            ok_vals = {"free", "available", "vacant", "unoccupied", "0", "false"}  # "Unoccupied" → available
            rows = rows[rows[status_col].astype(str).str.lower().isin(ok_vals)]

        items = []
        for _, r in rows.iterrows():
            items.append({
                "lat": float(r[lat_col]) if lat_col and not pd.isna(r[lat_col]) else None,
                "lon": float(r[lon_col]) if lon_col and not pd.isna(r[lon_col]) else None,
                "status": r[status_col] if status_col and not pd.isna(r[status_col]) else None
            })

        return jsonify({
            "zone_number": zone_number,
            "count": len(items),
            "items": items
        }), 200

    except Exception as e:
        return jsonify({"error": f"realtime failed: {e}"}), 500
@parking_bp.get("/predict")
def api_predict_by_zone():
    """
    Legacy: /api/parking/predict?zone_number=1234&hour=17&day_type=weekday
    """
    zone_number = request.args.get("zone_number", type=int)
    hour = request.args.get("hour", type=int, default=datetime.now().hour)
    day_type = request.args.get("day_type", type=str, default="weekday")
    if zone_number is None:
        return jsonify({"error": "missing zone_number"}), 400

    data, err = predict_by_zone(zone_number, hour, day_type)
    if err:
        return jsonify({"error": err}), 400
    return jsonify(data), 200

@parking_bp.get("/predict_many")
def api_predict_many():
    zone_number = request.args.get("zone_number", type=int)
    hour = request.args.get("hour", type=int, default=datetime.now().hour)
    day_type = request.args.get("day_type", type=str, default="weekday")
    hours_ahead = request.args.get("hours_ahead", type=int, default=3)
    if zone_number is None:
        return jsonify({"error": "missing zone_number"}), 400

    data, err = predict_many_by_zone(zone_number, hour, day_type, hours_ahead=hours_ahead)
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"zone_number": zone_number, "items": data}), 200
