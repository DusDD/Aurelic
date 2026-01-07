-- Letzten 10 Login Events aus auth.login_events
SELECT *
FROM auth.login_events
ORDER BY timestamp DESC
LIMIT 10;

-- Alle Usernames aus auth.users
SELECT username
FROM auth.users
ORDER BY username;
