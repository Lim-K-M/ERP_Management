# 진행 체크리스트 (과제 슬라이드 PART 03 §03 기준)

제출 전까지 이 파일을 계속 갱신하며 각 항목을 확인한다.

## 방법론 (먼저)
- [x] 요구사항 정의서를 읽고 이해했다 — `docs/specs/2026-07-08-employee-management-spec.md`
- [x] `docs/plans/`에 계획서 작성 (범위·파일·검증법) — `docs/plans/2026-07-08-employee-management-plan.md`
- [x] 승인받고 구현을 시작했다 — Plan Mode 승인 완료 (2026-07-08)
- [x] `ERP_<역할>` 브랜치에서 작업했다 — `main` 직접 커밋 금지 규칙에 따라 `ERP_initial_setup`부터 브랜치 사용
- [ ] 커밋을 의미 단위로 나눴다 — 각 브랜치 작업 중 계속 확인

## 기능 완성
- [x] 목록에 주요 필드 + 상태가 함께 보인다 (F-01) — 실제 DB로 검증 완료
- [x] 등록 validation 동작 (본인 ERD 규칙대로) (F-02) — 실제 DB로 검증 완료(사번 중복/필수값 누락/이메일 형식 오류 422 확인)
- [x] 상세·수정이 된다 (F-03) — 실제 DB로 검증 완료(404, 정보 수정, 자기 자신 관리자 지정 금지)
- [x] 재직·휴직·퇴직 변경 시 배지가 바뀐다 (F-04) — 실제 DB로 검증 완료(전이 사이클, RESIGNED 터미널, 잘못된 전이 409)
- [x] PostgreSQL에 실제로 저장된다 — WSL2 복구 후 `docker compose up` + `uvicorn` 실행, 한글 포함 정상 저장 확인(F-01~F-04 범위)

## 검증
- [x] 로컬에서 실행해 브라우저로 동작 확인 — F-01~F-05(검색/필터 포함) 범위까지. bonus(인사발령 이력)는 구현 후 재확인 필요
- [ ] 요구사항 정의서 항목과 대조
- [ ] 산출물 정리 — 결과화면 · AI 활용 · 만든 스킬

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
| `ERP_employment_history` | 인사발령 이력 bonus (선택) | 예정 |
| `feature/employee-login-auth` | 로그인 보호(스펙 범위 밖 별도 확장) — 세션 로그인, 등록/수정/상태변경만 보호, 조회는 그대로 공개 | 완료, 실제 DB/브라우저로 검증 완료 |

## 참고 — 스펙 범위 밖 별도 확장
- **로그인 기능**: `docs/specs/2026-07-08-employee-management-spec.md` §7은 "인증 없음"을 명시하고 있어 spec 문서 자체는 수정하지 않았다. 사용자 요청에 따라 별도 확장으로 세션 기반 로그인을 추가해 등록/수정/상태변경만 로그인 필수로 제한했다(계획서: `docs/plans/2026-07-12-employee-login-auth-plan.md`). 로컬 데모용 단일 계정(`admin` / `admin1234`, `.env`로 재정의 가능)이며 감사 컬럼 `_BY`는 기존과 동일하게 NULL로 유지한다.
- **사번/이메일/전화번호 형식 검증 강화**: `docs/specs/` §4는 `emp_no`를 "필수, 최대 20자, 고유", `phone`을 "선택, 최대 20자"로만 규정하고 패턴을 요구하지 않는다. 사용자 요청에 따라 `emp_no`는 `^[A-Z]\d{4}$`(예: `A0001`), `phone`은 하이픈 없는 숫자 9~11자리로 스펙보다 엄격하게 제한했다(`app/schemas/employee.py`). **주의**: 마감 제출물을 스펙 §4 기준으로만 평가할 경우, 이 형식과 다른 사번/전화번호 테스트 데이터는 422로 거부된다 — 스펙에 없는 제약이니 평가자에게 별도 확장임을 설명하거나 필요 시 완화 검토.
