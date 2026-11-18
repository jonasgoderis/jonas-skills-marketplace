---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*container=1)(?=[^>]*\bvalue="[^"])[^>]*>'
match: not_contains
---
