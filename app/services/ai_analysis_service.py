import requests
from app.core.config import CLOVA_API_KEY, CLOVA_API_URL

SYSTEM_PROMPT = """
당신은 사용자들의 요구사항을 분석하고 리뷰 데이터와 대조하여 식당을 추천합니다.. 어쩌구 저쩌구...
프롬프트 관리 방법 어떻게 하지.....
"""

def request_ai_analysis(analysis_data: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLOVA_API_KEY}"
    }
    
    print(CLOVA_API_KEY)
    print(CLOVA_API_URL)

    body = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": analysis_data}
        ],
        "topP": 0.8,
        "temperature": 0.7,
        "maxTokens": 256,
        "repeatPenalty": 1.1,
    }
    
    print(body)

    response = requests.post(CLOVA_API_URL, headers=headers, json=body)
    response.raise_for_status()

    return response.json()["result"]["message"]["content"]
