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
│                 hook-launcher.sh     static; copied to ~/.claude/hooks       │
│    scripts/     digest.py            transcript      -> evidence digest      │
│                 evaluate.sh          digest          -> scorecard            │
│                 hook.sh              SessionEnd JSON -> evaluate.sh          │
│                 install-hook.sh      wires it into settings.json             │
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
                                │  install-hook.sh --install   (opt-in, once)
                                ▼
┌─ (3) WIRED — your machine's configuration ───────────────────────────────────┐
│                                                                              │
│  ~/.claude/settings.json            "SessionEnd" -> ~/.claude/hooks/...      │
│      often a symlink into a dotfiles repo; the installer writes through it    │
│                                                                              │
│  ~/.claude/hooks/evaluate-session.sh    the launcher. Byte-identical on       │
│      every machine, so it can be tracked and symlinked like any other hook.   │
│      install-hook.sh leaves it alone if it finds a symlink.                   │
│                                                                              │
│  ~/.claude/hooks/evaluate-session.path  optional, one line, a working         │
│      checkout. Written only when installing from a checkout rather than a     │
│      plugin copy. Machine-specific — keep it out of version control.          │
│                                                                              │
│  changes: once, at install                                                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Why the launcher exists

Without it, `settings.json` has to name a real file, and every candidate is
wrong:

```
  settings.json -> .../claude-skills/1.9.1/skills/.../hook.sh
                                      └── gone after the next /plugin update

  settings.json -> /Users/you/code/marketplace/plugin/skills/.../hook.sh
                   └── absent on any other machine, and on this one the moment
                       the directory is renamed
```

A `SessionEnd` hook whose command does not exist fails without a message. The
launcher is one fixed path that resolves the real location at run time, so the
thing stored in configuration never has to change.

## What happens when a session ends

```
  /clear  ·  /resume  ·  /logout  ·  exit  ·  install-hook.sh --test
        │
        ▼
  Claude Code fires SessionEnd, JSON on stdin
  {"transcript_path": "...", "cwd": "...", "reason": "clear"}
        │
        ▼
  ~/.claude/hooks/evaluate-session.sh          the one stable path
        │   resolves the skill, first match wins:
        │     1. $EVALUATE_SESSION_SKILL
        │     2. newest ~/.claude/plugins/cache/**/skills/evaluate-session
        │     3. the path named in evaluate-session.path
        │   nothing resolves -> exit 0, silently. A session ending is not
        │   the moment to complain.
        ▼
  <skill>/scripts/hook.sh
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
                              ~/.claude/scorecards/index.md   one row appended
```

Scorecards live outside the project on purpose. One is about a person, belongs
to no codebase, and a public repo should never carry one.

## Installing, uninstalling, checking

```
install-hook.sh --install     write the launcher, add the SessionEnd entry.
                              Merges into existing hooks; never replaces them.
                              Re-run it after a skill update to refresh the
                              launcher.
                --status      is it installed, and are other SessionEnd hooks
                              present that would also run?
                --test        fire the installed hook against this project's
                              most recent session and wait for the scorecard.
                              Reads the command out of settings.json, so it
                              tests the wiring that exists.
                --uninstall   remove only the entry it added. Leaves a
                              symlinked launcher in place.
```

Settings are written atomically: a temp file beside the resolved target,
validated as JSON, then renamed over it. The symlink is followed, not replaced —
renaming onto the link would destroy it.

## Running it without the hook

```
evaluate.sh --transcript ~/.claude/projects/<slug>/<session>.jsonl \
            --project-dir . [--model haiku] [--dry-run]
```

`<slug>` is the project's path with every non-alphanumeric character replaced by
a dash. `--dry-run` builds the digest and the prompt, prints both with a token
estimate, and calls nothing — use it whenever the rubric or the prompt changes.
