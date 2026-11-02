---
type: regex
target:
  source: file
  path: docs/architecture.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?:(?![^>]*strokeColor=#999999)|(?![^>]*strokeWidth=2\b)|(?![^>]*endArrow=block))[^>]*>'
match: not_contains
---
