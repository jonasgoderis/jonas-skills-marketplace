---
name: session-handoff
description: Archive this session into the connected folder on Claude Desktop — summarise work since the last handoff, rescue files that exist only in the cloud, and refresh the cross-session index. Needs a connected folder. Triggers on /session-handoff.
---

# Handoff

Write a durable, local record of this session's work so a future session — on another machine, another subscription, or another account — can reconstruct the full context from the connected folder alone.

The connected folder is the only durable store. The cloud container's filesystem dies when the session is reclaimed, file cards delivered into chat are tied to this account, and published artifacts are account-bound. Nothing is safe until it is written into the folder.

## Preconditions

Run inline in the current conversation. Never delegate the whole skill to a subagent — a fresh agent has no memory of this conversation and cannot summarise what it never saw. Steps 5 and 6 delegate deliberately, with everything they need passed explicitly.

1. Confirm a folder is connected (`get_device_info` → `connectedFolders`; in `device_bash` they mount at `$HOME/mnt/<folder-name>`). If none is connected, stop and say so — there is nowhere durable to write.
2. With more than one folder connected, use the one this session has been working in. If that is ambiguous, ask; if working unattended, use the first and state the assumption.
3. Set `ROOT="$HOME/mnt/<folder>"` and `HANDOFF="$ROOT/_Handoffs"`. Create `$HANDOFF/entries` and `$HANDOFF/.state` if missing.

## Session identity

Multiple sessions share this folder, so everything written is namespaced per session.

- `SESSION_ID` — the first 8 characters of this session's identifier. Take it from the session URL if present in context, otherwise from the scratchpad directory name. It must stay stable across repeated `/session-handoff` runs within the same session.
- `SLUG` — a short kebab-case name for what this session is about (`azure-foundry-eval`, `q3-report`). Derive it once, then reuse the value stored in `$HANDOFF/.state/$SESSION_ID.json`.

## Step 1 — Find the window

Read `$HANDOFF/.state/$SESSION_ID.json`. If it exists, `last_run` is the cutoff: cover only what has happened since. If it does not exist, the window is the whole conversation.

Read `file_snapshot` from the same file — path, size and mtime for the folder as of the last run. It is what makes the file diff in step 4 reliable rather than guesswork.

## Step 2 — Rescue anything that exists only in the cloud

Do this before writing anything, every run, whether or not a migration is imminent.

1. List what this session produced: `/mnt/user-data/outputs/`, the working directory, and anything delivered with SendUserFile during the window.
2. Compare against `$ROOT`. For anything missing, copy it into `/mnt/user-data/outputs/` if it is not already there, then commit it with `device_commit_files` (`stagedPath` → `devicePath`), filing it by the folder conventions already in use. Pass `expectedMtimeMs` when re-committing a file that already exists, so an edit made by the user is never overwritten.
3. `/mnt/user-data/outputs/` accumulates every version staged during the session, so a file sitting there may be an earlier draft rather than the current one. Rescue from the authoritative source — the installed file, the live working copy, the thing actually in use — not from whatever happens to share its name in `outputs/`.
4. Re-stat every file after committing it and record the size and mtime you observe, never the ones you intended. A guarded commit can decline to write, and a decline that goes unnoticed becomes a confident false claim in the entry.
5. Source material the user attached in chat (`/mnt/user-data/uploads/`) is equally ephemeral. If the work depends on it and it is not already in the folder, copy it under `sources/`.
6. Check for published artifacts: `Artifact` with `action: "list"`, `scope: "mine"`. For anything created or updated inside the window with no local counterpart, `action: "read"` it and save the HTML into the folder. This catches pages published by default — dashboards, trackers — that were never deliberately published.
7. Record every path rescued, with its post-write size and mtime; step 4 needs the list.

## Step 3 — Rescue anything that exists only in the conversation

Step 2 covers files that exist in the cloud container but not the folder. This step covers content that was never a file at all — it exists only as chat text, and it dies with the session just as surely.

Scan the window for substance delivered inline and never written anywhere: explanations and reference material the user asked for, prompts and specs drafted in chat, code shown in a fenced block but never saved, research findings, comparisons, reasoning argued out at length.

Write each one into the folder as its own document — `notes/<topic>.md` for explanation and reference, `sources/` for material the user supplied. Preserve the content; do not compress it into a paragraph. The handoff entry is a briefing and has no room for it, which is precisely why it needs a file of its own. The entry then points at the file rather than trying to contain it.

This step is you deciding what counted as substantive, so err toward saving. When unsure whether something mattered, save it and note the uncertainty rather than dropping it — an unwanted file costs nothing, and an explanation that was never written down cannot be recovered once the session is gone.

## Step 4 — Gather raw notes

Write plain, checkable facts to the scratchpad as `handoff-notes.md`. Facts only, no narrative — this file is the ground truth the verifier grades the draft against.

- Decisions taken since the cutoff, each with the reasoning behind it.
- Files created or changed in `$ROOT` since the cutoff, diffed against `file_snapshot`. Cross-reference the other entries in `$HANDOFF/entries` and mark anything belonging to another session's workstream — do not claim it.
- Files rescued in step 2 and written out in step 3, each with the path it now lives at.
- Open threads, unresolved questions, and what the next session should do first.
- Anything account-bound that will not survive a migration: scheduled tasks (`list_triggers`), connectors and skills in use, Claude Project docs.
- Dead ends worth not repeating.

Be exhaustive rather than selective. This step runs on the session model and is the only point where the whole conversation is still visible — everything downstream can work solely from what these notes contain. Thin notes produce a fluent, verified, incomplete handoff, and the verifier cannot catch the gap, because the draft will match the thin notes perfectly. Where your own coverage is uncertain, write that down so it reaches `## Needs your check`.

Never write credentials, tokens, API keys or personal data into the notes or any handoff file. Reference where a secret lives instead of reproducing it.

## Step 5 — Draft (Opus)

Call `Agent` with `model: "opus"`. Have it read `handoff-notes.md` plus a current listing of `$ROOT`, and write the entry to a scratchpad path. Its prompt must state:

- Write only what the notes support. Invent nothing, infer nothing, smooth nothing over.
- Where the notes are ambiguous, say so rather than choosing a reading.
- The reader is a future Claude session with zero context reconstructing the state of the work — write a briefing, not a diary. No asides, no editorialising, no narrating the shape of the conversation.
- Every size, count and path is load-bearing. State only what you observed on disk.
- Content written out in step 3 is referenced by path under `## Rescued this run`, with a line on what it covers. Never restate its contents in the entry.
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
## Rescued this run
## Open threads and next steps
## Needs your check
```

## Step 6 — Verify (Sonnet)

Call `Agent` with `model: "sonnet"` for an independent check — a separate pass, because a draft cannot grade itself. Give it paths to `handoff-notes.md`, the draft, and a live listing of `$ROOT`. It reports; it does not edit. Ask for:

- **Unsupported claims** — anything asserted in the draft the notes do not back.
- **Omissions** — anything in the notes material to resuming the work that the draft dropped.
- **Bad references** — files named in the draft that do not exist at the path given.
- **Misattribution** — work credited to this session that the entries show belongs to another.
- **Contradicted facts** — check every size, mtime, count and path in the draft against the live listing. These are the claims a future session trusts most and the ones a draft gets wrong most easily, because it reports the write it intended rather than the write that landed. A number that disagrees with the listing is a finding, not a rounding difference.
- **Ephemeral paths** — container-side paths (`/root/…`, `/mnt/…`, scratchpad paths) recorded as though durable. Only paths under `$ROOT` survive the session; anything else must be described in prose, never given as a path to follow.

## Step 7 — Reconcile and write

1. Fix what the verifier found: strike unsupported claims, restore dropped facts, correct paths.
2. Anything unresolvable from the notes goes under `## Needs your check`, phrased as an open question. Never guess to fill a gap; never silently drop one.
3. Write the entry to `$HANDOFF/entries/<YYYY-MM-DD>_<HHMM>_<SESSION_ID>_<SLUG>.md`.
4. Regenerate `$HANDOFF/CURRENT.md` from all entries. It is derived, never hand-edited, so a collision between two concurrent sessions self-heals on the next run; write to a temp file and rename. Re-list `entries/` immediately before the rename and rebuild if anything appeared since you read it, so a session that handed off while you were drafting is not dropped from the index. It contains:
   - One line on what the folder is and that this file is where to start.
   - A section per active workstream — name, session id, last updated, where it stands, next steps, key file paths relative to `$ROOT` — newest first, with workstreams untouched for 60+ days moved to a dormant list at the bottom. Where two sessions share a slug, merge them under one heading and list each session id separately rather than emitting the heading twice.
   - A "Present but not yet indexed" section listing anything in `$ROOT` that no entry accounts for — files another session created but has not yet handed off. Name the paths and say plainly that their state is unknown from here and that running `/session-handoff` in the owning session will give them an entry. Never infer what they are or claim them.
   - A "Recreate on a new account" section: scheduled tasks, connectors, skills and Project docs that will not migrate — and for each skill, where its source lives, so it is reinstalled rather than reconstructed from memory.
   - A pointer to `entries/` for the detail.
5. Write `$ROOT/README.md` only if none exists, with a short pointer to `_Handoffs/CURRENT.md`, so a new session listing the folder finds the way in.
6. Update `$HANDOFF/.state/$SESSION_ID.json` with `last_run`, `slug`, `last_entry` and a fresh `file_snapshot`.

If nothing has changed since the last run, do not write an empty entry — say so and stop.

## Step 8 — Report

One or two lines in chat: what was written, how many files were rescued, and anything left under `Needs your check`. Do not paste the entry into the conversation.

## Resuming on a new account

A new session will not read `CURRENT.md` unprompted. Tell the user to open the new project against this folder and say: "read `_Handoffs/CURRENT.md` and catch up."

This skill is itself account-bound, but it is not account-*only*. Record in the "Recreate on a new account" section where its source actually lives — the plugin or repository it installs from — so it can be reinstalled on the new account before the first `/session-handoff` runs there.

Do not copy this file into the folder. A copy is a second source of truth that goes stale in silence, and a stale copy is worse than none: the entry then describes a version that is not the one running.
