import json
from fastapi import APIRouter, HTTPException, Request
from app.models.ai_analysis_model import ValidationRequest, ValidationResponse

router = APIRouter()


@router.post("/validate", response_model=ValidationResponse)
def validate_input(request: ValidationRequest):
    input_value = request.input
    
    # AI 응답 대신 테스트용 하드코딩
    if len(input_value) < 4 :
        return ValidationResponse(
            isValid=False,
            message="좀 더 구체적인 요구사항이 필요해요."
        )
        
    return ValidationResponse(
        isValid=True,
        message="통과~~"
    )