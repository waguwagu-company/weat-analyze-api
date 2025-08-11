from typing import Optional, List, Dict, Any
from sqlalchemy import text
from app.db.db import SessionFactory
from app.models.pipeline_job import PipelineJob


def create_pipeline_job(data: PipelineJob) -> PipelineJob:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                INSERT INTO public.pipeline_job
                    (pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order)
                VALUES
                    (:pipeline_id, :pipeline_job_name, :pipeline_job_description, :pipeline_job_order)
                RETURNING pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
            """),
            {
                "pipeline_id": data.pipeline_id,
                "pipeline_job_name": data.pipeline_job_name,
                "pipeline_job_description": data.pipeline_job_description,
                "pipeline_job_order": data.pipeline_job_order,
            },
        )
        row = result.mappings().one()
        session.commit()
        return PipelineJob(**row)


def get_pipeline_job(pipeline_job_id: int) -> Optional[PipelineJob]:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                SELECT pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
                  FROM public.pipeline_job
                 WHERE pipeline_job_id = :pipeline_job_id
            """),
            {"pipeline_job_id": pipeline_job_id},
        )
        row = result.mappings().first()
        return PipelineJob(**row) if row else None


def get_all_pipeline_job_list(pipeline_id: int, limit: int = 100, offset: int = 0) -> List[PipelineJob]:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                SELECT pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
                  FROM public.pipeline_job
                 WHERE pipeline_id = :pipeline_id
                 ORDER BY pipeline_job_order NULLS LAST, pipeline_job_id ASC
                 LIMIT :limit OFFSET :offset
            """),
            {"pipeline_id": pipeline_id, "limit": limit, "offset": offset},
        )
        return [PipelineJob(**row) for row in result.mappings().all()]


def update_pipeline_job(pipeline_job_id: int, data: PipelineJob) -> Optional[PipelineJob]:
    fields_to_update: Dict[str, Any] = {}
    set_clauses: List[str] = []

    if data.pipeline_id is not None:
        set_clauses.append("pipeline_id = :pipeline_id")
        fields_to_update["pipeline_id"] = data.pipeline_id
    if data.pipeline_job_name is not None:
        set_clauses.append("pipeline_job_name = :pipeline_job_name")
        fields_to_update["pipeline_job_name"] = data.pipeline_job_name
    if data.pipeline_job_description is not None:
        set_clauses.append("pipeline_job_description = :pipeline_job_description")
        fields_to_update["pipeline_job_description"] = data.pipeline_job_description
    if data.pipeline_job_order is not None:
        set_clauses.append("pipeline_job_order = :pipeline_job_order")
        fields_to_update["pipeline_job_order"] = data.pipeline_job_order

    if not set_clauses:
        return get_pipeline_job(pipeline_job_id)

    sql = f"""
        UPDATE public.pipeline_job
           SET {', '.join(set_clauses)}
         WHERE pipeline_job_id = :pipeline_job_id
     RETURNING pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
    """
    fields_to_update["pipeline_job_id"] = pipeline_job_id

    with SessionFactory() as session:
        result = session.execute(text(sql), fields_to_update)
        row = result.mappings().first()
        if row:
            session.commit()
            return PipelineJob(**row)
        session.rollback()
        return None


def delete_pipeline_job(pipeline_job_id: int) -> bool:
    with SessionFactory() as session:
        result = session.execute(
            text("DELETE FROM public.pipeline_job WHERE pipeline_job_id = :pipeline_job_id"),
            {"pipeline_job_id": pipeline_job_id},
        )
        session.commit()
        return result.rowcount > 0