from typing import Any
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

def format_response(
    data: Any | None = None,
    message: str = "Success",
    status_code: int = 200,
    status: bool | None = None,
    meta: dict | None = None,
) -> JSONResponse:
    if status is None:
        status = 200 <= status_code < 300

    response_content = {
        "status": status,
        "message": message,
        "data": data,
    }

    if meta is not None:
        response_content["meta"] = meta

    encoded_content = jsonable_encoder(response_content)

    return JSONResponse(content=encoded_content, status_code=status_code)
