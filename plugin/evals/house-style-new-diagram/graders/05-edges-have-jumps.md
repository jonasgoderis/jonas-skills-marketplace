---
type: regex
target:
  source: file
  path: docs/architecture.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?:(?![^>]*edgeStyle=orthogonalEdgeStyle)|(?![^>]*jumpStyle=arc)|(?![^>]*jumpSize=6))[^>]*>'
match: not_contains
---
