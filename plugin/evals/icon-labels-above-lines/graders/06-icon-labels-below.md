---
type: regex
target:
  source: file
  path: docs/aws.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?=[^>]*style="(?:image;|[^"]*shape=(?:image|mxgraph\.)))(?![^>]*verticalLabelPosition=bottom)[^>]*>'
match: not_contains
---
