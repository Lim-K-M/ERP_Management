# 직원정보 수정 로그인 보호 구현 계획

> **범위 안내:** 이 기능은 `docs/specs/2026-07-08-employee-management-spec.md` §7의 "인증 없음 — 감사 컬럼의 `_BY`는 NULL로 남는 것이 정상" 명시 사항을 벗어나는 **별도 확장**이다. 과제 제출 스펙 문서(`docs/specs/`)는 수정하지 않고 그대로 둔다. 감사 컬럼 `_BY`도 계속 NULL로 남긴다(로그인 사용자를 감사 컬럼에 채우는 것은 이번 범위 밖).

**Goal:** 로그인하지 않은 사용자는 직원 등록/수정/상태변경을 할 수 없도록 세션 기반 로그인 기능을 추가한다. 조회(목록/검색/상세)는 로그인 없이 계속 가능하다.

**Architecture:** Starlette `SessionMiddleware`(서명된 쿠키) 기반 세션 인증. 단일 관리자 계정(로컬 데모용, `.env`로 재정의 가능)으로 로그인한다. 로그인 여부는 `request.session`에 저장하고 Jinja 템플릿에서 `is_logged_in(request)` 전역 함수로 조회한다. 쓰기 라우트(POST/PATCH)에 로그인 필요 dependency를 추가해, 비로그인 시 페이지 라우트는 `/login`으로 303 리다이렉트, JSON API 라우트는 401을 반환한다.

**Tech Stack:** FastAPI, Starlette `SessionMiddleware`, `itsdangerous`(신규 의존성 1개), 기존 Jinja2 템플릿.

---

## Task 1: 세션 미들웨어 + 계정 설정

**파일:**
- 수정: `requirements.txt` — `itsdangerous` 추가
- 수정: `app/config.py` — `session_secret_key`, `admin_username`, `admin_password` 설정 필드 추가(기본값 포함, `.env`로 재정의 가능)
- 수정: `.env.example` — 대응 항목 주석과 함께 추가
- 수정: `app/main.py` — `SessionMiddleware` 등록

**검증:** `pip install -r requirements.txt` 후 서버가 에러 없이 기동되는지 확인.

## Task 2: 로그인/로그아웃 라우트 + 인증 dependency

**파일:**
- 생성: `app/core/auth.py` — `verify_credentials()`, `require_login()`(페이지용, 미로그인 시 커스텀 예외), `require_login_api()`(API용, 미로그인 시 401)
- 수정: `app/core/exceptions.py` — `LoginRequiredError` 추가
- 수정: `app/main.py` — `LoginRequiredError` → `/login?next=...` 303 리다이렉트 exception handler 등록
- 수정: `app/routers/pages.py` — `GET/POST /login`, `POST /logout` 라우트 추가
- 생성: `app/templates/login.html` — 아이디/비밀번호 폼(에러 메시지 표시), `base.html` 상속

**검증:** 브라우저에서 `/login` 접속 → 잘못된 계정 시도 시 에러 메시지 확인 → 올바른 계정으로 로그인 성공 후 원래 가려던 페이지(`next`)로 리다이렉트 확인.

## Task 3: 쓰기 라우트 보호 (페이지 + JSON API)

**파일:**
- 수정: `app/routers/pages.py` — `GET/POST /employees/new`, `POST /employees/{emp_id}`, `POST /employees/{emp_id}/status`에 `Depends(require_login)` 추가
- 수정: `app/routers/api_employees.py` — `POST /api/employees`, `PATCH /api/employees/{emp_id}`, `PATCH /api/employees/{emp_id}/status`에 `Depends(require_login_api)` 추가

**검증:** 로그아웃 상태에서 `/employees/new` 접속 시 `/login`으로 리다이렉트 확인. 로그인 후 등록/수정/상태변경 정상 동작 확인. `/docs`에서 비로그인 상태로 `PATCH /api/employees/{id}` 호출 시 401 확인.

## Task 4: UI 반영 (네비게이션 + 쓰기 버튼 숨김)

**파일:**
- 수정: `app/templating.py` — `is_logged_in(request)` Jinja 전역 함수 추가
- 수정: `app/templates/base.html` — 네비게이션에 로그인 상태별 로그인/로그아웃 링크 + 현재 사용자명 표시
- 수정: `app/templates/employees/list.html` — 비로그인 시 "직원 등록" 버튼 숨김
- 수정: `app/templates/employees/detail.html` — 비로그인 시 수정 폼/상태변경 버튼 숨기고 읽기 전용으로 표시

**검증:** 로그아웃 상태로 목록/상세 화면에서 쓰기 버튼이 안 보이는지, 로그인 후 다시 보이는지 확인.

## Task 5: 종합 검증 + 정리

- 브라우저 시나리오 재확인: 비로그인 조회 가능 → 쓰기 시도 차단 → 로그인 → 등록/수정/상태변경 정상 동작 → 로그아웃 → 다시 차단.
- `feature/employee-login-auth` 브랜치에서 의미 단위 커밋으로 진행 후 PR 생성.
- `docs/internal/progress-checklist.md`에 "스펙 범위 밖 별도 확장"으로 기록.

---

## 로그인 계정 (로컬 데모용, 직관적으로 설정)

| 아이디 | 비밀번호 |
|---|---|
| `admin` | `admin1234` |

`.env`의 `ADMIN_USERNAME` / `ADMIN_PASSWORD`로 재정의 가능. 프로덕션 배포용이 아닌 로컬 데모/과제 확장용 단일 계정이며, 비밀번호 해싱 없이 평문 비교한다(이 프로젝트 범위에서 별도 요구되지 않는 한 과한 보안 장치 추가 없이 단순하게 유지).
