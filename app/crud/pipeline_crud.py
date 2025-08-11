from typing import Optional, List, Dict, Any
from sqlalchemy import text
from app.db.db import SessionFactory
from app.models.pipeline import Pipeline

def create_pipeline(data: Pipeline) -> Pipeline:
    with SessionFactory() as session:
        res = session.execute(
            text("""
                INSERT INTO public.pipeline
                    (pipeline_name, pipeline_description)
                VALUES
                    (:name, :desc)
                RETURNING pipeline_id, pipeline_name, pipeline_description
            """),
            {
                "name": data.pipeline_name,
                "desc": data.pipeline_description,
            },
        )
        row = res.mappings().one()
        session.commit()
        return Pipeline(**row)


def get_pipeline(pipeline_id: int) -> Optional[Pipeline]:
    with SessionFactory() as session:
        res = session.execute(
            text("""
                SELECT pipeline_id, pipeline_name, pipeline_description
                  FROM public.pipeline
                 WHERE pipeline_id = :id
            """),
            {"id": pipeline_id},
        )
        row = res.mappings().first()
        return Pipeline(**row) if row else None


def get_all_pipeline_list(limit: int = 100, offset: int = 0) -> List[Pipeline]:
    with SessionFactory() as session:
        res = session.execute(
            text("""
                SELECT pipeline_id, pipeline_name, pipeline_description
                  FROM public.pipeline
                 ORDER BY pipeline_id ASC
                 LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset},
        )
        return [Pipeline(**row) for row in res.mappings().all()]


def update_pipeline(pipeline_id: int, data: Pipeline) -> Optional[Pipeline]:
    fields: Dict[str, Any] = {}
    sets: List[str] = []

    if data.pipeline_name is not None:
        sets.append("pipeline_name = :name")
        fields["name"] = data.pipeline_name
    if data.pipeline_description is not None:
        sets.append("pipeline_description = :desc")
        fields["desc"] = data.pipeline_description

    if not sets:
        return get_pipeline(pipeline_id)

    sql = f"""
        UPDATE public.pipeline
           SET {', '.join(sets)}
         WHERE pipeline_id = :id
     RETURNING pipeline_id, pipeline_name, pipeline_description
    """
    fields["id"] = pipeline_id

    with SessionFactory() as session:
        res = session.execute(text(sql), fields)
        row = res.mappings().first()
        if row:
            session.commit()
            return Pipeline(**row)
        session.rollback()
        return None


def delete_pipeline(pipeline_id: int) -> bool:
    with SessionFactory() as session:
        res = session.execute(
            text("DELETE FROM public.pipeline WHERE pipeline_id = :id"),
            {"id": pipeline_id},
        )
        session.commit()
        return res.rowcount > 0