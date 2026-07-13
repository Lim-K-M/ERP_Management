# 요구사항 체크리스트 (최종)

> `docs/specs/2026-07-08-employee-management-spec.md` §1~§7 전 항목을 실제 서버(uvicorn)에 대한 curl/DB 조회, 브라우저 시나리오로 재검증한 최종 결과. 스펙 범위 밖 확장은 ⚠️로 표시하고 근거를 남긴다.

## 1. 데이터 모델 (§1)

| 항목 | 상태 |
|---|---|
| `T_DEPARTMENT`, `T_POSITION`, `T_EMPLOYEE`, `T_EMPLOYMENT_HISTORY` 4개 테이블 | ✅ `app/db/metadata.py`에 전부 리플렉션 |
| 감사 컬럼(`_ON`은 트리거로 채움, `_BY`는 NULL 유지) | ✅ |

## 2. 공통 상태 정의/전이 (§2)

| 항목 | 상태 |
|---|---|
| `ACTIVE`/`LEAVE`/`RESIGNED` 3개 상태, `RESIGNED`는 터미널 | ✅ `ALLOWED_TRANSITIONS` 단일 소스로 구현 |
| 허용되지 않는 전이 API 호출 시 409 | ✅ 실제 curl로 확인(`RESIGNED → ACTIVE` 시도 → 409) |

## 3. 기능 요구사항 (§3)

| ID | 요구사항 | 상태 |
|---|---|---|
| F-01 | 목록 조회(주요 필드 + 상태 배지) | ✅ |
| F-02 | 등록(검증 통과 시만 저장, 상태 서버 강제 `ACTIVE`) | ✅ 클라이언트가 `emp_status`를 조작해 보내도 서버가 무시하고 `ACTIVE`로 저장하는 것까지 확인 |
| F-03 | 상세 조회·수정 | ✅ (단, 로그인 확장으로 "수정"만 로그인 필요 — §7 별도 확장 참고) |
| F-04 | 상태 변경(허용 전이만, 위반 시 409) | ✅ |
| F-05 (선택) | 이름·부서·상태 검색/필터 | ✅ (직급·입사연도 필터로 확장 포함) |
| Bonus (선택) | 인사발령 이력 기록·조회 + 목록 페이지네이션 | ✅ CHANGE_TYPE 6종(HIRE/TRANSFER/PROMOTION/LEAVE/RETURN/RESIGN) 전부 기록, 20명/페이지 페이지네이션(구글 스타일 페이지 번호 네비게이션 포함) |

## 4. 필드 검증 규칙 (§4)

| 필드 | 스펙 요구사항 | 상태 |
|---|---|---|
| `emp_no` | 필수·최대 20자·고유 | ✅ (⚠️ 스펙 초과: 숫자 4자리 형식(`^\d{4}$`) 강제 — 별도 확장, 2026-07-13 `^A\d{4}$`에서 재변경) |
| `emp_name` | 필수·최대 100자 | ✅ |
| `email` | 선택·이메일 형식 | ✅ 커스텀 정규식으로 형식 오류 시 한글 에러 메시지 |
| `phone` | 선택·최대 20자 | ✅ (⚠️ 스펙 초과: 하이픈 없는 숫자 9~11자리 강제 — 별도 확장) |
| `hire_date` | 필수·날짜 | ✅ |
| `dept_id`/`position_id` | 지정 시 실존 확인 | ✅ 없으면 422 |
| `manager_id` | 실존 + 자기 자신 불가 | ✅ (순환 참조·퇴직자 지정 금지까지 추가 방어) |
| `emp_status` | 값 + 전이 규칙 준수 | ✅ |

## 5. API 스펙 (§5)

| 항목 | 상태 |
|---|---|
| `GET/POST /api/employees`, `GET/PATCH /api/employees/{id}`, `PATCH .../status` | ✅ |
| `GET /api/departments`, `GET /api/positions` | ✅ |
| `GET /api/employees/{id}/history` (bonus) | ✅ |
| 화면 라우트가 API와 동일한 서비스 로직 공유 | ✅ Router → Service 계층 분리로 보장 |

## 6. 화면 (§6)

목록 / 등록 폼 / 상세·수정 3개 화면 — ✅ 전부 구현, 스크린샷으로 캡처 완료(`docs/internal/screenshots/`)

## 7. 비기능 요구사항 (§7)

| 항목 | 스펙 | 상태 |
|---|---|---|
| 배포 안 함, 로컬 `uvicorn` 실행 | 요구됨 | ✅ |
| 인증 없음 | 요구됨 | ⚠️ **스펙 범위 밖 별도 확장으로 로그인 추가** — 등록/수정/상태변경만 보호, 조회(F-01/F-05/bonus)는 그대로 공개. 사용자 승인 하에 진행(계획서: `docs/plans/2026-07-12-employee-login-auth-plan.md`) |
| CSRF 미도입 트레이드오프 | "인증 없음" 전제 | ⚠️ 로그인 추가로 전제가 깨져 재검토했으나 토큰은 여전히 미도입(`SessionMiddleware`의 `SameSite=Lax` 기본값으로 크로스사이트 POST 위조를 일부 완화). 잔여 리스크로 기록 |

## 결론

스펙에 명시된 필수/선택 요구사항(F-01~F-05, bonus 포함)은 전부 충족했다. 스펙을 벗어난 부분은 3곳(⚠️ 로그인 추가, 사번/전화번호 형식 강화, CSRF 재검토)이며 전부 사용자 승인을 받고 아래 문서에 근거를 남겼다:

- `docs/internal/progress-checklist.md` — "스펙 범위 밖 별도 확장" 절, "잔여 리스크" 절
- `docs/plans/2026-07-12-employee-login-auth-plan.md`
- `docs/plans/2026-07-12-employment-history-bonus-plan.md`

평가 시 스펙 §4/§7 기준으로만 채점한다면 위 ⚠️ 3곳이 스펙과 다르게 동작한다는 점만 참고하면 된다.
