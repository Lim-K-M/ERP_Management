from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.department import DepartmentRead
from app.services import department_service

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentRead])
async def list_departments(session: AsyncSession = Depends(get_session)):
    return await department_service.list_departments(session)
