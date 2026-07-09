from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.metadata import metadata


async def list_positions(session: AsyncSession):
    position = metadata.tables["t_position"]
    stmt = (
        select(position.c.position_id, position.c.position_name)
        .where(position.c.use_yn == "Y")
        .order_by(position.c.position_level)
    )
    result = await session.execute(stmt)
    return result.mappings().all()
