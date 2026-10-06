# CRANIX Server — QA Test Plan

- Version: 1.0
- Applies to packages: `cranix-base`, `cranix-java`, `cranix-web` (cranix-mobile-app)
- Audience: human test engineer executing a manual test run on a CRANIX test server
- German version: [QA-TESTPLAN.de.md](QA-TESTPLAN.de.md)

---

## 1. Purpose and scope

This plan verifies the quality of a CRANIX server after the regularly updated
packages **`cranix-base`**, **`cranix-java`** and **`cranix-web`**
(cranix-mobile-app) have been installed. It is a **human-executed, checkbox-based
regression test** intended to catch regressions introduced by a package update.

It covers:

| Package | What is tested |
|---|---|
| `cranix-base` | Backend scripts, tools, plugins, setup/update, Samba/AD, DNS/DHCP, printing, quota, backup, import/export, adhoc rooms, Salt |
| `cranix-java` | REST API (`cranix-api` on port 9080), database migration, authentication/ACL, all major API areas |
| `cranix-web` | Web admin GUI (Angular/Ionic) and mobile/PWA app: login, menus, all major screens |

It does **not** cover: OS/Kernel patches, third-party packages outside CRANIX,
Cephalix cloud internals, or hardware/network infrastructure.

---

## 2. Test environment

- A working, already-installed and configured **CRANIX test server** is used
  (test does not reinstall the appliance).
- Testing is **update-in-place**: the package(s) under test are installed on the
  running server, then the test cases below are executed.
- Recommended: a **disposable/snapshot-capable** test server, because several
  Tier 2 cases are destructive (delete users/rooms/devices, wipe class dirs,
  reinstall services).
- Test client: a machine on the school network with a current browser (Chrome/
  Firefox) and, for mobile cases, an iOS device or the browser's mobile/PWA mode.

### 2.1 Record the environment before starting

| Item | Value |
|---|---|
| Server hostname / IP | |
| Server OS version (`cat /etc/os-release`) | |
| `cranix-base` version (`rpm -q cranix-base`) | |
| `cranix-java` version (`rpm -q cranix-java`) | |
| `cranix-web` version (`rpm -q cranix-web`) | |
| Date/time of test run | |
| Tester | |

---

## 3. Preconditions and safety

1. Take a **backup/snapshot** before applying updates (`crx-backup -f` or VM
   snapshot). Confirm the update log exists afterwards
   (`/var/log/CRANIX-UPDATE-*`).
2. Confirm the following are available: an `admin` session, a test student, a
   test teacher, at least one room and one hardware configuration.
3. Optional but recommended for diagnosis: set `CRANIX_DEBUG="yes"` in
   `/etc/sysconfig/cranix`.
4. The setup scripts `bin/00300-setup-class-adhoc-rooms.sh` and
   `bin/00310-setup-teachers-adhoc-rooms.sh` create many random devices and rooms
   — run them only on a disposable test server.
5. After the run, remove `CRANIX_DEBUG` again and restore/delete test data.

---

## 4. Test data setup

The `cranix-tests` package provides generators. Everything is installed under
`/usr/share/cranix/tests` and driven by `tests/cranix-full-test.sh`.

```bash
# Run all setup phases in numbered order
/usr/share/cranix/tests/tests/cranix-full-test.sh
```

| Script | Purpose |
|---|---|
| `bin/00100-import-users.sh` | Imports generated students and teachers |
| `bin/00200-setup-radius.sh` | Installs `cranix-radius`, enables device registration |
| `bin/00300-setup-class-adhoc-rooms.sh` | Creates class adhoc rooms + student devices |
| `bin/00310-setup-teachers-adhoc-rooms.sh` | Creates teacher adhoc room + devices |
| `helper/create-students-import.sh` | Generates the student CSV (4 classes × 3 sections × 10) |
| `helper/create-teachers-import.sh` | Generates the teacher CSV (15 teachers) |
| `helper/create-random-mac.sh` | Random MAC address for device registration |
| `helper/functions.sh` | `check_result` helper for API JSON results |
| `datas/import-utf8-test.csv` | UTF-8 / umlaut import fixture |

Counts can be overridden before running, e.g.:

```bash
export CLASS_COUNT=1 STUDENT_COUNT=3 TEACHER_COUNT=2
```

---

## 5. Tier definitions

- **Tier 0 — Environment:** must always be executed before any other case.
- **Tier 1 — Smoke:** the critical path. Execute after **every** package update.
  Target duration ~1 hour. All Tier 1 cases must pass.
- **Tier 2 — Extended:** deeper and destructive coverage. Execute before a
  release or when a Tier 1 case fails and needs narrowing down. May take a
  half day or more.

Priority legend: **H** = high, **M** = medium, **L** = low.

---

## 6. Test case template

Each case uses this structure:

```
### ID — Title
- Tier: 1 | Package: cranix-base | Priority: H
- Preconditions: ...
- Steps:
  1. ...
- Expected result: ...
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: __________
```

Record the outcome directly in this document (or a copy of it) and return it to
the maintainer together with the environment table from section 2.1.

---

## 7. Test case catalog

### Tier 0 — Environment (`ENV-`)

#### ENV-01 — Record versions and apply the update
- Tier: 0 | Package: all | Priority: H
- Preconditions: Backup/snapshot taken.
- Steps:
  1. Fill in section 2.1.
  2. Update the package(s) under test (`zypper -n up <package>` or `crx_update.sh`).
  3. Note the resulting versions and the update log file.
- Expected result: Update completes without unresolved dependencies; new
  versions are recorded; no `error:`/`failed` lines in the update log.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### ENV-02 — Configuration merge after update
- Tier: 0 | Package: cranix-base | Priority: H
- Preconditions: Update applied.
- Steps:
  1. Inspect `/etc/sysconfig/cranix` for newly introduced `CRANIX_*` keys.
  2. If needed run `fix-sysconfig.py` and re-inspect.
- Expected result: New keys are present with sensible defaults; existing local
  values are preserved.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### ENV-03 — Service health
- Tier: 0 | Package: cranix-base, cranix-java | Priority: H
- Preconditions: Update applied.
- Steps:
  1. Run `check_services.sh` and inspect the JSON.
  2. Check `systemctl status cranix-api salt-master samba-ad samba-fileserver samba-printserver sssd chronyd apache2`.
  3. Check `/var/adm/cranix/opentasks` is empty.
- Expected result: All monitored services active; no unexpected failed units;
  no stuck open tasks.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### ENV-04 — Post-update reboot / persistence
- Tier: 0 | Package: all | Priority: M
- Preconditions: Update applied.
- Steps:
  1. Reboot the server.
  2. After boot, repeat ENV-03 and log in to the web GUI.
- Expected result: Everything comes back automatically; no manual restart needed.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

---

### cranix-base (`BASE-`)

#### BASE-01 — Samba AD and DNS host records
- Tier: 1 | Package: cranix-base | Priority: H
- Preconditions: ENV-03 passed; admin access to server console.
- Steps:
  1. Add a test host (`crx_add_host.sh <ip> <name> <mac>`).
  2. Resolve name → IP (forward) and IP → name (reverse) on a client.
  3. Rename and delete the host.
- Expected result: Forward and reverse records are created, updated and removed;
  name resolves from a network client.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-02 — Bulk import students
- Tier: 1 | Package: cranix-base | Priority: H
- Preconditions: Student CSV generator available.
- Steps:
  1. Run `helper/create-students-import.sh > /tmp/students.csv`.
  2. Run `crx_import_user_list.py --input /tmp/students.csv --role students --full --appendBirthdayToPassword --appendClassToPassword --cleanClassDirs`.
  3. Check `/home/groups/<class>` exists with correct ownership/ACLs.
- Expected result: Users and classes created; class directories exist; no
  `opentasks` remain; UIDs/group membership correct in Samba.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-03 — Bulk import teachers
- Tier: 1 | Package: cranix-base | Priority: H
- Preconditions: BASE-02 passed.
- Steps:
  1. Run `helper/create-teachers-import.sh > /tmp/teachers.csv`.
  2. Run `crx_import_user_list.py --input /tmp/teachers.csv --role teachers --full`.
- Expected result: Teachers created with role `teachers`; can be assigned to
  classes; no errors.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-04 — Export users
- Tier: 1 | Package: cranix-base | Priority: M
- Preconditions: BASE-02/03 passed.
- Steps:
  1. Run `crx_export_users.py students` (and `teachers`).
  2. Inspect the produced CSV.
- Expected result: All imported users appear with correct `uid;givenName;surName;classes;birthDay`.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-05 — Home and group directory reset
- Tier: 1 | Package: cranix-base | Priority: M
- Preconditions: Test users exist.
- Steps:
  1. Change a file/ACL in a user home and a group dir.
  2. Run `crx_reset_home.sh` and `crx_reset_groups.sh`.
  3. Re-check the home and group dirs.
- Expected result: Homes/groups restored from templates with correct ACLs;
  permissions are consistent for student/teacher roles.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-06 — Printer queue creation and CUPS
- Tier: 1 | Package: cranix-base | Priority: H
- Preconditions: CUPS/Samba printserver running.
- Steps:
  1. Add a printer queue (via API/GUI or `plugins/add_printer_queue`).
  2. Print a test page from a client.
  3. Run `get_printer_list.py` and the IPP test `ipptool <uri> /usr/share/cups/ipptool/crx-get-printers.test`.
- Expected result: Queue created in CUPS and Samba; print job completes; IPP
  test returns the printer list.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-07 — Backup and quota reporting
- Tier: 1 | Package: cranix-base | Priority: M
- Preconditions: Backup target configured (`CRANIX_BACKUP*`).
- Steps:
  1. Run `crx-backup -f -v` (or wait for the daily cron).
  2. Inspect the backup target and log.
  3. Run `crx-reportOverQuotaUsers`.
- Expected result: Backup completes; reports are generated; no missing-mount or
  permission errors.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-08 — Class adhoc rooms
- Tier: 1 | Package: cranix-base | Priority: M
- Preconditions: `CRANIX_MAINTAIN_ADHOC_ROOM_FOR_CLASSES="yes"`.
- Steps:
  1. Run `handle_class_adhoc_rooms.py`.
  2. List adhoc rooms (`GET adhocrooms/all` or GUI).
  3. Register a random device to a student (`addDeviceToUser`).
- Expected result: One adhoc room per class with configured device counts;
  registered device receives an IP from the room network.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-09 — Salt state apply and event plugins
- Tier: 1 | Package: cranix-base | Priority: H
- Preconditions: At least one Salt minion registered.
- Steps:
  1. Apply a state to a minion via `crx_apply_states.py` (or GUI).
  2. Start/present a client and observe `crx_salt_event_watcher`.
  3. Check `plugins/clients/{start,present}` behavior.
- Expected result: State applies; computer name set; client plugins run; no
  failures in `/var/adm/cranix/opentasks`.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-10 — User import edge cases
- Tier: 2 | Package: cranix-base | Priority: M
- Preconditions: Test server (creates users).
- Steps:
  1. Import `datas/import-utf8-test.csv` and verify umlauts/UTF-8 handling.
  2. Import with `--identifier uid` and `--identifier sn-gn-bd`.
  3. Import with `--test` (dry run) and confirm no changes.
- Expected result: Names/umlauts preserved; duplicate detection works; dry run
  changes nothing.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-11 — Filesystem and mail quota sync
- Tier: 2 | Package: cranix-base | Priority: M
- Preconditions: Quotas enabled.
- Steps:
  1. Set a quota with `crx_set_quota.sh`.
  2. Run `crx.syncFsQuotas` / `crx_manage_room_access`-independent `crx.syncMsQuotas`.
  3. Check the value in the GUI/API and on disk (`xfs_quota`/`repquota`).
- Expected result: Quota applied and visible via API; over-quota report triggers.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-12 — Room access and firewall
- Tier: 2 | Package: cranix-base | Priority: H
- Preconditions: Room with devices exists.
- Steps:
  1. Use `crx_manage_room_access.py` to deny/allow printing, login, portal,
     proxy and direct internet for a room.
  2. Test from a device in that room (browse, print, log on).
  3. Check `firewall-cmd`/iptables rules.
- Expected result: Access changes take effect immediately and consistently; no
  leftover rules after reset (`--set_defaults`).
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-13 — DHCP configuration
- Tier: 2 | Package: cranix-base | Priority: M
- Preconditions: DHCP service running.
- Steps:
  1. Create/modify a room with DHCP parameters via API/GUI.
  2. Restart DHCP and verify the rendered config.
  3. Request a lease from a client.
  4. Run `convert_dhcp_to_import.py` on the current config.
- Expected result: Config is valid; client gets the expected lease; conversion
  produces a valid import CSV.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-14 — Certificates and password documents
- Tier: 2 | Package: cranix-base | Priority: L
- Preconditions: --
- Steps:
  1. Run `create_server_certificates.sh` (test CA/server/proxy).
  2. Run `create_password_files.py` for a class.
  3. Run `check_password_complexity.sh` with a weak and a strong password.
- Expected result: Certificates generated; PDF password sheets created; weak
  passwords rejected according to policy.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-15 — Client control and wake-on-LAN
- Tier: 2 | Package: cranix-base | Priority: M
- Preconditions: A running client with a valid MAC.
- Steps:
  1. Send `open`, `close`, `reboot`, `shutdown`, `wol` via `crx_control_client.sh`.
  2. Trigger `lockInput`/`logout`.
- Expected result: Each action reaches the client; state is reflected in the GUI.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### BASE-16 — Fileserver split / import tools (optional)
- Tier: 2 | Package: cranix-base | Priority: L
- Preconditions: Disposable server.
- Steps:
  1. Run `pack_import.sh` / `read_installed_software.py` against a minion.
  2. Verify software state registered via API.
- Expected result: Tools complete without errors and register expected data.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

---

### cranix-java REST API (`JAVA-`)

#### JAVA-01 — API service and Swagger
- Tier: 1 | Package: cranix-java | Priority: H
- Preconditions: ENV-03 passed.
- Steps:
  1. `systemctl status cranix-api` and `ss -ltnp | grep 9080`.
  2. Fetch `http://127.0.0.1:9080/api/swagger.json`.
  3. Open the admin host `/api` through Apache.
- Expected result: Service active on 127.0.0.1:9080; Swagger JSON valid; `/api`
  reachable through the reverse proxy.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-02 — Session lifecycle
- Tier: 1 | Package: cranix-java | Priority: H
- Preconditions: JAVA-01 passed.
- Steps:
  1. Create a session (`POST /sessions/create`) with valid admin credentials.
  2. Call a protected endpoint with the Bearer token.
  3. Delete the session and retry.
- Expected result: Valid token grants access; after logout the token is
  rejected (401).
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-03 — Token status semantics and timeout
- Tier: 1 | Package: cranix-java | Priority: M
- Preconditions: JAVA-02 passed.
- Steps:
  1. Query `GET /sessions/byToken/{token}` for a valid, expired and invalid token.
  2. Leave a session idle beyond `CRANIX_SESSION_TIMEOUT` (default 90 min) and retry.
- Expected result: 401/402/403 returned as documented; expired session is
  cleaned up; superusers are exempt from timeout.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-04 — Localhost service token
- Tier: 1 | Package: cranix-java | Priority: H
- Preconditions: JAVA-01 passed.
- Steps:
  1. Run `crx_api.sh GET system/name` and `crx_api.sh GET users/uidsByRole/students`.
- Expected result: Calls succeed using the localhost token without a user session.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-05 — Core CRUD via API
- Tier: 1 | Package: cranix-java | Priority: H
- Preconditions: JAVA-02 passed.
- Steps:
  1. Create, read, modify and delete: a user, a group/class, a room, a device,
     a printer and a software entry.
  2. Confirm each is reflected in the GUI.
- Expected result: All CRUD operations return the documented status codes and
  are persisted/replicated to Samba/CUPS as appropriate.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-06 — ACL and negative authorization
- Tier: 1 | Package: cranix-java | Priority: H
- Preconditions: A teacher and a student test account.
- Steps:
  1. Log in as teacher/student and call admin-only endpoints (e.g. `POST /users/add`,
     `PUT /system/reboot`).
  2. Call protected endpoints with a missing/invalid token.
- Expected result: 403/401 as appropriate; no privilege escalation.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-07 — Database schema migration after update
- Tier: 1 | Package: cranix-java | Priority: H
- Preconditions: Update applied; DB backup taken.
- Steps:
  1. Restart `cranix-api`.
  2. Inspect the journal for EclipseLink DDL/migration errors.
  3. Read a few tables/entities through the API.
- Expected result: `create-or-extend-tables` completes; existing data intact;
  new columns/tables added as needed.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-08 — Startup side effects
- Tier: 1 | Package: cranix-java | Priority: M
- Preconditions: --
- Steps:
  1. Restart `cranix-api`.
  2. Verify PPD regeneration and printer setup ran (`CreatePrinterPpd.pl`).
  3. Verify the localhost session row exists.
- Expected result: Side effects complete without errors.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-09 — Two-factor authentication (if `CRX_2FA` enabled)
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: `/etc/sysconfig/CRX_2FA` exists; test user with `2fa.use`.
- Steps:
  1. Log in → expect PIN prompt; `POST /2fas/sendpin` then `POST /2fas/checkpin`.
  2. Try a wrong PIN; try accessing another endpoint before completing OTP.
- Expected result: Access granted only after valid PIN; wrong PIN rejected;
  other calls blocked until OTP succeeds.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-10 — Conditional resources present/absent
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: Control over `/etc/sysconfig/CRX_*` files.
- Steps:
  1. With `CRX_MDM`, `CRX_PTM`, `CRX_CAL`, `CRX_ID` present, call their endpoints.
  2. Remove the files, restart the API, and re-check Swagger/endpoints.
- Expected result: Resources registered only when the marker file exists; clean
  startup in both cases.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-11 — Self-management endpoints
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: A normal user session and a registered device.
- Steps:
  1. Call `/selfmanagement/me`, `/modify`, `/devices`, `/myFiles`, `/vpn/*`.
  2. Add and remove an own device.
- Expected result: A user can only manage their own data; RADIUS device add works
  from localhost.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-12 — Education / room control
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: Teacher session; room with devices.
- Steps:
  1. Use `/education/rooms/{id}/{action}` (open/close/lock/logout/projector).
  2. Use upload/collect and applyAction on groups/users/devices.
  3. Test the action whitelists from `cranix-api.properties`.
- Expected result: Actions apply to the correct targets; disallowed actions are
  rejected.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-13 — Software installations and licenses
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: At least one software package available.
- Steps:
  1. Create an installation/set and assign devices/rooms.
  2. Check status, licenses and `saveState`/`applyState`.
- Expected result: Installation state tracked correctly; licenses enforced.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-14 — Documents
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: A user with document rights.
- Steps:
  1. Create a document, add versions, restore a version.
  2. Create folders/subfolders, move a document, set/revoke rights.
  3. Search documents.
- Expected result: Versions and rights behave correctly; only authorized users
  see documents.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-15 — Calendar, courses, PTM
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: `CRX_CAL` / `CRX_PTM` as applicable.
- Steps:
  1. Create a calendar event; filter; sync.
  2. Create a course with appointments and register/unregister.
  3. Create a PTM session and register a parent.
- Expected result: Entities created and visible; registration flows work.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### JAVA-16 — System administration endpoints
- Tier: 2 | Package: cranix-java | Priority: M
- Preconditions: Admin session.
- Steps:
  1. Read `/system/status`, `/system/diskStatus`, `/system/services`.
  2. Exercise firewall services/rule endpoints and DNS record endpoints.
  3. Exercise proxy/unbound endpoints.
  4. Trigger a non-destructive job and inspect `/system/jobs/{id}`.
- Expected result: Config changes applied; jobs recorded; no API errors.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

---

### cranix-web GUI (`WEB-`) and mobile app (`MOB-`)

#### WEB-01 — Load login page
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: Apache proxy configured.
- Steps:
  1. Open `https://admin.<domain>/` and the school portal URL.
  2. Check the institute name is displayed.
- Expected result: Login page renders without console errors; server name shown.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-02 — Web login / logout
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: Admin credentials.
- Steps:
  1. Log in as admin.
  2. Log out.
  3. Log in with a wrong password.
- Expected result: Correct login routes to the start page; logout clears the
  session; wrong password shows an error and does not log in.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-03 — Menu filtered by role/ACL
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: Admin, teacher, student accounts.
- Steps:
  1. Log in with each role and inspect the side menu.
  2. Try to open an admin URL directly as a student.
- Expected result: Menu shows only allowed entries; direct access is blocked by
  the route guard.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-04 — Users management
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: Admin session.
- Steps:
  1. Open Users; search, create, edit and delete a user.
  2. Run a user import and check the import list.
- Expected result: Changes save correctly and are reflected on the server.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-05 — Groups / classes
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: Admin session.
- Steps:
  1. Open Groups; create a class; add/remove members.
- Expected result: Membership and class dirs update correctly.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-06 — Rooms and access control
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: A room with devices.
- Steps:
  1. Open Rooms; view devices and available IPs.
  2. Change access status (printing/login/internet/portal) for the room.
- Expected result: Access toggles save and take effect.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-07 — Devices
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: A device exists.
- Steps:
  1. Open Devices; view, edit homework config, and apply an action.
- Expected result: Device data and actions work.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-08 — Printers
- Tier: 1 | Package: cranix-web | Priority: M
- Preconditions: A printer exists.
- Steps:
  1. Open Printers; enable/disable, reset and set driver.
- Expected result: Printer state changes are reflected in CUPS.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-09 — System status and services
- Tier: 1 | Package: cranix-web | Priority: M
- Preconditions: Admin session.
- Steps:
  1. Open System → Status and Services.
- Expected result: Status/disk/services render with correct values.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-10 — Profile "Myself" and password change
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: A user able to change password.
- Steps:
  1. Open Profile → Myself; change the password; log in with the new password.
- Expected result: Password change succeeds and new password works.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-11 — Software packages, sets and licenses
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: Software packages downloaded.
- Steps:
  1. Open Softwares → Status/Packages/Sets; create a set; assign to a room.
- Expected result: Sets and assignments save and are reflected via API.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-12 — Security pages
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: Admin session.
- Steps:
  1. Open Security → Firewall, Proxy, Unbound, Access, Access-Log; make a change.
- Expected result: Changes apply and are visible on the server.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-13 — Documents
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: A user with document rights.
- Steps:
  1. Create a folder/document; upload content; add a version; set rights.
- Expected result: Document tree, versions and rights work in the GUI.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-14 — My groups (teacher)
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: Teacher with classes.
- Steps:
  1. Open My groups; view members; record attendance; add a note/grade.
- Expected result: Teacher sees only own classes; changes save.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-15 — Education / lessons
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: Teacher session.
- Steps:
  1. Open Lessons → Tests, Challenges, Room control, Courses, PTM.
  2. Perform one create/edit action in each tab.
- Expected result: Each tab functions; room control reaches devices.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### WEB-16 — Informations / announcements
- Tier: 2 | Package: cranix-web | Priority: L
- Preconditions: Admin session.
- Steps:
  1. Create an announcement and a task; mark as seen; view responses.
- Expected result: Content created and visible to the target audience.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### MOB-01 — Mobile login and saved servers
- Tier: 1 | Package: cranix-web | Priority: H
- Preconditions: Mobile browser / PWA / iOS build.
- Steps:
  1. Open the mobile/PWA entry (`mobillogin`).
  2. Add, edit and delete a saved server; then log in.
- Expected result: Server list persists in `localStorage`; login works.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### MOB-02 — PWA standalone behaviour
- Tier: 1 | Package: cranix-web | Priority: M
- Preconditions: Install the app to the home screen.
- Steps:
  1. Launch from the home screen (standalone).
  2. Confirm it opens the mobile login, not the desktop login.
- Expected result: Correct entry route for installed mode.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### MOB-03 — Interface language EN/DE
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: --
- Steps:
  1. Switch the interface language between English and German on several pages.
- Expected result: All visible strings switch; no missing translations.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### MOB-04 — Camera-based ID-card photo (iOS)
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: iOS build with Camera permission.
- Steps:
  1. Profile → Myself → take/choose an ID-card photo.
- Expected result: Photo captured/uploaded successfully.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### MOB-05 — VPN configuration download
- Tier: 2 | Package: cranix-web | Priority: L
- Preconditions: VPN enabled.
- Steps:
  1. Profile → My VPN; download the config/installer for the platform.
- Expected result: Correct file downloaded.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### MOB-06 — 2FA PIN modal
- Tier: 2 | Package: cranix-web | Priority: M
- Preconditions: 2FA enabled for the user.
- Steps:
  1. Log in from the app; enter the PIN; test a wrong PIN.
- Expected result: Correct PIN logs in; wrong PIN is rejected.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### MOB-07 — Print / screenshot pages
- Tier: 2 | Package: cranix-web | Priority: L
- Preconditions: A print/report action available.
- Steps:
  1. Trigger an ID-card/report print (opens `printPage`).
  2. Trigger a room screenshot view.
- Expected result: Content renders and the print dialog opens.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

---

### Cross-package regression (`REG-`)

#### REG-01 — Combined update smoke
- Tier: 1 | Package: all | Priority: H
- Preconditions: All three packages updated together.
- Steps:
  1. Re-run every Tier 1 case.
- Expected result: All Tier 1 cases pass.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### REG-02 — Log review
- Tier: 1 | Package: all | Priority: H
- Preconditions: Test run completed.
- Steps:
  1. Check `journalctl -u cranix-api`, `/var/log/CRANIX-UPDATE-*`, Samba logs and
     `/var/adm/cranix/opentasks`.
  2. Check the browser console on the main pages.
- Expected result: No unexpected errors/exceptions/tracebacks.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### REG-03 — Version and cache consistency
- Tier: 1 | Package: cranix-web | Priority: M
- Preconditions: --
- Steps:
  1. Hard-refresh the web GUI after the update.
  2. Confirm the loaded asset hashes/version changed and no stale cached chunks.
- Expected result: New frontend is served; no "chunk load failed" errors.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

#### REG-04 — End-to-end school day scenario
- Tier: 1 | Package: all | Priority: H
- Preconditions: Test users/devices/rooms exist.
- Steps:
  1. Teacher opens a room; students log on; a student prints.
  2. Student hands in a file; teacher collects it.
  3. Admin checks the session and device state in the GUI.
- Expected result: The full typical workflow succeeds across all three packages.
- Result: [ ] Pass [ ] Fail [ ] N/A   Notes: ______

---

## 8. Exit criteria

- All **Tier 1** cases pass (or deviations are explicitly accepted by the
  maintainer).
- No new failure in `ENV-03`, `JAVA-06` (ACL) or `REG-02` (logs).
- Tier 2 failures are documented as defects with reproduction steps.
- The completed environment table (2.1), the results and the log excerpts are
  handed back to the maintainer.

## 9. Reporting

Return the filled-in document with:

1. The environment table from section 2.1.
2. Pass/Fail/N/A for every executed case.
3. For each failure: exact command/steps, observed result, expected result,
   relevant log snippets, and whether it blocks release.

## 10. Known risk areas (from code review — verify with extra care)

These areas are known to be fragile or frequently affected; treat failures here
as high priority:

1. **DHCP via Kea** — `setup/scripts/setup-kea.py` appears to contain syntax
   errors; validate the Kea path explicitly (BASE-13).
2. **Conditional Java resources** — 2FA, MDM, PTM, Calendar and ID-request
   endpoints are only registered when the matching `/etc/sysconfig/CRX_*` file
   exists; test both present and absent (JAVA-10).
3. **Frontend build replace** — `cranix-web` replaces `utils.service.ts` with
   `utils.service-notest.ts` in production; a development build may silently
   point at a hardcoded server. Confirm which build is tested (WEB-01).
4. **Mobile branding/config** — `capacitor.config.json` still uses
   `appId: io.ionic.starter`, and there is no committed Android project; verify
   branding and the iOS/PWA build you actually ship (MOB-01, MOB-02).
5. **Firewall/access consistency** — legacy `iptables`/`CRANIX_USE_TFK` scripts
   and `crx_manage_room_access.py` coexist; check for leftover rules (BASE-12).
6. **Class adhoc rooms** — created during import when
   `CRANIX_MAINTAIN_ADHOC_ROOM_FOR_CLASSES="yes"`; verify device IPs match the
   room network (BASE-08).
7. **Database migration** — EclipseLink `create-or-extend-tables` runs on
   startup; a failed migration can corrupt data. Always back up first (JAVA-07).
