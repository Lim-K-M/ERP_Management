# ERP_Management

## 프로젝트 개요

인턴 과제로 진행하는 직원관리(HR) 시스템이다. 회사의 부서·직급 구조 아래 직원을 등록·조회·관리하고, 재직 상태(재직/휴직/퇴직) 변화를 추적한다.

주요 기능:
- 직원 목록 조회 — 사번·이름·부서·직급·입사일과 재직상태 배지를 표로 표시
- 직원 등록 — 검증 규칙을 통과한 입력만 저장, 등록 시 상태는 자동으로 "재직"
- 직원 상세 조회·수정
- 재직 상태 변경 — 재직⇄휴직, (재직|휴직)→퇴직만 허용, 퇴직은 종료 상태
- (선택) 이름·부서·상태로 검색/필터, 인사발령 이력 기록·조회

요구사항은 `docs/specs/`, 구현 계획은 `docs/plans/`를 유일한 기준(SSOT)으로 따른다.

## 기술 스택

- **Backend**: FastAPI, SQLAlchemy 2.x(Core), asyncpg, Pydantic v2
- **Frontend**: Jinja2 서버사이드 렌더링 (PRG 패턴)
- **DB**: PostgreSQL 16 (Docker Compose)

## 문서 구조

| 폴더 | 용도 |
|---|---|
| `docs/specs/` | 기획·요구사항 스펙 — 구현의 기준 |
| `docs/plans/` | 구현 계획서 (날짜 프리픽스) |
| `docs/designs/` | 디자인 양식·작성 안내 |
| `docs/guides/` | 아키텍처·개발자 가이드 |
| `docs/internal/` | 진행 체크리스트 등 내부 관리 자료 |
| `ddl/` | PostgreSQL 스키마(DDL) — SQL이 SSOT, 앱은 리플렉션으로 읽음 |

## 브랜치 전략

- `main`은 PR로만 반영, 직접 커밋 금지.
- 브랜치명은 `ERP_<역할>` 컨벤션 사용 (예: `ERP_initial_setup`, `ERP_project_scaffold`). 현황은 `docs/internal/progress-checklist.md` 참고.

## 로컬 실행

```bash
cp .env.example .env   # DB_PASSWORD/PGADMIN_PASSWORD/APP_DB_PASSWORD 값 채우기
docker compose up -d
psql "postgresql://emko:${DB_PASSWORD}@localhost:5433/emko" -f ddl/run_all.sql

python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000/healthz 로 확인
```

### 로그인 (스펙 범위 밖 별도 확장)

등록/수정/상태변경은 로그인이 필요하다(조회는 로그인 없이 가능). 로컬 데모용 단일 계정:

| 아이디 | 비밀번호 |
|---|---|
| `admin` | `admin1234` |

`.env`의 `ADMIN_USERNAME` / `ADMIN_PASSWORD`로 재정의 가능. 자세한 내용은 `docs/internal/progress-checklist.md`의 "스펙 범위 밖 별도 확장" 참고.

## 진행 상황

- 계획: `docs/plans/2026-07-08-employee-management-plan.md`
- 체크리스트: `docs/internal/progress-checklist.md`

## 브랜치별 구현 로그

> 브랜치를 병합할 때마다 이 섹션에 새 항목을 추가한다. 무엇을·왜 구현했는지 간단히 남긴다.

### `ERP_initial_setup` (Task 0~1)

- 개발 워크플로우 규칙(`.claude/rules/development-workflow.md`)과 관련 스킬 세팅
- DB 스키마(`ddl/`)와 `docker-compose.yml` 커밋
- 요구사항 스펙(`docs/specs/2026-07-08-employee-management-spec.md`), 구현 계획서(`docs/plans/2026-07-08-employee-management-plan.md`) 작성
- git/GitHub 초기화(`.gitignore`로 `.env` 제외, origin 연결), 진행 체크리스트(`docs/internal/progress-checklist.md`) 추가
- 코드 구현은 아직 없음 — 다음 브랜치(`ERP_project_scaffold`)부터 FastAPI 앱 골격 시작

### `ERP_project_scaffold` (Task 2)

- `app/main.py` — FastAPI 앱 + lifespan에서 DB 리플렉션 실행, `/healthz` 헬스체크
- `app/config.py` — pydantic-settings로 `.env`의 `APP_DB_*` 읽어 `DATABASE_URL` 구성
- `app/db/engine.py`, `app/db/session.py` — SQLAlchemy 2.x 비동기 엔진/세션
- `app/db/metadata.py` — `MetaData().reflect(only=[...])`로 `t_department`/`t_position`/`t_employee`/`t_employment_history` 리플렉션
- `requirements.txt` 작성
- **알려진 트레이드오프**: 이 작업 환경에서 Docker Desktop이 WSL2 미설치(`REGDB_E_CLASSNOTREG`)로 기동되지 않아 `docker compose up` → `/healthz` 실제 DB 연동 검증은 못했음. `python -c "import app.main"`으로 문법·임포트 오류만 확인. Docker가 정상 동작하는 환경에서 반드시 재검증 필요.

### `ERP_skills_fastapi_jinja2` (Task 3)

- `.claude/skills/fastapi-service-architecture/SKILL.md` — 프로젝트 골격, DB 리플렉션 패턴, Router/Service 계층, Pydantic 검증 매핑표(스펙 §4), 상태 전이 패턴(F-04), 에러 응답 규격
- `.claude/skills/jinja2-ssr-frontend/SKILL.md` — 템플릿 상속 구조, PRG(POST→303) 패턴, 상태 배지 커스텀 필터, autoescape/CSRF 트레이드오프
- 기존 `backend-service-architecture`/`frontend-ssr` 스킬(Node.js/Express·Vanilla HTML 대상, 다른 프로젝트 템플릿)은 이 프로젝트 스택과 맞지 않아 대체용으로 신규 작성. 두 스킬 모두 이 세션에서 정상 로드되는 것으로 frontmatter description 확인 완료.

### `ERP_employee_list_register` (Task 4 — F-01+F-02)

- `app/schemas/{employee,department,position}.py` — `EmployeeCreate`(스펙 §4 검증), `EmployeeRead`, 드롭다운용 `DepartmentRead`/`PositionRead`
- `app/services/{employee,department,position}_service.py` — 목록 조회(부서/직급 조인), 등록(부서/직급/관리자 존재 검증 + `emp_no` 중복 처리), 등록 시 상태는 서버가 `ACTIVE`로 강제
- `app/routers/pages.py` — `GET/POST /employees/new`(PRG: 실패 시 폼 재표시, 성공 시 303 리다이렉트), `GET /employees`(목록)
- `app/routers/api_{employees,departments,positions}.py` — 동일 서비스 로직을 공유하는 JSON API
- `app/templating.py` — `status_badge` Jinja 필터(재직/휴직/퇴직 배지)
- `app/templates/{base.html, partials/_nav.html, employees/{list,_form,register}.html}`, `app/static/css/style.css`
- **실제 DB 연동 검증 완료** (WSL2 복구 후 `docker compose up -d` → `ddl/run_all.sql` → `uvicorn` 실제 기동):
  - `GET /employees`, `GET /employees/new` 정상 렌더링, 등록 성공 시 303 → `/employees` 리다이렉트, 목록에 새 직원 즉시 반영
  - 등록 시 `emp_status`가 클라이언트 입력과 무관하게 항상 `ACTIVE`로 저장되는 것 확인
  - 검증 실패 케이스 3종 모두 422 + 폼 재표시 확인: 사번 중복(`emp_no` 유니크 제약 위반), 필수값(`hire_date`) 누락, 이메일 형식 오류
  - 한글 직원명이 DB에 올바른 UTF-8로 저장되는 것을 `encode(...,'hex')`로 바이트 단위까지 확인
- **버그 발견 및 수정**: 이 환경의 Starlette 버전이 `Jinja2Templates.TemplateResponse`의 시그니처를 `(name, {"request":...})`에서 `(request, name, context)`로 변경했음. 기존 방식으로 호출한 3곳(`pages.py`)이 500 에러를 냈고, 신버전 시그니처로 수정해 해결. **정적 검증(임포트/템플릿 더미 렌더링)만으로는 이 버그를 못 잡았음** — 실제 실행 검증이 필요했던 사례.

### `ERP_employee_detail_status` (Task 5 — F-03+F-04)

- `app/core/constants.py` — `ALLOWED_TRANSITIONS`(스펙 §2 전이 규칙) 단일 소스, `next_allowed_statuses()`
- `app/core/exceptions.py` — `EmployeeValidationError`/`EmployeeNotFoundError`/`InvalidTransitionError` (기존 `employee_service.py`에 있던 예외를 이곳으로 정리)
- `app/services/employee_service.py`(확장) — `get_employee`(404), `update_employee`(부분 수정, 부서/직급/관리자 존재 확인 + 자기 자신 관리자 지정 금지), `change_status`(허용된 전이만 반영, 아니면 409)
- `app/routers/api_employees.py`(확장) — `GET/PATCH /api/employees/{id}`, `PATCH /api/employees/{id}/status`(허용 안 되는 전이 시 409)
- `app/routers/pages.py`(확장) — `GET/POST /employees/{id}`(상세·수정, PRG), `POST /employees/{id}/status`
- `app/templates/employees/detail.html` — 상세 정보 + 현재 상태에서 허용되는 다음 상태만 버튼으로 노출 + `_form.html` 재사용한 수정 폼. `list.html`에 상세 페이지 링크 추가
- **실제 DB 연동 검증 완료**:
  - 존재하지 않는 `emp_id` 조회 시 404 (최초 500이 나던 버그를 발견해 `pages.py`에 404 처리 추가)
  - `ACTIVE → LEAVE → ACTIVE → RESIGNED` 전이 사이클 정상 동작, 목록/상세 배지 즉시 반영
  - `RESIGNED` 상태에서 상세 페이지에 전이 버튼이 하나도 노출되지 않음(터미널 상태) 확인
  - `RESIGNED → ACTIVE`처럼 허용되지 않는 전이를 JSON API로 직접 시도 시 409 확인
  - 정보 수정(전화번호 등 부분 수정) 반영 확인, 자기 자신을 관리자로 지정 시 422 확인

### UI 폴리싱 (F-05/bonus 착수 전)

- `app/static/css/style.css` — CSS 커스텀 프로퍼티(색상/간격 토큰)로 재작성, `.btn`/`.card`/`.page-header`/`.table-wrap`/`.employee-form .field` 등 재사용 가능한 컴포넌트 클래스 도입. 새 화면(검색바, 인사발령 이력 등)을 추가할 때 이 토큰·클래스를 그대로 재사용하도록 설계
- `base.html`/`_nav.html` — 상단 내비게이션에 브랜드 표시 추가
- `list.html` — 페이지 헤더(제목 + "직원 등록" 버튼) + 테이블을 카드로 감쌈, 빈 목록 상태 스타일링
- `register.html`/`detail.html` — 목록으로 돌아가는 브레드크럼, 폼을 카드로 감쌈
- `_form.html` — `<label>`+`<input>`을 `.field` 단위로 재구성해 2열 그리드 레이아웃(모바일에서는 1열)으로 정리, 필드별 에러 메시지 위치 통일
- `detail.html` — 상태 변경 버튼에 상태별 색상(재직=success outline, 휴직=warning outline, 퇴직=danger outline) 적용
- 실제 브라우저 기준으로 목록/등록/상세 페이지 전부 200 확인, 새로 등록한 직원의 상세 페이지에서 색상이 적용된 상태 변경 버튼이 정상 렌더링되는 것까지 확인 후 테스트 데이터 정리
- **참고**: 이 커밋은 원래 Task 5 PR(#6)에 포함시키려 했으나, push 전에 #6이 먼저 merge되어 main에 반영되지 못했다. `ERP_employee_search_filter` 브랜치로 cherry-pick해 이번 PR에 포함시켰다.

### `ERP_employee_search_filter` (Task 6 — F-05)

- `app/schemas/employee.py` — `EmployeeFilter`(name/dept_id/status)
- `app/services/employee_service.py`(확장) — `list_employees`가 `EmployeeFilter`를 받아 이름 `ilike` 부분일치 + 부서/상태 동등 조건을 조합
- `app/routers/api_employees.py`(확장) — `GET /api/employees`가 `name`/`dept_id`/`status` 쿼리 파라미터를 받음 (스펙 §5 API 스펙 표 반영)
- `app/routers/pages.py`(확장) — `GET /employees`도 동일 쿼리 파라미터 지원, 부서 목록과 현재 필터값을 템플릿에 전달
- `app/templates/employees/list.html` — 이름 검색창 + 부서/상태 드롭다운 + 검색/초기화 버튼(`.toolbar`), 현재 필터값이 폼에 그대로 반영되어 새로고침해도 유지
- **실제 DB 연동 검증 완료** (테스트용 부서 5개·직급 5개·직원 100명을 로컬 DB에 시딩해 검증):
  - 이름 부분검색, 부서 필터, 상태 필터 각각 단독 동작 확인
  - 이름+상태 조합 필터 동작 확인 (결과 6건 전부 조건 일치)
  - HTML 목록 페이지에서 필터 적용 시 행 수가 DB의 실제 개수와 일치, `<select>`에 현재 필터값이 `selected`로 유지되는 것 확인

### `ERP_employee_integrity_and_sort`

`docs/internal/2026-07-09-data-integrity-review.md` 리뷰에서 발견한 항목을 반영하고, 목록에 정렬 기능을 추가.

**데이터 무결성 수정**
- `_validate_references`(`employee_service.py`) — 관리자 지정 시 (1) 대상이 `RESIGNED` 상태면 거부, (2) `_would_create_manager_cycle`로 매니저 체인을 따라 올라가 순환 참조가 생기면 거부
- `change_status` — `SELECT` 후 `UPDATE`하던 방식에서, `WHERE emp_status = 현재값` 조건부 `UPDATE`로 변경(레이스 컨디션 방지). `rowcount == 0`이면 그 사이 상태가 바뀐 것으로 보고 409 처리
- `EmployeeCreate`/`EmployeeUpdate`에 `emp_no` 대문자 정규화 validator 추가 — `e001`과 `E001`이 다른 사번으로 취급되던 문제 해결
- `EmployeeStatusUpdate.emp_status`에 유효값(`ACTIVE`/`LEAVE`/`RESIGNED`) validator 추가 — 존재하지 않는 상태값을 보내면 409(전이 불가) 대신 422(값 자체가 잘못됨)로 명확히 구분
- **버그 발견 및 수정**: 목록 검색바에서 "전체 부서"(빈 값) 선택 후 검색을 누르면 FastAPI가 빈 문자열을 `int`로 파싱하려다 422 에러를 냈음. `dept_id` 쿼리 파라미터를 문자열로 받아 `EmployeeFilter`의 `mode="before"` validator에서 빈 문자열을 `None`으로 변환하도록 수정

**정렬 기능 (사번/이름/부서/직급/상태)**
- `employee_service.list_employees`가 `sort`/`order` 파라미터를 받아 해당 컬럼으로 `ORDER BY` 적용
- `GET /employees`, `GET /api/employees` 모두 `sort`/`order` 쿼리 파라미터 지원
- `list.html` 테이블 헤더에 작은 삼각형(▲/▼) 정렬 버튼 추가 — 클릭 시 해당 컬럼으로 정렬하고 다시 누르면 오름차순/내림차순 토글, 현재 필터 조건을 유지한 채 정렬 링크 생성

**실제 DB 연동 검증 완료**
- 부서 필터 빈 값 검색 버그 재현 후 수정 확인(200)
- `e001` 형태로 등록 시 `E001`로 저장, 대소문자만 다른 사번 재등록 시 422 확인
- 순환 참조 시도(A→B, B→A) 422로 차단, 퇴직자를 매니저로 지정 시도 422로 차단 확인
- 잘못된 상태값(`"FOO"`) 전송 시 422 확인(기존엔 409)
- 이름/상태 컬럼 정렬 오름차순·내림차순 확인(DB 자체적으로 desc가 asc의 정확한 역순임을 확인)
- 동시 요청 두 개로 상태변경 레이스 컨디션을 재현 시도했으나 두 요청이 순차적으로 처리되어(둘 다 유효한 전이) 실제 경합 상황은 못 만듦 — 조건부 UPDATE 로직 자체는 코드 리뷰로 원자성 확인
- 검증 후 테스트로 등록한 직원 데이터는 전부 삭제(부서 5개·직급 5개 참고 데이터만 유지) — 이후 실수로 사용자가 요청한 100명 테스트 데이터까지 지워서 동일 랜덤 시드로 재생성해 복구

**목록 사이드바 필터 UI**
- 왼쪽 사이드바에 입사연도/상태/직급/부서 필터를 배치. 초안은 클릭형 버튼 목록이었으나 옵션이 많아지자 세로 길이가 너무 길어져, 각 항목을 하나씩 차지하는 `<select>` 드롭다운(변경 시 `onchange="this.form.submit()"`로 즉시 재조회)으로 교체해 사이드바를 컴팩트하게 유지
- 이름 검색창을 사이드바 상단으로 이동, 기존 검색창 자리(목록 본문 상단)에는 브랜드 배너(로고 자리, 실제 로고 이미지는 없어 텍스트 워드마크로 대체) 배치
- `.sidebar`에 `position: sticky` 적용 — 페이지를 아래로 스크롤해도 사이드바가 함께 따라오도록 처리(콘텐츠가 뷰포트보다 길어질 경우를 대비해 `max-height`+`overflow-y: auto`도 함께 지정)
- `app/schemas/employee.py`의 `EmployeeFilter`에 `position_id`/`hire_year` 추가, `employee_service.list_employees`가 직급/입사연도 조건을 조합. `list_hire_years()`로 실제 DB에 존재하는 입사연도만 드롭다운에 노출
- **실제 DB 연동 검증 완료**: 사이드바 연도 옵션이 실제 데이터 기준(2018~2026)으로 뜨는 것 확인, 부서+상태 조합 선택 시 각 `<select>`에 `selected`로 반영되고 실제 조회 결과(17건)가 조건과 정확히 일치하는 것까지 확인

### `feature/employee-login-auth` (PR #11 — 스펙 범위 밖 별도 확장)

spec §7이 "인증 없음"을 명시하고 있어 spec 문서 자체는 그대로 두고, 사용자 요청에 따라 세션 기반 로그인을 별도 확장으로 추가. 등록/수정/상태변경만 로그인 필수로 제한하고 조회(F-01/F-05/bonus)는 그대로 공개.

- `app/core/auth.py` — `require_login`(페이지, 미로그인 시 `/login`으로 303)/`require_login_api`(API, 401) 두 종류의 의존성
- Starlette `SessionMiddleware`(서명된 쿠키) 등록, 로컬 데모용 단일 계정(`admin`/`admin1234`, `.env`로 재정의 가능)
- `app/templating.py`의 `is_logged_in(request)` 전역 함수로 템플릿에서 로그인 여부 분기 — 비로그인 시 목록의 등록 버튼, 상세의 수정폼/상태변경 버튼을 숨기고 읽기전용으로 표시
- 저장 성공 시 "저장되었습니다" 팝업, 퇴직(터미널 상태) 처리 전 confirm()으로 재확인 팝업 추가
- 사번(`^A\d{4}$`)/이메일/전화번호(숫자 9~11자리) 형식 검증 강화 — 이것도 spec §4보다 엄격한 별도 확장(자세한 내용은 `docs/internal/progress-checklist.md` 참고)
- **실제 브라우저/curl 검증 완료**: 비로그인 시 쓰기 라우트 303/401 차단, 로그인 후 정상 동작, 로그아웃 후 재차단, 조회는 로그아웃 상태에서도 항상 가능

### `feature/employment-history` (PR #12 — Task 7, Bonus)

spec §3 Bonus(인사 발령 이력 + 목록 페이지네이션)를 원 계획(Task 7)보다 확장된 범위로 구현 — CHANGE_TYPE 6종(HIRE/TRANSFER/PROMOTION/LEAVE/RETURN/RESIGN) 전부 기록.

- `app/services/employment_history_service.py` — `record_history()`/`list_history()`
- `app/services/employee_service.py`(확장) — 등록=HIRE, 부서변경=TRANSFER, 직급변경=PROMOTION, 상태변경은 LEAVE/RETURN/RESIGN으로 매핑해 같은 트랜잭션에서 기록
- `GET /api/employees/{id}/history` 추가, 상세 페이지에 이력 표 노출(로그인 여부 무관, 조회이므로)
- `employee_service`에 `count_employees()`/필터 로직 공유(`_apply_filters`), `list_employees`에 `page`/`page_size` 추가 — 목록 페이지·JSON API 모두 페이지네이션(20명/페이지) 지원
- **실제 DB 연동 검증 완료**: HIRE→TRANSFER→PROMOTION→LEAVE→RETURN→RESIGN 전체 시나리오로 이력 순서 확인, 100명 데이터로 5페이지 분할·경계·필터 재계산 확인

### 제출물 정리 (Task 8, PR #13~#19)

- **요구사항 정의서 대조**(#13): spec §1~§7 전 항목을 실제 curl/DB 조회로 재검증. 로그인 확장으로 spec §7의 "인증 없음→CSRF 트레이드오프 허용" 전제가 깨진 점을 잔여 리스크로 기록
- **결과화면 스크린샷**(#14, #16): Playwright로 헤드리스 브라우저를 직접 구동해 로그인→등록→부서/직급 변경→상태변경까지 실제 시나리오를 수행하며 8장 캡처(`docs/internal/screenshots/`)
- **버그 수정**(#15): 사번 형식이 "알파벳 **A** + 숫자 4자리"여야 하는데 정규식을 `^[A-Z]\d{4}$`(임의 알파벳)로 잘못 일반화했던 버그를 `^A\d{4}$`로 수정. 목록에 구글 스타일 페이지 번호 네비게이션(이전/다음 + 1,2,3,…,N) 추가
- **AI 활용 정리**(#17): `docs/internal/2026-07-08-ai-usage.md` — 계획서 우선 워크플로우, AI가 발견한 버그, 스펙 범위 밖 확장 승인 절차, AI 자신의 실수(사번 정규식 과일반화·`main` 직접 커밋·인코딩 문제)와 정정 과정 정리
- **스킬 최종 점검**(#18): `fastapi-service-architecture`/`jinja2-ssr-frontend` 두 스킬을 실제 구현과 대조 — PRG 예제의 구버전 `TemplateResponse` 시그니처, `EmailStr`→커스텀 정규식 전환 등 stale한 부분 수정
- **최종 PR 목록/커밋 로그 정리**(#19): `docs/internal/progress-checklist.md`에 전체 PR을 분류한 표 추가

### 스킬 라우팅 정합성 재점검 + 사번 형식 재변경 (2026-07-13)

- **스킬 라우팅 수정**: `backend-service-architecture`/`frontend-ssr`(다른 프로젝트용, 미사용)를 아직도 "정답"으로 가리키던 라우팅 문서 4곳을 이 프로젝트의 실제 스킬로 교체 — `.claude/rules/development-workflow.md`(always-on 규칙의 도메인 스킬 목록), `.claude/skills/README.md`(전체 스킬 지도를 FastAPI/Jinja2/PostgreSQL 기준으로 재작성, `db-development-postgres`를 ③으로 명시적 편입), `code-review-standard/SKILL.md`(리뷰 체크리스트), `db-development-postgres/SKILL.md` + 상세 가이드(Prisma 연동 섹션을 SQLAlchemy Core 리플렉션 기준으로 재작성). 두 미사용 스킬 자체는 손대지 않고 "다른 프로젝트용, 참고 보존"으로 명확히 표시만 함
- **사번 형식 재변경**: PR #15에서 `^A\d{4}$`(알파벳 A 고정)로 확정했던 사번 형식을, 사용자가 원본 근거(스펙/계획서/AI활용정리 어디에도 "A"나 "E" 고정 요구는 없었음을 함께 확인 후) "알파벳 상관없이 숫자 4자리로만"으로 재확정해 `^\d{4}$`로 변경(`app/schemas/employee.py`)
- **실제 DB 연동 검증 완료**: 옛 형식(`A0001`) 등록 시도 422 확인, 새 형식(`0001`) 등록 201 확인, 자릿수 오류(`00001`) 422 확인. 기존 시드 데이터 100명의 사번(`E1001~E1100`)도 새 형식(`1001~1100`)으로 일괄 변경

### 전체 재검토(4개 병렬 에이전트) + 버그 수정 + 인사발령 이력 페이지네이션 (2026-07-13)

스펙 대조/데이터 무결성·보안/코드 정확성/문서-코드 정합성 4개 관점으로 프로젝트 전체를 처음부터 다시 검토(에이전트 병렬 실행). 실제로 500 에러를 내는 버그 3개와 오픈 리다이렉트 1개를 발견해 전부 수정:

- **목록 필터 쿼리파라미터 미검증**(`dept_id`/`position_id`/`hire_year`에 숫자가 아닌 값) → `EmployeeFilter` 생성 실패가 그대로 500으로 새던 것을 `pages.py`/`api_employees.py` 양쪽에서 `ValidationError`를 잡아 422로 변환
- **JSON API 페이지네이션 범위 미검증** → `page=0`/`page=-1`/`page_size=-5`가 Postgres `OFFSET/LIMIT must not be negative`로 500이 나던 것을, `Query(ge=1)`/`Query(ge=1, le=100)`으로 FastAPI 레벨에서 422 처리(HTML 목록 라우트는 원래도 clamp돼 있어 안전했음 — API만 누락)
- **폼 등록/수정 시 정수 변환 미검증** → `_optional_int()`가 `int(value)`를 그냥 호출해 `ValueError`가 그대로 새던 것을, 실패 시 `EmployeeValidationError`를 던지도록 바꾸고 등록/수정 라우트에서 함께 처리
- **로그인 `next` 파라미터 오픈 리다이렉트** → `_safe_next_url()`로 이 앱 내부의 상대 경로(`/`로 시작, `//`·`/\`로 시작하지 않음)만 허용하도록 검증 추가. `/login`이 next 값을 렌더링할 때와 로그인 성공 후 리다이렉트할 때 모두 적용

**인사발령 이력 페이지네이션 추가**(요청사항): `employment_history_service.list_history()`가 `page`/`page_size`를 받아 구간 조회하도록 확장, `count_history()` 신규 추가. 상세 페이지에서 이력이 5건 초과일 때만 목록과 동일한 스타일의 페이지네이션 컨트롤 노출.

**실제 DB 연동 검증 완료**: 위 4개 버그 전부 수정 전(500)/수정 후(422 또는 정상 리다이렉트) 재현 확인. 이력 4건(페이지네이션 없음) → 6건으로 늘려 페이지네이션 등장 + 2페이지에 남은 1건 정확히 표시되는 것 확인 후 테스트 이력 삭제.

### 문서 정합성 정리 + PR #24 회귀 수정 (2026-07-13, PR #25~#26)

- **문서 정합성 정리**(#25): `progress-checklist.md`/`ai-usage.md`의 PR 개수·목록이 실제 병합 상태보다 뒤처져 있던 것을 정정, 미사용 의존성(`pydantic[email]`) 제거, 스킬 문서 누락분 보완. 사번 형식을 숫자 4자리로 바꾸면서 검증 로직(`app/schemas/employee.py`)만 고치고 놓쳤던 등록/수정 폼의 placeholder(`"예: A0001"`)를 **사용자가 화면에서 직접 발견**해 수정
- **PR #24 자체 회귀 수정**(#26): "방금 만든 수정 커밋도 무조건 옳다고 가정하지 말고 다시 검토해달라"는 요청에 따라 서브에이전트로 PR #24만 별도 재검토해 발견한 회귀 3건 수정 — 이력 페이지 실패 시 무조건 1페이지로 초기화되던 것을 실제 요청 페이지 유지로, 수정 성공(리다이렉트) 경로에서도 이력 조회 쿼리가 불필요하게 실행되던 것을 실패 경로에서만 지연 조회하도록, 폼 정수 필드 여러 개가 동시에 잘못돼도 첫 번째 에러만 보고되던 것을 전부 집계해 보고하도록 수정

### 직원관리 ERD 문서화 + 최종 체크리스트 마감 (2026-07-13, PR #27)

- `docs/specs/`§1 데이터 모델과 `ddl/`의 기존 스키마(부서/직급/직원/인사발령이력 4개 테이블)를 시각화한 ERD 문서(`docs/internal/2026-07-08-employee-erd.md`)를 신규 작성. `db-development-postgres` 스킬 표준(네이밍/공통 감사 컬럼/UUID)에 맞춰 정리했고, 로그인 확장 이후에도 감사 컬럼 `_BY`를 NULL로 유지하는 것이 승인된 스코프 예외임을 명시
- `progress-checklist.md`/`ai-usage.md`에 산출물 정리 항목 반영

### 목록 화면 부서/직급/상태별 인원 수 표시 (2026-07-13, PR #28)

스펙 범위 밖 소규모 UI 개선. 대화 중 여러 차례 방향을 조정한 끝에 최종적으로 아래 형태로 정착했다:

- 표 헤더의 **기존 정렬 화살표**(부서/직급/상태 컬럼의 ▲/▼)를 클릭하면, 그 컬럼 기준 인원 수 분포가 ERP 브랜드 배너 박스 안에(가운데 정렬, pill 형태 칩으로) 나타난다. 기본값(사번/이름 정렬)일 때는 상태별 인원(재직/휴직/퇴직)을 보여준다
- `employee_service.py`에 `count_by_status`/`count_by_department`/`count_by_position` GROUP BY 쿼리 3개 추가 — 카운트는 전체(global) 기준이라 다른 필터를 선택해도 숫자가 흔들리지 않는다
- 초기에는 사이드바 드롭다운 `(N)` 표시 → 상단 요약 스트립 → 버튼 3개(팝오버) 순으로 시도했다가 최종안으로 정착. 버튼 방식을 검증하던 중 `<details>`의 `toggle` 이벤트가 스펙상 비동기(큐잉된 태스크)로 발생해 두 패널이 동시에 열리는 레이스 컨디션을 실제로 재현(동일 시나리오 5회 반복 실행)해 발견했으나, 최종적으로 정렬 화살표 재사용 방식으로 방향을 바꾸며 해당 코드 자체가 제거됨
- 부서 5개가 한 줄에 안 들어가 배너가 2줄로 접히던 문제를 페이지 컨테이너 `max-width`를 1040px → 1180px로 소폭 확장해 해결
