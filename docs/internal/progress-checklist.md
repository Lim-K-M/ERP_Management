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
- [ ] 상세·수정이 된다 (F-03)
- [ ] 재직·휴직·퇴직 변경 시 배지가 바뀐다 (F-04)
- [x] PostgreSQL에 실제로 저장된다 — WSL2 복구 후 `docker compose up` + `uvicorn` 실행, 한글 포함 정상 저장 확인(F-01/F-02 범위)

## 검증
- [x] 로컬에서 실행해 브라우저로 동작 확인 — F-01/F-02(목록/등록) 범위까지. F-03~F-05/bonus는 구현 후 재확인 필요
- [ ] 요구사항 정의서 항목과 대조
- [ ] 산출물 정리 — 결과화면 · AI 활용 · 만든 스킬

## 참고 — 브랜치 현황
| 브랜치 | 내용 | 상태 |
|---|---|---|
| `ERP_initial_setup` | 초기 자료(규칙/스킬/DDL/docker-compose/spec/plan) | 완료, main 병합 |
| `ERP_project_scaffold` | FastAPI 프로젝트 골격 + DB 리플렉션 | 완료, main 병합. `/healthz` 실제 DB 리플렉션까지 검증 완료(WSL2 복구 후) |
| `ERP_skills_fastapi_jinja2` | 신규 스킬(fastapi-service-architecture, jinja2-ssr-frontend) | 완료, main 병합 |
| `ERP_employee_list_register` | F-01+F-02 (목록/등록) | 완료, 실제 DB로 검증 완료(TemplateResponse 버그 발견·수정 포함) |
| `ERP_employee_detail_status` | F-03+F-04 (상세/상태변경) | 예정 |
| `ERP_employee_search_filter` | F-05 검색/필터 (선택) | 예정 |
| `ERP_employment_history` | 인사발령 이력 bonus (선택) | 예정 |
