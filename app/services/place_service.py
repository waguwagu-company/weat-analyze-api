import httpx
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.core.config import GOOGLE_PLACES_API_KEY, GOOGLE_PLACES_API_MODE
from app.models.search_nearby_places_api_response import PlacesResponse
from app.models.place_detail_api_response import PlaceDetailResponse

"""
기준 위치(x, y)를 기반으로 주변 음식점 정보를 검색하고,
각 장소의 리뷰 정보만 수집하여 반환. (사진은 포함하지 않음)

Returns:
    List[Dict]: 각 장소의 정보 및 리뷰 목록
"""
async def fetch_nearby_place_infos(x: float, y: float, radius: float = 500.0, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        result = call_search_nearby_places_api(latitude=x, longitude=y, radius=radius, max_results=limit)

        places_data = []

        for place in result.places:
            place_info = {
                "placeId": place.id,
                "name": place.displayName.text,
                "address": place.formattedAddress,
                "ratingCount": place.userRatingCount,
                "priceLevel": place.priceLevel,
                "reviews": []
            }

            # 리뷰 정보 포함
            if place.reviews:
                place_info["reviews"] = [
                    {
                        "author": r.authorAttribution.displayName,
                        "rating": r.rating,
                        "text": r.text.text
                    }
                    for r in place.reviews
                ]

            places_data.append(place_info)

        return places_data

    except Exception as e:
        print(f"[장소 조회 오류] {e}")
        return []

"""
 특정 좌표/주소 기준 인근 장소 조회
"""
def call_search_nearby_places_api (
        latitude: float,
        longitude: float,
        radius: float = 500.0,
        max_results: int = 20,
        test_json_path: Optional[str] = None
) -> PlacesResponse:
    mode = GOOGLE_PLACES_API_MODE

    if mode.lower() == "mock":
        print("* 테스트 모드(mock json 응답 사용)")

        # 현재 파일(app/api/places_api.py 등) 기준 상위 디렉터리로부터 mock 경로 설정
        base_dir = Path(__file__).resolve().parent.parent  # app/
        json_path = Path(test_json_path) if test_json_path else base_dir / "mock" / "place_api_response.json"

        print(f"[DEBUG] Mock JSON 경로: {json_path}")

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
            "places.formattedAddress"
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

def call_place_photo_api (photo_reference: str, maxwidth: int = 400) -> Optional[bytes]:
    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "maxwidth": str(maxwidth),
        "photo_reference": photo_reference,
        "key": GOOGLE_PLACES_API_KEY
    }

    with httpx.Client(follow_redirects=True) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.content



def place_api_call_test():
    try:
        latitude = 37.5665
        longitude = 126.9780

        result = call_search_nearby_places_api(latitude, longitude)

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