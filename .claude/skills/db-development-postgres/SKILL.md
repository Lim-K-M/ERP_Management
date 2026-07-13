---
name: db-development-postgres
description: "PostgreSQL DB 객체(테이블·뷰·함수·프로시저) 생성/수정 시 따르는 네이밍·쿼리·설계 표준. 테이블/함수/트리거 작성, 스키마 변경, ORM(SQLAlchemy Core 리플렉션/Prisma) 연동 시 적용."
---
# DB 개발 표준 (PostgreSQL)

새 DB 객체를 만들거나 기존 객체를 수정할 때 이 규칙을 반드시 준수한다.

## 경계 (담당 / 위임)
- **담당**: DB 객체 네이밍, 쿼리 스타일, 공통 감사 컬럼, UUID, 감사 트리거, Prisma(SQL=SSOT) 연동.
- **위임**: 감사 컬럼 "필수" 선언과 작성자(`_BY`) 값 주입·서비스 호출 흐름은 `fastapi-service-architecture`. 단, 감사 컬럼의 **타입·트리거 표준은 여기가 주인**.

## 핵심 규칙

### 네이밍
- 테이블 `T_`, 뷰 `VW_`, 함수 `F_`, 프로시저 `PR_`, 트리거 테이블명+`_TRG`, 인덱스 `IDX_`, 제약조건 `PK_`/`FK_`/`UNQ_`/`CK_`+테이블명.
- 논리 그룹화: 스키마 분리(`auth.F_LOGIN()`) 또는 함수명 접두어(`F_USER_GET_LIST`).
- 변수: 파라미터 `p_`, 지역 변수 `l_`.

### 쿼리 스타일
- 키워드 소문자(`create`/`select`), 객체명·컬럼명 대문자(`T_USER`/`COMPANY_ID`), 데이터 타입 소문자(`varchar`/`numeric`).
- 주의: PostgreSQL은 따옴표 없는 대문자를 소문자로 인식한다. 일관성을 위해 대문자로 쓰되 내부 저장은 소문자임을 인지(또는 `"T_USER"` 형태 사용).

### 공통 컬럼 (필수)
모든 테이블에 4개 포함:
```sql
CREATED_ON    timestamptz       not null default current_timestamp,
CREATED_BY    bigint,           -- T_USER.USER_ID 참조
UPDATED_ON    timestamptz,
UPDATED_BY    bigint            -- T_USER.USER_ID 참조
```

### UUID 컬럼 (외부 노출 식별자용, 권장)
- 컬럼명 `테이블명_UUID`(예: `USER_UUID`), 타입 `uuid`, 제약 `unique`.
- 생성: PG18+ `default uuidv7()`(시간순 정렬, 단편화 적음) / PG13~17 `default gen_random_uuid()` / PG12 이하 `pgcrypto` 확장 후 `gen_random_uuid()`.

### 감사 트리거 패턴
공통 4컬럼만 다루도록 작성하면 **모든 테이블에 재사용** 가능. 테이블별 고유 컬럼(예: `USER_UUID`)은 트리거에서 건드리지 말고 컬럼 `default`에 맡긴다.
```sql
-- 1. 공통 감사 트리거 함수 (모든 테이블 재사용)
create or replace function F_AUDIT_LOG()
returns trigger as $$
declare
    l_user_id bigint;
begin
    l_user_id := cast(current_setting('app.current_user_id', true) as bigint);
    if (tg_op = 'INSERT') then
        new.CREATED_ON := current_timestamp;
        new.CREATED_BY := coalesce(new.CREATED_BY, l_user_id);
        return new;
    elsif (tg_op = 'UPDATE') then
        new.UPDATED_ON := current_timestamp;
        new.UPDATED_BY := coalesce(new.UPDATED_BY, l_user_id);
        return new;
    end if;
    return new;
end;
$$ language plpgsql;

-- 2. 테이블에 트리거 적용 (트리거명: 테이블명 + _TRG)
create trigger T_USER_TRG
    before insert or update on T_USER
    for each row execute function F_AUDIT_LOG();
```

### ORM 연동 (SQLAlchemy Core 리플렉션) — SQL이 진실의 원천(SSOT)
- **방향**: 스키마는 SQL(`ddl/`)로 작성 → 앱은 `MetaData().reflect(only=[...])`로 인트로스펙트. 앱에서 `create_all`/migration으로 스키마를 만들지 않는다.
- **네이밍 보존**: 리플렉션은 실제 컬럼/테이블명을 그대로 가져온다(unquoted 식별자는 Postgres가 소문자로 접는다 — `T_USER`→`t_user`). 별도 매핑 설정이 필요 없다.
- **트리거·기본값은 SQL 소관**: `F_AUDIT_LOG()`·`gen_random_uuid()` 등은 앱 코드가 아니라 DDL이 관리한다.
- **Repository 계층 없음**: Service에서 리플렉션된 `Table` 객체(`metadata.tables["t_user"]`)로 직접 쿼리한다. (`fastapi-service-architecture` §2)
- **`_BY` 주입**: 인증 컨텍스트가 있는 프로젝트라면 Service 계층에서 `_BY` 값을 세팅한다. (`_ON`=트리거, `_BY`=앱 레이어). 인증이 없는 프로젝트는 `_BY`를 NULL로 유지한다.
- **스키마 변경 절차**: SQL 수정 → DB 반영(`psql -f ddl/...`) → 앱의 `REFLECTED_TABLES` 화이트리스트에 반영. 앱 코드로 스키마를 역생성하지 않는다.

## 상세
전체 규칙·예시·Client Extension 매핑은 `docs/DB_ARCHITECTURE_GUIDE.md` 참조.
