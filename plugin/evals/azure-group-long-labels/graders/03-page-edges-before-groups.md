---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*container=1)(?=[^>]*\bparent="1")[^>]*>[\s\S]*<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*\bparent="1")'
match: not_contains
---
