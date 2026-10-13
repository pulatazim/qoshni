"""Barcha xatolar bitta ko'rinishda qaytadi: `{"error": {"code": ..., "message": ...}}`.

Kod barqaror va dastur uchun, message esa odam o'qiydigan matn (o'zbekcha).
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Kodlar ro'yxati: frontend shu so'zlarga qarab harakat qiladi.
AUTH_INVALID = "auth_invalid"
AUTH_BANNED = "auth_banned"
NOT_FOUND = "not_found"
FORBIDDEN = "forbidden"
VALIDATION_ERROR = "validation_error"
INTERNAL_ERROR = "internal_error"

# FastAPI sxema xatolari uchun status (starlette konstantalariga bog'lanmaymiz).
UNPROCESSABLE = 422

# Sxema xatosi statusi — sonni belgilab olamiz, kutubxona konstantasi nomini almashtirdi.
HTTP_UNPROCESSABLE = 422


class ApiError(Exception):
    """Kutilgan xato: HTTP status + barqaror kod + foydalanuvchi tilida matn."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.code, exc.message, exc.status_code)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {
            status.HTTP_401_UNAUTHORIZED: AUTH_INVALID,
            status.HTTP_403_FORBIDDEN: FORBIDDEN,
            status.HTTP_404_NOT_FOUND: NOT_FOUND,
        }.get(exc.status_code, INTERNAL_ERROR)
        message = exc.detail if isinstance(exc.detail, str) else "Xato yuz berdi"
        return error_response(code, message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(part) for part in first.get("loc", ())[1:]) or "so'rov"
        return error_response(
            VALIDATION_ERROR,
            f"{field} maydonida xato: {first.get('msg', 'qiymati yaramas')}",
            HTTP_UNPROCESSABLE,
        )
