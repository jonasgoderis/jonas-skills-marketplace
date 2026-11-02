---
type: regex
target:
  source: file
  path: docs/aws.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?=[^>]*style="(?:image;|[^"]*shape=(?:image|mxgraph\.)))[^>]*>[\s\S]*<mxCell\b(?=[^>]*\bedge="1")'
match: not_contains
---

Matches an icon that has an edge somewhere after it. This ignores the parent, so it is stricter than the skill when edges sit inside containers.
