#!/usr/bin/env python3
"""Check a small evidence graph. Not a conformity or evidence-authenticity tool."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def inspect(data, root):
    errors, gaps = [], []
    tables = {}
    for kind in ("needs", "hazards", "designs", "requirements", "tests", "prerequisites"):
        entries = data.get(kind)
        if not isinstance(entries, list) or not entries:
            errors.append(f"{kind}: expected a nonempty list")
            entries = []
        table = {}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"]:
                errors.append(f"{kind}: entry missing a string id")
                continue
            if entry["id"] in table:
                errors.append(f"duplicate id: {entry['id']}")
            table[entry["id"]] = entry
        tables[kind] = table
    all_ids = [key for table in tables.values() for key in table]
    if len(all_ids) != len(set(all_ids)):
        errors.append("IDs must be globally unique")
    if data.get("schema_version") != 1:
        errors.append("unsupported schema_version")
    if not isinstance(data.get("baseline"), str) or not data["baseline"]:
        errors.append("baseline identifier missing")

    def links(record, field, kind):
        values = record.get(field)
        if not isinstance(values, list) or not values:
            errors.append(f"{record['id']}: missing {field}")
            return []
        for value in values:
            if not isinstance(value, str) or value not in tables[kind]:
                errors.append(f"{record['id']}: unknown {field} reference {value!r}")
        return [v for v in values if isinstance(v, str) and v in tables[kind]]

    def artifact(owner, record):
        if not isinstance(record, dict):
            errors.append(f"{owner}: invalid artifact record")
            return
        name = record.get("path")
        if not isinstance(name, str) or not name:
            errors.append(f"{owner}: artifact path missing")
            return
        path = (root / name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(root.resolve()):
            errors.append(f"{owner}: artifact outside project root")
            return
        if not path.is_file():
            errors.append(f"{owner}: artifact does not exist: {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != record.get("sha256"):
            errors.append(f"{owner}: artifact hash mismatch: {name}")

    used_needs, used_hazards, used_designs, used_tests = set(), set(), set(), set()
    for req in tables["requirements"].values():
        rid = req["id"]
        for field in ("statement", "acceptance"):
            if not isinstance(req.get(field), str) or not req[field].strip():
                errors.append(f"{rid}: missing {field}")
        used_needs.update(links(req, "needs", "needs"))
        used_hazards.update(links(req, "hazards", "hazards"))
        used_designs.update(links(req, "designs", "designs"))
        tests = links(req, "tests", "tests")
        used_tests.update(tests)
        if req.get("status") not in ("draft", "implemented", "verified"):
            errors.append(f"{rid}: invalid status")
        if req.get("status") != "verified":
            gaps.append(f"{rid}: not verified")
        if not req.get("reviewer"):
            gaps.append(f"{rid}: review missing")
        unresolved = req.get("unresolved", [])
        if not isinstance(unresolved, list):
            errors.append(f"{rid}: unresolved must be a list")
        elif unresolved:
            gaps.append(f"{rid}: unresolved acceptance/design decisions")
        implementation = req.get("implementation")
        if not isinstance(implementation, list):
            errors.append(f"{rid}: implementation must be a list")
        elif not implementation:
            gaps.append(f"{rid}: implementation evidence missing")
        else:
            for item in implementation:
                artifact(rid, item)
        for tid in tests:
            if rid not in tables["tests"][tid].get("requirements", []):
                errors.append(f"{rid}/{tid}: missing reverse link")

    for kind, used in (("needs", used_needs), ("hazards", used_hazards),
                       ("designs", used_designs), ("tests", used_tests)):
        for ident in tables[kind].keys() - used:
            errors.append(f"orphan {kind}: {ident}")
    for test in tables["tests"].values():
        tid = test["id"]
        for rid in links(test, "requirements", "requirements"):
            if tid not in tables["requirements"][rid].get("tests", []):
                errors.append(f"{tid}/{rid}: missing reverse link")
        if not test.get("procedure") or not test.get("expected"):
            errors.append(f"{tid}: protocol or expected outcome missing")
        result = test.get("result")
        if result not in ("planned", "passed", "failed", "blocked"):
            errors.append(f"{tid}: invalid result")
        if result != "passed":
            gaps.append(f"{tid}: result is not passed")
        else:
            evidence = test.get("evidence")
            if not isinstance(evidence, dict):
                errors.append(f"{tid}: passed without evidence")
                continue
            artifact(tid, evidence)
            for field in ("run_id", "executed_at", "reviewer", "environment"):
                if not evidence.get(field):
                    errors.append(f"{tid}: evidence missing {field}")
            if evidence.get("baseline") != data.get("baseline"):
                errors.append(f"{tid}: evidence is for a different baseline")
    for pre in tables["prerequisites"].values():
        if pre.get("status") not in ("open", "satisfied"):
            errors.append(f"{pre['id']}: invalid prerequisite status")
        elif pre["status"] != "satisfied":
            gaps.append(f"{pre['id']}: prerequisite open")
        elif not pre.get("reviewer") or not isinstance(pre.get("evidence"), dict):
            errors.append(f"{pre['id']}: satisfied without reviewed evidence")
        else:
            artifact(pre["id"], pre["evidence"])
    return {"structural_errors": errors, "release_gaps": gaps,
            "counts": {kind: len(table) for kind, table in tables.items()},
            "recorded_release_gate_passed": not errors and not gaps,
            "scope": "Structural and recorded-evidence checks only; not standards conformity."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path)
    parser.add_argument("--root", type=Path, help="Project root; defaults to graph's parent directory's parent")
    parser.add_argument("--release", action="store_true", help="Fail for unfinished evidence as well as structural errors")
    args = parser.parse_args()
    try:
        data = json.loads(args.graph.read_text())
        if not isinstance(data, dict):
            raise ValueError("graph must be a JSON object")
        report = inspect(data, args.root or args.graph.resolve().parent.parent)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"input_error": str(exc)}))
        return 2
    print(json.dumps(report, indent=2))
    return int(bool(report["structural_errors"] or (args.release and report["release_gaps"])))


if __name__ == "__main__":
    sys.exit(main())
