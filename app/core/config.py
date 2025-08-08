from dotenv import load_dotenv
import os

load_dotenv()

CLOVA_API_KEY = os.getenv("CLOVA_API_KEY")
CLOVA_API_URL = os.getenv("CLOVA_API_URL")
GOOGLE_PLACES_API_KEY=os.getenv("GOOGLE_PLACES_API_KEY")
GOOGLE_PLACES_API_MODE=os.getenv("GOOGLE_PLACES_API_MODE")