---
type: regex
target:
  source: file
  path: docs/architecture.drawio
pattern: 'as="(source|target)Point"'
match: not_contains
---

Every edge in this diagram joins two shapes, so none needs a loose end point.
