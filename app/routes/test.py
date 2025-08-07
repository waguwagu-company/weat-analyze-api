
import json
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.test.dto.ai_analysis_request_dto import AIAnalysisRequest
from fastapi import APIRouter, HTTPException
from app.models.ai_analysis_model import AnalysisRequest, ChatResponse
from app.services.ai_analysis_service import request_ai_analysis


router = APIRouter()

@router.get("/ai/test")
def test():
    return {"message": "test API"}


@router.post("/api/analyze")
async def analyze(request_data: AIAnalysisRequest, request: Request):
    # 요청 로깅
    print("\n--- [Received AI Analysis Request] ---")
    print(await request.body())
    print("---------------------------------------\n")

    # 응답 JSON 파일 로딩 (문자열로 읽기)
    mock_file = Path(__file__).parent.parent / "mock" / "ai_response.json"
    with open(mock_file, "r", encoding="utf-8") as f:
        json_template = f.read()

    # groupId를 문자열 템플릿에 치환
    json_filled = json_template.replace("{{request_groupId}}", str(request_data.groupId))

    # JSON 파싱 및 반환
    return JSONResponse(content=json.loads(json_filled))


