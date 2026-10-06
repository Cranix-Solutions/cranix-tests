# cranix-tests

Test helpers and the QA test plan for checking the quality of a CRANIX server
after updating the packages `cranix-base`, `cranix-java` and `cranix-web`.

## QA test plan

- English: [QA-TESTPLAN.md](QA-TESTPLAN.md)
- Deutsch: [QA-TESTPLAN.de.md](QA-TESTPLAN.de.md)

The plans are human-executed, checkbox-based regression tests. Tier 0 sets up
the environment, Tier 1 is the smoke test to run after every package update, and
Tier 2 is the extended coverage for releases.

## Test helpers

All helpers are installed under `/usr/share/cranix/tests` and run from
`tests/cranix-full-test.sh`:

| Directory | Content |
|---|---|
| `bin/` | Numbered setup phases (user import, radius, adhoc rooms) |
| `helper/` | Data generators and shared functions |
| `datas/` | Import fixtures |
| `tests/` | `cranix-full-test.sh` entry point |
| `webapp/` | Result collector web app (see below) |

```bash
# Run all setup phases in numbered order
/usr/share/cranix/tests/tests/cranix-full-test.sh
```

Counts can be overridden, e.g. `CLASS_COUNT=1 STUDENT_COUNT=3 TEACHER_COUNT=2`.

## Result collector webapp

`webapp/` contains a dependency-free Python app that turns the test plan into an
interactive checklist and stores every run as a JSON file. It parses
`QA-TESTPLAN.md` and `QA-TESTPLAN.de.md` at runtime, so the plan stays the single
source of truth.

```bash
# Run from the repository
python3 webapp/server.py --port 8765
# open http://127.0.0.1:8765/
```

Installed under `/usr/share/cranix/tests/webapp`, it is started by the
`cranix-testcollector` systemd unit (results in `/var/lib/cranix-testcollector`).
Use `webapp/apache-cranix-testcollector.conf.example` to expose it to the test
network. Parser tests: `python3 -m unittest webapp.test_parser`.

### Authentication

The collector uses the CRANIX REST API (`/sessions/create`, `/sessions/byToken`,
`/sessions/{token}`) like the web app. The CRANIX token is kept server-side; the
browser only gets an `HttpOnly` session cookie. Only users holding the
**`qatest.manage`** ACL may sign in; everyone else gets a 403.

Relevant options: `--api-url` (default `http://127.0.0.1:9080/api`) and `--acl`
(default `qatest.manage`).

### Creating the qatest.manage ACL (manual)

The ACL is **not** provisioned automatically; create it once on the server where
the package is installed. For example, to grant it to the administrators group:

```bash
/usr/sbin/crx_api.sh PUT  system/enumerates/apiAcl/qatest.manage
/usr/sbin/crx_api.sh POST system/acls/groups/1 \
    '{"acl":"qatest.manage","allowed":true,"userId":null,"groupId":1}'
```

Adjust the group id (or use a user id) as needed, or assign it in the web GUI
under System → ACLs. Users must sign out and in again to pick up the new ACL.


## Install

```bash
make install        # install into DESTDIR=/
make dist           # build cranix-tests.tar.bz2 and push to the OBS repo
```
