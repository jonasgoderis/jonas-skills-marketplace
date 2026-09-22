# Evaluating the release-version skill

Status: proposal, awaiting a choice. Written 2026-09-18.

Companion to `2026-09-16-skill-evaluation.md`, which surveyed the tooling and
covered the three skills that existed then. `release-version` was added after it
was written and is not discussed there. This document is about that skill
specifically, because it evaluates differently from the others.

## Why this skill is a different problem

The other three skills are mostly prose: the model reads the body and produces
an answer. `release-version` is prose *plus* a 600-line shell script, and the
skill's own thesis is the split between them — `scripts/version.sh` owns every
state change, the model owns only the judgement and the English.

That split cuts the evaluation problem in two along the same line:

- **`version.sh` is ordinary software.** Version-source detection across six
  manifest formats, drift detection, semver arithmetic, in-place JSON editing,
  the test gate, the dirty-tree refusal. None of it needs a model to test. All of
  it breaks silently and is the part that, if wrong, corrupts manifests in
  someone else's repo.
- **The model's half is a procedure with hard rules.** Run `check` first. Read
  the commits, not the conversation. Dry run before the real thing. *Stop and
  wait before opening a PR.* Never hand-edit a version. Never reach for
  `--no-test` by reflex. These are behaviours, and behaviours need an agent run
  to observe.

A third question sits above both: does the skill fire at the right times? Its
description is deliberately pushy ("reach for it even when the word release is
never said"), which is the shape that over-fires — onto "bump the lodash
dependency", "what Node version is this", "what changed since Friday".

## Constraints the sandbox imposes

`claude plugin eval` gives each run a throwaway home, working directory and
config. For this skill that matters more than for the others:

- There is no git repo with a GitHub remote, and `gh` is not authenticated.
  `version.sh check` will fail in a bare sandbox — correctly, but that means a
  realistic case has to build its own world.
- `scaffold_script` (behind the `--scaffold` flag) runs author-supplied bash
  before the case. That is the enabler: a scaffold can `git init` a fixture repo
  with commits and a manifest, and drop a stub `gh` onto `PATH` that records its
  arguments instead of talking to GitHub. Without it, only trigger cases are
  possible.
- The skill needs `Bash`, so cases need `--allow-tools Bash`. Both flags run
  author-supplied code as you — fine for a suite in this repo, worth knowing
  before wiring it into CI.
- Under the default `with-without` ablation, a `tool_used: Skill` grader is
  reported as a plugin-fired indicator rather than scored. Negative trigger
  cases need `arm: both` set explicitly or they pass while asserting nothing.

## The options

### Option A — Trigger suite only

Six to ten `claude plugin eval` cases, no scaffold, no git fixture. Each is a
prompt plus a `tool_used` grader on the `Skill` tool.

Positive: "I think we're ready to ship this", "what should the next version be?",
"write the changelog for this branch", "get this branch out the door".
Negative (`min: 0, max: 0`, `arm: both`): "bump the lodash dependency", "what
Node version does this project need", "what changed since Friday", "create a PR
for this work" — that last one is the interesting near-miss, because opening a PR
is something the skill does but not something it should own.

- Cheap, quick to author, no `--scaffold` or `--allow-tools` needed.
- Tests the description, which is the only lever on trigger behaviour.
- Tests nothing about whether the release itself is done correctly. A skill that
  fires perfectly and then hand-edits `marketplace.json` scores full marks.

### Option B — `version.sh` unit tests, no model in the loop

A plain-bash test file (or `bats` if you want the harness) that builds throwaway
repos in a temp dir and asserts on `version.sh` directly, via `--repo`.

Roughly the cases worth having:

| Area | Assertion |
| --- | --- |
| Detection | Each of `VERSION`, `package.json`, `pyproject.toml` (both `[project]` and `[tool.poetry]`), `Cargo.toml`, `marketplace.json`, `*/plugin.json` is found |
| Multi-source | Two sources agreeing bump together; two disagreeing abort and name both |
| Arithmetic | `major`/`minor`/`patch`/explicit `X.Y.Z`; `1.9.0` → `2.0.0`, not `1.10.0` |
| Refusals | A prerelease in a source is an error; a non-semver string is an error |
| JSON editing | The diff is one changed line per file; a hand-formatted manifest survives byte-identical elsewhere |
| Dry run | `bump --dry-run` leaves every file unmodified |
| Test gate | A failing test command aborts with the tree untouched; a missing command stops rather than proceeding |
| Repo state | A dirty tree is refused; the bump is its own commit |
| PR body | Records the test command that ran, or that tests were skipped |

- Free, deterministic, sub-second, no API key, runs in `scripts/test.sh` today.
- Catches the class of bug that actually damages other people's repos.
- Says nothing about whether the model follows the procedure, or fires at all.

### Option C — Behavioural eval against a scaffolded repo

Two or three `claude plugin eval` cases with a `scaffold_script` that builds a
fixture repo — a few commits with a mix of features and fixes, a `VERSION` file
and a `marketplace.json`, a passing `scripts/test.sh`, and a stub `gh` on `PATH`
that logs its arguments to a file and exits 0.

The graders are where the value is, and most of them are free:

- `tool_order`: `version.sh check` precedes `version.sh release`.
- `tool_used` with `input_match` on `git log`: the model read the commits.
- `tool_used` on `--dry-run`: the dry run happened before the real call.
- `regex`, absent, on the transcript: no `gh pr create`, no `Edit`/`Write`
  touching `VERSION` or a manifest.
- `regex` on the stub `gh` log: **empty** — the run stopped for approval instead
  of opening a PR unprompted. This is the single most valuable assertion in the
  whole suite, because it is the failure with a real-world cost.
- One `llm` grader on the proposed changelog: does each bullet correspond to a
  commit in the fixture, and is the level argued from the diff?

- The only option that tests what the skill claims about itself.
- Needs `--scaffold` and `--allow-tools Bash`; author-supplied bash running as
  you. Slowest and the only one with a per-run API cost.
- Fixture authoring is unproven here — `scaffold_script` has not been used in
  this repo yet, and the stub-`gh`-on-`PATH` trick may need a round of debugging.

### Option D — All three, in order: B, then A, then C

B first because it is free and protects the dangerous part. A second because it
is cheap and the description is the only lever available. C last, small, once the
first two are green and the fixture mechanics are understood.

Add `claude plugin validate plugin --strict` to `scripts/test.sh` alongside B —
it is instant and catches a malformed manifest before anything else runs.

## Two decisions that come with any of these

**Where the eval suite lives.** The default is `plugin/evals/`, which means the
cases ship to everyone who installs the plugin. A repo-level `evals/` with
`--eval-dir` keeps the published plugin lean, at the cost of the default path no
longer working. Worth deciding once, now.

**Whether evals gate a release.** `scripts/test.sh` is already the test gate that
`version.sh release` runs, so anything added to it blocks a release the moment it
goes red. That is right for B and for `validate`. It is probably wrong for A and
C, which cost money and are stochastic — better as a separate script run
deliberately, or on a schedule.

## What has been verified

- `claude plugin eval` and `claude plugin eval init` exist on the installed CLI
  (v2.1.276); the flags named above come from `--help` on that binary.
- `scaffold_script`, `--scaffold`, `--allow-tools` and the `with-without`
  ablation behaviour for `tool_used: Skill` are documented in that same help
  output.
- The `version.sh` surface described in Option B was read from the script.

Not verified: nothing here has been run. No eval case has ever been executed
against this plugin, and the cost of a run is still unmeasured.
