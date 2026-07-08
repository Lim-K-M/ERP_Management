---
name: backend-service-architecture
description: "Node.js/Express 백엔드 서비스의 표준 아키텍처 — 프로젝트 골격·app.ts, 계층 구조, API 응답 규격, 에러/멱등성, 보안, 로깅, 성능, 런타임. 백엔드 코드 작성/리뷰 및 신규 Express 프로젝트 셋업 시 적용."
---
# 백엔드 서비스 아키텍처 표준 (Node.js/Express)

모든 Node.js/Express 백엔드 서비스에 적용하는 아키텍처 표준.

> **⚠️ 이 프로젝트 매핑 (kist)** — 아래 본문은 TypeScript·`services/server` 모노레포 기준의 범용 표준이다. 이 프로젝트의 실제 스택으로 읽는다:
> | 범용 표준(본문) | 이 프로젝트 실제 |
> |---|---|
> | TypeScript (`app.ts`, `tsconfig`, `dist/`) | 순수 JS, ES Modules — 엔트리 `server/server.js` |
> | 계층 `server/src/{routes,controllers,services}` | `server/{routes,controllers,services,middlewares,lib,utils,config}` (이미 계층 분리됨) |
> | 데이터 접근 = Prisma/PostgreSQL | **Oracle ORDS REST 프록시** (`server/lib/axios-config.js`의 axios 인스턴스). DB 객체를 직접 만들지 않음 |
> | 감사 컬럼(§1) 등 DB 표준 | ORDS가 데이터 소유 → 이 프로젝트엔 비해당. **응답 규격·에러·보안·로깅·성능·런타임 원칙은 그대로 적용** |
> 계층 분리·JSON Envelope·전역 에러·환경변수 Fail-Fast·winston 로깅·외부 호출 타임아웃은 언어 무관하게 적용한다.

## 경계 (담당 / 위임)
- **담당**: 프로젝트 골격·엔트리(`server/server.js`) 미들웨어 순서, 계층 구조(Router/Controller/Service), API 응답 규격, 전역 에러·멱등성, 보안·로깅·성능·런타임.
- **위임**: SSR 화면 렌더링·`client/`·빌드 → `frontend-ssr` / 도커·Compose 배포·운영 → `docker-compose-server-ops`. (이 프로젝트는 PostgreSQL을 직접 만들지 않으므로 DB 스킬 위임 없음 — 데이터는 Oracle ORDS 프록시)

## 0. 프로젝트 골격
**모노레포**: `services/server`(Node+Express+TS) + `services/web`(프론트). 서버 골격과 `app.ts`의 주인은 이 스킬이다.
- `server/src`: `routes/` · `controllers/` · `services/` + `lib/` · `utils/` · `config/`. (`routes/`만 두는 골격 금지)
- 의존성은 백엔드 집중(`express`, `typescript`, `ts-node`, `nodemon`, `zod`). `web/`는 복사 빌더만.
- `tsconfig`: `outDir: "./dist"`, `rootDir: "./src"`.

**표준 `app.ts` 미들웨어 순서** (여러 스킬이 같은 파일에 기여해도 흔들리지 않게):
1. 환경변수 Fail-Fast 검증(Zod, §2)
2. 보안 미들웨어(helmet/cors/rate-limit, §2)
3. 바디 파서 + 액세스 로깅(morgan, §3)
4. 정적 서빙 — SSR이면 `frontend-ssr`의 `NODE_ENV` 분기를 여기에 끼움
5. 라우터(페이지 + API)
6. 전역 에러 핸들러(§1) — 가장 마지막

## 1. 아키텍처
**계층 분리**
- Router: 경로 ↔ Controller 매핑만.
- Controller: HTTP 입출력 + 입력 검증(Zod)만. 비즈니스 로직 금지.
- Service: 프레임워크 비종속 순수 로직(단위 테스트 용이).
- 데이터 접근: **이 프로젝트는 Oracle ORDS REST 프록시**(`server/lib/axios-config.js`)를 Service에서 호출한다. (범용 표준: ORM이면 Service에서 직접 호출, Raw SQL이면 Repository 계층으로 격리)

**API 응답 규격** — 표준 JSON Envelope로 통일:
```json
{ "success": true, "data": { "id": 1, "name": "example" }, "message": "처리되었습니다." }
```

**전역 에러·멱등성** — try-catch → `next(err)` → 전역 핸들러에서 500 포맷 통일. 중복/유니크 충돌은 죽지 않고 기존 데이터 반환 또는 무시.

**감사 컬럼(범용 표준 — 이 프로젝트는 ORDS가 데이터 소유라 비해당)** — DB를 직접 소유하는 프로젝트에서는 모든 테이블에 아래 4개를 둔다.

| 컬럼 | 타입 | 의미 | 설정 |
|------|------|------|------|
| `CREATED_ON` | `TIMESTAMPTZ` | 생성 시각 | `DEFAULT NOW()` |
| `CREATED_BY` | `BIGINT` | 생성 주체(`T_USER.USER_ID`) | 앱 주입 |
| `UPDATED_ON` | `TIMESTAMPTZ` | 수정 시각 | 트리거 갱신 |
| `UPDATED_BY` | `BIGINT` | 수정 주체(`T_USER.USER_ID`) | 앱 주입 |

- `_ON`은 트리거, `_BY`는 앱 서비스가 인증 컨텍스트(JWT 사용자 ID)로 주입. 시스템 작업은 시스템 계정 ID 또는 `NULL`.
- 로그/시계열 등 append-only 테이블도 일관성을 위해 4컬럼을 유지한다.

## 2. 보안
- **환경변수 Fail-Fast**: 기동 지점(`app.ts`/`config.ts`)에서 Zod로 필수 값·타입을 가장 먼저 검증, 실패 시 즉시 중단.
- **Helmet / CORS / Rate-Limit**: 보안 헤더·명시적 CORS·로그인/공개 API 속도 제한.
- **하드코딩 금지**: 의미 불명 ID·토큰·만료시간은 `.env` 또는 설정 테이블로 분리.

## 3. 로깅
- `console.log`/`console.error` 금지. `winston` + `morgan`.
- 로그 순환(30일) / KST 타임존 / 헬스체크 스킵 / Slow Request(예: 2초 초과 시 `[WARN] SLOW`).
- 주의: morgan 액세스 로그를 `logger.http()`로 흘리면 winston 레벨이 그보다 낮을 때(기본 `info`) 파일에 안 남는다(레벨 우선순위 `error<warn<info<http<debug`). 보존하려면 `LOG_LEVEL=http` 이상으로 올리거나 morgan 브리지를 `logger.info()`로. 운영 정책에 맞춰 의도적으로 선택한다.

## 4. 성능
- 변경 빈도 낮은 설정/정적 데이터는 메모리 변수 또는 Redis에 캐싱하고 수정 API 호출 시에만 무효화.
- 외부 API 호출은 `AbortSignal.timeout()` 또는 `axios.timeout`으로 3~5초 타임아웃 강제.

## 5. 런타임
- **Graceful Shutdown**: `SIGTERM`/`SIGINT` 시 진행 중 요청을 대기하고 DB 커넥션을 정리한 뒤 종료.
- **슈퍼바이저 하나만** (PM2 vs Docker 상호배타): 베어메탈/단일 호스트 = PM2(`ecosystem.config.js`); 컨테이너 = Docker가 슈퍼바이저, **컨테이너 안에서 PM2 금지**(SIGTERM·헬스체크 이중 감독 충돌), `CMD ["node", "dist/server.js"]`. 도커/Compose 운영 구체 표준은 `docker-compose-server-ops`.
- **단위 테스트**: 결제·권한·물리 제어 등 크리티컬 로직은 필수.
- **CI/CD**: Push/PR 시 Lint·타입 검사·테스트 자동화.
