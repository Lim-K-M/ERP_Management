from datetime import date

from pydantic import BaseModel


class EmploymentHistoryRead(BaseModel):
    history_id: int
    emp_id: int
    change_type: str
    dept_id: int | None
    dept_name: str | None
    position_id: int | None
    position_name: str | None
    effective_date: date
    remark: str | None
