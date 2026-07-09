from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import ALLOWED_TRANSITIONS


class EmployeeCreate(BaseModel):
    emp_no: str = Field(..., min_length=1, max_length=20)
    emp_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    hire_date: date
    dept_id: int | None = None
    position_id: int | None = None
    manager_id: int | None = None

    @field_validator("emp_no")
    @classmethod
    def normalize_emp_no(cls, value: str) -> str:
        return value.upper()


class EmployeeUpdate(BaseModel):
    emp_no: str | None = Field(None, min_length=1, max_length=20)
    emp_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    hire_date: date | None = None
    dept_id: int | None = None
    position_id: int | None = None
    manager_id: int | None = None

    @field_validator("emp_no")
    @classmethod
    def normalize_emp_no(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else value


class EmployeeStatusUpdate(BaseModel):
    emp_status: str

    @field_validator("emp_status")
    @classmethod
    def validate_status_value(cls, value: str) -> str:
        if value not in ALLOWED_TRANSITIONS:
            raise ValueError(f"'{value}'는 유효한 상태값이 아닙니다. (ACTIVE/LEAVE/RESIGNED 중 하나)")
        return value


class EmployeeFilter(BaseModel):
    name: str | None = None
    dept_id: int | None = None
    status: str | None = None

    @field_validator("dept_id", mode="before")
    @classmethod
    def blank_dept_id_to_none(cls, value):
        return None if value == "" else value


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
