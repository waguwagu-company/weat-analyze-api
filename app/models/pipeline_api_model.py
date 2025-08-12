from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PipelineExecutionStatusResponse(BaseModel):
    pipelineExecutionId: int
    pipelineId: int
    analysisId: int
    pipelineExecutionStatus: Optional[str] = None
    pipelineExecutionStage: Optional[int] = None
    pipelineExecutionStartTime: Optional[str] = None
    pipelineExecutionEndTime: Optional[str] = None
    pipelineExecutionDuration: Optional[int] = None

    currentPipelineJobOrder: Optional[int] = None
    currentPipelineJobName: Optional[str] = None

    pipelineJobExecutionIdList: List[int] = Field(default=None)
    pipelineJobExecutionOrderMap: Dict[str, int] = Field(default=None)

    # 프론트에서 라벨/상태 같이 보여줄 때 사용
    pipelineJobExecutionSummaryList: List["PipelineJobExecutionSummary"] = Field(default=None)


class PipelineJobExecutionSummary(BaseModel):
    pipelineJobExecutionId: int
    pipelineJobExecutionOrder: int
    pipelineJobName: Optional[str] = None
    pipelineJobExecutionStatus: Optional[str] = None


class PipelineJobExecutionDetailResponse(BaseModel):
    pipelineJobExecutionId: int
    pipelineJobId: int
    analysisId: int
    pipelineJobExecutionStatus: Optional[str] = None
    pipelineJobExecutionStartTime: Optional[str] = None
    pipelineJobExecutionEndTime: Optional[str] = None
    pipelineJobExecutionDuration: Optional[int] = None
    pipelineJobExecutionRequestData: Optional[Dict[str, Any]] = None
    pipelineJobExecutionResultData: Optional[Dict[str, Any]] = None

    pipelineJobName: Optional[str] = None
    pipelineJobExecutionOrder: Optional[int] = None


class PipelineJobExecutionListResponse(BaseModel):
    pipelineJobExecutionList: List[PipelineJobExecutionDetailResponse] = Field(default=None)
    pipelineJobExecutionTotalCount: int = 0