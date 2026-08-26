#!/usr/bin/env bash
# Manual worktree sandbox helper — the same pattern run_evals.py automates.
# Usage:
#   ./.evals/sandbox.sh up <name>      # create a sandbox worktree at .evals/sandbox-<name>
#   ./.evals/sandbox.sh down <name>    # remove it
#   ./.evals/sandbox.sh list           # show all worktrees
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
ACTION="${1:-}"
NAME="${2:-}"

case "$ACTION" in
  up)
    [ -n "$NAME" ] || { echo "usage: $0 up <name>" >&2; exit 1; }
    SANDBOX="$REPO_ROOT/.evals/sandbox-$NAME"
    git -C "$REPO_ROOT" worktree add "$SANDBOX" HEAD
    echo "Sandbox ready: $SANDBOX"
    echo "  cd $SANDBOX && claude -p \"your prompt\" --output-format json"
    ;;
  down)
    [ -n "$NAME" ] || { echo "usage: $0 down <name>" >&2; exit 1; }
    SANDBOX="$REPO_ROOT/.evals/sandbox-$NAME"
    git -C "$REPO_ROOT" worktree remove --force "$SANDBOX"
    echo "Removed: $SANDBOX"
    ;;
  list)
    git -C "$REPO_ROOT" worktree list
    ;;
  *)
    echo "usage: $0 {up|down} <name> | list" >&2
    exit 1
    ;;
esac
