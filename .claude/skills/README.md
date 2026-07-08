# 스킬 가이드 — 프로젝트 아키텍처 표준

> 이 프로젝트의 `.claude/skills/`에는 도메인/절차 스킬이 있다. AI 코딩으로 **프론트 · 백엔드 · 인프라 · 협업**을 일관된 표준으로 만들기 위한 것이며, 서로 역할이 겹치지 않고 참조하는 구조다.
> "언제 어떤 스킬을 부르는가"만 명확하면 된다.

> **이 프로젝트 스택 (kist)**: Express SSR + 순수 HTML 조립 + Tailwind + **Oracle ORDS(REST 프록시)**, 순수 JS(ES Modules). 데이터는 ORDS가 소유하므로 **DB 객체를 직접 만들지 않는다**(PostgreSQL DB 스킬 없음). 백엔드/프론트 스킬 본문은 TS·모노레포 기준 범용 표준이며, 실제 매핑은 각 `SKILL.md` 상단 "이 프로젝트 매핑" 노트를 따른다.

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
  ① 백엔드 서비스          ② 프론트            ③ 데브옵스/운영
  backend-service-       frontend-ssr       docker-compose-
  architecture           (화면 조립 SSR)      server-ops
  (계층·API·골격·엔트리)    (렌더링·빌드)        (도커 스택 운영)
──────────────────────────────────────────────────────────────
협업 레이어 (SKILL · 여러 사람 작업을 합칠 때 켜짐)
  ④ code-review-standard   ← PR 리뷰 기준 (Git·PR·커밋 규약은 development-workflow가 담당)
──────────────────────────────────────────────────────────────
절차 레이어 (SKILL · 기획→구현 단계에서 켜짐)
  brainstorming(설계 구체화) · writing-plans(계획서 작성) · executing-plans(계획 실행)
```

핵심: 도메인 스킬은 **역할별 동급**이며, 만드는 대상에 따라 켜진다. 영역이 겹치는 부분은 "주인"을 정해 서로 참조한다 — **백엔드 계층·프로젝트 골격·엔트리(`server/server.js`)는 ①**, **SSR 화면 렌더링·빌드는 ②**, 도커 배포·운영은 ③. 협업 시 PR 리뷰는 ④가 기준이고, 개발 프로세스·Git 규약은 always-on **규칙**이다.

> 데이터는 **Oracle ORDS를 서버에서 REST 프록시**한다([`../../server/lib/axios-config.js`](../../server/lib/axios-config.js)). PostgreSQL 등 DB 객체를 직접 설계하지 않으므로 DB 도메인 스킬은 두지 않는다.

---

## 폴더 구조

```
.claude/skills/
├── README.md                                  ← 이 문서 (스킬 사용 안내)
├── backend-service-architecture/              ← ① 백엔드 서비스 + 프로젝트 골격
│   └── SKILL.md
├── frontend-ssr/                               ← ② 프론트: SSR 렌더링/빌드
│   └── SKILL.md
├── docker-compose-server-ops/                  ← ③ 데브옵스: 도커 운영
│   ├── SKILL.md
│   └── references/                             ← 6개 상세 레퍼런스
│       ├── architecture.md
│       ├── logging.md
│       ├── database-and-backup.md
│       ├── automation.md
│       ├── operations.md
│       └── troubleshooting.md
├── code-review-standard/                       ← ④ 협업: PR 리뷰 기준
│   └── SKILL.md
├── brainstorming/                              ← 절차: 아이디어 → 설계 구체화
├── writing-plans/                              ← 절차: 구현 계획서 작성
└── executing-plans/                            ← 절차: 계획서 실행
```

각 스킬은 `SKILL.md`(진입점)를 갖고, 상세 규칙이 많은 스킬은 `references/`로 분리해 둔다.

---

## 1. `backend-service-architecture` (① 백엔드 서비스)
**Node.js/Express 백엔드 서비스의 표준 아키텍처**

- **아키텍처**: Router/Controller/Service 계층 분리, 표준 JSON Envelope 응답, 전역 에러 핸들링, 멱등성
- **보안**: 환경변수 Fail-Fast 검증(Zod), Helmet/CORS/Rate-Limit, 하드코딩 배제
- **로깅**: `console.log` 금지, `winston`+`morgan`, 로그 순환(30일)/KST/헬스체크 스킵, Slow Request 모니터링
- **성능**: 설정값 캐싱, 외부 API 타임아웃 강제
- **런타임/배포**: Graceful Shutdown, 슈퍼바이저 하나만(PM2 vs Docker 상호배타), 단위 테스트, CI/CD. **도커/Compose 배포 구체 표준은 ③ `docker-compose-server-ops`로 위임**
- **이 프로젝트 매핑**: TS·`services/server` 기준 본문 → 순수 JS·`server/server.js`·Oracle ORDS 프록시. 데이터는 ORDS 소유라 DB 객체/감사 컬럼 표준은 비해당. 상세는 `SKILL.md` 상단 노트.

## 2. `frontend-ssr` (② 프론트)
**순수 Vanilla HTML 파편을 조립하는 SSR 렌더링 레이어** (프로젝트 골격·엔트리는 ①이 주인)

- React/Vue/EJS 같은 프레임워크·템플릿 엔진 배제, **순수 Vanilla HTML/CSS(Tailwind)** 사용
- HTML Fragment(`head/header/sidebar/footer/base`)를 `fs.readFileSync`로 읽어 캐싱 후 Slot 치환
- `escapeHtml`로 동적 출력 XSS 차단
- **독립 프로덕션 빌드**: 개발 시 원본 참조, 배포 시 `dist/`로 복사(`build.mjs`, `NODE_ENV` 분기)
- **이 프로젝트 매핑**: 본문 `services/web/{layouts,pages}`→실제 `client/{components,pages,styles}`+`public/`, `ssrRenderer.ts`→`server/server.js` 조립 로직, `escapeHtml.ts`→`server/utils/escapeHtml.js`. 상세는 `SKILL.md` 상단 노트.

## 3. `docker-compose-server-ops` (③ 데브옵스/운영)
**Docker Compose 단일 스택으로 서버를 구축·운영하는 데브옵스 표준** (검증 예시: 산업용 AI 서버 — 산업 AI 구성은 예시이며 프로젝트에 맞게 치환)

- **올-도커 철학**: 여러 PC가 동일 이미지 사용 → 환경 동일화. `:latest` 금지, 태그 핀 권장
- **시작 순서**: `depends_on` + healthcheck
- **로그/백업**: 파일 30일 + Docker 드라이버 캡
- **오버레이**: `docker-compose.yml` + `override`(개발) + `prod`(현장), profile 토글
- **신규 프로젝트 시작점**: `references/architecture.md` **§0 프로젝트 환경 프로파일** 표부터 채운다 (환경 종속값이 거기에 모여 있음)
- 6개 레퍼런스: `architecture` / `logging` / `database-and-backup` / `automation` / `operations` / `troubleshooting`

## 4. `code-review-standard` (④ 협업)
**PR/diff 리뷰 시 따르는 공통 코드리뷰 표준** — 여러 사람이 각자 AI로 일해도 머지 품질을 일정하게 유지.

- **체크리스트**: 프로세스 정합성(승인 계획 대비 스코프) → 정확성 → 보안 → **도메인 스킬 컨벤션 준수(①~③)** → 테스트 → 품질
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
- **부르는 스킬**: `backend-service-architecture`(골격·엔트리) + `frontend-ssr`(SSR 화면을 붙일 때)
- **트리거 예시**: *"신규 Express 프로젝트 표준대로 셋업해줘"*, *"SSR 조립기 방식으로 프론트 붙여줘"*
- **하는 일**: ①이 `server/` 계층 골격(Router/Controller/Service)·엔트리 미들웨어 순서·환경변수 Fail-Fast·로거를 세움 → 그 위에 ②가 `client/` + 조립 로직을 얹음

### 2단계 — 데이터 연동 (Oracle ORDS)
- **부르는 스킬**: `backend-service-architecture` (데이터 접근부)
- **트리거 예시**: *"서비스 목록 ORDS API 연동해줘"*
- **하는 일**: `server/lib/axios-config.js`의 ORDS 프록시 인스턴스를 통해 호출, Bearer 토큰은 서버 보관(브라우저 노출 금지), 외부 호출 타임아웃 강제
- **주의**: DB 스키마는 ORDS 쪽이 소유. 이 레포에서 테이블/함수를 직접 만들지 않는다.

### 3단계 — 백엔드 로직
- **부르는 스킬**: `backend-service-architecture`
- **트리거 예시**: *"주문 생성 API 만들어줘"*
- **하는 일**: Controller는 검증만, Service에 순수 로직, JSON Envelope 응답, 전역 에러 핸들링, winston 로깅, 외부 호출 타임아웃

### 4단계 — 프론트(화면)
- **부르는 스킬**: `frontend-ssr`
- **트리거 예시**: *"주문 목록 페이지 추가해줘"*
- **하는 일**: `client/pages`에 HTML 파편 추가 → `server/server.js`가 조립, 동적 데이터는 `escapeHtml` 거쳐 주입

### 5단계 — 배포/운영
- **부르는 스킬**: `docker-compose-server-ops`
- **트리거 예시**: *"이 프로젝트 도커 스택으로 배포 구성해줘"*, *"메인PC/미니PC 동일하게 맞춰줘"*
- **하는 일**: compose 단일 스택, 이미지 태그 핀, `depends_on`+healthcheck 시작순서, 로그 30일+드라이버 캡. **먼저 `architecture.md §0` 프로파일 표를 채운다.**

### 6단계 — 리뷰/머지 (협업)
- **부르는 스킬**: `code-review-standard`
- **트리거 예시**: *"이 PR 리뷰해줘"*, *"머지 전에 봐줘"*
- **하는 일**: 체크리스트로 1차 리뷰(스코프·정확성·보안·컨벤션·테스트) → 등급(🔴/🟡/🟢) 부여 → 사람 확인. Git·커밋·PR 형식은 `development-workflow` 규약을 따름

---

## 충돌 지점 정리 (헷갈리기 쉬운 부분)

| 주제 | 어느 스킬이 "주인"인가 |
|---|---|
| 프로세스 관리 (PM2 vs Docker) | 올-도커면 **`docker-compose-server-ops`** 우선 (`backend-service-architecture`의 PM2 옵션은 비-컨테이너 전용) |
| 로그 30일 정책 | 앱 레벨은 `backend-service-architecture`, 컨테이너 stdout 캡은 `docker-compose-server-ops` |
| **프로젝트 골격·엔트리(`server/server.js`)·미들웨어 순서** | `backend-service-architecture` (①) — 단일 주인. ②는 정적 서빙·조립만 기여 |
| **SSR 화면 렌더링·`client/`·빌드** | `frontend-ssr` (②). 서버 내부 계층·엔트리는 ①에 위임 |
| PR 리뷰 "무엇을 보나" vs Git·PR "형식" | 리뷰 기준 = `code-review-standard` / 브랜치·커밋·PR 규약 = `development-workflow` |

---

## 부록: 환경 종속값은 한 곳에

`docker-compose-server-ops`는 산업용 AI 서버 운영에서 검증된 구조라, 호스트/IP/포트/GPU 같은 **환경 종속값은 모두 `architecture.md §0 프로젝트 환경 프로파일` 표 한 곳에 격리**돼 있다. 표의 구체값은 "참고(검증 예시)"로만 표기 — 기본값이 아니므로 그대로 베끼지 말 것. 새 프로젝트는 §0 표만 채우고 본문의 `<project>`·`<user>`·`<gpu>` 토큰을 치환하면 된다.
