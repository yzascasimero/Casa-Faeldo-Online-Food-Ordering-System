# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file and override existing env vars
load_dotenv(override=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False