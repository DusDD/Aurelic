# RDBMS PostGreSQL
About managing and connecting. So I don't forget commands.

## Starting, Stopping and Login
start docker with ``docker start postgres``

stop docker with ``docker stop postgres``

check containers with ``docker ps -a``

login with ``psql -h localhost -U postgres``
or just use connect file

more under https://docs.docker.com/reference/cli/docker/container/start/

## Die Datenbank dauerhaft machen, über Containarisierung hinaus
⚠️ Aber Achtung: Container ≠ dauerhaft, wenn kein Volume

Wenn du den Container z. B. mit

docker run --name postgres_stockapp -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres

gestartet hast, ohne ein Volume zu mounten, dann gilt:

❌ Wenn du docker rm postgres_stockapp machst → alles (auch deine Tabellen) ist weg.

✅ So machst du deine Daten dauerhaft (persistente Speicherung)

Das geht mit einem sogenannten Docker Volume oder einem bind mount.
Z. B.:

docker run -d \
  --name postgres_stockapp \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres


Das -v pgdata:/var/lib/postgresql/data sorgt dafür,
dass die Daten außerhalb des Containers aufbewahrt werden.

Wenn du den Container löscht oder neu startest → deine DB bleibt.

Du kannst prüfen, ob du das schon hast:

docker inspect postgres_stockapp | grep Mounts -A 5

Wenn dort etwas mit /var/lib/postgresql/data steht → alles gut ✅