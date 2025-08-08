
import json
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException
from app.services.analysis_service import *
from pprint import pprint


router = APIRouter()

def print_pretty_request(data):
    def to_dict(obj):
        if isinstance(obj, list):
            return [to_dict(item) for item in obj]
        elif hasattr(obj, "dict"):
            return {k: to_dict(v) for k, v in obj.dict().items()}
        else:
            return obj

    print("--- [Parsed Request Data] ---")
    pprint(to_dict(data), indent=2, width=120)
    print("-----------------------------")



@router.get("/ai/test")
def test():
    return {"message": "test API"}


@router.post("/api/analyze/temp")
async def analyze(request_data: AIAnalysisRequest, request: Request):
    # 요청 로깅
    print("\n--- [Received AI Analysis Request] ---")
    print(await request.body())
    print("---------------------------------------\n")

    print_pretty_request(request_data)
    # 응답 JSON 파일 로딩 (문자열로 읽기)
    mock_file = Path(__file__).parent.parent / "mock" / "ai_response.json"
    with open(mock_file, "r", encoding="utf-8") as f:
        json_template = f.read()

    # groupId를 문자열 템플릿에 치환
    json_filled = json_template.replace("{{request_groupId}}", str(request_data.groupId))

    # JSON 파싱 및 반환
    return JSONResponse(content=json.loads(json_filled))


@router.post("/api/analyze")
async def analyze(request_data: AIAnalysisRequest, request: Request):
    # 요청 로깅
    print("\n--- [Received AI Analysis Request] ---")
    print(await request.body())
    print("---------------------------------------\n")

    print_pretty_request(request_data)

    # 분석 요청 정보 가공
    analysis_info = analyze_request_preprocessing(request_data)

    # 프롬프트 생성
    category_prompt = build_category_prompt(analysis_info["categoryPreference"])
    input_text_prompt = build_input_text_prompt(analysis_info["inputTextSummarySource"])

    print("\n[Generated Prompts]")
    print(">> 카테고리 선호 프롬프트:")
    print(category_prompt)
    print("\n>> 비정형 통합 프롬프트:")
    print(input_text_prompt)
    print("-----------------------------\n")

    # 응답 생성
    return {
        "groupId": analysis_info["groupId"],
        "isGroup": analysis_info["isGroup"],
        "memberCount": analysis_info["memberCount"],
        "basePosition": analysis_info["basePosition"],
        "categoryPrompt": category_prompt,
        "inputTextPrompt": input_text_prompt
    }





