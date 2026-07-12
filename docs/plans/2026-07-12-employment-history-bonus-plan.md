# 인사발령 이력 + 목록 페이지네이션 (Bonus) 구현 계획

**Goal:** `docs/specs/2026-07-08-employee-management-spec.md` §3 Bonus — 인사 발령 이력(`T_EMPLOYMENT_HISTORY`) 기록·조회, 목록 페이지네이션을 구현한다. 기존 승인된 `docs/plans/2026-07-08-employee-management-plan.md` Task 7의 범위를 아래 두 가지로 확정·확장한다:
- CHANGE_TYPE 6종(HIRE/TRANSFER/PROMOTION/LEAVE/RETURN/RESIGN) 전부 기록 — 원 계획은 HIRE/LEAVE/RETURN/RESIGN만 언급했으나, 부서·직급 변경(TRANSFER/PROMOTION)도 기록하기로 사용자 확인 완료.
- 직원 목록에 페이지네이션 추가 — 원 계획엔 없었으나 spec §3이 bonus 항목으로 명시해 사용자 확인 후 포함.

**Architecture:** `t_employment_history`는 이미 `app/db/metadata.py`에 리플렉션 대상으로 등록되어 있어 추가 작업 불필요. 새 서비스(`employment_history_service`)가 이력 insert/조회를 전담하고, 기존 `employee_service`의 등록/수정/상태변경 함수가 각 케이스에 맞는 CHANGE_TYPE으로 이력을 남긴다(같은 트랜잭션, 커밋 전). 조회는 스펙상 인증 요구사항이 없어 로그인 여부와 무관하게 상세 페이지·API 양쪽에서 노출한다. 페이지네이션은 LIMIT/OFFSET 기반, 목록 페이지·JSON API 둘 다 `page`/`page_size` 쿼리 파라미터를 받는다(스펙 §5 API 표에 명시된 파라미터).

**Tech Stack:** 기존 스택 그대로(FastAPI, SQLAlchemy Core, Jinja2). 신규 의존성 없음.

---

## Task 1: 이력 스키마 + 서비스

**파일:**
- 생성: `app/schemas/employment_history.py` — `EmploymentHistoryRead`
- 생성: `app/services/employment_history_service.py` — `record_history()`, `list_history()`
- 수정: `app/core/constants.py` — `CHANGE_TYPE_LABEL` 딕셔너리 추가(HIRE=입사, TRANSFER=부서이동, PROMOTION=승진, LEAVE=휴직, RETURN=복직, RESIGN=퇴직)

`record_history(session, *, emp_id, change_type, dept_id=None, position_id=None, effective_date=None, remark=None)`은 `effective_date`가 없으면 `date.today()`를 사용해 insert만 하고 커밋은 호출자(employee_service)가 한다(같은 트랜잭션 유지).

`list_history(session, emp_id)`는 부서/직급명을 outer join해 `effective_date, history_id` 오름차순으로 반환한다.

**검증:** 단독으로는 호출부가 없으니 Task 2에서 함께 확인.

## Task 2: 등록/수정/상태변경에 이력 기록 연동

**파일:** `app/services/employee_service.py` 수정

- `create_employee`: insert 후 반환된 `emp_id`로 `record_history(..., change_type="HIRE", dept_id=payload.dept_id, position_id=payload.position_id, effective_date=payload.hire_date)` 호출 후 커밋.
- `update_employee`: 404 체크용으로 이미 호출하는 `get_employee`의 결과를 `before`로 보관. update 실행 후 `values`에 `dept_id`가 있고 `before["dept_id"]`와 다르면 `TRANSFER` 기록, `position_id`가 있고 달라졌으면 `PROMOTION` 기록(둘 다 바뀌면 두 건 모두 기록, 각각 변경 후 최종 dept_id/position_id 스냅샷 사용). 커밋은 기존처럼 마지막에 한 번.
- `change_status`: 성공적으로 update된 직후, `target_status`를 `{"LEAVE": "LEAVE", "ACTIVE": "RETURN", "RESIGNED": "RESIGN"}`로 매핑해 현재(변경 전) `dept_id`/`position_id`로 기록 후 커밋.

**검증:** 브라우저로 (1)신규 등록 → HIRE 이력 1건, (2)부서만 변경 → TRANSFER 1건, (3)직급만 변경 → PROMOTION 1건, (4)ACTIVE→LEAVE→ACTIVE→RESIGNED 순서로 상태변경 → LEAVE/RETURN/RESIGN 각 1건씩, DB에서 `select * from t_employment_history where emp_id=...`로 순서·타입 확인.

## Task 3: 이력 조회 API + 상세 화면 노출

**파일:**
- 생성: `app/routers/api_employment_history.py` — `GET /api/employees/{emp_id}/history` (스펙 §5), 404 처리
- 수정: `app/main.py` — 라우터 등록
- 수정: `app/routers/pages.py` — `employee_detail_page`에서 `employment_history_service.list_history` 호출해 컨텍스트에 `history` 추가
- 수정: `app/templating.py` — `change_type_label` Jinja 필터 추가(`app/core/constants.CHANGE_TYPE_LABEL` 사용)
- 수정: `app/templates/employees/detail.html` — "인사발령 이력" 표(발령구분/부서/직급/발령일/비고) 추가, 로그인 여부와 무관하게 항상 노출

**검증:** 로그인 없이 상세 페이지 접속해도 이력 표가 보이는지, `/docs`에서 `GET /api/employees/{id}/history` 호출 시 JSON 배열 확인.

## Task 4: 직원 목록 페이지네이션

**파일:**
- 수정: `app/services/employee_service.py` — 필터 적용 로직을 `_apply_filters()`로 추출해 `list_employees`/신규 `count_employees`가 공유, `list_employees`에 `page`/`page_size` 파라미터 추가(LIMIT/OFFSET)
- 수정: `app/routers/pages.py` — `employee_list_page`에 `page`(기본 1)/`page_size`(기본 20, 고정값) 쿼리 파라미터 추가, `count_employees`로 총 개수 계산 후 `total_pages` 산출·`page`를 유효 범위로 clamp, 이전/다음 페이지 링크 빌더(`_build_page_link`, 기존 `_build_sort_links`처럼 `page`를 제외한 현재 쿼리 유지) 추가. `_build_sort_links`는 정렬 변경 시 `page`를 결과 URL에서 제외해 1페이지로 리셋되게 한다.
- 수정: `app/routers/api_employees.py` — `GET /api/employees`에도 `page`/`page_size` 추가(스펙 §5 명시), 응답 형식(`list[EmployeeRead]`)은 유지하고 슬라이스만 적용
- 수정: `app/templates/employees/list.html` — 목록 하단에 페이지네이션(이전/다음 + "N / 총M페이지 (전체 K명)") 추가
- 수정: `app/static/css/style.css` — `.pagination` 스타일 추가

**검증:** 100명 이상의 테스트 데이터로 페이지 2, 3으로 이동 시 다른 직원이 보이는지, 필터/정렬 적용 후에도 페이지네이션이 정상 동작(필터링된 결과 기준 총 페이지 재계산)하는지, 마지막 페이지에서 "다음" 링크가 사라지는지 확인.

## Task 5: 종합 검증 + 문서 정리

- 브라우저로 전체 시나리오 재확인(Task 2~4 검증 항목 통합).
- `feature/employment-history` 브랜치에서 의미 단위 커밋 후 PR 생성.
- `docs/internal/progress-checklist.md`의 "bonus (선택)" 항목을 완료로 갱신.
