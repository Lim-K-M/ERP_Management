-- =========================================================
-- 전체 DDL 실행 스크립트 (psql 전용)
-- 사용:  psql "$DATABASE_URL" -f ddl/run_all.sql
-- FK 의존성 순서대로 실행한다.
-- =========================================================
\i functions/F_AUDIT_LOG.sql
\i tables/T_DEPARTMENT.sql
\i tables/T_POSITION.sql
\i tables/T_EMPLOYEE.sql
\i tables/T_EMPLOYMENT_HISTORY.sql
