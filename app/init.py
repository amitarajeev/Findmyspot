# app/__init__.py
import os
from flask import Flask
from flask_cors import CORS

# IMPORTANT: we keep your structure & imports exactly as discussed
from app.routes import core_bp
from app.parking.parking_routes import parking_bp
from app.trends.population_routes import population_bp
from app.trends.vehicle_routes import vehicle_bp

def create_app():
    app = Flask(__name__)

    # CORS for frontend (Vite dev server and Render)
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=False
    )

    # JSON pretty for dev
    app.config["JSON_SORT_KEYS"] = False

    # Register blueprints with stable prefixes
    app.register_blueprint(core_bp, url_prefix="/api")
    app.register_blueprint(parking_bp, url_prefix="/api/parking")
    app.register_blueprint(population_bp, url_prefix="/api/population")
    app.register_blueprint(vehicle_bp, url_prefix="/api/vehicles")

    @app.route("/")
    def index():
        return "FindMySpot backend is running. Try /api/health", 200

    return app
