import traceback
from fastapi import APIRouter, Request
from service.users_service import create_user_service, get_users_service, get_user_service, update_user_service, delete_user_service
from utils.logger import log_event
from utils.response import format_response
from schemas.user_schema import CreateUserRequest, UpdateUserRequest
from fastapi import HTTPException

router = APIRouter(tags=["Users"])

SERVICE_NAME = "user_routes"


@router.post("/create_users")
async def create_user(payload: CreateUserRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="create_user",
        message="Create user API called",
        metadata={"email": payload.email},
    )

    try:
        data = await create_user_service(payload)

        return format_response(
            data=data,
            message="User created successfully",
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="create_user",
            message="Failed to create user",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get_all_users")
async def get_users():
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="get_users",
        message="Get users API called",
    )

    try:
        data = await get_users_service()

        return format_response(
            data=data,
            message="Users fetched successfully",
            status_code=200,
        )

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_users",
            message="Failed to fetch users",
            stack_trace=traceback.format_exc(),
        )
        raise


@router.get("/get_single_user/{user_id}")
async def get_user(user_id: int):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="get_user",
        message="Get single user API called",
        metadata={"user_id": user_id},
    )

    try:
        data = await get_user_service(user_id)

        return format_response(
            data=data,
            message="User fetched successfully",
            status_code=200,
        )

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_user",
            message="Failed to fetch user",
            metadata={"user_id": user_id},
            stack_trace=traceback.format_exc(),
        )
        raise

@router.patch("/update_user/{user_id}")
async def update_user(user_id: int, payload: UpdateUserRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="update_user",
        message="Update user API called",
        metadata={"user_id": user_id},
    )

    try:
        data = await update_user_service(user_id, payload)

        return format_response(
            data=data,
            message="User updated successfully",
            status_code=200,
        )

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="update_user",
            message="Failed to update user",
            metadata={"user_id": user_id},
            stack_trace=traceback.format_exc(),
        )
        raise


@router.delete("/delete_single_user/{user_id}")
async def delete_user(user_id: int):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="delete_user",
        message="Delete user API called",
        metadata={"user_id": user_id},
    )

    try:
        data = await delete_user_service(user_id)

        return format_response(
            data=data,
            message="User deleted successfully",
            status_code=200,
        )

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="delete_user",
            message="Failed to delete user",
            metadata={"user_id": user_id},
            stack_trace=traceback.format_exc(),
        )
        raise