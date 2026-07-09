from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.metadata import metadata
from app.schemas.employee import EmployeeCreate


class EmployeeValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(str(errors))


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
            employee.c.emp_status,
        )
        .select_from(employee)
        .outerjoin(department, employee.c.dept_id == department.c.dept_id)
        .outerjoin(position, employee.c.position_id == position.c.position_id)
    )


async def list_employees(session: AsyncSession):
    employee = metadata.tables["t_employee"]
    stmt = _employee_select().order_by(employee.c.emp_no)
    result = await session.execute(stmt)
    return result.mappings().all()


async def get_employee(session: AsyncSession, emp_id: int):
    employee = metadata.tables["t_employee"]
    stmt = _employee_select().where(employee.c.emp_id == emp_id)
    result = await session.execute(stmt)
    return result.mappings().one()


async def create_employee(session: AsyncSession, payload: EmployeeCreate) -> int:
    employee = metadata.tables["t_employee"]
    department = metadata.tables["t_department"]
    position = metadata.tables["t_position"]

    errors: dict[str, str] = {}

    if payload.dept_id is not None:
        exists = await session.scalar(select(department.c.dept_id).where(department.c.dept_id == payload.dept_id))
        if exists is None:
            errors["dept_id"] = "존재하지 않는 부서입니다."

    if payload.position_id is not None:
        exists = await session.scalar(select(position.c.position_id).where(position.c.position_id == payload.position_id))
        if exists is None:
            errors["position_id"] = "존재하지 않는 직급입니다."

    if payload.manager_id is not None:
        exists = await session.scalar(select(employee.c.emp_id).where(employee.c.emp_id == payload.manager_id))
        if exists is None:
            errors["manager_id"] = "존재하지 않는 관리자입니다."

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
