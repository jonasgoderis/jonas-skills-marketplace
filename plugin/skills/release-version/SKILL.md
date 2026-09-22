---
name: release-version
description: Cut a release — bump the project version, write the changelog entry, open the release pull request, and tag once it merges. Use this whenever the user wants to release, ship, publish or cut a new version, bump to X.Y.Z, prepare release notes or a changelog entry, sync a version across manifests, or get a finished branch out the door. Reach for it even when the word "release" is never said: "the work's done", "get this out the door", "what should the next version be", "write the changelog for this branch". Those read like one-step jobs, which is exactly why they get done by hand — but writing the changelog, editing a version or pushing the branch yourself skips the manifest sync, the test gate and the approval step that make a release reproducible. A pull request for work still in progress is not a release; finishing something and sending it out is. Triggers on /release-version.
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
version.sh init [X.Y.Z]               create a VERSION file (default 0.1.0)
version.sh bump <level> [--dry-run]   write the new version, nothing else
version.sh release <level> --notes-file F --title T [--mode combined|release]
                                      [--test-cmd C | --no-test] [--base B]
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

## Procedure

1. **Check first.** Run `version.sh check`. It reports missing `gh`, missing auth,
   a missing remote, a dirty tree, the test command and the version sources in one
   pass, and exits non-zero if any of it would block a release. Fix what it names
   before going on.
2. **Read what actually changed.** `git log --oneline <base>..HEAD` and
   `git diff --stat <base>..HEAD`. The changelog is written from this, not from
   memory of the conversation — work done before the branch existed does not belong
   in it, and work you did not do does not either.
3. **Propose the level.** Breaking change to a documented interface → `major`.
   New capability, backwards compatible → `minor`. Fix, correction or internal
   change only → `patch`. Say which and why in one line, and let the user correct
   you. Below `1.0.0` the same rules apply one place to the right in practice, but
   do not silently reinterpret them — ask.
4. **Write the notes** to a scratch file (session scratchpad, not the project).
   This is the body of both the changelog entry and the PR description.
5. **Dry run.** `version.sh release <level> --notes-file <f> --title <t> --dry-run`
   runs the tests for real, then prints the plan and the rendered PR body. Nothing
   is written, branched, committed or pushed.
6. **Show the user the notes and the plan, and wait.** A PR is outward-facing and
   permanent enough. Do not open one on your own initiative.
7. **Release.** Drop `--dry-run`.
8. **After the merge**, `version.sh tag <X.Y.Z>`. Tagging before the merge tags a
   commit that may never reach the default branch.

## Writing the notes

Keep a Changelog structure, `###` headings, only the sections that have content:
**Added**, **Changed**, **Fixed**, **Removed**, **Deprecated**, **Security**.

- One line per change, in the present tense, describing what is different for
  someone using the project — not which files moved.
- Lead with the thing that changed, not with the verb: "Trip itineraries now
  render offline" beats "Added offline rendering to trip itineraries".
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
