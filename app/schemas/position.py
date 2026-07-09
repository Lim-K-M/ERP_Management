from pydantic import BaseModel


class PositionRead(BaseModel):
    position_id: int
    position_name: str
