from enum import Enum

class ErrorCode(Enum):
    AI_EMPTY_RESPONSE = ("40001", "AI 응답이 비어 있습니다.")
    INVALID_JSON_FORMAT = ("40002", "AI 응답 형식이 잘못되었습니다.")
    AI_INTERNAL_ERROR = ("50001", "AI 내부 오류가 발생했습니다.")
    AI_RESPONSE_FAIL = "50002", "AI 응답에 실패하였습니다."
    
    SERVER_ERROR = ("50000", "서버 오류가 발생했습니다.")

    def __init__(self, code: str, message: str):
        self._code = code
        self._message = message

    @property
    def code(self) -> str:
        return self._code

    @property
    def message(self) -> str:
        return self._message