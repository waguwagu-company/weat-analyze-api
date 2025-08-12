import requests, logging, httpx, json, re
from app.core.config import CLOVA_API_KEY, CLOVA_API_URL
from app.common.responses import ErrorResponse, SuccessResponse
from app.common.error_codes import ErrorCode
from typing import Optional
import asyncio

RETRY = 2


async def request_ai_analysis(prompt: str, analysis_data: str) -> str:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {CLOVA_API_KEY}"
    }
    
    body = {
        "messages": [
            # {"role": "system", "content": prompt},
            {
                "role": "user", 
                "content": prompt + "\n\n [사용자 데이터]: \n" + analysis_data
            }
        ],
        
        "topP": 0.8,
        "temperature": 0.7,
        "maxTokens": 2000,
        "repeatPenalty": 1.1,
        "stopBefore": [],
        "includeAiFilters": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"요청 바디: {json.dumps(body, indent=2, ensure_ascii=False)}")
            response = await client.post(CLOVA_API_URL, headers=headers, json=body)
            
            print(f"응답 바디: {response.text}")

            response.raise_for_status()
            data = response.json()
            
            if data.get("status", {}).get("code") != "20000":
                print(f"CLOVA 응답 상태 오류: {data.get('status')}")
                error = ErrorCode.AI_INTERNAL_ERROR
                return ErrorResponse(code=error.code, message=error.message)

            content = data.get("result", {}).get("message", {}).get("content", "")
            if not content:
                error = ErrorCode.AI_EMPTY_RESPONSE
                return ErrorResponse(code=error.code, message=error.message)

            return content.strip()

    except httpx.HTTPStatusError as e:
        print(f"CLOVA API HTTP 오류: {e.response.status_code} - {e.response.text}")
        error = ErrorCode.AI_INTERNAL_ERROR
        return ErrorResponse(code=error.code, message=error.message)

    except Exception as e:
        print("CLOVA 오류")
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



async def call_clova_ai_with_client(client: httpx.AsyncClient, prompt: str, analysis_data: str = "") -> str:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {CLOVA_API_KEY}"
    }
    body = {
        "messages": [{"role": "user", "content": prompt + "\n\n[사용자 데이터]:\n" + analysis_data}],
        "topP": 0.8,
        "temperature": 0.7,
        "maxTokens": 1000,
        "repeatPenalty": 1.1,
        "stopBefore": [],
        "includeAiFilters": False
    }

    last_err = None
    for attempt in range(RETRY + 1):
        try:
            res = await client.post(CLOVA_API_URL, headers=headers, json=body, timeout=30.0)
            res.raise_for_status()
            data = res.json()
            return (data.get("result", {}).get("message", {}).get("content", "") or "").strip()
        except httpx.HTTPStatusError as e:
            last_err = e
            # 429/5xx는 재시도, 그 외는 즉시 실패
            if e.response.status_code not in (429, 500, 502, 503, 504) or attempt == RETRY:
                print(f"[CLOVA HTTP 오류] {e.response.status_code} - {e.response.text}")
                return f"[CLOVA 오류] 상태 코드 {e.response.status_code} - {e.response.text}"
        except Exception as e:
            last_err = e
            if attempt == RETRY:
                print("[CLOVA 예외]")
                return f"[CLOVA 예외] {str(e)}"
        # 지수 백오프
        await asyncio.sleep(0.5 * (2 ** attempt))
    # 여기 오면 모두 실패
    return f"[CLOVA 예외] {str(last_err) if last_err else '알 수 없는 오류'}"