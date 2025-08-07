from fastapi import FastAPI
from app.routes.test import router as test
from app.routes.ai_validation import router as validation

app = FastAPI()

app.include_router(test)
app.include_router(validation)