---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?=[^>]*style="(?:image;|[^"]*shape=(?:image|mxgraph\.)))(?=[^>]*\bvalue="[^"]*?[^"&]{31})[^>]*>'
match: not_contains
---
