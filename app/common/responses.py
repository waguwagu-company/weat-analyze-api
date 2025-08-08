from pydantic import BaseModel
from typing import Optional



class ErrorResponse(BaseModel):
    success: bool = False
    code: str
    message: Optional[str] = None
    
class SuccessResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
