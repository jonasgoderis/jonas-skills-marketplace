---
type: regex
target:
  source: file
  path: docs/gateway.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*followTerminals=1)[^>]*>\s*<mxGeometry\b[^>]*>\s*<Array as="points">'
match: contains
---
