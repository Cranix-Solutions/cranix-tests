#!/usr/bin/env python3
"""CRANIX QA test result collector.

A dependency-free web application (Python standard library only) that serves the
QA test plan from ``QA-TESTPLAN.md`` / ``QA-TESTPLAN.de.md`` as an interactive
checklist and stores every test run as a JSON file.

Usage:
    python3 server.py [--host 127.0.0.1] [--port 8765]
                      [--plan-dir DIR] [--results-dir DIR]
                      [--api-url URL] [--acl NAME]
"""

import argparse
import csv
import io
import json
import os
import re
import secrets
import tempfile
import threading
import time
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

try:
    from http.server import ThreadingHTTPServer
except ImportError:  # Python < 3.7
    from socketserver import ThreadingMixIn

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

from plan_parser import build_plan

HERE = os.path.dirname(os.path.abspath(__file__))

STATUSES = ("pass", "fail", "na", "notrun")
VALID_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
}

_write_lock = threading.Lock()


class Config:
    def __init__(
        self,
        plan_dir,
        results_dir,
        static_dir,
        api_url="http://127.0.0.1:9080/api",
        acl="qatest.manage",
        cookie_name="ck_testcollector",
        session_ttl=28800,
        secure_cookie=False,
    ):
        self.plan_dir = plan_dir
        self.results_dir = results_dir
        self.static_dir = static_dir
        self.index_file = os.path.join(static_dir, os.pardir, "index.html")
        self.api_url = api_url.rstrip("/")
        self.acl = acl
        self.cookie_name = cookie_name
        self.session_ttl = session_ttl
        self.secure_cookie = secure_cookie
        self.sessions = {}
        self.sessions_lock = threading.Lock()
        self._plan = None
        self._plan_stamp = None

    def plan(self):
        en = os.path.join(self.plan_dir, "QA-TESTPLAN.md")
        de = os.path.join(self.plan_dir, "QA-TESTPLAN.de.md")
        stamp = tuple(
            os.path.getmtime(path) if os.path.exists(path) else None
            for path in (en, de)
        )
        if self._plan is None or self._plan_stamp != stamp:
            self._plan = build_plan(en, de)
            self._plan_stamp = stamp
        return self._plan


def _api_call(config, method, path, payload=None, token=None, timeout=10):
    """Call the CRANIX REST API. Returns (status_code, json_or_none)."""
    url = config.api_url + path
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            try:
                return response.status, json.loads(raw)
            except ValueError:
                return response.status, None
    except HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode("utf-8"))
        except (ValueError, OSError):
            return error.code, None
    except (URLError, OSError):
        return 0, None


def _prune_sessions(config, now):
    expiry = now - config.session_ttl
    with config.sessions_lock:
        for sid in [s for s, data in config.sessions.items() if data["lastSeen"] < expiry]:
            config.sessions.pop(sid, None)



def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_id(run_id):
    if not run_id or ".." in run_id or not VALID_ID.match(run_id):
        return None
    return run_id


def _run_path(config, run_id):
    return os.path.join(config.results_dir, run_id + ".json")


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _empty_run(config):
    return {
        "id": None,
        "tester": "",
        "created": _now(),
        "updated": _now(),
        "language": "en",
        "environment": {},
        "results": {},
    }


def _new_run_id(config, tester):
    slug = re.sub(r"[^a-z0-9]+", "-", (tester or "").lower()).strip("-") or "tester"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = "{}-{}".format(slug[:40], stamp)
    suffix = 1
    while os.path.exists(_run_path(config, candidate)):
        suffix += 1
        candidate = "{}-{}-{}".format(slug[:40], stamp, suffix)
    return candidate


def _list_runs(config):
    if not os.path.isdir(config.results_dir):
        return []
    runs = []
    for name in sorted(os.listdir(config.results_dir)):
        if not name.endswith(".json"):
            continue
        try:
            run = _read_json(os.path.join(config.results_dir, name))
        except (OSError, ValueError):
            continue
        runs.append(
            {
                "id": run.get("id", name[:-5]),
                "tester": run.get("tester", ""),
                "created": run.get("created", ""),
                "updated": run.get("updated", ""),
                "counts": _counts(config.plan(), run.get("results", {})),
            }
        )
    runs.sort(key=lambda item: item.get("updated", ""), reverse=True)
    return runs


def _counts(plan, results):
    counts = {status: 0 for status in STATUSES}
    tier1 = {"total": 0, "pass": 0, "fail": 0, "na": 0, "notrun": 0}
    for case in plan["cases"]:
        status = (results.get(case["id"]) or {}).get("status", "notrun")
        if status not in STATUSES:
            status = "notrun"
        counts[status] += 1
        if case["tier"] == 1:
            tier1["total"] += 1
            tier1[status] += 1
    counts["total"] = len(plan["cases"])
    return {"statuses": counts, "tier1": tier1}


_STATUS_LABELS = {
    "en": {"pass": "Pass", "fail": "Fail", "na": "N/A", "notrun": "Not run"},
    "de": {
        "pass": "Bestanden",
        "fail": "Fehlgeschlagen",
        "na": "N/A",
        "notrun": "Nicht getestet",
    },
}


def _render_markdown(config, run, lang):
    lang = lang if lang in ("en", "de") else "en"
    plan = config.plan()
    labels = _STATUS_LABELS[lang]
    if lang == "de":
        strings = {
            "title": "CRANIX Server \u2014 QA-Testbericht",
            "tester": "Tester",
            "date": "Datum/Uhrzeit",
            "run_id": "Testlauf-ID",
            "env": "Testumgebung",
            "summary": "Zusammenfassung",
            "total": "Gesamt",
            "tier1": "Tier 1",
            "not_run": "Nicht getestet",
            "item": "Punkt",
            "value": "Wert",
            "status": "Status",
            "notes": "Notizen",
            "observed": "Beobachtetes Ergebnis",
            "log": "Log-Auszug",
            "blocks": "Blockiert Release",
            "yes": "ja",
            "no": "nein",
        }
    else:
        strings = {
            "title": "CRANIX Server \u2014 QA Test Report",
            "tester": "Tester",
            "date": "Date/time",
            "run_id": "Run id",
            "env": "Test environment",
            "summary": "Summary",
            "total": "Total",
            "tier1": "Tier 1",
            "not_run": "Not run",
            "item": "Item",
            "value": "Value",
            "status": "Status",
            "notes": "Notes",
            "observed": "Observed result",
            "log": "Log snippet",
            "blocks": "Blocks release",
            "yes": "yes",
            "no": "no",
        }

    lines = ["# " + strings["title"], ""]
    lines.append("- {}: {}".format(strings["tester"], run.get("tester", "")))
    lines.append("- {}: {}".format(strings["date"], run.get("updated", "")))
    lines.append("- {}: {}".format(strings["run_id"], run.get("id", "")))
    lines.append("")

    lines.append("## " + strings["env"])
    lines.append("")
    lines.append("| {} | {} |".format(strings["item"], strings["value"]))
    lines.append("|---|---|")
    environment = run.get("environment", {})
    for field in plan["envFields"]:
        value = environment.get(field["id"], "")
        lines.append(
            "| {} | {} |".format(field["label"][lang], value.replace("|", "\\|"))
        )
    lines.append("")

    counts = _counts(plan, run.get("results", {}))
    statuses = counts["statuses"]
    tier1 = counts["tier1"]
    lines.append("## " + strings["summary"])
    lines.append("")
    lines.append("| {} | {} |".format(strings["status"], strings["total"]))
    lines.append("|---|---|")
    for status in STATUSES:
        lines.append("| {} | {} |".format(labels[status], statuses[status]))
    lines.append(
        "| {} | {}/{} |".format(strings["tier1"], tier1["pass"], tier1["total"])
    )
    lines.append("")

    results = run.get("results", {})
    current_group = None
    for case in plan["cases"]:
        if case["group"] != current_group:
            current_group = case["group"]
            group_label = next(
                (
                    group["label"][lang]
                    for group in plan["groups"]
                    if group["prefix"] == current_group
                ),
                current_group,
            )
            lines.append("## " + group_label)
            lines.append("")
        result = results.get(case["id"]) or {}
        status = result.get("status", "notrun")
        if status not in STATUSES:
            status = "notrun"
        lines.append("### {} \u2014 {}".format(case["id"], case["title"][lang]))
        lines.append("- {}: {}".format(strings["status"], labels[status]))
        notes = result.get("notes", "")
        if notes:
            lines.append("- {}: {}".format(strings["notes"], notes.replace("\n", " ")))
        if status == "fail":
            if result.get("observed"):
                lines.append(
                    "- {}: {}".format(
                        strings["observed"], result["observed"].replace("\n", " ")
                    )
                )
            if result.get("log"):
                lines.append("- {}: {}".format(strings["log"], result["log"]))
            lines.append(
                "- {}: {}".format(
                    strings["blocks"],
                    strings["yes"] if result.get("blocksRelease") else strings["no"],
                )
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _render_csv(config, run, lang):
    plan = config.plan()
    lang = lang if lang in ("en", "de") else "en"
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "tier",
            "package",
            "priority",
            "group",
            "title",
            "status",
            "notes",
            "observed",
            "log",
            "blocks_release",
        ]
    )
    results = run.get("results", {})
    for case in plan["cases"]:
        result = results.get(case["id"]) or {}
        status = result.get("status", "notrun")
        if status not in STATUSES:
            status = "notrun"
        writer.writerow(
            [
                case["id"],
                case["tier"],
                case["package"],
                case["priority"],
                case["group"],
                case["title"][lang],
                status,
                result.get("notes", ""),
                result.get("observed", ""),
                result.get("log", ""),
                "yes" if result.get("blocksRelease") else "no",
            ]
        )
    return buffer.getvalue()


class Handler(BaseHTTPRequestHandler):
    config = None

    def _send(
        self, status, body, content_type="application/json; charset=utf-8", extra_headers=None
    ):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in extra_headers or []:
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status, payload, extra_headers=None):
        self._send(
            status,
            json.dumps(payload, ensure_ascii=False),
            "application/json; charset=utf-8",
            extra_headers,
        )

    def _error(self, status, message):
        self._json(status, {"error": message})

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except ValueError:
            return None

    def _get_cookie(self, name):
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        try:
            jar = SimpleCookie()
            jar.load(raw)
        except Exception:
            return None
        return jar[name].value if name in jar else None

    def _cookie_header(self, value, max_age):
        parts = [
            "{}={}".format(self.config.cookie_name, value),
            "Path=/",
            "HttpOnly",
            "SameSite=Lax",
            "Max-Age={}".format(max_age),
        ]
        if self.config.secure_cookie:
            parts.append("Secure")
        return [("Set-Cookie", "; ".join(parts))]

    def _user_payload(self, session):
        return {
            "username": session.get("uid", ""),
            "fullName": session.get("fullName", ""),
            "role": session.get("role", ""),
            "acls": session.get("acls", []),
        }

    def _drop_session(self, sid):
        with self.config.sessions_lock:
            self.config.sessions.pop(sid, None)

    def _authenticate(self):
        sid = self._get_cookie(self.config.cookie_name)
        if not sid:
            return None
        now = time.time()
        _prune_sessions(self.config, now)
        with self.config.sessions_lock:
            session = self.config.sessions.get(sid)
        if session is None:
            return None
        if now - session["lastSeen"] > self.config.session_ttl:
            self._drop_session(sid)
            return None
        if now - session.get("validated", 0) > 60:
            status, data = _api_call(
                self.config,
                "GET",
                "/sessions/byToken/" + quote(session["token"], safe=""),
                token=session["token"],
            )
            if status != 200 or not data:
                self._drop_session(sid)
                return None
            session["acls"] = data.get("acls", session.get("acls", []))
            session["fullName"] = data.get("fullName", session.get("fullName", ""))
            session["validated"] = now
        session["lastSeen"] = now
        return session

    def _require_auth(self):
        session = self._authenticate()
        if session is None:
            self._error(401, "authentication required")
            return None
        if self.config.acl not in session.get("acls", []):
            self._error(403, "missing ACL " + self.config.acl)
            return None
        return session

    def _handle_session(self):
        session = self._require_auth()
        if session is None:
            return
        return self._json(200, self._user_payload(session))

    def _handle_login(self):
        body = self._read_body()
        if body is None:
            return self._error(400, "invalid json")
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", ""))
        if not username or not password:
            return self._error(400, "username and password are required")
        status, data = _api_call(
            self.config,
            "POST",
            "/sessions/create",
            {"username": username, "password": password},
        )
        if status == 0:
            return self._error(502, "cannot reach the CRANIX API")
        if status != 200 or not data or not data.get("token"):
            return self._error(401, "invalid username or password")
        token = data["token"]
        acls = data.get("acls") or []
        if data.get("mustChange"):
            _api_call(
                self.config,
                "DELETE",
                "/sessions/" + quote(token, safe=""),
                token=token,
            )
            return self._error(403, "password change required")
        if self.config.acl not in acls:
            _api_call(
                self.config,
                "DELETE",
                "/sessions/" + quote(token, safe=""),
                token=token,
            )
            return self._error(403, "missing ACL " + self.config.acl)
        now = time.time()
        sid = secrets.token_urlsafe(32)
        session = {
            "token": token,
            "uid": data.get("name") or username,
            "fullName": data.get("fullName") or username,
            "role": data.get("role", ""),
            "acls": acls,
            "created": now,
            "lastSeen": now,
            "validated": now,
        }
        with self.config.sessions_lock:
            self.config.sessions[sid] = session
        return self._json(
            200, self._user_payload(session), self._cookie_header(sid, self.config.session_ttl)
        )

    def _handle_logout(self):
        sid = self._get_cookie(self.config.cookie_name)
        session = None
        if sid:
            with self.config.sessions_lock:
                session = self.config.sessions.pop(sid, None)
        if session:
            _api_call(
                self.config,
                "DELETE",
                "/sessions/" + quote(session["token"], safe=""),
                token=session["token"],
            )
        return self._json(200, {"ok": True}, self._cookie_header("", 0))

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            return self._serve_file(self.config.index_file)
        if path.startswith("/static/"):
            return self._serve_static(path[len("/static/"):])
        if path == "/favicon.ico":
            return self._send(204, b"", "image/x-icon")
        if path == "/testapi/health":
            return self._json(200, {"status": "ok", "time": _now()})
        if path == "/testapi/session":
            return self._handle_session()
        if path == "/testapi/plan":
            if self._require_auth() is None:
                return
            return self._json(200, self.config.plan())

        run_match = re.match(r"^/testapi/runs/([^/]+)(/export)?$", path)
        if run_match:
            run_id = _safe_id(run_match.group(1))
            if not run_id:
                return self._error(400, "invalid run id")
            if self._require_auth() is None:
                return
            if run_match.group(2):
                return self._export(run_id, query)
            run = self._load_run(run_id)
            if run is None:
                return self._error(404, "run not found")
            return self._json(200, run)

        if path == "/testapi/runs":
            if self._require_auth() is None:
                return
            return self._json(200, _list_runs(self.config))
        return self._error(404, "not found")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        if path == "/testapi/login":
            return self._handle_login()
        if path == "/testapi/logout":
            return self._handle_logout()
        if path != "/testapi/runs":
            return self._error(404, "not found")
        if self._require_auth() is None:
            return
        body = self._read_body()
        if body is None:
            return self._error(400, "invalid json")
        run = _empty_run(self.config)
        run["tester"] = str(body.get("tester", "")).strip()
        run["language"] = body.get("language", "en")
        run["environment"] = body.get("environment", {}) or {}
        run["results"] = body.get("results", {}) or {}
        with _write_lock:
            requested = _safe_id(body.get("id")) if body.get("id") else None
            if requested and not os.path.exists(_run_path(self.config, requested)):
                run["id"] = requested
            else:
                run["id"] = _new_run_id(self.config, run["tester"])
            _write_json(_run_path(self.config, run["id"]), run)
        return self._json(201, run)

    def do_PUT(self):
        path = unquote(urlparse(self.path).path)
        run_match = re.match(r"^/testapi/runs/([^/]+)$", path)
        if not run_match:
            return self._error(404, "not found")
        if self._require_auth() is None:
            return
        run_id = _safe_id(run_match.group(1))
        if not run_id:
            return self._error(400, "invalid run id")
        body = self._read_body()
        if body is None:
            return self._error(400, "invalid json")
        existing = self._load_run(run_id) or _empty_run(self.config)
        existing["id"] = run_id
        if "tester" in body:
            existing["tester"] = str(body["tester"]).strip()
        if "language" in body:
            existing["language"] = body["language"]
        if "environment" in body:
            existing["environment"] = body["environment"] or {}
        if "results" in body:
            existing["results"] = body["results"] or {}
        existing["updated"] = _now()
        with _write_lock:
            _write_json(_run_path(self.config, run_id), existing)
        return self._json(200, existing)

    def do_DELETE(self):
        path = unquote(urlparse(self.path).path)
        run_match = re.match(r"^/testapi/runs/([^/]+)$", path)
        if not run_match:
            return self._error(404, "not found")
        if self._require_auth() is None:
            return
        run_id = _safe_id(run_match.group(1))
        if not run_id:
            return self._error(400, "invalid run id")
        response = self._load_run(run_id)
        if response is None:
            return self._error(404, "run not found")
        with _write_lock:
            try:
                os.unlink(_run_path(self.config, run_id))
            except FileNotFoundError:
                pass
        return self._json(200, {"deleted": run_id})

    def _load_run(self, run_id):
        path = _run_path(self.config, run_id)
        if not os.path.exists(path):
            return None
        try:
            return _read_json(path)
        except (OSError, ValueError):
            return None

    def _export(self, run_id, query):
        run = self._load_run(run_id)
        if run is None:
            return self._error(404, "run not found")
        fmt = (query.get("format", ["md"])[0] or "md").lower()
        lang = query.get("lang", [run.get("language", "en")])[0]
        if fmt == "json":
            body = json.dumps(run, ensure_ascii=False, indent=2)
            filename = "{}.json".format(run_id)
            content_type = "application/json; charset=utf-8"
        elif fmt == "csv":
            body = _render_csv(self.config, run, lang)
            filename = "{}.csv".format(run_id)
            content_type = "text/csv; charset=utf-8"
        else:
            body = _render_markdown(self.config, run, lang)
            filename = "{}.md".format(run_id)
            content_type = "text/markdown; charset=utf-8"
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Disposition", 'attachment; filename="{}"'.format(filename)
        )
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _serve_static(self, relative):
        return self._serve_file(os.path.join(self.config.static_dir, relative))

    def _serve_file(self, path):
        path = os.path.abspath(path)
        root = os.path.abspath(self.config.static_dir)
        parent = os.path.abspath(os.path.join(root, os.pardir))
        if not (path == parent or path.startswith(parent + os.sep)):
            return self._error(403, "forbidden")
        if not os.path.isfile(path):
            return self._error(404, "not found")
        extension = os.path.splitext(path)[1].lower()
        content_type = CONTENT_TYPES.get(extension, "application/octet-stream")
        with open(path, "rb") as handle:
            body = handle.read()
        self._send(200, body, content_type)


def main():
    parser = argparse.ArgumentParser(description="CRANIX QA test result collector")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--plan-dir",
        default=os.environ.get("CK_TESTCOLLECTOR_PLAN_DIR", os.path.dirname(HERE)),
    )
    parser.add_argument(
        "--results-dir",
        default=os.environ.get(
            "CK_TESTCOLLECTOR_RESULTS_DIR", os.path.join(HERE, "results")
        ),
    )
    parser.add_argument(
        "--static-dir",
        default=os.environ.get(
            "CK_TESTCOLLECTOR_STATIC_DIR", os.path.join(HERE, "static")
        ),
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get(
            "CK_TESTCOLLECTOR_API_URL", "http://127.0.0.1:9080/api"
        ),
    )
    parser.add_argument(
        "--acl",
        default=os.environ.get("CK_TESTCOLLECTOR_ACL", "qatest.manage"),
    )
    parser.add_argument(
        "--cookie-name",
        default=os.environ.get("CK_TESTCOLLECTOR_COOKIE", "ck_testcollector"),
    )
    parser.add_argument(
        "--session-ttl",
        type=int,
        default=int(os.environ.get("CK_TESTCOLLECTOR_SESSION_TTL", "28800")),
    )
    parser.add_argument(
        "--secure-cookie",
        action="store_true",
        default=os.environ.get("CK_TESTCOLLECTOR_SECURE_COOKIE", "") == "yes",
    )
    args = parser.parse_args()

    config = Config(
        args.plan_dir,
        args.results_dir,
        args.static_dir,
        api_url=args.api_url,
        acl=args.acl,
        cookie_name=args.cookie_name,
        session_ttl=args.session_ttl,
        secure_cookie=args.secure_cookie,
    )
    Handler.config = config

    os.makedirs(config.results_dir, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        "CRANIX QA test collector on http://{}:{}/ (plan: {}, results: {}, api: {}, acl: {})".format(
            args.host,
            args.port,
            config.plan_dir,
            config.results_dir,
            config.api_url,
            config.acl,
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
