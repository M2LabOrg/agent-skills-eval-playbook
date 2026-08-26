#!/usr/bin/env python3
"""Deterministic style checker for the python-code-review skill.

Stdlib only (ast, json, sys, argparse). Checks four rules:
  - bare-except
  - missing-docstring   (public functions only)
  - mutable-default-arg (list/dict/set literal as a default value)
  - missing-type-hints  (public function params and/or return annotation)

Usage:
    python check_style.py <file.py> [--json]

Exit code is always 0 on a successful parse (violations are reported, not
treated as a script failure); exit code is 2 on a syntax error in the
target file, with the error printed to stderr.
"""
import argparse
import ast
import json
import sys


def is_public(name: str) -> bool:
    return not name.startswith("_")


def check_file(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=path)
    violations: list[dict] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            violations.append(
                {"rule": "bare-except", "line": node.lineno,
                 "detail": "except: with no exception type"}
            )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_public(node.name) and not ast.get_docstring(node):
                violations.append(
                    {"rule": "missing-docstring", "line": node.lineno,
                     "detail": f"function '{node.name}' has no docstring"}
                )

            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    violations.append(
                        {"rule": "mutable-default-arg", "line": node.lineno,
                         "detail": f"function '{node.name}' uses a mutable default argument"}
                    )

            if is_public(node.name):
                for arg in node.args.args:
                    if arg.arg == "self":
                        continue
                    if arg.annotation is None:
                        violations.append(
                            {"rule": "missing-type-hints", "line": node.lineno,
                             "detail": f"parameter '{arg.arg}' of '{node.name}' has no type hint"}
                        )
                if node.returns is None:
                    violations.append(
                        {"rule": "missing-type-hints", "line": node.lineno,
                         "detail": f"function '{node.name}' has no return type hint"}
                    )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Python file to check")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    try:
        violations = check_file(args.path)
    except SyntaxError as e:
        print(f"SyntaxError in {args.path}: line {e.lineno}, col {e.offset}: {e.msg}",
              file=sys.stderr)
        return 2

    result = {"file": args.path, "violation_count": len(violations), "violations": violations}

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.path}: {len(violations)} violation(s)")
        for v in violations:
            print(f"  line {v['line']}: [{v['rule']}] {v['detail']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
