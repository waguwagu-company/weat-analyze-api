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
@router.post("/api/analysis")
async def analyze(request_data: AIAnalysisRequest, request: Request):
    try:
        print("\n--- [분석 요청 수신] ---")
        print(await request.body())
        print("-------------------------------------\n")

        result = await run_place_recommendation_pipeline(request_data)
        print(result)
        return JSONResponse(content=result)

    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        traceback.print_exc 
        return JSONResponse(status_code=500, content={"error": str(e)})


