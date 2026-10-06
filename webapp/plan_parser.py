#!/usr/bin/env python3
"""Parse the CRANIX QA test plan Markdown files into a merged plan.

The English (QA-TESTPLAN.md) and German (QA-TESTPLAN.de.md) documents share the
same case identifiers, so both are parsed and merged by case id. Every textual
field is kept per language, which lets the collector UI switch languages without
duplicating the plan.
"""

import re
from datetime import datetime, timezone

CASE_RE = re.compile(r"^####\s+([A-Z]+-\d+)\s+[\u2014\u2013-]\s+(.*\S)\s*$")
GROUP_RE = re.compile(r"^###\s+(.+?)\s*$")
GROUP_CODE_RE = re.compile(r"`([A-Z]+)-`")
META_RE = re.compile(r"^(Tier|Paket|Package|Priority|Priorit\u00e4t)\s*:\s*(.*)$")
FIELD_RE = re.compile(
    r"^(Preconditions|Vorbedingungen|Steps|Schritte|Expected result|"
    r"Erwartetes Ergebnis|Result|Ergebnis)\s*:\s*(.*)$"
)
STEP_RE = re.compile(r"^\s*\d+\.\s*(.*)$")

_PRE_KEYS = {"preconditions", "vorbedingungen"}
_STEP_KEYS = {"steps", "schritte"}
_EXPECTED_KEYS = {"expected result", "erwartetes ergebnis"}
_RESULT_KEYS = {"result", "ergebnis"}


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "field"


def parse_plan_file(path):
    """Parse a single test plan Markdown file.

    Returns a dict with ``cases`` (id -> case), ``order`` (list of ids),
    ``groups`` (prefix -> heading) and ``env_fields`` (section 2.1 rows).
    """
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    cases = {}
    order = []
    groups = {}
    env_fields = []

    in_fence = False
    in_env_table = False
    env_header_seen = False
    current = None
    mode = None

    def new_case():
        return {
            "id": None,
            "title": "",
            "tier": None,
            "package": "",
            "priority": "",
            "preconditions": "",
            "steps": [],
            "expected": "",
        }

    def append_continuation(text):
        if not text:
            return
        if mode == "steps":
            step = STEP_RE.match(text)
            if step:
                current["steps"].append(step.group(1).strip())
            elif current["steps"]:
                current["steps"][-1] = (current["steps"][-1] + " " + text).strip()
        elif mode == "pre":
            current["preconditions"] = (current["preconditions"] + " " + text).strip()
        elif mode == "expected":
            current["expected"] = (current["expected"] + " " + text).strip()

    for raw in lines:
        line = raw.rstrip()

        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if line.startswith("## "):
            in_env_table = False
            current = None
            mode = None
            continue

        group_match = GROUP_RE.match(line)
        if group_match:
            heading = group_match.group(1)
            codes = GROUP_CODE_RE.findall(heading)
            if codes:
                for code in codes:
                    groups.setdefault(code, heading)
                in_env_table = False
            else:
                in_env_table = heading.startswith("2.1")
                env_header_seen = False
            current = None
            mode = None
            continue

        if in_env_table and line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                key = cells[0].lower()
                value = cells[1].lower()
                if key in ("item", "punkt") and value in ("value", "wert"):
                    env_header_seen = True
                    continue
                if set("".join(cells)) <= set("-: "):
                    continue
                if env_header_seen and cells[0]:
                    env_fields.append({"id": _slug(cells[0]), "label": cells[0]})
            continue

        case_match = CASE_RE.match(line)
        if case_match:
            current = new_case()
            current["id"] = case_match.group(1)
            current["title"] = case_match.group(2).strip()
            cases[current["id"]] = current
            order.append(current["id"])
            mode = None
            continue

        if current is None:
            continue

        if line.startswith("- "):
            body = line[2:].strip()
            field_match = FIELD_RE.match(body)
            if field_match:
                key = field_match.group(1).lower()
                value = field_match.group(2).strip()
                if key in _PRE_KEYS:
                    mode = "pre"
                    current["preconditions"] = value
                elif key in _STEP_KEYS:
                    mode = "steps"
                    if value:
                        append_continuation(value)
                elif key in _EXPECTED_KEYS:
                    mode = "expected"
                    current["expected"] = value
                elif key in _RESULT_KEYS:
                    mode = None
                else:
                    mode = None
                continue

            is_meta = False
            for segment in body.split("|"):
                meta_match = META_RE.match(segment.strip())
                if not meta_match:
                    continue
                is_meta = True
                meta_key = meta_match.group(1).lower()
                meta_value = meta_match.group(2).strip()
                if meta_key == "tier":
                    try:
                        current["tier"] = int(meta_value)
                    except ValueError:
                        current["tier"] = meta_value
                elif meta_key in ("package", "paket"):
                    current["package"] = meta_value
                else:
                    current["priority"] = meta_value
            if is_meta:
                mode = None
                continue

            append_continuation(body)
            continue

        append_continuation(line.strip())

    return {"cases": cases, "order": order, "groups": groups, "env_fields": env_fields}


def _normalize_packages(value):
    packages = []
    for part in re.split(r"[,/]", value or ""):
        part = part.strip().lower()
        if not part:
            continue
        if part in ("alle", "all"):
            part = "all"
        if part not in packages:
            packages.append(part)
    return packages or ["all"]


def _localized(en_case, de_case, field, fallback):
    value_en = en_case.get(field, fallback)
    value_de = de_case.get(field) if de_case else None
    return {"en": value_en, "de": value_de if value_de else value_en}


def build_plan(en_path, de_path):
    """Parse and merge the English and German plan files."""
    en = parse_plan_file(en_path)
    de = parse_plan_file(de_path)

    cases = []
    for case_id in en["order"]:
        en_case = en["cases"][case_id]
        de_case = de["cases"].get(case_id)
        cases.append(
            {
                "id": case_id,
                "group": case_id.split("-", 1)[0],
                "tier": en_case["tier"],
                "package": en_case["package"],
                "packages": _normalize_packages(en_case["package"]),
                "priority": en_case["priority"],
                "title": _localized(en_case, de_case, "title", ""),
                "preconditions": _localized(en_case, de_case, "preconditions", ""),
                "steps": _localized(en_case, de_case, "steps", []),
                "expected": _localized(en_case, de_case, "expected", ""),
            }
        )

    group_labels = []
    seen = set()
    for source in (en["groups"], de["groups"]):
        for prefix, heading in source.items():
            if prefix in seen:
                continue
            seen.add(prefix)
            group_labels.append(
                {
                    "prefix": prefix,
                    "label": {
                        "en": en["groups"].get(prefix, heading),
                        "de": de["groups"].get(prefix, heading),
                    },
                }
            )

    env_fields = []
    for index, field in enumerate(en["env_fields"]):
        label_de = (
            de["env_fields"][index]["label"]
            if index < len(de["env_fields"])
            else field["label"]
        )
        env_fields.append(
            {"id": field["id"], "label": {"en": field["label"], "de": label_de}}
        )

    return {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "caseCount": len(cases),
            "groupCount": len(group_labels),
        },
        "groups": group_labels,
        "envFields": env_fields,
        "cases": cases,
    }


if __name__ == "__main__":
    import argparse
    import json
    import os

    parser = argparse.ArgumentParser(description="Parse the CRANIX QA test plan.")
    parser.add_argument("--plan-dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = parser.parse_args()
    plan = build_plan(
        os.path.join(args.plan_dir, "QA-TESTPLAN.md"),
        os.path.join(args.plan_dir, "QA-TESTPLAN.de.md"),
    )
    print(json.dumps(plan, ensure_ascii=False, indent=2))
