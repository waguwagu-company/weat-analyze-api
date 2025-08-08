from statistics import mean
from typing import Dict, List, Tuple
from app.test.dto.ai_analysis_request_dto import AIAnalysisRequest, MemberSetting
from app.services.ai_analysis_service import request_ai_analysis
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

    # 카테고리 태그 취합
    all_category_tags = []
    for m in members:
        for c in m.categoryList:
            if c.categoryTagName:
                all_category_tags.append({
                    "tag": c.categoryTagName,
                    "isPreferred": c.isPreferred
                })

    print(f">> 총 카테고리 태그 수: {len(all_category_tags)}")
    preferred = [t for t in all_category_tags if t["isPreferred"]]
    non_preferred = [t for t in all_category_tags if t["isPreferred"] is False]
    print(f"  - 선호 태그 수: {len(preferred)}")
    print(f"  - 비선호 태그 수: {len(non_preferred)}")

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
        "categoryPreference": all_category_tags,
        "inputTextSummarySource": all_input_texts
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
def build_category_prompt(category_tags: list[dict]) -> str:
    if not category_tags:
        return "사용자들이 선택한 선호/비선호 음식 태그가 없습니다."

    lines = []
    for tag in category_tags:
        status = "선호" if tag["isPreferred"] else "비선호"
        lines.append(f"- {tag['tag']} ({status})")

    # TODO: 프롬프트 템플릿은 분석 파이프라인 완성 후 수정 필요
    prompt = (
        "다음은 사용자들이 입력한 음식 선호 태그입니다:\n"
        + "\n".join(lines)
        + "\n\n위 데이터를 바탕으로, 가능한 한 모두의 취향을 존중할 수 있는 음식 태그를 선정해 주세요.\n"
        + "너무 많은 태그를 포함하지 말고, 공통된 선호를 고려하여 **3개 정도**만 추려 주세요.\n"
        + "응답에는 \"어떤 설명도 포함하지 말고\", 아래와 같은 형식으로 숫자와 태그명만 출력해 주세요:\n\n"
        + "1. 뷔페\n"
        + "2. 돼지고기\n"
        + "3. 게/랍스터"
    )
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