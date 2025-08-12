from typing import Optional
from pydantic import BaseModel, Field

class PipelineJob(BaseModel):
    pipeline_job_id: Optional[int] = None
    pipeline_id: int = Field(..., description="파이프라인식별자 (FK)")
    pipeline_job_name: Optional[str] = Field(default=None, max_length=50, description="파이프라인작업명")
    pipeline_job_description: Optional[str] = Field(default=None, description="파이프라인작업설명")
    pipeline_job_order: Optional[int] = Field(default=None, description="파이프라인작업순서")