import requests, logging, httpx, json, re
from app.core.config import CLOVA_API_KEY, CLOVA_API_URL
from app.common.responses import ErrorResponse, SuccessResponse
from app.common.error_codes import ErrorCode
from typing import Optional, Tuple

log = logging.getLogger(__name__)


async def request_ai_analysis(prompt: str, analysis_data: str) -> str:
    log.info(f"CLOVA_API_URL: {CLOVA_API_URL}")
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {CLOVA_API_KEY}"
    }
    
    # 시스템 프롬프트를 따로 보낼 경우 500 에러 발생. 
    # content에 프롬프트와 사용자 입력값을 함께 보내야 제대로 답이 오는 상황
    body = {
        "messages": [
            # {"role": "system", "content": prompt},
            {"role": "user", "content": prompt + "\n\n 분석 대상이 되는 사용자 데이터 및 입력값: " + analysis_data}
        ],
        
        # 추후 변경 필요할 경우 파라미터로 받기
        "topP": 0.8,
        "temperature": 0.7,
        "maxTokens": 2000,
        "repeatPenalty": 1.1,
        "stopBefore": [],
        "includeAiFilters": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            log.info(f"요청 바디: {json.dumps(body, indent=2, ensure_ascii=False)}")
            response = await client.post(CLOVA_API_URL, headers=headers, json=body)
            
            log.info(f"응답 바디: {response.text}")

            response.raise_for_status()
            data = response.json()
            
            if data.get("status", {}).get("code") != "20000":
                log.info(f"CLOVA 응답 상태 오류: {data.get('status')}")
                error = ErrorCode.AI_INTERNAL_ERROR
                return ErrorResponse(code=error.code, message=error.message)

            # Clova 응답 구조에 따라 결과 파싱
            content = data.get("result", {}).get("message", {}).get("content", "")
            if not content:
                error = ErrorCode.AI_EMPTY_RESPONSE
                return ErrorResponse(code=error.code, message=error.message)


            # content 안에서 JSON만 추출 
            parsed_json = extract_json_from_ai_response(content)
            if not parsed_json:
                error = ErrorCode.INVALID_JSON_FORMAT
                return ErrorResponse(code=error.code, message=error.message)

            return parsed_json

    except httpx.HTTPStatusError as e:
        log.error(f"CLOVA API HTTP 오류: {e.response.status_code} - {e.response.text}")
        error = ErrorCode.AI_INTERNAL_ERROR
        return ErrorResponse(code=error.code, message=error.message)

    except Exception as e:
        log.exception("예기치 못한 오류")
        error = ErrorCode.SERVER_ERROR
        return ErrorResponse(code=error.code, message=error.message)




def extract_json_from_ai_response(content: str) -> Optional[dict]:
    # 순수 JSON인 경우
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 마크다운 형식 제거
    markdown_match = re.search(r"```(?:json)?\n([\s\S]+?)\n```", content)
    if markdown_match:
        try:
            return json.loads(markdown_match.group(1))
        except json.JSONDecodeError:
            pass
        
    # 중괄호 부분만 추출
    bracket_match = re.search(r"\{[\s\S]*\}", content)
    if bracket_match:
        try:
            return json.loads(bracket_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None