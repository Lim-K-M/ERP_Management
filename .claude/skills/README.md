# 스킬 가이드 — 프로젝트 아키텍처 표준

> 이 프로젝트의 `.claude/skills/`에는 도메인/절차 스킬이 있다. AI 코딩으로 **프론트 · 백엔드 · 인프라 · 협업**을 일관된 표준으로 만들기 위한 것이며, 서로 역할이 겹치지 않고 참조하는 구조다.
> "언제 어떤 스킬을 부르는가"만 명확하면 된다.

> **이 프로젝트 스택 (ERP_Management)**: FastAPI + SQLAlchemy Core(리플렉션) + Jinja2 SSR + PostgreSQL(Docker Compose). `ddl/`의 기존 스키마가 SSOT이며 앱은 `MetaData().reflect()`로 **읽기만** 한다(마이그레이션/`create_all` 없음). 아래 도메인 스킬(①②)은 다른 프로젝트에서 가져온 범용 템플릿이 아니라 **이 프로젝트 전용으로 작성**됐다.

---

## 먼저: 규칙(always-on) vs 스킬(트리거)

두 가지를 구분한다. **개발 워크플로우 자체는 스킬이 아니라 규칙**이다.

| | **규칙** (`CLAUDE.md` / `.claude/rules/`) | **스킬** (`.claude/skills/`) |
|---|---|---|
| 로드 시점 | **항상** (매 세션, 모든 작업) | **트리거될 때만** (설명 매칭 / `/호출`) |
| 성격 | 늘 지켜야 할 **제약·가드레일** | 특정 작업의 **절차·능력** |
| 예시 | "승인 전 코드 금지", "main 직접 커밋 금지" | "SSR 화면은 이렇게 조립해라" |

- **개발 프로세스(플랜-퍼스트 7단계 + 금지사항)** 는 모든 작업에 항상 적용돼야 하므로 **규칙**으로 둔다 → [`../../CLAUDE.md`](../../CLAUDE.md) + [`../rules/development-workflow.md`](../rules/development-workflow.md)(always-on). 사람용 정본은 [`../../docs/guides/development-process.md`](../../docs/guides/development-process.md).
- **도메인·절차 표준**(아래 스킬들)은 해당 작업을 할 때만 끌어다 쓰는 **스킬**이다.

---

## 전체 그림: 역할별 도메인 스킬

```
프로세스 레이어 (RULE · 항상 켜짐)
        development-workflow   ← "어떻게 일하나" (플랜-퍼스트 + Git·PR·커밋 규약)
══════════════════════════════════════════════════════════════
도메인 레이어 (SKILL · 만드는 대상에 따라 켜짐)
  ① 백엔드 서비스          ② 프론트             ③ 데이터        ④ 데브옵스/운영
  fastapi-service-       jinja2-ssr-        db-development-  docker-compose-
  architecture           frontend           postgres          server-ops
  (계층·API·골격·엔트리)    (템플릿 렌더링)       (DB 객체 설계)     (도커 스택 운영)
──────────────────────────────────────────────────────────────
협업 레이어 (SKILL · 여러 사람 작업을 합칠 때 켜짐)
  ⑤ code-review-standard   ← PR 리뷰 기준 (Git·PR·커밋 규약은 development-workflow가 담당)
──────────────────────────────────────────────────────────────
절차 레이어 (SKILL · 기획→구현 단계에서 켜짐)
  brainstorming(설계 구체화) · writing-plans(계획서 작성) · executing-plans(계획 실행)
```

핵심: 도메인 스킬은 **역할별 동급**이며, 만드는 대상에 따라 켜진다. 영역이 겹치는 부분은 "주인"을 정해 서로 참조한다 — **백엔드 계층·프로젝트 골격·엔트리(`app/main.py`)는 ①**, **Jinja2 템플릿 렌더링은 ②**, **새 DB 객체(테이블/함수/트리거) 설계는 ③**, 도커 배포·운영은 ④. 협업 시 PR 리뷰는 ⑤가 기준이고, 개발 프로세스·Git 규약은 always-on **규칙**이다.

> `ddl/`이 스키마의 SSOT이고 앱은 `MetaData().reflect()`로 읽기만 한다([`../../app/db/metadata.py`](../../app/db/metadata.py)). 새 테이블/함수를 설계할 때만 ③이 켜진다 — 앱이 스키마를 직접 만들지 않는다.

---

## 폴더 구조

```
.claude/skills/
├── README.md                                  ← 이 문서 (스킬 사용 안내)
├── fastapi-service-architecture/              ← ① 백엔드 서비스 + 프로젝트 골격
│   └── SKILL.md
├── jinja2-ssr-frontend/                        ← ② 프론트: Jinja2 템플릿 렌더링
│   └── SKILL.md
├── db-development-postgres/                    ← ③ 데이터: PostgreSQL DB 객체 설계
│   ├── SKILL.md
│   └── docs/DB_ARCHITECTURE_GUIDE.md
├── docker-compose-server-ops/                  ← ④ 데브옵스: 도커 운영
│   ├── SKILL.md
│   └── references/                             ← 6개 상세 레퍼런스
│       ├── architecture.md
│       ├── logging.md
│       ├── database-and-backup.md
│       ├── automation.md
│       ├── operations.md
│       └── troubleshooting.md
├── code-review-standard/                       ← ⑤ 협업: PR 리뷰 기준
│   └── SKILL.md
├── brainstorming/                              ← 절차: 아이디어 → 설계 구체화
├── writing-plans/                              ← 절차: 구현 계획서 작성
├── executing-plans/                            ← 절차: 계획서 실행
├── backend-service-architecture/               ← (미사용) 다른 프로젝트(Node.js/Express·Oracle ORDS)용 템플릿, 참고용으로만 보존
└── frontend-ssr/                                ← (미사용) 다른 프로젝트(Vanilla HTML SSR)용 템플릿, 참고용으로만 보존
```

각 스킬은 `SKILL.md`(진입점)를 갖고, 상세 규칙이 많은 스킬은 `references/`로 분리해 둔다.

---

## 1. `fastapi-service-architecture` (① 백엔드 서비스)
**FastAPI + SQLAlchemy Core 리플렉션 기반 백엔드 서비스 아키텍처** (이 프로젝트 전용)

- **골격**: `app/{main.py,config.py,db/,schemas/,services/,routers/,templates/}` — DB 리플렉션은 `lifespan`에서 1회 실행
- **계층**: Router(HTML/JSON, 파싱만) → Service(순수 로직, FastAPI 비의존) → 리플렉션된 Table. Controller 계층 없음, 화면 라우터와 API 라우터가 같은 Service 함수를 공유
- **검증**: Pydantic 필드/validator로 스펙 §4 규칙을 그대로 옮김. 스펙에 없는 검증(정규식 강화 등)은 사용자 승인 후에만 예외적으로 추가
- **상태 전이**: `ALLOWED_TRANSITIONS` 단일 상수 + 순수 예외(`InvalidTransitionError`) → Router에서 409로 변환
- **에러 응답**: `HTTPException`으로 통일(422/404/409/500), DB `IntegrityError`는 Service에서 사용자 친화적 메시지로 변환
- **위임**: 화면 렌더링은 ② `jinja2-ssr-frontend`, 새 DB 객체 설계는 ③ `db-development-postgres`, 도커 배포는 ④ `docker-compose-server-ops`

## 2. `jinja2-ssr-frontend` (② 프론트)
**Jinja2 서버사이드 렌더링 화면 레이어** (이 프로젝트 전용, 프로젝트 골격·엔트리는 ①이 주인)

- **템플릿 상속**: `base.html`의 `{% block title/content %}`를 하위 템플릿이 채움, 등록/수정처럼 구조가 같은 화면은 `_form.html`을 `{% include %}`로 재사용
- **PRG 패턴**: 폼 제출 성공 시 303 리다이렉트, 실패 시 같은 폼을 에러와 함께 재렌더링(입력값 유지)
- **상태 배지**: 커스텀 Jinja 필터(`status_badge`)로 렌더링, 고정값에만 `Markup` 예외 허용
- **autoescape/CSRF**: autoescape는 항상 켜둔다. CSRF 트레이드오프는 "인증 없음" 전제일 때만 성립 — 로그인 기능이 추가되면 반드시 재검토
- **위임**: 라우터의 실제 요청 처리·Service 호출·Pydantic 검증은 ① `fastapi-service-architecture`

## 3. `db-development-postgres` (③ 데이터)
**PostgreSQL DB 객체(테이블·뷰·함수·트리거) 생성/수정 시 따르는 네이밍·설계 표준**

- **네이밍**: 테이블 `T_`, 함수 `F_`, 트리거 `_TRG`, 인덱스 `IDX_`, 제약조건 `PK_`/`FK_`/`UNQ_`/`CK_`
- **공통 컬럼**: 모든 테이블에 `CREATED_ON/BY`, `UPDATED_ON/BY` 4종 + `F_AUDIT_LOG()` 감사 트리거
- **ORM 연동**: SQL이 SSOT → 앱은 `MetaData().reflect()`로 읽기만 함(마이그레이션 금지). Repository 계층 없이 Service가 리플렉션된 Table을 직접 쿼리
- **적용 시점**: `ddl/`에 새 테이블/함수/트리거를 추가하거나 기존 것을 바꿀 때만 켜진다 — 이 프로젝트는 대부분 `ddl/`이 이미 확정돼 있어 자주 켜지지 않음

## 4. `docker-compose-server-ops` (④ 데브옵스/운영)
**Docker Compose 단일 스택으로 서버를 구축·운영하는 데브옵스 표준** (검증 예시: 산업용 AI 서버 — 산업 AI 구성은 예시이며 프로젝트에 맞게 치환)

- **올-도커 철학**: 여러 PC가 동일 이미지 사용 → 환경 동일화. `:latest` 금지, 태그 핀 권장
- **시작 순서**: `depends_on` + healthcheck
- **로그/백업**: 파일 30일 + Docker 드라이버 캡
- **오버레이**: `docker-compose.yml` + `override`(개발) + `prod`(현장), profile 토글
- **신규 프로젝트 시작점**: `references/architecture.md` **§0 프로젝트 환경 프로파일** 표부터 채운다 (환경 종속값이 거기에 모여 있음)
- 6개 레퍼런스: `architecture` / `logging` / `database-and-backup` / `automation` / `operations` / `troubleshooting`
- **이 프로젝트 적용 범위**: 스펙 §7에 따라 배포는 하지 않음 — `docker-compose.yml`은 로컬 PostgreSQL/pgAdmin 실행에만 사용, 위 배포 표준 대부분은 비해당

## 5. `code-review-standard` (⑤ 협업)
**PR/diff 리뷰 시 따르는 공통 코드리뷰 표준** — 여러 사람이 각자 AI로 일해도 머지 품질을 일정하게 유지.

- **체크리스트**: 프로세스 정합성(승인 계획 대비 스코프) → 정확성 → 보안 → **도메인 스킬 컨벤션 준수(①~④)** → 테스트 → 품질
- **심각도 등급**: 🔴 Blocker(머지 차단) / 🟡 Should / 🟢 Nit
- **AI 1차 리뷰 → 사람 확인** 흐름. 빌트인 `/code-review`도 이 기준에 맞춘다
- Git·브랜치·커밋·PR **형식**은 `development-workflow`(규칙)가 담당 — 이 스킬은 "무엇을 보나"에 집중

## 절차 스킬 (기획 → 구현)
- **`brainstorming`**: 아이디어 단계에서 요구사항·설계를 구체화. 기능을 만들기 전에 부른다.
- **`writing-plans`**: 구현 계획서를 작성한다(7단계 ② 단계). 계획서는 `docs/plans/YYYY-MM-DD-<주제>.md`.
- **`executing-plans`**: 승인된 계획서를 단계별 체크포인트로 실행한다(7단계 ⑤ 단계).

---

## 단계별 사용 가이드 (프로젝트 생애주기 순)

### 1단계 — 프로젝트 골격 잡기
- **부르는 스킬**: `fastapi-service-architecture`(골격·엔트리) + `jinja2-ssr-frontend`(화면을 붙일 때)
- **트리거 예시**: *"FastAPI 프로젝트 골격 세팅해줘"*, *"Jinja2로 화면 붙여줘"*
- **하는 일**: ①이 `app/` 계층 골격(Router/Service)·`lifespan` DB 리플렉션·`config.py`를 세움 → 그 위에 ②가 `templates/` + 렌더링 로직을 얹음

### 2단계 — 데이터 연동 (DB 리플렉션)
- **부르는 스킬**: `fastapi-service-architecture` (DB 리플렉션 패턴)
- **트리거 예시**: *"직원 목록 조회 API 연동해줘"*
- **하는 일**: `app/db/metadata.py`의 리플렉션된 `Table` 객체로 Service에서 쿼리 조립
- **주의**: DB 스키마는 `ddl/`이 SSOT. 이 레포(앱 코드)에서 테이블/함수를 직접 만들지 않는다. 새 테이블/함수가 필요하면 ③ `db-development-postgres`로 `ddl/`에 먼저 추가한다.

### 3단계 — 백엔드 로직
- **부르는 스킬**: `fastapi-service-architecture`
- **트리거 예시**: *"직원 등록 API 만들어줘"*
- **하는 일**: Router는 파싱만, Service에 순수 로직(검증·상태 전이), `HTTPException`으로 통일된 에러 응답

### 4단계 — 프론트(화면)
- **부르는 스킬**: `jinja2-ssr-frontend`
- **트리거 예시**: *"직원 상세 페이지 추가해줘"*
- **하는 일**: `app/templates/`에 화면 추가(`{% extends "base.html" %}`) → PRG 패턴으로 폼 제출 처리, 동적 데이터는 autoescape로 보호

### 5단계 — 배포/운영 (이 프로젝트는 로컬 DB 실행에만 해당)
- **부르는 스킬**: `docker-compose-server-ops`
- **트리거 예시**: *"docker-compose에 새 서비스 추가해줘"*
- **하는 일**: `docker-compose.yml`로 PostgreSQL/pgAdmin 실행. 스펙 §7에 따라 실제 배포는 하지 않으므로, 이 스킬의 배포/운영 표준 대부분은 이 프로젝트엔 비해당

### 6단계 — 리뷰/머지 (협업)
- **부르는 스킬**: `code-review-standard`
- **트리거 예시**: *"이 PR 리뷰해줘"*, *"머지 전에 봐줘"*
- **하는 일**: 체크리스트로 1차 리뷰(스코프·정확성·보안·컨벤션·테스트) → 등급(🔴/🟡/🟢) 부여 → 사람 확인. Git·커밋·PR 형식은 `development-workflow` 규약을 따름

---

## 충돌 지점 정리 (헷갈리기 쉬운 부분)

| 주제 | 어느 스킬이 "주인"인가 |
|---|---|
| **프로젝트 골격·엔트리(`app/main.py`)·Router/Service 계층** | `fastapi-service-architecture` (①) — 단일 주인. ②는 템플릿 렌더링만 기여 |
| **Jinja2 화면 렌더링·`app/templates/`·PRG** | `jinja2-ssr-frontend` (②). 라우터의 실제 처리·Service 호출은 ①에 위임 |
| 새 DB 객체(테이블/함수/트리거) 설계 | `db-development-postgres` (③). 앱이 그 객체를 어떻게 리플렉션·쿼리하는지는 ① |
| PR 리뷰 "무엇을 보나" vs Git·PR "형식" | 리뷰 기준 = `code-review-standard` / 브랜치·커밋·PR 규약 = `development-workflow` |

---

## 부록: 다른 프로젝트용 미사용 스킬

`backend-service-architecture`(Node.js/Express)·`frontend-ssr`(Vanilla HTML SSR)는 이 프로젝트가 시작되기 전 다른 프로젝트("kist")에서 검증된 템플릿이며, 이 프로젝트의 실제 스택(FastAPI/Jinja2)과 맞지 않아 **그대로 두고 대체용으로 ①②를 새로 작성**했다. 두 파일은 초기 커밋 이후 수정된 적이 없고, 이 문서를 포함한 어떤 라우팅 문서에서도 더 이상 참조하지 않는다. 삭제하지 않은 이유는 향후 실제로 Node.js/Express 프로젝트를 다룰 일이 생기면 참고용으로 쓸 수 있기 때문 — 이 프로젝트 작업에는 관여하지 않는다.
