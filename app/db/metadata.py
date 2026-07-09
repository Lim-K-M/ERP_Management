from sqlalchemy import MetaData

from app.db.engine import engine

metadata = MetaData()

REFLECTED_TABLES = ("t_department", "t_position", "t_employee", "t_employment_history")


async def reflect_metadata() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata.reflect, only=REFLECTED_TABLES)
