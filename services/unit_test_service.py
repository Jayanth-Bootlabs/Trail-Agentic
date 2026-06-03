import traceback
import json
from fastapi import HTTPException
from builder.unit_test_builder import build_unit_test_graph
from schemas.unit_test_schema import UnitTestRequest
from models.code_model import GeneratedCode
from models.unit_tests_model import UnitTests
from utils.logger import log_event
from utils.cache import get_redis


SERVICE_NAME = "unit_test_service"


async def generate_unit_tests_service(payload: UnitTestRequest):
    try:
        code_id = payload.code_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_unit_tests_service",
            message="Starting unit test generation",
            metadata={
                "code_id": code_id
            },
        )

        existing_unit_test = await UnitTests.get_or_none(
            code_id=code_id,
            is_completed=True
        )

        if existing_unit_test:
            raise HTTPException(
                status_code=409,
                detail="Unit tests already generated for this code id"
            )

        code_record = await GeneratedCode.get_or_none(
            id=code_id,
            is_completed=True
        )

        if not code_record:
            raise HTTPException(
                status_code=404,
                detail="Generated code not found or code generation is not completed yet"
            )

        graph = build_unit_test_graph()

        config = {
            "configurable": {
                "thread_id": f"code-{code_id}"
            }
        }

        result = await graph.ainvoke(
            {
                "code": code_record.code_json,
                "retry_count": 0
            },
            config=config
        )

        ai = result.get("unit_tests", {})

        test_obj = await UnitTests.create(
            code=code_record,
            test_code=ai.get("test_code", ""),
            test_summary=ai.get("test_summary", ""),
            frameworks_used=ai.get("frameworks_used", []),
            is_completed=(result.get("status") == "valid"),
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_unit_tests_service",
            message="Unit test record created",
            metadata={
                "unit_test_id": test_obj.id,
                "code_id": test_obj.code_id,
                "status": result.get("status")
            },
        )

        return {
            "unit_test_id": test_obj.id,
            "code_id": test_obj.code_id,
            "test_code": ai.get("test_code", ""),
            "test_summary": ai.get("test_summary", ""),
            "frameworks_used": ai.get("frameworks_used", []),
            "status": result.get("status"),
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_unit_tests_service",
            message="Unit test generation crashed",
            metadata={
                "code_id": payload.code_id if payload else None
            },
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
    
async def get_unit_tests_service(unit_test_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_unit_tests_service",
            message="Fetching unit tests",
            metadata={"unit_test_id": unit_test_id},
        )

        # check cache first
        redis = await get_redis()

        if redis:
            cache_key = f"unit_test:{unit_test_id}"
            cached = await redis.get(cache_key)


        cache_key = f"unit_tests:{unit_test_id}"
        cached = await redis.get(cache_key)

        if cached:
            log_event(
                level="INFO",
                service=SERVICE_NAME,
                function="get_unit_tests_service",
                message="Cache hit",
                metadata={"unit_test_id": unit_test_id},
            )
            return json.loads(cached)

        # cache miss — fetch from DB
        test_record = await UnitTests.get_or_none(id=unit_test_id)

        if not test_record:
            raise HTTPException(status_code=404, detail="Unit tests not found")

        result = {
            "unit_test_id": test_record.id,
            "code_id": test_record.code_id,
            "test_code": test_record.test_code or "",
            "test_summary": test_record.test_summary or "",
            "frameworks_used": test_record.frameworks_used or [],
            "created_at": str(test_record.created_at) if test_record.created_at else None,
        }

        # store in cache for 1 hour
        await redis.set(cache_key, json.dumps(result), ex=3600)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_unit_tests_service",
            message="Cache miss — stored in cache",
            metadata={"unit_test_id": unit_test_id},
        )

        return result

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_unit_tests_service",
            message="Fetching unit tests failed",
            metadata={"trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail="Internal server error")