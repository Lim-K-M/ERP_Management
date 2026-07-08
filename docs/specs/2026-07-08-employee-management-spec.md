# 직원관리 시스템 — 요구사항 정의서

> 인턴 과제(2026-07-13 15:00 제출)의 기획 자료. 구현의 유일한 기준(SSOT)이며, 여기 없는 기능은 임의로 추가하지 않는다.

## 1. 데이터 모델 (ERD/DDL — 이미 확정, `ddl/` 참고)

| 테이블 | 용도 | 주요 컬럼 |
|---|---|---|
| `T_DEPARTMENT` | 부서 (자기참조 조직계층) | `DEPT_ID`, `DEPT_NAME`, `PARENT_DEPT_ID`, `USE_YN` |
| `T_POSITION` | 직급 | `POSITION_ID`, `POSITION_NAME`(unique), `POSITION_LEVEL`, `USE_YN` |
| `T_EMPLOYEE` | 직원 | `EMP_ID`, `EMP_NO`(사번, unique), `EMP_NAME`, `EMAIL`, `PHONE`, `HIRE_DATE`, `DEPT_ID`(FK), `POSITION_ID`(FK), `MANAGER_ID`(자기참조 FK), `EMP_STATUS` |
| `T_EMPLOYMENT_HISTORY` | 인사 발령 이력 (bonus) | `HISTORY_ID`, `EMP_ID`(FK), `CHANGE_TYPE`, `DEPT_ID`, `POSITION_ID`, `EFFECTIVE_DATE`, `REMARK` |

모든 테이블 공통: `CREATED_ON/BY`, `UPDATED_ON/BY` 감사 4컬럼(트리거 `F_AUDIT_LOG`가 `_ON`을 채움, `_BY`는 인증 컨텍스트가 없으므로 이 과제에서는 NULL 유지 — 정상 동작).

## 2. 공통 상태 정의 (모든 인턴 동일 — 임의 변경 금지)

| 상태 | 코드값 | 의미 |
|---|---|---|
| 재직 | `ACTIVE` | 정상 근무 중 (기본값) |
| 휴직 | `LEAVE` | 복직 가능 |
| 퇴직 | `RESIGNED` | 종료 상태 (터미널) |

**허용 전이**: `ACTIVE ⇄ LEAVE`, `(ACTIVE|LEAVE) → RESIGNED`. `RESIGNED`에서는 어떤 전이도 불가.

## 3. 기능 요구사항

- **F-01 직원 목록 조회** — 사번/이름/부서/직급/입사일 등 주요 필드와 재직상태를 표(table)로 표시. 상태는 배지(badge)로 표시.
- **F-02 직원 등록** — ERD 필드에 맞는 입력 폼. §4 검증 규칙을 통과해야 저장. 등록 시 상태는 서버가 `ACTIVE`로 강제(클라이언트가 임의 지정 불가).
- **F-03 직원 상세/수정** — 한 직원의 상세 정보를 조회하고 수정할 수 있다.
- **F-04 상태 변경** — §2 허용 전이만 가능. 변경 시 목록의 배지가 즉시 반영된다. 허용되지 않는 전이는 요청 자체를 거부(HTTP 409).
- **F-05 검색·필터 (선택)** — 이름·부서·상태로 목록을 필터링.
- **Bonus (선택)** — 인사 발령 이력(`T_EMPLOYMENT_HISTORY`) 기록·조회, 목록 페이지네이션.

## 4. 필드 검증 규칙 (DDL 제약에서 도출)

| 필드 | 규칙 |
|---|---|
| `emp_no` (사번) | 필수, 최대 20자, 고유(중복 시 저장 거부) |
| `emp_name` (이름) | 필수, 최대 100자 |
| `email` | 선택, 이메일 형식, 최대 255자 |
| `phone` | 선택, 최대 20자 |
| `hire_date` (입사일) | 필수, 날짜 |
| `dept_id` / `position_id` | 선택이지만 지정 시 실제 존재하는 부서/직급이어야 함(없으면 422) |
| `manager_id` | 선택, 실제 존재하는 직원이어야 하며 자기 자신은 불가 |
| `emp_status` | `ACTIVE`/`LEAVE`/`RESIGNED` 중 하나, §2 전이 규칙 준수 |

## 5. API 스펙 (REST, 스택 무관 — 실제로는 FastAPI로 구현)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/employees` | 목록 (쿼리: `name`, `dept_id`, `status`, `page`, `page_size`) |
| POST | `/api/employees` | 등록 |
| GET | `/api/employees/{id}` | 상세 |
| PATCH | `/api/employees/{id}` | 수정 |
| PATCH | `/api/employees/{id}/status` | 상태 변경 |
| GET | `/api/departments` | 부서 목록 (드롭다운용) |
| GET | `/api/positions` | 직급 목록 (드롭다운용) |
| GET | `/api/employees/{id}/history` | 인사 발령 이력 (bonus) |

화면(HTML)은 `/employees`, `/employees/new`, `/employees/{id}` 등 별도 페이지 라우트로 제공하며 위 API와 동일한 서비스 로직을 공유한다.

## 6. 화면

- 목록 페이지: 표 + 상태 배지 + (선택)검색/필터 바
- 등록 폼 페이지
- 상세/수정 페이지: 조회 + 수정 + 상태 변경 컨트롤(현재 상태에서 허용되는 다음 상태만 노출)

## 7. 비기능 요구사항

- 배포하지 않음 — 로컬 실행(`uvicorn`)으로 동작 확인.
- 인증 없음 — 감사 컬럼의 `_BY`는 NULL로 남는 것이 정상.
- CSRF 토큰 미도입(로컬 데모, 인증 없음) — 알려진 트레이드오프로 문서화.
