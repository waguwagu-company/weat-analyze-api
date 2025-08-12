import json
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException
from app.services.analysis_service import *
from pprint import pprint
import traceback

router = APIRouter()

"""
특정 위치를 기준으로 AI 분석을 통해 주변 장소의 리뷰를 평가하고,
적합도 기준으로 상위 N개의 장소를 반환
"""
@router.post("/api/analysis", response_model=AnalysisResponse)
async def analyze(request_data: AIAnalysisRequest, request: Request) -> AnalysisResponse:
    try:
        print("\n--- [분석 요청 수신] ---")
        pprint(json.loads(await request.body()))
        print("-------------------------------------\n")

        result = await run_place_recommendation_pipeline_v2(request_data, analysis_id=214)
        return result

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


