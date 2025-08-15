# app/trends/population_routes.py
from flask import Blueprint, request, jsonify
from app.trends.trend_utils import filter_population

population_bp = Blueprint("population", __name__)

@population_bp.get("/trends")
def population_trends():
    start_year = request.args.get("start", type=int)
    end_year = request.args.get("end", type=int)
    data = filter_population(start_year, end_year)
    return jsonify({"count": len(data), "items": data}), 200
