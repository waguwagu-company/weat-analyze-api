from typing import List, Optional
from pydantic import BaseModel

class Photo(BaseModel):
    height: Optional[int]
    width: Optional[int]
    photo_reference: Optional[str]
    html_attributions: Optional[List[str]]


class PlaceDetailResult(BaseModel):
    name: Optional[str]
    photos: Optional[List[Photo]]


class PlaceDetailResponse(BaseModel):
    html_attributions: Optional[List[str]]
    result: Optional[PlaceDetailResult]
    status: Optional[str]