import httpx
import json
import math
from pprint import pprint
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.core.config import GOOGLE_PLACES_API_KEY, GOOGLE_PLACES_API_MODE
from app.models.google_places_schema import PlacesResponse
from app.models.google_places_schema import PlaceDetailResponse


NUMBER_OF_PHOTOS_TO_FETCH = 1             # 결과별로 반환할 사진 개수

"""
기준 위치(x, y)를 기반으로 주변 음식점 정보를 검색하고,
각 장소의 리뷰 정보만 수집하여 반환. (사진은 포함하지 않음)

Returns:
    List[Dict]: 각 장소의 정보 및 리뷰 목록
"""
async def fetch_nearby_place_infos(
    x: float,
    y: float,
    category_tags: List[str],
    radius: float = 500.0,
    limit: int = 10
) -> List[Dict[str, Any]]:
    try:
        places_data: List[Dict[str, Any]] = []
        seen_place_id_set = set()

        # 1. 태그 키워드 기반 텍스트 포함하여 위치 검색
        for tag in category_tags:
            if len(places_data) >= limit:
                break

            result = await call_search_nearby_places_with_text_api(
                latitude=x, longitude=y, radius=radius, max_results=limit, keyword=tag
            )

            for place in getattr(result, "places", []) or []:
                if len(places_data) >= limit:
                    break

                place_id = getattr(place, "id", None)
                if not place_id or place_id in seen_place_id_set:
                    continue

                seen_place_id_set.add(place_id)

                place_info = {
                    "placeId": place_id,
                    "name": getattr(getattr(place, "displayName", None), "text", None),
                    "address": getattr(place, "formattedAddress", None),
                    "ratingCount": getattr(place, "userRatingCount", None),
                    "priceLevel": getattr(place, "priceLevel", None),
                    "placeUrl": getattr(place, "googleMapsUri", None),
                    "reviews": [],
                    "photos": []  # 사진 미포함 정책 유지
                }

                # 리뷰 정보 포함 (없으면 빈 리스트)
                reviews = getattr(place, "reviews", None) or []
                place_info["reviews"] = [
                    {
                        "author": getattr(getattr(r, "authorAttribution", None), "displayName", None),
                        "rating": getattr(r, "rating", None),
                        "text": getattr(getattr(r, "text", None), "text", None),
                    }
                    for r in reviews
                ]

                places_data.append(place_info)

        print(f"카테고리 태그 텍스트기반 장소검색 수 => {len(places_data)}개")

        """
        # TODO: 테스트를 위해 임시 비활성화
        
        # 2. 텍스트 기반 검색 결과가 부족한 경우 단순히 위치 기반 조회로 보완
        if len(places_data) < limit:

            needed = limit - len(places_data)
            nearby_result = await call_search_nearby_places_api(
                latitude=x, longitude=y, radius=radius, max_results=needed,
            )

            print(f"단순 위치기반 장소검색 API 호출({needed}개 보완)")
            for place in getattr(nearby_result, "places", []) or []:
                if len(places_data) >= limit:
                    break

                place_id = getattr(place, "id", None)
                if not place_id or place_id in seen_place_id_set:
                    continue

                seen_place_id_set.add(place_id)

                place_info = {
                    "placeId": place_id,
                    "name": getattr(getattr(place, "displayName", None), "text", None),
                    "address": getattr(place, "formattedAddress", None),
                    "ratingCount": getattr(place, "userRatingCount", None),
                    "priceLevel": getattr(place, "priceLevel", None),
                    "placeUrl": getattr(place, "googleMapsUri", None),
                    "reviews": [],
                    "photos": []
                }

                reviews = getattr(place, "reviews", None) or []
                place_info["reviews"] = [
                    {
                        "author": getattr(getattr(r, "authorAttribution", None), "displayName", None),
                        "rating": getattr(r, "rating", None),
                        "text": getattr(getattr(r, "text", None), "text", None),
                    }
                    for r in reviews
                ]

                places_data.append(place_info)
            """
        print(f"총 장소 개수 => {len(places_data)}")
        return places_data

    except Exception as e:
        print(f"[장소 조회 오류] {e}")
        return []


"""
 중심 좌표기준 반경 n 미터 BBOX 연산
"""
def calculate_bbox(lat: float, lot: float, radius: float):

    # bbox 산출시 설정 반경 2배로 재조정
    resized_radius = 2 * radius

    R = 6378137.0  # WGS84 좌표계
    lat_rad = math.radians(lat)

    # 위도
    lat_min = lat - math.degrees(resized_radius / R)
    lat_max = lat + math.degrees(resized_radius / R)

    # 경도
    lon_min = lot - math.degrees(resized_radius / R * math.cos(lat_rad))
    lon_max = lot + math.degrees(resized_radius / R * math.cos(lat_rad))
    return lat_min, lon_min, lat_max, lon_max


"""
 특정 좌표/주소 기준 인근 장소 조회
"""
async def call_search_nearby_places_api (
        latitude: float,
        longitude: float,
        radius: float = 500.0,
        max_results: int = 20,
        test_json_path: str = "../mock/place_api_response.json"
) -> PlacesResponse:
    mode = GOOGLE_PLACES_API_MODE

    if mode.lower() == "mock":
        print("* 테스트 모드(mock json 응답 사용)")
        json_path = Path(test_json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"테스트 응답 파일이 존재하지 않습니다: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PlacesResponse(**data)

    print("* API 호출")
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": ",".join([
            "places.displayName",
            "places.id",
            "places.userRatingCount",
            "places.priceLevel",
            "places.reviews",
            "places.formattedAddress",
            "places.googleMapsUri"
        ]),
        "Accept-Language": "ko"
    }

    payload = {
        "includedTypes": ["restaurant"],
        "maxResultCount": max_results,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius
            }
        }
    }

    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    return PlacesResponse(**response.json())



"""
 특정 좌표/주소 기준 인근 장소를 텍스트 정보를 포함하여 조회
"""
async def call_search_nearby_places_with_text_api(
        latitude: float,
        longitude: float,
        radius: float = 500.0,
        max_results: int = 10,
        keyword: str = "",
        test_json_path: Optional[str] = None
) -> PlacesResponse:
    mode = GOOGLE_PLACES_API_MODE

    if mode.lower() == "mock":
        print("* 테스트 모드(mock json 응답 사용)")
        base_dir = Path(__file__).resolve().parent.parent  # app/
        json_path = Path(test_json_path) if test_json_path else base_dir / "mock" / "place_api_response.json"
        print(f"[DEBUG] Mock JSON 경로: {json_path}")
        if not json_path.exists():
            raise FileNotFoundError(f"테스트 응답 파일이 존재하지 않습니다: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PlacesResponse(**data)

    print("* API 호출")
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": ",".join([
            "places.displayName",
            "places.id",
            "places.userRatingCount",
            "places.priceLevel",
            "places.reviews",
            "places.formattedAddress",
            "places.googleMapsUri"
        ]),
        "Accept-Language": "ko"
    }

    lat_min, lot_min, lat_max, lot_max = calculate_bbox(latitude, longitude, radius)

    payload = {
        "textQuery": keyword,
        "languageCode": "ko",
        "pageSize": max_results,
        "locationRestriction": {
            "rectangle": {
                "low":  { "latitude": lat_min, "longitude": lot_min },
                "high": { "latitude": lat_max, "longitude": lot_max }
            }
        },
        "rankPreference": "RELEVANCE"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    return PlacesResponse(**response.json())


async def fetch_place_images(top_places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for place in top_places:
        print(f"[{place.get('name', '이름 없음')}] 장소 이름")
        try:
            place_id = place.get("placeId")
            if not place_id:
                print(f"[{place.get('name', '이름 없음')}] 장소 ID 미존재")
                continue

            # 장소 세부 정보 검색
            place_detail = call_place_details_api(place_id, fields="photos")

            # photos_url 리스트에 사진 URL 추가
            if place_detail.result and place_detail.result.photos:
                photos_url = []
                # 개발 단계에서는 사진 2개만 가져오기
                for i, photo in enumerate(place_detail.result.photos[:NUMBER_OF_PHOTOS_TO_FETCH]):
                    photo_reference = photo.photo_reference
                    print(f"photo_reference: {photo_reference}")
                    
                    photo_url = generate_place_photo_url(photo_reference)
                    
                    print(f"사진 URL: {photo_url}")
                    photos_url.append(photo_url)

                place["photos"] = photos_url
            else:
                print(f"사진 없음")


        except Exception as e:
            print(f"[{place.get('name', '이름 없음')}] 사진 가져오기 중 오류 발생: {e}")

    return top_places




"""
특정 장소 세부정보 검색 
"""
def call_place_details_api(
    place_id: str,
    fields: str = "name,photos",
    language: str = "ko"
) -> PlaceDetailResponse:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": fields,
        "language": language,
        "key": GOOGLE_PLACES_API_KEY
    }

    response = httpx.get(url, params=params)
    response.raise_for_status()

    return PlaceDetailResponse(**response.json())

def generate_place_photo_url (photo_reference: str, maxwidth: int = 400) -> Optional[bytes]:
    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "maxwidth": str(maxwidth),
        "photo_reference": photo_reference,
        "key": GOOGLE_PLACES_API_KEY
    }

    with httpx.Client(follow_redirects=True) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        
        # API key가 포함된 url이 아닌 user content url 반환
        return str(response.url)



def place_api_call_test():
    try:
        latitude = 37.5665
        longitude = 126.9780

        result = call_search_nearby_places_with_text_api(latitude, longitude)

        for place in result.places:

            place_detail = call_place_details_api(place.id)
        

            print(f"[{place.displayName.text}]")
            print(f"{place.formattedAddress}")
            print(f"  - 평점 수: {place.userRatingCount}, 가격대: {place.priceLevel}")
            if place.reviews:
                for review in place.reviews[:10]:
                    print(f"  - 리뷰️[별점:{review.rating}]: {review.text.text[:50]}...")
            print()

            print(f"place_detail.result.photos 개수 => {len(place_detail.result.photos)}")

            for idx, photo in enumerate(place_detail.result.photos):
                print(f"[{idx+1}] photo_reference: {photo.photo_reference}")

    except Exception as e:
        print(f"에러 발생: {e}")



if __name__ == "__main__":
    place_api_call_test()