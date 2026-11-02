---
type: regex
target:
  source: file
  path: docs/aws.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?=[^>]*style="(?:image;|[^"]*shape=(?:image|mxgraph\.)))(?![^>]*whiteSpace=nowrap)[^>]*>'
match: not_contains
---
