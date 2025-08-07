import os

class Config:
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default_key'
