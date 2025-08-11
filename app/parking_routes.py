from flask import Blueprint, request, jsonify
from .parking_utils import (
    get_realtime_parking,
    get_historical_parking_by_hour,
    get_predicted_parking,
    get_zone_rules,
    get_zones_by_street
)

parking_api = Blueprint("parking_api", __name__)

@parking_api.route("/api/parking/realtime", methods=["GET"])
def realtime_parking():
    zone_number = request.args.get("zone_number")
    only_available = request.args.get("only_available", "true").lower() == "true"
    data = get_realtime_parking(zone_number=zone_number, only_available=only_available)
    return jsonify(data), 200

@parking_api.route("/api/parking/historical", methods=["GET"])
def historical_parking():
    zone_number = request.args.get("zone_number")
    day_type = request.args.get("day_type", "Weekday")
    data = get_historical_parking_by_hour(zone_number=zone_number, day_type=day_type)
    return jsonify(data), 200

@parking_api.route("/api/parking/predict", methods=["GET"])
def predicted_parking():
    zone_number = request.args.get("zone_number")
    hour = request.args.get("hour", type=int)
    day_type = request.args.get("day_type")
    hours_ahead = request.args.get("hours_ahead", default=3, type=int)
    suggest_nearby = request.args.get("suggest_nearby", default="true").lower() == "true"
    max_suggestions = request.args.get("max_suggestions", default=3, type=int)
    radius_m = request.args.get("radius_m", default=600, type=int)

    data = get_predicted_parking(
        zone_number=zone_number,
        hour=hour,
        day_type=day_type,
        hours_ahead=hours_ahead,
        suggest_nearby=suggest_nearby,
        max_suggestions=max_suggestions,
        radius_m=radius_m
    )
    return jsonify(data), 200

@parking_api.route("/api/parking/zones", methods=["GET"])
def parking_zones():
    on_street = request.args.get("on_street")
    data = get_zones_by_street(on_street)
    return jsonify(data), 200

@parking_api.route("/api/parking/zone/<zone_id>/rules", methods=["GET"])
def zone_rules(zone_id):
    data = get_zone_rules(zone_id)
    return jsonify(data), 200
