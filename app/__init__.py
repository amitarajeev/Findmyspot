from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # Allow cross-origin access (for WordPress frontend)

    # Epic 1 endpoints
    from .routes import main
    app.register_blueprint(main)
    
    # Epic 2 endpoints (Parking APIs)
    from .parking_routes import parking_api
    app.register_blueprint(parking_api)

    return app
