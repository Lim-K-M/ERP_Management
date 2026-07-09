from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.employee import EmployeeCreate
from app.services import department_service, employee_service, position_service
from app.services.employee_service import EmployeeValidationError
from app.templating import templates

router = APIRouter()


def _optional_int(value: str | None) -> int | None:
    return int(value) if value else None


@router.get("/employees")
async def employee_list_page(request: Request, session: AsyncSession = Depends(get_session)):
    employees = await employee_service.list_employees(session)
    return templates.TemplateResponse("employees/list.html", {"request": request, "employees": employees})


@router.get("/employees/new")
async def employee_register_page(request: Request, session: AsyncSession = Depends(get_session)):
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)
    return templates.TemplateResponse(
        "employees/register.html",
        {"request": request, "departments": departments, "positions": positions, "errors": {}, "form": {}},
    )


@router.post("/employees/new")
async def employee_register_submit(request: Request, session: AsyncSession = Depends(get_session)):
    form = await request.form()
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)

    try:
        payload = EmployeeCreate(
            emp_no=form.get("emp_no", ""),
            emp_name=form.get("emp_name", ""),
            email=form.get("email") or None,
            phone=form.get("phone") or None,
            hire_date=form.get("hire_date"),
            dept_id=_optional_int(form.get("dept_id")),
            position_id=_optional_int(form.get("position_id")),
            manager_id=_optional_int(form.get("manager_id")),
        )
    except ValidationError as e:
        errors = {str(err["loc"][0]): err["msg"] for err in e.errors()}
        return templates.TemplateResponse(
            "employees/register.html",
            {"request": request, "departments": departments, "positions": positions, "errors": errors, "form": form},
            status_code=422,
        )

    try:
        await employee_service.create_employee(session, payload)
    except EmployeeValidationError as e:
        return templates.TemplateResponse(
            "employees/register.html",
            {"request": request, "departments": departments, "positions": positions, "errors": e.errors, "form": form},
            status_code=422,
        )

    return RedirectResponse("/employees", status_code=303)
