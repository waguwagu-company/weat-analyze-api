from typing import List, Optional, Annotated
from pydantic import BaseModel, Field

class CategorySetting(BaseModel):
    categoryId: Optional[int] = None
    categoryName: Optional[str] = None
    categoryTagId: Optional[int] = None
    categoryTagName: Optional[str] = None
    isPreferred: Optional[bool] = None

class MemberSetting(BaseModel):
    memberId: int
    xPosition: Optional[float] = None
    yPosition: Optional[float] = None
    roadnameAddress: Optional[str] = None
    categoryList: Annotated[List[CategorySetting], Field(default_factory=list)]
    inputText: Optional[str]

class AIAnalysisRequest(BaseModel):
    groupId: str
    analysisId: int
    memberSettingList: Annotated[List[MemberSetting], Field(default_factory=list)]