import json, logging
from fastapi import APIRouter, HTTPException
from app.models.validation_schema import ValidationRequest, ValidationResponse
from app.services.ai_request_service import request_ai_analysis, extract_json_from_ai_response
from app.prompts.clova_prompt import SYSTEM_PROMPT_VALIDATION
from app.common.responses import SuccessResponse, ErrorResponse
from app.common.error_codes import ErrorCode

router = APIRouter()
log = logging.getLogger(__name__)

@router.post("/api/validate", response_model=ValidationResponse)
async def validate_input(request: ValidationRequest):
    try:
        ai_result = await request_ai_analysis(SYSTEM_PROMPT_VALIDATION, request.userInput)
        
         # 실패 시 spring으로 500 응답
        if isinstance(ai_result, ErrorResponse):
            raise HTTPException(
                status_code=500,
                detail=ai_result.model_dump()
            )
        
        # content 안에서 JSON만 추출
        parsed_ai_result = extract_json_from_ai_response(ai_result)
        if not parsed_ai_result:
            error = ErrorCode.INVALID_JSON_FORMAT
            return ErrorResponse(code=error.code, message=error.message)

        return ValidationResponse(**parsed_ai_result)
    
    except Exception as e:
        log.exception("AI 응답 실패")
        error = ErrorCode.AI_RESPONSE_FAIL
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(code=error.code, message=error.message).model_dump()
        )