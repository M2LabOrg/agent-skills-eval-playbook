# 4. Evaluation and benchmarking — without a framework

This repo's paired with-skill/baseline design (Metric 0 below) follows the
same principle published benchmarks for Agent Skills use as their
foundation: measure the same task under matched no-skill and with-skill
conditions and report the gap, rather than judging a skill's output in
isolation. Nothing here depends on any such benchmark, package, or external
tool — it's the same idea implemented from scratch in plain Python against
this repo's own toy app.

Two different questions need two different measurements. Conflating them is
the most common mistake in skill evals.

1. **Does the skill trigger at the right times?** — a routing question,
   answered by the `description` field.
2. **Does the skill produce good output once it fires?** — a quality
   question, answered by whatever the skill actually does.

Both are answered here with plain Python (`ast`, `subprocess`, `json`,
`csv` — nothing installed) driving the `claude` CLI in headless mode
(`claude -p "..." --output-format json`), which runs one prompt to
completion and exits. See
[`.evals/run_evals.py`](../.evals/run_evals.py).

## Metric 0 — Paired uplift (with-skill vs. baseline)

The question a skill eval most needs to answer isn't "did this edit make
the skill better than its previous version" — it's the more basic "does
this skill add anything over the agent's unaided behavior at all." A
capable model might already write docstrings and type hints unprompted;
if so, a benchmark that only ever runs *with* the skill present would
never notice the skill is dead weight.

So every quality case in this repo runs twice per repetition, on the same
commit, with the same prompt: once with `.agents/skills/python-code-review/`
present (`with_skill`), and once with that folder deleted from the sandbox
before the agent runs (`baseline`). `run_evals.py` reports the fully-clean
rate for each condition separately, the raw gap in percentage points, and
a **normalized gain**: `(with − baseline) / (100 − baseline)`. The raw pp
gap alone can be misleading at small scale — a skill that closes a
baseline's 20-point gap looks identical in raw pp to one that closes a
90-point gap unless you normalize against how much headroom the baseline
left. With only two quality cases in this repo the normalized number is
mostly illustrative; it earns its keep once you add enough cases that
baseline performance varies meaningfully across them.

## Metric 0.5 — Qualitative review (`--critique`)

Three of the manual review steps described in `docs/02` — pasting
`SKILL.md` into a fresh chat to check triggering, to simulate step-by-step
execution, and to have the model attack it as a ruthless QA tester — are
automated by `python .evals/run_evals.py --critique`. It runs each of the
three as a single read-only `claude -p` call and prints the output; it does
**not** produce a pass/fail score, because "is this instruction ambiguous"
isn't something a script can grade. Read the output, decide whether
`SKILL.md` needs an edit, and re-run after making one.

## Metric 1 — Trigger precision & recall

[`.evals/test_cases.json`](../.evals/test_cases.json) lists two kinds of
prompts:

- **True positives** — realistic requests that should load
  `python-code-review` ("review app/turbine_monitor.py before I open a PR").
- **True negatives** — near-miss requests that should not ("explain what
  Flask's request object does", "review our Vue component naming").

`run_evals.py` runs every case through `claude -p`, checks whether the
skill's name appears in the run's tool-use trace, and reports:

- **Recall** — of the prompts that *should* trigger it, how many did.
  Low recall means the description is too narrow.
- **Precision** — of the prompts that triggered it, how many *should have*.
  Low precision means the description is too broad.

## Metric 2 — Quality, measured as a before/after violation count

This is the part that avoids needing an LLM-as-judge (and therefore avoids
needing any eval package at all): `scripts/check_style.py` inside the skill
is a deterministic linter. The benchmark:

1. Counts violations in the target file **before** the agent runs.
2. Lets the agent run the skill and edit the file.
3. Counts violations **after**.
4. Reports `reduction = before - after`.

That number is the whole quality score. It's reproducible, requires no
subjective judgment, and directly answers "did this change to `SKILL.md`
make the skill better or worse at its one job." Edit the skill, re-run
`run_evals.py`, compare `reduction` to the previous logged run.

## Metric 3 — Reliability (pass^k)

Agents are stochastic. Run each quality case `--repeat N` times (default 3)
and report how many of the `N` runs fully resolved all violations
(`reduction == before`, i.e. `after == 0`). A skill that fixes everything
on 1 of 3 runs is not the same as one that fixes everything on 3 of 3, even
though a single run of either might look identical.

## Reading `eval_log.csv`

`run_evals.py` appends one row per case per run: timestamp, case id,
`condition` (`with_skill` or `baseline`, `""` for trigger cases), metric
values, and the skill version (short git commit hash of
`.agents/skills/`). Diff this file after any `SKILL.md` edit — a regression
shows up as a lower `reduction` or a flipped `pass`/`fail` on a case that
used to pass, on the `with_skill` rows specifically. The `baseline` rows
shouldn't change at all between runs unless the toy app or prompts changed
— if they do, something about the sandbox setup is leaking state.

## Where this runs

Every run happens inside an isolated `git worktree`, never your real working
tree — see [`05-sandbox-worktrees.md`](05-sandbox-worktrees.md). The same
script also runs in CI: [`.github/workflows/skill-eval.yml`](../.github/workflows/skill-eval.yml)
triggers on any pull request touching `.agents/skills/**`, so a skill change
gets the same benchmark a human would run locally, automatically, before
merge.
