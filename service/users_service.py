import traceback
from models.users import Users
from utils.logger import log_event
from fastapi import HTTPException
from schemas.user_schema import CreateUserRequest, UpdateUserRequest

SERVICE_NAME = "user_service"

async def create_user_service(payload: CreateUserRequest):
    try:
        if not payload.email.endswith("@bootlabstech.com"):
            raise HTTPException(
                status_code=400,
                detail="Only @bootlabstech.com emails are allowed",
            )

        existing_user = (
            await Users.filter(email=payload.email)
            .first()
        )

        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        user = await Users.create(
            email=payload.email,
            name=payload.name,
        )

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="create_user_service",
            message="Error creating user",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_users_service():
    try:
        users = await Users.all()

        data = [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
            }
            for u in users
        ]

        return {
            "total": len(data),
            "data": data
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_users_service",
            message="Error fetching users",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_user_service(user_id: int):
    try:
        user = await Users.filter(id=user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_user_service",
            message="Error fetching user",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")

async def update_user_service(user_id: int, payload: UpdateUserRequest):
    try:
        user = await Users.filter(id=user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if payload.name:
            user.name = payload.name

        await user.save()

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="update_user_service",
            message="Error updating user",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")

async def delete_user_service(user_id: int):
    try:
        user = await Users.filter(id=user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await user.delete()

        return {"deleted": True}

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="delete_user_service",
            message="Error deleting user",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")