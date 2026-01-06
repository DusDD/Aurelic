# NB-DD-Studienarbeit
- never leak .env
- always reference on .env
- use .env.example for setting up own .env
- it is used as login credentials reference for the local database and its initializing scripts

## collaborators rough task mapping (up to 06.01.)
- Becker: overleaf-owner+design, finishing overleaf-sections, design/plan paper, hard paperwork, communication, frontend
- Doehring: paper-assistance, documentation-meetings/labortagebuch/sprints, github/kanban/zotero-owner, programming-architecture, backend

## work with zotero and overleaf
- user DD edits single point of truth references.bib locally
- file is pushed on github by default programming workflow
- file is manually replaced on overleaf (as automation proves as tedious to set up)
- both collaborators cite with keys from .bib
- zotero **can't** be edited via overleaf, only locally at single point of truth

## work with postgres
```
git clone <repo>
cd project
cp .env.example .env
docker compose up -d
```

connect directly to it via
`psql -h localhost -U [USERNAME] -d [DATABASE_NAME]`

## work with docker
initial wie oben: docker compose up -d
`docker ps` -> zeigt laufende Container
`docker ps -a` -> zeigt alle Container
`docker start <container_name>` -> startet gestoppten Container
`docker stop <container_name>` -> stoppt laufenden Container
`docker rm <container_name>` -> entfernt den Container
`docker logs -f <container_name>` -> zeigt Echtzeitlogs
`docker volume ls` -> listet alle Docker Volumes (virtuelle Datenträger)
`docker exec -it <container_name>` -> führt Befehle im Container aus

## workflow KanBan and Issues
always add to KanBan for every task
add as draft if not coding specific
add as issue if coding specific

## Some git
always use this workstream:

`git pull` when start working

`git add [files or just "."] ` add what you want to commit and push

`git commit -m "[your message]"` commit to document what happens

`git push` sync changes to Github for someone else to pull

always work on dedicated branch, never push on main

## PostgreSQL
Version 18.0
Now working with docker on windows 11
inside the DB when manually connected with
`psql -h localhost -U [USERNAME] -d [DATABASE_NAME]`

use commands:
`\q` quits
`\d [table]` displays table

normal SQL works as well:
`SELECT current_database();` shows current DB

## Libraries 
postgreSQL extensions:
- timescaledb //für Zeitreihen-Analysen
- pgvector //KI-basierte Analysen?

postgreSQL to python integration:
- psycopg2, asyncpg //klassische SQL-Abfragen
- SQLAlchemy //strukturierte Abbildung von Tabellen auf Klasse
- pandas //Daten aus SQL in DataFrames ziehen ->Analyse und Visualisierung


## Work-Stream DB
- DB so früh wie möglich machen, um direkt Daten zu sammeln
- PostgreSQL nutzen
- wie nutzen?
```
use this to login via psql on cmd: psql -h localhost -U postgres
use this to login without psql, not recommended, just trouble shooting: docker exec -it postgres psql -U postgres
```

## Work-Stream general (good for KAUMA as well)
- document every commit (summarise)
- implement Unittests??
- how to use KanBan, V-Modell and Github in parallel? some workstream ideas?


# Workflow vor dem Coden
✅ Dein Workflow (leicht erweitert)

1️⃣ Terminal starten / Projekt öffnen
Wechsel in dein Projektverzeichnis
`cd ~/stockapp`

2️⃣ Virtuelle Umgebung aktivieren
`source venv/bin/activate` Linux / macOS
`venv\Scripts\activate`    Windows PowerShell


✅ Wichtig: Jedes Mal, wenn du eine neue Terminal-Session startest.
Optional: PyCharm nutzt venv automatisch, wenn korrekt konfiguriert.

3️⃣ Requirements prüfen
Vor dem Start schauen, ob jemand neue Libraries hinzugefügt hat:

`pip install -r requirements.txt`

Das stellt sicher, dass dein venv aktuell ist, z. B. nach Pull vom Repo.

4️⃣ Arbeiten & neue Libraries installieren
Neue Library installieren:

`pip install <library_name>`

Wichtig: Danach immer requirements.txt aktualisieren:

`pip freeze > requirements.txt`

Am besten sofort nach Installation, nicht erst am Ende des Tages. So gehen Änderungen nicht verloren.

5️⃣ Git-Workflow parallel
Vor der Arbeit:

`git pull`

Am Ende des Tages / nach Features:

```
git add .
git commit -m "Beschreibung der Änderungen"
git push
```

6️⃣ Optional: venv deaktivieren
Terminal schließen oder explizit:

`deactivate`

🔹 Kleine zusätzliche Tipps
requirements.txt versionieren: Immer updaten, sobald du Libraries installierst.
.gitignore prüfen: venv darf nicht hochgeladen werden.
Environment-Consistency: Für Cross-System-Arbeit (Linux + Windows) immer pip install -r requirements.txt nach Pull auf jedem System.
Optional: Commit-Signierung mit GPG, falls du es schon eingerichtet hast.
