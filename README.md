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
