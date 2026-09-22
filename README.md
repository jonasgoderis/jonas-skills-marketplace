# Jonas Skills Marketplace

Personal Claude Code marketplace with skills, commands, and tools.

## Install

```bash
# Register the marketplace (once)
/plugin marketplace add jonasgoderis/jonas-skills-marketplace

# Install the plugin
/plugin install claude-skills@jonas-skills-marketplace
```

## Update

```bash
/plugin update
```

## Adding a new skill

1. Create a directory under `plugin/skills/`:

```
plugin/skills/my-new-skill/
├── SKILL.md
└── scripts/          # optional — anything the skill should do deterministically
```

2. Write `SKILL.md` with frontmatter:

```yaml
---
name: my-new-skill
description: Use when [trigger conditions]. Examples: "do X", "help with Y".
---

# My New Skill

Skill content here...
```

3. Commit the skill, then run `/release-version` — it bumps both manifests, writes the
   changelog entry and opens the release PR
4. After the merge, run `/plugin update`

## Checks

None of these gate a release; they are run on purpose.

| Command | When |
| --- | --- |
| `scripts/test.sh` | Before pushing. Manifests, skill frontmatter, shell syntax. |
| `scripts/test-version-sh.sh` | After touching `release-version`'s `version.sh`. 66 unit tests, free and offline. |
| `scripts/eval.sh` | After changing a skill description or procedure. Costs money; see `plugin/evals/README.md`. |
| `scripts/sync-eval-fixtures.sh` | After editing an eval fixture. `--check` reports drift. |
| `claude plugin validate plugin --strict` | Any change to a manifest. |

## Structure

```
├── .claude-plugin/
│   └── marketplace.json        # Marketplace registry
├── plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json         # Plugin metadata
│   └── skills/
│       └── <skill-name>/
│           ├── SKILL.md
│           └── scripts/        # optional
└── README.md
```
