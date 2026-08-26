#!/usr/bin/env python3
"""Deterministic benchmark harness for .agents/skills/python-code-review.

No third-party packages: subprocess + json + csv + argparse + pathlib,
all stdlib. Drives the `claude` CLI in headless mode and the skill's own
scripts/check_style.py as the scoring function.

Metrics computed (see docs/04-evaluation-and-benchmarking.md):
  0. Paired uplift: each quality case runs under both a with_skill and a
     baseline (skill folder absent) condition on the same commit, so the
     benchmark can answer "does the skill add anything" — not just "did
     this edit make the skill better or worse than its own last version."
  1. Trigger precision / recall  (from test_cases.json -> trigger_cases)
  2. Quality: violation-count reduction, before vs. after, per condition
  3. Reliability: pass^k across --repeat runs of each (case, condition)

Note: quality cases now run 2x --repeat calls each (with_skill + baseline),
so total `claude -p` invocations roughly double versus a with-skill-only run.

Usage:
    python .evals/run_evals.py                # full run, repeat=3
    python .evals/run_evals.py --repeat 1      # faster, less reliable
    python .evals/run_evals.py --skip-trigger  # quality cases only
    python .evals/run_evals.py --skip-quality  # trigger cases only
    python .evals/run_evals.py --critique      # qualitative SKILL.md review
                                                # (discovery/logic/edge-case),
                                                # prints for human judgment,
                                                # no CSV logging
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "python-code-review"
CHECKER = SKILL_DIR / "scripts" / "check_style.py"
TEST_CASES = Path(__file__).resolve().parent / "test_cases.json"
LOG_PATH = Path(__file__).resolve().parent / "eval_log.csv"
SKILL_NAME = "python-code-review"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def skill_version() -> str:
    """Short commit hash of the skill folder's last change, for the log."""
    result = run(["git", "log", "-1", "--format=%h", "--", str(SKILL_DIR)], cwd=REPO_ROOT)
    return result.stdout.strip() or "uncommitted"


def make_sandbox(case_id: str) -> Path:
    sandbox = REPO_ROOT / ".evals" / f"sandbox-{case_id}-{uuid.uuid4().hex[:6]}"
    result = run(["git", "worktree", "add", "--quiet", str(sandbox), "HEAD"], cwd=REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"git worktree add failed: {result.stderr}")
    return sandbox


def remove_sandbox(sandbox: Path) -> None:
    run(["git", "worktree", "remove", "--force", str(sandbox)], cwd=REPO_ROOT)
    shutil.rmtree(sandbox, ignore_errors=True)  # belt and braces


def claude_run(prompt: str, cwd: Path, allowed_tools: str) -> dict:
    """Invoke `claude -p` headlessly and return its parsed JSON result.

    The CLI exits 1 when it hits --max-turns with tool calls still pending
    (is_error:true, stop_reason:tool_use) — the JSON response is still valid
    and contains the full turn history, so we parse it regardless of exit code
    and only raise when stdout is genuinely unparseable."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--allowedTools", allowed_tools,
        "--max-turns", "20",
    ]
    result = run(cmd, cwd=cwd)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        if result.returncode != 0:
            raise RuntimeError(
                f"claude -p failed (exit {result.returncode}): {result.stderr[:500]}"
            )
        # Non-zero but unparseable stdout — fall back to raw text so a trigger
        # check can still string-match it.
        return {"result": result.stdout}


def violation_count(target: Path) -> int:
    result = run(["python3", str(CHECKER), str(target), "--json"])
    if result.returncode != 0:
        raise RuntimeError(f"check_style.py failed on {target}: {result.stderr}")
    return json.loads(result.stdout)["violation_count"]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill_tree(skill_dir: Path) -> str:
    lines = []
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            lines.append(str(p.relative_to(skill_dir)))
    return "\n".join(lines)


def run_critique() -> int:
    """Automate the three manual LLM-roleplay review steps against the
    current SKILL.md: discovery (does the description trigger/avoid the
    right prompts), logic (does the step-by-step avoid forcing the agent to
    guess), and edge cases (a ruthless-QA pass). Each is one read-only
    `claude -p` call; output is printed for a human to read and act on —
    this stays qualitative on purpose, there is no deterministic score for
    "is this instruction ambiguous." See docs/02 for the manual version of
    this same idea."""
    skill_md = load_text(SKILL_DIR / "SKILL.md")
    tree = skill_tree(SKILL_DIR)

    passes = {
        "1. Discovery validation": f"""
You are reviewing the frontmatter of an Agent Skill (agentskills.io spec).
Agents decide whether to load a skill based entirely on its `name` and
`description` fields, shown below.

---
{skill_md.split("---", 2)[1] if skill_md.count("---") >= 2 else skill_md}
---

Based strictly on this frontmatter:
1. Write 3 realistic user prompts you are confident SHOULD trigger this skill.
2. Write 3 prompts that sound similar but should NOT trigger it (near misses).
3. Say plainly whether the description is too broad, too narrow, or about
   right, and suggest a rewrite only if it needs one.
""",
        "2. Logic validation": f"""
Here is the full SKILL.md for an Agent Skill, and the file tree of its
supporting folder:

Tree:
{tree}

SKILL.md:
{skill_md}

Act as an agent that just triggered this skill for a real request:
"Review app/turbine_monitor.py against our python style guide and fix the
issues." Simulate your execution step by step. For each step, state exactly
what you are doing and which file you are reading or running. Explicitly
flag any point where the instructions are ambiguous enough that you would
have to guess rather than follow them directly.
""",
        "3. Edge case testing": f"""
Here is the full SKILL.md for an Agent Skill:

{skill_md}

Act as a ruthless QA tester whose job is to break this skill. Ask 3 to 5
specific, challenging questions about edge cases, failure states, or
missing fallbacks — for example, what happens if the checker script itself
has a bug, if the target file has a syntax error, or if a rule fires on
code the author considers a deliberate, justified exception. Do not answer
your own questions — just ask them.
""",
    }

    for title, prompt in passes.items():
        print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
        output = claude_run(prompt, cwd=REPO_ROOT, allowed_tools="Read,Grep")
        print(output.get("result", json.dumps(output, indent=2)))

    print(f"\n{'=' * 72}")
    print("This is qualitative — read the three passes above and decide "
          "whether SKILL.md needs edits. Re-run --critique after editing.")
    return 0


def eval_trigger_cases(cases: list[dict]) -> list[dict]:
    rows = []
    for case in cases:
        sandbox = make_sandbox(case["id"])
        try:
            # Read-only tools: a trigger check should never need to edit files.
            output = claude_run(case["prompt"], cwd=sandbox, allowed_tools="Read,Grep,Glob")
            triggered = SKILL_NAME in json.dumps(output)
            passed = triggered == case["should_trigger"]
            rows.append({
                "case_id": case["id"], "kind": "trigger", "condition": "with_skill",
                "expected_trigger": case["should_trigger"], "actual_trigger": triggered,
                "pass": passed, "before": "", "after": "", "reduction": "",
            })
        finally:
            remove_sandbox(sandbox)
    return rows


def eval_quality_cases(cases: list[dict], repeat: int) -> list[dict]:
    """Paired evaluation: each case runs under both a `with_skill` and a
    `baseline` (skill folder physically absent) condition, matched on the
    same commit and the same prompt. This is what lets the benchmark answer
    "does the skill add anything over the agent's unaided behavior" rather
    than only "did this edit make the skill better or worse than before" —
    see docs/04-evaluation-and-benchmarking.md, Metric 0."""
    rows = []
    for case in cases:
        target_rel = case["target_file"]
        for condition in ("with_skill", "baseline"):
            for run_idx in range(repeat):
                sandbox = make_sandbox(f"{case['id']}-{condition}-r{run_idx}")
                try:
                    if condition == "baseline":
                        shutil.rmtree(sandbox / ".agents" / "skills" / SKILL_NAME,
                                       ignore_errors=True)

                    target = sandbox / target_rel
                    before = violation_count(target)
                    claude_run(
                        case["prompt"], cwd=sandbox,
                        allowed_tools="Read,Edit,Bash(python3 .agents/skills/python-code-review/scripts/check_style.py:*)",
                    )
                    after = violation_count(target)
                    rows.append({
                        "case_id": f"{case['id']}#{run_idx}", "kind": "quality",
                        "condition": condition,
                        "expected_trigger": "", "actual_trigger": "",
                        "pass": after == 0, "before": before, "after": after,
                        "reduction": before - after,
                    })
                finally:
                    remove_sandbox(sandbox)
    return rows


def write_log(rows: list[dict]) -> None:
    version = skill_version()
    timestamp = datetime.now(timezone.utc).isoformat()
    fieldnames = ["timestamp", "skill_version", "case_id", "kind", "condition",
                  "expected_trigger", "actual_trigger", "pass",
                  "before", "after", "reduction"]
    is_new = not LOG_PATH.exists()
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_new:
            writer.writeheader()
        for row in rows:
            writer.writerow({"timestamp": timestamp, "skill_version": version, **row})


def summarize(rows: list[dict]) -> None:
    trigger_rows = [r for r in rows if r["kind"] == "trigger"]
    quality_rows = [r for r in rows if r["kind"] == "quality"]

    if trigger_rows:
        tp = sum(1 for r in trigger_rows if r["expected_trigger"] and r["actual_trigger"])
        fp = sum(1 for r in trigger_rows if not r["expected_trigger"] and r["actual_trigger"])
        fn = sum(1 for r in trigger_rows if r["expected_trigger"] and not r["actual_trigger"])
        precision = tp / (tp + fp) if (tp + fp) else float("nan")
        recall = tp / (tp + fn) if (tp + fn) else float("nan")
        print(f"Trigger accuracy: precision={precision:.2f} recall={recall:.2f} "
              f"({tp} TP, {fp} FP, {fn} FN, {len(trigger_rows)} cases)")

    if quality_rows:
        for condition in ("with_skill", "baseline"):
            rows_c = [r for r in quality_rows if r["condition"] == condition]
            if not rows_c:
                continue
            avg_reduction = sum(r["reduction"] for r in rows_c) / len(rows_c)
            pass_k = sum(1 for r in rows_c if r["pass"]) / len(rows_c)
            print(f"Quality [{condition}]: avg violation reduction={avg_reduction:.1f}, "
                  f"fully-clean rate={pass_k:.0%} ({len(rows_c)} runs)")

        with_rows = [r for r in quality_rows if r["condition"] == "with_skill"]
        base_rows = [r for r in quality_rows if r["condition"] == "baseline"]
        if with_rows and base_rows:
            with_pct = 100 * sum(1 for r in with_rows if r["pass"]) / len(with_rows)
            base_pct = 100 * sum(1 for r in base_rows if r["pass"]) / len(base_rows)
            gain_pp = with_pct - base_pct
            print(f"Paired uplift (with_skill - baseline): {gain_pp:+.1f} pp "
                  f"fully-clean rate.")
            if base_pct >= 100:
                print("Normalized gain: undefined (baseline already at 100% — "
                      "raw pp above is the only meaningful number here; add "
                      "harder quality cases if you want headroom to measure).")
            else:
                normalized = 100 * gain_pp / (100 - base_pct)
                print(f"Normalized gain: {normalized:+.1f}% "
                      f"= (with - baseline) / (100 - baseline), "
                      f"SkillsBench's formula so a skill can't look strong "
                      f"purely because the baseline was already weak.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=3,
                         help="times to repeat each quality case (pass^k)")
    parser.add_argument("--skip-trigger", action="store_true")
    parser.add_argument("--skip-quality", action="store_true")
    parser.add_argument("--critique", action="store_true",
                         help="run the qualitative discovery/logic/edge-case "
                              "review against SKILL.md instead of the "
                              "quantitative benchmark, then exit")
    args = parser.parse_args()

    if shutil.which("claude") is None:
        print("ERROR: the `claude` CLI is not on PATH. Install it with "
              "`npm i -g @anthropic-ai/claude-code` and authenticate first.", file=sys.stderr)
        return 1

    if args.critique:
        return run_critique()

    with open(TEST_CASES) as f:
        cases = json.load(f)

    rows: list[dict] = []
    if not args.skip_trigger:
        rows += eval_trigger_cases(cases["trigger_cases"])
    if not args.skip_quality:
        rows += eval_quality_cases(cases["quality_cases"], repeat=args.repeat)

    write_log(rows)
    summarize(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
