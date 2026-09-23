# How evaluate-session fits together

Read this when the hook is not firing, when a path has gone stale, or before
changing how any of it is installed.

## Three worlds

The confusion this document exists to prevent comes from there being three
copies of the skill's files, in three places, changing on three different
schedules.

```
┌─ (1) SOURCE — the marketplace repo, under git ───────────────────────────────┐
│                                                                              │
│  plugin/skills/evaluate-session/                                             │
│    SKILL.md                                                                  │
│    references/  best-practices.md    BP-01..BP-19, the catalogue             │
│                 rubric.md            how evidence becomes a grade            │
│                 architecture.md      this file                               │
│    assets/      grader-prompt.md     what the grader is asked to produce     │
│                 secret-patterns.txt  the privacy gate's patterns             │
│    scripts/     digest.py            transcript      -> evidence digest      │
│                 evaluate.sh          digest          -> scorecard            │
│                 hook.sh              SessionEnd JSON -> evaluate.sh          │
│                 enable-hook.sh       switches grading on and off             │
│                 log.sh               one log line per session outcome        │
│  plugin/hooks/hooks.json             registers the SessionEnd hook           │
│                                                                              │
│  changes: on every commit                                                    │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │  /plugin install  ·  /plugin update
                                ▼
┌─ (2) INSTALLED — the plugin cache, managed by Claude Code ───────────────────┐
│                                                                              │
│  ~/.claude/plugins/cache/jonas-skills-marketplace/claude-skills/1.9.1/       │
│                                                                ^^^^^         │
│    skills/evaluate-session/...          the version is IN the path           │
│                                                                              │
│  A release creates a NEW directory beside the old ones. Nothing may point     │
│  at this path directly, or it breaks on the next update — silently.          │
│                                                                              │
│  changes: on every release you install                                       │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │  enable-hook.sh --on          (opt-in, once)
                                ▼
┌─ (3) SWITCHED ON — one marker file ──────────────────────────────────────────┐
│                                                                              │
│  ${CLAUDE_PLUGIN_DATA}/enabled        written by enable-hook.sh --on          │
│      (or ~/.claude/evaluate-session/enabled outside a plugin install)         │
│                                                                              │
│  That is the whole of it. Nothing is written to settings.json, nothing is     │
│  placed in ~/.claude/hooks, and nothing holds a path that an update can       │
│  invalidate.                                                                 │
│                                                                              │
│  ${CLAUDE_PLUGIN_DATA}/evaluate-session.log   one line per ended session:    │
│      graded, skipped and why, or failed. Written whether on or off; the       │
│      tail is what enable-hook.sh --status shows.                              │
│                                                                              │
│  changes: when you switch it on or off                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Why a marker file rather than settings.json

The plugin registers its hook in `hooks/hooks.json`, which is the documented way
for a plugin to provide one, and `${CLAUDE_PLUGIN_ROOT}` there expands to
whichever version-numbered directory is current. So the path problem solves
itself and nothing needs to live in the user's configuration.

What `hooks.json` cannot express is opt-in: a plugin's hooks are live the moment
the plugin is enabled. Grading every session spends the installer's tokens, and
nobody should start paying that by installing a collection of skills. The marker
file is the opt-in, checked on the first line of `hook.sh`:

```
  no marker  ->  log "skipped: off", exit 0   a few milliseconds, one log line
  marker     ->  parse payload, hand off
```

The rejected alternative was writing a path into `settings.json`. It needed a
launcher script at a stable location to survive plugin updates, a per-machine
file to find a working checkout, and careful handling of a settings file that is
usually a symlink into a dotfiles repo. Three moving parts, all of them able to
fail silently, to avoid one `[ -f ]` test.

## What happens when a session ends

```
  /clear  ·  /resume  ·  /logout  ·  exit  ·  enable-hook.sh --test
        │
        ▼
  Claude Code fires SessionEnd, JSON on stdin
  {"transcript_path": "...", "cwd": "...", "reason": "clear"}
        │
        ▼
  ${CLAUDE_PLUGIN_ROOT}/skills/evaluate-session/scripts/hook.sh
        │   expanded by Claude Code to the current plugin version
        │
        │   marker file absent?  ──►  log, exit 0   automatic grading is off
        │   reads the payload, returns 0 immediately
        │   ──────────────────────────────►  your exit is never delayed
        │
        └── nohup ──► evaluate.sh          detached, finishes in 60-90s
                          │
                          ├─ CLAUDE_EVALUATE_SESSION set?  ──► exit 0
                          │     the grading run is itself a session, which
                          │     ends, which fires SessionEnd. Without this
                          │     guard the first exit forks until something
                          │     gives out.
                          │
                          ├─► digest.py
                          │     transcript.jsonl        ~2.8 MB
                          │       dedupe on uuid (resumed sessions replay)
                          │       drop meta, sidechain, tool results,
                          │         injected skill bodies, auto-continuations
                          │       keep YOUR messages verbatim
                          │       reduce the rest to shape: tool counts,
                          │         files, commits, test runs, compactions
                          │       read the project for the structural practices
                          │     ──► under 5 prompts   : exit 3, nothing written
                          │     ──► secret pattern hit: exit 4, nothing sent
                          │     digest.json             ~4 KB   (127x-659x)
                          │
                          ├─► claude -p --model haiku --restricted
                          │     prompt = grader-prompt + catalogue + rubric
                          │              + digest
                          │     ~6,000 input tokens, a fraction of a cent
                          │     --restricted: the grader reads and answers,
                          │     it cannot run anything. The transcript it is
                          │     reading is untrusted text.
                          │
                          └─► ~/.claude/scorecards/<date>-<time>-<project>.md
                              ends with <!-- session: <session-id> -->
                              ~/.claude/scorecards/index.md   one row appended
```

Scorecards live outside the project on purpose. One is about a person, belongs
to no codebase, and a public repo should never carry one.

## Switching it on, off, and checking it

```
enable-hook.sh --on       write the marker; every session that ends is graded
               --off      remove it; /evaluate-session still works
               --status   report whether it is on, and tail the hook log
               --test     grade this project's most recent session now, through
                          the same entry point the hook uses, whether or not
                          automatic grading is on
```

## Running it without the hook

```
evaluate.sh --transcript ~/.claude/projects/<slug>/<session>.jsonl \
            --project-dir . [--model haiku] [--dry-run]
```

`<slug>` is the project's path with every non-alphanumeric character replaced by
a dash. `--dry-run` builds the digest and the prompt, prints both with a token
estimate, and calls nothing — use it whenever the rubric or the prompt changes.
