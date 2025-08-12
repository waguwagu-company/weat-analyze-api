from dotenv import load_dotenv
import os

load_dotenv()

# Clova API Configuration
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY")
CLOVA_API_URL = os.getenv("CLOVA_API_URL")

# Google Places API Configuration
GOOGLE_PLACES_API_KEY=os.getenv("GOOGLE_PLACES_API_KEY")
GOOGLE_PLACES_API_MODE=os.getenv("GOOGLE_PLACES_API_MODE")

# Database Configuration
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")