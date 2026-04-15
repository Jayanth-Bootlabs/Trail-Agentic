from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from models.users import Users
from utils.logger import log_event

SERVICE_NAME = "user_middleware"


class UserTypeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            user_email = request.headers.get("Authorization")

            if not user_email:
                return JSONResponse(
                    status_code=401,
                    content={"message": "Authorization header missing"},
                )

            user = await Users.filter(email=user_email, is_active=True).first()

            if not user:
                return JSONResponse(
                    status_code=401,
                    content={"message": "Invalid user"},
                )

            request.state.user = user
            request.state.user_id = user.id
            request.state.email = user.email

            log_event(
                level="INFO",
                service=SERVICE_NAME,
                function="dispatch",
                message="User validated successfully",
                metadata={"email": user.email},
            )

            response = await call_next(request)
            return response

        except Exception as e:
            log_event(
                level="ERROR",
                service=SERVICE_NAME,
                function="dispatch",
                message="Middleware error",
                metadata={"error": str(e)},
            )

            return JSONResponse(
                status_code=500,
                content={"message": "Internal Server Error"},
            )