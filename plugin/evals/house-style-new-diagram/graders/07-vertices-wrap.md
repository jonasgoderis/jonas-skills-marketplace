---
type: regex
target:
  source: file
  path: docs/architecture.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?![^>]*edgeLabel)(?![^>]*style="(?:image;|[^"]*shape=(?:image|mxgraph\.)))(?![^>]*whiteSpace=wrap)[^>]*>'
match: not_contains
---
