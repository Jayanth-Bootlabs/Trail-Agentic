import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from database.connection import init_db
from middleware.middleware import UserTypeMiddleware
from routes import users_route, validation_routes

load_dotenv(override=True)

SERVICE_NAME = "main_app"

app = FastAPI(title="AI Multi-Agent System")

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default_secret")

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

init_db(app)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(users_route.router)
app.include_router(validation_routes.router)