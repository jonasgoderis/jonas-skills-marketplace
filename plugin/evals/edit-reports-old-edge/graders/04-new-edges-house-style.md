---
type: regex
target:
  source: file
  path: docs/flow.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?![^>]*id="e-user-api")(?:(?![^>]*jumpStyle=arc)|(?![^>]*strokeColor=#999999)|(?![^>]*strokeWidth=2\b)|(?![^>]*endArrow=block))[^>]*>'
match: not_contains
---
