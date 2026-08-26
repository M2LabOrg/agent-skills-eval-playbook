# 5. Sandboxing evals with `git worktree`

An eval run lets an agent read and edit real files. You don't want that
happening in the same working directory you're using for everything else —
a bad run could leave half-applied edits, stray files, or an inconsistent
git state behind. `git worktree` solves this without needing containers,
VMs, or a second clone of the repo.

## What is a `git worktree`?

A `git worktree` is a feature built into git itself — no plugins, no extra
installs. It lets you check out a second (or third, or twentieth) working
directory from the same repository, all sharing the same `.git` history.

The key differences from alternatives:

| | `git worktree` | `git clone` | branch switch |
|---|---|---|---|
| Speed | Near-instant | Network fetch + full object copy | Fast, but disturbs open files |
| Disk (objects) | None extra — shared `.git` | Full duplicate | None extra |
| Isolation | Own working tree | Own working tree + own `.git` | Same working tree |
| Cleanup | `git worktree remove` | `rm -rf` the clone | `git checkout -` |

For a benchmark that spins up a clean sandbox per test case, dozens of
times per run, that speed difference matters.

## Creating and removing a worktree by hand

```bash
# Create a new worktree at the given path, checked out at the current HEAD
git worktree add .evals/sandbox-mytest HEAD

# Work inside it (your real working tree is untouched)
cd .evals/sandbox-mytest
# ... agent runs here, edits files here ...
cd -

# Remove it when done — leaves no trace in the working tree or git history
git worktree remove --force .evals/sandbox-mytest
```

`git worktree list` shows all active worktrees. `git worktree prune` cleans
up stale entries left behind by an interrupted run.

## The pattern this repo uses

```bash
# from the main repo, on a clean commit
git worktree add .evals/sandbox-<case-id> HEAD

# run the agent inside the sandbox
cd .evals/sandbox-<case-id>
# e.g. with Claude Code CLI:
claude -p "<prompt>" --output-format json > result.json
# or any other agent you're benchmarking

cd -
git worktree remove --force .evals/sandbox-<case-id>
```

Every case gets its own directory, checked out from the *exact same commit*,
with no memory of any previous case's edits. That matters for a benchmark
specifically: if case 2 ran in a directory case 1 already modified, you'd be
measuring case 1's leftover state, not case 2's actual behavior.
[`.evals/sandbox.sh`](../.evals/sandbox.sh) is this pattern as a standalone
script you can run by hand; [`.evals/run_evals.py`](../.evals/run_evals.py)
does the same thing programmatically for every case in `test_cases.json`.

## Why not just copy the repo folder instead?

A plain `cp -r` would work once, but it copies all tracked *and* untracked
files — including your `.venv`, any half-written edits, and anything else
that happens to be in the tree. A `git worktree add ... HEAD` gives you
exactly what's committed, nothing more and nothing less, every time.

## Cleaning up interrupted runs

Worktrees left behind after a crash are harmless but accumulate. Check with:

```bash
git worktree list
```

Remove stale entries with `git worktree prune`. `run_evals.py` removes its
worktree in a `finally` block specifically so a crashed eval run doesn't
leave one behind, but `prune` is the manual fallback if it does.
