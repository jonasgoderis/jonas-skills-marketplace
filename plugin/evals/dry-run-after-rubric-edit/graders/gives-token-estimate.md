---
type: regex
target: last_message
pattern: '[0-9][0-9,.]*\s*[kK]?\s*(input\s+)?tokens'
match: contains
---

A number followed by "tokens" — the estimate --dry-run prints.
