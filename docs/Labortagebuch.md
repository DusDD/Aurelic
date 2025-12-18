Labortagebuch:

17.12.2025: Aufholen verteilter/fehlender Dokumentation über die Umsetzung des Projekts an einem Ort
Initial wird die Projektstruktur angelegt, die sich in folgende Ordner aufteilt: "src" für den Quellcode, "db" für Skripte für zur Manipulation der Datenbank genutzte Skripte, "gui" für die Nutzeroberfläche und "images" zum Speichern von Bilddateien.
Der Ordner "docs" wird genutzt, um Dokumente an einem Ort zu sammeln, Skripte für die Docker-Umgebung im Ordner "docker" und Skripte zur Automatisierung ausgehend vom Betriebssystem in "scripts".
Außerdem werden weitere Ordner zur lokalen Organisation der Anwendung genutzt. Darunter zählt ".idea", der PyCharm-spezifisch ist und "venv" ermöglicht die Nutzung einer virtuellen Umgebung für Python3.
Beide werden durch die Datei ".gitignore" von der Synchronisierung über GitHub abgehalten. Gleiches gilt für die Datei ".env", die zur Speicherung von Login-Informationen der Datenbank genutzt wird und nicht geteilt werden sollte.

heutiger Fortschritt:
Zur Erarbeitung der im Projekt definierten Ziele, muss die zugrunde liegende Infrastruktur sowie Abhängigkeiten klar definiert sein. 
Darunter zählen die genutzten Geräte, Anwendungen und organisationstechnischen Maßnahmen. 
Zur Programmierung wird PyCharm zur Verwendung der Programmiersprache Python3 genutzt. Um die IDE mit einer funktionsfähigen Datenbankumgebung zu nutzen, wird Docker verwendet.
Ein Container mit Postgres Datenbank ermöglicht das Erstellen und organisieren von Datensätzen, die mithilfe von SQL-Abfragen innerhalb der IDE manipuliert werden können.
Zum Austausch der Abhängigkeiten für eine gleiche Programmierumgebung1 wird die Datei "requirements.txt" genutzt. So können zum Start des regelmäßigen Arbeitsflusses mit einem Befehl die externen Bibliotheken aller Teilnehmen abgeglichen und ergänzt werden.
Da sie darüber hinaus verschiedene Betriebssysteme nutzen, die jeweils die oben genannten Techniken unterstützen, wird eine "docker-compose.yml" angelegt, die das initiale Teilen der Docker-Umgebung ermöglicht.
In weiterer Dokumentation wird erstmals beschrieben, wie die initial auf einem Windows-System erstellte Datenbank nun ebenfalls über Github auf die Unix-basierten Systeme MacOS und LinuxMint übertragen werden können, sowie die Zusammenhänge der bereits genannten Projektstruktur. 
Diese werden in der "README.md" zusammengefasst.

Zur Programmierung der Anwendung werden Testdaten benötigt. Diese werden über API-Keys und einem Python-Skript mit zwei Methoden in der Datenbank gespeichert. Zuerst wird ein größerer Datenauszug genutzt, der 
die Datenhistorie der Aktien wieder spiegelt. Parallel wird eine tägliche Datenabfrage erstellt, die genauere Zeitabstände übergibt. Eine Datenübertragung mit genauen Kursbewegungen ist auch über die Vergangenheit, jedoch nur proprietär möglich.
Grundlegend wird folgender Stack zum Einpflegen der Daten genutzt:

[Kostenlose Aktien-API]
          ↓ (HTTP / JSON)
     Python Script
   (Daten holen & prüfen)
          ↓
   Daten aufbereiten
 (Datumsformat, Typen)
          ↓
     PostgreSQL DB
          ↑
   täglicher Scheduler
  (cron / Task Scheduler)

Für die Historie-Daten wird "yahoo finance" genutzt. 
Für die täglichen Daten wird "Alpha Vantage" genutzt.

Damit auf allen Geräten dieselbe Datenbankumgebung besteht, werden in einem Ordner "docker"
Initialisierungskripte hinterlegt, die das Grundschema der Datenbank bereits zum Start erstellt.

Die jetzige Implementierung ermöglicht somit folgende Standards:
- Komplettstruktur der Projektordner
- Synchronisierung der Docker und Datenbankumgebung über .env und der docker-compose.yml
- Skripten zur Automatisierung der data pulls und Einspeisung der Historie in die Datenbank
- Dokumentation zur Nachstellung des Vorgehens by design
- eine industry-standard main, von welcher nun Branches erstellt werden können

Das weitere Vorgehen sollte den kompletten SSDLC und Anforderungsmanagement angehen und den IST-Zustand vergleichen.
Die jetzige Implementierung dient als Fundament zur effektiven Kollaboration und ersten Datenpunkten.

