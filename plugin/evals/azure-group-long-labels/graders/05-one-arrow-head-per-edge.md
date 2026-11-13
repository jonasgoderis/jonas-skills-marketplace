---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*startArrow=(?!none)\w)[^>]*>'
match: not_contains
---
