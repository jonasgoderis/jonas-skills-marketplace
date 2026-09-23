# Plan: evaluate-session

Proposed 2026-09-22, from `todo/evaluate-best-practices.md`. Not yet started.

The todo asks for two things that look like one: a written, numbered catalogue of
AI-use best practices, and a hook that grades a finished session against it. They
are separable, and the catalogue is the harder and more durable half — the hook is
plumbing around it.

Two decisions were taken before writing this, and the plan assumes them:

- **The plugin ships the skill, the rubric and the scripts, but no active hook.**
  A plugin's `hooks/hooks.json` is live the moment the plugin is enabled, so an
  auto-on hook would spend every installer's tokens on every exit without them
  asking. Installation of the hook is an explicit step, on this machine too.
- **Once installed, it runs on every real exit, on Haiku 4.5.** A script
  compresses the transcript before anything reaches the model, so the graded input
  is small.

---

## What was verified

Checked directly, so the plan does not rest on assumption:

| Claim | How it was checked |
| --- | --- |
| `SessionEnd` is a real hook event on 2.1.278 | present in the CLI binary alongside the other seven events |
| Hook input carries `transcript_path` | `transcript_path` present in the binary; the field is what makes this feasible at all |
| `prompt_input_exit` and `other` are SessionEnd reasons | both appear, adjacent, in the binary's reason union |
| Plugins can ship hooks and reference `${CLAUDE_PLUGIN_ROOT}` | `hooks.json` and `CLAUDE_PLUGIN_ROOT` both present |
| Transcripts are queryable JSONL | `~/.claude/projects/<slug>/<session-id>.jsonl`, one JSON object per line, `.type` in `user`/`assistant`/`system`/`attachment`/… — parsed a real one with `jq` |
| A headless grading call is possible | `claude -p --model haiku --output-format json --restricted` — every flag exists |

Not yet verified, and each has a named fallback below: whether `clear` and
`logout` are also SessionEnd reasons; whether SessionEnd stdout is rendered
anywhere before the process exits; whether a `SessionStart` hook's stdout reaches
the next session's context.

`--bare` looked like the clean way to stop the grading run from recursively
firing the hook, but it refuses OAuth and keychain auth — it wants
`ANTHROPIC_API_KEY`. Unusable on a subscription. The guard is an environment
variable instead (below).

---

## Shape

```
plugin/skills/evaluate-session/
├── SKILL.md                        the on-demand half, and the install story
├── references/
│   ├── best-practices.md           the numbered catalogue — BP-01 … BP-19
│   ├── rubric.md                   how a grade is assigned, for the grader prompt
│   └── architecture.md             added in build: how the pieces relate
├── scripts/
│   ├── digest.py                   transcript JSONL → compact evidence digest
│   ├── evaluate.sh                 digest → graded report on disk
│   ├── hook.sh                     SessionEnd payload → evaluate.sh, detached
│   └── enable-hook.sh              switches automatic grading on and off
└── assets/
    ├── grader-prompt.md            the fixed prompt the headless call is given
    └── secret-patterns.txt         the privacy gate's built-in patterns
```

Two departures from this, both decided while building. The digest is `digest.py`
rather than `digest.sh` — uuid dedupe, nested message content and five exclusion
rules are write-only code in bash and jq. And `install-hook.sh` became
`enable-hook.sh` when the hook stopped being installed at all; see the superseded
section below.

Nothing here is invented for this repo's convenience: the catalogue in
`references/` is the progressive-disclosure rule from `CLAUDE.md` (the rubric is
long and only needed when the skill fires), and everything in `scripts/` is a
fixed procedure that a model would otherwise reconstruct slightly differently
every run.

### Name and triggering

Settled: **`evaluate-session`**. The output it produces is still called a
scorecard — that is the artifact, not the skill.

The reasoning that was offered for it does not survive checking, so it is
recorded here to stop it being re-derived. **There is no verb or gerund
convention for skill names.** Checked in three places:

- `skill-creator`, which `CLAUDE.md` names as the authority, defines the field as
  "**name**: Skill identifier" and says nothing else about it.
- The only rule enforced anywhere is in `skill-creator/scripts/quick_validate.py`:
  kebab-case, lowercase letters, digits and hyphens, no leading or trailing
  hyphen, no consecutive hyphens. That is the whole of it.
- Empirically, across the 25 skills in Anthropic's official plugin marketplace,
  nouns outnumber verbs roughly four to one — `skill-development`,
  `hook-development`, `plugin-structure`, `frontend-design`, `session-report`,
  `claude-security`. The verb-first ones are a minority (`build-mcp-server`,
  `build-mcpb`, `m5-onboard`) and there is a single gerund (`writing-rules`).

The likely source of the belief is real, and worth keeping straight: this repo's
`CLAUDE.md` does say **"Imperative instructions. 'Read the commits', not 'you
should read'."** That rule is about the instruction prose inside `SKILL.md`. It
does not reach the `name` field.

So `evaluate-session` is valid — kebab-case, verb-first like a handful of
Anthropic's own — just not *required*. One reservation, noted and overruled: it
names the session as the object being evaluated, when the thing actually graded
is how the user drove it. `evaluate-practices` would have been more precise.
Since the name does not drive triggering, this is a readability point only.

**The description is what triggers, and it gets tested rather than argued.**
skill-creator is emphatic that Claude under-triggers, so the description leans
pushy on performance contexts — "how did I do", "grade this session", "which
practices am I weakest on", and the case where the user wants the feedback
without naming it. It is not pre-narrowed to avoid competing with
`context-handover` and `session-handoff`; that competition is settled by the
trigger evals in Phase 4, whose negative cases are exactly those near-misses.

Not at stake in any of the above: **the hook path is not skill triggering.** A
`SessionEnd` hook runs a shell command and never matches a description against a
prompt, so nothing the sibling skills say can suppress the automatic evaluation.

### Prior art — Anthropic's `session-report`

Found while checking the naming question. Anthropic ships an official
`session-report` skill that reads the same `~/.claude/projects` transcripts, and
bundles `analyze-sessions.mjs` to parse them.

It is **not** a duplicate: it reports *usage* — tokens, cache hit rate, subagent
spend, expensive prompts — where this skill judges *practice*. Adjacent, not
overlapping.

But its analyser already solves the transcript-parsing half of `digest.sh`,
including multi-session aggregation. Read it before writing `digest.sh` in
Phase 2 rather than reinventing the parse. Its `--json --since 7d` output shape
is also a candidate signal source: cache breaks and prompt cost are evidence for
BP-01 and BP-05 that a transcript read alone would not surface.

## The catalogue — `references/best-practices.md`

Your list, reorganised into five groups and given stable `BP-nn` identifiers. The
numbers are the contract: the grader cites them, and you look them up. Once
published, a number never changes meaning — a retired practice keeps its number
and gets marked retired.

Each entry gets: the name, one paragraph on what it means and *why* it matters,
what doing it well looks like, and — this is the part that makes the grading
honest — how observable it is from a transcript.

**Context and scope**
- BP-01 Watch the context, hand off before it rots
- BP-02 Split project context across files instead of one big CLAUDE.md
- BP-03 Break big tasks into small, checkable steps
- BP-04 One session, one subject
- BP-05 Checkpoint knowledge to disk, not to the conversation

**Asking well**
- BP-06 Be specific — goal, constraints, audience
- BP-07 Show one concrete example of what you want
- BP-08 Spell out the format
- BP-09 Iterate; treat the first answer as a draft
- BP-10 Don't inject the answer — over-seeding with examples narrows the reply
- BP-11 Zoom out first, zoom in on request

**Delegation and determinism**
- BP-12 Send wide, read-heavy work to a subagent
- BP-13 Offload deterministic work to scripts
- BP-14 Use reference files in skills so context loads on demand

**Trust**
- BP-15 Verify; confident and correct are different things
- BP-16 Read the actual diff before accepting
- BP-17 Keep a human deciding anything with real consequences
- BP-18 Mind what you share

**Setup**
- BP-19 Keep rules in separate `.claude/rules` files

Three observability tiers, because pretending otherwise produces a grade that
punishes you for things the transcript cannot show:

- **Direct** — BP-03, BP-04, BP-06, BP-07, BP-08, BP-09, BP-10, BP-11, BP-12,
  BP-18. Visible in what you typed and what happened next.
- **Indirect** — BP-01, BP-05, BP-13, BP-15, BP-16, BP-17. Inferable from
  signals (was a handoff written before the context filled, were commits made,
  did a script exist for the repeated thing) but not proof.
- **Structural** — BP-02, BP-14, BP-19. Properties of the repo and your config,
  not of the session. Checked once by `digest.sh` looking at the filesystem, not
  guessed by the grader.

Ungraded practices still belong in the catalogue. It is a reference you'll read
outside this hook, and a list that only contains what is convenient to grade is a
worse list.

---

## `digest.sh` — the part that must not be a model's job

Input: a transcript path. Output: a compact evidence digest, JSON.

It exists for three reasons at once. A 1.8 MB transcript is too expensive to
grade raw. Extraction is a fixed procedure, so it belongs in a script. And it is
the privacy boundary: what it does not extract does not reach the grading call.

Extracted:

- Session metadata — id, project, start and end time, duration, turn count.
- **Every user message, verbatim.** This is the thing being graded; paraphrasing
  it would grade the paraphrase. Slash-command invocations and the skill
  preambles they expand into are recorded as `command: /name` and dropped.
- Assistant turns reduced to a **shape**: tool names in order, counts, whether a
  subagent was launched, how many files were edited, whether tests ran. Never the
  prose, never tool output, never file contents.
- Signals — context-window pressure and compaction events, whether a handover or
  checkpoint file was written, git commits made during the session.
- Structural facts, read from the filesystem rather than the transcript: does the
  project have a `CLAUDE.md` and is it split, does `.claude/rules/` exist, do
  skills present use `references/`.

Deliberately not extracted: assistant prose, tool results, file contents,
diffs, environment variables. A transcript is exactly the kind of file that
contains a pasted token or a client name; a digest that never carries tool output
cannot leak one by accident. `digest.sh` also refuses to emit a digest whose user
messages match the secret patterns already used by
`~/.claude/hooks/guard-outbound.sh`, and says so in the report instead.

Target size: under 15k tokens for a long session. Truncation is by whole user
messages from the oldest end, and the digest records that it truncated.

---

## `evaluate.sh` — the graded report

```
evaluate.sh --transcript <path> [--reason <r>] [--model haiku] [--out <dir>] [--dry-run]
```

1. Guard: if `CLAUDE_EVALUATE_SESSION` is set, exit 0 immediately. The grading
   call is itself a Claude session, which ends, which fires SessionEnd. Without
   this, the first exit forks indefinitely. This is the single most important
   line in the plan and it is four characters of shell.
2. Run `digest.sh`. If the session is trivially short, write nothing and exit —
   a grade on a three-turn session is noise.
3. `claude -p --model haiku --restricted --permission-mode dontAsk
   --output-format json`, fed `assets/grader-prompt.md` plus
   `references/rubric.md` plus the digest. `--restricted` removes Bash and the
   other execution tools: the grader reads and answers, it does not act.
4. Write `~/.claude/scorecards/<YYYY-MM-DD>-<HHMM>-<project>.md`. Outside the
   project, because a scorecard about you is not something any repo should carry
   — and this repo is public.
5. Append one line to `~/.claude/scorecards/index.md`: date, project, grade,
   the two focus practices. That file is the point. One scorecard is a mood; the
   index is whether you are actually getting better.

The report, as the todo specifies:

```markdown
# Session scorecard — <project>, <date>

**Grade: B+**

## Focus on
- **BP-06 — Be specific** — <one line naming what happened, with a turn reference>
- **BP-03 — Break big tasks into small steps** — <…>

## Did well
BP-13, BP-16, BP-18

## Not observable this session
BP-07, BP-17
```

Two focus items, never more. A list of nine faults gets skimmed and nothing
changes.

`--dry-run` prints the digest and the prompt, and spends nothing. That is what
makes the rubric iterable.

---

## Seeing it

SessionEnd runs as the process is tearing down, so whether its stdout renders
anywhere is unconfirmed. The design does not depend on it:

- `evaluate.sh` runs **detached**, so the grading call never delays your exit.
  The scorecard lands a few seconds after the terminal is already back.
- A companion `SessionStart` hook prints one line — `Last session: B+ · focus
  BP-06, BP-03 · ~/.claude/scorecards/…` — at the top of the next session in the
  same project. Fallback if SessionStart stdout turns out not to surface: the
  same line goes in the statusline, or you just read the index.

---

## ~~`install-hook.sh` — opt-in, and reversible~~ — SUPERSEDED 2026-09-22

This section described writing the hook into the user's `settings.json`. It was
built, shipped in three successive commits, and then removed entirely. Kept here
because the reasoning for dropping it is worth not rediscovering.

The approach needed a launcher script at a stable path (because the installed
plugin lives under a version-numbered directory that every update replaces), a
per-machine file naming a working checkout, and careful handling of a
`settings.json` that is usually a symlink into a dotfiles repo. Three moving
parts, each able to fail silently — a `SessionEnd` hook whose command does not
exist produces no error at all.

What replaced it is what the documentation prescribes and what Anthropic's own
plugins do: the plugin ships `hooks/hooks.json`, where `${CLAUDE_PLUGIN_ROOT}`
expands to whichever version is current. The path problem then does not arise.

The one thing `hooks.json` cannot express is opt-in — a plugin's hooks are live
the moment it is enabled. So `hook.sh` checks for a marker file on its first line
and exits when it is absent, and `enable-hook.sh --on` / `--off` writes and
removes it. An installer who never wanted this pays a few milliseconds per exit.

Current design is in `plugin/skills/evaluate-session/references/architecture.md`.

---

## Phases

Each stops cleanly, and the first is useful even if nothing follows it.

**Phase 1 — the catalogue — DONE 2026-09-22.** `references/best-practices.md`, all nineteen
entries written out properly, plus `references/rubric.md`. No scripts, no hook.
This is most of the todo's actual value and the only part that is useless if done
carelessly. Reviewed by you before anything is built on it.

**Phase 2 — the digest and on-demand grading — DONE 2026-09-22.** The digest script, the grader
prompt, `evaluate.sh`, and a `SKILL.md` that supports `/session-scorecard` on the
current session. Calibrate on three of your existing transcripts in this project
— they are real sessions with real variation, and one of them will already be a
long ugly one. Confirm cost per run before going further.

**Phase 3 — the hook — MOSTLY DONE 2026-09-22.** Built, then rebuilt on
`hooks/hooks.json` as above. The recursion guard, the detached run and the index
are in. The reason set was verified rather than assumed, in the binary and then
against the documentation: `clear`, `resume`, `logout`, `prompt_input_exit`,
`other`. **Still outstanding: the SessionStart line** that surfaces the last
grade at the top of the next session — without it a scorecard exists only if you
go looking for it, which undercuts the point.

**Phase 4 — evals — NOT STARTED.** No longer optional, because the description tension above
has to be settled empirically rather than asserted. Two separate things:

- *Trigger cases*, in this repo's existing `plugin/evals/` harness from the
  release-version work — same `case.yaml` plus `skill-fired` / `skill-not-fired`
  grader shape already in use. The negatives that matter are the near-misses
  against the siblings: "wrap this up for tomorrow" should reach
  `context-handover`, not the scorecard. This is the committed, re-runnable suite.
- *Description optimisation*, optionally, via skill-creator's own
  `scripts/run_loop.py` — 20 queries, 60/40 train/test split, three runs per query
  for a stable trigger rate, up to five proposed rewrites, best picked on the
  held-out set. A one-off tuning pass rather than something the repo carries.

A grader-consistency case (same digest, three runs, do the grades agree) still
belongs here too, and is the one that tells us whether the letter grade means
anything.

Phases 1 and 2 are a session's work. Phase 3 is short but needs live testing.

---

## Things worth deciding with open eyes

**This scores a person.** A letter grade on how you worked is a judgement about
you, produced by a model, from partial evidence. The plan keeps it defensible
rather than pretending the problem away: the rubric is a file you can read and
edit, every finding cites a numbered practice and a turn, practices the
transcript cannot show are reported as unobservable instead of silently counting
against you, and the output is advice on a local disk that decides nothing. If it
ever grows past that — feeding a dashboard, comparing people — that is a
different thing needing a different conversation.

**It re-sends your session to a model.** Same API the session already used, so no
new category of exposure, but it is a second transmission and the digest is what
bounds it. The secret-pattern refusal and the no-tool-output rule are there for
that reason, not for tidiness.

**Grade stability is the real risk.** An LLM judge given the same input twice can
return B+ and A-. If Phase 2's calibration shows that, the fix is a coarser scale
(four bands, not eleven) rather than a more elaborate prompt. Better a grade that
is stable and vague than one that is precise and random.

**The other session.** Another Claude is working in this checkout, on
`versioning-skill`, and committed during the writing of this plan. Sharing one
working tree means its `git checkout` changes files under this session's feet.
Recommendation: this work runs in a separate git worktree off `main`, on a branch
like `session-scorecard`. It touches `plugin/skills/evaluate-session/`, the
README skill list and the marketplace description — no overlap with the eval work
except the README, which is a one-line conflict at worst.

**Version bump.** A new skill is a `minor`. `/release-version` handles it; the
manifests are not edited by hand.

---

## Out of scope

Grading anything other than a Claude Code session. Cross-project or
cross-timeframe analytics beyond the index line. Sending a scorecard anywhere off
the machine. Any automatic change to how Claude behaves based on a grade — the
scorecard tells you something, it does not tune anything.

---

## Status — 2026-09-23

Built and working end to end on branch `evaluate-session`, based on `main` at
1.9.1. `scripts/test.sh` passes. Not released; automatic grading ships off.

Measured rather than estimated: digest reduction 127x–659x across seven real
transcripts, ~6,000 input tokens per grading call on Haiku, hook returns
immediately with the scorecard landing 60–90s later from the detached run.

### Before release — one blocker

**There is no negative control.** The grader's misattribution fix was verified
against a single session, which moved from B to A. No session that *should* grade
badly has been run through it, so nothing shows the grader can still distinguish.
Bands now resolve upward on ambiguity and more practices correctly report "not
applicable", which makes "everything gets an A" the plausible failure — and it
would ship looking like it worked.

Settle it by grading a session that genuinely went badly: one sprawling unscoped
request, no checkpoints, no verification. It has to land C or D. If it lands A,
the bands need a threshold rather than more prose.

### After that

- **Evals.** `plugin/evals/` already exists for `release-version`. Wanted: trigger
  cases against the near-misses with `context-handover` and `session-handoff`, and
  a grader-consistency case — one digest, three runs, do the bands agree.
- **The `SessionStart` line.** Planned in Phase 3, never built. Without it a
  scorecard exists only if someone goes looking for it.
- **Release.** A new skill is a `minor`, so 1.10.0 through `/release-version`.

### Known-unverified

`/btw` is folded into BP-12 and `digest.py` counts sidechain user messages as
`user_activity.side_questions`. No transcript on the development machine contains
a `/btw`, and `isSidechain` was false on every event examined, so the counter may
always read zero. Confirm against a transcript that actually has one before
relying on it.

