import requests, logging, httpx, json, re
from app.core.config import CLOVA_API_KEY, CLOVA_API_URL


async def request_ai_analysis(prompt: str, analysis_data: str) -> str:
    print(f"CLOVA_API_URL: {CLOVA_API_URL}")
    
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
            print(f"요청 바디: {json.dumps(body, indent=2, ensure_ascii=False)}")
            response = await client.post(CLOVA_API_URL, headers=headers, json=body)
            
            print(f"응답 바디: {response.text}")

            response.raise_for_status()
            data = response.json()
            
            if data.get("status", {}).get("code") != "20000":
                print(f"CLOVA 응답 상태 오류: {data.get('status')}")
                return json.dumps({
                    "isValid": False,
                    "message": "AI 응답 상태 코드 오류가 발생했어요. 다시 시도해 주세요."
                })

            # Clova 응답 구조에 따라 결과 파싱
            content = data.get("result", {}).get("message", {}).get("content", "")
            if not content:
                logging.error("Clova 응답에서 content가 비어 있습니다.")
                return json.dumps({
                    "isValid": False,
                    "message": "AI 응답이 비어 있습니다. 다시 시도해 주세요."
                })


            # content 안에서 JSON만 추출 
            match = re.search(r'\{[\s\S]*\}', content)
            if not match:
                logging.error(f"응답 content에서 JSON을 찾을 수 없습니다: {content}")
                return json.dumps({
                    "isValid": False,
                    "message": "AI 응답에서 유효한 JSON 형식을 찾지 못했어요."
                })

            extracted_json_str = match.group(0)
            try:
                parsed = json.loads(extracted_json_str)
                return json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError as e:
                logging.error(f"JSON 파싱 실패: {e}")
                return json.dumps({
                    "isValid": False,
                    "message": "AI 응답 형식이 잘못되어 파싱할 수 없습니다."
                })
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
