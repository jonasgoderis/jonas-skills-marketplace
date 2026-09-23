# Claude Marketplace

A personal Claude Code marketplace. Each skill lives in `plugin/skills/<name>/`
and ships to anyone who installs the plugin, so treat every skill as published
software rather than a personal note.

## Anthropic's skill-authoring guidance is the standard here

Before creating a skill, or making any non-trivial change to one, load the
`anthropic-skills:skill-creator` skill and follow it. It is the authority; this
file only records the parts that apply to every change so they are not
rediscovered each session.

The guidance lives in two places on disk, and going to it directly beats
reasoning from memory about what Anthropic recommends:

- **`anthropic-skills:skill-creator`** owns the authoring loop — draft, test
  prompts, evals, description optimisation. Two of its scripts settle questions
  that otherwise get argued: `scripts/quick_validate.py` is the only thing
  anywhere that enforces a naming rule, and `scripts/run_loop.py` optimises a
  description against measured trigger rates rather than taste.
- **The official plugin marketplace**, under
  `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/`. Its
  `plugin-dev` plugin carries `skill-development`, `hook-development`,
  `command-development`, `agent-development`, `plugin-structure`,
  `plugin-settings` and `mcp-integration`. Read the matching one when a change
  touches plugin machinery rather than a skill's prose — shipping a hook is a
  different job from writing a `SKILL.md`, and this file says nothing about it.

The parts of that guidance which bear on every change here:

- **The description is the trigger.** All "when to use this" information belongs
  in the frontmatter `description`, not the body. Claude tends to *under*-trigger
  skills, so descriptions lean pushy: name the contexts, the alternative
  phrasings, and the cases where the user needs the skill without naming it.
- **Progressive disclosure.** Metadata is always in context, the body loads when
  the skill fires, bundled resources load only when needed. Keep `SKILL.md` under
  500 lines; past that, move detail into `references/` and point at it.
- **Deterministic work goes in `scripts/`.** If the skill describes a fixed
  procedure in prose — a file format, an index rebuild, a sequence of `git` and
  `gh` calls — the model will reconstruct it, slightly differently, every run.
  Write it once as a script and have the skill call it. Fixed output files
  (templates, wrappers, stylesheets) go in `assets/` for the same reason.
- **Explain why, don't shout.** Capitalised `MUST` / `ALWAYS` / `NEVER` and rigid
  scaffolding are a sign the reasoning is missing. State the reason and the model
  handles the cases the rule never anticipated.
- **Write for reuse, not for the example in front of you.** A skill that only
  works for one project, one person or one trip is a note, not a skill. Where
  something genuinely is personal configuration, isolate it in `references/` so
  the skill still degrades gracefully for everyone else.
- **Imperative instructions.** "Read the commits", not "you should read".

### Settled, so stop re-deriving it

- **There is no verb or gerund convention for skill names.** `skill-creator`
  defines `name` as an identifier and says nothing further; `quick_validate.py`
  enforces only kebab-case — lowercase letters, digits and hyphens, none leading,
  trailing or doubled. Across Anthropic's own official skills, nouns outnumber
  verbs about four to one. Pick what reads well and move on. **Imperative
  instructions**, above, governs the instruction prose, not the `name` field —
  they are easy to conflate.
- **A description is tested, not argued.** It is the trigger, so a disagreement
  about whether a skill will fire — or whether it will steal a sibling skill's
  prompts — is settled by trigger cases in `plugin/evals/`, where the negatives
  that matter are the near-misses against those siblings. `run_loop.py` is there
  for a one-off tuning pass when a description needs more than a guess.
- **Look for prior art before building.** The official marketplace ships adjacent
  skills, and one may already have solved the hard half. `session-report`, for
  instance, parses `~/.claude/projects` transcripts and bundles the analyser for
  it. Reuse the approach rather than reinventing the parse.

## Repo conventions

- `name:` in the frontmatter must equal the skill's directory name.
- `scripts/test.sh` validates the marketplace — manifests, skill frontmatter,
  shell syntax. Run it before pushing; the release gate runs it too.
- Never hand-edit the version in `.claude-plugin/marketplace.json` or
  `plugin/.claude-plugin/plugin.json`. Run `/release-version`, which bumps both,
  writes `CHANGELOG.md` and opens the release PR. Tag after the merge.
- Plans and design docs go in `docs/plans/`, dated `YYYY-MM-DD-`.

## Publishing

This repo is public. Anything committed here is outbound: no credentials, no
client material, and no personal data about the author or anyone else. Personal
preferences baked into a skill are still personal data — flag them rather than
shipping them quietly.
