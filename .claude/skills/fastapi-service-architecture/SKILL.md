---
name: fastapi-service-architecture
description: "FastAPI + SQLAlchemy Core 리플렉션 기반 백엔드 서비스 아키텍처 — 프로젝트 골격, DB 리플렉션 패턴, Router/Service 계층, Pydantic 검증 매핑, 상태 전이 검증, 에러 응답. FastAPI 백엔드 코드 작성/리뷰, 신규 라우터·서비스 추가 시 적용."
---
# FastAPI 서비스 아키텍처 표준

이 프로젝트(`ERP_Management`)의 FastAPI + SQLAlchemy Core + PostgreSQL 백엔드에 적용하는 아키텍처 표준.

## 경계 (담당 / 위임)
- **담당**: `app/` 프로젝트 골격, DB 리플렉션(`app/db/`), Router(HTML/JSON)/Service 계층, Pydantic 스키마 검증, 상태 전이 검증, 에러 응답 규격.
- **위임**: 화면 렌더링·템플릿 상속·PRG·상태 배지 → [`jinja2-ssr-frontend`](../jinja2-ssr-frontend/SKILL.md). PostgreSQL DDL 자체 설계 → `db-development-postgres`(단, 이 프로젝트는 `ddl/`이 이미 SSOT이므로 앱은 리플렉션으로 **읽기만** 한다 — 새 DB 객체를 앱에서 만들지 않음).

## 0. 프로젝트 골격
```text
app/
├── main.py             # FastAPI 앱, lifespan(리플렉션 실행), /healthz
├── config.py           # pydantic-settings, .env(APP_DB_*) → DATABASE_URL
├── db/
│   ├── engine.py        # AsyncEngine
│   ├── session.py       # async_sessionmaker + get_session 의존성
│   └── metadata.py       # MetaData().reflect(only=[...])
├── schemas/             # Pydantic 요청/응답 모델
├── services/             # 순수 로직 (Router 비의존, 단위 테스트 용이)
├── routers/              # pages.py(HTML) / api_*.py(JSON) — 같은 서비스 로직 공유
└── templates/             # jinja2-ssr-frontend 담당
```

## 1. DB 리플렉션 패턴 (SQL = SSOT)
- `ddl/`의 기존 스키마를 SQLAlchemy Core `MetaData().reflect()`로 그대로 읽는다. ORM 모델을 앱에서 직접 선언하지 않는다(Prisma `db pull`의 Python 대응).
- `app/main.py`의 `lifespan`에서 앱 시작 시 1회 리플렉션을 실행하고 `metadata` 객체에 캐싱한다. 서비스 계층은 `metadata.tables["t_employee"]` 형태로 테이블 객체에 접근한다.
- 리플렉션 대상은 `app/db/metadata.py`의 `REFLECTED_TABLES`에 화이트리스트로 명시한다(`only=` 인자). 새 테이블을 쓰려면 ddl에 실제로 반영한 뒤 이 목록에 추가한다 — **앱이 스키마를 만들지 않는다.**

## 2. 계층 구조
Router(HTML/JSON) → Service(순수 로직) → 리플렉션된 Table. 별도 Controller 계층은 두지 않는다(FastAPI 라우터 함수가 얇은 진입점 역할을 겸함).
- **Router**: 경로/의존성 주입(`Depends(get_session)`)/요청 파싱/응답 포맷만 담당. 비즈니스 로직 금지.
- **Service**: SQLAlchemy Core 쿼리 조립 + 도메인 규칙(검증/상태 전이) 수행. FastAPI에 비의존적이라 단위 테스트가 쉽다.
- 화면 라우터(`routers/pages.py`)와 API 라우터(`routers/api_*.py`)는 **동일한 Service 함수**를 호출해 로직이 갈라지지 않게 한다.

## 3. 검증 매핑표 (Pydantic ↔ 스펙 §4)
`docs/specs/2026-07-08-employee-management-spec.md` §4의 필드별 검증 규칙을 Pydantic 필드/validator로 그대로 옮긴다. 스펙에 없는 검증을 임의로 추가하지 않는다.

| 스펙 규칙 | Pydantic 표현 |
|---|---|
| `emp_no` 필수·최대 20자·고유 | `str = Field(..., max_length=20)` + INSERT 시 `IntegrityError`(23505) 캐치 → 422로 변환 |
| `emp_name` 필수·최대 100자 | `str = Field(..., max_length=100)` |
| `email` 선택·이메일 형식·최대 255자 | `str \| None = Field(None, max_length=255)` + `field_validator`로 정규식 검증(한글 에러 메시지 직접 제어 위해 `EmailStr` 대신 커스텀 정규식 사용) |
| `phone` 선택·최대 20자 | `str \| None = Field(None, max_length=20)` |
| `hire_date` 필수·날짜 | `date` |
| `dept_id`/`position_id` 지정 시 실존 확인 | Service에서 조회 후 없으면 422(`HTTPException`) — FK 위반 예외를 그대로 노출하지 않음 |
| `manager_id` 실존 + 자기 자신 불가 | Pydantic validator가 아니라 **전부 Service**(`_validate_references`)에서 처리: 실존 확인, `manager_id == emp_id`(자기 자신, 수정 API에서만 emp_id를 알 수 있어 적용), 퇴직자 지정 금지, 순환 참조 확인까지 한 곳에서 수행 |
| `emp_status` 등록 시 서버 강제 `ACTIVE` | `EmployeeCreate` 스키마에 `emp_status` 필드 자체를 두지 않음(클라이언트가 값을 보내도 무시) |
| `emp_status` 값·전이 | §4 상태 전이 패턴 참고 |

> **참고 — 스펙보다 엄격한 예외**: 이 프로젝트에서는 사용자 요청에 따라 `emp_no`(`^1\d{3}$`, 1로 시작하는 숫자 4자리)와 `phone`(하이픈 없는 숫자 9~11자리)에 스펙 §4보다 엄격한 정규식 검증을 승인받아 추가했다(`docs/internal/progress-checklist.md` "스펙 범위 밖 별도 확장" 참고). 이런 예외는 **반드시 사용자 승인 후, 문서에 근거를 남기고** 추가한다 — 위 원칙("스펙에 없는 검증을 임의로 추가하지 않는다")의 예외 사례로 취급한다.
>
> **참고 — Pydantic v2 커스텀 validator 에러 메시지**: `field_validator`에서 `raise ValueError(msg)`를 하면 Pydantic이 자동으로 `"Value error, "` 접두사를 붙인다. 화면에 한글 메시지만 깔끔하게 보여주려면 라우터에서 `err["msg"].removeprefix("Value error, ")`로 벗겨낸다.

## 4. 상태 전이 패턴 (F-04)
스펙 §2의 허용 전이(`ACTIVE ⇄ LEAVE`, `(ACTIVE|LEAVE) → RESIGNED`, `RESIGNED`는 터미널)를 단일 상수로 관리한다. Service는 FastAPI에 의존하지 않아야 하므로(§2 원칙), `HTTPException`을 직접 던지지 않고 순수 예외를 발생시켜 Router에서 HTTP 상태 코드로 변환한다.

```python
# app/core/constants.py
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "ACTIVE": {"LEAVE", "RESIGNED"},
    "LEAVE": {"ACTIVE", "RESIGNED"},
    "RESIGNED": set(),
}

# app/core/exceptions.py
class InvalidTransitionError(Exception):
    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        super().__init__(f"{current} -> {target} 전이는 허용되지 않습니다.")

# app/services/employee_service.py
async def change_status(session, emp_id: int, target_status: str) -> None:
    current = await get_employee(session, emp_id)
    if target_status not in ALLOWED_TRANSITIONS[current["emp_status"]]:
        raise InvalidTransitionError(current["emp_status"], target_status)
    # 현재 상태를 조건으로 건 조건부 UPDATE로 레이스 컨디션 방지 (rowcount==0이면 그 사이 상태가 바뀐 것)
    ...

# app/routers/api_employees.py
@router.patch("/{emp_id}/status")
async def change_status(emp_id: int, payload: EmployeeStatusUpdate, session=Depends(get_session)):
    try:
        await employee_service.change_status(session, emp_id, payload.emp_status)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return await employee_service.get_employee(session, emp_id)
```

- 상태 변경 API(`PATCH /api/employees/{id}/status`)는 항상 Service의 전이 검증을 거친다. 허용되지 않은 전이는 **요청 자체를 거부**(409) — 부분 처리하거나 조용히 무시하지 않는다.
- 화면 라우터(`routers/pages.py`)는 같은 `InvalidTransitionError`를 잡아 위조 요청으로 간주하고 상세 페이지로 되돌린다(화면에는 애초에 허용된 다음 상태만 버튼으로 노출하므로, 여기 도달하면 요청이 조작된 경우다).
- 화면에는 `ALLOWED_TRANSITIONS[current_status]`로 계산한 "현재 허용되는 다음 상태"만 버튼으로 노출한다(→ 렌더링은 `jinja2-ssr-frontend` 담당, 계산은 이 스킬의 Service 로직).

## 5. 에러 응답
- FastAPI `HTTPException`으로 통일한다: 422(검증 실패) · 404(not found) · 409(상태 전이 위반) · 500(그 외).
- `IntegrityError`(unique violation, `emp_no` 중복 등)는 Service에서 잡아 사용자 친화적 422 메시지로 변환한다 — 원본 DB 에러 문자열을 그대로 클라이언트에 노출하지 않는다.
