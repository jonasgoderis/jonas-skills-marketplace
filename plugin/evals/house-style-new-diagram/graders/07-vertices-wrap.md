---
type: regex
target:
  source: file
  path: docs/architecture.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?![^>]*edgeLabel)(?![^>]*whiteSpace=wrap)[^>]*>'
match: not_contains
---
