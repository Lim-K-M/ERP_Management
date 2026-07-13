# 진행 체크리스트 (과제 슬라이드 PART 03 §03 기준)

제출 전까지 이 파일을 계속 갱신하며 각 항목을 확인한다.

## 방법론 (먼저)
- [x] 요구사항 정의서를 읽고 이해했다 — `docs/specs/2026-07-08-employee-management-spec.md`
- [x] `docs/plans/`에 계획서 작성 (범위·파일·검증법) — `docs/plans/2026-07-08-employee-management-plan.md`
- [x] 승인받고 구현을 시작했다 — Plan Mode 승인 완료 (2026-07-08)
- [x] `ERP_<역할>` 브랜치에서 작업했다 — `main` 직접 커밋 금지 규칙에 따라 `ERP_initial_setup`부터 브랜치 사용
- [x] 커밋을 의미 단위로 나눴다 — 전체 26개 PR로 기능/문서 단위 분리(아래 "최종 PR 목록" 참고). 중간에 실수로 `main`에 직접 커밋한 1건은 즉시 브랜치로 옮기고 `main`을 원복해 규칙을 회복했다.

## 기능 완성
- [x] 목록에 주요 필드 + 상태가 함께 보인다 (F-01) — 실제 DB로 검증 완료
- [x] 등록 validation 동작 (본인 ERD 규칙대로) (F-02) — 실제 DB로 검증 완료(사번 중복/필수값 누락/이메일 형식 오류 422 확인)
- [x] 상세·수정이 된다 (F-03) — 실제 DB로 검증 완료(404, 정보 수정, 자기 자신 관리자 지정 금지)
- [x] 재직·휴직·퇴직 변경 시 배지가 바뀐다 (F-04) — 실제 DB로 검증 완료(전이 사이클, RESIGNED 터미널, 잘못된 전이 409)
- [x] PostgreSQL에 실제로 저장된다 — WSL2 복구 후 `docker compose up` + `uvicorn` 실행, 한글 포함 정상 저장 확인(F-01~F-04 범위)

## 검증
- [x] 로컬에서 실행해 브라우저로 동작 확인 — F-01~F-05(검색/필터 포함) + bonus(인사발령 이력, 목록 페이지네이션) 전부 실제 DB로 검증 완료
- [x] 요구사항 정의서 항목과 대조 — §1~§7 전 항목 실제 API/DB 호출로 재검증 완료(아래 "요구사항 정의서 대조 결과" 참고)
- [x] 산출물 정리 — 결과화면(`docs/internal/screenshots/`) · AI 활용(`docs/internal/2026-07-08-ai-usage.md`) · 만든 스킬(최종 점검 완료, 아래 "최종 PR 목록" #18) · 직원관리 ERD 다이어그램(`docs/internal/2026-07-08-employee-erd.md`)

## 참고 — 브랜치 현황
| 브랜치 | 내용 | 상태 |
|---|---|---|
| `ERP_initial_setup` | 초기 자료(규칙/스킬/DDL/docker-compose/spec/plan) | 완료, main 병합 |
| `ERP_project_scaffold` | FastAPI 프로젝트 골격 + DB 리플렉션 | 완료, main 병합. `/healthz` 실제 DB 리플렉션까지 검증 완료(WSL2 복구 후) |
| `ERP_skills_fastapi_jinja2` | 신규 스킬(fastapi-service-architecture, jinja2-ssr-frontend) | 완료, main 병합 |
| `ERP_employee_list_register` | F-01+F-02 (목록/등록) | 완료, 실제 DB로 검증 완료(TemplateResponse 버그 발견·수정 포함) |
| `ERP_employee_detail_status` | F-03+F-04 (상세/상태변경) | 완료, 실제 DB로 검증 완료(404 처리 버그 발견·수정 포함) |
| `ERP_employee_search_filter` | F-05 검색/필터 (선택) | 완료, 실제 DB로 검증 완료 (Task 5 UI 폴리싱 커밋도 이 브랜치로 cherry-pick해 포함) |
| `ERP_data_integrity_review` | 데이터 무결성 리뷰 문서 | PR #8 리뷰 대기 |
| `ERP_employee_integrity_and_sort` | 무결성 리뷰 반영(순환참조/레이스컨디션/퇴직자매니저/사번대소문자/부서필터빈값버그) + 목록 정렬(사번/이름/부서/직급/상태) | 완료, 실제 DB로 검증 완료 |
| `feature/employment-history` | 인사발령 이력 bonus(선택) — HIRE/TRANSFER/PROMOTION/LEAVE/RETURN/RESIGN 전체 기록·조회 + 목록 페이지네이션(20명/페이지) | 완료, 실제 DB로 검증 완료(계획서: `docs/plans/2026-07-12-employment-history-bonus-plan.md`) |
| `feature/employee-login-auth` | 로그인 보호(스펙 범위 밖 별도 확장) — 세션 로그인, 등록/수정/상태변경만 보호, 조회는 그대로 공개 | 완료, 실제 DB/브라우저로 검증 완료 |
| `feature/docs-requirements-check`, `feature/docs-screenshots` | 요구사항 대조 문서, 결과화면 스크린샷 | 완료, main 병합 |
| `fix/emp-no-pattern-and-page-numbers` | 사번 형식 버그 수정(1차: `^A\d{4}$`) + 페이지 번호 네비게이션 | 완료, main 병합 |
| `docs/screenshots-refresh`, `docs/ai-usage-summary`, `docs/skills-final-review`, `docs/final-pr-summary`, `docs/skills-second-pass-review`, `docs/requirements-checklist-final` | 스크린샷 재교체, AI 활용 정리, 스킬/PR 목록 최종 점검 문서 | 완료, main 병합 |
| `docs/skill-routing-and-emp-no-fix` | 스킬 라우팅 문서 4곳을 이 프로젝트 실제 스킬로 교체 + 사번 형식 2차 변경(`^\d{4}$`, 숫자만) + 스크린샷 재캡처 | 완료, main 병합 |
| `fix/query-validation-and-history-pagination` | 4개 관점 병렬 재검토에서 발견한 500 에러 3건·오픈 리다이렉트 수정 + 인사발령 이력 페이지네이션 추가 | 완료, main 병합 |
| `docs/final-consistency-pass` | PR 개수/목록 정정, ai-usage.md 최신화, 미사용 의존성 제거, 스킬 문서 누락 보완 + 사번 입력창 placeholder 버그 수정(사용자 발견) | 완료, main 병합 |
| `fix/history-pagination-regressions` | PR #24 자체를 서브에이전트로 재검토해 발견한 회귀 3건 수정(이력 페이지 유지, 불필요한 쿼리 제거, 필드 에러 집계) | 완료, main 병합 |

## 요구사항 정의서 대조 결과 (2026-07-12)

`docs/specs/2026-07-08-employee-management-spec.md` §1~§7 전 항목을 실제 서버(uvicorn)에 대한 curl/DB 조회로 재검증했다.

| 항목 | 결과 |
|---|---|
| §1 데이터 모델(4개 테이블 리플렉션) | ✅ `app/db/metadata.py`에 4개 테이블 전부 반영 |
| §2 상태 정의/전이 | ✅ `ALLOWED_TRANSITIONS`로 구현, RESIGNED→ACTIVE 시도 시 API 409 확인 |
| F-01 목록(필드+배지) | ✅ 사번/이름/이메일/전화/입사일/부서/직급/상태 전부 응답에 포함 |
| F-02 등록(검증+ACTIVE 강제) | ✅ 클라이언트가 `emp_status=RESIGNED`로 조작 요청해도 서버가 `ACTIVE`로 강제 저장하는 것 확인 |
| F-03 상세/수정 | ✅ (단, 로그인 확장으로 수정은 로그인 필요 — 아래 별도 확장 참고) |
| F-04 상태변경(409) | ✅ 허용되지 않는 전이 API 호출 시 409 + 메시지 확인 |
| F-05 검색/필터 | ✅ status 필터 등 정상 동작 |
| Bonus 이력/페이지네이션 | ✅ 이력 API 응답 확인(HIRE 기록), `/api/departments`, `/api/positions` 스펙대로 응답 |
| §5 API 경로 | ✅ 스펙에 명시된 8개 경로 전부 존재(추가 파라미터는 F-05/bonus용으로 additive) |
| §7 비기능(로컬 실행/CSRF) | ⚠️ 아래 "잔여 리스크" 참고 |

### 잔여 리스크
- 로그인 확장으로 인해 F-02/F-03/F-04의 **쓰기** 동작(등록/수정/상태변경)이 로그인 세션 없이는 불가능해졌다. 조회(F-01/F-05/bonus)는 스펙대로 인증 없이 가능.
- spec §7은 "인증 없음이므로 CSRF 트레이드오프 허용"을 전제로 하는데, 로그인 확장으로 실제 인증 세션이 생겨 이 전제가 더 이상 성립하지 않는다. 다만 세션 쿠키가 `SameSite=Lax`(Starlette `SessionMiddleware` 기본값)로 설정되어 일반적인 크로스사이트 POST 위조는 브라우저 차원에서 상당 부분 막힌다. 별도 CSRF 토큰은 여전히 도입하지 않았다(로컬 데모 범위 내 트레이드오프로 유지).

## 참고 — 스펙 범위 밖 별도 확장
- **로그인 기능**: `docs/specs/2026-07-08-employee-management-spec.md` §7은 "인증 없음"을 명시하고 있어 spec 문서 자체는 수정하지 않았다. 사용자 요청에 따라 별도 확장으로 세션 기반 로그인을 추가해 등록/수정/상태변경만 로그인 필수로 제한했다(계획서: `docs/plans/2026-07-12-employee-login-auth-plan.md`). 로컬 데모용 단일 계정(`admin` / `admin1234`, `.env`로 재정의 가능)이며 감사 컬럼 `_BY`는 기존과 동일하게 NULL로 유지한다.
- **사번/이메일/전화번호 형식 검증 강화**: `docs/specs/` §4는 `emp_no`를 "필수, 최대 20자, 고유", `phone`을 "선택, 최대 20자"로만 규정하고 패턴을 요구하지 않는다. 사용자 요청에 따라 `emp_no`는 `^\d{4}$`(숫자 4자리, 예: `0001`), `phone`은 하이픈 없는 숫자 9~11자리로 스펙보다 엄격하게 제한했다(`app/schemas/employee.py`). **주의**: 마감 제출물을 스펙 §4 기준으로만 평가할 경우, 이 형식과 다른 사번/전화번호 테스트 데이터는 422로 거부된다 — 스펙에 없는 제약이니 평가자에게 별도 확장임을 설명하거나 필요 시 완화 검토.
  - **변경 이력**: 처음엔 `^A\d{4}$`(알파벳 A 고정)였다가, 2026-07-13에 사용자가 "알파벳 상관없이 숫자 4자리로만"으로 재확정해 `^\d{4}$`로 변경했다.

## 최종 PR 목록 (2026-07-13 기준, 총 26개 · 전부 main 병합 완료)

| PR | 제목 | 분류 |
|---|---|---|
| #1 | chore: 프로젝트 초기 자료 및 개발 워크플로우 규칙 세팅 | 초기 세팅 |
| #2 | docs: README 초기 작성 | 초기 세팅 |
| #3 | feat(app): FastAPI 프로젝트 골격 + DB 리플렉션 | 초기 세팅 |
| #4 | docs(skills): FastAPI/Jinja2 스킬 신규 작성 | 초기 세팅 |
| #5 | feat(employee): 직원 목록 조회 + 등록 (F-01, F-02) | 핵심 기능 |
| #6 | feat(employee): 직원 상세/수정 + 상태 변경 (F-03, F-04) | 핵심 기능 |
| #7 | feat(employee): 검색/필터 (F-05) | 핵심 기능(선택) |
| #8 | docs: 데이터 무결성 리뷰 저장 | 품질 개선 |
| #9 | fix(employee): 데이터 무결성 수정 + 목록 정렬 기능 | 품질 개선 |
| #10 | feat(employee): 목록 사이드바 필터(입사연도/상태/직급/부서) | 품질 개선 |
| #11 | feat(auth): 로그인 기반 쓰기 보호 (스펙 범위 밖 별도 확장) | 별도 확장 |
| #12 | feat(history): 인사발령 이력(bonus) + 목록 페이지네이션 | Bonus |
| #13 | docs: 요구사항 정의서 §1~§7 전 항목 대조 결과 | 제출물 정리 |
| #14 | docs: 결과화면 스크린샷 추가 | 제출물 정리 |
| #15 | fix: 사번 형식 A 고정(1차, 이후 #23에서 숫자만으로 재변경) + 페이지 번호 네비게이션 추가 | 버그 수정 |
| #16 | docs: 최신 스크린샷으로 교체 (PR #14/#15 merge 순서 이슈 수정) | 제출물 정리 |
| #17 | docs: AI 활용 정리 문서 작성 | 제출물 정리 |
| #18 | docs(skills): 신규 스킬 2개 최종 점검 | 제출물 정리 |
| #19 | docs: 최종 PR 목록/커밋 로그 정리 | 제출물 정리 |
| #20 | docs(readme): 브랜치별 구현 로그 최신화 + 로그인 계정 안내 | 제출물 정리 |
| #21 | docs(skills): 처음부터 다시 점검해 발견한 추가 불일치 수정 | 제출물 정리 |
| #22 | docs: 최종 요구사항 체크리스트 문서화 | 제출물 정리 |
| #23 | docs(skills): 스킬 라우팅 수정 + fix(employee): 사번 형식 재변경(숫자 4자리) | 버그 수정 |
| #24 | fix: 쿼리 검증 500 에러 3건 + 오픈 리다이렉트 수정, 인사발령 이력 페이지네이션 추가 | 버그 수정 |
| #25 | docs: 최종 문서 정합성 정리 + 사번 placeholder 버그 수정 | 버그 수정 / 제출물 정리 |
| #26 | fix(employee): PR #24 자체 회귀 3건 수정 (서브에이전트 재검토 발견) | 버그 수정 |

- 커밋 로그 전체는 `git log --oneline main`으로 확인 가능. Conventional Commits(`feat`/`fix`/`docs`/`chore`) 형식 유지.
- 관련 계획서: `docs/plans/2026-07-08-employee-management-plan.md`(기본 계획), `docs/plans/2026-07-12-employee-login-auth-plan.md`, `docs/plans/2026-07-12-employment-history-bonus-plan.md`.
- 2026-07-13: 다른 PC 세션에서 병합된 PR #11~#22 이후, 스펙 대조/데이터 무결성·보안/코드 정확성/문서 정합성 4개 관점 병렬 재검토를 진행해 실제 500 에러 3건과 오픈 리다이렉트 1건을 추가로 발견·수정(#24), 스킬 문서가 이 프로젝트 스택을 가리키지 않던 문제와 사번 형식을 최종 확정(#23)했다.
- 이어서 잔여 문서 drift(PR 개수 불일치, 미사용 의존성, 스킬 문서 누락)를 정리하고 사번 placeholder 버그를 사용자가 직접 찾아 수정(#25), PR #24 자체를 다시 서브에이전트로 검토해 회귀 3건을 발견·수정(#26)했다. 직원관리 ERD 다이어그램(`docs/internal/2026-07-08-employee-erd.md`)도 이 시점에 정리했다.
