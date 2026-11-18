---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*container=1)(?=[^>]*dashed=1)(?![^>]*strokeColor=#999999)[^>]*>'
match: not_contains
---
