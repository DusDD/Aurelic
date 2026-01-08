-- Letzten 10 Login Events aus auth.login_events
SELECT *
FROM auth.login_events
ORDER BY timestamp DESC
LIMIT 10;

-- Alle Usernames aus auth.users
SELECT id, last_name
FROM auth.users
ORDER BY last_name;


-- ALTER
-- auth.users Soft-Delete Spalte hinzufügen
ALTER TABLE auth.users
ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS failed_login_attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

ALTER TABLE auth.users
RENAME COLUMN postal TO postal_code;
