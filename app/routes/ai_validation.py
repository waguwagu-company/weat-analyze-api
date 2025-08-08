import json, logging
from fastapi import APIRouter, HTTPException
from app.models.ai_analysis_model import ValidationRequest, ValidationResponse
from app.services.ai_analysis_service import request_ai_analysis
from app.prompts.clova_prompt import SYSTEM_PROMPT_VALIDATION
from app.common.responses import SuccessResponse, ErrorResponse
from app.common.error_codes import ErrorCode

router = APIRouter()


@router.post("/api/validate", response_model=ValidationResponse)
async def validate_input(request: ValidationRequest):
    
    ai_result = await request_ai_analysis(SYSTEM_PROMPT_VALIDATION, request.input)
        
    # 실패 시 spring으로 500 응답
    if isinstance(ai_result, ErrorResponse):
        raise HTTPException(
            status_code=500,
            detail=ai_result.dict()
        )

    try:
        parsed = ValidationResponse(**ai_result.data)
        return SuccessResponse(data=parsed.dict())
    except Exception as e:
        logging.exception("AI 응답 파싱 실패")
        error = ErrorCode.AI_INVALID_JSON
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(code=error.code, message=error.message).dict()
        )