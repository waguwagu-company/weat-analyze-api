from fastapi import APIRouter, HTTPException
from app.models.ai_analysis import AnalysisRequest, ChatResponse
from app.services.ai_analysis_service import request_ai_analysis

router = APIRouter()

@router.get("/test")
def test():
    return {"message": "test API"}

@router.post("/clova-test", response_model=ChatResponse)
def analyze(req: AnalysisRequest):
    try:
        result = request_ai_analysis(req.data)
        return ChatResponse(reply=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))