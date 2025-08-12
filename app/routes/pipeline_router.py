from fastapi import APIRouter, HTTPException, Query
from app.crud.pipeline_execution_query import (
    get_latest_pipeline_execution,
    list_job_executions_for_execution,
    get_job_execution_detail,
)
from app.models.pipeline_api_model import *

router = APIRouter()

@router.get(
    "/api/pipeline/executions/status",
    response_model=PipelineExecutionStatusResponse
)
async def get_pipeline_execution_status(
    pipelineId: int = Query(..., description="파이프라인식별자"),
    analysisId: int = Query(..., description="분석식별자"),
):
    """
    현재 파이프라인 실행 상태와 관련 작업실행 식별자, 요약 제공
    """
    execution = get_latest_pipeline_execution(pipeline_id=pipelineId, analysis_id=analysisId)
    if not execution:
        raise HTTPException(status_code=404, detail="pipelineExecution not found")

    rows = list_job_executions_for_execution(pipeline_id=pipelineId, analysis_id=analysisId)

    pipeline_job_execution_id_list: List[int] = [r["pipeline_job_execution_id"] for r in rows]
    pipeline_job_order_map: Dict[str, int] = {
        str(r["pipeline_job_order"]): r["pipeline_job_execution_id"] for r in rows
    }
    pipeline_job_execution_summary_list: List[PipelineJobExecutionSummary] = [
        PipelineJobExecutionSummary(
            pipelineJobExecutionId=r["pipeline_job_execution_id"],
            pipelineJobExecutionOrder=r["pipeline_job_order"],
            pipelineJobName=r.get("pipeline_job_name"),
            pipelineJobExecutionStatus=r.get("pipeline_job_execution_status"),
        )
        for r in rows
    ]

    current_order = execution.get("pipeline_execution_stage")
    current_name = None
    if current_order is not None:
        for r in rows:
            if r["pipeline_job_order"] == current_order:
                current_name = r.get("pipeline_job_name")
                break

    return PipelineExecutionStatusResponse(
        pipelineExecutionId=execution["pipeline_execution_id"],
        pipelineId=execution["pipeline_id"],
        analysisId=execution["analysis_id"],
        pipelineExecutionStatus=execution.get("pipeline_execution_status"),
        pipelineExecutionStage=execution.get("pipeline_execution_stage"),
        pipelineExecutionStartTime=(
            execution.get("pipeline_execution_start_time").isoformat()
            if execution.get("pipeline_execution_start_time")
            else None
        ),
        pipelineExecutionEndTime=(
            execution.get("pipeline_execution_end_time").isoformat()
            if execution.get("pipeline_execution_end_time")
            else None
        ),
        pipelineExecutionDuration=execution.get("pipeline_execution_duration"),
        currentPipelineJobOrder=current_order,
        currentPipelineJobName=current_name,
        pipelineJobExecutionIdList=pipeline_job_execution_id_list,
        pipelineJobExecutionOrderMap=pipeline_job_order_map,
        pipelineJobExecutionSummaryList=pipeline_job_execution_summary_list,
    )


@router.get(
    "/api/pipeline/executions/jobs",
    response_model=PipelineJobExecutionListResponse
)
async def get_pipeline_job_execution_list(
    pipelineId: int = Query(..., description="파이프라인식별자"),
    analysisId: int = Query(..., description="분석식별자")
):
    """
    파이프라인에 속한 작업실행 목록
    """
    rows = list_job_executions_for_execution(pipeline_id=pipelineId, analysis_id=analysisId)

    items: List[PipelineJobExecutionDetailResponse] = []
    for r in rows:
        items.append(
            PipelineJobExecutionDetailResponse(
                pipelineJobExecutionId=r["pipeline_job_execution_id"],
                pipelineJobId=r["pipeline_job_id"],
                analysisId=r["analysis_id"],
                pipelineJobExecutionStatus=r.get("pipeline_job_execution_status"),
                pipelineJobExecutionStartTime=(
                    r.get("pipeline_job_execution_start_time").isoformat()
                    if r.get("pipeline_job_execution_start_time")
                    else None
                ),
                pipelineJobExecutionEndTime=(
                    r.get("pipeline_job_execution_end_time").isoformat()
                    if r.get("pipeline_job_execution_end_time")
                    else None
                ),
                pipelineJobExecutionDuration=r.get("pipeline_job_execution_duration"),
                pipelineJobExecutionRequestData=r.get("pipeline_job_execution_request_data"),
                pipelineJobExecutionResultData=r.get("pipeline_job_execution_result_data"),
                pipelineJobName=r.get("pipeline_job_name"),
                pipelineJobExecutionOrder=r.get("pipeline_job_order"),
            )
        )

    return PipelineJobExecutionListResponse(
        pipelineJobExecutionList=items,
        pipelineJobExecutionTotalCount=len(items),
    )


@router.get(
    "/api/pipeline/executions/jobs/{pipelineJobExecutionId}",
    response_model=PipelineJobExecutionDetailResponse
)
async def get_pipeline_job_execution_detail_api(pipelineJobExecutionId: int):
    """
    단일 작업실행 상세
    """
    r = get_job_execution_detail(pipeline_job_execution_id=pipelineJobExecutionId)
    if not r:
        raise HTTPException(status_code=404, detail="pipelineJobExecution not found")

    return PipelineJobExecutionDetailResponse(
        pipelineJobExecutionId=r["pipeline_job_execution_id"],
        pipelineJobId=r["pipeline_job_id"],
        analysisId=r["analysis_id"],
        pipelineJobExecutionStatus=r.get("pipeline_job_execution_status"),
        pipelineJobExecutionStartTime=(
            r.get("pipeline_job_execution_start_time").isoformat()
            if r.get("pipeline_job_execution_start_time")
            else None
        ),
        pipelineJobExecutionEndTime=(
            r.get("pipeline_job_execution_end_time").isoformat()
            if r.get("pipeline_job_execution_end_time")
            else None
        ),
        pipelineJobExecutionDuration=r.get("pipeline_job_execution_duration"),
        pipelineJobExecutionRequestData=r.get("pipeline_job_execution_request_data"),
        pipelineJobExecutionResultData=r.get("pipeline_job_execution_result_data"),
        pipelineJobName=r.get("pipeline_job_name"),
        pipelineJobExecutionOrder=r.get("pipeline_job_order"),
    )