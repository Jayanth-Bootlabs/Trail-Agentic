#Run these 2 commands in your vscode terminal

#brew install redis
#brew services start redis

#To verify whether redis is installed or not,run 
# redis-cli ping  
# You will see PONG

from redis import asyncio as aioredis
from utils.logger import log_event

SERVICE_NAME = "cache"

redis = None


async def init_redis():
    global redis
    try:
        redis = await aioredis.from_url(
            "redis://localhost:6379",
            encoding="utf8",
            decode_responses=True
        )
        
        await redis.ping()
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="init_redis",
            message="Redis connection initialized successfully",
        )
    except Exception:
        log_event(
            level="WARNING",
            service=SERVICE_NAME,
            function="init_redis",
            message="Redis connection failed — caching disabled",
        )
        redis = None

    return redis


async def get_redis():
    return redis