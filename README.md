# Agent Skills Eval Playbook

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![eval harness: stdlib only](https://img.shields.io/badge/eval%20harness-stdlib%20only-green.svg)
![Works with Claude Code](https://img.shields.io/badge/works%20with-Claude%20Code-blueviolet.svg)

A small, self-contained repo that teaches engineers how to write **Agent
Skills** that don't bloat an agent's context window, and how to **evaluate
and benchmark** those skills with quantifiable, deterministic metrics — no
third-party eval frameworks, just Python's standard library, git, and the
`claude` CLI.

It targets engineers using Claude (Claude Code / Claude in VS Code) and
Copilot-style agents that support the open `agentskills.io` folder
convention (`SKILL.md` + `scripts/` + `references/` + `assets/`).

## What you'll learn

- How to structure a skill so an agent loads only what it needs, when it
  needs it (`docs/01`–`03`)
- How to measure, quantifiably, whether a skill is actually helping —
  including a **paired with-skill vs. baseline comparison**, the same
  principle published Agent Skills benchmarks use as their foundation
  (`docs/04`)
- How to run those measurements in an isolated sandbox so a bad agent run
  never touches your real working directory (`docs/05`)

## Prerequisites

- Python 3.10+ and `git`
- Node.js + npm, to install the Claude Code CLI: `npm i -g @anthropic-ai/claude-code`
- The `claude` CLI authenticated (`claude` once, interactively, to log in) —
  only needed for the "try the skill" and benchmark steps below, not for
  reading the docs

## What's here

| Path | Purpose |
|---|---|
| `docs/` | The lessons — read these in order |
| `.agents/skills/python-code-review/` | One real, working example skill |
| `app/` | A toy Flask wind-turbine sensor monitoring service with intentional style issues, used as the skill's target |
| `.evals/` | A from-scratch benchmark harness: trigger precision/recall, a paired with-skill/baseline uplift score (raw + normalized gain), pass^k reliability, and a `--critique` mode for qualitative SKILL.md review |

## Quickstart

```bash
git clone <your-fork-url>
cd agent-skills-eval-playbook
python3 -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt

# Run the toy app
python app/app.py

# Try the skill by hand (requires the Claude Code CLI, `npm i -g @anthropic-ai/claude-code`)
claude -p "Review app/turbine_monitor.py against our python style guide and fix the issues"

# Run the deterministic benchmark
python .evals/run_evals.py
```

### Expected output

`run_evals.py` prints a summary like this (numbers vary run to run — agents
are stochastic, which is exactly why `docs/04` also tracks a pass^k
reliability rate):

```
Trigger accuracy: precision=1.00 recall=1.00 (3 TP, 0 FP, 0 FN, 7 cases)
Quality [with_skill]: avg violation reduction=6.5, fully-clean rate=100% (6 runs)
Quality [baseline]: avg violation reduction=3.2, fully-clean rate=17% (6 runs)
Paired uplift (with_skill - baseline): +83.0 pp fully-clean rate. This is the
number that answers 'does the skill add anything over unaided behavior.'
```

Every run also appends rows to `.evals/eval_log.csv` — that file is your
regression history across `SKILL.md` edits.

For a qualitative check instead — is the description well-targeted, are the
steps unambiguous, what breaks it — run:

```bash
python .evals/run_evals.py --critique
```

This prints three read-only review passes against the current `SKILL.md`
for you to read and act on; see `docs/04` for what each one covers.

If you see `ERROR: the claude CLI is not on PATH`, install and authenticate
it first (see Prerequisites above) — the docs and skill are still fully
readable without it, only the live benchmark needs it.

## Reading order

1. [`docs/01-skill-structure.md`](docs/01-skill-structure.md) — the folder layout and why each part exists
2. [`docs/02-frontmatter-and-discoverability.md`](docs/02-frontmatter-and-discoverability.md) — writing a `name`/`description` that triggers reliably
3. [`docs/03-progressive-disclosure.md`](docs/03-progressive-disclosure.md) — keeping `SKILL.md` lean, and what belongs in `references/`, `scripts/`, `assets/`
4. [`docs/04-evaluation-and-benchmarking.md`](docs/04-evaluation-and-benchmarking.md) — the metrics this repo computes and how to read them
5. [`docs/05-sandbox-worktrees.md`](docs/05-sandbox-worktrees.md) — why evals run in a `git worktree` sandbox, never your main working tree

## The worked example

`.agents/skills/python-code-review/` reviews Python files against four
deterministic rules (bare `except`, missing docstrings, mutable default
arguments, missing type hints), fixes them, and reports back using a fixed
template. It's small on purpose — small enough to read end to end in five
minutes, and small enough that the benchmark's numbers are easy to trust.

## Design constraints this repo follows

- **No third-party eval packages.** The benchmark harness in `.evals/` is
  plain Python (`ast`, `subprocess`, `json`, `csv`) — nothing to `pip install`
  beyond Flask for the toy app itself.
- **Deterministic scoring.** The quality score is "how many rule violations
  did the agent remove," counted by a script, not judged by another LLM call.
- **Sandbox isolation.** Every eval run happens in its own `git worktree` so
  a bad agent run can never touch your real working directory or main branch.

## License

MIT — see [`LICENSE`](LICENSE).
