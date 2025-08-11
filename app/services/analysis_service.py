from statistics import mean
from typing import Dict, List, Tuple, Optional, Any
from app.test.dto.ai_analysis_request_dto import AIAnalysisRequest, MemberSetting
from app.services.place_service import *
import re
from collections import defaultdict

"""
    분석 요청을 전처리하여 멤버별 설정정보를 하나의 데이터 재구성
    - 사용자 유형(개인/단체)
    - 중심 위치 계산
    - 선호/비선호 카테고리 데이터
    - 사용자 입력 문장 데이터
"""
def analyze_request_preprocessing(request: AIAnalysisRequest) -> Dict:
    members = request.memberSettingList
    group_id = request.groupId

    print(f">> [분석 시작] groupId = {group_id}")
    print(f">> 총 멤버 수: {len(members)}")

    base_x, base_y, is_group = calculate_base_position(members)
    print(f">> 분석 유형: {'단체' if is_group else '개인'}")

    # 카테고리 태그 취합 (태그별로 선호/비선호 개수 증가)
    category_tag_count = defaultdict(lambda: {"preferred": 0, "non_preferred": 0})
    for m in members:
        for c in m.categoryList:
            if c.categoryTagName:
                if c.isPreferred:
                    category_tag_count[c.categoryTagName]["preferred"] += 1
                else:
                    category_tag_count[c.categoryTagName]["non_preferred"] += 1

    print(f">> 카테고리 태그 취합 결과: {dict(category_tag_count)}")

    # 비정형 입력 취합
    all_input_texts = [m.inputText for m in members if m.inputText]
    print(f">> 비정형 문장 개수: {len(all_input_texts)}")

    return {
        "groupId": group_id,
        "isGroup": is_group,
        "memberCount": len(members),
        "basePosition": {
            "x": base_x,
            "y": base_y
        },
        "categoryPreference": dict(category_tag_count),
        "inputTextSummarySource": all_input_texts
    }

"""
AI를 활용하여 분석설정 취합 및 요약
"""
async def summarize_group_preferences_with_ai(request: AIAnalysisRequest) -> Dict[str, str]:

    # 요청 전처리
    preprocessed = analyze_request_preprocessing(request)
    print(f"요정 전처리 완료")
    category_tag_count = preprocessed["categoryPreference"]
    input_texts = preprocessed["inputTextSummarySource"]

    # 프롬프트 생성
    category_prompt = build_category_prompt(category_tag_count)
    print(f"Category Prompt: {category_prompt}")
    input_text_prompt = build_input_text_prompt(input_texts)
    print(f"Input Text Prompt: {input_text_prompt}")
    

    # Clova에 요청
    category_response_text = await call_clova_ai(prompt=category_prompt, analysis_data="")
    input_text_response_text = await call_clova_ai(prompt=input_text_prompt, analysis_data="")

    return {
        "categoryResponse": category_response_text.split(";"),
        "inputTextResponse": input_text_response_text
    }


"""
멤버들의 위치 설정을 기반으로 기준 위치(x, y)를 계산
개인으로 분석하는 경우 설정한 위치를 그대로 사용하고, 그룹일 경우 평균값을 계산

Args:
    members (List[MemberSetting]): 위치 정보가 포함된 사용자 리스트

Returns:
    Tuple[float, float, bool]: (기준 x 좌표, 기준 y 좌표, 단체 여부)
"""
def calculate_base_position(members: List[MemberSetting]) -> Tuple[float, float, bool]:

    is_group = len(members) > 1

    if is_group:
        base_x = mean([m.xPosition for m in members])
        base_y = mean([m.yPosition for m in members])
        print(f">> 중간 위치 사용: x = {base_x}, y = {base_y}")
    else:
        base_x = members[0].xPosition
        base_y = members[0].yPosition
        print(f">> 개인 위치 사용: x = {base_x}, y = {base_y}")

    return base_x, base_y, is_group


"""
단체 사용자의 카테고리태그 데이터를 기반으로, 
AI에게 카테고리태그 취합 요청을 위한 프롬프트 생성
"""
def build_category_prompt(category_tag_count: dict) -> str:
    if not category_tag_count:
        return "사용자들이 선택한 선호/비선호 음식 태그가 없습니다."

    print(f"build_category_prompt")
    category_tags = []
    for tag_name, counts in category_tag_count.items():
        category_tags.append({
            "tag": tag_name,
            "preferred": counts["preferred"],
            "non_preferred": counts["non_preferred"]
        })

    # 상위 2개의 선호 태그만 요청
    tag_lines = "\n".join(
        [f"- {tag['tag']} (선호: {tag['preferred']}, 비선호: {tag['non_preferred']})"
        for tag in category_tags]
    )

    prompt = f"""
    다음은 사용자들이 선택한 음식 태그입니다. 아래의 데이터를 바탕으로 선호도와 비선호도를 고려하여 **2개의 태그**만 선정해 주세요:
    {tag_lines}

    2개의 태그를 선택한 뒤 아무런 부연 설명 없이 세미콜론(;)으로 구분하여 보내주세요.
    응답 형식: 
    태그명;태그명
    """
    
    return prompt


"""
    여러 사용자의 비정형 입력값들을 기반으로
    AI가 하나의 조건 요약문으로 정리할 수 있도록 요청 프롬프트 생성
"""
def build_input_text_prompt(input_texts: list[str]) -> str:

    if not input_texts:
        return "사용자들이 입력한 음식점에 대한 요구 조건이 없습니다."

    bullet_points = "\n".join(f"- {text}" for text in input_texts)

    # TODO: 프롬프트 템플릿은 분석 파이프라인 완성 후 수정 필요
    prompt = (
        "다음은 사용자들이 음식점에 대해 요청한 조건입니다:\n"
        + bullet_points
        + "\n\n위 내용을 바탕으로 모두의 의견을 반영하는 하나의 문장으로 요약해주세요."
    )
    return prompt



"""
단일 리뷰에 대해 사용자의 요구조건과 얼마나 부합하는지 AI 평가 요청
Returns:
    float: 적합도 점수 (0.0~10.0) 또는 기본값 1.0
"""
async def score_reviews_with_ai(review_texts: List[str], user_conditions: str) -> List[float]:
    reviews_prompt = "\n".join(review_texts)
    
    prompt = (
        f"다음은 음식점 리뷰입니다:\n\"{reviews_prompt}\"\n\n"
        f"사용자 조건: {user_conditions}\n"
        "위 리뷰들이 해당 조건에 얼마나 부합하는지 평가하여 10점 만점으로 차례대로 점수를 매겨주세요.\n"
        "소수점 첫째 자리까지 반영해서 평가해 주세요.\n"
        "숫자만 답하되 각 리뷰의 점수를 아래와 같이 세미콜론(;)으로 구분하여 차례대로 적어주세요."
        "어떤 경우에도 부연 설명은 하지 말고 아래 형식으로 답해주세요."
        "0.0;0.0;0.0"
    )

    response = await call_clova_ai(prompt)
    print(f"클로바 응답 Content: {response}")
    
    # 여러 점수를 세미콜론으로 구분하여 받기 (예: "9.5;4.0;10.0")
    scores = []
    for score_str in response.split(";"):
        # 숫자만 추출
        match = re.search(r'\b(10(?:\.0)?|[0-9](?:\.[0-9])?)\b', score_str)
        if match:
            score = float(match.group(1))
            scores.append(min(max(score, 0.0), 10.0))
        else:
            # 점수 파싱 실패 시 기본값 1.0
            print(f"[AI 응답 파싱 실패] 원본 응답: {score_str} → 기본값 1.0 반환")
            scores.append(1.0)

    print(f"[AI 응답 파싱 성공] {response} → 점수들: {scores}")
    return scores

"""
해당 장소의 리뷰들에 대해 AI 적합도 평가 → 평균 점수 반환
추가로 topReviews 필드에 상위 리뷰 5개 저장
"""
# 현재 미사용 함수
# async def calculate_place_score(place: Dict[str, Any], user_conditions: str) -> float:
#     reviews = place.get("reviews", [])[:10]  # 최대 10개 평가

#     if not reviews:
#         place["topReviews"] = []
#         return 0.0

#     scored_reviews = []
#     for r in reviews:
#         score = await score_review_with_ai(r["text"], user_conditions)
#         if score is not None:
#             scored_reviews.append({
#                 "text": r["text"],
#                 "score": score,
#                 "author": r.get("author", None)
#             })

#     if not scored_reviews:
#         place["topReviews"] = []
#         return 0.0

#     # 점수 높은 순으로 정렬 후 상위 5개만 유지
#     top_reviews = sorted(scored_reviews, key=lambda x: x["score"], reverse=True)[:5]

#     # 장소에 topReviews 필드 추가
#     place["topReviews"] = top_reviews

#     # 평균 점수 반환
#     return round(sum(r["score"] for r in scored_reviews) / len(scored_reviews), 2)

"""
모든 장소에 대해 AI 기반 점수 계산 후 상위 N개 반환
"""
async def evaluate_places_and_rank(
    places: List[Dict[str, Any]], user_conditions: str, top_k: int = 3
) -> List[Dict[str, Any]]:

    scored_places = []

    try: 
        for idx, place in enumerate(places, start=1):
            print(f"\n[장소 {idx}] {place.get('name', '이름 없음')} 평가 시작")
            reviews = place.get("reviews", [])[:10]
            top_reviews = []
            
            # ===== 리뷰 데이터 점검 =====
            if not reviews:
                print("[DEBUG] reviews 리스트가 비어있습니다.")
            else:
                for r_idx, r in enumerate(reviews, start=1):
                    if not isinstance(r, dict):
                        print(f"[DEBUG] 리뷰 {r_idx} 비정상 데이터(타입):", r)
                    elif r.get("text") is None:
                        print(f"[DEBUG] 리뷰 {r_idx} text 없음:", r)
            
            # ===== 리뷰 텍스트 생성 (널 가드) =====
            review_texts = [
                f"{i+1}번 리뷰: { (r.get('text') or '') }"
                for i, r in enumerate(reviews or [])
                if isinstance(r, dict)
            ]
            
            # ==== AI로 점수 계산 ====
            scores = await score_reviews_with_ai(review_texts, user_conditions)

            # ===== 각 리뷰에 점수 매핑 =====
            for i, (r, score) in enumerate(zip(reviews or [], scores), start=1):
                if not isinstance(r, dict):
                    continue
                r["score"] = score
                text_preview = (r.get("text") or "")[:30]
                if score is not None:
                    top_reviews.append(r)
                    print(f"  [리뷰 {i}] \"{text_preview}...\" → 점수: {score}")
                else:
                    print(f"  [리뷰 {i}] \"{text_preview}...\" → 점수 계산 실패 (기본값 사용)")

            # 점수를 기준으로 상위 2개 리뷰 정렬
            top_reviews_sorted = sorted(top_reviews, key=lambda r: r["score"], reverse=True)
            place["topReviews"] = top_reviews_sorted[:2]

            # 평균 점수 계산
            avg_score = round(
                sum(r["score"] for r in top_reviews_sorted) / len(top_reviews_sorted), 2
            ) if top_reviews_sorted else 0.0

            place["score"] = avg_score
            scored_places.append(place)

            print(f"  → 종합 점수: {avg_score}")
            print(f"  → Top 리뷰:")
            for t_idx, t in enumerate(place["topReviews"], start=1):
                text_preview = (t.get("text") or "")[:50] if isinstance(t, dict) else ""
                print(f"  {t_idx}. {text_preview}... (점수: {t.get('score')})")
    except Exception as e:
        print(f"[ERROR] 리뷰 분석 중 실패: {e}")

    # 최종 결과를 점수를 기준으로 정렬
    scored_places.sort(key=lambda p: p["score"], reverse=True)

    print("\n==============================")
    print("[최종 추천 장소 TOP3 점수]")
    for rank, p in enumerate(scored_places[:top_k], start=1):
        text_preview = (t.get("text") or "")[:50] if isinstance(t, dict) else ""
        print(f"  {t_idx}. {text_preview}... (점수: {t.get('score')})")
    print("==============================\n")

    return scored_places[:top_k]

async def run_place_recommendation_pipeline(request: AIAnalysisRequest) -> Dict[str, Any]:
    # 요약/분석
    ai_summary = await summarize_group_preferences_with_ai(request)
    user_condition = ai_summary["inputTextResponse"]

    # 기준 위치
    preprocessed = analyze_request_preprocessing(request)
    base_x = preprocessed["basePosition"]["x"]
    base_y = preprocessed["basePosition"]["y"]
    group_id = preprocessed["groupId"]

    # 장소 조회
    places = await fetch_nearby_place_infos(base_x, base_y, ai_summary["categoryResponse"])
    
    # 적합도 평가
    top_places = await evaluate_places_and_rank(places, user_condition)

    # 상위 장소들의 사진 url 가져오기
    top_places = await fetch_place_images(top_places)

    response = convert_to_response_format(group_id, top_places)
    return response

"""
API 응답 형식에 맞춰 추천 장소(top_places) 리스트 변환
"""
def convert_to_response_format(group_id: str, top_places: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "groupId": group_id,
        "analysisResult": {
            "analysisResultDetailList": [
                {
                    "place": {
                        "placeName": place.get("name"),
                        "placeRoadNameAddress": place.get("address"),
                        "placeImageList": [
                            {"placeImageUrl": url}
                            for url in place.get("photos", [])
                        ]
                    },
                    "analysisResultDetailContent": (
                        place.get("topReviews", [{}])[0].get("text", "")
                        if place.get("topReviews") else ""
                    ),
                    "analysisBasisList": [
                        {
                            "analysisBasisType": "REVIEW",
                            "analysisBasisContent": review.get("text")
                        }
                        for review in place.get("topReviews", [])[:2]
                    ]
                }
                for place in top_places
            ]
        }
    }

####





import httpx
import logging
from app.core.config import CLOVA_API_KEY, CLOVA_API_URL

log = logging.getLogger(__name__)

async def call_clova_ai(prompt: str, analysis_data: str = "") -> str:
    """
    CLOVA Chat Completion API 호출
    응답을 문자열로 받아서 처리
    """
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {CLOVA_API_KEY}"
    }

    body = {
        "messages": [
            {
                "role": "user",
                "content": prompt + "\n\n[사용자 데이터]:\n" + analysis_data
            }
        ],
        "topP": 0.8,
        "temperature": 0.7,
        "maxTokens": 1000,
        "repeatPenalty": 1.1,
        "stopBefore": [],
        "includeAiFilters": False
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"[CLOVA 요청 바디]: {body}")
            response = await client.post(CLOVA_API_URL, headers=headers, json=body)
            print(f"[CLOVA 응답 바디]: {response.text}")

            response.raise_for_status()
            data = response.json()

            content = data.get("result", {}).get("message", {}).get("content", "")
            if not content:
                return "[CLOVA 응답 없음] result.message.content 비어있음"

            return content.strip()

    except httpx.HTTPStatusError as e:
        log.error(f"[CLOVA HTTP 오류] {e.response.status_code} - {e.response.text}")
        return f"[CLOVA 오류] 상태 코드 {e.response.status_code} - {e.response.text}"

    except Exception as e:
        log.exception("[CLOVA 예외]")
        return f"[CLOVA 예외] {str(e)}"

