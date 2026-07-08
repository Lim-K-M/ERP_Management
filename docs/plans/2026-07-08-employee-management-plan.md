# 직원관리 시스템 구현 계획

**Goal:** `docs/specs/2026-07-08-employee-management-spec.md`의 요구사항(F-01~F-05, bonus)을 Python/FastAPI + Jinja2 + PostgreSQL로 구현한다.

**Architecture:** FastAPI 단일 서비스. `ddl/`의 기존 스키마를 SQLAlchemy Core `MetaData().reflect()`로 그대로 읽어와 사용(SQL=SSOT, Prisma `db pull`의 Python 대응). Router(HTML/JSON) → Service(순수 로직) → 리플렉션된 Table 순으로 계층 분리. 화면은 Jinja2 서버사이드 렌더링, 폼 제출은 PRG(POST→303 리다이렉트) 패턴.

**Tech Stack:** FastAPI, SQLAlchemy 2.x(Core), asyncpg, Pydantic v2, Jinja2, uvicorn.

---

## Task 0: 문서/승인

- [x] `docs/specs/2026-07-08-employee-management-spec.md` 작성
- [x] 본 계획서 작성 및 사용자 승인 (2026-07-08, Plan Mode)

## Task 1: git/GitHub 초기화

**대상:** 저장소 루트(`ai 개발 방법론\ai 개발 방법론`)

- `git init`, `git branch -M main`
- `.gitignore` 작성 (`.venv/`, `__pycache__/`, `.env`, `*.pyc` 등)
- `.env`는 이미 비밀번호를 담고 있으므로 **최초 커밋 전에 반드시 gitignore 처리**, 대신 `.env.example` 커밋
- `git remote add origin https://github.com/Lim-K-M/ERP_Management.git`
- 초기 커밋(기존 ddl/docs/docker-compose/.claude 포함) → `git push -u origin main`

**검증:** `git status`로 `.env`가 추적되지 않는지 확인 → GitHub 저장소에 push 확인.

## Task 2: `feature/project-scaffold`

**파일:** `app/main.py`, `app/config.py`, `app/db/engine.py`, `app/db/metadata.py`, `app/db/session.py`, `requirements.txt`, `.env.example`

- FastAPI 앱 + lifespan에서 `MetaData().reflect(only=["t_department","t_position","t_employee","t_employment_history"])`
- `/healthz` 헬스체크 라우트
- `.env`에서 `APP_DB_*` 읽어 `DATABASE_URL` 구성 (pydantic-settings)

**검증:** `docker compose up -d` → `psql ... -f ddl/run_all.sql` → `uvicorn app.main:app --reload` 기동 → `/healthz` 200, 콘솔에 리플렉션 에러 없음. PR 생성 → main 병합.

## Task 3: `feature/skills-fastapi-jinja2`

**파일:** `.claude/skills/fastapi-service-architecture/SKILL.md`, `.claude/skills/jinja2-ssr-frontend/SKILL.md`

- 승인된 계획의 §5 스킬 아웃라인대로 작성 (경계/역할, DB 리플렉션 패턴, 검증 매핑표, 상태 전이 패턴, 템플릿 상속, PRG 패턴, 상태 배지 필터, autoescape/CSRF 트레이드오프)

**검증:** frontmatter `description`이 향후 "FastAPI 백엔드 작업", "Jinja2 화면 추가" 요청에 매칭될 만큼 구체적인지 확인. PR → main 병합.

## Task 4: `feature/employee-list-register` (F-01 + F-02)

**파일:** `app/schemas/employee.py,department.py,position.py`, `app/services/employee_service.py,department_service.py,position_service.py`, `app/routers/pages.py,api_employees.py,api_departments.py,api_positions.py`, `app/templates/base.html,partials/*,employees/list.html,_form.html,register.html`, `app/static/css/style.css`

- 목록: 부서/직급 조인 + 상태 배지
- 등록 폼: `EmployeeCreate` 검증(스펙 §4), 성공 시 303 리다이렉트, 실패 시 에러 메시지와 함께 폼 재표시
- `emp_no` 중복(IntegrityError 23505) → 사용자 친화적 에러

**검증:** 브라우저로 등록→목록 반영 확인, 필수값 누락/중복 사번으로 저장 실패 확인.

## Task 5: `feature/employee-detail-status` (F-03 + F-04)

**파일:** `app/templates/employees/detail.html`, `app/core/constants.py`, `app/core/exceptions.py`, `app/services/employee_service.py`(확장), `app/routers/pages.py,api_employees.py`(확장)

- 상세 조회, 수정 폼(공용 `_form.html` 재사용)
- 상태 변경: `ALLOWED_TRANSITIONS` 기반 검증, 허용된 다음 상태만 버튼 노출, 위반 시 409

**검증:** ACTIVE→LEAVE→ACTIVE→RESIGNED 정상 동작 + 배지 즉시 반영, RESIGNED에서 전이 버튼 없음, `/docs`에서 잘못된 전이 시도 시 409.

## Task 6: `feature/employee-search-filter` (F-05, 선택)

**파일:** `app/templates/employees/list.html`(확장), `app/services/employee_service.py`(쿼리 확장), `app/schemas/employee.py`(필터 파라미터)

**검증:** 이름/부서/상태 조합 필터링 결과 확인.

## Task 7: `feature/employment-history` (bonus, 선택)

**파일:** `app/schemas/employment_history.py`, `app/services/employment_history_service.py`, `app/routers/api_employment_history.py`, `app/templates/employees/detail.html`(확장)

- 등록 시 `HIRE` 이력 기록, 상태 변경 시 `LEAVE`/`RETURN`/`RESIGN` 이력 기록

**검증:** 이력 테이블에 변경 사항이 순서대로 쌓이는지 확인.

## Task 8: 제출물 정리

- 결과 화면 스크린샷/데모 캡처
- AI 활용 정리 문서 작성 (`docs/internal/2026-07-08-ai-usage.md` 또는 README 섹션)
- 신규 스킬 2개 최종 점검
- 최종 PR 목록/커밋 로그 정리

---

## 검증 방법 (공통)

각 Task의 PR 병합 전, `docs/specs`의 F-01~F-05 체크리스트와 대조하며 `uvicorn` 로컬 서버 + 브라우저로 직접 동작을 확인한다. `main` 직접 커밋 없이 `feature/*` → PR → 병합만 사용한다. 배포는 하지 않는다.
