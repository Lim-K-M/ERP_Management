from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_login, verify_credentials
from app.core.constants import next_allowed_statuses
from app.core.exceptions import EmployeeNotFoundError, EmployeeValidationError, InvalidTransitionError
from app.db.session import get_session
from app.schemas.employee import EmployeeCreate, EmployeeFilter, EmployeeUpdate
from app.services import department_service, employee_service, position_service
from app.services.employee_service import DEFAULT_SORT, SORT_COLUMNS
from app.templating import templates

router = APIRouter()


def _optional_int(value: str | None) -> int | None:
    return int(value) if value else None


def _employee_form_fields(form) -> dict:
    return {
        "emp_no": form.get("emp_no", ""),
        "emp_name": form.get("emp_name", ""),
        "email": form.get("email") or None,
        "phone": form.get("phone") or None,
        "hire_date": form.get("hire_date"),
        "dept_id": _optional_int(form.get("dept_id")),
        "position_id": _optional_int(form.get("position_id")),
        "manager_id": _optional_int(form.get("manager_id")),
    }


def _build_sort_links(request: Request, sort: str, order: str) -> tuple[dict[str, str], dict[str, str | None]]:
    base_query = {k: v for k, v in request.query_params.items() if k not in ("sort", "order")}
    links: dict[str, str] = {}
    states: dict[str, str | None] = {}
    for column in SORT_COLUMNS:
        next_order = "desc" if sort == column and order == "asc" else "asc"
        links[column] = "/employees?" + urlencode({**base_query, "sort": column, "order": next_order})
        states[column] = order if sort == column else None
    return links, states


@router.get("/login")
async def login_page(request: Request, next: str = "/employees"):
    return templates.TemplateResponse(request, "login.html", {"error": None, "next": next})


@router.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    next_url = form.get("next") or "/employees"

    if verify_credentials(username, password):
        request.session["user"] = username
        return RedirectResponse(next_url, status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "아이디 또는 비밀번호가 올바르지 않습니다.", "next": next_url},
        status_code=401,
    )


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/employees", status_code=303)


@router.get("/employees")
async def employee_list_page(
    request: Request,
    name: str | None = None,
    dept_id: str | None = None,
    position_id: str | None = None,
    status: str | None = None,
    hire_year: str | None = None,
    sort: str = DEFAULT_SORT,
    order: str = "asc",
    session: AsyncSession = Depends(get_session),
):
    if sort not in SORT_COLUMNS:
        sort = DEFAULT_SORT
    if order not in ("asc", "desc"):
        order = "asc"

    filters = EmployeeFilter(name=name, dept_id=dept_id, position_id=position_id, status=status, hire_year=hire_year)
    employees = await employee_service.list_employees(session, filters, sort=sort, order=order)
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)
    hire_years = await employee_service.list_hire_years(session)
    sort_links, sort_state = _build_sort_links(request, sort, order)

    return templates.TemplateResponse(
        request,
        "employees/list.html",
        {
            "employees": employees,
            "filters": filters,
            "departments": departments,
            "positions": positions,
            "hire_years": hire_years,
            "sort_links": sort_links,
            "sort_state": sort_state,
            "current_sort": sort,
            "current_order": order,
        },
    )


@router.get("/employees/new")
async def employee_register_page(
    request: Request, session: AsyncSession = Depends(get_session), user: str = Depends(require_login)
):
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)
    return templates.TemplateResponse(
        request,
        "employees/register.html",
        {"departments": departments, "positions": positions, "errors": {}, "form": {}},
    )


@router.post("/employees/new")
async def employee_register_submit(
    request: Request, session: AsyncSession = Depends(get_session), user: str = Depends(require_login)
):
    form = await request.form()
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)

    try:
        payload = EmployeeCreate(**_employee_form_fields(form))
    except ValidationError as e:
        errors = {str(err["loc"][0]): err["msg"] for err in e.errors()}
        return templates.TemplateResponse(
            request,
            "employees/register.html",
            {"departments": departments, "positions": positions, "errors": errors, "form": form},
            status_code=422,
        )

    try:
        await employee_service.create_employee(session, payload)
    except EmployeeValidationError as e:
        return templates.TemplateResponse(
            request,
            "employees/register.html",
            {"departments": departments, "positions": positions, "errors": e.errors, "form": form},
            status_code=422,
        )

    return RedirectResponse("/employees", status_code=303)


@router.get("/employees/{emp_id}")
async def employee_detail_page(emp_id: int, request: Request, session: AsyncSession = Depends(get_session)):
    try:
        employee = await employee_service.get_employee(session, emp_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.") from e
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)
    return templates.TemplateResponse(
        request,
        "employees/detail.html",
        {
            "employee": employee,
            "departments": departments,
            "positions": positions,
            "errors": {},
            "form": employee,
            "next_statuses": sorted(next_allowed_statuses(employee["emp_status"])),
        },
    )


@router.post("/employees/{emp_id}")
async def employee_update_submit(
    emp_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(require_login),
):
    try:
        employee = await employee_service.get_employee(session, emp_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.") from e

    form = await request.form()
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)

    def _render_error(errors: dict[str, str]):
        return templates.TemplateResponse(
            request,
            "employees/detail.html",
            {
                "employee": employee,
                "departments": departments,
                "positions": positions,
                "errors": errors,
                "form": form,
                "next_statuses": sorted(next_allowed_statuses(employee["emp_status"])),
            },
            status_code=422,
        )

    try:
        payload = EmployeeUpdate(**_employee_form_fields(form))
    except ValidationError as e:
        errors = {str(err["loc"][0]): err["msg"] for err in e.errors()}
        return _render_error(errors)

    try:
        await employee_service.update_employee(session, emp_id, payload)
    except EmployeeValidationError as e:
        return _render_error(e.errors)

    return RedirectResponse(f"/employees/{emp_id}", status_code=303)


@router.post("/employees/{emp_id}/status")
async def employee_status_submit(
    emp_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(require_login),
):
    form = await request.form()
    target_status = form.get("emp_status", "")

    try:
        await employee_service.change_status(session, emp_id, target_status)
    except (EmployeeNotFoundError, InvalidTransitionError):
        # 화면에는 허용된 다음 상태만 버튼으로 노출하므로, 여기 도달하면 위조된 요청이다.
        # 조용히 무시하지 않고 상세 페이지로 되돌려 현재 상태를 그대로 보여준다.
        pass

    return RedirectResponse(f"/employees/{emp_id}", status_code=303)
