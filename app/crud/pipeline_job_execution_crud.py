from typing import Optional, List, Dict, Any
from sqlalchemy import text
from app.db.db import SessionFactory
from app.models.pipeline_job_execution import PipelineJobExecution


def create_pipeline_job_execution(data: PipelineJobExecution) -> PipelineJobExecution:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                INSERT INTO public.pipeline_job_execution
                    (pipeline_job_id, analysis_id, job_execution_status,
                     job_execution_end_time, job_execution_duration,
                     job_execution_request_data, job_execution_result_data)
                VALUES
                    (:pipeline_job_id, :analysis_id, :job_execution_status,
                     :job_execution_end_time, :job_execution_duration,
                     :job_execution_request_data, :job_execution_result_data)
                RETURNING pipeline_job_execution_id, pipeline_job_id, analysis_id,
                          job_execution_status, job_execution_start_time, job_execution_end_time,
                          job_execution_duration, job_execution_request_data, job_execution_result_data
            """),
            {
                "pipeline_job_id": data.pipeline_job_id,
                "analysis_id": data.analysis_id,
                "job_execution_status": data.job_execution_status,
                # start_time은 DB DEFAULT now() 사용
                "job_execution_end_time": data.job_execution_end_time,
                "job_execution_duration": data.job_execution_duration,
                "job_execution_request_data": data.job_execution_request_data,
                "job_execution_result_data": data.job_execution_result_data,
            },
        )
        row = result.mappings().one()
        session.commit()
        return PipelineJobExecution(**row)


def get_pipeline_job_execution(pipeline_job_execution_id: int) -> Optional[PipelineJobExecution]:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                SELECT pipeline_job_execution_id, pipeline_job_id, analysis_id,
                       job_execution_status, job_execution_start_time, job_execution_end_time,
                       job_execution_duration, job_execution_request_data, job_execution_result_data
                  FROM public.pipeline_job_execution
                 WHERE pipeline_job_execution_id = :pipeline_job_execution_id
            """),
            {"pipeline_job_execution_id": pipeline_job_execution_id},
        )
        row = result.mappings().first()
        return PipelineJobExecution(**row) if row else None


def get_all_pipeline_job_execution_list(
    pipeline_job_id: Optional[int] = None,
    analysis_id: Optional[int] = None,
    job_execution_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[PipelineJobExecution]:
    where_clauses = []
    parameters: Dict[str, Any] = {"limit": limit, "offset": offset}

    if pipeline_job_id is not None:
        where_clauses.append("pipeline_job_id = :pipeline_job_id")
        parameters["pipeline_job_id"] = pipeline_job_id
    if analysis_id is not None:
        where_clauses.append("analysis_id = :analysis_id")
        parameters["analysis_id"] = analysis_id
    if job_execution_status is not None:
        where_clauses.append("job_execution_status = :job_execution_status")
        parameters["job_execution_status"] = job_execution_status

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    sql = f"""
        SELECT pipeline_job_execution_id, pipeline_job_id, analysis_id,
               job_execution_status, job_execution_start_time, job_execution_end_time,
               job_execution_duration, job_execution_request_data, job_execution_result_data
          FROM public.pipeline_job_execution
          {where_sql}
         ORDER BY job_execution_start_time DESC NULLS LAST,
                  pipeline_job_execution_id DESC
         LIMIT :limit OFFSET :offset
    """

    with SessionFactory() as session:
        result = session.execute(text(sql), parameters)
        return [PipelineJobExecution(**row) for row in result.mappings().all()]


def update_pipeline_job_execution(pipeline_job_execution_id: int, data: PipelineJobExecution) -> Optional[PipelineJobExecution]:
    fields_to_update: Dict[str, Any] = {}
    set_clauses: List[str] = []

    if data.pipeline_job_id is not None:
        set_clauses.append("pipeline_job_id = :pipeline_job_id")
        fields_to_update["pipeline_job_id"] = data.pipeline_job_id
    if data.analysis_id is not None:
        set_clauses.append("analysis_id = :analysis_id")
        fields_to_update["analysis_id"] = data.analysis_id
    if data.job_execution_status is not None:
        set_clauses.append("job_execution_status = :job_execution_status")
        fields_to_update["job_execution_status"] = data.job_execution_status
    if data.job_execution_start_time is not None:
        set_clauses.append("job_execution_start_time = :job_execution_start_time")
        fields_to_update["job_execution_start_time"] = data.job_execution_start_time
    if data.job_execution_end_time is not None:
        set_clauses.append("job_execution_end_time = :job_execution_end_time")
        fields_to_update["job_execution_end_time"] = data.job_execution_end_time
    if data.job_execution_duration is not None:
        set_clauses.append("job_execution_duration = :job_execution_duration")
        fields_to_update["job_execution_duration"] = data.job_execution_duration
    if data.job_execution_request_data is not None:
        set_clauses.append("job_execution_request_data = :job_execution_request_data")
        fields_to_update["job_execution_request_data"] = data.job_execution_request_data
    if data.job_execution_result_data is not None:
        set_clauses.append("job_execution_result_data = :job_execution_result_data")
        fields_to_update["job_execution_result_data"] = data.job_execution_result_data

    if not set_clauses:
        return get_pipeline_job_execution(pipeline_job_execution_id)

    sql = f"""
        UPDATE public.pipeline_job_execution
           SET {', '.join(set_clauses)}
         WHERE pipeline_job_execution_id = :pipeline_job_execution_id
     RETURNING pipeline_job_execution_id, pipeline_job_id, analysis_id,
               job_execution_status, job_execution_start_time, job_execution_end_time,
               job_execution_duration, job_execution_request_data, job_execution_result_data
    """
    fields_to_update["pipeline_job_execution_id"] = pipeline_job_execution_id

    with SessionFactory() as session:
        result = session.execute(text(sql), fields_to_update)
        row = result.mappings().first()
        if row:
            session.commit()
            return PipelineJobExecution(**row)
        session.rollback()
        return None


def delete_pipeline_job_execution(pipeline_job_execution_id: int) -> bool:
    with SessionFactory() as session:
        result = session.execute(
            text("DELETE FROM public.pipeline_job_execution WHERE pipeline_job_execution_id = :pipeline_job_execution_id"),
            {"pipeline_job_execution_id": pipeline_job_execution_id},
        )
        session.commit()
        return result.rowcount > 0