from flask import Flask, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Existing blueprints
    from .routes import main
    app.register_blueprint(main)

    from .parking_routes import parking_api
    app.register_blueprint(parking_api)

    # NEW: simple root and health endpoints
    @app.get("/")
    def index():
        return jsonify({
            "service": "FindMySpot API",
            "status": "ok",
            "docs": "/api",
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
