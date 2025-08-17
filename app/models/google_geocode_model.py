from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class GeocodeLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    lat: float
    lng: float


class GeocodeGeometry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    location: GeocodeLocation


class GeocodeResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    formatted_address: Optional[str] = Field(default=None, alias="formatted_address")
    place_id: Optional[str] = Field(default=None, alias="place_id")
    geometry: GeocodeGeometry


class GeocodeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    results: List[GeocodeResult] = Field(default=None)
    status: str


class Coordinate(BaseModel):
    x: float
    y: float
    formattedAddress: Optional[str] = None
    placeId: Optional[str] = None
    source: str = "google_geocoding"


def get_coordinate(geo: GeocodeResponse) -> Coordinate:
    if geo.status != "OK" or not geo.results:
        raise ValueError(f"Geocoding 실패: status={geo.status}, results={len(geo.results)}")

    top = geo.results[0]
    lat = top.geometry.location.lat
    lng = top.geometry.location.lng

    return Coordinate(
        x=lat,
        y=lng,
        formattedAddress=top.formatted_address,
        placeId=top.place_id,
    )