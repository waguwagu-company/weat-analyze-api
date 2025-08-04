from dotenv import load_dotenv
import os

load_dotenv()

CLOVA_API_KEY = os.getenv("CLOVA_API_KEY")
CLOVA_API_URL = os.getenv("CLOVA_API_URL")