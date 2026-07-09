from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.services import employee_service
from app.services.employee_service import EmployeeValidationError

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeRead])
async def list_employees(session: AsyncSession = Depends(get_session)):
    return await employee_service.list_employees(session)


@router.post("", response_model=EmployeeRead, status_code=201)
async def create_employee(payload: EmployeeCreate, session: AsyncSession = Depends(get_session)):
    try:
        emp_id = await employee_service.create_employee(session, payload)
    except EmployeeValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors) from e
    return await employee_service.get_employee(session, emp_id)
