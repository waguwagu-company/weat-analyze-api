from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import text
from app.db.db import SessionFactory


def get_latest_pipeline_execution(pipeline_id: int, analysis_id: int) -> Optional[Dict[str, Any]]:
    """
    최신 파이프라인 실행 1건 반환
    """
    sql = text("""
        SELECT 
            pe.pipeline_execution_id,
            pe.pipeline_id,
            pe.analysis_id,
            pe.pipeline_execution_status,
            pe.pipeline_execution_stage,
            pe.pipeline_execution_start_time,
            pe.pipeline_execution_end_time,
            pe.pipeline_execution_duration
        FROM public.pipeline_execution pe
        WHERE pe.pipeline_id = :pipeline_id
          AND pe.analysis_id = :analysis_id
        ORDER BY pe.pipeline_execution_start_time DESC NULLS LAST,
                 pe.pipeline_execution_id DESC
        LIMIT 1
    """)
    with SessionFactory() as session:
        res = session.execute(sql, {"pipeline_id": pipeline_id, "analysis_id": analysis_id})
        row = res.mappings().first()
        return dict(row) if row else None


def list_job_executions_for_execution(pipeline_id: int, analysis_id: int) -> List[Dict[str, Any]]:
    """
    해당 파이프라인에 속한 작업실행 목록 (작업순서 오름차순)
    """
    sql = text("""
        SELECT 
            pje.pipeline_job_execution_id,
            pje.pipeline_job_id,
            pje.analysis_id,
            pje.job_execution_status        AS pipeline_job_execution_status,
            pje.job_execution_start_time    AS pipeline_job_execution_start_time,
            pje.job_execution_end_time      AS pipeline_job_execution_end_time,
            pje.job_execution_duration      AS pipeline_job_execution_duration,
            pje.job_execution_request_data  AS pipeline_job_execution_request_data,
            pje.job_execution_result_data   AS pipeline_job_execution_result_data,
            pj.pipeline_job_name            AS pipeline_job_name,
            pj.pipeline_job_order AS pipeline_job_order
        FROM public.pipeline_job_execution pje
        JOIN public.pipeline_job pj
          ON pj.pipeline_job_id = pje.pipeline_job_id
        WHERE pje.analysis_id = :analysis_id
          AND pj.pipeline_id   = :pipeline_id
        ORDER BY pj.pipeline_job_order ASC,
                 pje.pipeline_job_execution_id ASC
    """)
    with SessionFactory() as session:
        res = session.execute(sql, {"pipeline_id": pipeline_id, "analysis_id": analysis_id})
        return [dict(r) for r in res.mappings().all()]


def get_job_execution_detail(pipeline_job_execution_id: int) -> Optional[Dict[str, Any]]:
    """
    단일 작업 실행 상세
    """
    sql = text("""
        SELECT 
            pje.pipeline_job_execution_id,
            pje.pipeline_job_id,
            pje.analysis_id,
            pje.job_execution_status        AS pipeline_job_execution_status,
            pje.job_execution_start_time    AS pipeline_job_execution_start_time,
            pje.job_execution_end_time      AS pipeline_job_execution_end_time,
            pje.job_execution_duration      AS pipeline_job_execution_duration,
            pje.job_execution_request_data  AS pipeline_job_execution_request_data,
            pje.job_execution_result_data   AS pipeline_job_execution_result_data,
            pj.pipeline_job_name            AS pipeline_job_name,
            pj.pipeline_job_order AS pipeline_job_order
        FROM public.pipeline_job_execution pje
        JOIN public.pipeline_job pj
          ON pj.pipeline_job_id = pje.pipeline_job_id
        WHERE pje.pipeline_job_execution_id = :pipeline_job_execution_id
        LIMIT 1
    """)
    with SessionFactory() as session:
        res = session.execute(sql, {"pipeline_job_execution_id": pipeline_job_execution_id})
        row = res.mappings().first()
        return dict(row) if row else None