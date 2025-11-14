# NB-DD-Studienarbeit

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
