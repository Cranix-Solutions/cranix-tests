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

```bash
# Run all setup phases in numbered order
/usr/share/cranix/tests/tests/cranix-full-test.sh
```

Counts can be overridden, e.g. `CLASS_COUNT=1 STUDENT_COUNT=3 TEACHER_COUNT=2`.

## Install

```bash
make install        # install into DESTDIR=/
make dist           # build cranix-tests.tar.bz2 and push to the OBS repo
```
