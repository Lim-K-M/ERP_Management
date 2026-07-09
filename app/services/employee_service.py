from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ALLOWED_TRANSITIONS
from app.core.exceptions import EmployeeNotFoundError, EmployeeValidationError, InvalidTransitionError
from app.db.metadata import metadata
from app.schemas.employee import EmployeeCreate, EmployeeFilter, EmployeeUpdate


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


async def list_employees(session: AsyncSession, filters: EmployeeFilter | None = None):
    employee = metadata.tables["t_employee"]
    stmt = _employee_select()

    if filters is not None:
        if filters.name:
            stmt = stmt.where(employee.c.emp_name.ilike(f"%{filters.name}%"))
        if filters.dept_id is not None:
            stmt = stmt.where(employee.c.dept_id == filters.dept_id)
        if filters.status:
            stmt = stmt.where(employee.c.emp_status == filters.status)

    stmt = stmt.order_by(employee.c.emp_no)
    result = await session.execute(stmt)
    return result.mappings().all()


async def get_employee(session: AsyncSession, emp_id: int):
    employee = metadata.tables["t_employee"]
    stmt = _employee_select().where(employee.c.emp_id == emp_id)
    result = await session.execute(stmt)
    try:
        return result.mappings().one()
    except NoResultFound as e:
        raise EmployeeNotFoundError(emp_id) from e


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
            exists = await session.scalar(select(employee.c.emp_id).where(employee.c.emp_id == manager_id))
            if exists is None:
                errors["manager_id"] = "존재하지 않는 관리자입니다."

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

    await session.commit()
    return result.scalar_one()


async def update_employee(session: AsyncSession, emp_id: int, payload: EmployeeUpdate) -> None:
    employee = metadata.tables["t_employee"]

    await get_employee(session, emp_id)  # 404 if not found

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

    await session.commit()


async def change_status(session: AsyncSession, emp_id: int, target_status: str) -> None:
    employee = metadata.tables["t_employee"]

    current = await get_employee(session, emp_id)
    current_status = current["emp_status"]

    if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise InvalidTransitionError(current_status, target_status)

    stmt = update(employee).where(employee.c.emp_id == emp_id).values(emp_status=target_status)
    await session.execute(stmt)
    await session.commit()
