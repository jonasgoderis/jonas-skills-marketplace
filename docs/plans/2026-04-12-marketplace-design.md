# Personal Claude Code Skills Marketplace

## Overview

Turn the `claude-skills` git repo into a native Claude Code marketplace with a single bundled plugin containing all personal skills.

## Decisions

- **Audience**: Personal use only
- **Structure**: One plugin (`claude-skills`) containing all skills
- **Marketplace name**: `jonas-skills-marketplace`
- **Plugin name**: `claude-skills`
- **Migration**: Start fresh (existing skills in `~/.claude/skills/` left as-is)

## Architecture

The repo uses Claude Code's native plugin/marketplace system. The repo itself is the marketplace, containing a single plugin with all skills bundled.

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json           # Marketplace registry
├── plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json            # Plugin metadata
│   ├── skills/
│   │   └── <skill-name>/
│   │       └── SKILL.md
│   ├── commands/                   # Future slash commands
│   └── hooks/                      # Future hooks
└── README.md
```

### marketplace.json

Registers the marketplace and points to the bundled plugin at `./plugin`.

### plugin.json

Contains plugin metadata: name, description, author.

### Skills

Each skill is a directory under `plugin/skills/` containing a `SKILL.md` with YAML frontmatter (`name`, `description`) and markdown content.

## Installation Flow

1. Push repo to GitHub
2. Register: `/plugin marketplace add jonasgoderis/jonas-skills-marketplace`
3. Install: `/plugin install claude-skills@jonas-skills-marketplace`
4. Update: `/plugin update`

## Adding a New Skill

1. Create `plugin/skills/<name>/SKILL.md`
2. Add frontmatter with `name` and `description`
3. Commit, push
4. Run `/plugin update` to pull latest
