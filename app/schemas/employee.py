import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.core.constants import ALLOWED_TRANSITIONS

EMP_NO_PATTERN = re.compile(r"^[A-Z]\d{4}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\d{9,11}$")

EMP_NO_FORMAT_ERROR = "사번은 알파벳 1자 + 숫자 4자리 형식이어야 합니다. (예: A0001)"
EMAIL_FORMAT_ERROR = "이메일 형식이 올바르지 않습니다."
PHONE_FORMAT_ERROR = "전화번호는 숫자만 입력해주세요. (하이픈 없이, 9~11자리)"


def _normalize_emp_no(value: str) -> str:
    value = value.upper()
    if not EMP_NO_PATTERN.match(value):
        raise ValueError(EMP_NO_FORMAT_ERROR)
    return value


def _validate_email(value: str | None) -> str | None:
    if not value:
        return None
    if not EMAIL_PATTERN.match(value):
        raise ValueError(EMAIL_FORMAT_ERROR)
    return value


def _validate_phone(value: str | None) -> str | None:
    if not value:
        return None
    if not PHONE_PATTERN.match(value):
        raise ValueError(PHONE_FORMAT_ERROR)
    return value


class EmployeeCreate(BaseModel):
    emp_no: str = Field(..., min_length=1, max_length=20)
    emp_name: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    hire_date: date
    dept_id: int | None = None
    position_id: int | None = None
    manager_id: int | None = None

    @field_validator("emp_no")
    @classmethod
    def normalize_emp_no(cls, value: str) -> str:
        return _normalize_emp_no(value)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str | None) -> str | None:
        return _validate_email(value)

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, value: str | None) -> str | None:
        return _validate_phone(value)


class EmployeeUpdate(BaseModel):
    emp_no: str | None = Field(None, min_length=1, max_length=20)
    emp_name: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    hire_date: date | None = None
    dept_id: int | None = None
    position_id: int | None = None
    manager_id: int | None = None

    @field_validator("emp_no")
    @classmethod
    def normalize_emp_no(cls, value: str | None) -> str | None:
        return _normalize_emp_no(value) if value is not None else value

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str | None) -> str | None:
        return _validate_email(value)

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, value: str | None) -> str | None:
        return _validate_phone(value)


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
    position_id: int | None = None
    status: str | None = None
    hire_year: int | None = None

    @field_validator("dept_id", "position_id", "hire_year", mode="before")
    @classmethod
    def blank_to_none(cls, value):
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
