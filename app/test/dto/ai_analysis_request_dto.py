from typing import List, Optional
from pydantic import BaseModel, Field


class Category(BaseModel):
    categoryId: int
    categoryName: str


class MemberSetting(BaseModel):
    memberId: int
    xPosition: Optional[float]
    yPosition: Optional[float]
    inputText: Optional[str]
    categoryList: List[Category] = Field(default_factory=list)


class AIAnalysisRequest(BaseModel):
    groupId: str
    memberSettingList: List[MemberSetting] = Field(default_factory=list)