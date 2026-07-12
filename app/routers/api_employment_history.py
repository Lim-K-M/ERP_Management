from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmployeeNotFoundError
from app.db.session import get_session
from app.schemas.employment_history import EmploymentHistoryRead
from app.services import employee_service, employment_history_service

router = APIRouter(prefix="/api/employees", tags=["employment-history"])


@router.get("/{emp_id}/history", response_model=list[EmploymentHistoryRead])
async def get_employment_history(emp_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await employee_service.get_employee(session, emp_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.") from e
    return await employment_history_service.list_history(session, emp_id)
