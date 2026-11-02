---
type: regex
target:
  source: file
  path: docs/flow.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*source="api")(?=[^>]*target="db")(?=[^>]*jumpStyle=arc)[^>]*>'
match: contains
---
