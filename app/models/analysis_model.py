from __future__ import annotations
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CategoryVote(BaseModel):
    preferred: int = 0
    non_preferred: int = 0


class BasePosition(BaseModel):
    x: float
    y: float


class PreprocessResult(BaseModel):
    groupId: str
    isGroup: bool
    memberCount: int
    basePosition: BasePosition
    categoryPreference: Dict[str, CategoryVote]
    inputTextSummarySource: List[str]


class GroupPreferenceSummary(BaseModel):
    categoryResponse: List[str] = Field(default_factory=list)
    inputTextResponse: str = ""


class ReviewWithScore(BaseModel):
    text: Optional[str] = None
    score: Optional[float] = None
    author: Optional[str] = None


class Place(BaseModel):
    placeId: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    reviews: List[ReviewWithScore] = Field(default=None)
    photos: List[str] = Field(default=None)
    score: Optional[float] = None
    topReviews: List[ReviewWithScore] = Field(default=None)
    # 임시 추가
    analysisBasis: Optional[str] = None  # REVIEW or AI
    aiMessage: Optional[str] = None


class AnalysisBasis(BaseModel):
    analysisBasisType: str
    analysisBasisContent: str


class PlaceResponse(BaseModel):
    placeName: Optional[str] = None
    placeRoadNameAddress: Optional[str] = None
    placeImageList: List[Dict[str, str]] = Field(default=None)


class AnalysisResultDetail(BaseModel):
    place: PlaceResponse
    analysisResultDetailContent: str
    analysisBasisList: List[AnalysisBasis]


class AnalysisResponse(BaseModel):
    groupId: str
    analysisResult: Dict[str, List[AnalysisResultDetail]]