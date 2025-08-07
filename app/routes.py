from flask import Blueprint, request, jsonify
from .utils import get_vehicle_growth_data, get_population_growth_data

# Create a blueprint
main = Blueprint('main', __name__)

@main.route('/api/vehicle-growth', methods=['GET'])
def vehicle_growth():
    """
    API Endpoint to return vehicle registration growth data.
    Optional query params:
      - start: start year (e.g., 2016)
      - end: end year (e.g., 2021)
    """
    try:
        # Get query params with default values
        start_year = int(request.args.get('start', 2016))
        end_year = int(request.args.get('end', 2021))

        data = get_vehicle_growth_data(start_year, end_year)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/api/population-growth', methods=['GET'])
def population_growth():
    """
    API Endpoint to return Melbourne CBD population growth data.
    Optional query params:
      - start: start year
      - end: end year
      - region: specific suburb/area
    """
    try:
        start_year = int(request.args.get('start', 2015))
        end_year = int(request.args.get('end', 2021))
        region = request.args.get('region')  # Optional

        data = get_population_growth_data(start_year, end_year, region)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500