-- Initialize read-only role and user for NL-to-SQL guardrails
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'civic_readonly') THEN
        CREATE ROLE civic_readonly WITH LOGIN PASSWORD 'readonlypassword';
    END IF;
END
$$;

-- Grant connect on database
GRANT CONNECT ON DATABASE civicsignal TO civic_readonly;
GRANT USAGE ON SCHEMA public TO civic_readonly;

-- By default, allow SELECT on all tables except sensitive ones (e.g. users)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO civic_readonly;
