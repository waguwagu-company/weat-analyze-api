from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.common.responses import ErrorResponse
from app.common.error_codes import ErrorCode

import logging
log = logging.getLogger(__name__)

# 일반 예외 처리
async def global_exception_handler(request: Request, exc: Exception):
    log.exception("서버 내부 에러 발생")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code=ErrorCode.SERVER_ERROR.code,
            message=ErrorCode.SERVER_ERROR.message
        ).model_dump()
    )
