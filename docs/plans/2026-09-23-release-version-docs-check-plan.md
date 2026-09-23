# release-version: check the docs and show the flow

## The ask

1. Before releasing, check the project's documentation against what changed: README,
   CLAUDE.md, anything under `docs/`, and any other doc files. Where docs are missing
   or out of date, write them and then continue with the release.
2. While the skill runs, show a clear overview of the flow: which steps are done,
   which one is running, and which are still to come.
3. The PR body records the result of the docs check, the same way it already
   records the tests.
4. A path that the docs mention but that no longer exists is reported as a warning.
   For now it doesn't block the release.

## Where the skill stands today

- `version.sh check` looks at tools, auth, remote, working tree, test command and
  version sources. The tests are the only gate.
- Nothing compares the branch's diff with the docs.
- The procedure has eight numbered steps in prose. There is no visible progress; the
  user only sees whichever tool call is running.
- The skill's design splits the work: the script handles every state change and every
  deterministic fact, and the model writes the prose and makes the judgement calls.
  Both additions have to fit that split.

## Design decisions

### The docs check is a step the model performs; the script only supplies facts

Whether a change needs a doc update is a judgement call, so the script doesn't decide
it. The script lists the doc files, shows which ones the branch touched, and warns
about missing paths. The model reads those facts next to the diff and decides.

### Writing the missing docs

When the model finds a gap, it writes the doc change, commits it as its own commit
("Document …"), and carries on. That fits the existing rules for three reasons:

- `release` refuses a dirty tree, so the docs commit has to exist before the dry run.
- Nothing has left the machine yet. The approval pause at the dry-run step still comes
  before anything is pushed. At that pause the model shows the docs commit next to the
  notes, so the user reviews the doc change in the same place.
- A separate commit keeps the doc change easy to amend or drop at the pause.

One limit: the model fills gaps that follow from the diff. It does not rewrite docs
for style, and it doesn't restructure a doc that is merely old.

### Which docs count

The skill ships to everyone who installs the plugin, so the doc list is found by
convention, not hard-coded:

- `README*`, `CONTRIBUTING*` and `AGENTS.md` at the root
- every `CLAUDE.md`, including nested ones
- living documents under `docs/` or `doc/`

The last item needs a rule. `docs/` usually mixes two kinds of file:

- **Living docs**, such as a usage guide or an architecture page, describe the project
  as it is now. They get checked.
- **Point-in-time docs**, such as dated plans, reviews, ADRs or snapshots (in this repo,
  everything named `YYYY-MM-DD-*`), record what was true when they were written.
  Rewriting them falsifies history. They are skipped, and a stale one doesn't count as
  a gap.

The script applies that split with a simple rule: a date prefix or an `adr/` /
`decisions/` directory marks a file as point-in-time. The model can override the rule
when it's obviously wrong for a particular file.

The script already writes `CHANGELOG.md`, so it isn't in the list.

### What "needs updating" means for each kind of reader

- **User-facing docs** (README, usage guides): install, usage, commands, options,
  configuration, listed features or documented structure changed.
- **Agent-facing docs** (CLAUDE.md, AGENTS.md): a convention, command, layout or
  workflow they state is now false, or the change adds a convention that future
  sessions would otherwise have to rediscover.
- **Contributor docs** (CONTRIBUTING, dev guides): how to build, test or release
  changed.
- **Never a reason on its own:** internal refactors, fixes that don't change
  documented behaviour, or test-only changes.

### Showing the flow: the harness's task list, not a hand-drawn checklist

Claude Code already has a task list that stays on screen and marks each step done, in
progress or pending. That is exactly the overview asked for, and it's more visible than
anything printed into chat. So the skill:

- creates the task list at the start, using fixed step names so every run looks the
  same:

  1. Pre-flight check
  2. Read what changed
  3. Check the docs
  4. Propose the version
  5. Write the release notes
  6. Dry run (tests)
  7. Your approval
  8. Open the release PR
  9. Tag after merge

- marks each step as it starts and as it finishes. A step with a result gets it in one
  line, for example "Check the docs — README updated, CLAUDE.md no change".
- at the approval pause, also prints the same list as a short status block in chat,
  because the user reads the conversation at that moment and has to see what is
  already done.

Where no task-list tool is available, as in another client or an older version, the
skill falls back to printing the status block at every step change. The format lives
in `assets/progress.md`, so it doesn't change between runs.

Why not have the script render progress: the steps are driven by the model, so the
script doesn't know where the run is. Bash output also isn't reliably shown to the
user. A `progress` command would mean state files and would still need the model to
repeat its output.

## The plan

### 1. `version.sh check`: a `docs:` section

- It lists the doc files found under the rules above, each marked *touched* or
  *untouched* in `<base>..HEAD`, with point-in-time files shown as skipped.
- It reports `warn:` lines for backticked repo paths in those docs that no longer
  exist. These don't cause a non-zero exit.
- **Base:** the default branch in `combined` mode, and the last tag in `release` mode.
  In release mode the work is already merged, so a diff against the default branch
  would be empty.

Unit tests go in `scripts/test-version-sh.sh`. They cover:

- a touched doc and an untouched one
- a nested CLAUDE.md
- a dated file under `docs/` that should be skipped
- a missing path
- a repo with no docs
- a release-mode base taken from the tag

### 2. `release --docs-note "<text>"`

- It adds a `Docs:` line to the PR body next to the `Tests:` line, such as
  "Docs: README and docs/usage.md updated" or "Docs: checked, no change needed".
- It is required, following the same reasoning as the tests: if it's missing,
  `release` stops. A release that skipped the check must not look like one that ran it.
  `--no-docs-check` exists as the explicit escape hatch, and when it's used the PR body
  says so.
- Unit tests cover the rendered line, the refusal when the note is missing, and the
  escape hatch.

### 3. `SKILL.md`

- **New step 3, "Check the docs",** covering the rules above: find the docs, judge each
  one against the diff, write and commit the missing parts, and record a one-line
  outcome for `--docs-note`.
- **Procedure intro:** create the task list with the fixed names, and update it at each
  transition. Add `assets/progress.md` for the fallback.
- **Step 6 (approval):** show the docs commit next to the notes and the dry-run plan.
- **Description:** add "checks and updates the docs" so it's clear the skill covers
  that, and confirm with a trigger run that routing doesn't move.
- The file grows by about 40 lines and stays well under 500.

### 4. Evals

These are new behavioural cases on the `release-repo.sh` fixture:

- **`stale-readme`:** the branch adds a user-facing command that the README doesn't
  mention. Graders check that:
  - a docs commit exists before the dry run
  - the README mentions the new command
  - `--docs-note` was passed
  - no PR was opened
- **`internal-fix-no-docs`:** the branch only fixes an internal bug. The graders check
  that there is no docs commit and that the note reads "no change needed". This is the
  near-miss that stops the check turning into busywork.
- **`dated-plan-untouched`:** the branch makes a change that a dated plan in `docs/`
  describes out of date. The grader checks that the plan was not edited.
- **Progress:** a `tool_used` grader on the task-list tool is added to the existing
  `cut-a-release` case.

### 5. Housekeeping in this repo

- Load `anthropic-skills:skill-creator` before editing, as CLAUDE.md requires.
- Update the README's "Checks" table (the unit-test count changes) and document the new
  `check` output and `--docs-note`. The release of this change is the first real run of
  the docs check.
- CLAUDE.md probably needs no change. The new step will confirm that rather than me
  assuming it.
- Ship via `/release-version` as a **minor** release. It adds a capability, but with a
  caveat: making `--docs-note` required breaks anyone who calls `version.sh release`
  directly. The skill is the only caller, so I'd treat it as minor and name the new
  flag in the notes. If you'd rather avoid that change, make the flag optional and
  let only the skill insist on it.

## Order of work

1. Script: the `docs:` section, `--docs-note`, and their unit tests
2. SKILL.md: docs step, task list, `assets/progress.md`, description
3. Evals: the three new cases and the progress grader, then run `scripts/eval.sh` on
   those cases only, because it costs money
4. README, `scripts/test.sh`, then the release

## Outcome

Built as planned, with one change: the dated-plan check went into `stale-docs`
instead of a third case, since the model is already editing docs there and that
makes it the better near-miss.

The first eval passes surfaced three things the plan did not foresee:

- **A README typo became a changelog line** after the model had just made a docs
  commit. "Writing the notes" now says doc-only commits are not bullets.
- **Doc edits happened while a blocker was open.** In `no-test-command`, the
  model raised the missing tests and then edited the README anyway, leaving an
  uncommitted change. Step 3 now waits until nothing earlier is waiting on the
  user.
- **No status block appeared** while the step list lived only in
  `assets/progress.md`. The block is now inline in the Procedure section. The
  first progress grader used `target: trace`, so it matched the skill's own text
  and passed a run that showed no progress; it now uses `target: last_message`
  and requires a status glyph.

Final results: all 8 trigger cases at 1.00 on 1 run, and all 4 behavioural cases
at 1.00 on 3 runs. Unit tests: 90/90.
