from fastapi import FastAPI
from app.routes.analysis_router import router as analysis_router
from app.routes.ai_validation import router as validation

app = FastAPI()

app.include_router(analysis_router)
app.include_router(validation)