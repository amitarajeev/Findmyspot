from flask import Blueprint, request, jsonify
from .parking_utils import (
    get_realtime_parking,
    get_historical_parking_by_hour,
    get_predicted_parking,
    get_zone_rules,
    get_zones_by_street
)

parking_api = Blueprint("parking_api", __name__)

# 2.1 Real-time available parking, filter by zone if wanted
@parking_api.route("/api/parking/realtime", methods=["GET"])
def realtime_parking():
    zone_number = request.args.get("zone_number")  # e.g. 4002, optional
    only_available = request.args.get("only_available", "true").lower() == "true"
    data = get_realtime_parking(zone_number=zone_number, only_available=only_available)
    return jsonify(data), 200

# 2.3 Hourly historical trend for zone (defaults to all if not provided)
@parking_api.route("/api/parking/historical", methods=["GET"])
def historical_parking():
    zone_number = request.args.get("zone_number")  # e.g. 4002
    day_type = request.args.get("day_type", "Weekday")  # Weekday, Saturday, Sunday
    data = get_historical_parking_by_hour(zone_number=zone_number, day_type=day_type)
    return jsonify(data), 200

# 2.2 AI-predicted parking for zone, hour, day
@parking_api.route("/api/parking/predict", methods=["GET"])
def predicted_parking():
    zone_number = request.args.get("zone_number")  # e.g. 4002
    hour = request.args.get("hour")  # 0-23
    day_type = request.args.get("day_type")  # Weekday, Saturday, Sunday
    data = get_predicted_parking(zone_number=zone_number, hour=hour, day_type=day_type)
    return jsonify(data), 200

# Helper: get all parking zones by OnStreet
@parking_api.route("/api/parking/zones", methods=["GET"])
def parking_zones():
    on_street = request.args.get("on_street")  # e.g. "Lonsdale St"
    data = get_zones_by_street(on_street)
    return jsonify(data), 200

# Get all sign/rules for a ParkingZone
@parking_api.route("/api/parking/zone/<zone_id>/rules", methods=["GET"])
def zone_rules(zone_id):
    data = get_zone_rules(zone_id)
    return jsonify(data), 200
