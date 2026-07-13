from datetime import date

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.metadata import metadata


def _history_select():
    history = metadata.tables["t_employment_history"]
    department = metadata.tables["t_department"]
    position = metadata.tables["t_position"]
    return (
        select(
            history.c.history_id,
            history.c.emp_id,
            history.c.change_type,
            history.c.dept_id,
            department.c.dept_name,
            history.c.position_id,
            position.c.position_name,
            history.c.effective_date,
            history.c.remark,
        )
        .select_from(history)
        .outerjoin(department, history.c.dept_id == department.c.dept_id)
        .outerjoin(position, history.c.position_id == position.c.position_id)
    )


async def record_history(
    session: AsyncSession,
    *,
    emp_id: int,
    change_type: str,
    dept_id: int | None = None,
    position_id: int | None = None,
    effective_date: date | None = None,
    remark: str | None = None,
) -> None:
    history = metadata.tables["t_employment_history"]
    stmt = insert(history).values(
        emp_id=emp_id,
        change_type=change_type,
        dept_id=dept_id,
        position_id=position_id,
        effective_date=effective_date or date.today(),
        remark=remark,
    )
    await session.execute(stmt)


async def list_history(
    session: AsyncSession,
    emp_id: int,
    page: int | None = None,
    page_size: int | None = None,
):
    """emp_id의 이력을 발령일 오름차순(입사가 맨 위)으로 반환한다. page/page_size를 둘 다 주면 그 구간만 잘라 반환한다."""
    history = metadata.tables["t_employment_history"]
    stmt = (
        _history_select()
        .where(history.c.emp_id == emp_id)
        .order_by(history.c.effective_date.asc(), history.c.history_id.asc())
    )
    if page is not None and page_size is not None:
        stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    result = await session.execute(stmt)
    return result.mappings().all()


async def count_history(session: AsyncSession, emp_id: int) -> int:
    history = metadata.tables["t_employment_history"]
    stmt = select(func.count()).select_from(history).where(history.c.emp_id == emp_id)
    return await session.scalar(stmt)
