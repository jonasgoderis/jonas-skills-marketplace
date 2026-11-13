---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*dashed=1)(?=[^>]*dashPattern=)[^>]*>'
match: not_contains
---
