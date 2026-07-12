from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.metadata import metadata, reflect_metadata
from app.routers import api_departments, api_employees, api_employment_history, api_positions, pages


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await reflect_metadata()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(pages.router)
app.include_router(api_employees.router)
app.include_router(api_employment_history.router)
app.include_router(api_departments.router)
app.include_router(api_positions.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "tables": ",".join(sorted(metadata.tables.keys()))}
