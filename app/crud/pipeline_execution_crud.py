from typing import Optional, List, Dict, Any
from sqlalchemy import text
from app.db.db import SessionFactory
from app.models.pipeline_execution import PipelineExecution

def create_pipeline_execution(data: PipelineExecution) -> PipelineExecution:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                INSERT INTO public.pipeline_execution
                    (pipeline_id, analysis_id, pipeline_execution_status,
                     pipeline_execution_stage, pipeline_execution_end_time,
                     pipeline_execution_duration)
                VALUES
                    (:pipeline_id, :analysis_id, :pipeline_execution_status,
                     :pipeline_execution_stage, :pipeline_execution_end_time,
                     :pipeline_execution_duration)
                RETURNING pipeline_execution_id, pipeline_id, analysis_id,
                          pipeline_execution_status, pipeline_execution_stage,
                          pipeline_execution_start_time, pipeline_execution_end_time,
                          pipeline_execution_duration
            """),
            {
                "pipeline_id": data.pipeline_id,
                "analysis_id": data.analysis_id,
                "pipeline_execution_status": data.pipeline_execution_status,
                "pipeline_execution_stage": data.pipeline_execution_stage,
                "pipeline_execution_end_time": data.pipeline_execution_end_time,
                "pipeline_execution_duration": data.pipeline_execution_duration,
            },
        )
        row = result.mappings().one()
        session.commit()
        return PipelineExecution(**row)


def get_pipeline_execution(pipeline_execution_id: int) -> Optional[PipelineExecution]:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                SELECT pipeline_execution_id, pipeline_id, analysis_id,
                       pipeline_execution_status, pipeline_execution_stage,
                       pipeline_execution_start_time, pipeline_execution_end_time,
                       pipeline_execution_duration
                  FROM public.pipeline_execution
                 WHERE pipeline_execution_id = :pipeline_execution_id
            """),
            {"pipeline_execution_id": pipeline_execution_id},
        )
        row = result.mappings().first()
        return PipelineExecution(**row) if row else None


def get_all_pipeline_execution_list(
    pipeline_id: Optional[int] = None,
    analysis_id: Optional[int] = None,
    pipeline_execution_status: Optional[str] = None,
    pipeline_execution_stage: Optional[int] = None,
    only_active: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> List[PipelineExecution]:
    where_clauses = []
    parameters: Dict[str, Any] = {"limit": limit, "offset": offset}

    if pipeline_id is not None:
        where_clauses.append("pipeline_id = :pipeline_id")
        parameters["pipeline_id"] = pipeline_id
    if analysis_id is not None:
        where_clauses.append("analysis_id = :analysis_id")
        parameters["analysis_id"] = analysis_id
    if pipeline_execution_status is not None:
        where_clauses.append("pipeline_execution_status = :pipeline_execution_status")
        parameters["pipeline_execution_status"] = pipeline_execution_status
    if pipeline_execution_stage is not None:
        where_clauses.append("pipeline_execution_stage = :pipeline_execution_stage")
        parameters["pipeline_execution_stage"] = pipeline_execution_stage
    if only_active:
        where_clauses.append("pipeline_execution_end_time IS NULL")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    sql = f"""
        SELECT pipeline_execution_id, pipeline_id, analysis_id,
               pipeline_execution_status, pipeline_execution_stage,
               pipeline_execution_start_time, pipeline_execution_end_time,
               pipeline_execution_duration
          FROM public.pipeline_execution
          {where_sql}
         ORDER BY pipeline_execution_start_time DESC NULLS LAST,
                  pipeline_execution_id DESC
         LIMIT :limit OFFSET :offset
    """

    with SessionFactory() as session:
        result = session.execute(text(sql), parameters)
        return [PipelineExecution(**row) for row in result.mappings().all()]


def update_pipeline_execution(pipeline_execution_id: int, data: PipelineExecution) -> Optional[PipelineExecution]:
    fields: Dict[str, Any] = {}
    set_clauses: List[str] = []

    if data.pipeline_id is not None:
        set_clauses.append("pipeline_id = :pipeline_id")
        fields["pipeline_id"] = data.pipeline_id
    if data.analysis_id is not None:
        set_clauses.append("analysis_id = :analysis_id")
        fields["analysis_id"] = data.analysis_id
    if data.pipeline_execution_status is not None:
        set_clauses.append("pipeline_execution_status = :pipeline_execution_status")
        fields["pipeline_execution_status"] = data.pipeline_execution_status
    if data.pipeline_execution_stage is not None:
        set_clauses.append("pipeline_execution_stage = :pipeline_execution_stage")
        fields["pipeline_execution_stage"] = data.pipeline_execution_stage
    if data.pipeline_execution_start_time is not None:
        set_clauses.append("pipeline_execution_start_time = :pipeline_execution_start_time")
        fields["pipeline_execution_start_time"] = data.pipeline_execution_start_time
    if data.pipeline_execution_end_time is not None:
        set_clauses.append("pipeline_execution_end_time = :pipeline_execution_end_time")
        fields["pipeline_execution_end_time"] = data.pipeline_execution_end_time
    if data.pipeline_execution_duration is not None:
        set_clauses.append("pipeline_execution_duration = :pipeline_execution_duration")
        fields["pipeline_execution_duration"] = data.pipeline_execution_duration

    if not set_clauses:
        return get_pipeline_execution(pipeline_execution_id)

    sql = f"""
        UPDATE public.pipeline_execution
           SET {', '.join(set_clauses)}
         WHERE pipeline_execution_id = :pipeline_execution_id
     RETURNING pipeline_execution_id, pipeline_id, analysis_id,
               pipeline_execution_status, pipeline_execution_stage,
               pipeline_execution_start_time, pipeline_execution_end_time,
               pipeline_execution_duration
    """
    fields["pipeline_execution_id"] = pipeline_execution_id

    with SessionFactory() as session:
        result = session.execute(text(sql), fields)
        row = result.mappings().first()
        if row:
            session.commit()
            return PipelineExecution(**row)
        session.rollback()
        return None


def delete_pipeline_execution(pipeline_execution_id: int) -> bool:
    with SessionFactory() as session:
        result = session.execute(
            text("DELETE FROM public.pipeline_execution WHERE pipeline_execution_id = :pipeline_execution_id"),
            {"pipeline_execution_id": pipeline_execution_id},
        )
        session.commit()
        return result.rowcount > 0