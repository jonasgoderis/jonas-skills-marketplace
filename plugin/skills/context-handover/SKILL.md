---
name: context-handover
description: Hand this Claude Code session over to the next one — write a briefing into the project so the conversation can be cleared without losing the thread. Use it when the session has got long and the answers are getting sloppy, before a /clear or a compact, when stopping for the day to resume tomorrow, or when handing the work to a different session or machine. Reach for it when the user says the context is full or that they are losing the thread, or asks how to carry this over, hand it off, or brief the next session. `/context-handover resume` is the other half — run it at the start of a fresh session to read the last briefing back and pick up the thread. Triggers on /context-handover.
---

# Context handover

A long session degrades. The fix is to end it deliberately: distil what matters into one file, clear the conversation, and start cold with the briefing instead of the transcript.

The files on disk are already safe. The only thing at risk is the conversation — the reasoning behind the code, the decisions, the dead ends, and where things actually stand. That is what this briefing carries, and it is a baton, not an archive: written once, read once, then gone.

## Preconditions

Write mode runs inline in the current conversation. Never delegate it to a subagent — a fresh agent has no memory of this conversation and cannot summarise what it never saw. Read the file listings and run the commands yourself.

## Two modes

Bare `/context-handover` writes a handover. `/context-handover resume` reads one back.

## Write mode

1. Handover files live in `.claude/handover/` relative to the project root. Create it if missing.
2. Name the file `<YYYY-MM-DD>-<HHMM>-<slug>.md`, where the slug is short kebab-case for what the session was about. The timestamp is what makes it unique and orderable.
3. On the first run in a project: if this is a git repo and `.claude/handover/` is not already ignored, append it to `.gitignore` and tell the user. These are transient working notes, not something the repo should carry, and an untracked file at a predictable path gets committed by accident.
4. Work out the window. List `.claude/handover/` and read `.claude/handover/.consumed` if it exists; the newest entry in either is the cutoff, and you cover only what has happened since. With neither present, the window is the whole conversation.
5. The reader is the next Claude session, starting cold in this project with zero conversation history. Write a briefing, not a diary. No narration of how the conversation went, no "we then discussed" — state what is true now.
6. Use this structure:

```
---
date: <ISO 8601>
project: <project name>
slug: <slug>
previous: <filename of the last handover, or null>
---

# <Slug> — <date>

## Where things stand
## What I was asked to do
## Decisions and why
## Files touched
## Open threads
## Start here
## Dead ends
```

   - **Where things stand** — the state of play in a few lines. What works, what is half-done.
   - **What I was asked to do** — the actual goal, in the user's terms, including anything deliberately ruled out of scope.
   - **Decisions and why** — each decision with its reasoning. The reasoning is the part that dies with the conversation; the decision is usually visible in the code, the why never is.
   - **Files touched** — paths relative to the project root, one line each on what changed. Only files you verified exist.
   - **Open threads** — unresolved questions, known bugs, things deliberately deferred.
   - **Start here** — the concrete first action for the next session.
   - **Dead ends** — what was tried and did not work, so it is not tried again. This is the highest-value section and the one routinely left out, because a failed attempt feels like nothing to report. It is the thing the next session will otherwise spend an hour rediscovering.

7. Facts only. Every path, command and claim must be something you observed, not something you intended. If you are unsure whether a change landed, write the uncertainty rather than the assumption — a briefing the next session cannot trust is worse than no briefing.
8. Never write credentials, tokens, API keys or personal data into the file. Reference where a secret lives instead of reproducing its value.
9. If nothing meaningful has happened since the last handover, say so and write nothing. An empty handover trains the next session to distrust the file.
10. Finish by telling the user the path and that they can clear the conversation now. Do not paste the briefing into chat — the whole point is that it is not occupying context.

## Resume mode

1. List `.claude/handover/` for `*.md` and take the newest. Ignore `.consumed` — it is bookkeeping, not a handover. If there is no handover file, say so and stop.
2. Read it in full and absorb it. This is the context you are starting from.
3. Report in one or two lines what you picked up — the workstream and the first action — so the user can see it landed.
4. Only then delete the file, and append its filename and the current date to `.claude/handover/.consumed` so a later handover knows where its window starts. Deletion follows a confirmed successful read and never precedes it: the file is the only copy, and deleting it before it is absorbed loses the context permanently. If the read failed, or the file was empty or malformed, leave it in place and say so.
5. If several unconsumed files are present, read the newest and tell the user the others are there. Do not delete or silently ignore them — you do not know what is in them.
