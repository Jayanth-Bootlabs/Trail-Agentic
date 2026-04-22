from tortoise.contrib.fastapi import register_tortoise
from utils.logger import log_event
import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = "database_connection"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def init_db(app):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="init_db",
        message="Initializing database connection",
        metadata={"db_name": DB_NAME},
    )

    register_tortoise(
        app=app,
        db_url=DATABASE_URL,
        modules={"models": ["models.users_model", "models.prompt_validator_model", 
                            "models.requirements_gathering_model", "models.code_generator_model"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="init_db",
        message="Database initialized successfully",
    )