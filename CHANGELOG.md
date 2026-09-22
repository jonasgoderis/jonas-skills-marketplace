# Changelog


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

