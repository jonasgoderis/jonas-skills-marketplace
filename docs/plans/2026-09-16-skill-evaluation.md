# Skill evaluation for this marketplace

Status: proposal, not yet implemented. Written 2026-09-16.

How we could evaluate the skills in `claude-skills` before shipping them, using
the tooling Claude Code actually provides today rather than something we'd build.

## What "evaluation" has to mean here

Two separable questions, and they need different machinery:

1. **Does the skill fire when it should, and stay quiet when it shouldn't?**
   A description-matching problem. The failure mode is a skill that hijacks
   unrelated conversations, or one that never fires because its description is
   too narrow.
2. **When it fires, is the output any good?**
   A behavioural problem. The failure mode is a skill that triggers correctly
   and then produces a thin, wrong, or unusable result.

The first is cheap to test and the one we get wrong most often. The second is
expensive and only worth automating for the skills where quality actually varies.

## The tooling

### `claude plugin eval`

The primary mechanism. Requires Claude Code v2.1.269+ (v2.1.273 is installed
here). It runs a suite of prompts against the plugin in a fresh isolated
`claude -p` session, scores each run with graders, and by default *also* runs
the same prompts with no plugin loaded, reporting the delta. That ablation arm
is the interesting part: it answers "is this skill adding anything?", which is a
harder and more useful question than "did it pass?".

```
claude plugin eval [options] [target]
claude plugin eval init [options] [name]
```

`init` opens an interactive session that interviews you about the skill,
proposes should-trigger and should-not-trigger prompts, designs graders, pilots
them, and writes the case files. That is the intended starting point — it is
built around exactly the trigger-accuracy problem described above.
`--bare <name>` writes a blank placeholder non-interactively, for CI.

Flags worth knowing:

| Flag | Why it matters |
| --- | --- |
| `--ablation none \| with-without` | Turn off the baseline arm to halve cost |
| `--model` / `--judge-model` | Pin both in CI, or results drift under you |
| `--runs <n>` | Default 3; skill triggering is stochastic, don't trust 1 |
| `--threshold <0..1>` | Default 1.0. Any case below it exits 1 |
| `--max-cost-usd` | Hard ceiling; partial results and exit 2 if hit |
| `--allow-tools` | Grants gated tools (Bash, Write, WebFetch, `mcp__*`) |
| `--trust-plugin` | Required in CI, or the job blocks on the trust prompt |
| `--json [path]` | Full result document; quiet run |
| `--concurrency 1-8` | Default 1. Raise it and the wall clock collapses |

### Suite layout

Lives at `<plugin-root>/evals/` by default — so `plugin/evals/` for us.

```
plugin/
├── .claude-plugin/plugin.json
├── skills/
└── evals/
    ├── traveler-fires-on-trip-planning/
    │   ├── prompt.md
    │   ├── case.yaml          # only needed for context.* fields
    │   └── graders/
    │       ├── skill-fired.md
    │       └── criteria.md
    └── results/<timestamp>/    # aggregate-result.json, report.html
```

`prompt.md` carries case config in frontmatter and the prompt in the body:

```markdown
---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

We want to do a long weekend somewhere in northern Portugal in May, two of us,
we like hiking and good food. Where should we go?
```

### Graders

| Type | Passes when | Cost |
| --- | --- | --- |
| `regex` | Pattern found/absent/counted in output or a named file | free |
| `tool_used` | Calls to a tool matching `input_match` fall within `[min, max]` | free |
| `tool_order` | First matching `before` call precedes first matching `after` | free |
| `file_exists` | A file created during the run matches the glob | free |
| `llm` | Judge model votes PASS in ≥2 of 3 | paid |
| `baseline` | Judge finds the run at least as good as a reference transcript | paid |

Deterministic graders are free because they are computed from the transcript.
Reserve `llm` graders for short text — judge verdicts get noisier the longer the
output, which is precisely the wrong property for something like a full
itinerary. For long structured output, assert on the file with `regex` instead.

## Testing triggering

A `tool_used` grader on the `Skill` tool:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?the-traveler"'
---
```

Default `min: 1` asserts it fired. For a should-*not*-fire case — "help me debug
this Python script" must not summon a trip planner — set `min: 0, max: 0`.

**The trap:** under the default `with-without` ablation, every `tool_used`
grader targeting the `Skill` tool is excluded from the score in both arms and
reported only as a pass/fail indicator. A negative-trigger check written the
obvious way will look like it is passing while contributing nothing. It needs
`arm: both` set explicitly. This is the single most likely mistake in a
trigger-focused suite, and it fails silently.

## What this means per skill

The three skills in the plugin need quite different treatment, and two of them
are awkward to evaluate for reasons worth stating up front.

**`the-traveler`** — the only one where a trigger suite pays for itself. Its
description is broad and example-heavy ("plan a road trip to Scotland", "where
should we go this summer"), which is exactly the shape that over-fires. Worth
6–10 cases: three or four genuine trip prompts phrased differently, and three or
four adjacent-but-wrong ones (a commute question, a restaurant recommendation, a
geography question, "book me a flight") asserting `min: 0, max: 0` with
`arm: both`. Output quality is testable with `file_exists` on the itinerary plus
`regex` on its contents for the required sections.

**`context-handover`** and **`session-handoff`** — these two need trigger cases
for a reason specific to them: they are near-neighbours. Both are "handoff"
skills, and a prompt like "let's wrap up here" could plausibly pull either. The
cases that matter are the *disambiguating* ones — a prompt about clearing a
local Claude Code session must fire `context-handover` and not `session-handoff`
(`min: 0, max: 0`, `arm: both`), and one about a connected folder must do the
reverse. Their descriptions are the only thing separating them, so this is a
test of the descriptions more than of the skills.

Both were briefly given `disable-model-invocation: true`, which would have made
trigger evals moot by preventing auto-invocation entirely. That was reverted:
the field is Claude Code-only and not part of the Agent Skills spec, so it
breaks these skills for Chat and Cowork, where they are also used. Worth
recording as a general constraint — **any skill in this plugin that needs to run
outside Claude Code is limited to the spec fields** (`name`, `description`,
`license`, `compatibility`, `metadata`, `allowed-tools`), which means
description tuning is the *only* lever on trigger behaviour here. That makes the
eval suite more important, not less.

Output quality for these two is genuinely hard to test:

- Both summarise *a conversation*, and the eval sandbox starts from a fresh
  session with no history. A case can only test them against a synthetic prior
  conversation, via `case.yaml`'s `context.history_file` (resume a `.jsonl`
  transcript, with the case prompt as the next turn). That is the only honest
  way to eval either, and it means hand-building fixture transcripts.
- Both have side effects — writing files, and in `session-handoff`'s case
  committing into a connected folder. `session-handoff` additionally depends on
  Desktop-only tools (`device_bash`, `device_commit_files`) that do not exist in
  the eval sandbox. **`session-handoff` is effectively not evaluable with this
  tooling.** Say so rather than building a suite that tests a degraded path.
- `context-handover` *is* evaluable: give it a fixture transcript, run write
  mode, and assert with `file_exists` on `.claude/handover/*.md` plus `regex`
  graders for each required section heading. Then a second case runs resume mode
  against a pre-placed file and asserts the file is gone afterwards.

## The sandbox

Each run gets a throwaway home directory, working directory and Claude Code
config, with only the target plugin loaded — no personal settings, hooks,
CLAUDE.md, other plugins, memory or skills. Only an env allowlist plus `EVAL_*`
vars pass through, and the case definitions are hidden from the agent under
test. The Artifact tool is unavailable inside a run.

This is isolation for repeatability, not a security boundary: a suite that
passes says nothing about whether a plugin is safe.

## CI

```bash
claude plugin eval . \
  --trust-plugin \
  --json results.json \
  --threshold 0.8 \
  --model claude-sonnet-5 \
  --judge-model claude-haiku-4-5 \
  --no-publish \
  --max-cost-usd 20
```

Exit codes: `0` all cases at or above threshold; `1` below threshold, load
error, no cases, or untrusted directory without `--trust-plugin`; `2` partial
(cost ceiling or auth failure, with `partial: true` in the JSON); `130`
interrupted; `143` terminated. Needs an API key in the environment.

`aggregate-result.json` is `schemaVersion: 1`, camelCase, additive-only. A
gating script reads `partial`, `aggregates.overallScore`,
`aggregates.casesPassed` / `casesTotal`, `aggregates.meanDelta`, and per-case
`cases[].aggregates.score` / `.delta`. `report.html` is self-contained — verdict
line, tiles, per-case cards with delta, per-run grader chips with explanations.

## Adjacent tooling

- **`claude plugin validate <path>`** — structural and schema validation, not
  behaviour. Cheap, instant, and catches a malformed manifest before anything
  else runs. Add `--strict` to treat warnings as failures. This should be the
  first thing wired up, well before any eval suite.
- **`/skill-doctor`** — a usage and context-cost report, not a linter. Per-skill
  cost, 7-day tokens and uses, never-invoked warnings. Useful for spotting a
  skill that is loading its description into every conversation and never
  actually firing. Interactively it opens the plugin manager's Stats tab.
- **`skill-creator`** (`/plugin install skill-creator@claude-plugins-official`)
  — a separate, older eval system with its own `evals/evals.json` format, *not*
  interchangeable with `claude plugin eval`. Its useful feature is description
  tuning: it generates should-trigger and should-not-trigger prompts, measures
  hit rate, and proposes description edits when a skill activates on the wrong
  requests. That is directly aimed at `the-traveler`'s problem.
- **`claude --plugin-dir ./plugin`** — manual smoke test during development.

## Suggested order

1. `claude plugin validate plugin --strict` in CI. Cheap, and catches the
   failures that waste the most time.
2. A trigger suite for `the-traveler` only. Six to ten cases, roughly half
   negative, `arm: both` on the negatives.
3. Run `skill-creator`'s description tuner against `the-traveler` and fold the
   result back into its description.
4. Output-quality cases for `the-traveler` and `context-handover`, using fixture
   transcripts for the latter.
5. Leave `session-handoff` out. Revisit if the eval sandbox ever grows the
   Desktop tool surface.

## Open questions

- Cost per full run is unmeasured. Worth a single `--max-cost-usd 5` run with
  one case to calibrate before committing to a suite size.
- Whether the ablation arm is meaningful for a skill like `the-traveler`, where
  the no-plugin baseline will still produce *a* trip plan, just a worse one.
  That is a judge call on quality, which is the expensive grader type.
- Fixture transcript authoring for `context-handover` is unproven — the
  `context.history_file` mechanism is documented but we have not used it.

## Sources

Verified against the live Claude Code documentation on 2026-09-16 and against
`claude plugin eval --help` on the locally installed CLI (v2.1.273):

- https://code.claude.com/docs/en/plugin-evals.md
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/plugins.md

The `/skill-doctor` description comes from Claude Code's embedded reference;
there is no public documentation page for it yet. Nothing in this document has
been executed — no eval suite has been run against this plugin.
