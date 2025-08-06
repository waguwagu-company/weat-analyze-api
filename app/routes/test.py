from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# 테스트용 요청/응답 DTO 정의
class AIAnalysisRequest(BaseModel):
    groupId: str

class AIAnalysisResponse(BaseModel):
    groupId: str
    result: str

@router.get("/test")
def test():
    return {"message": "test API"}

# 테스트용 API
@router.post("/api/analyze", response_model=AIAnalysisResponse)
def analyze(request: AIAnalysisRequest):
    # 간단한 응답 로직 (예: groupId 그대로 리턴 + 고정 응답)
    return {
        "groupId": request.groupId,
        "result": f"AI 분석 완료 for groupId={request.groupId}"
    }
