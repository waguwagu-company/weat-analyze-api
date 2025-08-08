from pydantic import BaseModel

# 테스트용 모델
class AnalysisRequest(BaseModel):
    data: str

class ChatResponse(BaseModel):
    reply: str
    
    
class ValidationRequest(BaseModel):
    userInput: str
    
class ValidationResponse(BaseModel):
    isValid: bool
    message: str