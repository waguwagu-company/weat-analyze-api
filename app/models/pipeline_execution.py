from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class PipelineExecution(BaseModel):
    pipeline_execution_id: Optional[int] = None
    pipeline_id: int = Field(..., description="파이프라인식별자 (FK)")
    analysis_id: int = Field(..., description="분석식별자 (FK)")
    pipeline_execution_status: Optional[str] = Field(default=None, max_length=50, description="파이프라인진행상태")
    pipeline_execution_stage: Optional[int] = Field(default=None, description="파이프라인진행단계")
    pipeline_execution_start_time: Optional[datetime] = Field(default=None, description="파이프라인시작시간")
    pipeline_execution_end_time: Optional[datetime] = Field(default=None, description="파이프라인종료시간")
    pipeline_execution_duration: Optional[int] = Field(default=None, description="파이프라인소요시간(초 등 단위 통일 권장)")