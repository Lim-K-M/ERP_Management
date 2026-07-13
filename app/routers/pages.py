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
from app.services import department_service, employee_service, employment_history_service, position_service
from app.services.employee_service import DEFAULT_SORT, SORT_COLUMNS
from app.templating import templates

router = APIRouter()

PAGE_SIZE = 20
HISTORY_PAGE_SIZE = 5


def _validation_errors(exc: ValidationError) -> dict[str, str]:
    return {str(err["loc"][0]): err["msg"].removeprefix("Value error, ") for err in exc.errors()}


def _optional_int(value: str | None) -> int | None:
    return int(value) if value else None


def _employee_form_fields(form) -> dict:
    fields = {
        "emp_no": form.get("emp_no", ""),
        "emp_name": form.get("emp_name", ""),
        "email": form.get("email") or None,
        "phone": form.get("phone") or None,
        "hire_date": form.get("hire_date"),
    }
    errors: dict[str, str] = {}
    for key in ("dept_id", "position_id", "manager_id"):
        try:
            fields[key] = _optional_int(form.get(key))
        except ValueError:
            errors[key] = "숫자만 입력해주세요."
    if errors:
        raise EmployeeValidationError(errors)
    return fields


def _query_page(request: Request) -> int:
    try:
        return max(1, int(request.query_params.get("page", 1)))
    except ValueError:
        return 1


def _safe_next_url(value: str | None) -> str:
    """오픈 리다이렉트 방지: 이 앱 안의 상대 경로만 허용한다."""
    if value and value.startswith("/") and not value.startswith("//") and not value.startswith("/\\"):
        return value
    return "/employees"


def _build_sort_links(request: Request, sort: str, order: str) -> tuple[dict[str, str], dict[str, str | None]]:
    base_query = {k: v for k, v in request.query_params.items() if k not in ("sort", "order", "page")}
    links: dict[str, str] = {}
    states: dict[str, str | None] = {}
    for column in SORT_COLUMNS:
        next_order = "desc" if sort == column and order == "asc" else "asc"
        links[column] = "/employees?" + urlencode({**base_query, "sort": column, "order": next_order})
        states[column] = order if sort == column else None
    return links, states


def _build_page_link(request: Request, target_page: int) -> str:
    base_query = {k: v for k, v in request.query_params.items() if k != "page"}
    return "/employees?" + urlencode({**base_query, "page": target_page})


def _page_numbers(current: int, total: int, window: int = 2) -> list[int | None]:
    """현재 페이지 주변 + 처음/끝 페이지 번호 목록. 건너뛴 구간은 None(생략 표시)."""
    if total <= 1:
        return [1]
    keep = {1, total, current}
    keep.update(p for p in range(current - window, current + window + 1) if 1 <= p <= total)
    numbers: list[int | None] = []
    prev: int | None = None
    for p in sorted(keep):
        if prev is not None and p - prev > 1:
            numbers.append(None)
        numbers.append(p)
        prev = p
    return numbers


async def _history_pagination(session: AsyncSession, emp_id: int, page: int) -> dict:
    total_count = await employment_history_service.count_history(session, emp_id)
    total_pages = max(1, -(-total_count // HISTORY_PAGE_SIZE))
    page = max(1, min(page, total_pages))
    history = await employment_history_service.list_history(
        session, emp_id, page=page, page_size=HISTORY_PAGE_SIZE
    )
    return {
        "history": history,
        "history_current_page": page,
        "history_total_pages": total_pages,
        "history_total_count": total_count,
        "history_page_numbers": _page_numbers(page, total_pages),
        "history_page_link": lambda p: f"/employees/{emp_id}?page={p}",
    }


@router.get("/login")
async def login_page(request: Request, next: str = "/employees"):
    return templates.TemplateResponse(request, "login.html", {"error": None, "next": _safe_next_url(next)})


@router.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    next_url = _safe_next_url(form.get("next"))

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
    page: int = 1,
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
        raise HTTPException(status_code=422, detail=_validation_errors(e)) from e

    total_count = await employee_service.count_employees(session, filters)
    total_pages = max(1, -(-total_count // PAGE_SIZE))
    page = max(1, min(page, total_pages))
    employees = await employee_service.list_employees(
        session, filters, sort=sort, order=order, page=page, page_size=PAGE_SIZE
    )
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)
    hire_years = await employee_service.list_hire_years(session)
    status_counts = await employee_service.count_by_status(session)
    dept_counts = await employee_service.count_by_department(session)
    position_counts = await employee_service.count_by_position(session)
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
            "status_counts": status_counts,
            "dept_counts": dept_counts,
            "position_counts": position_counts,
            "sort_links": sort_links,
            "sort_state": sort_state,
            "current_sort": sort,
            "current_order": order,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "prev_page_link": _build_page_link(request, page - 1) if page > 1 else None,
            "next_page_link": _build_page_link(request, page + 1) if page < total_pages else None,
            "page_numbers": _page_numbers(page, total_pages),
            "page_number_link": lambda p: _build_page_link(request, p),
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
    except EmployeeValidationError as e:
        return templates.TemplateResponse(
            request,
            "employees/register.html",
            {"departments": departments, "positions": positions, "errors": e.errors, "form": form},
            status_code=422,
        )
    except ValidationError as e:
        errors = _validation_errors(e)
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
async def employee_detail_page(
    emp_id: int, request: Request, page: int = 1, session: AsyncSession = Depends(get_session)
):
    try:
        employee = await employee_service.get_employee(session, emp_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.") from e
    departments = await department_service.list_departments(session)
    positions = await position_service.list_positions(session)
    history_ctx = await _history_pagination(session, emp_id, page)
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
            **history_ctx,
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

    async def _render_error(errors: dict[str, str]):
        # 실패했을 때만 이력을 조회한다 - 성공(리다이렉트) 경로에서는 불필요한 쿼리를 피한다.
        history_ctx = await _history_pagination(session, emp_id, _query_page(request))
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
                **history_ctx,
            },
            status_code=422,
        )

    try:
        payload = EmployeeUpdate(**_employee_form_fields(form))
    except EmployeeValidationError as e:
        return await _render_error(e.errors)
    except ValidationError as e:
        errors = _validation_errors(e)
        return await _render_error(errors)

    try:
        await employee_service.update_employee(session, emp_id, payload)
    except EmployeeValidationError as e:
        return await _render_error(e.errors)

    return RedirectResponse(f"/employees/{emp_id}?saved=1", status_code=303)


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
