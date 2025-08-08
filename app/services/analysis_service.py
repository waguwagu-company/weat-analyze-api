from statistics import mean
from typing import Dict, List, Tuple
from app.test.dto.ai_analysis_request_dto import AIAnalysisRequest, MemberSetting

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