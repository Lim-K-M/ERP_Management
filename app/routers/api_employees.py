from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_login_api
from app.core.exceptions import EmployeeNotFoundError, EmployeeValidationError, InvalidTransitionError
from app.db.session import get_session
from app.schemas.employee import EmployeeCreate, EmployeeFilter, EmployeeRead, EmployeeStatusUpdate, EmployeeUpdate
from app.services import employee_service
from app.services.employee_service import DEFAULT_SORT, SORT_COLUMNS

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeRead])
async def list_employees(
    name: str | None = None,
    dept_id: str | None = None,
    position_id: str | None = None,
    status: str | None = None,
    hire_year: str | None = None,
    sort: str = DEFAULT_SORT,
    order: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    if sort not in SORT_COLUMNS:
        sort = DEFAULT_SORT
    if order not in ("asc", "desc"):
        order = "asc"
    try:
        filters = EmployeeFilter(
            name=name, dept_id=dept_id, position_id=position_id, status=status, hire_year=hire_year
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422, detail={str(err["loc"][0]): err["msg"] for err in e.errors()}
        ) from e
    return await employee_service.list_employees(session, filters, sort=sort, order=order, page=page, page_size=page_size)


@router.post("", response_model=EmployeeRead, status_code=201)
async def create_employee(
    payload: EmployeeCreate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(require_login_api),
):
    try:
        emp_id = await employee_service.create_employee(session, payload)
    except EmployeeValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors) from e
    return await employee_service.get_employee(session, emp_id)


@router.get("/{emp_id}", response_model=EmployeeRead)
async def get_employee(emp_id: int, session: AsyncSession = Depends(get_session)):
    try:
        return await employee_service.get_employee(session, emp_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.") from e


@router.patch("/{emp_id}", response_model=EmployeeRead)
async def update_employee(
    emp_id: int,
    payload: EmployeeUpdate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(require_login_api),
):
    try:
        await employee_service.update_employee(session, emp_id, payload)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.") from e
    except EmployeeValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors) from e
    return await employee_service.get_employee(session, emp_id)


@router.patch("/{emp_id}/status", response_model=EmployeeRead)
async def change_status(
    emp_id: int,
    payload: EmployeeStatusUpdate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(require_login_api),
):
    try:
        await employee_service.change_status(session, emp_id, payload.emp_status)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.") from e
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return await employee_service.get_employee(session, emp_id)
