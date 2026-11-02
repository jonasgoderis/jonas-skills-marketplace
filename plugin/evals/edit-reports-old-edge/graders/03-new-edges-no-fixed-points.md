---
type: regex
target:
  source: file
  path: docs/flow.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?![^>]*id="e-user-api")(?=[^>]*(exit|entry)(X|Y|Dx|Dy)=)[^>]*>'
match: not_contains
---
