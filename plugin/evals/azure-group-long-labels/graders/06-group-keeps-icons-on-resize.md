---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*container=1)(?![^>]*recursiveResize=0)[^>]*>'
match: not_contains
---
