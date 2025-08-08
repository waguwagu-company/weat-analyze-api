from typing import List, Optional
from pydantic import BaseModel


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