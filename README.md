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
└── SKILL.md
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

3. Bump the version in `.claude-plugin/marketplace.json` and `plugin/.claude-plugin/plugin.json`
4. Commit, push, then run `/plugin update`

## Structure

```
├── .claude-plugin/
│   └── marketplace.json        # Marketplace registry
├── plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json         # Plugin metadata
│   └── skills/
│       └── <skill-name>/
│           └── SKILL.md
└── README.md
```
