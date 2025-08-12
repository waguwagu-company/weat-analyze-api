from dataclasses import dataclass
from typing import Optional, Dict, Any
from utils.utils import now_utc, seconds_between
from app.models.pipeline_execution import PipelineExecution
from app.crud.pipeline_execution_crud import create_pipeline_execution, update_pipeline_execution
from app.models.pipeline_job_execution import PipelineJobExecution
from app.crud.pipeline_job_execution_crud import create_pipeline_job_execution, update_pipeline_job_execution


@dataclass
class PipelineExecutionContext:
    pipeline_execution_id: int
    start_time: Any


@dataclass
class PipelineJobExecutionContext:
    pipeline_job_execution_id: int
    start_time: Any


class PipelineExecutionManager:
    def __init__(self, pipeline_id: int, analysis_id: int, initial_stage: int = 0):
        self.pipeline_id = pipeline_id
        self.analysis_id = analysis_id
        self.initial_stage = initial_stage
        self.context: Optional[PipelineExecutionContext] = None

    async def __aenter__(self):
        start_time = now_utc()
        created = create_pipeline_execution(
            PipelineExecution(
                pipeline_id=self.pipeline_id,
                analysis_id=self.analysis_id,
                pipeline_execution_status="RUNNING",
                pipeline_execution_stage=self.initial_stage,
                pipeline_execution_start_time=start_time,
            )
        )
        self.context = PipelineExecutionContext(
            pipeline_execution_id=created.pipeline_execution_id,
            start_time=start_time,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        assert self.context is not None
        end_time = now_utc()
        duration = seconds_between(self.context.start_time, end_time)
        if exc is None:
            update_pipeline_execution(
                self.context.pipeline_execution_id,
                PipelineExecution(
                    pipeline_id=self.pipeline_id,
                    analysis_id=self.analysis_id,
                    pipeline_execution_status="SUCCEEDED",
                    pipeline_execution_end_time=end_time,
                    pipeline_execution_duration=duration,
                ),
            )
        else:
            update_pipeline_execution(
                self.context.pipeline_execution_id,
                PipelineExecution(
                    pipeline_id=self.pipeline_id,
                    analysis_id=self.analysis_id,
                    pipeline_execution_status="FAILED",
                    pipeline_execution_end_time=end_time,
                    pipeline_execution_duration=duration,
                ),
            )
        return False

    def advance_stage(self, stage: int, status: Optional[str] = None):
        assert self.context is not None
        update_pipeline_execution(
            self.context.pipeline_execution_id,
            PipelineExecution(
                pipeline_id=self.pipeline_id,
                analysis_id=self.analysis_id,
                pipeline_execution_stage=stage,
                pipeline_execution_status=status,
            ),
        )


class PipelineJobExecutionManager:
    def __init__(
        self,
        pipeline_job_id: int,
        analysis_id: int,
        job_execution_request_data: Optional[Dict[str, Any]] = None,
    ):
        self.pipeline_job_id = pipeline_job_id
        self.analysis_id = analysis_id
        self.job_execution_request_data = job_execution_request_data or {}
        self.context: Optional[PipelineJobExecutionContext] = None

    async def __aenter__(self):
        start_time = now_utc()
        created = create_pipeline_job_execution(
            PipelineJobExecution(
                pipeline_job_id=self.pipeline_job_id,
                analysis_id=self.analysis_id,
                job_execution_status="RUNNING",
                job_execution_start_time=start_time,
                job_execution_request_data=self.job_execution_request_data,
            )
        )
        self.context = PipelineJobExecutionContext(
            pipeline_job_execution_id=created.pipeline_job_execution_id,
            start_time=start_time,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        assert self.context is not None
        end_time = now_utc()
        duration = seconds_between(self.context.start_time, end_time)

        if exc is None:
            update_pipeline_job_execution(
                self.context.pipeline_job_execution_id,
                PipelineJobExecution(
                    pipeline_job_id=self.pipeline_job_id,
                    analysis_id=self.analysis_id,
                    job_execution_status="SUCCEEDED",
                    job_execution_end_time=end_time,
                    job_execution_duration=duration,
                ),
            )
        else:
            update_pipeline_job_execution(
                self.context.pipeline_job_execution_id,
                PipelineJobExecution(
                    pipeline_job_id=self.pipeline_job_id,
                    analysis_id=self.analysis_id,
                    job_execution_status="FAILED",
                    job_execution_end_time=end_time,
                    job_execution_duration=duration,
                    job_execution_result_data={"error": str(exc)},
                ),
            )
        return False

    def attach_result(self, result_data: Dict[str, Any]):
        update_pipeline_job_execution(
            self.context.pipeline_job_execution_id,
            PipelineJobExecution(
                pipeline_job_id=self.pipeline_job_id,
                analysis_id=self.analysis_id,
                job_execution_result_data=result_data,
            ),
        )