---
name: session-handoff
description: Save a session handoff into the connected folder — summarise work since this session's last handoff, rescue files that exist only in the cloud, and refresh the cross-session index. Triggers on /session-handoff.
---

# Handoff

Write a durable, local record of this session's work so a future session — on another machine, another subscription, or another account — can reconstruct the full context from the connected folder alone.

The connected folder is the only durable store. The cloud container's filesystem dies when the session is reclaimed, file cards delivered into chat are tied to this account, and published artifacts are account-bound. Nothing is safe until it is written into the folder.

## Preconditions

Run inline in the current conversation. Never delegate the whole skill to a subagent — a fresh agent has no memory of this conversation and cannot summarise what it never saw. Steps 4 and 5 delegate deliberately, with everything they need passed explicitly.

1. Confirm a folder is connected (`get_device_info` → `connectedFolders`; in `device_bash` they mount at `$HOME/mnt/<folder-name>`). If none is connected, stop and say so — there is nowhere durable to write.
2. With more than one folder connected, use the one this session has been working in. If that is ambiguous, ask; if working unattended, use the first and state the assumption.
3. Set `ROOT="$HOME/mnt/<folder>"` and `HANDOFF="$ROOT/_Handoffs"`. Create `$HANDOFF/entries` and `$HANDOFF/.state` if missing.

## Session identity

Multiple sessions share this folder, so everything written is namespaced per session.

- `SESSION_ID` — the first 8 characters of this session's identifier. Take it from the session URL if present in context, otherwise from the scratchpad directory name. It must stay stable across repeated `/session-handoff` runs within the same session.
- `SLUG` — a short kebab-case name for what this session is about (`azure-foundry-eval`, `q3-report`). Derive it once, then reuse the value stored in `$HANDOFF/.state/$SESSION_ID.json`.

## Step 1 — Find the window

Read `$HANDOFF/.state/$SESSION_ID.json`. If it exists, `last_run` is the cutoff: cover only what has happened since. If it does not exist, the window is the whole conversation.

Read `file_snapshot` from the same file — path, size and mtime for the folder as of the last run. It is what makes the file diff in step 3 reliable rather than guesswork.

## Step 2 — Rescue anything that exists only in the cloud

Do this before writing anything, every run, whether or not a migration is imminent.

1. List what this session produced: `/mnt/user-data/outputs/`, the working directory, and anything delivered with SendUserFile during the window.
2. Compare against `$ROOT`. For anything missing, copy it into `/mnt/user-data/outputs/` if it is not already there, then commit it with `device_commit_files` (`stagedPath` → `devicePath`), filing it by the folder conventions already in use. Pass `expectedMtimeMs` when re-committing a file that already exists, so an edit made by the user is never overwritten.
3. Source material the user attached in chat (`/mnt/user-data/uploads/`) is equally ephemeral. If the work depends on it and it is not already in the folder, copy it under `sources/`.
4. Check for published artifacts: `Artifact` with `action: "list"`, `scope: "mine"`. For anything created or updated inside the window with no local counterpart, `action: "read"` it and save the HTML into the folder. This catches pages published by default — dashboards, trackers — that were never deliberately published.
5. Record every path rescued; step 3 needs the list.

## Step 3 — Gather raw notes

Write plain, checkable facts to the scratchpad as `handoff-notes.md`. Facts only, no narrative — this file is the ground truth the verifier grades the draft against.

- Decisions taken since the cutoff, each with the reasoning behind it.
- Files created or changed in `$ROOT` since the cutoff, diffed against `file_snapshot`. Cross-reference the other entries in `$HANDOFF/entries` and mark anything belonging to another session's workstream — do not claim it.
- Files rescued in step 2.
- Open threads, unresolved questions, and what the next session should do first.
- Anything account-bound that will not survive a migration: scheduled tasks (`list_triggers`), connectors and skills in use, Claude Project docs.
- Dead ends worth not repeating.

Never write credentials, tokens, API keys or personal data into the notes or any handoff file. Reference where a secret lives instead of reproducing it.

## Step 4 — Draft (Opus)

Call `Agent` with `model: "opus"`. Have it read `handoff-notes.md` plus a current listing of `$ROOT`, and write the entry to a scratchpad path. Its prompt must state:

- Write only what the notes support. Invent nothing, infer nothing, smooth nothing over.
- Where the notes are ambiguous, say so rather than choosing a reading.
- The reader is a future Claude session with zero context reconstructing the state of the work — write a briefing, not a diary.
- Use this structure:

```
---
session: <SESSION_ID>
workstream: <SLUG>
date: <ISO 8601>
window_start: <ISO 8601 or "conversation start">
previous_entry: <filename or null>
---

# <Workstream> — <date>

## Where things stand
## Decisions since last handoff
## Files created or changed
## Rescued from the cloud this run
## Open threads and next steps
## Needs your check
```

## Step 5 — Verify (Sonnet)

Call `Agent` with `model: "sonnet"` for an independent check — a separate pass, because a draft cannot grade itself. Give it paths to `handoff-notes.md`, the draft, and a live listing of `$ROOT`. It reports; it does not edit. Ask for:

- **Unsupported claims** — anything asserted in the draft the notes do not back.
- **Omissions** — anything in the notes material to resuming the work that the draft dropped.
- **Bad references** — files named in the draft that do not exist at the path given.
- **Misattribution** — work credited to this session that the entries show belongs to another.

## Step 6 — Reconcile and write

1. Fix what the verifier found: strike unsupported claims, restore dropped facts, correct paths.
2. Anything unresolvable from the notes goes under `## Needs your check`, phrased as an open question. Never guess to fill a gap; never silently drop one.
3. Write the entry to `$HANDOFF/entries/<YYYY-MM-DD>_<HHMM>_<SESSION_ID>_<SLUG>.md`.
4. Regenerate `$HANDOFF/CURRENT.md` from all entries. It is derived, never hand-edited, so a collision between two concurrent sessions self-heals on the next run; write to a temp file and rename. It contains:
   - One line on what the folder is and that this file is where to start.
   - A section per active workstream — name, session id, last updated, where it stands, next steps, key file paths — newest first, with workstreams untouched for 60+ days moved to a dormant list at the bottom.
   - A "Recreate on a new account" section: scheduled tasks, connectors, skills and Project docs that will not migrate.
   - A pointer to `entries/` for the detail.
5. Write `$ROOT/README.md` only if none exists, with a short pointer to `_Handoffs/CURRENT.md`, so a new session listing the folder finds the way in.
6. Update `$HANDOFF/.state/$SESSION_ID.json` with `last_run`, `slug`, `last_entry` and a fresh `file_snapshot`.

If nothing has changed since the last run, do not write an empty entry — say so and stop.

## Step 7 — Report

One or two lines in chat: what was written, how many files were rescued, and anything left under `Needs your check`. Do not paste the entry into the conversation.

## Resuming on a new account

A new session will not read `CURRENT.md` unprompted. Tell the user to open the new project against this folder and say: "read `_Handoffs/CURRENT.md` and catch up."

This skill is itself account-bound. Keep a copy of this file at `$HANDOFF/skill/SKILL.md`, refreshed whenever the skill changes, so it can be recreated on the new account before the first `/session-handoff` runs there.
