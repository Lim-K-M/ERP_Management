from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.metadata import metadata


async def list_departments(session: AsyncSession):
    department = metadata.tables["t_department"]
    stmt = (
        select(department.c.dept_id, department.c.dept_name)
        .where(department.c.use_yn == "Y")
        .order_by(department.c.dept_name)
    )
    result = await session.execute(stmt)
    return result.mappings().all()
