from pydantic import BaseModel, Field
from typing import Optional

class Pipeline(BaseModel):
    pipeline_id: Optional[int] = None
    pipeline_name: Optional[str] = Field(default=None, max_length=100)
    pipeline_description: Optional[str] = None