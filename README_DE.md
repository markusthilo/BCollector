# BCollector
- Dateien von einem HTTP-, HTTPS- oder SFTP-Server in die lokale Infrastruktur herunterladen.
- Dateien in das Zielverzeichnis kopieren oder entschlüsseln.
- Backup im Download-Ordner für einen bestimmten Zeitraum aufbewahren, veraltete Dateien löschen.
- Funktioniert als Daemon / in einer Endlosschleife.
## Abhängigkeiten
Die Anwendung funktioniert mit Python 3.12. Neuere Versionen sollten kein Problem darstellen.

Zusätzlich zu den Standardbibliotheken werden `python-gnupg`, `py7zr` und `paramiko` benötigt:

```
python -m pip install python-gnupg py7zr paramiko
```
Falls Ihr Download-Rechner offline ist, laden Sie die Bibliotheken auf einem Online-System herunter:

```
python -m pip download python-gnupg py7zr paramiko
```
Übertragen Sie die .whl-Dateien auf den Offline-Rechner und führen Sie aus:
```
python -m pip install --no-index --find-links .\ python-gnupg paramiko
```
## Konfiguration
BCollector liest die Konfiguration aus einer Datei. Da `configparser` verwendet wird, wird die INI-Dateisyntax verwendet. Der Standard ist `bcollector.conf` im Verzeichnis von `bcollector.py`.

### Beispiel:
```
[REMOTE]
# Remote-Standort (URL) zum Synchronisieren
#url = https://example.org/
url = http://example.org:8080/
#url = sftp://user@example.org/
#password for sftp
#password = dummy
# Regulärer Ausdruck zur Auswahl der Zieldateien
match = *
#match = .*\.7z
#match = .*\.gpg
#match = ^[^.].*
# Timeout für Verbindungsversuch in Sekunden
timeout = 30
# Maximale Wiederholungen bei fehlgeschlagenen Download-Versuchen
retries = 10
# Verzögerung in Sekunden nach fehlgeschlagenem Download-Versuch
delay = 2
# pgp zum Entschlüsseln von pgp/gpg-Dateien mit symmetrischem Passwort, 7z zum Entpacken/Entschlüsseln von 7zip-Dateien oder none zum Deaktivieren der Entschlüsselung
encryption = pgp
#encryption = none
# Passphrase zum Entschlüsseln
passphrase = dummy

[LOCAL]
# Download-Verzeichnis (zum Synchronisieren/Prüfen auf neue Dateien)
download = /home/user/Download
# Zielverzeichnis zum Kopieren der Dateien, bei Bedarf unterwegs entschlüsseln
destination = /home/user/Public
# Log-Datei
logfile = /home/user/Logging/bcollector_log.txt
# Max. Größe der Log-Datei in MiB
logsize = 32
# Datenbank zur Verfolgung von Dateien
db = /home/user/.bcollector/files.db
# Auf yes setzen, um die Weiterleitung zu verzögern, bis das Zielverzeichnis nicht existiert
wait = yes
# Trigger-Dateiname zum Schreiben in das Zielverzeichnis
trigger = /home/neo/Public/test_trigger.txt
# Minuten zum Aufbewahren von Dateien im Download-Verzeichnis
keep_files = 1
# Minuten zum Aufbewahren von Einträgen in der Datenbank
keep_entries = 2

[LOOP]
# Endlosschleife mit yes aktivieren
enable = no
# Stunden des Tages (every = jede Stunde)
# hours = 0, 3, 9, 12, 15, 18, 21
hours = every
# Minuten der Stunde, wann der Download-Versuch gestartet werden soll (every = jede Minute)
#minutes = 8, 18, 28, 38, 48, 58
minutes = every
```
### REMOTE
Wenn die Quelldateien auf einem HTTP- oder HTTPS-Server gehostet werden, benötigt die Konfiguration
```
url = http://example.org:8080/
```
oder
```
url = https://example.org/
```
im REMOTE-Abschnitt der Konfigurationsdatei. Für das SFTP-Protokoll wird die URL in folgender Syntax angegeben:
```
url = sftp://user@example.org/
password = topsecret
```
Die Dateien können durch einen regulären Ausdruck ausgewählt werden. Der Eintrag
```
match = .*\.7z
```
würde alle Dateien mit der Erweiterung `.7z` kopieren/synchronisieren,
```
match = *
```
wählt alle Dateien aus.

Eine gute Wahl für die Kommunikation mit dem Server könnte sein:
```
timeout = 30
retries = 10
delay = 2
```
Dies bedeutet:
- Download-Versuch überspringen, wenn 30 Sekunden lang keine Antwort erfolgt
- Download-Versuch 10 Mal wiederholen, bevor ein Fehler ausgegeben wird
- 2 Sekunden vor neuem Download-Versuch warten

Eine spezielle Funktionalität ist das Entschlüsseln von Dateien beim Transport vom Download-Ordner zum endgültigen Ziel. GnuPG und 7-Zip sind derzeit implementiert. Die Verschlüsselung wird durch `pgp`, `7z` oder `none` für keine Verschlüsselung angegeben, z.B.:
```
encryption = pgp
passphrase = ultrasecret
```
### LOCAL
In diesem Abschnitt der Konfigurationsdatei werden die lokalen Pfade definiert:
```
download = /home/user/Download
destination = /home/user/Public
logfile = /home/user/Logging/bcollector_log.txt
logsize = 32
db = /home/user/.bcollector/files.db
```
Dies bedeutet:
- neue Dateien nach `/home/user/Download` herunterladen
- sie nach `/home/user/Public` kopieren (ggf. entschlüsselt)
- Log nach `/home/user/Logging/bcollector_log.txt` schreiben
- alte Logs mit ZIP komprimieren (im selben Verzeichnis) und neue Log-Datei erstellen
- Informationen über Dateien als SQLite datenbank in `/home/user/.bcollector/files.db` speichern

Unter Windows können Pfade `/` oder `\` verwenden (z.B. ist `C:\Users\User\Documents` dasselbe wie `C:/Users/User/Documents`), da Python's `pathlib` verwendet wird.

Wenn Sie den Transport vom Download zum Ziel verzögern möchten, bis der Zielordner gelöscht wird, fügen Sie
```
wait = yes
```
zum REMOTE-Abschnitt der Konfigurationsdatei hinzu.

Um weitere Aktionen auszulösen, kann eine Trigger-Datei erstellt werden, nachdem Dateien vom Download zum Zielordner weitergeleitet wurden:
```
trigger = /home/neo/Public/test_trigger.txt
```
Dateien im Download-Verzeichnis und Einträge in der SQLite-Datenbank können nach einem bestimmten Zeitdelta in Minuten entfernt werden. Offensichtlich funktioniert dies nicht, wenn die Einträge in der Datenbank vor dem Entfernen der Dateien gelöscht werden. Dieses Beispiel behält ein Backup für 6 Monate:
```
keep_files = 262980
keep_entries = 264420
```
### LOOP
Das Tool kann als Daemon ausgeführt werden:
```
enable = yes
```
Dies aktiviert eine Endlosschleife, die mit "Strg + C" unterbrochen werden kann.

Der Prozess gem. vorgegebener Stunde und Minute ausgelöst. Beispiele:
- alle 10 Minuten:
```
hours = every
minutes = 8, 18, 28, 38, 48, 58
```
- täglich um 02:10 und 14:10 (Systemzeit):
```
hours = 2, 14
minutes = 10
```
- jede Minute (maximale Frequenz):
```
hours = every
minutes = every
```
## Kommandozeile
BCollector ist ein Kommandozeilen-Tool. Optionen/Schalter mit `-h`/`--help` anzeigen:
```
python bcollector.py -h
```
Sie können die in `myconfig.conf` angegebene Verbindung zum Server mit `-s`/`--simulate` testen, bevor Sie als Daemon ausführen:

```
python bcollector.py -c myconfig.conf -s
```
Um das Log-Level auf DEBUG zu erhöhen, verwenden Sie `-d` oder `-l debug`:

```
python bcollector.py -d
```
Ohne Optionen
```
python bcollector.py
```
läuft das Tool im Log-Level INFO.
## Rechtlicher Hinweis
### Lizenz
GPL-3 beachten: https://www.gnu.org/licenses/gpl-3.0.en.html
### Haftungsausschluss
Verwenden Sie die Software auf eigenes Risiko.

Dies ist kein kommerzielles Produkt mit einer Armee von Entwicklern und einer eigenen Abteilung für Qualitätssicherung.