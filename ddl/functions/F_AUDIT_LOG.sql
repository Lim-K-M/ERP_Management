-- =========================================================
-- F_AUDIT_LOG — 공통 감사 트리거 함수 (모든 테이블 재사용)
-- 실행 순서: 테이블 생성보다 먼저 실행되어야 한다.
--   · _ON  = 이 트리거가 채운다 (생성/수정 시각)
--   · _BY  = 앱이 세션 변수 app.current_user_id 로 주입한 사용자 ID
-- =========================================================
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
