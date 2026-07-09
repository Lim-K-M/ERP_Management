from datetime import date

from pydantic import BaseModel, EmailStr, Field


class EmployeeCreate(BaseModel):
    emp_no: str = Field(..., min_length=1, max_length=20)
    emp_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    hire_date: date
    dept_id: int | None = None
    position_id: int | None = None
    manager_id: int | None = None


class EmployeeRead(BaseModel):
    emp_id: int
    emp_no: str
    emp_name: str
    email: str | None
    phone: str | None
    hire_date: date
    dept_id: int | None
    dept_name: str | None
    position_id: int | None
    position_name: str | None
    emp_status: str
