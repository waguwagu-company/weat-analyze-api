import json, logging
from fastapi import APIRouter, HTTPException, Request
from app.models.ai_analysis_model import ValidationRequest, ValidationResponse
from app.services.ai_analysis_service import request_ai_analysis
from app.prompts.clova_prompt import SYSTEM_PROMPT_VALIDATION

router = APIRouter()


@router.post("/api/validate", response_model=ValidationResponse)
async def validate_input(request: ValidationRequest):
    
    ai_response_str = await request_ai_analysis(SYSTEM_PROMPT_VALIDATION, request.input)
        
    logging.info(f"ai 응답: {ai_response_str}")
    try:
        parsed = json.loads(ai_response_str)
        return ValidationResponse(**parsed)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        logging.info(f"에러: {e}")
        return ValidationResponse(
            isValid=False,
            message="입력을 이해하지 못했어요. 다시 한번 입력해 주세요?????"
        )