#!/usr/bin/env python3
"""Validate all benchmark JSONL files against schema.json."""

import json
import sys
import jsonschema
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    schema_path = BASE_DIR / "schema.json"
    datasets_dir = BASE_DIR / "datasets"

    with open(schema_path) as f:
        schema = json.load(f)

    total = 0
    passed = 0
    failed = 0

    jsonl_files = sorted(datasets_dir.glob("*.jsonl"))
    if not jsonl_files:
        print("ERROR: No JSONL files found in datasets/")
        sys.exit(1)

    for jsonl_file in jsonl_files:
        cases = []
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    cases.append(json.loads(line))

        file_ok = 0
        for i, case in enumerate(cases):
            total += 1
            try:
                jsonschema.validate(case, schema)
                passed += 1
                file_ok += 1
            except jsonschema.ValidationError as e:
                failed += 1
                print(f"  FAIL [{jsonl_file.name}] case {i} ({case.get('case_id', '?')}): {e.message}")

        status = "✅" if file_ok == len(cases) else "❌"
        print(f"{status} {jsonl_file.name}: {file_ok}/{len(cases)} passed")

    print(f"\nTotal: {passed}/{total} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
