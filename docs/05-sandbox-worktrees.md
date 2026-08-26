# 5. Sandboxing evals with `git worktree`

An eval run lets an agent read and edit real files. You don't want that
happening in the same working directory you're using for everything else —
a bad run could leave half-applied edits, stray files, or an inconsistent
git state behind. `git worktree` solves this without needing containers,
VMs, or a second clone of the repo.

## Why `worktree` instead of a fresh `git clone`

A worktree is a second working directory backed by the *same* `.git`
history — creating one is close to instant (no network fetch, no full
object copy), and removing one leaves no trace. For a benchmark that spins
up a clean sandbox per test case, dozens of times per run, that speed
difference matters.

## The pattern this repo uses

```bash
# from the main repo, on a clean commit
git worktree add ../sandbox-<case-id> HEAD

cd ../sandbox-<case-id>
claude -p "<prompt>" --output-format json > result.json

cd -
git worktree remove --force ../sandbox-<case-id>
```

Every case gets its own directory, checked out from the *exact same commit*,
with no memory of any previous case's edits. That matters for a benchmark
specifically: if case 2 ran in a directory case 1 already modified, you'd be
measuring case 1's leftover state, not case 2's actual behavior.
[`.evals/sandbox.sh`](../.evals/sandbox.sh) is this pattern as a standalone
script you can run by hand; [`.evals/run_evals.py`](../.evals/run_evals.py)
does the same thing programmatically for every case in
`test_cases.json`.

## In CI

[`.github/workflows/skill-eval.yml`](../.github/workflows/skill-eval.yml)
runs on a fresh GitHub Actions runner per job, which is already an isolated
sandbox — so the worktree layer there is mainly about running many test
cases in parallel-safe isolation within that one runner, not about
protecting anything outside it. Locally, it's the opposite: the worktree is
what stands between an experimental `SKILL.md` edit and your actual
uncommitted work.

## Cleaning up

Worktrees left behind after an interrupted run are harmless but will
accumulate — `git worktree list` shows them, `git worktree prune` removes
stale entries. `run_evals.py` removes its worktree in a `finally` block
specifically so a crashed eval run doesn't leave one behind.
