---
name: python-code-review
description: Reviews Python source files against this repo's style guide (missing docstrings, missing type hints, mutable default arguments, bare except clauses) and fixes them. Use when the user asks to review, lint, clean up, or improve Python code in this repository, or before opening a PR. Do not use for non-Python files, for architectural or design review, for security audits, or for style questions about JavaScript, Vue, or other non-Python languages.
---

## Steps

1. Identify the target Python file(s) from the user's request. If none is
   specified, ask which file(s) to review before proceeding.
2. Run `scripts/check_style.py <file>` for each target file. Its JSON output
   is the single source of truth for violations — do not re-derive rules
   from memory or flag anything the script didn't report.
3. If a reported violation's rule name is unfamiliar, read
   `references/style-guide.md` for its rationale before proposing a fix.
   Skip this step for rules already understood from earlier in the session.
4. For each violation, edit the file with a fix consistent with the
   surrounding code style (naming, quote style, existing type hint style).
5. Re-run `scripts/check_style.py <file>` to confirm the violation count is
   zero. If any remain, either fix them or explain concretely why each one
   is a false positive.
6. Write the final summary using the exact section structure in
   `assets/review-template.md` — do not invent a different report format.

## Error handling

- If `scripts/check_style.py` exits with a syntax error, report the exact
  line/column from its stderr and stop. Do not attempt to fix a syntax error
  by guessing at the author's intent.
- If a target file does not exist, say so and stop rather than reviewing a
  different file.
