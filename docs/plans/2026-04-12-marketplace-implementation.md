# Personal Skills Marketplace Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scaffold the `claude-skills` repo as a native Claude Code marketplace with a single bundled plugin.

**Architecture:** The repo root is the marketplace (`.claude-plugin/marketplace.json`). A `plugin/` directory contains the single `claude-skills` plugin with its own `.claude-plugin/plugin.json` and a `skills/` directory for skill definitions.

**Tech Stack:** Claude Code plugin system (JSON config + Markdown skills)

---

### Task 1: Create marketplace.json

**Files:**
- Create: `.claude-plugin/marketplace.json`

**Step 1: Create the marketplace config**

```json
{
  "name": "jonas-skills-marketplace",
  "description": "Personal skills, commands, and tools for Claude Code",
  "owner": {
    "name": "Jonas Goderis"
  },
  "plugins": [
    {
      "name": "claude-skills",
      "description": "Personal skills collection for Claude Code",
      "version": "1.0.0",
      "source": "./plugin",
      "author": {
        "name": "Jonas Goderis"
      }
    }
  ]
}
```

**Step 2: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: add marketplace config"
```

---

### Task 2: Create plugin.json

**Files:**
- Create: `plugin/.claude-plugin/plugin.json`

**Step 1: Create the plugin metadata**

```json
{
  "name": "claude-skills",
  "description": "Personal skills collection for Claude Code",
  "version": "1.0.0",
  "author": {
    "name": "Jonas Goderis"
  },
  "keywords": ["skills", "personal"]
}
```

**Step 2: Commit**

```bash
git add plugin/.claude-plugin/plugin.json
git commit -m "feat: add plugin metadata"
```

---

### Task 3: Create placeholder skill

**Files:**
- Create: `plugin/skills/.gitkeep`

A `.gitkeep` so the skills directory is tracked in git even when empty. Skills will be added later.

**Step 1: Create the placeholder**

```bash
touch plugin/skills/.gitkeep
```

**Step 2: Commit**

```bash
git add plugin/skills/.gitkeep
git commit -m "feat: add skills directory"
```

---

### Task 4: Create README

**Files:**
- Create: `README.md`

**Step 1: Write the README**

The README should cover:
- What this repo is
- How to install (register marketplace + install plugin)
- How to add a new skill (create directory, write SKILL.md, commit, push, update)
- Link to Claude Code plugin docs

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with install and usage instructions"
```

---

### Task 5: Push to GitHub

**Step 1: Create GitHub repo**

```bash
gh repo create jonas-skills-marketplace --private --source=. --push
```

Note: Use `--private` since this is a personal marketplace. The user can make it public later if desired.
