import requests, logging, httpx, json
from app.core.config import CLOVA_API_KEY, CLOVA_API_URL


async def request_ai_analysis(prompt: str, analysis_data: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLOVA_API_KEY}"
    }
    
    body = {
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": analysis_data}
        ],
        
        # 추후 변경 필요할 경우 파라미터로 받기
        "topP": 0.8,
        "temperature": 0.7,
        "maxTokens": 500,
        "repeatPenalty": 1.1,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logging.info(f"요청 바디: {json.dumps(body, indent=2, ensure_ascii=False)}")
            response = await client.post(CLOVA_API_URL, headers=headers, json=body)
            
            logging.info(f"응답 바디: {response.text}")

            response.raise_for_status()
            return response.json()["result"]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logging.error(f"CLOVA API HTTP 오류: {e.response.status_code} - {e.response.text}")
        return json.dumps({
            "isValid": False,
            "message": "AI 호출에 실패했어요. 다시 시도해 주세요."
        })
    except Exception as e:
        logging.exception("예기치 못한 오류")
        return json.dumps({
            "isValid": False,
            "message": "잠시 오류가 발생했어요. 나중에 다시 시도해 주세요."
        })
