from fastapi import FastAPI
from app.routes.test import router as test

app = FastAPI()

app.include_router(test)