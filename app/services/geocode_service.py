import requests
from app.models.google_geocode_model import *
from app.core.config import GOOGLE_PLACES_API_KEY

def geocode_to_coordinate(address: str, language: str = "ko", region: str = "KR") -> Coordinate:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_PLACES_API_KEY,
        "language": language,
        "region": region,
    }

    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"Geocoding 실패: status={data.get('status')}")

    top = data["results"][0]
    lat = top["geometry"]["location"]["lat"]
    lng = top["geometry"]["location"]["lng"]

    return Coordinate(
        x=lat,
        y=lng,
        formattedAddress=top.get("formatted_address"),
        placeId=top.get("place_id"),
    )