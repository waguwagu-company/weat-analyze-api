from fastapi import FastAPI

from app.routes.pipeline_router import router as pipeline_router
from app.routes.analysis_router import router as analysis_router
from app.routes.validation_router import router as validation
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://weat.kro.kr"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(validation)
app.include_router(pipeline_router)
