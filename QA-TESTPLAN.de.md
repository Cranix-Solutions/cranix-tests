# CRANIX Server — QA-Testplan

- Version: 1.0
- Gilt für Pakete: `cranix-base`, `cranix-java`, `cranix-web` (cranix-mobile-app)
- Zielgruppe: menschlicher Testingenieur, der einen manuellen Testlauf auf einem CRANIX-Testserver durchführt
- Englische Version: [QA-TESTPLAN.md](QA-TESTPLAN.md)

---

## 1. Zweck und Umfang

Dieser Plan prüft die Qualität eines CRANIX-Servers, nachdem die regelmäßig
aktualisierten Pakete **`cranix-base`**, **`cranix-java`** und **`cranix-web`**
(cranix-mobile-app) installiert wurden. Es handelt sich um einen
**manuell auszuführenden Regressionstest mit Ankreuzfeldern**, der
Regressionen durch ein Paket-Update aufdecken soll.

Abgedeckt sind:

| Paket | Was getestet wird |
|---|---|
| `cranix-base` | Backend-Skripte, Tools, Plugins, Setup/Update, Samba/AD, DNS/DHCP, Drucken, Quota, Backup, Import/Export, Adhoc-Räume, Salt |
| `cranix-java` | REST-API (`cranix-api` auf Port 9080), Datenbankmigration, Authentifizierung/ACL, alle wichtigen API-Bereiche |
| `cranix-web` | Web-Admin-GUI (Angular/Ionic) und Mobile-/PWA-App: Login, Menüs, alle wichtigen Seiten |

Nicht abgedeckt: OS-/Kernel-Patches, Fremdpakete außerhalb von CRANIX,
Cephalix-Cloud-Interna sowie Hardware-/Netzwerkinfrastruktur.

---

## 2. Testumgebung

- Es wird ein funktionierender, bereits installierter und konfigurierter
  **CRANIX-Testserver** verwendet (keine Neuinstallation des Systems).
- Getestet wird **Update-in-place**: Das/die zu testende(n) Paket(e) werden auf
  dem laufenden Server installiert, danach werden die Testfälle ausgeführt.
- Empfohlen: ein **disponibler/snapshot-fähiger** Testserver, da mehrere
  Tier-2-Fälle destruktiv sind (Benutzer/Räume/Geräte löschen, Klassenverzeichnisse
  leeren, Dienste neu installieren).
- Testclient: ein Rechner im Schulnetz mit aktuellem Browser (Chrome/Firefox)
  und für Mobile-Fälle ein iOS-Gerät oder der Mobile-/PWA-Modus des Browsers.

### 2.1 Umgebung vor dem Start erfassen

| Punkt | Wert |
|---|---|
| Server-Hostname / IP | |
| Server-OS-Version (`cat /etc/os-release`) | |
| `cranix-base` Version (`rpm -q cranix-base`) | |
| `cranix-java` Version (`rpm -q cranix-java`) | |
| `cranix-web` Version (`rpm -q cranix-web`) | |
| Datum/Uhrzeit des Testlaufs | |
| Tester | |

---

## 3. Vorbedingungen und Sicherheit

1. Vor dem Einspielen der Updates ein **Backup/Snapshot** erstellen
   (`crx-backup -f` oder VM-Snapshot). Danach prüfen, dass das Update-Log
   existiert (`/var/log/CRANIX-UPDATE-*`).
2. Sicherstellen, dass vorhanden sind: eine `admin`-Sitzung, ein Testschüler, ein
   Testlehrer, mindestens ein Raum und eine Hardwarekonfiguration.
3. Optional, aber zur Diagnose empfohlen: `CRANIX_DEBUG="yes"` in
   `/etc/sysconfig/cranix` setzen.
4. Die Setup-Skripte `bin/00300-setup-class-adhoc-rooms.sh` und
   `bin/00310-setup-teachers-adhoc-rooms.sh` erzeugen viele Zufallsgeräte und
   Räume — nur auf einem disponiblen Testserver ausführen.
5. Nach dem Lauf `CRANIX_DEBUG` wieder entfernen und Testdaten aufräumen.

---

## 4. Testdaten einrichten

Das Paket `cranix-tests` enthält Generatoren. Alles wird unter
`/usr/share/cranix/tests` installiert und über `tests/cranix-full-test.sh`
gesteuert.

```bash
# Alle Setup-Phasen in nummerierter Reihenfolge ausführen
/usr/share/cranix/tests/tests/cranix-full-test.sh
```

| Skript | Zweck |
|---|---|
| `bin/00100-import-users.sh` | Importiert generierte Schüler und Lehrer |
| `bin/00200-setup-radius.sh` | Installiert `cranix-radius`, aktiviert Geräteregistrierung |
| `bin/00300-setup-class-adhoc-rooms.sh` | Erzeugt Klassen-Adhoc-Räume + Schülergeräte |
| `bin/00310-setup-teachers-adhoc-rooms.sh` | Erzeugt Lehrer-Adhoc-Raum + Geräte |
| `helper/create-students-import.sh` | Erzeugt die Schüler-CSV (4 Klassen × 3 Züge × 10) |
| `helper/create-teachers-import.sh` | Erzeugt die Lehrer-CSV (15 Lehrer) |
| `helper/create-random-mac.sh` | Zufällige MAC-Adresse für Geräteregistrierung |
| `helper/functions.sh` | `check_result`-Helfer für API-JSON-Ergebnisse |
| `datas/import-utf8-test.csv` | UTF-8-/Umlaut-Import-Fixture |

Anzahlen können vor dem Lauf überschrieben werden, z. B.:

```bash
export CLASS_COUNT=1 STUDENT_COUNT=3 TEACHER_COUNT=2
```

---

## 5. Tier-Definitionen

- **Tier 0 — Umgebung:** muss immer vor allen anderen Fällen ausgeführt werden.
- **Tier 1 — Smoke:** der kritische Pfad. Nach **jedem** Paket-Update ausführen.
  Zieldauer ca. 1 Stunde. Alle Tier-1-Fälle müssen bestehen.
- **Tier 2 — Erweitert:** tiefergehende und destruktive Abdeckung. Vor einem
  Release ausführen oder wenn ein Tier-1-Fall fehlschlägt und eingegrenzt werden
  muss. Kann einen halben Tag oder länger dauern.

Prioritätslegende: **H** = hoch, **M** = mittel, **L** = niedrig.

---

## 6. Testfall-Vorlage

Jeder Fall nutzt diese Struktur:

```
### ID — Titel
- Tier: 1 | Paket: cranix-base | Priorität: H
- Vorbedingungen: ...
- Schritte:
  1. ...
- Erwartetes Ergebnis: ...
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: __________
```

Das Ergebnis direkt in dieses Dokument (oder eine Kopie davon) eintragen und
zusammen mit der Umgebungstabelle aus Abschnitt 2.1 an den Maintainer
zurückgeben.

---

## 7. Testfall-Katalog

### Tier 0 — Umgebung (`ENV-`)

#### ENV-01 — Versionen erfassen und Update einspielen
- Tier: 0 | Paket: alle | Priorität: H
- Vorbedingungen: Backup/Snapshot erstellt.
- Schritte:
  1. Abschnitt 2.1 ausfüllen.
  2. Das/die zu testende(n) Paket(e) aktualisieren (`zypper -n up <paket>` oder `crx_update.sh`).
  3. Resultierende Versionen und die Update-Logdatei notieren.
- Erwartetes Ergebnis: Update läuft ohne unaufgelöste Abhängigkeiten durch; neue
  Versionen erfasst; keine `error:`/`failed`-Zeilen im Update-Log.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### ENV-02 — Konfigurations-Zusammenführung nach dem Update
- Tier: 0 | Paket: cranix-base | Priorität: H
- Vorbedingungen: Update eingespielt.
- Schritte:
  1. `/etc/sysconfig/cranix` auf neu hinzugekommene `CRANIX_*`-Schlüssel prüfen.
  2. Ggf. `fix-sysconfig.py` ausführen und erneut prüfen.
- Erwartetes Ergebnis: Neue Schlüssel mit sinnvollen Standardwerten vorhanden;
  bestehende lokale Werte bleiben erhalten.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### ENV-03 — Dienstzustand
- Tier: 0 | Paket: cranix-base, cranix-java | Priorität: H
- Vorbedingungen: Update eingespielt.
- Schritte:
  1. `check_services.sh` ausführen und das JSON prüfen.
  2. `systemctl status cranix-api salt-master samba-ad samba-fileserver samba-printserver sssd chronyd apache2` prüfen.
  3. Prüfen, dass `/var/adm/cranix/opentasks` leer ist.
- Erwartetes Ergebnis: Alle überwachten Dienste aktiv; keine unerwarteten
  fehlerhaften Units; keine hängenden offenen Aufgaben.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### ENV-04 — Neustart / Persistenz nach dem Update
- Tier: 0 | Paket: alle | Priorität: M
- Vorbedingungen: Update eingespielt.
- Schritte:
  1. Server neu starten.
  2. Nach dem Boot ENV-03 wiederholen und sich in der Web-GUI anmelden.
- Erwartetes Ergebnis: Alles kommt automatisch wieder hoch; kein manueller
  Neustart nötig.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

---

### cranix-base (`BASE-`)

#### BASE-01 — Samba AD und DNS-Host-Einträge
- Tier: 1 | Paket: cranix-base | Priorität: H
- Vorbedingungen: ENV-03 bestanden; Admin-Zugang zur Serverkonsole.
- Schritte:
  1. Testhost anlegen (`crx_add_host.sh <ip> <name> <mac>`).
  2. Auflösung Name → IP (forward) und IP → Name (reverse) an einem Client prüfen.
  3. Host umbenennen und löschen.
- Erwartetes Ergebnis: Forward- und Reverse-Einträge werden angelegt, geändert
  und entfernt; der Name ist von einem Netzclient auflösbar.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-02 — Massenimport Schüler
- Tier: 1 | Paket: cranix-base | Priorität: H
- Vorbedingungen: Schüler-CSV-Generator verfügbar.
- Schritte:
  1. `helper/create-students-import.sh > /tmp/students.csv` ausführen.
  2. `crx_import_user_list.py --input /tmp/students.csv --role students --full --appendBirthdayToPassword --appendClassToPassword --cleanClassDirs` ausführen.
  3. Prüfen, dass `/home/groups/<Klasse>` mit korrektem Eigentümer/ACLs existiert.
- Erwartetes Ergebnis: Benutzer und Klassen angelegt; Klassenverzeichnisse
  vorhanden; keine `opentasks` übrig; UIDs/Gruppenzuordnung in Samba korrekt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-03 — Massenimport Lehrer
- Tier: 1 | Paket: cranix-base | Priorität: H
- Vorbedingungen: BASE-02 bestanden.
- Schritte:
  1. `helper/create-teachers-import.sh > /tmp/teachers.csv` ausführen.
  2. `crx_import_user_list.py --input /tmp/teachers.csv --role teachers --full` ausführen.
- Erwartetes Ergebnis: Lehrer mit Rolle `teachers` angelegt; Klassen zuweisbar;
  keine Fehler.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-04 — Benutzer exportieren
- Tier: 1 | Paket: cranix-base | Priorität: M
- Vorbedingungen: BASE-02/03 bestanden.
- Schritte:
  1. `crx_export_users.py students` (und `teachers`) ausführen.
  2. Die erzeugte CSV prüfen.
- Erwartetes Ergebnis: Alle importierten Benutzer erscheinen mit korrektem
  `uid;givenName;surName;classes;birthDay`.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-05 — Home- und Gruppenverzeichnisse zurücksetzen
- Tier: 1 | Paket: cranix-base | Priorität: M
- Vorbedingungen: Testbenutzer vorhanden.
- Schritte:
  1. Eine Datei/ein ACL im Benutzer-Home und einem Gruppenverzeichnis ändern.
  2. `crx_reset_home.sh` und `crx_reset_groups.sh` ausführen.
  3. Homes und Gruppenverzeichnisse erneut prüfen.
- Erwartetes Ergebnis: Homes/Gruppen aus Vorlagen mit korrekten ACLs
  wiederhergestellt; Berechtigungen konsistent für Schüler-/Lehrerrollen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-06 — Druckerwarteschlange und CUPS
- Tier: 1 | Paket: cranix-base | Priorität: H
- Vorbedingungen: CUPS/Samba-Printserver läuft.
- Schritte:
  1. Eine Druckerwarteschlange hinzufügen (via API/GUI oder `plugins/add_printer_queue`).
  2. Eine Testseite von einem Client drucken.
  3. `get_printer_list.py` und den IPP-Test `ipptool <uri> /usr/share/cups/ipptool/crx-get-printers.test` ausführen.
- Erwartetes Ergebnis: Warteschlange in CUPS und Samba angelegt; Druckjob läuft
  durch; IPP-Test liefert die Druckerliste.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-07 — Backup und Quota-Report
- Tier: 1 | Paket: cranix-base | Priorität: M
- Vorbedingungen: Backup-Ziel konfiguriert (`CRANIX_BACKUP*`).
- Schritte:
  1. `crx-backup -f -v` ausführen (oder den täglichen Cron abwarten).
  2. Backup-Ziel und Log prüfen.
  3. `crx-reportOverQuotaUsers` ausführen.
- Erwartetes Ergebnis: Backup läuft durch; Reports werden erzeugt; keine
  Fehler zu fehlendem Mount oder Berechtigungen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-08 — Klassen-Adhoc-Räume
- Tier: 1 | Paket: cranix-base | Priorität: M
- Vorbedingungen: `CRANIX_MAINTAIN_ADHOC_ROOM_FOR_CLASSES="yes"`.
- Schritte:
  1. `handle_class_adhoc_rooms.py` ausführen.
  2. Adhoc-Räume auflisten (`GET adhocrooms/all` oder GUI).
  3. Ein Zufallsgerät bei einem Schüler registrieren (`addDeviceToUser`).
- Erwartetes Ergebnis: Ein Adhoc-Raum pro Klasse mit konfigurierten
  Geräteanzahlen; registriertes Gerät erhält eine IP aus dem Raum-Netz.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-09 — Salt-State anwenden und Event-Plugins
- Tier: 1 | Paket: cranix-base | Priorität: H
- Vorbedingungen: Mindestens ein Salt-Minion registriert.
- Schritte:
  1. Einen State auf einen Minion anwenden via `crx_apply_states.py` (oder GUI).
  2. Einen Client starten und `crx_salt_event_watcher` beobachten.
  3. Verhalten der `plugins/clients/{start,present}` prüfen.
- Erwartetes Ergebnis: State wird angewendet; Computername gesetzt; Client-Plugins
  laufen; keine Fehler in `/var/adm/cranix/opentasks`.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-10 — Benutzerimport-Sonderfälle
- Tier: 2 | Paket: cranix-base | Priorität: M
- Vorbedingungen: Testserver (erzeugt Benutzer).
- Schritte:
  1. `datas/import-utf8-test.csv` importieren und Umlaut-/UTF-8-Behandlung prüfen.
  2. Mit `--identifier uid` und `--identifier sn-gn-bd` importieren.
  3. Mit `--test` (Dry-Run) importieren und prüfen, dass nichts geändert wird.
- Erwartetes Ergebnis: Namen/Umlaute bleiben erhalten; Duplikaterkennung
  funktioniert; Dry-Run ändert nichts.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-11 — Dateisystem- und Mail-Quota-Synchronisation
- Tier: 2 | Paket: cranix-base | Priorität: M
- Vorbedingungen: Quotas aktiviert.
- Schritte:
  1. Eine Quota mit `crx_set_quota.sh` setzen.
  2. `crx.syncFsQuotas` / `crx.syncMsQuotas` ausführen.
  3. Den Wert in GUI/API und auf der Platte prüfen (`xfs_quota`/`repquota`).
- Erwartetes Ergebnis: Quota angewendet und via API sichtbar; Over-Quota-Report
  wird ausgelöst.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-12 — Raumzugriff und Firewall
- Tier: 2 | Paket: cranix-base | Priorität: H
- Vorbedingungen: Raum mit Geräten vorhanden.
- Schritte:
  1. Mit `crx_manage_room_access.py` Drucken, Login, Portal, Proxy und direktes
     Internet für einen Raum sperren/erlauben.
  2. Von einem Gerät in diesem Raum testen (Surfen, Drucken, Anmelden).
  3. `firewall-cmd`/iptables-Regeln prüfen.
- Erwartetes Ergebnis: Zugriffsänderungen greifen sofort und konsistent; keine
  übriggebliebenen Regeln nach Reset (`--set_defaults`).
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-13 — DHCP-Konfiguration
- Tier: 2 | Paket: cranix-base | Priorität: M
- Vorbedingungen: DHCP-Dienst läuft.
- Schritte:
  1. Einen Raum mit DHCP-Parametern via API/GUI anlegen/ändern.
  2. DHCP neu starten und die gerenderte Konfiguration prüfen.
  3. Von einem Client ein Lease anfordern.
  4. `convert_dhcp_to_import.py` auf die aktuelle Konfiguration anwenden.
- Erwartetes Ergebnis: Konfiguration gültig; Client erhält das erwartete Lease;
  Konvertierung erzeugt eine gültige Import-CSV.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-14 — Zertifikate und Passwortdokumente
- Tier: 2 | Paket: cranix-base | Priorität: L
- Vorbedingungen: --
- Schritte:
  1. `create_server_certificates.sh` ausführen (Test-CA/Server/Proxy).
  2. `create_password_files.py` für eine Klasse ausführen.
  3. `check_password_complexity.sh` mit einem schwachen und einem starken Passwort ausführen.
- Erwartetes Ergebnis: Zertifikate erzeugt; PDF-Passwortblätter erstellt;
  schwache Passwörter je nach Richtlinie abgelehnt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-15 — Client-Steuerung und Wake-on-LAN
- Tier: 2 | Paket: cranix-base | Priorität: M
- Vorbedingungen: Ein laufender Client mit gültiger MAC.
- Schritte:
  1. `open`, `close`, `reboot`, `shutdown`, `wol` via `crx_control_client.sh` senden.
  2. `lockInput`/`logout` auslösen.
- Erwartetes Ergebnis: Jede Aktion erreicht den Client; Zustand in der GUI
  sichtbar.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### BASE-16 — Fileserver-Split / Import-Tools (optional)
- Tier: 2 | Paket: cranix-base | Priorität: L
- Vorbedingungen: Disponibler Server.
- Schritte:
  1. `pack_import.sh` / `read_installed_software.py` gegen einen Minion ausführen.
  2. Prüfen, dass der Softwarezustand via API registriert wird.
- Erwartetes Ergebnis: Tools laufen fehlerfrei durch und registrieren die
  erwarteten Daten.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

---

### cranix-java REST-API (`JAVA-`)

#### JAVA-01 — API-Dienst und Swagger
- Tier: 1 | Paket: cranix-java | Priorität: H
- Vorbedingungen: ENV-03 bestanden.
- Schritte:
  1. `systemctl status cranix-api` und `ss -ltnp | grep 9080`.
  2. `http://127.0.0.1:9080/api/swagger.json` abrufen.
  3. Den Admin-Host `/api` über Apache öffnen.
- Erwartetes Ergebnis: Dienst aktiv auf 127.0.0.1:9080; Swagger-JSON gültig;
  `/api` über den Reverse-Proxy erreichbar.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-02 — Sitzungslebenszyklus
- Tier: 1 | Paket: cranix-java | Priorität: H
- Vorbedingungen: JAVA-01 bestanden.
- Schritte:
  1. Eine Sitzung erzeugen (`POST /sessions/create`) mit gültigen Admin-Zugangsdaten.
  2. Einen geschützten Endpunkt mit dem Bearer-Token aufrufen.
  3. Die Sitzung löschen und erneut versuchen.
- Erwartetes Ergebnis: Gültiges Token gewährt Zugriff; nach Logout wird das
  Token abgelehnt (401).
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-03 — Token-Status-Semantik und Timeout
- Tier: 1 | Paket: cranix-java | Priorität: M
- Vorbedingungen: JAVA-02 bestanden.
- Schritte:
  1. `GET /sessions/byToken/{token}` für ein gültiges, abgelaufenes und ungültiges Token abfragen.
  2. Eine Sitzung länger als `CRANIX_SESSION_TIMEOUT` (Standard 90 min) idle lassen und erneut versuchen.
- Erwartetes Ergebnis: 401/402/403 wie dokumentiert; abgelaufene Sitzung wird
  bereinigt; Superuser sind vom Timeout ausgenommen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-04 — Localhost-Service-Token
- Tier: 1 | Paket: cranix-java | Priorität: H
- Vorbedingungen: JAVA-01 bestanden.
- Schritte:
  1. `crx_api.sh GET system/name` und `crx_api.sh GET users/uidsByRole/students` ausführen.
- Erwartetes Ergebnis: Aufrufe gelingen mit dem Localhost-Token ohne
  Benutzersitzung.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-05 — Kern-CRUD via API
- Tier: 1 | Paket: cranix-java | Priorität: H
- Vorbedingungen: JAVA-02 bestanden.
- Schritte:
  1. Erzeugen, Lesen, Ändern und Löschen: Benutzer, Gruppe/Klasse, Raum, Gerät,
     Drucker und Software-Eintrag.
  2. Prüfen, dass jedes in der GUI sichtbar ist.
- Erwartetes Ergebnis: Alle CRUD-Operationen liefern die dokumentierten
  Statuscodes und werden persistiert, je nach Fall nach Samba/CUPS repliziert.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-06 — ACL und negative Autorisierung
- Tier: 1 | Paket: cranix-java | Priorität: H
- Vorbedingungen: Ein Testlehrer- und ein Testschülerkonto.
- Schritte:
  1. Als Lehrer/Schüler anmelden und Admin-Endpunkte aufrufen (z. B. `POST /users/add`, `PUT /system/reboot`).
  2. Geschützte Endpunkte mit fehlendem/ungültigem Token aufrufen.
- Erwartetes Ergebnis: 403/401 je nach Fall; keine Rechteausweitung.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-07 — Datenbank-Schema-Migration nach dem Update
- Tier: 1 | Paket: cranix-java | Priorität: H
- Vorbedingungen: Update eingespielt; DB-Backup erstellt.
- Schritte:
  1. `cranix-api` neu starten.
  2. Journal auf EclipseLink-DDL-/Migrationsfehler prüfen.
  3. Einige Tabellen/Entitäten über die API lesen.
- Erwartetes Ergebnis: `create-or-extend-tables` läuft durch; bestehende Daten
  intakt; neue Spalten/Tabellen bei Bedarf ergänzt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-08 — Seiteneffekte beim Start
- Tier: 1 | Paket: cranix-java | Priorität: M
- Vorbedingungen: --
- Schritte:
  1. `cranix-api` neu starten.
  2. Prüfen, dass PPD-Neuerzeugung und Drucker-Setup liefen (`CreatePrinterPpd.pl`).
  3. Prüfen, dass die Localhost-Sitzungszeile existiert.
- Erwartetes Ergebnis: Seiteneffekte laufen fehlerfrei durch.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-09 — Zwei-Faktor-Authentifizierung (falls `CRX_2FA` aktiviert)
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: `/etc/sysconfig/CRX_2FA` existiert; Testbenutzer mit `2fa.use`.
- Schritte:
  1. Anmelden → PIN-Aufforderung erwartet; `POST /2fas/sendpin`, dann `POST /2fas/checkpin`.
  2. Falsche PIN versuchen; vor Abschluss der OTP einen anderen Endpunkt aufrufen.
- Erwartetes Ergebnis: Zugriff erst nach gültiger PIN; falsche PIN abgelehnt;
  andere Aufrufe blockiert bis OTP erfolgreich.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-10 — Bedingte Ressourcen vorhanden/nicht vorhanden
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: Kontrolle über `/etc/sysconfig/CRX_*`-Dateien.
- Schritte:
  1. Mit vorhandenen `CRX_MDM`, `CRX_PTM`, `CRX_CAL`, `CRX_ID` deren Endpunkte aufrufen.
  2. Dateien entfernen, API neu starten und Swagger/Endpunkte erneut prüfen.
- Erwartetes Ergebnis: Ressourcen nur registriert, wenn die Marker-Datei
  existiert; sauberer Start in beiden Fällen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-11 — Self-Management-Endpunkte
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: Normale Benutzersitzung und ein registriertes Gerät.
- Schritte:
  1. `/selfmanagement/me`, `/modify`, `/devices`, `/myFiles`, `/vpn/*` aufrufen.
  2. Ein eigenes Gerät hinzufügen und entfernen.
- Erwartetes Ergebnis: Ein Benutzer kann nur eigene Daten verwalten;
  RADIUS-Geräteregistrierung funktioniert von localhost.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-12 — Education / Raumsteuerung
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: Lehrer-Sitzung; Raum mit Geräten.
- Schritte:
  1. `/education/rooms/{id}/{action}` nutzen (open/close/lock/logout/projector).
  2. Upload/Collect und applyAction auf Gruppen/Benutzer/Geräte nutzen.
  3. Die Action-Whitelists aus `cranix-api.properties` testen.
- Erwartetes Ergebnis: Aktionen treffen die richtigen Ziele; nicht erlaubte
  Aktionen werden abgelehnt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-13 — Software-Installationen und Lizenzen
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: Mindestens ein Softwarepaket verfügbar.
- Schritte:
  1. Eine Installation/ein Set erstellen und Geräten/Räumen zuweisen.
  2. Status, Lizenzen und `saveState`/`applyState` prüfen.
- Erwartetes Ergebnis: Installationszustand korrekt verfolgt; Lizenzen
  durchgesetzt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-14 — Dokumente
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: Ein Benutzer mit Dokumentrechten.
- Schritte:
  1. Ein Dokument erstellen, Versionen hinzufügen, eine Version wiederherstellen.
  2. Ordner/Unterordner erstellen, ein Dokument verschieben, Rechte setzen/entziehen.
  3. Dokumente durchsuchen.
- Erwartetes Ergebnis: Versionen und Rechte funktionieren korrekt; nur
  autorisierte Benutzer sehen Dokumente.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-15 — Kalender, Kurse, PTM
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: `CRX_CAL` / `CRX_PTM` je nach Fall.
- Schritte:
  1. Ein Kalenderereignis erstellen; filtern; syncen.
  2. Einen Kurs mit Terminen erstellen und an-/abmelden.
  3. Eine PTM-Sitzung erstellen und einen Elternteil registrieren.
- Erwartetes Ergebnis: Entitäten erstellt und sichtbar; Registrierungsabläufe
  funktionieren.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### JAVA-16 — System-Administrationsendpunkte
- Tier: 2 | Paket: cranix-java | Priorität: M
- Vorbedingungen: Admin-Sitzung.
- Schritte:
  1. `/system/status`, `/system/diskStatus`, `/system/services` lesen.
  2. Firewall-Service-/Regel-Endpunkte und DNS-Record-Endpunkte testen.
  3. Proxy-/Unbound-Endpunkte testen.
  4. Einen nicht-destruktiven Job auslösen und `/system/jobs/{id}` prüfen.
- Erwartetes Ergebnis: Konfigurationsänderungen angewendet; Jobs aufgezeichnet;
  keine API-Fehler.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

---

### cranix-web GUI (`WEB-`) und Mobile-App (`MOB-`)

#### WEB-01 — Login-Seite laden
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Apache-Proxy konfiguriert.
- Schritte:
  1. `https://admin.<domain>/` und die Schulportal-URL öffnen.
  2. Prüfen, dass der Institutname angezeigt wird.
- Erwartetes Ergebnis: Login-Seite rendert ohne Konsolenfehler; Servername
  angezeigt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-02 — Web-Login / Logout
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Admin-Zugangsdaten.
- Schritte:
  1. Als Admin anmelden.
  2. Abmelden.
  3. Mit falschem Passwort anmelden.
- Erwartetes Ergebnis: Korrektes Login führt zur Startseite; Logout löscht die
  Sitzung; falsches Passwort zeigt einen Fehler und meldet nicht an.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-03 — Menü gefiltert nach Rolle/ACL
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Admin-, Lehrer-, Schülerkonten.
- Schritte:
  1. Mit jeder Rolle anmelden und das Seitenmenü prüfen.
  2. Als Schüler eine Admin-URL direkt öffnen.
- Erwartetes Ergebnis: Menü zeigt nur erlaubte Einträge; Direktzugriff wird vom
  Route-Guard blockiert.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-04 — Benutzerverwaltung
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Admin-Sitzung.
- Schritte:
  1. Benutzer öffnen; suchen, anlegen, bearbeiten und löschen.
  2. Einen Benutzerimport ausführen und die Importliste prüfen.
- Erwartetes Ergebnis: Änderungen werden korrekt gespeichert und
  serverseitig widergespiegelt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-05 — Gruppen / Klassen
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Admin-Sitzung.
- Schritte:
  1. Gruppen öffnen; eine Klasse anlegen; Mitglieder hinzufügen/entfernen.
- Erwartetes Ergebnis: Mitgliedschaft und Klassenverzeichnisse aktualisieren
  korrekt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-06 — Räume und Zugriffskontrolle
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Ein Raum mit Geräten.
- Schritte:
  1. Räume öffnen; Geräte und verfügbare IPs prüfen.
  2. Zugriffsstatus (Drucken/Login/Internet/Portal) für den Raum ändern.
- Erwartetes Ergebnis: Zugriffsumschaltungen werden gespeichert und wirksam.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-07 — Geräte
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Ein Gerät existiert.
- Schritte:
  1. Geräte öffnen; anzeigen, Homework-Konfiguration bearbeiten und eine Aktion anwenden.
- Erwartetes Ergebnis: Gerätedaten und Aktionen funktionieren.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-08 — Drucker
- Tier: 1 | Paket: cranix-web | Priorität: M
- Vorbedingungen: Ein Drucker existiert.
- Schritte:
  1. Drucker öffnen; aktivieren/deaktivieren, zurücksetzen und Treiber setzen.
- Erwartetes Ergebnis: Druckerstatusänderungen spiegeln sich in CUPS wider.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-09 — Systemstatus und Dienste
- Tier: 1 | Paket: cranix-web | Priorität: M
- Vorbedingungen: Admin-Sitzung.
- Schritte:
  1. System → Status und Dienste öffnen.
- Erwartetes Ergebnis: Status/Disk/Dienste rendern mit korrekten Werten.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-10 — Profil "Myself" und Passwortänderung
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Ein Benutzer, der das Passwort ändern darf.
- Schritte:
  1. Profil → Myself öffnen; das Passwort ändern; mit dem neuen Passwort anmelden.
- Erwartetes Ergebnis: Passwortänderung erfolgreich und neues Passwort
  funktioniert.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-11 — Softwarepakete, Sets und Lizenzen
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: Softwarepakete heruntergeladen.
- Schritte:
  1. Softwares → Status/Packages/Sets öffnen; ein Set erstellen; einem Raum zuweisen.
- Erwartetes Ergebnis: Sets und Zuweisungen werden gespeichert und via API
  widergespiegelt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-12 — Sicherheitsseiten
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: Admin-Sitzung.
- Schritte:
  1. Security → Firewall, Proxy, Unbound, Access, Access-Log öffnen; eine Änderung vornehmen.
- Erwartetes Ergebnis: Änderungen werden angewendet und sind serverseitig
  sichtbar.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-13 — Dokumente
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: Ein Benutzer mit Dokumentrechten.
- Schritte:
  1. Ordner/Dokument erstellen; Inhalt hochladen; eine Version hinzufügen; Rechte setzen.
- Erwartetes Ergebnis: Dokumentbaum, Versionen und Rechte funktionieren in der
  GUI.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-14 — Meine Gruppen (Lehrer)
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: Lehrer mit Klassen.
- Schritte:
  1. Meine Gruppen öffnen; Mitglieder anzeigen; Anwesenheit erfassen; Notiz/Note hinzufügen.
- Erwartetes Ergebnis: Lehrer sieht nur eigene Klassen; Änderungen werden
  gespeichert.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-15 — Education / Unterricht
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: Lehrer-Sitzung.
- Schritte:
  1. Lessons → Tests, Challenges, Room control, Courses, PTM öffnen.
  2. In jedem Tab eine Erstellen-/Bearbeiten-Aktion ausführen.
- Erwartetes Ergebnis: Jeder Tab funktioniert; Raumsteuerung erreicht die Geräte.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### WEB-16 — Informationen / Ankündigungen
- Tier: 2 | Paket: cranix-web | Priorität: L
- Vorbedingungen: Admin-Sitzung.
- Schritte:
  1. Eine Ankündigung und eine Aufgabe erstellen; als gesehen markieren; Antworten ansehen.
- Erwartetes Ergebnis: Inhalte erstellt und für die Zielgruppe sichtbar.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### MOB-01 — Mobile-Login und gespeicherte Server
- Tier: 1 | Paket: cranix-web | Priorität: H
- Vorbedingungen: Mobiler Browser / PWA / iOS-Build.
- Schritte:
  1. Den Mobile-/PWA-Eingang (`mobillogin`) öffnen.
  2. Einen gespeicherten Server hinzufügen, bearbeiten und löschen; dann anmelden.
- Erwartetes Ergebnis: Serverliste bleibt in `localStorage` erhalten; Login
  funktioniert.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### MOB-02 — PWA-Standalone-Verhalten
- Tier: 1 | Paket: cranix-web | Priorität: M
- Vorbedingungen: App zum Home-Bildschirm hinzufügen.
- Schritte:
  1. Vom Home-Bildschirm starten (standalone).
  2. Prüfen, dass der Mobile-Login geöffnet wird, nicht der Desktop-Login.
- Erwartetes Ergebnis: Korrekte Einstiegsroute im installierten Modus.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### MOB-03 — Oberflächensprache EN/DE
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: --
- Schritte:
  1. Die Sprache auf mehreren Seiten zwischen Englisch und Deutsch umschalten.
- Erwartetes Ergebnis: Alle sichtbaren Texte wechseln; keine fehlenden
  Übersetzungen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### MOB-04 — Kamerabasiertes Ausweisfoto (iOS)
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: iOS-Build mit Kamera-Berechtigung.
- Schritte:
  1. Profil → Myself → Ausweisfoto aufnehmen/auswählen.
- Erwartetes Ergebnis: Foto erfolgreich aufgenommen/hochgeladen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### MOB-05 — VPN-Konfiguration herunterladen
- Tier: 2 | Paket: cranix-web | Priorität: L
- Vorbedingungen: VPN aktiviert.
- Schritte:
  1. Profil → My VPN; die Konfiguration/den Installer für die Plattform herunterladen.
- Erwartetes Ergebnis: Korrekte Datei heruntergeladen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### MOB-06 — 2FA-PIN-Dialog
- Tier: 2 | Paket: cranix-web | Priorität: M
- Vorbedingungen: 2FA für den Benutzer aktiviert.
- Schritte:
  1. In der App anmelden; die PIN eingeben; eine falsche PIN testen.
- Erwartetes Ergebnis: Korrekte PIN meldet an; falsche PIN wird abgelehnt.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### MOB-07 — Druck-/Screenshot-Seiten
- Tier: 2 | Paket: cranix-web | Priorität: L
- Vorbedingungen: Eine Druck-/Report-Aktion verfügbar.
- Schritte:
  1. Einen Ausweis-/Reportdruck auslösen (öffnet `printPage`).
  2. Eine Raum-Screenshot-Ansicht auslösen.
- Erwartetes Ergebnis: Inhalt rendert und der Druckdialog öffnet sich.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

---

### Paketübergreifende Regression (`REG-`)

#### REG-01 — Kombinierter Update-Smoke-Test
- Tier: 1 | Paket: alle | Priorität: H
- Vorbedingungen: Alle drei Pakete gemeinsam aktualisiert.
- Schritte:
  1. Alle Tier-1-Fälle erneut ausführen.
- Erwartetes Ergebnis: Alle Tier-1-Fälle bestehen.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### REG-02 — Log-Prüfung
- Tier: 1 | Paket: alle | Priorität: H
- Vorbedingungen: Testlauf abgeschlossen.
- Schritte:
  1. `journalctl -u cranix-api`, `/var/log/CRANIX-UPDATE-*`, Samba-Logs und `/var/adm/cranix/opentasks` prüfen.
  2. Die Browser-Konsole auf den Hauptseiten prüfen.
- Erwartetes Ergebnis: Keine unerwarteten Fehler/Ausnahmen/Tracebacks.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### REG-03 — Version- und Cache-Konsistenz
- Tier: 1 | Paket: cranix-web | Priorität: M
- Vorbedingungen: --
- Schritte:
  1. Die Web-GUI nach dem Update hart neu laden.
  2. Prüfen, dass sich die geladenen Asset-Hashes/Version geändert haben und
     keine veralteten gecachten Chunks vorliegen.
- Erwartetes Ergebnis: Neues Frontend wird ausgeliefert; keine
  "chunk load failed"-Fehler.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

#### REG-04 — End-to-End-Szenario Schultag
- Tier: 1 | Paket: alle | Priorität: H
- Vorbedingungen: Testbenutzer/-geräte/-räume vorhanden.
- Schritte:
  1. Lehrer öffnet einen Raum; Schüler melden sich an; ein Schüler druckt.
  2. Schüler gibt eine Datei ab; Lehrer sammelt sie ein.
  3. Admin prüft Sitzungs- und Gerätezustand in der GUI.
- Erwartetes Ergebnis: Der vollständige typische Workflow gelingt über alle drei
  Pakete hinweg.
- Ergebnis: [ ] Bestanden [ ] Fehlgeschlagen [ ] N/A   Notizen: ______

---

## 8. Abbruchkriterien

- Alle **Tier-1**-Fälle bestehen (oder Abweichungen werden vom Maintainer
  ausdrücklich akzeptiert).
- Kein neuer Fehler in `ENV-03`, `JAVA-06` (ACL) oder `REG-02` (Logs).
- Tier-2-Fehler sind als Defekte mit Reproduktionsschritten dokumentiert.
- Die ausgefüllte Umgebungstabelle (2.1), die Ergebnisse und Log-Auszüge werden
  an den Maintainer zurückgegeben.

## 9. Bericht

Das ausgefüllte Dokument mit folgenden Inhalten zurückgeben:

1. Die Umgebungstabelle aus Abschnitt 2.1.
2. Bestanden/Fehlgeschlagen/N-A für jeden ausgeführten Fall.
3. Zu jedem Fehler: genaue Befehle/Schritte, beobachtetes Ergebnis, erwartetes
   Ergebnis, relevante Log-Auszüge und ob er das Release blockiert.

## 10. Bekannte Risikobereiche (aus der Code-Prüfung — besonders sorgfältig prüfen)

Diese Bereiche sind bekanntermaßen fragil oder häufig betroffen; Fehler hier
haben hohe Priorität:

1. **DHCP über Kea** — `setup/scripts/setup-kea.py` scheint Syntaxfehler zu
   enthalten; den Kea-Pfad explizit validieren (BASE-13).
2. **Bedingte Java-Ressourcen** — 2FA-, MDM-, PTM-, Kalender- und
   ID-Request-Endpunkte werden nur registriert, wenn die passende
   `/etc/sysconfig/CRX_*`-Datei existiert; beide Fälle testen (JAVA-10).
3. **Frontend-Build-Ersetzung** — `cranix-web` ersetzt in Produktion
   `utils.service.ts` durch `utils.service-notest.ts`; ein Entwicklungs-Build
   kann still auf einen fest verdrahteten Server zeigen. Prüfen, welcher Build
   getestet wird (WEB-01).
4. **Mobile-Branding/-Konfiguration** — `capacitor.config.json` nutzt noch
   `appId: io.ionic.starter`, und es gibt kein eingechecktes Android-Projekt;
   das tatsächlich ausgelieferte iOS-/PWA-Build prüfen (MOB-01, MOB-02).
5. **Firewall-/Zugriffskonsistenz** — Legacy-`iptables`/`CRANIX_USE_TFK`-Skripte
   und `crx_manage_room_access.py` bestehen parallel; auf übriggebliebene Regeln
   prüfen (BASE-12).
6. **Klassen-Adhoc-Räume** — werden beim Import erzeugt, wenn
   `CRANIX_MAINTAIN_ADHOC_ROOM_FOR_CLASSES="yes"`; prüfen, dass Geräte-IPs zum
   Raum-Netz passen (BASE-08).
7. **Datenbankmigration** — EclipseLink `create-or-extend-tables` läuft beim
   Start; eine fehlgeschlagene Migration kann Daten beschädigen. Immer zuerst
   ein Backup erstellen (JAVA-07).
