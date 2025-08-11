import os

class Config:
    DEBUG = os.environ.get("DEBUG", "1") == "1"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    JSON_SORT_KEYS = False
