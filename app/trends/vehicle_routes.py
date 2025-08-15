# app/trends/vehicle_routes.py
from flask import Blueprint, request, jsonify
from app.trends.trend_utils import filter_vehicles

vehicle_bp = Blueprint("vehicles", __name__)

@vehicle_bp.get("/trends")
def vehicle_trends():
    vehicle_type = request.args.get("type")
    start_year = request.args.get("start", type=int)
    end_year   = request.args.get("end", type=int)
    suburb     = request.args.get("suburb")
    data = filter_vehicles(vehicle_type, start_year, end_year, suburb)
    return jsonify({"count": len(data), "items": data}), 200
