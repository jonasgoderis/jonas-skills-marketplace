---
type: regex
target:
  source: file
  path: gh.log
pattern: 'pr create'
match: not_contains
---
