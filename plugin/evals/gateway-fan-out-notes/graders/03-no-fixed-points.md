---
type: regex
target:
  source: file
  path: docs/gateway.drawio
pattern: '(?:exit|entry)(?:X|Y|Dx|Dy)='
match: not_contains
---
