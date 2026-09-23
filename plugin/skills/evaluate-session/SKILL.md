---
name: evaluate-session
description: Grade how well the user drove a Claude Code session against a catalogue of AI-use best practices — a letter band, the two practices to focus on, and the ones they did well. Use whenever the user asks how they did, how their prompting was, whether they used Claude well, which practices they are weakest on, where they are wasting context, tokens or turns, or wants feedback on their own working method rather than on the code. Reach for it when they ask to be evaluated, scored, graded, reviewed or marked as a user, when they ask what they should do differently next time, and when they want a session scorecard without naming it. Also covers installing the hook that produces a scorecard automatically at the end of every session. Triggers on /evaluate-session.
---

# Evaluate session

Two jobs with opposite requirements, so the split is strict. Deciding what a
session shows about how it was driven needs judgement. Parsing a transcript,
bounding what gets sent, writing the report and maintaining the index has to
happen identically every time, so scripts own all of it.

What is graded is the *user's* side: how the work was scoped, asked for and
checked. Not the code, and not the assistant's answers. A session that shipped
working code through six vague prompts graded badly; a session that carefully
scoped a task that turned out to be unnecessary graded well.

## The catalogue is the authority

`references/best-practices.md` defines BP-01 to BP-19 — the practices, the
reasoning behind each, and how observable each one is. `references/rubric.md`
governs how evidence becomes a grade. Read them before overriding anything here;
they are what the grader is given, and they are meant to be edited when a
practice changes.

Only ten of the nineteen are visible in a transcript. Three are properties of the
project, read from the filesystem. The rest are inferable from signals at best.
That is why a practice the evidence cannot show is reported as unobserved rather
than counted against anyone — a grade that punishes invisible things cannot be
argued with, so it gets ignored.

## The scripts

Under `${CLAUDE_PLUGIN_ROOT}/skills/evaluate-session/`, or next to this file if
that variable is unset.

```
scripts/digest.py       transcript .jsonl  ->  compact evidence digest (JSON)
scripts/evaluate.sh     digest -> graded scorecard on disk, plus an index line
scripts/hook.sh         SessionEnd payload -> evaluate.sh, detached
scripts/enable-hook.sh  switches automatic grading on and off
```

`digest.py` is the privacy boundary as much as the cost control. It carries the
user's messages verbatim, because they are what is being graded, and reduces
everything else to shape — tool names and counts, files touched, commits, test
runs. Assistant prose, tool output and file contents never enter it. Paths are
made relative to the project and anything outside it is dropped. A transcript
whose messages match a secret pattern produces no digest at all, rather than an
annotated one; `assets/secret-patterns.txt` holds the built-in set and
`--secret-patterns FILE` replaces it.

Real transcripts come out 127 to 659 times smaller than the raw file. A 2.8 MB
session becomes 4 KB, which is what makes grading every session affordable.

## Running it on demand

```
evaluate.sh --transcript <path.jsonl> [--project-dir DIR] [--model haiku] [--dry-run]
```

Transcripts live in `~/.claude/projects/<slugified-project-path>/<session-id>.jsonl`.
For the session in progress, the newest file in that directory is the current one.

Run `--dry-run` first when changing the rubric or the prompt. It builds the
digest and the full prompt, prints both with a token estimate, and calls nothing.

Sessions shorter than five prompts exit silently. A grade on a three-turn session
is noise, and producing one teaches the user to ignore the rest.

## Running it automatically

The plugin registers a `SessionEnd` hook in `hooks/hooks.json`, so it is present
as soon as the plugin is enabled. It does nothing until switched on.

```
enable-hook.sh --on       grade every session from now on
               --off      stop; /evaluate-session still works
               --status   is it on?
               --test     grade this project's latest session now, through the
                          same entry point the hook uses
```

`--on` writes a marker file under the plugin's own data directory. `hook.sh`
looks for it and exits immediately when it is absent, so an installer who never
wanted this pays a few milliseconds per exit and nothing else. Nothing is ever
written to `settings.json`, so there is no path anywhere that a plugin update can
leave pointing at a directory that no longer exists.

Never switch it on uninvited. It spends the user's tokens on every exit — say
what it costs first, roughly 6,000 input tokens per session on Haiku, a fraction
of a cent.

The hook runs detached, so it never delays the exit; the scorecard lands a few
seconds after the terminal is back. `SessionEnd` fires on `clear`, `resume`,
`logout`, `prompt_input_exit` and `other`, so `/clear` triggers it for real — at
the cost of the conversation, which is why `--test` exists.

`evaluate.sh` exits immediately when `CLAUDE_EVALUATE_SESSION` is set. The
grading call is itself a Claude session, which ends, which fires `SessionEnd`
again — without the guard the first exit forks until something gives out.

## Where the output goes

`~/.claude/scorecards/<date>-<time>-<project>.md`, with one line appended to
`~/.claude/scorecards/index.md`.

Outside the project on purpose. A scorecard is about a person, it is not part of
any codebase, and a repo that is public should never carry one.

The index is the point. One scorecard is a mood; the table is whether the
practice is actually improving. When the user asks how they are doing generally,
read the index rather than regrading anything.

## Reporting it

Give the grade, the focus items and the path — nothing else. The report is
already written; restating it in chat wastes the context the whole exercise is
about (BP-11).

Never soften a grade, pad a thin report, or add a second focus item because one
looks sparse. One focus item, or none, is a legitimate result and a more useful
one than a manufactured second.
