# Changelog

## [1.9.0] - 2026-09-18

### Added

- **Versioning skill.** Bumps the project version and opens a release pull request
  with a written changelog. A shell script owns every state change, so releases are
  reproducible; the model only writes the prose.
- The script finds the version wherever the project already keeps it — `VERSION`,
  `package.json`, `composer.json`, `pyproject.toml`, `Cargo.toml`,
  `.claude-plugin/marketplace.json`, any `*/.claude-plugin/plugin.json` — bumps all
  of them together, and stops if they disagree. Projects with no version source at
  all get a `VERSION` file.
- Releases are gated on the project's tests. The command is found by convention,
  the release aborts on a failure with the tree untouched, and the PR body records
  whether the suite ran or was skipped.
- `CHANGELOG.md` is maintained from the same notes that become the PR description.
- Tagging is a separate step, run after the merge.
- **`scripts/test.sh`** — validates the marketplace: manifests parse and agree on
  version and plugin name, every skill has frontmatter whose name matches its
  directory and a non-empty body, every shell script parses and is executable.

### Changed

- The "adding a new skill" steps in the README now point at `/versioning` instead
  of hand-editing both manifests, and the skill layout allows a `scripts/`
  directory.

