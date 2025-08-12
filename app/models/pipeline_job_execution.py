from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PipelineJobExecution(BaseModel):
    pipeline_job_execution_id: Optional[int] = None
    pipeline_job_id: int = Field(..., description="파이프라인작업식별자 (FK)")
    analysis_id: int = Field(..., description="분석식별자 (FK)")
    job_execution_status: Optional[str] = Field(default=None, max_length=50, description="작업진행상태")
    job_execution_start_time: Optional[datetime] = Field(default=None, description="작업시작시간")
    job_execution_end_time: Optional[datetime] = Field(default=None, description="작업종료시간")
    job_execution_duration: Optional[int] = Field(default=None, description="작업소요시간(초)")
    job_execution_request_data: Optional[Dict[str, Any]] = Field(default=None, description="요청데이터(JSON)")
    job_execution_result_data: Optional[Dict[str, Any]] = Field(default=None, description="결과데이터(JSON)")