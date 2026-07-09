from pydantic import BaseModel


class DepartmentRead(BaseModel):
    dept_id: int
    dept_name: str
