---
type: regex
target:
  source: file
  path: docs/gateway.drawio
pattern: '<mxCell\b(?=[^>]*value="PCI scoped")(?=[^>]*autosize=1)[^>]*>'
match: contains
---
