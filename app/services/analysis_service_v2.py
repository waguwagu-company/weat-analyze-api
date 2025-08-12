from statistics import mean
from typing import List, Tuple, Any
from collections import defaultdict
import re
import logging
import httpx
from app.test.dto.ai_analysis_request_dto import AIAnalysisRequest, MemberSetting
from app.services.place_service import fetch_nearby_place_infos, fetch_place_images
from app.services.pipeline_service import PipelineJobExecutionManager, PipelineExecutionManager
from app.core.config import CLOVA_API_KEY, CLOVA_API_URL
from app.models.analysis_model import (
    PreprocessResult, CategoryVote, BasePosition,
    GroupPreferenceSummary, Place, ReviewWithScore,
    AnalysisResponse, AnalysisResultDetail, PlaceResponse, AnalysisBasis
)

log = logging.getLogger(__name__)

NUMBER_OF_TOP_PLACES_TO_RETURN = 2        # 최종 결과에 포함할 장소 개수
NUMBER_OF_TOP_REVIEWS_TO_KEEP = 1        # 각 장소에서 유지할 상위 리뷰 개수
#NUMBER_OF_PHOTOS_TO_FETCH = 2             # 결과별로 반환할 사진 개수

# 파이프라인 작업
PIPELINE_ID = 1
PIPELINE_JOB_ID_ANALYSIS_REQUEST = 1
PIPELINE_JOB_ID_PREPROCESSING = 2
PIPELINE_JOB_ID_COLLECTING_DATA = 3
PIPELINE_JOB_ID_ANALYSIS_START = 4
PIPELINE_JOB_ID_BUILD_RESULT = 5

JOB_ORDER_TO_NAME = {
    1: "ANALYSIS_REQUEST",
    2: "PREPROCESSING",
    3: "COLLECTING_DATA",
    4: "ANALYSIS_START",
    5: "BUILD_RESULT",
}


async def run_place_recommendation_pipeline_v2(request: AIAnalysisRequest) -> AnalysisResponse:
    async with PipelineExecutionManager(
        pipeline_id=PIPELINE_ID,
        analysis_id=request.analysisId,
        initial_stage=0,
    ) as pipeline_tracker:

        # 1. 분석요청
        pipeline_tracker.advance_stage(
            stage=1,
            status=f"RUNNING: {JOB_ORDER_TO_NAME[1]}"
        )
        async with PipelineJobExecutionManager(
            pipeline_job_id=PIPELINE_JOB_ID_ANALYSIS_REQUEST,
            analysis_id=request.analysisId,
            job_execution_request_data=(
                request.model_dump() if hasattr(request, "model_dump") else request.__dict__
            ),
        ) as analysis_request_tracker:
            analysis_request_tracker.attach_result({"received": True})

        # 2. 전처리
        pipeline_tracker.advance_stage(
            stage=2,
            status=f"RUNNING: {JOB_ORDER_TO_NAME[2]}"
        )
        async with PipelineJobExecutionManager(
            pipeline_job_id=PIPELINE_JOB_ID_PREPROCESSING,
            analysis_id=request.analysisId,
            job_execution_request_data={"step": "preprocessing"},
        ) as preprocessing_tracker:
            preprocessed = analyze_request_preprocessing(request)
            preference_summary = await summarize_group_preferences_with_ai(request)
            preprocessing_tracker.attach_result({
                "preprocessed": preprocessed.model_dump(),
                "categoryResponse": preference_summary.categoryResponse,
                "inputTextResponse": preference_summary.inputTextResponse,
            })

        user_condition = preference_summary.inputTextResponse
        base_x = preprocessed.basePosition.x
        base_y = preprocessed.basePosition.y
        group_id = preprocessed.groupId

        # 3. 데이터 수집
        pipeline_tracker.advance_stage(
            stage=3,
            status=f"RUNNING: {JOB_ORDER_TO_NAME[3]}"
        )
        async with PipelineJobExecutionManager(
            pipeline_job_id=PIPELINE_JOB_ID_COLLECTING_DATA,
            analysis_id=request.analysisId,
            job_execution_request_data={
                "base_x": base_x, "base_y": base_y,
                "categoryResponse": preference_summary.categoryResponse
            },
        ) as collecting_tracker:
            raw_places = await fetch_nearby_place_infos(base_x, base_y, preference_summary.categoryResponse)
            places = [dict_to_place(p) for p in raw_places]
            collecting_tracker.attach_result({"placeCount": len(places)})

        # 4. 분석 시작
        pipeline_tracker.advance_stage(
            stage=4,
            status=f"RUNNING: {JOB_ORDER_TO_NAME[4]}"
        )
        async with PipelineJobExecutionManager(
            pipeline_job_id=PIPELINE_JOB_ID_ANALYSIS_START,
            analysis_id=request.analysisId,
            job_execution_request_data={
                "user_condition": user_condition,
                "placeCount": len(places),
                "numberOfTopPlacesToReturn": NUMBER_OF_TOP_PLACES_TO_RETURN,
                "numberOfTopReviewsToKeep": NUMBER_OF_TOP_REVIEWS_TO_KEEP,
            },
        ) as analysis_tracker:
            top_places = await evaluate_places_and_rank(
                places,
                user_conditions=user_condition,
                number_of_top_places_to_return=NUMBER_OF_TOP_PLACES_TO_RETURN,
                number_of_top_reviews_to_keep=NUMBER_OF_TOP_REVIEWS_TO_KEEP,
            )
            analysis_tracker.attach_result({"topPlaceCount": len(top_places)})

        # 5. 결과 생성
        pipeline_tracker.advance_stage(
            stage=5,
            status=f"RUNNING: {JOB_ORDER_TO_NAME[5]}"
        )
        async with PipelineJobExecutionManager(
            pipeline_job_id=PIPELINE_JOB_ID_BUILD_RESULT,
            analysis_id=request.analysisId,
            job_execution_request_data={
                "topPlaceCountBeforeImages": len(top_places),
                "numberOfTopReviewsToKeep": NUMBER_OF_TOP_REVIEWS_TO_KEEP
            },
        ) as build_result_tracker:
            enriched_top_places = await fetch_place_images([p.model_dump() for p in top_places])
            top_places = [dict_to_place(p) for p in enriched_top_places]
            response = convert_to_response_format(
                group_id,
                top_places,
                basis_count=NUMBER_OF_TOP_REVIEWS_TO_KEEP
            )
            build_result_tracker.attach_result({
                "topPlaceCountAfterImages": len(top_places),
                "responseReady": True
            })

        return response


def analyze_request_preprocessing(request: AIAnalysisRequest) -> PreprocessResult:
    members: List[MemberSetting] = request.memberSettingList
    group_id: str = request.groupId

    # 위치 정보 취합
    base_x, base_y, is_group = calculate_base_position(members)

    # 카테고리 설정 취합
    tag_counter: dict[str, CategoryVote] = defaultdict(lambda: CategoryVote())
    for member in members:
        for category in member.categoryList:
            if not category.categoryTagName:
                continue
            vote = tag_counter[category.categoryTagName]
            if category.isPreferred:
                vote.preferred += 1
            else:
                vote.non_preferred += 1
            tag_counter[category.categoryTagName] = vote

    # 비정형 입력 설정 취합
    input_texts = [m.inputText for m in members if m.inputText]

    return PreprocessResult(
        groupId=group_id,
        isGroup=is_group,
        memberCount=len(members),
        basePosition=BasePosition(x=base_x, y=base_y),
        categoryPreference=dict(tag_counter),
        inputTextSummarySource=input_texts
    )


def calculate_base_position(members: List[MemberSetting]) -> Tuple[float, float, bool]:
    is_group = len(members) > 1
    if is_group:
        base_x = mean([m.xPosition for m in members])
        base_y = mean([m.yPosition for m in members])
    else:
        base_x = members[0].xPosition
        base_y = members[0].yPosition
    return base_x, base_y, is_group


def build_category_prompt(category_tag_count: dict[str, CategoryVote]) -> str:
    if not category_tag_count:
        return "사용자들이 선택한 선호/비선호 음식 태그가 없습니다."
    lines = [f"- {tag} (선호: {vote.preferred}, 비선호: {vote.non_preferred})"
             for tag, vote in category_tag_count.items()]
    tag_lines = "\n".join(lines)
    prompt = f"""
다음은 사용자들이 선택한 음식 태그입니다. 아래의 데이터를 바탕으로 선호도와 비선호도를 고려하여 **2개의 태그**만 선정해 주세요:
{tag_lines}

2개의 태그를 선택한 뒤 아무런 부연 설명 없이 세미콜론(;)으로 구분하여 보내주세요.
응답 형식:
태그명;태그명
"""
    return prompt.strip()


def build_input_text_prompt(input_texts: List[str]) -> str:
    if not input_texts:
        return "사용자들이 입력한 음식점에 대한 요구 조건이 없습니다."
    bullets = "\n".join(f"- {t}" for t in input_texts)
    return (
        "다음은 사용자들이 음식점에 대해 요청한 조건입니다:\n"
        + bullets
        + "\n\n위 내용을 바탕으로 모두의 의견을 반영하는 하나의 문장으로 요약해주세요."
    )


async def summarize_group_preferences_with_ai(request: AIAnalysisRequest) -> GroupPreferenceSummary:
    preprocessed = analyze_request_preprocessing(request)
    category_prompt = build_category_prompt(preprocessed.categoryPreference)
    input_text_prompt = build_input_text_prompt(preprocessed.inputTextSummarySource)

    category_response_text = await call_clova_ai(prompt=category_prompt, analysis_data="")
    input_text_response_text = await call_clova_ai(prompt=input_text_prompt, analysis_data="")

    categories = [c.strip() for c in (category_response_text or "").split(";") if c.strip()]
    return GroupPreferenceSummary(
        categoryResponse=categories,
        inputTextResponse=(input_text_response_text or "").strip()
    )


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
    scores: List[float] = []
    for token in (response or "").split(";"):
        m = re.search(r'\b(10(?:\.0)?|[0-9](?:\.[0-9])?)\b', token)
        if m:
            val = float(m.group(1))
            scores.append(min(max(val, 0.0), 10.0))
        else:
            scores.append(1.0)
    return scores


async def evaluate_places_and_rank(
    places: List[Place],
    user_conditions: str,
    number_of_top_places_to_return: int = NUMBER_OF_TOP_PLACES_TO_RETURN,
    number_of_top_reviews_to_keep: int = NUMBER_OF_TOP_REVIEWS_TO_KEEP,
) -> List[Place]:
    scored: List[Place] = []
    for place in places:
        reviews = place.reviews[:10] if place.reviews else []
        review_texts = [f"{i+1}번 리뷰: {(rv.text or '')}" for i, rv in enumerate(reviews)]
        scores = await score_reviews_with_ai(review_texts, user_conditions)

        top_reviews: List[ReviewWithScore] = []
        for rv, sc in zip(reviews, scores):
            top_reviews.append(ReviewWithScore(text=rv.text, author=rv.author, score=sc))

        top_reviews_sorted = sorted(top_reviews, key=lambda r: (r.score or 0), reverse=True)

        # 상위 리뷰 N개
        place.topReviews = top_reviews_sorted[:number_of_top_reviews_to_keep]

        # 평균 점수(전체 리뷰 기반)
        place.score = round(
            sum((r.score or 0) for r in top_reviews_sorted) / len(top_reviews_sorted), 2
        ) if top_reviews_sorted else 0.0

        scored.append(place)

    scored.sort(key=lambda p: (p.score or 0.0), reverse=True)
    # 최종 장소 N개 반환
    return scored[:number_of_top_places_to_return]


def convert_to_response_format(
    group_id: str,
    top_places: List[Place],
    basis_count: int = NUMBER_OF_TOP_REVIEWS_TO_KEEP
) -> AnalysisResponse:
    details: List[AnalysisResultDetail] = []

    for p in top_places:
        # 점수가 가장 높은 리뷰 텍스트 (없으면 "")
        top_text = p.topReviews[0].text if (p.topReviews and p.topReviews[0] and p.topReviews[0].text) else ""

        # 상위 N개 리뷰 (점수+텍스트)
        basis_list: List[AnalysisBasis] = []
        for rv in (p.topReviews[:basis_count] if p.topReviews else []):
            if not rv.text:
                continue
            score_value = rv.score if isinstance(rv.score, (int, float)) else 0.0
            basis_list.append(
                AnalysisBasis(
                    analysisBasisType="REVIEW",
                    analysisBasisContent=f"[{score_value:.1f}점] {rv.text}"
                )
            )

        place_resp = PlaceResponse(
            placeName=p.name,
            placeRoadNameAddress=p.address,
            placeImageList=[{"placeImageUrl": url} for url in (p.photos or [])]
        )

        details.append(
            AnalysisResultDetail(
                place=place_resp,
                analysisResultDetailContent=top_text,   # 리뷰 중 가장 점수가 높은 리뷰
                analysisBasisList=basis_list            # 상위 N개 리뷰(점수 포함)
            )
        )

    return AnalysisResponse(
        groupId=group_id,
        analysisResult={"analysisResultDetailList": details}
    )


def dict_to_place(raw: dict) -> Place:
    reviews_raw = raw.get("reviews") or []
    top_reviews_raw = raw.get("topReviews") or []

    return Place(
        placeId=raw.get("placeId"),
        name=raw.get("name"),
        address=raw.get("address"),
        photos=raw.get("photos", []),
        # 원본 리뷰
        reviews=[
            ReviewWithScore(
                text=(r.get("text") if isinstance(r, dict) else None),
                author=(r.get("author") if isinstance(r, dict) else None),
                score=(r.get("score") if isinstance(r, dict) else None),
            )
            for r in reviews_raw if isinstance(r, dict)
        ],
        # 상위 리뷰(점수 포함)
        topReviews=[
            ReviewWithScore(
                text=(r.get("text") if isinstance(r, dict) else None),
                author=(r.get("author") if isinstance(r, dict) else None),
                score=(r.get("score") if isinstance(r, dict) else None),
            )
            for r in top_reviews_raw if isinstance(r, dict)
        ],
        score=raw.get("score"),
    )


async def call_clova_ai(prompt: str, analysis_data: str = "") -> str:
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
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(CLOVA_API_URL, headers=headers, json=body)
            res.raise_for_status()
            data = res.json()
            return (data.get("result", {}).get("message", {}).get("content", "") or "").strip()
    except httpx.HTTPStatusError as e:
        log.error(f"[CLOVA HTTP 오류] {e.response.status_code} - {e.response.text}")
        return f"[CLOVA 오류] 상태 코드 {e.response.status_code} - {e.response.text}"
    except Exception as e:
        log.exception("[CLOVA 예외]")
        return f"[CLOVA 예외] {str(e)}"