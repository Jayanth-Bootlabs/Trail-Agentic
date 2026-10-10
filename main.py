import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from middleware.middleware import UserTypeMiddleware
from utils.cache import init_redis
from database.connection import init_db
from routes import (
    user_routes,
    validation_routes,
    code_routes,
    unit_test_routes,
    insights_routes,
    documentation_routes,
    requirements_routes,
    orchestrator_routes,
)

load_dotenv(override=True)

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default_secret")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield


app = FastAPI(
    title="AI Multi-Agent System",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=ENCRYPTION_KEY,
    same_site="none",
    https_only=True,
)

app.add_middleware(UserTypeMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

Instrumentator(
    excluded_handlers=[
        "/metrics",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ],
).instrument(app).expose(app)

init_db(app)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(user_routes.router)
app.include_router(validation_routes.router)
app.include_router(requirements_routes.router)
app.include_router(code_routes.router)
app.include_router(unit_test_routes.router)
app.include_router(insights_routes.router)
app.include_router(documentation_routes.router)
app.include_router(orchestrator_routes.router)