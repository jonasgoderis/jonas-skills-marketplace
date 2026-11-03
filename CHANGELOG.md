# Changelog


## [1.16.0] - 2026-11-03

### Changed

- drawio-conventions: lines that leave or enter the same side of a shape no longer overlap. Each gets one waypoint at its own height within that side, with `followTerminals=1` so the waypoints move along when the shape is dragged. Fixed connection points stay forbidden.
- drawio-conventions: the gap between shapes is now 80 to 120 px instead of at least 120 px. The agent picks the wider gap where several lines meet, lines run side by side, or lines carry labels.
- drawio-conventions: every icon label sits centred under the icon. The keys that set this are in the house style, because many of draw.io's own style strings put the label on or beside the picture.
- drawio-conventions: each note is sized to its own text and gets `autosize=1`, instead of all notes sharing one large size.
- drawio-conventions: `check_drawio.py` checks all four rules. Two lines that meet one side of a shape at the same point give a warning. An icon label that is not under the icon is a failure. A note much larger than its text gives a warning. The gap warning now starts below 80 px.

## [1.15.0] - 2026-11-02

### Added

- **drawio-conventions checker script.** `scripts/check_drawio.py` runs the mechanical part of the checklist over the file on disk: edges, fixed points, line jumps, perimeters, flat look, drawing order, compression, tabs and label length. It also checks the spacing, alignment and avoidable crossings of connected shapes, and checks icon names against the installed draw.io app. `--find` looks up icon names and prints a style string to copy.
- **Safe file writing in drawio-conventions.** Before a generator script runs again, Claude keeps the user's own draw.io edits. Claude also warns when draw.io has unsaved changes to the file, and keeps the tab ids and names of multi-tab files unique.
- **New drawio-conventions house-style rules.** The rules cover a colour per flow when a legend explains it, step numbers on ordered flows, labels of at most 3 lines, group containers, and labels that move along their own line.

### Changed

- **More room and straighter lines in drawio diagrams.** The minimum gap between shapes is now 120 px, up from 80 px. Connected shapes line up by their centres. Every edge keeps a straight end of 30 px before the arrow head (`targetJettySize=30`). Icon labels no longer wrap. Items in a stacked list without edges between them may sit 10–20 px apart.

### Fixed

- **Eval grader for icon drawing order.** The grader `icon-labels-above-lines` now compares parents. Before, it failed correct diagrams that put icons inside a group container.

## [1.14.0] - 2026-11-02

### Added

- **Drawio-conventions skill.** A house style for draw.io diagrams, applied whenever a `.drawio` file is created or edited. Edges attach to the shape rather than to a fixed connection point, so they follow when shapes move. Line jumps are on by default. Spacing, edge, label and icon defaults keep diagrams readable, and Claude runs a checklist over the XML before it calls a diagram done. The style choices live in `references/house-style.md`, so they can be replaced without touching the rules.
- Eval suites for evaluate-session (12 cases) and drawio-conventions (11 cases), next to the existing release-version suite. `scripts/eval.sh <skill-name>` runs one skill's cases.

### Fixed

- Evaluate-session no longer grades a session itself when the grading script produces no scorecard. A skipped short session, a secret match or a failed grading call is now reported with its reason.
- `evaluate.sh` no longer needs `claude` on PATH for a skip or a dry run, and a skip is now reported on stderr instead of ending silently.
- Switching on automatic grading repeats the cost and how to switch it off in the reply that confirms it.

## [1.13.0] - 2026-09-23

### Added

- Releases now check the project's docs against the change before going out. `version.sh check`, and `version.sh docs` on its own, list every README, CLAUDE.md, AGENTS.md, CONTRIBUTING and living doc under `docs/`, mark which ones the branch touched, and warn about paths a doc names that are no longer in the repo. The skill judges each doc for its reader, writes and commits what is missing before the dry run, and leaves dated plans, ADRs and decision records alone because they are history.
- A release now shows its progress: nine fixed steps marked done, running or still to come, through the task list when the harness has one and always at the approval step.

### Changed

- `version.sh release` requires `--docs-note "<outcome>"`, which appears in the PR body under the tests line, or `--no-docs-check`, which makes the PR say the docs were not checked. Anyone calling `version.sh release` directly needs to add one of the two.

## [1.12.0] - 2026-09-23

### Added
- Scorecards now record which session they graded, in an invisible `<!-- session: <id> -->` line at the end, so tools such as a dashboard can link each scorecard to its session.

## [1.11.0] - 2026-09-23

### Added

- The evaluate-session hook now logs one line for every session that ends: graded, skipped and why (grading off, too few prompts, a secret matched, no transcript), or failed and where. The log lives in the plugin's data directory, trims itself, and `enable-hook.sh --status` shows the last five lines. Before this, a skipped session looked exactly like a hook that never fired.

## [1.10.0] - 2026-09-23

### Added

- **Evaluate-session skill.** Grades how *you* drove a Claude Code session —
  not the code it produced. A session that shipped working code through six
  vague prompts grades badly; one that carefully scoped a task that turned out
  to be unnecessary grades well. You get a letter band, the two practices worth
  focusing on with the message numbers they rest on, and the ones you did well,
  written to `~/.claude/scorecards/` with a line appended to an index. The index
  is the point: one scorecard is a mood, the table is whether anything is
  improving. Scorecards live outside the project on purpose — they are about a
  person, not a codebase, and a public repo should never carry one.
- **A catalogue of nineteen practices** behind the grade, `BP-01` to `BP-19`,
  each with its reasoning and how observable it is in a transcript. Only ten are
  visible in a session; three are properties of the project, read from the
  filesystem; the rest are inferable at best. A practice the evidence cannot
  show is reported as unobserved rather than counted against you, because a
  grade that punishes invisible things cannot be argued with and gets ignored.
  The catalogue and the rubric are both meant to be edited.
- **Automatic grading at the end of every session, off by default.** The plugin
  registers a `SessionEnd` hook that does nothing until `enable-hook.sh --on`
  writes a marker file, so installers who never wanted this pay a few
  milliseconds per exit and nothing else. Switched on, it grades every real exit
  on Haiku for roughly 6,000 input tokens — a fraction of a cent. It runs
  detached, so it never delays the exit. `--off`, `--status` and `--test` do
  what they say; `/evaluate-session` keeps working either way. Nothing is
  written to `settings.json`, so no path can go stale when the plugin updates.
- **A privacy boundary in front of the grading call.** Transcripts are reduced
  to a digest before anything is sent: your messages verbatim, because they are
  what is being graded, and everything else flattened to shape — tool names and
  counts, files touched, commits, test runs. Assistant prose, tool output and
  file contents never enter it. Paths are made relative to the project and
  anything outside it is dropped. A transcript whose messages match a secret
  pattern produces no digest at all rather than an annotated one. Real sessions
  come out 127 to 659 times smaller, which is what makes grading every session
  affordable.
- **A calibration suite for the grader.** `plugin/evals/session-calibration/`
  builds two synthetic sessions with known ground truth — one that cost itself
  five episodes, one driven properly — and fails when either escapes its band.
  A rubric that resolves ambiguity upward can quietly stop marking anything
  down, and no real transcript can detect that: a run of A grades looks the same
  whether the rubric works or not.

### Changed

- **`scripts/test.sh` validates plugin hooks.** A malformed `hooks.json` fails
  silently — the hook simply never runs, and nothing else would notice. The
  suite now checks that it parses, declares its events, and points at files that
  exist and are executable.

## [1.9.1] - 2026-09-22

### Fixed

- **Installs sitting on 1.9.0 can pick up updates again.** 1.9.0 was published
  twice with different contents, on 18 and 22 September, so an install that took
  the first publication saw no version change to update towards and stayed on the
  older files. This release republishes the current contents under a version that
  updates do pick up. Coming from 1.9.0, that means everything listed under it:
  the eval suite and the `version.sh` unit tests, the release-version description
  and changelog-writing fixes, and the `mktemp` change that lets the release
  script run where only `TMPDIR` is writable.

## [1.9.0] - 2026-09-22

### Added

- **Release-version skill.** Bumps the project version and opens a release pull
  request with a written changelog. A shell script owns every state change, so
  releases are reproducible; the model only writes the prose. It finds the
  version wherever the project already keeps it — `VERSION`, `package.json`,
  `composer.json`, `pyproject.toml`, `Cargo.toml`,
  `.claude-plugin/marketplace.json`, any `*/.claude-plugin/plugin.json` — bumps
  them together, and stops if they disagree. Releases are gated on the
  project's tests: the release aborts on a failure with the tree untouched, and
  the pull request body records whether the suite ran or was skipped. Tagging
  is a separate step, run after the merge.
- **`scripts/test.sh`** — validates the marketplace: manifests parse and agree
  on version and plugin name, every skill has frontmatter whose name matches
  its directory and a non-empty body, every shell script parses and is
  executable.
- **Checks for the release script itself.** `scripts/test-version-sh.sh` is 66
  offline unit tests over version-source detection, semver arithmetic, the
  in-place JSON edit that keeps a manifest diff to one line, the test gate and
  the dirty-tree refusal. `plugin/evals/` holds a ten-case eval suite, run by
  `scripts/eval.sh`, that checks the skill fires on a real release request,
  stays quiet on near misses, and stops for approval rather than opening the
  pull request on its own.

### Changed

- **Context-handover and session-handoff trigger without being named.** Their
  descriptions now name the situations — a session getting long, stopping for
  the day, moving to another machine or account, ending a long session that
  produced work worth keeping — instead of waiting for the command.
- **Session-handoff's `CURRENT.md` is derived by a script.** Two sessions that
  collide on the index self-heal on the next run, long lists are capped so it
  stays readable, and an entry the script cannot parse stops the run and names
  the file rather than dropping a workstream from the index.
- The "adding a new skill" steps in the README point at `/release-version`
  instead of hand-editing both manifests, and the skill layout allows a
  `scripts/` directory.

