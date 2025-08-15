from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal

class AnalysisBasisType(str, Enum):
    REVIEW = "REVIEW"
    AI = "AI"

class AIMessageTemplate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    ai_message_template_id: int
    ai_message_template_title: str
    ai_message_template_content: str
    ai_analysis_basis_type: List[Literal["REVIEW", "AI"]] = Field(default=None)