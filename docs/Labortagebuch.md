Labortagebuch:
Aufholen verteilter/fehlender Dokumentation über die Umsetzung des Projekts an einem Ort
Initial wird die Projektstruktur angelegt, die sich in folgende Ordner aufteilt: "src" für den Quellcode, "db" für Skripte für zur Manipulation der Datenbank genutzte Skripte, "gui" für die Nutzeroberfläche und "images" zum Speichern von Bilddateien.
Der Ordner "docs" wird genutzt, um Dokumente an einem Ort zu sammeln, Skripte für die Docker-Umgebung im Ordner "docker" und Skripte zur Automatisierung ausgehend vom Betriebssystem in "scripts".
Außerdem werden weitere Ordner zur lokalen Organisation der Anwendung genutzt. Darunter zählt ".idea", der PyCharm-spezifisch ist und "venv" ermöglicht die Nutzung einer virtuellen Umgebung für Python3.
Beide werden durch die Datei ".gitignore" von der Synchronisierung über GitHub abgehalten. Gleiches gilt für die Datei ".env", die zur Speicherung von Login-Informationen der Datenbank genutzt wird und nicht geteilt werden sollte.

## 17.12.2025:
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

## 07.01.2026: 
Zum täglichen Befüllen der Datenbank wird statt AlphaVantage nun Polygon genutzt.
Authentifizierung wird in produktiven Umgebungen eines Neo-Brokers durch Server-Client Kommunikation umgesetzt. 
Allerdings liegt der Fokus in der Implementierungsphase des Projekts auf der Architektur und nicht auf der Infrastruktur.
Deshalb wird die Logik voerst lokal beschrieben, jedoch modularisiert für spätere serverseitige Kommunikation ergestellt.
Zur sicheren Speicherung von Authentisierungsdaten, werden in der Datenbank zwei Schemata angelegt,
um diese logisch von Aktiendaten zu trennen. Für die Registrierungs- und Loginprozesse werden kryptografisch 
sicher Authentisierungsdaten getrennt von Eventdaten gespeichert.


## 17.12.2025:
### Projektinfrastruktur und Entwicklungsumgebung

Zur Erarbeitung der im Projekt definierten Ziele ist es erforderlich, die zugrunde liegende technische Infrastruktur sowie alle relevanten Abhängigkeiten klar und reproduzierbar zu definieren. Dazu zählen sowohl die genutzten Endgeräte als auch die eingesetzten Anwendungen und organisatorischen Maßnahmen zur Zusammenarbeit.

Die Entwicklung der Anwendung erfolgt unter Verwendung der integrierten Entwicklungsumgebung PyCharm mit der Programmiersprache Python 3. Um eine konsistente und unabhängig vom Host-System funktionierende Datenbankumgebung bereitzustellen, wird Docker eingesetzt. Hierbei wird ein Container mit einer PostgreSQL-Datenbank genutzt, welcher das strukturierte Erstellen, Verwalten und Abfragen von Datensätzen ermöglicht. Der Zugriff auf die Daten erfolgt über SQL-Abfragen direkt aus der Entwicklungsumgebung heraus.

Zum Austausch und zur Synchronisierung externer Abhängigkeiten innerhalb des Entwicklungsteams wird die Datei requirements.txt verwendet. Diese erlaubt es, mit einem einzelnen Befehl sämtliche benötigten Python-Bibliotheken zu installieren und stellt somit sicher, dass alle Projektbeteiligten mit einer identischen Programmierumgebung arbeiten.

Da innerhalb des Projektteams unterschiedliche Betriebssysteme (Windows, macOS, Linux Mint) verwendet werden, wird zusätzlich eine docker-compose.yml bereitgestellt. Diese ermöglicht das initiale sowie fortlaufende Teilen einer einheitlichen Docker-Umgebung und abstrahiert systemabhängige Unterschiede. In der begleitenden Dokumentation wird beschrieben, wie eine ursprünglich auf einem Windows-System erstellte Datenbankumgebung über GitHub auf Unix-basierte Systeme übertragen werden kann. Die Zusammenhänge zwischen Projektstruktur, Docker-Setup und Datenbankinitialisierung werden zentral in der Datei README.md dokumentiert.

### Datenbeschaffung und -persistenz

Zur Entwicklung und zum Test der Anwendung werden realitätsnahe Aktiendaten benötigt. Diese werden über externe APIs bezogen und mithilfe eines Python-Skripts in der PostgreSQL-Datenbank gespeichert. Das Skript besteht aus zwei logisch getrennten Methoden:
Zum einen wird ein größerer Datenauszug genutzt, welcher die historische Entwicklung von Aktienkursen abbildet. Zum anderen wird eine regelmäßige, tägliche Datenabfrage implementiert, die feinere zeitliche Auflösungen bereitstellt. Eine noch granularere Kursdarstellung (z. B. Tick-Daten) ist grundsätzlich auch retrospektiv verfügbar, jedoch ausschließlich über proprietäre und kostenpflichtige Schnittstellen.

Der grundlegende technische Ablauf zur Datenintegration lässt sich wie folgt darstellen:

[Kostenlose Aktien-API]
          ↓ (HTTP / JSON)
     Python-Skript
   (Daten abrufen & validieren)
          ↓
   Datenaufbereitung
 (Datumsformate, Datentypen)
          ↓
     PostgreSQL-Datenbank
          ↑
   Täglicher Scheduler
  (cron / Task Scheduler)


Für den Import historischer Kursdaten wird die API von Yahoo Finance verwendet. Für die initial geplante tägliche Aktualisierung wurde zunächst Alpha Vantage genutzt.

Um sicherzustellen, dass auf allen Entwicklungsrechnern dieselbe Datenbankstruktur vorhanden ist, werden im Ordner docker Initialisierungsskripte hinterlegt. Diese erzeugen beim Start des Containers automatisch das erforderliche Grundschema der Datenbank, einschließlich der Tabellen zur Speicherung von Aktienkursen.

### Aktueller Stand der Implementierung

Die bisherige Implementierung stellt folgende Standards und Funktionalitäten bereit:

- Vollständige und nachvollziehbare Projektordnerstruktur
- Synchronisierung der Docker- und Datenbankumgebung über .env-Dateien und docker-compose.yml

- Skripte zur Automatisierung des Datenimports (historische und tägliche Daten)

- Dokumentation zur reproduzierbaren Nachstellung des Entwicklungsprozesses

- Eine konsistente und industrieübliche Hauptentwicklungslinie (main), von welcher Feature-Branches abgeleitet werden können

Diese Implementierung bildet das Fundament für eine strukturierte Weiterentwicklung des Projekts, eine effektive Kollaboration im Team sowie erste belastbare Datenpunkte. Das weitere Vorgehen orientiert sich am vollständigen Secure Software Development Life Cycle (SSDLC) sowie an einem systematischen Anforderungsmanagement, wobei der aktuelle Ist-Zustand als Referenz dient.

## 07.01.2026
### Erweiterung um Authentifizierungslogik

Im Zuge der Weiterentwicklung wurde für die tägliche Befüllung der Datenbank die bisher verwendete API Alpha Vantage durch Polygon ersetzt, um stabilere und zeitnähere Marktdaten zu erhalten.

Ein weiterer zentraler Schwerpunkt dieser Projektphase liegt auf der Implementierung einer Authentifizierungslogik. In produktiven Umgebungen, wie sie beispielsweise bei Neo-Brokern eingesetzt werden, erfolgt die Authentifizierung üblicherweise über eine serverseitige Client-Server-Kommunikation. Da sich das Projekt jedoch aktuell in einer Implementierungs- und Architekturphase befindet, liegt der Fokus nicht auf der finalen Infrastruktur, sondern auf einer sauberen, modularen Logik.

Aus diesem Grund wird die Authentifizierungslogik zunächst lokal implementiert, jedoch von Beginn an so modular aufgebaut, dass eine spätere serverseitige Erweiterung (z. B. über REST-APIs) ohne grundlegende Änderungen möglich ist.

Zur sicheren Speicherung von Authentifizierungsdaten wird die bestehende PostgreSQL-Datenbank um ein separates Schema erweitert. Dieses Authentifizierungs-Schema ist logisch vollständig von den Aktiendaten getrennt. Während das bestehende Schema ausschließlich Finanz- und Marktdaten enthält, werden im Authentifizierungs-Schema ausschließlich benutzerbezogene Daten gespeichert. Diese Trennung reduziert die Angriffsfläche und folgt dem Prinzip der geringsten Berechtigung.

Im Rahmen der Implementierung wurden folgende Komponenten realisiert:

- Registrierung neuer Benutzer mit kryptografisch sicherem Passwort-Hashing (bcrypt)

- Login-Mechanismus mit Passwortverifikation

- Zählung fehlgeschlagener Login-Versuche

- Temporäre Kontosperre nach einer definierten Anzahl fehlerhafter Anmeldeversuche

- Protokollierung sicherheitsrelevanter Ereignisse (Registrierung, erfolgreicher Login, fehlgeschlagener Login, Kontosperre) in einer separaten Event-Tabelle

Die gesamte Authentifizierungslogik ist strikt von der grafischen Benutzeroberfläche getrennt. Die GUI fungiert ausschließlich als Eingabe- und Ausgabeschicht, während sicherheitskritische Entscheidungen ausschließlich innerhalb der Authentifizierungsmodule getroffen werden. Dieses Design ermöglicht eine klare Trennung von Zuständigkeiten, verbessert die Testbarkeit und stellt sicher, dass die Implementierung später ohne größere Anpassungen in eine serverbasierte Architektur überführt werden kann.

Nach der grundlegenden Implementierung der Registrierungs- und Login-Funktionalität wurde die Authentisierungslogik schrittweise erweitert, um sicherheitsrelevante Anforderungen eines produktionsnahen Systems abzubilden. Ziel war es, trotz lokaler Ausführung eine Architektur zu entwerfen, die später ohne grundlegende Änderungen in eine serverbasierte Client-Server-Kommunikation überführt werden kann.

Zentraler Bestandteil dieser Erweiterung war die klare Trennung von fachlichen Daten (Aktiendaten) und sicherheitskritischen Informationen (Authentifizierungs- und Nutzerdaten). Zu diesem Zweck wurde die PostgreSQL-Datenbank um ein separates Schema auth ergänzt. Dieses Schema enthält ausschließlich Tabellen zur Benutzerverwaltung, Authentisierung sowie sicherheitsrelevante Ereignisse. Die bereits bestehenden Aktiendaten verbleiben isoliert im Schema stocks. Dadurch wird eine logische und organisatorische Trennung sensibler Daten erreicht, was sowohl der Wartbarkeit als auch den Prinzipien des Least-Privilege-Ansatzes entspricht.

### Passwortsicherheit und Validierung
Die Registrierung eines neuen Nutzers erfolgt ausschließlich nach erfolgreicher Validierung des gewählten Passworts. Dabei werden sowohl funktionale als auch sicherheitsrelevante Kriterien geprüft. Die Passwortvalidierung ist bewusst im Backend implementiert, obwohl im Frontend bereits eine dynamische Rückmeldung erfolgt. Dies verhindert das Umgehen von Sicherheitsregeln durch manipulierte Clients.

Die Validierungslogik umfasst folgende Kriterien:

- Mindestlänge des Passworts

- Vorhandensein von Groß- und Kleinbuchstaben

- Verwendung numerischer Zeichen

- Verwendung von Sonderzeichen

- Ausschluss bekannter, leicht erratbarer Passwörter

Erst nach erfolgreicher Prüfung wird das Passwort mithilfe des kryptografischen Hash-Verfahrens bcrypt verarbeitet. Das Klartextpasswort wird zu keinem Zeitpunkt persistent gespeichert. Die Verwendung von passlib abstrahiert dabei die Hash-Funktion und erlaubt eine spätere Migration auf alternative Verfahren (z. B. Argon2), ohne die restliche Logik anzupassen.

### Login-Absicherung und Account-Schutzmechanismen
Zur Absicherung gegen automatisierte Login-Angriffe und Brute-Force-Versuche wurden mehrere Schutzmechanismen implementiert, die unterschiedliche Zeithorizonte abdecken.

#### Rate Limiting (kurzfristig)

Ein speicherbasierter Rate Limiter verhindert, dass ein Nutzer innerhalb eines kurzen Zeitfensters zu viele Login-Versuche durchführen kann. Hierbei werden Zeitstempel fehlgeschlagener Login-Versuche temporär im Arbeitsspeicher gehalten. Wird das definierte Limit überschritten, wird der Login-Versuch unmittelbar abgelehnt.

Diese Implementierung ist bewusst lokal gehalten, jedoch so gestaltet, dass sie später problemlos durch eine serverseitige Lösung (z. B. Redis) ersetzt werden kann.

#### Account Lock (persistente Sperre)

Zusätzlich zum Rate Limiting wird bei wiederholten fehlgeschlagenen Login-Versuchen eine kontobasierte Sperre aktiviert. Die Anzahl fehlgeschlagener Versuche sowie ein möglicher Sperrzeitpunkt (locked_until) werden persistent in der Datenbank gespeichert.

Erreicht ein Nutzer eine definierte Anzahl fehlgeschlagener Login-Versuche, wird sein Konto für einen festgelegten Zeitraum gesperrt. Während dieser Zeit sind Login-Versuche unabhängig vom Passwort nicht möglich. Nach erfolgreichem Login werden sowohl der Zähler für fehlgeschlagene Versuche als auch eine bestehende Sperre zurückgesetzt.
Diese Trennung zwischen kurzfristigem Rate Limiting und persistentem Account Lock stellt sicher, dass sowohl automatisierte Angriffe als auch manuelle Fehlbedienungen angemessen behandelt werden.

### Token-basierte Authentisierung und Zugriffsschutz
Nach erfolgreichem Login wird ein kryptografisch zufälliger Token erzeugt, der den authentifizierten Nutzer eindeutig identifiziert. Dieser Token fungiert als Session-Äquivalent in der lokalen Umgebung und ist bewusst unabhängig von der grafischen Benutzeroberfläche implementiert.

Der Zugriff auf geschützte Ressourcen, insbesondere auf Aktiendaten, erfolgt ausschließlich über einen Auth-Guard. Dieser überprüft bei jedem Datenzugriff:

- ob ein Token vorhanden ist,

- ob der Token gültig ist,

- welchem Nutzer der Token zugeordnet ist.

Erst nach erfolgreicher Prüfung wird der Zugriff auf die entsprechenden Datenbankabfragen erlaubt. Dadurch ist sichergestellt, dass fachliche Daten ausschließlich authentifizierten Nutzern zur Verfügung stehen. Die Implementierung orientiert sich konzeptionell an serverseitigen Middleware-Mechanismen und kann später durch JWT oder andere tokenbasierte Verfahren ersetzt werden.

### Logging von sicherheitsrelevanten Ereignissen
Zur Nachvollziehbarkeit und späteren Analyse sicherheitsrelevanter Vorgänge werden Login- und Registrierungsereignisse protokolliert. Diese Ereignisse werden getrennt von den eigentlichen Nutzerdaten gespeichert und enthalten unter anderem:

- Benutzer-ID

- Ereignistyp (z. B. Login, fehlgeschlagener Login, Registrierung)

- Zeitstempel

Diese Logs bilden die Grundlage für Monitoring, Auditing sowie forensische Analysen und entsprechen gängigen Anforderungen an sicherheitskritische Anwendungen.

### Architekturentscheidung und Ausblick
Obwohl die aktuelle Implementierung lokal ausgeführt wird, orientiert sich die gesamte Authentisierungsarchitektur an produktionsnahen Standards. Die klare Modularisierung der Komponenten (Registrierung, Login, Security, Guard, Logging) ermöglicht eine spätere Erweiterung um serverseitige Kommunikation, HTTPS-Absicherung (TLS) sowie Zwei-Faktor-Authentifizierung, ohne bestehende Logik grundlegend verändern zu müssen.

Die aktuelle Implementierung stellt somit einen stabilen, sicheren und erweiterbaren Authentifizierungs-Kern dar, der als Grundlage für weitere Entwicklungsphasen im Sinne eines vollständigen Secure Software Development Life Cycle (SSDLC) dient.


