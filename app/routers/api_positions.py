from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.position import PositionRead
from app.services import position_service

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("", response_model=list[PositionRead])
async def list_positions(session: AsyncSession = Depends(get_session)):
    return await position_service.list_positions(session)
