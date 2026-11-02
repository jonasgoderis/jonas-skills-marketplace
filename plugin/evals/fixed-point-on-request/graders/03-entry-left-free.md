---
type: regex
target:
  source: file
  path: docs/flow.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*source="api")(?=[^>]*target="db")(?=[^>]*entry(X|Y)=)[^>]*>'
match: not_contains
---

The user asked about the exit only. The entry stays on the perimeter.
