from fastapi import FastAPI

from app.routes.pipeline_router import router as pipeline_router
from app.routes.analysis_router import router as analysis_router
from app.routes.validation_router import router as validation

app = FastAPI()

app.include_router(analysis_router)
app.include_router(validation)
app.include_router(pipeline_router)
