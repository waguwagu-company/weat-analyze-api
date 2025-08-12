from typing import List, Optional
from pydantic import BaseModel


# ==== Google Place 장소 정보 조회 ====
class DisplayName(BaseModel):
    text: Optional[str] = None
    languageCode: Optional[str] = None


class ReviewText(BaseModel):
    text: Optional[str] = None
    languageCode: Optional[str] = None


class AuthorAttribution(BaseModel):
    displayName: Optional[str] = None
    uri: Optional[str] = None
    photoUri: Optional[str] = None


class Review(BaseModel):
    name: Optional[str] = None
    relativePublishTimeDescription: Optional[str] = None
    rating: Optional[int] = None
    text: Optional[ReviewText] = None
    originalText: Optional[ReviewText] = None
    authorAttribution: Optional[AuthorAttribution] = None
    publishTime: Optional[str] = None
    flagContentUri: Optional[str] = None
    googleMapsUri: Optional[str] = None


class Place(BaseModel):
    id: Optional[str] = None
    formattedAddress: Optional[str] = None
    priceLevel: Optional[str] = None
    userRatingCount: Optional[int] = None
    displayName: Optional[DisplayName] = None
    reviews: Optional[List[Review]] = None


class PlacesResponse(BaseModel):
    places: Optional[List[Place]] = None

    
    

# ==== Google Place 장소 세부 정보 조회 ====
class Photo(BaseModel):
    height: Optional[int]
    width: Optional[int]
    photo_reference: Optional[str]
    html_attributions: Optional[List[str]]


class PlaceDetailResult(BaseModel):
    name: Optional[str] = ""
    photos: Optional[List[Photo]]


class PlaceDetailResponse(BaseModel):
    html_attributions: Optional[List[str]]
    result: Optional[PlaceDetailResult]
    status: Optional[str]