---
type: regex
target:
  source: file
  path: docs/gateway.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?=[^>]*style="[^"]*(?:\btext;|shape=note))(?=[^>]*autosize=1)[^>]*>'
match: not_contains
---
