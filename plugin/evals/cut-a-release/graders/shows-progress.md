---
type: regex
target: last_message
pattern: '[✓▶○]\s*Check the docs'
match: contains
---

The approval message opens with the status block from assets/progress.md. The
glyph is what makes this a use and not a mention: the skill text itself names
the step, and on `target: trace` that alone passed a run that showed no
progress at all.
