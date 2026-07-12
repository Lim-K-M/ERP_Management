from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.core.exceptions import LoginRequiredError
from app.db.metadata import metadata, reflect_metadata
from app.routers import api_departments, api_employees, api_employment_history, api_positions, pages


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await reflect_metadata()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(pages.router)
app.include_router(api_employees.router)
app.include_router(api_employment_history.router)
app.include_router(api_departments.router)
app.include_router(api_positions.router)


@app.exception_handler(LoginRequiredError)
async def login_required_handler(request: Request, exc: LoginRequiredError) -> RedirectResponse:
    return RedirectResponse(f"/login?next={request.url.path}", status_code=303)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "tables": ",".join(sorted(metadata.tables.keys()))}
