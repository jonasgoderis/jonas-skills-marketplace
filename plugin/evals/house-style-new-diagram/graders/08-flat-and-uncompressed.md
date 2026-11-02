---
type: regex
target:
  source: file
  path: docs/architecture.drawio
pattern: 'compressed="true"|shadow=1|sketch=1|comic=1|glass=1|gradientColor='
match: not_contains
---
