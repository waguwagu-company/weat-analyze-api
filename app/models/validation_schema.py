from pydantic import BaseModel
    
    
class ValidationRequest(BaseModel):
    userInput: str
    
class ValidationResponse(BaseModel):
    isValid: bool
    message: str