-- Runs once, when the Postgres container is created for the first time.
-- Creates the read-only role used by the future NL-to-SQL feature.
-- (Local development password. Use a strong, different one in production.)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'civic_readonly') THEN
        CREATE ROLE civic_readonly WITH LOGIN PASSWORD 'readonlypassword';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE civicsignal TO civic_readonly;
GRANT USAGE ON SCHEMA public TO civic_readonly;

-- No table access here on purpose (least privilege).
-- Alembic migration 0003 grants SELECT on the safe columns of `complaints` only
-- (never `users`, never `complaints.reporter_id`). New tables are NOT shared automatically.
