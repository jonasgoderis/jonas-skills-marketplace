---
name: release-version
description: Cut a release — check the docs still match the change, bump the project version, write the changelog entry, open the release pull request, and tag once it merges. Use this whenever the user wants to release, ship, publish or cut a new version, bump to X.Y.Z, prepare release notes or a changelog entry, sync a version across manifests, or get a finished branch out the door. Reach for it even when the word "release" is never said: "the work's done", "get this out the door", "what should the next version be", "write the changelog for this branch". Those read like one-step jobs, which is exactly why they get done by hand — but writing the changelog, editing a version or pushing the branch yourself skips the manifest sync, the test gate, the docs check and the approval step that make a release reproducible. A pull request for work still in progress is not a release; finishing something and sending it out is. Triggers on /release-version.
---

# Release version

A release is two jobs with opposite requirements. Deciding what changed and saying
it in readable English needs judgement. Editing manifests, branching, committing,
pushing and opening the PR needs to happen the same way every time, and a model
improvising `git` and `gh` invocations does not do that.

So the split is strict: `scripts/version.sh` owns every state change, and you own
the prose. You never bump a version with an editor, never call `gh pr create`
yourself, and never guess what changed — you read the commits.

## The script

`${CLAUDE_PLUGIN_ROOT}/skills/release-version/scripts/version.sh`, or `scripts/version.sh`
next to this file if that variable is unset. It acts on the current working
directory unless given `--repo`.

```
version.sh check                      tools, auth, repo state, tests, version sources
version.sh current                    the current version
version.sh test                       run the project's test command
version.sh docs                       the project's docs, which the branch touched, dead paths
version.sh init [X.Y.Z]               create a VERSION file (default 0.1.0)
version.sh bump <level> [--dry-run]   write the new version, nothing else
version.sh release <level> --notes-file F --title T [--mode combined|release]
                                      [--test-cmd C | --no-test] [--base B]
                                      [--docs-note N | --no-docs-check]
                                      [--branch B] [--draft] [--no-changelog]
                                      [--dry-run]
version.sh tag [X.Y.Z]                tag the merge commit, after the PR lands
```

`<level>` is `major`, `minor`, `patch`, or an explicit `X.Y.Z`. Versions are plain
`MAJOR.MINOR.PATCH`; prereleases are not supported and a source holding one is an
error, not something to bump past.

It finds the version wherever the project already keeps it — `VERSION`,
`package.json`, `composer.json`, `pyproject.toml`, `Cargo.toml`,
`.claude-plugin/marketplace.json`, any `*/.claude-plugin/plugin.json` — and bumps
all of them together. If several disagree it stops and shows you which, because
a project whose manifests have drifted apart has a problem a release will only
bury. If none exists, `init` creates a `VERSION` file; ask first, since adding one
to a repo that deliberately has none is a decision, not a detail.

JSON manifests are edited in place so the diff is one changed line per file, not a
reformat.

## Tests gate the release

`release` runs the project's tests before it touches anything, and aborts on a
failure with the tree untouched. It finds the command by convention, first match
winning: `scripts/test.sh`, `./test.sh`, a `test` script in `package.json` (with
the runner picked from the lockfile), a `test` target in a `Makefile`,
`cargo test`, `go test ./...`, then pytest.

If it finds nothing it stops and asks for `--test-cmd '<command>'` or `--no-test`.
It does not quietly proceed: a release that skipped the tests and a release that
had none look identical afterwards, and that is exactly the distinction worth
keeping. Whichever you use, the PR body records it: the command that ran and that it
passed, or that it was skipped. Leave that line alone. A PR that implies a green run
that never happened is worse than one that admits it skipped.

Tests run in the dry run too. That is the point of the dry run: it proves the
release would be green without creating anything.

If the project has no tests at all, say so and offer to write a test script before
releasing rather than reaching for `--no-test` by reflex.

## Docs are part of the release

Tests prove the code works; they say nothing about whether the README still tells
people how to use it. A release is the last moment someone looks at the whole
change before it goes out, so it is where stale docs get caught.

`release` requires `--docs-note "<one line>"` saying what the check found —
"README and docs/usage.md updated", "checked, no change needed" — and puts it in
the PR body under the tests line. `--no-docs-check` exists for the user who asks
for it, and the PR then says the docs were not checked. Same reason as the tests:
a skipped check and a clean one must not look alike afterwards.

The script cannot judge whether a doc needs changing, so it only supplies facts.
The `docs:` section of `check` (or `version.sh docs` on its own) lists every doc
it found — root `README*`, `CONTRIBUTING*`, `AGENTS.md`, every `CLAUDE.md` and
README at any depth, and everything under `docs/` or `doc/` — marks each one
touched or untouched on this branch, and warns about backticked paths a doc names
that are no longer in the repo. A warning is a lead, not a verdict: a doc may
legitimately name a file in another project.

Judge each change in the diff against the reader of each doc:

- **User-facing** (README, usage and install guides): does it change how someone
  installs, runs, configures or calls the project, or what it lists as features or
  structure? A new command, flag, option, setting or skill counts.
- **Agent-facing** (CLAUDE.md, AGENTS.md): is a convention, command, layout or
  workflow it states now false? Does the change add a convention the next session
  would otherwise have to rediscover? A new feature on its own is not a reason.
- **Contributor-facing** (CONTRIBUTING, dev guides): did how to build, test or
  release change?

Internal refactors, fixes that leave documented behaviour alone and test-only
changes need nothing. Do not invent doc work to have something to show — "checked,
no change needed" is a real result, and the common one.

"Touched" is not "up to date". A branch that updated the README for its first
feature and then added a second one has touched the README and still left a gap.

**Point-in-time docs are history.** The script counts dated files (`YYYY-MM-DD-*`),
`adr/` and `decisions/` as point-in-time and skips them. A plan that says "out of
scope: X" is still an accurate record after X ships; rewriting it falsifies what
was decided. Leave them alone, and do not report them as gaps.

When a doc needs changing, write the change: fill the gap the diff opened, in the
doc's own voice and structure, and nothing more — a release is not the moment to
restyle a README. Commit it on its own (`Document <the thing>`) before the dry run,
since `release` refuses a dirty tree. Nothing has left the machine yet, and the
approval step shows the commit next to the notes, so the user reviews both at once.
If the right content is genuinely unclear — the diff adds a setting and nothing
says what it is for — ask instead of guessing.

## Procedure

Releasing is several minutes of steps, most of them silent tool calls, so keep the
user oriented: they should always be able to see what is done, what is running and
what is still to come. The steps below have fixed names so every release reads the
same:

```
✓ Pre-flight check        — clean tree, gh ok, 2 version sources
✓ Read what changed       — 5 commits since main
✓ Check the docs          — README updated (committed)
✓ Propose the version     — minor: new --shout flag
✓ Write the release notes
✓ Dry run (tests)         — scripts/test.sh passed
▶ Your approval
○ Open the release PR
○ Tag after merge
```

`✓` done, with its result after the dash; `▶` in progress; `○` still to come; `–`
skipped, with the reason. If the harness has a task list, create these nine as
tasks before step 1 and update them as you go. With or without one, print this
block at the approval step — the user stops there to read, and a task list is not
always on screen. `assets/progress.md` has the same block with notes.

1. **Check first.** Run `version.sh check`. It reports missing `gh`, missing auth,
   a missing remote, a dirty tree, the test command, the version sources and the
   docs in one pass, and exits non-zero if any of it would block a release. Fix what it names
   before going on.
2. **Read what actually changed.** `git log --oneline <base>..HEAD` and
   `git diff --stat <base>..HEAD`. The changelog is written from this, not from
   memory of the conversation — work done before the branch existed does not belong
   in it, and work you did not do does not either. In `--mode release` the base is
   the last tag, since the work is already on the default branch.
3. **Check the docs** against that diff, as in *Docs are part of the release*.
   Write and commit what is missing; settle the one-line `--docs-note`. Only once
   nothing earlier is waiting on the user: if `check` raised a blocker — no tests,
   a dirty tree — stop and ask about that first. Doc edits made while the release
   may not happen leave uncommitted changes behind and bury the question under them.
   A docs gap you noticed can go in the same message as a question.
4. **Propose the level.** Breaking change to a documented interface → `major`.
   New capability, backwards compatible → `minor`. Fix, correction or internal
   change only → `patch`. Say which and why in one line, and let the user correct
   you. Below `1.0.0` the same rules apply one place to the right in practice, but
   do not silently reinterpret them — ask.
5. **Write the notes** to a scratch file (session scratchpad, not the project).
   This is the body of both the changelog entry and the PR description.
6. **Dry run.** `version.sh release <level> --notes-file <f> --title <t> --docs-note <n> --dry-run`
   runs the tests for real, then prints the plan and the rendered PR body. Nothing
   is written, branched, committed or pushed.
7. **Stop for approval.** Open the message with the status block from
   `assets/progress.md`, then give the notes, any docs commit from step 3 and the
   plan, and wait. A PR is outward-facing and permanent enough. Do not open one on
   your own initiative.
8. **Release.** Drop `--dry-run`.
9. **After the merge**, `version.sh tag <X.Y.Z>`. Tagging before the merge tags a
   commit that may never reach the default branch.

## Writing the notes

Keep a Changelog structure, `###` headings, only the sections that have content:
**Added**, **Changed**, **Fixed**, **Removed**, **Deprecated**, **Security**.

- One line per change, in the present tense, describing what is different for
  someone using the project — not which files moved.
- Lead with the thing that changed, not with the verb: "Trip itineraries now
  render offline" beats "Added offline rendering to trip itineraries".
- Doc-only commits are not bullets: a README typo fix, a reworded paragraph, or the
  docs commit from step 3. The changelog says what changed in the project, and the
  docs describing that change are already covered by its line. A doc is a line only
  when the doc is the product — a new guide someone would go looking for.
- A commit is not a bullet. Several commits that add one capability are one line;
  a commit that fixes a typo in a commit from an hour ago is no line at all.
- Collapsing is not the same as dropping. When several commits become one line,
  that line still has to account for all of them. A branch that adds two things
  and gets a note mentioning the second, with the first written as though it
  were already there, understates the release and misleads the reader about
  what is new.
- Breaking changes go first, under **Changed**, prefixed **BREAKING:**, and say
  what the reader has to do.
- No filler. A release with three real changes gets three lines. Padding it to
  look substantial teaches people to skip the changelog.
- Never claim a change you have not seen in the diff.

## Before the PR goes out

The PR body leaves this machine. Check it the way anything outbound gets checked:
no credentials, tokens or connection strings, no client names or internal paths,
no personal data, nothing quoted out of a private file. If the diff itself
contains any of that, say so and stop — a release is the wrong moment to discover
a secret was committed.

## One PR or two

The default, `--mode combined`, puts the work and the version bump in the same PR,
on the branch you are already on. One review, one merge, and the version in the
default branch always matches what is in it. This is the right default and what
you should use unless told otherwise.

`--mode release` is the alternative: it branches off the default branch and opens
a PR containing only the version bump and the changelog. Use it when the work has
already been merged unversioned, when several PRs are in flight at once and each
one bumping the same manifest line would mean a conflict per merge, or when
releasing is a separate decision from merging — a batch of merged work cut into a
release on its own schedule. It is the release-please model, and it is worth
proposing when you can see more than one open PR against the repo.

Both modes refuse to sweep uncommitted work into the release commit. Commit or
stash first; the bump is always its own commit.

## After it lands

`version.sh tag <X.Y.Z>` on the merged default branch. Then tell the user what
still needs doing by hand for this project — for a Claude Code marketplace that is
`/plugin update`.
