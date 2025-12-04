# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file and override existing env vars
load_dotenv(override=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-12345'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///food_ordering.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False