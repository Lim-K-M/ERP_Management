from sqlalchemy import extract, insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ALLOWED_TRANSITIONS
from app.core.exceptions import EmployeeNotFoundError, EmployeeValidationError, InvalidTransitionError
from app.db.metadata import metadata
from app.schemas.employee import EmployeeCreate, EmployeeFilter, EmployeeUpdate
from app.services import employment_history_service

STATUS_TO_CHANGE_TYPE = {"LEAVE": "LEAVE", "ACTIVE": "RETURN", "RESIGNED": "RESIGN"}

SORT_COLUMNS = ("emp_no", "emp_name", "dept_name", "position_name", "emp_status")
DEFAULT_SORT = "emp_no"


def _employee_select():
    employee = metadata.tables["t_employee"]
    department = metadata.tables["t_department"]
    position = metadata.tables["t_position"]
    return (
        select(
            employee.c.emp_id,
            employee.c.emp_no,
            employee.c.emp_name,
            employee.c.email,
            employee.c.phone,
            employee.c.hire_date,
            employee.c.dept_id,
            department.c.dept_name,
            employee.c.position_id,
            position.c.position_name,
            employee.c.manager_id,
            employee.c.emp_status,
        )
        .select_from(employee)
        .outerjoin(department, employee.c.dept_id == department.c.dept_id)
        .outerjoin(position, employee.c.position_id == position.c.position_id)
    )


async def list_employees(
    session: AsyncSession,
    filters: EmployeeFilter | None = None,
    sort: str = DEFAULT_SORT,
    order: str = "asc",
):
    employee = metadata.tables["t_employee"]
    department = metadata.tables["t_department"]
    position = metadata.tables["t_position"]
    stmt = _employee_select()

    if filters is not None:
        if filters.name:
            stmt = stmt.where(employee.c.emp_name.ilike(f"%{filters.name}%"))
        if filters.dept_id is not None:
            stmt = stmt.where(employee.c.dept_id == filters.dept_id)
        if filters.position_id is not None:
            stmt = stmt.where(employee.c.position_id == filters.position_id)
        if filters.status:
            stmt = stmt.where(employee.c.emp_status == filters.status)
        if filters.hire_year is not None:
            stmt = stmt.where(extract("year", employee.c.hire_date) == filters.hire_year)

    sort_columns = {
        "emp_no": employee.c.emp_no,
        "emp_name": employee.c.emp_name,
        "dept_name": department.c.dept_name,
        "position_name": position.c.position_level,  # 이름 가나다순이 아니라 직급 서열 기준
        "emp_status": employee.c.emp_status,
    }
    column = sort_columns.get(sort, employee.c.emp_no)
    stmt = stmt.order_by(column.desc() if order == "desc" else column.asc())

    result = await session.execute(stmt)
    return result.mappings().all()


async def list_hire_years(session: AsyncSession) -> list[int]:
    employee = metadata.tables["t_employee"]
    year_col = extract("year", employee.c.hire_date)
    stmt = select(year_col.label("year")).distinct().order_by(year_col.desc())
    result = await session.execute(stmt)
    return [int(row.year) for row in result]


async def get_employee(session: AsyncSession, emp_id: int):
    employee = metadata.tables["t_employee"]
    stmt = _employee_select().where(employee.c.emp_id == emp_id)
    result = await session.execute(stmt)
    try:
        return result.mappings().one()
    except NoResultFound as e:
        raise EmployeeNotFoundError(emp_id) from e


async def _would_create_manager_cycle(session: AsyncSession, emp_id: int, manager_id: int) -> bool:
    """manager_id를 emp_id의 매니저로 지정했을 때 순환 참조가 생기는지 확인한다.

    manager_id부터 매니저 체인을 따라 올라가다 emp_id를 다시 만나면 순환이다.
    """
    employee = metadata.tables["t_employee"]
    current: int | None = manager_id
    visited: set[int] = set()
    while current is not None:
        if current == emp_id:
            return True
        if current in visited:
            break  # 기존에 이미 형성된 별개의 순환 - 무한루프 방지용
        visited.add(current)
        current = await session.scalar(select(employee.c.manager_id).where(employee.c.emp_id == current))
    return False


async def _validate_references(
    session: AsyncSession,
    *,
    dept_id: int | None,
    position_id: int | None,
    manager_id: int | None,
    emp_id: int | None = None,
) -> dict[str, str]:
    employee = metadata.tables["t_employee"]
    department = metadata.tables["t_department"]
    position = metadata.tables["t_position"]

    errors: dict[str, str] = {}

    if dept_id is not None:
        exists = await session.scalar(select(department.c.dept_id).where(department.c.dept_id == dept_id))
        if exists is None:
            errors["dept_id"] = "존재하지 않는 부서입니다."

    if position_id is not None:
        exists = await session.scalar(select(position.c.position_id).where(position.c.position_id == position_id))
        if exists is None:
            errors["position_id"] = "존재하지 않는 직급입니다."

    if manager_id is not None:
        if emp_id is not None and manager_id == emp_id:
            errors["manager_id"] = "자기 자신을 관리자로 지정할 수 없습니다."
        else:
            manager_status = await session.scalar(
                select(employee.c.emp_status).where(employee.c.emp_id == manager_id)
            )
            if manager_status is None:
                errors["manager_id"] = "존재하지 않는 관리자입니다."
            elif manager_status == "RESIGNED":
                errors["manager_id"] = "퇴직한 직원은 관리자로 지정할 수 없습니다."
            elif emp_id is not None and await _would_create_manager_cycle(session, emp_id, manager_id):
                errors["manager_id"] = "관리자 지정이 순환 참조를 만듭니다."

    return errors


async def create_employee(session: AsyncSession, payload: EmployeeCreate) -> int:
    employee = metadata.tables["t_employee"]

    errors = await _validate_references(
        session, dept_id=payload.dept_id, position_id=payload.position_id, manager_id=payload.manager_id
    )
    if errors:
        raise EmployeeValidationError(errors)

    stmt = (
        insert(employee)
        .values(
            emp_no=payload.emp_no,
            emp_name=payload.emp_name,
            email=payload.email,
            phone=payload.phone,
            hire_date=payload.hire_date,
            dept_id=payload.dept_id,
            position_id=payload.position_id,
            manager_id=payload.manager_id,
            emp_status="ACTIVE",
        )
        .returning(employee.c.emp_id)
    )
    try:
        result = await session.execute(stmt)
    except IntegrityError as e:
        await session.rollback()
        raise EmployeeValidationError({"emp_no": "이미 사용 중인 사번입니다."}) from e

    emp_id = result.scalar_one()
    await employment_history_service.record_history(
        session,
        emp_id=emp_id,
        change_type="HIRE",
        dept_id=payload.dept_id,
        position_id=payload.position_id,
        effective_date=payload.hire_date,
    )
    await session.commit()
    return emp_id


async def update_employee(session: AsyncSession, emp_id: int, payload: EmployeeUpdate) -> None:
    employee = metadata.tables["t_employee"]

    before = await get_employee(session, emp_id)  # 404 if not found

    values = payload.model_dump(exclude_unset=True)
    if not values:
        return

    errors = await _validate_references(
        session,
        dept_id=values.get("dept_id"),
        position_id=values.get("position_id"),
        manager_id=values.get("manager_id"),
        emp_id=emp_id,
    )
    if errors:
        raise EmployeeValidationError(errors)

    stmt = update(employee).where(employee.c.emp_id == emp_id).values(**values)
    try:
        await session.execute(stmt)
    except IntegrityError as e:
        await session.rollback()
        raise EmployeeValidationError({"emp_no": "이미 사용 중인 사번입니다."}) from e

    new_dept_id = values.get("dept_id", before["dept_id"])
    new_position_id = values.get("position_id", before["position_id"])

    if "dept_id" in values and values["dept_id"] != before["dept_id"]:
        await employment_history_service.record_history(
            session, emp_id=emp_id, change_type="TRANSFER", dept_id=new_dept_id, position_id=new_position_id
        )
    if "position_id" in values and values["position_id"] != before["position_id"]:
        await employment_history_service.record_history(
            session, emp_id=emp_id, change_type="PROMOTION", dept_id=new_dept_id, position_id=new_position_id
        )

    await session.commit()


async def change_status(session: AsyncSession, emp_id: int, target_status: str) -> None:
    employee = metadata.tables["t_employee"]

    current = await get_employee(session, emp_id)
    current_status = current["emp_status"]

    if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise InvalidTransitionError(current_status, target_status)

    # 현재 상태를 조건으로 거는 조건부 UPDATE — SELECT와 UPDATE 사이에 다른 요청이
    # 먼저 상태를 바꿔버리는 레이스 컨디션에서 조용히 덮어쓰지 않고 실패시킨다.
    stmt = (
        update(employee)
        .where(employee.c.emp_id == emp_id, employee.c.emp_status == current_status)
        .values(emp_status=target_status)
    )
    result = await session.execute(stmt)
    if result.rowcount == 0:
        await session.rollback()
        raise InvalidTransitionError(current_status, target_status)

    await employment_history_service.record_history(
        session,
        emp_id=emp_id,
        change_type=STATUS_TO_CHANGE_TYPE[target_status],
        dept_id=current["dept_id"],
        position_id=current["position_id"],
    )
    await session.commit()
