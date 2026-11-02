---
type: regex
target:
  source: file
  path: docs/architecture.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?:(?![^>]*\bsource=")|(?![^>]*\btarget="))[^>]*>'
match: not_contains
---

Matches an edge tag that lacks a source or a target. None may exist.
