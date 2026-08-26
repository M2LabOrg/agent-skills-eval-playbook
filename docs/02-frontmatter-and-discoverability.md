# 2. Frontmatter and discoverability

Before a skill's body is ever loaded, the agent sees exactly two fields:
`name` and `description`. That's the entire routing signal. If they're
vague, the skill is invisible or — worse — fires on the wrong tasks.

## `name`

- 1–64 characters, lowercase letters, numbers, and single hyphens only.
- Must exactly match the parent directory.
- Should read like a slug you'd recognize in a list of fifty other skills:
  `python-code-review`, not `review` or `helper`.

## `description`

This is the only field the agent uses to decide *when* to load the skill —
so it has to do two jobs at once: say what the skill does, and say what it
is **not** for.

Bad:

> "Reviews Python code."

Good (this repo's actual skill description):

> "Reviews Python source files against this repo's style guide (docstrings,
> type hints, mutable defaults, bare excepts) and proposes fixes... Use when
> the user asks to review, lint, clean up, or improve Python code in this
> repository, or before opening a PR. Do not use for non-Python files, for
> architectural/design review, or for style questions about JavaScript, Vue,
> or other languages."

Three ingredients make the difference:

1. **Third-person, capability-first.** Describe what the skill does, not
   "I will help you..." — the agent is matching this against a task, not
   reading it as conversation.
2. **Trigger phrases from real requests.** Include the words engineers
   actually use ("review", "lint", "clean up", "before I open a PR"), not
   just the formal name of the capability.
3. **Negative triggers.** Explicitly rule out the nearest confusable cases.
   This is what stops a `python-code-review` skill from firing on a request
   to review Vue components, or a `react-styling` skill from firing on a
   request to bump a React version number.

## Testing a description before you commit to it

You don't need any tooling for this — paste the frontmatter into a fresh
chat with an LLM and ask it to (a) generate three prompts that should
obviously trigger the skill, (b) generate three near-miss prompts that
should *not*, and (c) critique whether the description is too broad or too
narrow. This repo turns exactly that idea into an automated, repeatable
check — see
[`04-evaluation-and-benchmarking.md`](04-evaluation-and-benchmarking.md) and
[`.evals/test_cases.json`](../.evals/test_cases.json), where the "near-miss"
prompts are written down once and re-run on every change instead of
re-invented by hand each time.
