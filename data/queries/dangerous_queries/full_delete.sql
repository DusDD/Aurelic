-- =========================
-- FULL RESET
-- =========================

DROP SCHEMA IF EXISTS stocks CASCADE;

-- optional: sequences clean
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT sequence_schema, sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'stocks'
    )
    LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS '
        || quote_ident(r.sequence_schema) || '.'
        || quote_ident(r.sequence_name)
        || ' CASCADE';
    END LOOP;
END$$;
