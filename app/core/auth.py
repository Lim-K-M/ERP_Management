from fastapi import HTTPException, Request

from app.config import settings
from app.core.exceptions import LoginRequiredError


def verify_credentials(username: str, password: str) -> bool:
    return username == settings.admin_username and password == settings.admin_password


def current_user(request: Request) -> str | None:
    return request.session.get("user")


def require_login(request: Request) -> str:
    user = current_user(request)
    if user is None:
        raise LoginRequiredError()
    return user


def require_login_api(request: Request) -> str:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return user
