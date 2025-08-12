from flask import Flask, jsonify
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__)

    # CORS — keep permissive for now; tighten to your Netlify/custom domain later.
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
    )

    # ---- Register blueprints (your existing modules) ----
    # Epic 1 endpoints
    from .routes import main
    app.register_blueprint(main)

    # Epic 2 endpoints (Parking APIs)
    from .parking_routes import parking_api
    app.register_blueprint(parking_api)

    # ---- Simple health check for deployments ----
    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    return app


# Expose a module-level WSGI application:
# This lets Gunicorn/Azure load it with "app:app"
app = create_app()
