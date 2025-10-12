# NB-DD-Studienarbeit

**unter Trello: https://trello.com/b/OKz8xrqB/my-trello-board**

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
