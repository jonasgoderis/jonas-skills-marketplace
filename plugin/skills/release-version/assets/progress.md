# Release progress

The nine steps, named the same in every release. Use them verbatim as task-list
items, or in the status block below when there is no task list.

1. Pre-flight check
2. Read what changed
3. Check the docs
4. Propose the version
5. Write the release notes
6. Dry run (tests)
7. Your approval
8. Open the release PR
9. Tag after merge

## Status block

One line per step. `✓` done, with its result after the dash; `▶` in progress;
`○` still to come. Keep each result to a few words: the line is a signpost,
not the report.

```
Release v1.4.0 — progress
✓ Pre-flight check        — clean tree, gh ok, 2 version sources
✓ Read what changed       — 5 commits since main
✓ Check the docs          — README updated (committed), CLAUDE.md no change
✓ Propose the version     — minor: new --shout flag
✓ Write the release notes
✓ Dry run (tests)         — scripts/test.sh passed
▶ Your approval
○ Open the release PR
○ Tag after merge
```

A step that was skipped says so rather than showing `✓`, for the same reason
the PR body records a skipped test run: `– Dry run (tests) — skipped (--no-test)`.
