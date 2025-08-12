from flask import Flask, jsonify
from flask_cors import CORS
import re

def create_app():
    app = Flask(__name__)

    CORS(
        app,
        resources={
            r"/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://localhost:3000",
                    "http://localhost:5000",
                    "https://deft-cucurucho-91fbf7.netlify.app",  # your Netlify site
                ],
                # "supports_credentials": True,  # uncomment if you use cookies/session auth
            }
        },
    )

    # Register your blueprints as before
    from .routes import main
    app.register_blueprint(main)

    from .parking_routes import parking_api
    app.register_blueprint(parking_api)

    @app.get("/")
    def index():
        return jsonify({"service": "FindMySpot API", "status": "ok", "docs": "/api"})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
