from typing import Optional, List, Dict, Any
from sqlalchemy import text
from app.db.db import SessionFactory
from app.models.pipeline_job import PipelineJob

def create_pipeline_job(data: PipelineJob) -> PipelineJob:
    with SessionFactory() as session:
        res = session.execute(
            text("""
                INSERT INTO public.pipeline_job
                    (pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order)
                VALUES
                    (:pid, :name, :desc, :ord)
                RETURNING pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
            """),
            {
                "pid": data.pipeline_id,
                "name": data.pipeline_job_name,
                "desc": data.pipeline_job_description,
                "ord": data.pipeline_job_order,
            },
        )
        row = res.mappings().one()
        session.commit()
        return PipelineJob(**row)


def get_pipeline_job(pipeline_job_id: int) -> Optional[PipelineJob]:
    with SessionFactory() as session:
        res = session.execute(
            text("""
                SELECT pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
                  FROM public.pipeline_job
                 WHERE pipeline_job_id = :id
            """),
            {"id": pipeline_job_id},
        )
        row = res.mappings().first()
        return PipelineJob(**row) if row else None


def get_all_pipeline_job_list(pipeline_id: int, limit: int = 100, offset: int = 0) -> List[PipelineJob]:
    with SessionFactory() as session:
        res = session.execute(
            text("""
                SELECT pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
                  FROM public.pipeline_job
                 WHERE pipeline_id = :pid
                 ORDER BY pipeline_job_order NULLS LAST, pipeline_job_id ASC
                 LIMIT :limit OFFSET :offset
            """),
            {"pid": pipeline_id, "limit": limit, "offset": offset},
        )
        return [PipelineJob(**row) for row in res.mappings().all()]


def update_pipeline_job(pipeline_job_id: int, data: PipelineJob) -> Optional[PipelineJob]:
    fields: Dict[str, Any] = {}
    sets: List[str] = []

    if data.pipeline_id is not None:
        sets.append("pipeline_id = :pid")
        fields["pid"] = data.pipeline_id
    if data.pipeline_job_name is not None:
        sets.append("pipeline_job_name = :name")
        fields["name"] = data.pipeline_job_name
    if data.pipeline_job_description is not None:
        sets.append("pipeline_job_description = :desc")
        fields["desc"] = data.pipeline_job_description
    if data.pipeline_job_order is not None:
        sets.append("pipeline_job_order = :ord")
        fields["ord"] = data.pipeline_job_order

    if not sets:
        return get_pipeline_job(pipeline_job_id)

    sql = f"""
        UPDATE public.pipeline_job
           SET {', '.join(sets)}
         WHERE pipeline_job_id = :id
     RETURNING pipeline_job_id, pipeline_id, pipeline_job_name, pipeline_job_description, pipeline_job_order
    """
    fields["id"] = pipeline_job_id

    with SessionFactory() as session:
        res = session.execute(text(sql), fields)
        row = res.mappings().first()
        if row:
            session.commit()
            return PipelineJob(**row)
        session.rollback()
        return None


def delete_pipeline_job(pipeline_job_id: int) -> bool:
    with SessionFactory() as session:
        res = session.execute(
            text("DELETE FROM public.pipeline_job WHERE pipeline_job_id = :id"),
            {"id": pipeline_job_id},
        )
        session.commit()
        return res.rowcount > 0