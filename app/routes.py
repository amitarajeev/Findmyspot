# app/routes.py
from flask import Blueprint, jsonify
import os

core_bp = Blueprint("core", __name__)

@core_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@core_bp.get("/version")
def version():
    # surface a minimal version stub
    return jsonify({
        "name": "findmyspot-backend",
        "env": os.getenv("FLASK_ENV", "production")
    }), 200
